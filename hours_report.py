#!/usr/bin/env python3

import os, sys, json, smtplib, logging, mariadb
from dotenv import dotenv_values
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

project_folder = os.path.dirname(__file__)
env_path = os.path.join(project_folder, ".env")
log_path = os.path.join(project_folder, "out.log")
config = dotenv_values(env_path)
logging.basicConfig(
    filename=log_path,
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s: %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger(__name__)


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
        LOGGER.error("Error connecting to MariaDB Platform: ", e)
        exit(1)
    return connection


def _construct_email(
    sender_email, recipient_emails, subject, body, attachment_filename
):
    # Create a MIME object for the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_emails)
    msg["Subject"] = subject

    # Attach the email body
    msg.attach(MIMEText(body, "plain"))

    # Open and attach the file
    file_path = os.path.join(project_folder, f"data/{attachment_filename}")
    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", f"attachment; filename= {attachment_filename}"
        )
        msg.attach(part)

    return msg


def get_timestamp_data():
    """
    :return: a list of timestamps from the last two weeks
    sample entry: ["Mon Sep 28 2023 08:00:00AM", "John"]
    """
    connection = _get_db_cxn()
    cursor = connection.cursor()
    timestamp_query = (
        "SELECT t.time, u.name FROM timestamps AS t"
        " JOIN users AS u ON t.UID = u.UID WHERE"
        " t.time >= DATE_SUB(NOW(), INTERVAL 2 WEEK) AND t.time <= NOW();"
    )
    cursor.execute(timestamp_query)

    timestamps = []
    timestamp_fmt = "%a %b %d %Y %I:%M:%S%p"
    for timestamp, name in cursor:
        timestamps.append([timestamp.strftime(timestamp_fmt), name])

    cursor.close()
    connection.close()
    return timestamps


def write_to_json(timestamps):
    """
    parses the timestamps and writes them to a json file
    :param timestamps: a list of timestamps
    :return: the filename of the json file (current date)
    """
    data = {}
    for row in timestamps:
        timestamp = row[0]
        name = row[1]
        date = timestamp[4:15]
        time = timestamp[16:27]

        if name not in data:
            data[name] = {}

        if date not in data[name]:
            data[name][date] = []

        data[name][date].append(time)

    # write data to json
    file_name = f"{datetime.now().strftime('%Y-%m-%d')}.json"
    file_path = os.path.join(project_folder, f"data/{file_name}")

    try:
        with open(file_path, "w") as outfile:
            json.dump(data, outfile, indent=4)
        return file_name
    except Exception as e:
        LOGGER.error("Error writing to file: ", e)
        exit(1)


def calculate_hours(timestamps):
    """
    computes the total hours worked for a single day
    :param timestamps: a list of timestamps for a single day
    :return: a timedelta object representing the total hours worked
    """
    total_hours = timedelta(hours=0)
    for start_time, end_time in timestamps:
        start_datetime = datetime.strptime(start_time, "%I:%M:%S%p")
        end_datetime = datetime.strptime(end_time, "%I:%M:%S%p")
        total_hours += end_datetime - start_datetime
    return total_hours


def json_to_email(file_name):
    """
    creates a MIME email object from the json file, containing
    the total hours worked for each employee
    :param file_name: the filename of the json file
    :return: a MIME email object
    """
    file_path = os.path.join(project_folder, f"data/{file_name}")
    try:
        with open(file_path, "r") as infile:
            data = json.load(infile)
    except Exception as e:
        LOGGER.error("Error reading from file: ", e)
        exit(1)

    # get the start date from the name of the file
    start_date = datetime.strptime(file_name, "%Y-%m-%d.json") - timedelta(days=13)
    start_date_fmtd = start_date.strftime("%B %-d")
    end_date_fmtd = (start_date + timedelta(days=13)).strftime("%B %-d")
    date_range = f"{start_date_fmtd} - {end_date_fmtd}\n\n"

    email_body = "Hours from: "
    email_body += date_range
    recipients = config["RECIPIENTS"].split(",")
    errors_exist = False

    for employee, dates in data.items():
        email_body += f"{employee}:   "
        total_hours = timedelta(hours=0)
        errors = ""

        # iterates over the dates for a single employee
        for date, timestamps in dates.items():
            if len(timestamps) % 2 == 1:
                errors_exist = True
                errors += f"{date} error; "

            else:
                timestamps = [
                    (timestamps[i], timestamps[i + 1])
                    for i in range(0, len(timestamps), 2)
                ]
                # daily_hours = calculate_hours(timestamps)
                # print(f"  {date}: {daily_hours}\n")
                total_hours += calculate_hours(timestamps)

        if total_hours > timedelta(hours=0) and not errors:
            # append total_hours with 2 decimal places
            total_hours = total_hours.total_seconds() / 3600
            total_hours = f"{total_hours:.2f}"
            email_body += f"{total_hours} hours, {len(data[employee].values())} days\n"

        else:
            email_body += f"{errors}\n"

    if errors_exist:
        # construct failure email
        email = _construct_email(
            config["EMAIL_SENDER"],
            recipients,
            "Error Summing Hours",
            email_body,
            file_name,
        )

    else:
        # construct success email
        email = _construct_email(
            config["EMAIL_SENDER"],
            recipients,
            "Hours Summary",
            email_body,
            file_name,
        )

    return email


def send_email(email):
    """
    sends an email using credentials from secrets.json
    """
    try:
        server = smtplib.SMTP(config["SMTP_SERVER"], config["SMTP_PORT"])
        server.starttls()
        server.login(config["EMAIL_SENDER"], config["EMAIL_PWORD"])
        text = email.as_string()
        server.sendmail(email["From"], email["To"].split(", "), text)
        LOGGER.info("Email sent successfully")
    except Exception as e:
        LOGGER.error("Error sending email: ", e)
    finally:
        server.quit()


def main():
    with open(log_path, "r") as logfile:
        # fails if empty file
        last_updated = datetime.strptime(list(logfile)[-1][:10], "%Y-%m-%d")

    if len(sys.argv) == 1:
        if datetime.now() - last_updated < timedelta(days=8):
            LOGGER.info("Trying to compute hours off schedule")
            exit(0)
        timestamps = get_timestamp_data()
        filename = write_to_json(timestamps)
        email = json_to_email(filename)
        send_email(email)

    elif len(sys.argv) == 2:
        filename = sys.argv[1]
        email = json_to_email(filename)
        print(email.as_string())
        # ask for confirmation or cancellation before sending
        confirm = input("\nSend email? (y/n): ")
        if confirm == "y":
            send_email(email)

    else:
        print("Usage: hours_report.py [YYYY-MM-DD.json in data/]")
        exit(1)


if __name__ == "__main__":
    main()
