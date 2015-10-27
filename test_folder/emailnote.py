#!/usr/bin/python
import urllib
import argparse
from HTMLParser import HTMLParser
import string
import datetime
import os
import time
import ftplib
import getpass
import sys
import socket

#Import smtp library and email MIME functino for email alerts
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

#from email.mime.text import MIMEText

subjectDate=False
emailSubject = ''
smtpServer = 'localhost'
emailMessage=''
current_time=datetime.datetime.utcnow()


def emailNote(message, emailSubject, toWho, fromWho):

	#print message
	emailMessage=message

	# Fill out MIME text with the body, Subject, From and To fields
	email=MIMEText(emailMessage)
	if subjectDate:
		email['Subject'] = emailSubject + current_time.strftime("%Y%m%d.%H%M")
	else:
		email['Subject'] = emailSubject
	email['From']=fromWho
	email['To'] = toWho

	# Get an smtp object to send the email
	s=smtplib.SMTP(smtpServer)
	s.sendmail(fromWho, toWho, email.as_string())
	print "Email away...going to:"+toWho
	s.quit()
	return


if __name__=='__main__':
	# Email Information #######################################################
	# smtpServer is the host to use that will ctuall send the email
	# emailFlag is set to 1 if a condition arises that requires an email alert
	# emailMessage is initialized to nothing here, and filled in with an
	# appropriate mssage depending upon the reason for the email.

	parser = argparse.ArgumentParser(description='Processing email arguments')
	parser.add_argument('-m', '--emailMessage',required=False, default="emailnote.py", help="Identify email message")
	parser.add_argument('-s', '--emailSubject',required=False, default="This is a test",help="Identify email subject")
	parser.add_argument('--to',		required=False, default='blorgon@yahoo.com', help="Identify email address recipient")
	parser.add_argument('--sending',	required=False, default='inspector@spacetime.com', help="Identify email address sending from")
	parser.add_argument('--date',		required=False, help="Mark for date to be in subject", action='store_true')
	opts=parser.parse_args()
	#Read the options into the variables.
	emailMessage=opts.emailMessage
	emailSubject=opts.emailSubject
	emailRecipients=opts.to
	emailFrom=opts.sending
	subjectDate=opts.date

	message=open( '%s' % emailMessage, 'r').read()

	emailNote(message, emailSubject, emailRecipients, emailFrom)
