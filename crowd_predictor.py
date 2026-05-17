import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

def train_model():
    data = pd.read_csv("crowd_dataset.csv")

    # Convert categorical to numbers
    data['place'] = data['place'].astype('category').cat.codes
    data['day'] = data['day'].astype('category').cat.codes

    # Features and target
    X = data[['place', 'hour', 'day']]
    y = data['visit_count']

    # Train model
    model = RandomForestRegressor()
    model.fit(X, y)

    # Save model
    joblib.dump(model, "crowd_model.pkl")
    print("Model trained successfully!")

# Prediction function
def predict_crowd(place, hour, day):
    model = joblib.load("crowd_model.pkl")

    # Convert input same way
    place = hash(place) % 10
    day = hash(day) % 7

    prediction = model.predict([[place, hour, day]])
    return int(prediction[0])


if __name__ == "__main__":
    train_model()