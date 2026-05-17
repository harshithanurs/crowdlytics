import mysql.connector
import pandas as pd

print("Connecting to DB...")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="crowdlytics"
)

query = """
SELECT 
    places.name AS place,
    visits.checkin_time
FROM visits
JOIN places ON visits.place_id = places.id
WHERE visits.checkin_time IS NOT NULL
"""

print("Reading data...")

df = pd.read_sql(query, db)

print("Raw Data:")
print(df.head())

# Convert to datetime
df['checkin_time'] = pd.to_datetime(df['checkin_time'])

# Extract time features
df['hour'] = df['checkin_time'].dt.hour
df['day'] = df['checkin_time'].dt.day_name()

# Group visits by place + hour + day
dataset = df.groupby(['place', 'hour', 'day']).size().reset_index(name='visit_count')

print("Processed Dataset:")
print(dataset.head())

dataset.to_csv("crowd_dataset.csv", index=False)
print("Dataset saved as crowd_dataset.csv")
