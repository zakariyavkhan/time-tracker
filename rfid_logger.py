#!/usr/bin/env python3

from time import sleep
from dotenv import dotenv_values
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import mariadb

reader = SimpleMFRC522()
config = dotenv_values(".env")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)


def _get_db_cxn():
    """
    :return: a connection to the database
    """
    conn_params = {
        "user": config["DB_USER"],
        "password": config["DB_PWORD"],
        "host": "localhost",
        "database": "checkin",
        "autocommit": True,
    }
    try:
        connection = mariadb.connect(**conn_params)
    except Exception as e:
        print("Error connecting to MariaDB Platform: ", e)
        # exit(1)
    return connection


def flash_green():
    GPIO.output(16, GPIO.HIGH)
    sleep(4)
    GPIO.output(16, GPIO.LOW)
    sleep(7)


def execute_query(query):
    """
    :param query: the query to execute
    """
    connection = _get_db_cxn()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        flash_green()
    except Exception as e:
        print("Error executing query: ", e)
        # exit(1)

    cursor.close()
    connection.close()


# main loop; read RFID tags and insert into database
while True:
    current_user_id, discard = reader.read()
    execute_query(f"INSERT INTO timestamps (UID) VALUES ({current_user_id})")
