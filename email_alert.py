# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 11:41:22 2024

@author: Adam
"""

import smtplib
from email.message import EmailMessage

def email_alert(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to
    
    user = 'admexalert@gmail.com'
    msg['from'] = user
    password = 'lcfdpuxprphfxphe'
    # c/WH=.G8pCZ@ay(u:wRebT
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(user, password)
    server.send_message(msg)
    
    server.quit()
    
if __name__ == '__main__':
    email_alert('Hey', 'Hello world', 'adam.jakus99@gmail.com')
    