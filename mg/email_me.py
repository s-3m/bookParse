import smtplib
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


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
    msg["Subject"] = "Parse result (gvardia)"

    with open('gv_result/gv_result.xlsx', 'rb') as f:
        file_stock = MIMEApplication(f.read(), 'xlsx')

    file_stock.add_header('content-disposition', 'attachment', filename='gvardia_result.xlsx')
    msg.attach(file_stock)
    time.sleep(30)
    print('sending...')
    server.sendmail(sender, sender, msg.as_string())
    print('Success')