#!/usr/bin python
# -*- encoding: utf-8 -*-

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#       STUDY OF SOTWARE-DEFINED NETWORKING
#  THROUGH THE DEVELOPMENT OF VIRTUAL SCENARIOS
#       BASED ON THE OPENDAYLIGHT CONTROLLER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Author: Raúl Álvarez Pinilla
# Tutor: David Fernández Cambronero
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Telematics Engineering Department (DIT)
# Technical University of Madrid (UPM)
# SPAIN

import os, sys, libxml2, urllib, re, pycurl
from StringIO import StringIO    
from subprocess import check_output, CalledProcessError

# Show menu options
def menu():
	while True:
		print "\n[1] Show topology information"
		print "[2] Show blocked hosts"
		print "[3] Block a specific host"
		print "[4] Unblock a specific host"
		print "[q] Quit\n"
		option = raw_input("Select an option: ")

		if option == '1':
			getTopology()
			showTopology()
		elif option == '2':
			getTopology()
			getBlocks()
			showBlockList()
		elif option == '3':
			getTopology()
			blockHost()
		elif option == '4':
			getTopology()
			unblockHost()
		elif option == 'q':
			sys.exit(1)

# Get network topology making HTTP GET request to OpenDaylight API
def getTopology():
	url = 'http://localhost:8181/restconf/operational/network-topology:network-topology'
	storage = StringIO()
	connection = pycurl.Curl()
	connection.setopt(connection.URL, url)
	connection.setopt(connection.USERPWD, 'admin:admin')
	connection.setopt(connection.HTTPHEADER, ['Accept: application/xml'])
	connection.setopt(connection.WRITEFUNCTION, storage.write)
	connection.perform()
	connection.close()

	content = storage.getvalue()
	topology = libxml2.parseDoc(re.sub(' xmlns="[^"]+"', '', storage.getvalue()))
	nodes=topology.xpathEval('/network-topology/topology/node')

	#Clear previous entries
	for i in range(len(switch_list)):
		switch_list.pop()
	for i in range(len(host_list)):
		host_list.pop()

	for node in nodes:
		node_id=str(libxml2.parseDoc(str(node)).xpathEval('/node/node-id/text()')[0])
		if node_id.find("openflow")>= 0:
			switch_list.append(node)
		if node_id.find("host")>= 0:
			host_list.append(node)

# Show information tables with network topology
def showTopology():
	print "\n   => Number of switches: ",len(switch_list)
	print "   => Number of hosts: ",len(host_list)

	print "\n   |---------------------|"
	print "   |---- SWITCH LIST ----|"
	print "   |---------------------|"
	for switch in switch_list:
		print "   |    ",libxml2.parseDoc(str(switch)).xpathEval('/node/node-id/text()')[0],"\t |"
	print "   |---------------------|"

	print "\n   |--------------------------------------------------------------|"
	print "   |------------------------- HOST LIST --------------------------|"
	print "   |--------------------------------------------------------------|"
	print "   |         MAC         |      IP   \t|    SWITCH  \t|   PORT  |"
	print "   |                     |           \t|            \t|         |"
	for host in host_list:
		print "   | ",
		print str(libxml2.parseDoc(str(host)).xpathEval('/node/node-id/text()')[0])[5:22], " | ",
		print libxml2.parseDoc(str(host)).xpathEval('/node/addresses/ip/text()')[0],"\t| ",
		tpID=str(libxml2.parseDoc(str(host)).xpathEval('/node/attachment-points/tp-id/text()')[0]).split(':')
		print tpID[0]+':'+tpID[1],"\t|   ",
		print tpID[2],"   |"
	print "   |--------------------------------------------------------------|\n"

# Get blocked hosts making HTTP GET request to OpenDaylight API
def getBlocks():
	url = 'http://localhost:8181/restconf/operational/opendaylight-inventory:nodes'
	storage = StringIO()
	connection = pycurl.Curl()
	connection.setopt(connection.URL, url)
	connection.setopt(connection.USERPWD, 'admin:admin')
	connection.setopt(connection.HTTPHEADER, ['Accept: application/xml'])
	connection.setopt(connection.WRITEFUNCTION, storage.write)
	connection.perform()
	connection.close()

	content = storage.getvalue()
	flows = libxml2.parseDoc(re.sub(' xmlns="[^"]+"', '', storage.getvalue())).xpathEval('//flow')

	#Clear previous entries
	for i in range(len(block_list)):
		block_list.pop()

	for flow in flows:
		flow_id=str(libxml2.parseDoc(str(flow)).xpathEval('/flow/id/text()')[0])
		if flow_id.find("block")>= 0:
			block_list.append(flow_id[6:23])			

# Show information table with blocked hosts
def showBlockList():
	print "\n   => Number of blocked hosts: ",len(block_list)

	print "\n   |--------------------------------------------------------------|"
	print "   |--------------------- BLOCKED HOST LIST ----------------------|"
	print "   |--------------------------------------------------------------|"
	print "   |         MAC         |      IP   \t|    SWITCH  \t|   PORT  |"
	print "   |                     |           \t|            \t|         |"

	for host in host_list:
		if str(libxml2.parseDoc(str(host)).xpathEval('/node/node-id/text()')[0])[5:22] in block_list:
			print "   | ",
			print str(libxml2.parseDoc(str(host)).xpathEval('/node/node-id/text()')[0])[5:22], " | ",
			print libxml2.parseDoc(str(host)).xpathEval('/node/addresses/ip/text()')[0],"\t| ",
			tpID=str(libxml2.parseDoc(str(host)).xpathEval('/node/attachment-points/tp-id/text()')[0]).split(':')
			print tpID[0]+':'+tpID[1],"\t|   ",
			print tpID[2],"   |"
	print "   |--------------------------------------------------------------|\n"

# Block a target host knowing the mac making HTTP PUT request to OpenDaylight API
def blockHost():
	mac = raw_input("\n   Enter the target host to block [mac]: ")
	
	founded = False
	for host in host_list:
		if str(libxml2.parseDoc(str(host)).xpathEval('/node/node-id/text()')[0])[5:22] == mac:
			founded = True
			targetHost = host
			break
	if founded == False:
		print "\n   => Host not founded in network topology\n"
		return		

	ip = libxml2.parseDoc(str(targetHost)).xpathEval('/node/addresses/ip/text()')[0]
	tpID=str(libxml2.parseDoc(str(host)).xpathEval('/node/attachment-points/tp-id/text()')[0]).split(':')
	switch = tpID[0]+':'+tpID[1]
	port = tpID[2]

	print "\n   => Host founded in network topology"
	print "   ======>    MAC: ", mac
	print "   ======>     IP: ", ip
	print "   ======> SWITCH: ", switch
	print "   ======>   PORT: ", port

	flowId = 'block-'+ mac
	url = 'http://localhost:8181/restconf/config/opendaylight-inventory:nodes/node/'+switch+'/table/0/flow/'+flowId
	data  = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><flow xmlns="urn:opendaylight:flow:inventory">'
	data += '<hard-timeout>0</hard-timeout><idle-timeout>0</idle-timeout><priority>20</priority><flow-name>blockedHost-'+mac+'</flow-name>'
	data += '<match><ethernet-match><ethernet-source><address>'+mac+'</address></ethernet-source></ethernet-match></match>'
	data += '<id>'+flowId+'</id><table_id>0</table_id><instructions><instruction><order>0</order><apply-actions><action>'
	data += '<order>0</order><drop-action/></action></apply-actions></instruction></instructions></flow>'
	connection = pycurl.Curl()
	connection.setopt(connection.URL, url)
	connection.setopt(connection.USERPWD, 'admin:admin')
	connection.setopt(connection.HTTPHEADER, ['Content-type: application/xml', 'Accept: application/xml'])
	connection.setopt(connection.CUSTOMREQUEST, 'PUT')
	connection.setopt(connection.POSTFIELDS, data)
	connection.perform()
	connection.close()

	print "   => Request to block host has been sended\n"

# Unblock a target host knowing the mac making HTTP DELETE request to OpenDaylight API
def unblockHost():
	mac = raw_input("\n   Enter the target host to unblock [mac]: ")
	
	founded = False
	for host in host_list:
		if str(libxml2.parseDoc(str(host)).xpathEval('/node/node-id/text()')[0])[5:22] == mac:
			founded = True
			targetHost = host
			break
	if founded == False:
		print "\n   => Host not founded in network topology\n"
		return

	ip = libxml2.parseDoc(str(targetHost)).xpathEval('/node/addresses/ip/text()')[0]
	tpID=str(libxml2.parseDoc(str(host)).xpathEval('/node/attachment-points/tp-id/text()')[0]).split(':')
	switch = tpID[0]+':'+tpID[1]
	port = tpID[2]

	print "\n   => Host founded in network topology"
	print "   ======>    MAC: ", mac
	print "   ======>     IP: ", ip
	print "   ======> SWITCH: ", switch
	print "   ======>   PORT: ", port

	url = 'http://localhost:8181/restconf/config/opendaylight-inventory:nodes/node/'+switch+'/table/0/flow/block-'+mac
	connection = pycurl.Curl()
	connection.setopt(connection.URL, url)
	connection.setopt(connection.USERPWD, 'admin:admin')
	connection.setopt(connection.CUSTOMREQUEST, 'DELETE')
	connection.perform()
	connection.close()

	print "   => Request to unblock host has been sended\n"

# Main
try:
	# Lists
	host_list=[]
	switch_list=[]
	block_list=[]

	os.system('clear')
	print "\n|------------------------------------------|"
	print "|--- Network Access Control Application ---|"
	print "|------------------------------------------|"
	menu()

except CalledProcessError as e:
    print "Error:", e.returncode		
    sys.exit(1)
