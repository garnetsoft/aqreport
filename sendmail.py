#Python Send Html, Image And Attachment Email Example
import os
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.image import MIMEImage

import numpy as np
import pandas as pd
import sys
from sys import argv
from pandas.tseries.offsets import BDay

import requests
from pandas_datareader import data
import ffn
import datetime
from datetime import datetime, timedelta
import configparser

import qpython
from qpython import qconnection
print('qPython %s Cython extensions enabled: %s' % (qpython.__version__, qpython.__is_cython_enabled__))


##################################################################
# global properties 
##################################################################

# load email configs -
config = {}

def usage():
    print("usage: python sendmail.py <configfile>")

# config utils 
def load_app_config(config_file):
    try:
        appconfig = configparser.ConfigParser()
        base_dir = os.path.abspath(os.path.dirname('__file__'))
        appconfig.read(os.path.join(base_dir, config_file))

        print('==================')
        for c in appconfig['DEFAULT']:
            config[c] = appconfig['DEFAULT'][c]
        print("DEFAULT configs: ", config)
        print('------------------')
    except Exception as e:
        raise Exception('Error init/start Services. %s' %e) 


# set config file to be same as main script    
config_file = os.path.basename(argv[0]).replace(".py", ".config")
print('xxxx config_file: ',config_file)

if len(sys.argv) < 2:
    usage()
    #sys.exit(-1)
    load_app_config(config_file)
else:
    # load input configs
    load_app_config(sys.argv[1])
    
ticker_file = config['ticker_file']
print('xxxx running report for ticker_file: ', ticker_file)


# get user input
# input sender email address and password:
from_addr = config['from_addr']
password = config['password']
# input receiver email address.
to_addr = config['to_addr']
# input smtp server ip address:
smtp_server = config['smtp_server']
smtp_port = config['smtp_port']

#1. simple html content
#msg = MIMEText('<html><body><h1>Hello World</h1><p>this is hello world from <a href="http://www.python.org">Python</a>...</p></body></html>', 'html', 'utf-8')

#2. Send Email With Attachments.

# email object that has multiple part:
#msg = MIMEMultipart()
msg = MIMEMultipart('alternative')
msg['From'] = from_addr
msg['To'] = to_addr
msg['Subject'] = f'{config["subject"]} {os.path.basename(ticker_file).replace(".csv","")} - {datetime.now().strftime("%Y-%m-%d")}' 


# support both plain text and html
#msg.attach(MIMEText('hello this is a plain text version.', 'plain', 'utf-8'))
#msg.attach(MIMEText('<html><body><h1>Hello this is html version</h1></body></html>', 'html', 'utf-8'))

# attache a MIMEText object to save email content
msg_content = MIMEText('hello this is a plain text version - send with attachment...', 'plain', 'utf-8')
msg.attach(msg_content)

# add section headers
sections = config["sections"].split(",")

### load images 
#image_files = ['img1.png', 'fig1.png']
image_files = config["images"].split(",")


def add_image_files(msg, image_files):
    for i, image in enumerate(image_files):

        # to add an attachment is just add a MIMEBase object to read a picture locally.
        with open(f'/tmp/{image}', 'rb') as f:
            # set attachment mime and file name, the image type is png
            mime = MIMEBase('image', 'png', filename=f'{image}')
            # add required header data:
            mime.add_header('Content-Disposition', 'attachment', filename=f'{image}')
            mime.add_header('X-Attachment-Id', f'{i}')
            mime.add_header('Content-ID', f'<{i}>')
            # read attachment file content into the MIMEBase object
            mime.set_payload(f.read())
            # encode with base64
            encoders.encode_base64(mime)
            # add MIMEBase object to MIMEMultipart object
            msg.attach(mime)


"""
Code working

    att = MIMEImage(imgData)
    att.add_header('Content-ID', f'<image{i}.{imgType}>')
    att.add_header('X-Attachment-Id', f'image{i}.{imgType}')
    att['Content-Disposition'] = f'inline; filename=image{i}.{imgType}'
    msg.attach(att)
"""

add_image_files(msg, image_files)

# embedded the image in the email content
#msg.attach(MIMEText('<html><body><h1>Hello HTML</h1><p><img src="cid:0"></p><h1>2nd Image.</h1><p><img src="cid:1"></p></body></html>', 'html', 'utf-8'))
#msg.attach(MIMEText('<html><body><h1>2nd Image.</h1><p><img src="cid:1"></p></body></html>', 'html', 'utf-8'))

image_content = ''
for i, image in enumerate(image_files):
    image_content += f'<h1>{sections[i]} - </h1><p><img src="cid:{i}"></p>'

msg.attach(MIMEText(f'<html><body> {image_content} </body></html>', 'html', 'utf-8'))


# define smtp server domain and port number.
#smtp_server = 'smtp.yahoo.com'
#smtp_port = 989
smtp_server = 'smtp.gmail.com'
smtp_port = 587

# create smtp server object.
#server = smtplib.SMTP(smtp_server, 25)
server = smtplib.SMTP(smtp_server, smtp_port)
# use ssl protocol to secure the smtp session connection, all the data transferred by the session will be secured. 
server.starttls()
# send the email as normal.
server.set_debuglevel(1)

server.login(from_addr, password)
server.sendmail(from_addr, [to_addr], msg.as_string())
server.quit()

print('xxxx DONE - email sent.')
