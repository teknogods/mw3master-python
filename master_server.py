from __future__ import with_statement
import SocketServer
import struct
import threading
import time
import socket



serversList = {}
serversLock = threading.Lock()






class ServerList:

	MW3_MS_CLEANUP_RATE = 30		#seconds

	def __init__(self):
		self.lock = threading.Lock()
		self.known = {}

	def ping(self, ip, port):
		with self.lock:
			self.known[(ip, port)] = time.time()
			
	def expire(self):
		now = time.time()
		with self.lock:
			for (key, last) in self.known.items():
				diff = now - last
				if diff >= ServerList.MW3_MS_CLEANUP_RATE:
					del self.known[key]
					(ip, port) = key
					port = struct.unpack("H", port)[0]
					print(socket.inet_ntoa(ip) + " " + str(port) + " expired")
	
	def getKnown(self):
		with self.lock:
			return self.known
	
	





class ExpireThread(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__(self)
		
	def run(self):
		while(True):
			time.sleep(1)	#seconds
			with serversLock:
				for serverList in serversList.values():
					serverList.expire()
					
					




class handler(SocketServer.BaseRequestHandler):

	MW3_MS_SERVER_MAGIC4CC = struct.pack("I", 0x424f4f42)
	MW3_MS_CLIENT_MAGIC4CC = struct.pack("I", 0x434f4b45)
	
	
	def handle(self):
		magic = self.request.recv(4)

		if magic == handler.MW3_MS_SERVER_MAGIC4CC:
			version = self.request.recv(4)
			port = self.request.recv(2)
			ip = socket.inet_aton(self.client_address[0])
			print("SERVER_MAGIC Ip: %08X, Port: %d, Version: %08X") % (struct.unpack("I", ip)[0], struct.unpack("I", port+"\0\0")[0], struct.unpack("I", version)[0])
			ip = socket.htonl(struct.unpack("I", ip)[0])
			ip = struct.pack("I", ip)
			self.getServerList(version).ping(ip, port)

		elif magic == handler.MW3_MS_CLIENT_MAGIC4CC:
			version = self.request.recv(4)
			print("CLIENT_MAGIC Version: %08X") % (struct.unpack("I", version))
			known = self.getServerList(version).getKnown()
			s = struct.pack("I", len(known))
			for (ip, port) in known:
				s += ip + port
			self.request.send(s)


	def getServerList(self, version):
		with serversLock:
			try:
				return serversList[version]
			except:
				serverList = ServerList()
				serversList[version] = serverList
				return serverList
	




if __name__ == "__main__":

	expireThread = ExpireThread()
	expireThread.start()
	
	MW3_MS_LISTEN_PORT = 27017

	print("TeknoMW3 Master Server v1.0c")
	print("============================")
	print("")
	print("Listening to connections")
	print("")

	server = SocketServer.TCPServer(("", MW3_MS_LISTEN_PORT), handler)
	server.serve_forever()
