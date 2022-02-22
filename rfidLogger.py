#! /usr/bin/python

import time
from time import sleep
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import mysql.connector

# Configure raspberrypi GPIO outputs for LEDs
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
green = 16
red = 18
GPIO.setup(green, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(red, GPIO.OUT, initial=GPIO.LOW)

reader = SimpleMFRC522()

# Configure database init details, SQL queries
dbHost = 'localhost'
dbName = 'YOUR_DB_NAME'
dbUser = 'YOUR_DB_USER'
dbPassword = 'YOUR_DB_USER_PASSWORD'

# config = {
#  'user': 'YOUR_DB_USER',
#  'password': 'YOUR_DB_USER_PASSWORD',
#  'host': 'localhost',
#  'database': 'YOUR_DB_NAME'
# }

idSearch = 'SELECT id, name FROM users WHERE rfid_uid ='
attendanceInsert = 'INSERT INTO attendance (user_id, name) VALUES (%s, %s)'
connection = None


# Initializes database
def init_db():
    return mysql.connector.connect(
        host=dbHost,
        user=dbUser,
        passwd=dbPassword,
        database=dbName
        # **config
    )


# Reactivates connection if necessary and returns cursor on database
def get_cursor():
    global connection
    try:
        connection.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error as err:
        connection = init_db()
    return connection.cursor()


# Flashes LED
def flash(color):
    GPIO.output(color, GPIO.HIGH)
    sleep(2)
    GPIO.output(color, GPIO.LOW)
    sleep(3)


connection = init_db()
cursor = get_cursor()

# Main loop: Records UID and timestamp to database when RFID card is scanned
while True:
    current_user_id, discard = reader.read()
    cursor = get_cursor()
    cursor.execute(idSearch + str(current_user_id))
    result = cursor.fetchone()
    if cursor.rowcount < 1:
        flash(red)
        cursor.close()
    elif cursor.rowcount >= 1:
        cursor.execute(attendanceInsert, (result[0], result[1]))
        connection.commit()
        flash(green)
        cursor.close()
    else:
        sleep(3)
        cursor.close()
