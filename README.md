Welcome to the Murmur source code repository! 

This version of Murmur is written to evaluate 5-day readmissions. Every day, it is run by Microsoft Task Scheduler, checks the Epic Clarity database for yesterday's 5-day readmits, identifies the discharge attending, identifies the readmitting attending (with help from the Amion API), text messages the discharge attending a Redcap survey link, waits two hours, pulls the "signout" field from the discharge attending's survey response, and texts the readmitting attending with the discharge attending's signout AND a Redcap survey link. Once a week it checks Redcap to see if any patients were referred for case review and sends a text message to the designated case reviewer with these patients' initials and CSN numbers.

There are several files here that you need to customize for your institution:
1) murmur_parameters.py
2) murmur_app_modular_with_redcap_without_so
3) readmission_murmur_with_redcap
4) name_translator.csv
5) clarity_phones.csv
--

1) Fill in the values required by the parameters file. See below for definitions
- SQL Server: 
sshostname is your Epic SQL Server host name, 
ssusername is your Epic SQL Server user name, 
sspassword is your Epic SQL Server password, 
sql_query is the SQL query you want Murmur to run

- Amion: 
amionlo is your password to amion

- Redcap:
redcaptoken is your API token from Redcap, 
redcapid is your Redcap survey's ID (alphanumeric string), 
redcapurl is the URL for the Redcap API

- E-mail: 
emailhost is your e-mail host name, 
emailehlo is the domain for your e-mail host, 
emailusername is your e-mail user name, 
emailpw is your e-mail password, 
email sender is your full e-mail address, 
emailcasereview is the e-mail that Murmur should use to notify of 5-day readmits where respondent requested case review

2) This file contains the bulk of the functions that are used by readmission_murmur_with_redcap

3) This is the main Python file. This is what you provide to Microsoft Task Scheduler to have your Murmur run every day
My task scheduler settings are: "run only when user is logged on", trigger is "daily" at 2 pm, action is "start a program", I use "C:\Users\nader\Anaconda\python.exe" as the path to the python interpreter (because I use Anaconda as my IDE for Python), "add arguments" contains the full path to the readmission_murmur_with_redcap file (in quotes), "start in" is the directory where you've put the Murmur files.

4) name_translator is a CSV file with two columns: name of the person as listed in Amion, name of the person in the Clarity database

5) clarity_phones.csv is a CSV file with two columns: the person's name in the Clarity databse, the person's cellphone number written as an e-mail address for use in text messaging (you need to know the person's cellphone provider to append the right domain name)
AT&T: txt.att.net (e.g. 5551234@txt.att.net)
T-Mobile: tmomail.net
Verizon: vtext.com
Sprint: messaging.sprintpcs.com
