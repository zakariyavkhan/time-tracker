#! /usr/bin/python

from datetime import datetime, timedelta
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Enter your sending & receiving emails here
sender = 'examplesender@gmail.com'
password = 'YOUR_PASSWORD'
receiver = ['examplerecipient@gmail.com', 'otherexamplerecipient@gmail.com']
admin = 'exampleadmin@gmail.com'

#Timestamp format from SQL export
format = '%Y-%m-%d %H:%M:%S'
now = datetime.now()

#Name and path of .csv from SQL export
fileName = '/var/tmp/timestamps_' + now.strftime('%Y_%m_%d') + '.csv'

#Subject and body of email message
subject = 'Hours: ' + now.strftime('%B %-d, %Y')
body = 'Here are the hours worked from the pay period ending ' + now.strftime('%B %-d, %Y') + ': \n'

try:
    #Main loop: summing hours for each employee and appending email body
    with open(fileName) as csvFile:
        csvReader = csv.reader(csvFile, quoting = csv.QUOTE_ALL, delimiter = ',')
        secondsWorked = 0
        row = csvReader.__next__()
        employee = row[1]

        while row[1] == employee:
            timeStampBegin = datetime.strptime(row[2], format)
            name = row[3]
            row = csvReader.__next__()
            timeStampEnd = datetime.strptime(row[2], format)

            #Alert someone if unexpected timestamp difference
            if ((((timeStampEnd - timeStampBegin).total_seconds())-1800) > 45000):
                subject = 'Error Summing Hours'
                body = 'Excessive timestamp difference'
                message = MIMEMultipart()
                message['From'] = sender
                message['To'] = ', '.join(admin)
                message['Subject'] = subject
                message.attach(MIMEText(body, 'plain'))
                bodyText = message.as_string()

                try:
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.login(sender, password)
                    server.sendmail(sender, admin, bodyText)
                    server.close()
                except:
                    print('alert email failed')

            secondsWorked += (((timeStampEnd - timeStampBegin).total_seconds())-1800)
            try:
                row = csvReader.__next__()
                if employee != row[1]:
                    body += name + ': ' + str(timedelta(seconds = secondsWorked)) + '\n'
                    employee = row[1]
                    secondsWorked = 0
            except:
                body += name + ': ' + str(timedelta(seconds = secondsWorked)) + '\n'
                break

        #Constructing email
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = ', '.join(receiver)
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        bodyText = message.as_string()

        #Connecting to SMTP and sending email
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender, password)
            server.sendmail(sender, receiver, bodyText)
            server.close()
        except:
            print('email failed')

except:
    print('no file to parse')
