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

class SendImage2(object):
    def __init__(self):
        self.config = {}


    # config utils 
    def load_mail_config(self, config_file):
        try:
            appconfig = configparser.ConfigParser()
            #base_dir = os.path.abspath(os.path.dirname('__file__'))
            #appconfig.read(os.path.join(base_dir, config_file))
            appconfig.read(config_file)

            print('==================')
            for c in appconfig['DEFAULT']:
                self.config[c] = appconfig['DEFAULT'][c]
            print("DEFAULT configs: ", self.config)
            print('------------------')
            
        except Exception as e:
            raise Exception('Error init/start Services. %s' %e) 

    def get_ticker_file(self):
        return self.config['ticker_file']


    def get_image_list(self, ticker_file, prefix="AQ_indicator", img_type="png"):
        tickers = list(pd.read_csv(ticker_file).Symbol)
        image_files = []

        for ticker in tickers:
            image_files.append(f'{prefix}_{ticker}.{img_type}')
        print('xxxx DEBUG: image_files: ', image_files)

        return image_files


    def get_image_rank(self, tickers, prefix="AQ_indicator", img_type="png"):
        """
        image_files = []
        for ticker in tickers:
            image_files.append(f'{prefix}_{ticker}.{img_type}')
        print('xxxx DEBUG: image_files: ', image_files)

        return image_files
        """
        return [f'{prefix}_{ticker}.{img_type}' for ticker in tickers]


    def add_image_files(self, msg, image_files):
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


    def add_image_content(self, msg, image_files):
        image_content = ''
        for i, image in enumerate(image_files):
            #image_content += f'<h1>{sections[i]} - </h1><p><img src="cid:{i}"></p>'
            image_content += f'<p><img src="cid:{i}"></p>'

        msg.attach(MIMEText(f'<html><body> {image_content} </body></html>', 'html', 'utf-8'))


    def send_image_files(self, image_files):
        from_addr = self.config['from_addr']
        password = self.config['password']
        to_addr = self.config['to_addr']
        smtp_server = self.config['smtp_server']
        smtp_port = self.config['smtp_port']

        # add section headers
        subject = self.config['subject']
        sections = self.config["sections"].split(",")
        ticker_filename = os.path.basename(self.config['ticker_file']).replace(".csv","")

        # email object that has multiple part:
        #msg = MIMEMultipart()
        msg = MIMEMultipart('alternative')
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = f'{subject} {ticker_filename} - {datetime.now().strftime("%Y-%m-%d")}' 

        # support both plain text and html
        #msg.attach(MIMEText('hello this is a plain text version.', 'plain', 'utf-8'))
        #msg.attach(MIMEText('<html><body><h1>Hello this is html version</h1></body></html>', 'html', 'utf-8'))

        # attache a MIMEText object to save email content
        msg_content = MIMEText('hello this is a plain text version - send with attachment...', 'plain', 'utf-8')
        msg.attach(msg_content)

        self.add_image_files(msg, image_files)
        self.add_image_content(msg, image_files)

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


#### main ####
if __name__ == '__main__':
    # set config file to be same as main script
    config_file = os.path.basename(argv[0]).replace(".py", ".config")

    if len(sys.argv) > 1:
        # load input configs
        config_file = sys.argv[1]
    print('xxxx config_file: ',config_file)

    sm = SendImage2()
    sm.load_mail_config(config_file)
    ticker_file = sm.get_ticker_file()
    #ticker_file = config['ticker_file']
    print('xxxx running report for ticker_file: ', ticker_file)

    #image_files = get_image_list(ticker_file)
    tickers = list(pd.read_csv(ticker_file).ticker)    
    image_files = sm.get_image_rank(tickers)

    sm.send_image_files(image_files)
