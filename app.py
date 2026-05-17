from flask import Flask, render_template, request, redirect, session, jsonify
from database import get_db
from datetime import datetime
import webbrowser
from threading import Timer
import joblib

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "crowdlytics_secret_key"

# ---------------- LOAD ML MODEL ----------------
model = joblib.load("crowd_model.pkl")

# ---------------- ML FUNCTION (NEXT HOUR PREDICTION) ----------------
def predict_next_hour(place="Library"):
    now = datetime.now()
    hour = (now.hour + 1) % 24
    day = now.strftime("%A")  # Monday, Tuesday...

    # Encode same as training
    place_encoded = hash(place) % 10
    day_encoded = hash(day) % 7

    prediction = model.predict([[place_encoded, hour, day_encoded]])[0]

    if prediction < 10:
        return "Low"
    elif prediction < 25:
        return "Medium"
    else:
        return "High"


# ---------------- MANUAL ML PREDICTION ----------------
@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect('/')

    place = request.form['place']
    hour = int(request.form['hour'])
    day = request.form['day']

    place_encoded = hash(place) % 10
    day_encoded = hash(day) % 7

    prediction = model.predict([[place_encoded, hour, day_encoded]])[0]

    if prediction < 10:
        level = "Low"
    elif prediction < 25:
        level = "Medium"
    else:
        level = "High"

    return render_template(
        "dashboard.html",
        prediction=int(prediction),
        level=level,
        user=session['user']
    )


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (request.form['username'], request.form['password'])
        )
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:
            session['user'] = user['username']
            return redirect('/dashboard')

        return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')


# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (request.form['username'], request.form['password'])
        )
        db.commit()

        cursor.close()
        db.close()
        return redirect('/')

    return render_template('signup.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT places.id, places.name, places.capacity,
               COUNT(visits.id) AS occupancy
        FROM places
        LEFT JOIN visits
        ON places.id = visits.place_id
        AND visits.checkout_time IS NULL
        GROUP BY places.id
    """)

    places = cursor.fetchall()
    cursor.close()
    db.close()

    future_prediction = predict_next_hour("Library")

    return render_template(
        "dashboard.html",
        places=places,
        user=session['user'],
        future_prediction=future_prediction
    )


# ---------------- LIVE DATA ----------------
@app.route('/live-data')
def live_data():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT places.id, places.capacity,
               COUNT(visits.id) AS occupancy
        FROM places
        LEFT JOIN visits
        ON places.id = visits.place_id
        AND visits.checkout_time IS NULL
        GROUP BY places.id
    """)

    places = cursor.fetchall()
    cursor.close()
    db.close()

    for p in places:
        ratio = p['occupancy'] / p['capacity']
        if ratio < 0.4:
            p['status'] = "Low"
        elif ratio < 0.7:
            p['status'] = "Medium"
        else:
            p['status'] = "High"

    return jsonify(places)


# ---------------- CHECK IN ----------------
@app.route('/checkin/<int:place_id>')
def checkin(place_id):
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (session['user'],)
    )
    user = cursor.fetchone()

    if user:
        cursor.execute(
            "INSERT INTO visits (user_id, place_id, checkin_time) VALUES (%s, %s, %s)",
            (user['id'], place_id, datetime.now())
        )
        db.commit()

    cursor.close()
    db.close()
    return "ok"


# ---------------- CHECK OUT ----------------
@app.route('/checkout/<int:place_id>')
def checkout(place_id):
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT visits.id FROM visits
        JOIN users ON users.id = visits.user_id
        WHERE users.username=%s
        AND visits.place_id=%s
        AND visits.checkout_time IS NULL
        ORDER BY visits.checkin_time DESC
        LIMIT 1
    """, (session['user'], place_id))

    visit = cursor.fetchone()

    if visit:
        cursor.execute(
            "UPDATE visits SET checkout_time=%s WHERE id=%s",
            (datetime.now(), visit['id'])
        )
        db.commit()

    cursor.close()
    db.close()
    return "ok"


# ---------------- AUTO CLEAN ----------------
@app.route('/auto-clean')
def auto_clean():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE visits
        SET checkout_time = NOW()
        WHERE checkout_time IS NULL
        AND TIMESTAMPDIFF(MINUTE, checkin_time, NOW()) > 30
    """)

    db.commit()
    cursor.close()
    db.close()
    return "cleaned"


# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            places.name AS place,
            HOUR(visits.checkin_time) AS hour,
            COUNT(*) AS count
        FROM visits
        JOIN places ON visits.place_id = places.id
        WHERE visits.checkin_time >= NOW() - INTERVAL 1 HOUR
        GROUP BY place, hour
        ORDER BY hour
    """)

    data = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("analytics.html", data=data)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- AUTO OPEN BROWSER ----------------
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True)