import socket
import thread

UDP_IP = "10.0.0.3"
UDP_IP_DST = "10.0.0.1"
UDP_PORT = 5005

print "UDP own IP:", UDP_IP
print "UDP target IP:", UDP_IP_DST
print "UDP target port:", UDP_PORT


duplicated = {}
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
print "recieving.py: Starting recieving..."

while True:
	data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes

	message_id = data[0:10]

	if message_id not in duplicated.keys():
		sock.sendto( repr( data ), ( UDP_IP_DST, UDP_PORT ) )
		duplicated[ message_id ] = 1
		previous = str(int(message_id)-1).zfill(10)

		if previous in duplicated.keys():
			del duplicated[previous]


			