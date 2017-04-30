# Author: Nader Najafi

import murmur_parameters
import murmur_app_modular_with_redcap_without_so
import pyodbc
import requests
import importlib
import time
from datetime import datetime
from datetime import timedelta
importlib.reload(murmur_app_modular_with_redcap_without_so)


################################# Remember that pyodbc returns a list of tuples (rows)

fhand = open('log.txt','a')

def readmit_lookup(date):
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=%s;DATABASE=CLARITY;UID=%s;PWD=%s' % (murmur_parameters.sshostname, murmur_parameters.ssusername, murmur_parameters.sspassword))
    cursor = cnxn.cursor()
    date = datetime.strftime(date,'%Y-%m-%d')
    datetime1 = date + ' 00:01:00.000'
    datetime2 = date + ' 23:59:00.000'
    cursor.execute(murmur_parameters.sql_query % (datetime1,datetime2) )
    rows = cursor.fetchall()
    cnxn.close()
    attg_list = []
    pat_list = []
    attg_dict = murmur_app_modular_with_redcap_without_so.svc_attg_finder(today)
    for row in rows:
        readmit_attg_name = murmur_app_modular_with_redcap_without_so.service_to_attg_converter(row[10], attg_dict, row[5])
        attg_list.append([row[4],readmit_attg_name])
        pat_list.append([row[0],str(row[1])])
    return attg_list, pat_list
	
today = datetime.now()
today = today - timedelta(days=1) # Clarity database is one day behind


attg_pairs, patients = readmit_lookup(today)

############ Write attendings and patients to log file ##########
fhand.write('\n')
fhand.write(today.strftime('%m/%d/%Y'))
fhand.write('\n')
for value in zip(attg_pairs, patients):
    fhand.write('\t'.join(value[0]))
    fhand.write('\t')
    fhand.write('\t'.join(value[1]))
    fhand.write('\n')

today = datetime.strftime(today,'%Y-%m-%d') # Formatted as a string for Redcap

############ Survey for discharge attending ############
for idx, pair in enumerate(attg_pairs): 
     patient_name_tokens = patients[idx][0].split(',')
     patient = '%s%s' % (patient_name_tokens[1][0], patient_name_tokens[0][0]) + '_' + patients[idx][1]
     dc_attg = pair[0]
     dc_attg_phone = murmur_app_modular_with_redcap_without_so.phone_lookup(dc_attg)
     if dc_attg_phone == None:
         fhand.write('\n')
         fhand.write('No number')
         fhand.write('\t')
         continue
     dc_flag = True
     host,sender,msg = murmur_app_modular_with_redcap_without_so.message_prep(dc_attg, dc_attg_phone, today, patient, dc_flag)
     print(host,sender,msg,'\n')
     fhand.write(str(dc_attg_phone))
     fhand.write('\t')
     time.sleep(2) # slow down the SMS's to avoid upsetting the mail server
     murmur_app_modular_with_redcap_without_so.text_sender(host,sender,dc_attg_phone,msg)
fhand.write('\n')
     
######### TIME DELAY ##########

time.sleep(7200) # delay in seconds


######### Get signout data from discharging attendings #######    
header_data = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
payload = {
     'token': murmur_parameters.redcaptoken,
     'content': 'record',
     'format': 'json',
     'returnFormat': 'json',
     'type': 'flat'}
url = murmur_parameters.redcapurl
s = requests.post(url,data=payload)
records = s.json()

############ Survey for readmit attending ############


for idx, pair in enumerate(attg_pairs): ## For (re)admitting attendings  
    patient_name_tokens = patients[idx][0].split(',')
    patient = '%s%s' % (patient_name_tokens[1][0], patient_name_tokens[0][0]) + '_' + patients[idx][1]
    readmit_attg = pair[1]
    readmit_attg_phone = murmur_app_modular_with_redcap_without_so.phone_lookup(readmit_attg)
    if readmit_attg_phone == None:
        fhand.write('\n')
        fhand.write('No number')
        fhand.write('\t')
        continue
    signout = 'Signout: None' # initial state until the loop
    for record in records:
        if (record['pt'] == patient and record['date'] == today): 
            signout = record['so']
        else: continue 
    dc_flag = False
    host,sender,msg = murmur_app_modular_with_redcap_without_so.message_prep(readmit_attg, readmit_attg_phone, today, patient, dc_flag, signout)
    print(host,sender,msg,'\n\n')
    fhand.write(str(readmit_attg_phone))
    fhand.write('\t')
    murmur_app_modular_with_redcap_without_so.text_sender(host,sender,readmit_attg_phone,msg)
fhand.write('\n')
fhand.write('***')

########## Notification of referrals to case review in the last week - happens each Monday ###
if datetime.today().weekday() == 0:
    murmur_app_modular_with_redcap_without_so.case_review_notifier(records)

    
fhand.close()
