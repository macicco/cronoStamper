#!/usr/bin/python
'''
    Simple socket server using threads
'''

import zmq
import time
import socket
import sys
import threading
from config import *



 
HOST = ''   # Symbolic name meaning all available interfaces
PORT = socketsPort # Arbitrary non-privileged port
 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Starting CronoStamper Sockets Server.'
print 'Socket created'
 
#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
     
print 'Socket bind complete'
 
#Start listening on socket
s.listen(10)
print 'Socket now listening'
 
#ZMQ context
context = zmq.Context()


#Function for handling connections. This will be used to create threads
#Important: Each thread has to have its own zmq sockets to avoid data corruption
def clientthread(conn,addr):
    print 'Connected with ' + addr[0] + ':' + str(addr[1])

    topicfilter = ShutterFlange
    socket = context.socket(zmq.SUB)
    #only one message (do not work with the stock version of zmq, works from ver 4.1.4)
    socket.setsockopt(zmq.CONFLATE, 1)
    socket.connect ("tcp://localhost:%s" % zmqShutterPort)
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

    GPStopicfilter = "GPS"
    socketGPS = context.socket(zmq.SUB)
    #CONFLATE: get only one message (do not work with the stock version of zmq, works from ver 4.1.4)
    socketGPS.setsockopt(zmq.CONFLATE, 1)
    socketGPS.connect ("tcp://localhost:%s" % zmqGPSPort)
    socketGPS.setsockopt(zmq.SUBSCRIBE, GPStopicfilter)

    lastGPS={}


    #Sending message to connected client
    #conn.send('OK.CronoStamper socket server.\n') #send only takes string
     
    #infinite loop so that function do not terminate and thread do not end.
    while True:
		#get shutter time
		m= socket.recv()
		topic, msg  = demogrify(m)

		#try get GPS and time data
		try:
			GPSm= socketGPS.recv(flags=zmq.NOBLOCK)
			topic, GPSmsg  = demogrify(GPSm)
			lastGPS=GPSmsg
			msgGPS = GPSmsg
		except:
			msgGPS = lastGPS


		#format the reply string
		try:
			reply = "%s %010.6f %1.0d %5.3e\r\n" % (msg['dateUTC'],msg['pulse'],msgGPS['mode'],msgGPS['ClkError'])
		except:
			reply = "%s %010.6f - -.-------\r\n" % (msg['dateUTC'],msg['pulse'])

		#catch the send reply to manage if client close the socket
		try:
    			conn.sendall(reply)
	
		except:     
			#came out of loop. close socket and thread
		    	print 'Disconnected:' + addr[0] + ':' + str(addr[1])
		    	conn.close()
			socket.close()
			socketGPS.close()
		    	break
		



 
#now keep talking with the client
while True:
    #wait to accept a connection - blocking call
    conn, addr = s.accept()

     
    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    t = threading.Thread(target=clientthread,args=(conn,addr,))
    t.start()

s.close()
