#! /usr/bin/python

from datetime import datetime
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Enter your sending & receiving emails here
# Sender must be gmail address
sender = 'examplesender@gmail.com'
password = 'YOUR_PASSWORD'
recipients = ['examplerecipient1@gmail.com', 'examplerecipient2@gmail.com']
admin = 'exampleadmin@gmail.com'

# Timestamp format from SQL export
formatDate = '%Y-%m-%d %H:%M:%S'
now = datetime.now()

# Name and path of .csv from SQL export
fileName = '/var/tmp/timestamps_' + now.strftime('%Y_%m_%d') + '.csv'

# Subject, body, server of email message
subject = 'Hours: ' + now.strftime('%B %-d, %Y')
body = 'Here are the hours worked from the pay period ending ' + now.strftime('%B %-d, %Y') + ': \n'

# Send email
def send_email(receiver, emailSubject, emailBody, exceptMessage):
    # Constructing email
    emailMessage = MIMEMultipart()
    emailMessage['From'] = sender
    emailMessage['To'] = receiver
    emailMessage['Subject'] = emailSubject
    emailMessage.attach(MIMEText(emailBody, 'plain'))
    composedEmail = emailMessage.as_string()

    # Connecting to SMTP and sending email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, password)
        server.sendmail(sender, receiver, composedEmail)
        server.close()
    except:
        print(exceptMessage)

try:
    # Main loop: summing hours for each employee and appending email
    with open(fileName) as csvFile:
        csvReader = csv.reader(csvFile, quoting=csv.QUOTE_ALL, delimiter=',')
        secondsWorked = 0
        row = csvReader.__next__()
        employee = row[1]

        while row[1] == employee:
            timeStampBegin = datetime.strptime(row[2], formatDate)
            name = row[3]
            row = csvReader.__next__()
            timeStampEnd = datetime.strptime(row[2], formatDate)

            # Alert if unexpected timestamp difference
            if (((timeStampEnd - timeStampBegin).total_seconds()) - 1800) > 43200 or (((timeStampEnd - timeStampBegin).total_seconds()) - 1800) < 0:
                subject = 'Error Summing Hours'
                body = 'Excessive timestamp difference at: ' + name + ' ' + str(timeStampBegin)

                send_email(admin, subject, body, 'alert email failed')
                quit()

            secondsWorked += (((timeStampEnd - timeStampBegin).total_seconds()) - 1800)
            try:
                row = csvReader.__next__()
                if employee != row[1]:
                    body += name + ': ' + str(round(secondsWorked/3600, 2)) + 'hours \n'
                    employee = row[1]
                    secondsWorked = 0
            except:
                body += name + ': ' + str(round(secondsWorked/3600, 2)) + 'hours \n'
                break

        send_email(recipients, subject, body, 'hours email failed')

except:
    print('gremlin')
