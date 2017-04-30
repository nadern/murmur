# Author: Nader N

import smtplib
from email.mime.text import MIMEText
import urllib.request
from datetime import datetime
import re
from datetime import timedelta
import time
import csv
import murmur_parameters

with open('name_translator.csv','r') as name_translator_file_raw:
    name_translator_file_read = csv.reader(name_translator_file_raw)
    name_translator = dict((rows[0],rows[1]) for rows in name_translator_file_read)


with open('clarity_phones.csv','r') as clarity_phones_file_raw:
    clarity_phones_file_read = csv.reader(clarity_phones_file_raw)
    clarity_phones = dict((rows[0],rows[1]) for rows in clarity_phones_file_read)
              
					
def svc_attg_finder(now):
        
    month = now.month
    day = now.day
    year = str(now.year)[2:]
    attg_dict = dict()
    
    url = 'http://www.amion.com/cgi-bin/ocs?Lo=%s&Rpt=%s&Month=%s&Day=%s&Syr=%s' % (murmur_parameters.amionlo,murmur_parameters.amionrpt,month,day,year)
    net_data = urllib.request.urlopen(url)
    for line in net_data:
        line = str(line)
        if not re.search('Hospital Medicine',line): continue
        if re.search('GMS1',line):
            tokens = line.split("\",")
            attg_dict['GOLDMAN MED #1'] = tokens[1].replace('"','')
        elif re.search('GMS2',line):
            tokens = line.split("\",")
            attg_dict['GOLDMAN MED #2'] = tokens[1].replace('"','')
        elif re.search('GMS3',line):
            tokens = line.split("\",")
            attg_dict['GOLDMAN MED #3'] = tokens[1].replace('"','')
        elif re.search('GMS4',line):
            tokens = line.split("\",")
            attg_dict['GOLDMAN MED #4'] = tokens[1].replace('"','')
        elif re.search('GMS5',line):
            tokens = line.split("\",")
            attg_dict['GOLDMAN MED #5'] = tokens[1].replace('"','')
        elif re.search('GMS6',line):
            tokens = line.split("\",")
            attg_dict['GOLDMAN MED #6'] = tokens[1].replace('"','')
        elif re.search('M-L Wards Team',line):
            team = re.findall('M-L Wards Team (.)',line)[0]
            team = 'MEDICINE ' + team
            tokens = line.split("\",")
            attg_dict[team] = tokens[1].replace('"','')
        else: continue
    return attg_dict


def service_to_attg_converter(service, attg_dict, listed_attg):
    readmit_attg_name = ''
    service_name = service.split(',')[0]
    if (re.search('MEDICINE', service_name) and not re.search('NIGHT', service_name)):    
        service_name = 'MEDICINE ' + re.findall('MEDICINE (.)',service_name)[0] # extract the letter and not the number after, e.g. E2 or A3
        readmit_attg_name_amion_version = attg_dict[service_name]
        try: 
            readmit_attg_name = name_translator[readmit_attg_name_amion_version]
        except KeyError:
            readmit_attg_name = listed_attg
    if re.search('GOLDMAN', service_name):
        try:
            readmit_attg_name_amion_version = attg_dict[service_name]
        except KeyError: 
            readmit_attg_name = listed_attg
        if readmit_attg_name == '':
            try:
                readmit_attg_name = name_translator[readmit_attg_name_amion_version]
            except KeyError:
                readmit_attg_name = listed_attg
    if re.search('NIGHT', service_name):
        readmit_attg_name = 'N*, NADER'
    else: 
        readmit_attg_name = listed_attg
    
    return readmit_attg_name
    

def phone_lookup(attg):
	if attg in clarity_phones.keys():
		return clarity_phones[attg]
	else: 
		print("Couldn't find a phone number for %s" %(attg))
		return None

def message_prep(attg, attg_phone, date, patient, dc_flag, signout = ''):
    if re.search('\,',attg):       # In case the attg name has a comma, use the first part for below
        attg = attg.split(',')[0]
    if dc_flag:
        murmur_url = 'https://redcap.ucsf.edu/surveys/?s=%s&md=%s&date=%s&pt=%s&dcf=1' % (murmur_parameters.redcapid, attg, date, patient)
    else:
        murmur_url = 'https://redcap.ucsf.edu/surveys/?s=%s&md=%s&date=%s&pt=%s&dcf=0' % (murmur_parameters.redcapid, attg, date, patient)    
    host = murmur_parameters.emailhost
    sender = murmur_parameters.emailsender
    if dc_flag: content = ' Dr.%s: %s' %(attg,murmur_url) + '  %s' % (signout) + ' You have 2 hrs to complete this survey!'
    if not dc_flag: content = 'For patient %s: %s' %(patient[:2],murmur_url) + '\n%s' % (signout)
    text_subtype = 'plain'
    msg = MIMEText(content, text_subtype)
    msg['From'] = sender
    print(attg,attg_phone)
    return host,sender,msg
	
def text_sender(host,sender,recipient,msg):
	server = smtplib.SMTP_SSL(host,465)
	server.ehlo(murmur_parameters.emailehlo)
	server.set_debuglevel(True)
	server.login(murmur_parameters.emailusername,murmur_parameters.emailpw)
	server.sendmail(sender,recipient,msg.as_string())
	server.quit()
 
def case_review_notifier(records):
    one_week_ago = datetime.now() - timedelta(days=7)
    for record in records:
        try:
            record_date = datetime.strptime(record['date'], '%Y-%m-%d')
        except ValueError:
            continue
        if record_date > one_week_ago:
            if record['refer'] == '1' or record['refer2'] == '1':
                print('sending case review notification', '\n')
                content = record['pt'] + ' Has been referred for Case Review' + ' by ' + record['md']
                msg = MIMEText(content, 'plain')
                msg['subject'] = 'Murmur referral notification'
                text_sender(murmur_parameters.emailhost, murmur_parameters.emailsender, murmur_parameters.emailcasereview, msg)
                time.sleep(2)
