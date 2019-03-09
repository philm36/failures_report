#!/usr/bin/python3
#
# Test for email sending to multiple users read from external csv file
# Attaches four files - 1 csv and 1 pdf file for each of ZLFA & ZLFS, taken
# from 'Output' directory and produced by v 2.2 of analysis scripts

from smtplib import SMTP
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import getpass
import csv

# Create list for email receipients and open/read from csv file
recipients=[]
try:
    with open('Data/email_list.csv') as f1:
        reader=csv.reader(f1, delimiter=',')
        for row in reader:
            recipients.append(row[0])
    print('Recipients file processed')
except:
    FileNotFoundError
    print('No Recipients file found so there is no list of people to email to.')
    print('Filename should be "Data/email_list.csv"')
    exit()

# Get the user to enter the report date
report_date=input("Enter the date for the report: ")

# Set header data for email
FROM = 'pmyott@f2s.com'
TO = recipients
SUBJECT = 'Batch Delivery Failures for '+str(report_date)
TEXT = 'Batch Delivery Failures for ZLFA and ZLFS attached'

# Create list of files to be attached
files_to_attach = ['Output/full_analysis_output_zlfa_2.2.csv',
    'Output/full_analysis_output_zlfs_2.2.csv',
    'Output/piechart_zlfa.pdf', 'Output/piechart_zlfs.pdf']

# Create MIME email
msg = MIMEMultipart()
msg['From'] = FROM
msg['To'] = ", ".join(TO)
msg['Subject'] = SUBJECT

# Open and attach each of the files in the list
for fi in files_to_attach:
    attachment = MIMEBase('application','octet-string')
    try:
        attachment.set_payload(open(fi, 'rb',).read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=fi)
        msg.attach(attachment)
        print(fi,' attached')
    except:
        FileNotFoundError
        print('File ', fi, ' not found. Run "analysis" script to create one')
        print('Email has not been sent')
        exit()

# Attach the text content for the body of the email
content = MIMEText(TEXT, 'plain')
msg.attach(content)

# Connect to smtp server and send email
with SMTP("smtp-server-address") as smtp:  # smtp server here
    smtp.ehlo()
    print('Started with smtp')
    # Prompt user for email/smtp password
    password=getpass.getpass(prompt="Enter smtp password: ")
    smtp.login('smtp-logon',password)  # smtp logon here
    smtp.sendmail(FROM, TO, msg.as_string())
    print('Email sent')
