#! /usr/bin/python

from datetime import datetime
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# configure send/receive emails
senderEmail = 'examplesender@gmail.com'
senderPassword = 'YOUR_PASSWORD'
recipientEmails = ['examplerecipient1@gmail.com', 'examplerecipient2@gmail.com']
errorEmail = 'exampleerror@gmail.com'

dateFormat = '%Y-%m-%d %H:%M:%S'
now = datetime.now()
timestampFile = '/var/tmp/timestamps_' + now.strftime('%Y_%m_%d') + '.csv'

emailSubject = 'Hours: ' + now.strftime('%B %-d, %Y')
emailBody = 'Here are the hours worked from the pay period ending ' + now.strftime('%B %-d, %Y') + ': \n'

# send email; return exception if error
def send_email(receiver, subject, body, exceptMessage):
    emailMessage = MIMEMultipart()
    emailMessage['From'] = senderEmail
    emailMessage['To'] = receiver
    emailMessage['Subject'] = subject
    emailMessage.attach(MIMEText(body, 'plain'))
    composedEmail = emailMessage.as_string()

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(senderEmail, senderPassword)
        server.sendmail(senderEmail, receiver, composedEmail)
        server.close()
    except:
        print(exceptMessage)

try:
    # parse timestamp file to sum hours for each individual and send email with total hours
    with open(timestampFile) as csvFile:
        csvReader = csv.reader(csvFile, quoting=csv.QUOTE_ALL, delimiter=',')
        timeElapsed = 0
        row = csvReader.__next__()
        userID = row[1]

        while row[1] == userID:
            timeStampBegin = datetime.strptime(row[2], dateFormat)
            userName = row[3]
            row = csvReader.__next__()
            timeStampEnd = datetime.strptime(row[2], dateFormat)

            # alert if unexpected timestamp difference
            if (((timeStampEnd - timeStampBegin).total_seconds()) - 1800) > 43200 or (((timeStampEnd - timeStampBegin).total_seconds()) - 1800) < 0:
                emailSubject = 'Error Summing Hours'
                emailBody = 'Unexpected timestamp difference at: ' + userName + ' ' + str(timeStampBegin)

                send_email(errorEmail, emailSubject, emailBody, 'alert email failed')
                quit()
            elif (timeStampEnd - timeStampBegin).total_seconds() < 18000:
                timeElapsed += (timeStampEnd - timeStampBegin).total_seconds()
            else:
                timeElapsed += (((timeStampEnd - timeStampBegin).total_seconds()) - 1800)

            try:
                row = csvReader.__next__()
                if userID != row[1]:
                    emailBody += userName + ': ' + str(round(timeElapsed / 3600, 2)) + 'hours \n'
                    userID = row[1]
                    timeElapsed = 0
            except:
                emailBody += userName + ': ' + str(round(timeElapsed / 3600, 2)) + 'hours \n'
                break

        send_email(recipientEmails, emailSubject, emailBody, 'hours email failed')

except:
    print('other error')
