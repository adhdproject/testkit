#!/usr/bin/env python
import subprocess
import getpass

if getpass.getuser() != "root":
	print "Please run this script as root"
	exit()




#We will check each portion of setup one at a time.
#We will start with dependencies
#When running this test, you may need to update this script to track the latest dependency additions

cur_dist = "16.04"

fi = open("dependencies.txt","r")
data = fi.read()
fi.close()

a = {}
for line in data.split("\n"):
	sec = line.split(",")
	if len(line) < 1 or line[0] == "#" or len(sec) < 4:
		continue

	name = sec[0].strip()
	tool = sec[1].strip() #currently unused
	dist = sec[2].strip()
	meth = sec[3].strip()
	if dist == "all" or dist == cur_dist:
		a[name] = [False,tool,meth]

#a = {"git":False,"sqlite3":False,"sqlite":False,"falsepackage":False}


#First we check apt/dpkg
output = subprocess.check_output("dpkg -l", shell=True)

count = 0
for line in output.split("\n"):
	t = line.split()
	if len(t) > 1:
		t = t[1]
		if t in a.keys() and a[t][2] == "apt":
			a[t][0] = True

#now by pip

import pip
installed = pip.get_installed_distributions()
lll = ["%s" % i.key for i in installed]
for line in lll:
	if line in a.keys() and a[line][2] == "pip":
		a[line][0] = True


#now ruby gems
output = subprocess.check_output("gem list", shell=True)
for line in output.split("\n"):
	if len(line) < 1:
		continue
	line = line.split()[0]
	if line in a.keys() and a[line][2] == "gem":
		a[line][0] = True

#Print out the missing dependencies
print "--- Missing dependencies ---"
print "Package\t\tTool\t\tMethod"
print "================================================="
for key in a.keys():
	if a[key][0] == False:
		print key,"\t\t", a[key][1].strip(),"\t\t", a[key][2]

#Now we will check for the existence of files on the drive
print 
print
print "--- Checking filesystem status --- "
print "===================================="
import os.path

#webkit
webkit = True
webkit_path = "/var/www/"
webkit_files = []
fi = open("webkit_files.txt","r")
data = fi.read()
fi.close()
for line in data.split("\n"):
	webkit_files.append(line.strip())

webkit_false = []
for fil in webkit_files:
	if len(fil) < 1:
		continue
	if not os.path.isfile(webkit_path + fil):
		webkit = False
		webkit_false.append(fil)

print "Webkit loaded:", webkit
if not webkit:
	for fil in webkit_false:
		print "\t*", fil

#/opt
opt = True
opt_path = "/opt/"
opt_files = []
fi = open("opt_files.txt","r")
data = fi.read()
fi.close()
for line in data.split("\n"):
	opt_files.append(line.strip())

opt_false = []
for fil in opt_files:
	if len(fil) < 1:
		continue
	if not os.path.isfile(opt_path + fil):
		opt = False
		opt_false.append(fil)

print "/opt/ loaded:", opt
if not opt:
	for fil in opt_false:
		print "\t*", fil



#Now we will assess the service profile of the system to see if everything we expect to see running/listening is.

print
print
print "--- Service Status ---"
print "======================"
output = subprocess.check_output("lsof -i -P", shell=True)
services = {"apache2":False,"mysqld":False,"postgres":False}
for line in output.split("\n"):
	if len(line) < 3:
		continue
	fir = line.split()[0]
	if fir in services.keys():
		services[fir] = True

for service in services.keys():
	status = "running"
	if services[service] == False:
		status = "off"
	print service, "is:", status


#Testing if the webkit applications are actually working

import socket

fi = open("webkit_test.txt","r")
data = fi.read()
fi.close()
ee = {}
for line in data.split("\n"):
	if len(line) < 1 or line[0] == "#":
		continue
	line = line.split(",")
	if len(line) < 3:
		continue

	path = line[0].strip()
	go = line[1].strip()
	nogo = line[2].strip()
	ee[path] = [False,go,nogo]

for entry in ee.keys():

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(("localhost",80))
	s.sendall("GET %s HTTP/1.0\r\n\r\n" % entry)
	data = s.recv(1024)
	s.close()

	if ee[entry][2] not in data and ee[entry][1] in data:
		ee[entry][0] = True


print
print
print "--- Webkit Response Tests ---"
print "============================="
ordered = []
for key in ee.keys():
	ordered.append(key)
ordered.sort(key=len)
for entry in ordered:
	extra = ""
	status = "appears to"
	if not ee[entry][0]:
		status = "does not"
		extra = "!!!"
	print entry, status,"respond", extra

#Database insertion tests

print
print
print "--- Webkit Database Insertion Tests ---"
print "======================================="
print "Testing Honeybadger:::"

import sqlite3

insertstring = "/honeybadger/service.php?target=TESTINGINPROGRESS&agent=TESTINGINPROGRESS&lat=0&lng=0&acc=1"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost",80))
s.sendall("GET %s HTTP/1.0\r\n\r\n" % insertstring)
data = s.recv(1024)
s.close()

conn = sqlite3.connect('/var/www/honeybadger/data/data.db')
cursor = conn.execute("SELECT agent FROM beacons")
for row in cursor:
	if row[0] == "TESTINGINPROGRESS":
		print "\tHoneybadger insertion test successful"
conn.execute("delete from beacons where agent='TESTINGINPROGRESS'")
conn.commit()
conn.close()

print 
print "Testing Web-Bug-Server:::"

insertstring = "/web-bug-server/index.php?id=TESTINGINPROGRESS&type=css"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost",80))
s.sendall("GET %s HTTP/1.0\r\n\r\n" % insertstring)
data = s.recv(1024)
s.close()

#gotta hack it on the command line
output = subprocess.check_output("mysql -u root -p\"adhd\" -e 'select id from webbug.requests' 2>/dev/null", shell=True)
if "TESTINGINPROGRESS" in output:
	print "\tWeb-Bug-Server insertion test successful"
output = subprocess.check_output("mysql -u root -p\"adhd\" -e 'delete from webbug.requests where id=\"TESTINGINPROGRESS\"' 2>/dev/null", shell=True)



