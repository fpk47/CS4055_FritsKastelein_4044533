import socket
import time
import threading

UDP_IP_IN = "10.0.0.1"
UDP_IP_OUT = "10.0.0.3"
UDP_PORT = 5005

print "UDP own IP:", UDP_IP_IN
print "UDP target IP:", UDP_IP_OUT
print "UDP target port:", UDP_PORT

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP_IN, UDP_PORT))
sendList = {}

def sendData( delay ):
    counter = 0
    print "sending.py: Starting sending..."
    while True:
        counter = counter + 1
        message_id = str(counter).zfill(10)
        sendList[message_id] = time.time()
        sock.sendto( message_id, ( UDP_IP_OUT, UDP_PORT ) )
        time.sleep( delay )

def recieveData( delay ):
    printData = False
    timeout = 1
    deleteCounter = 0
    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        message_id = data[1:11]

        if message_id in sendList.keys():
            sendList[message_id] = time.time() - sendList[message_id]

        deleteList = []
        for key in sendList.keys():

            if sendList[key] < timeout:
                deleteList.append(key)
            elif time.time() - sendList[key] > timeout:
                deleteList.append(key)
                deleteCounter = deleteCounter + 1
                printData = True

        if printData:
            print "Number Of Packets Lost: " + repr(deleteCounter)
            printData = False

        for key in deleteList:
            del sendList[key]



class sendThread (threading.Thread):
    def __init__(self, delay):
        threading.Thread.__init__(self)
        self.delay = delay
    def run(self):
        sendData(self.delay)

class recieveThread (threading.Thread):
    def __init__(self, delay):
        threading.Thread.__init__(self)
        self.delay = delay
    def run(self):
        recieveData(self.delay)

# Create new threads
thread1 = sendThread(0.001) #1000 times per second
thread2 = recieveThread(0.00001)

# Start new Threads
thread1.start()
thread2.start()






