import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="hopper.proxy.rlwy.net",
        user="root",
        password="hreREZRNOiharqMKjaLVZRRTBPqNYxkJ",
        database="railway",
        port=int("23564"),
        autocommit=True,
        connection_timeout=10
    )