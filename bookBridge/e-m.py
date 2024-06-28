# Import smtplib for the actual sending function
import os
import smtplib
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

# Import the email modules we'll need
from email.mime.text import MIMEText

def send_email():
    print('Start')
    sender = 's-3m@yandex.ru'
    password = 'aplxoqrzhjashimq'

    server = smtplib.SMTP('smtp.yandex.ru', 587)
    server.starttls()


    print('Login...')
    server.login('s-3m', password)
    msg = MIMEMultipart()
    print('Login success')
    msg["From"] = sender
    msg["To"] = sender
    msg["Subject"] = "Test"

    with open('5.xlsx', 'rb') as f:
        file = MIMEApplication(f.read(), 'xlsx')

    file.add_header('content-disposition', 'attachment', filename='e-m.xlsx')
    msg.attach(file)

    print('sending...')
    server.sendmail(sender, sender, msg.as_string())
    print('Success')


while True:
    print('Waiting file')
    if os.path.exists('5.xlsx'):
        send_email()
        break
    time.sleep(10)