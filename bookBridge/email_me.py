import smtplib
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


def send_email():

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
    msg["Subject"] = "Parse result (bb)"

    with open('compare/bb_del.xlsx', 'rb') as f:
        file_del = MIMEApplication(f.read(), 'xlsx')

    with open('compare/bb_new_stock.xlsx', 'rb') as f:
        file_new_stock = MIMEApplication(f.read(), 'xlsx')

    file_del.add_header('content-disposition', 'attachment', filename='bb_del.xlsx')
    file_new_stock.add_header('content-disposition', 'attachment', filename='bb_new_stock.xlsx')

    msg.attach(file_del)
    msg.attach(file_new_stock)
    time.sleep(30)

    print('sending...')
    server.sendmail(sender, sender, msg.as_string())
    print('Success')
    server.close()
