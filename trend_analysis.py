import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("crowd_dataset.csv")

# Hourly trend
hourly = df.groupby("hour")["visit_count"].sum()

plt.figure()
hourly.plot(kind="bar")
plt.title("Crowd Trend by Hour")
plt.xlabel("Hour of Day")
plt.ylabel("Total Visits")
plt.show()

# Day trend
daily = df.groupby("day")["visit_count"].sum()

plt.figure()
daily.plot(kind="bar")
plt.title("Crowd Trend by Day")
plt.xlabel("Day")
plt.ylabel("Total Visits")
plt.show()
