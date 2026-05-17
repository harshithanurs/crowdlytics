import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",          # your password
        database="crowdlytics",
        autocommit=True,
        connection_timeout=10
    )
