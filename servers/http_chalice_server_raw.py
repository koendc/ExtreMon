#!/usr/bin/env python3

#
#	ExtreMon Project
#	Copyright (C) 2009-2013 Frank Marien
#	frank@apsu.be
#
#	This file is part of ExtreMon.
#
#	ExtreMon is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	ExtreMon is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with ExtreMon.  If not, see <http://www.gnu.org/licenses/>.
#

import 							sys
from http.server		import 	HTTPServer,BaseHTTPRequestHandler
from socketserver		import 	ThreadingMixIn
from queue 				import 	Queue,Full
from socket 			import 	error
from extremon			import 	CauldronReceiver,ChaliceServer
from threading			import 	Thread


class HTTPChaliceRequestHandler(BaseHTTPRequestHandler):

	server_version = "Extremon/0.1"

	def do_GET(self):
		self.outq=Queue(maxsize=1024)
		self.running=True
		self.server.add_consumer(self)

		self.send_response(200)
		self.send_header("Content-type", "text/plain")
		self.send_header("Access-Control-Allow-Origin", "*")
		self.end_headers()
		self.running=True

		try:
			while self.running:
				try:
					self.wfile.write(self.outq.get())
					self.outq.task_done()
				except error:
					self.running=False
		finally:
			self.server.remove_consumer(self)

	def write(self,data):
		try:
			self.outq.put(data,block=False)
		except Full:
			pass

class HTTPChaliceServer(ThreadingMixIn, ChaliceServer,HTTPServer):
	def __init__(self,listen,prefix):
		HTTPServer.__init__(self,listen, HTTPChaliceRequestHandler)
		ChaliceServer.__init__(self, prefix)

class HTTPChaliceDispatcher(Thread):
	def __init__(self,mcast_addr,listen,prefix):
		Thread.__init__(self)
		self.deamon=True
		self.server=HTTPChaliceServer(listen,prefix)
		self.receiver=CauldronReceiver(mcast_addr=mcast_addr,handler=self);
		self.server.start()
		self.start()
		self.server.serve_forever()

	def run(self):
		self.receiver.receive_forever()

	def handle_shuttle(self,data):
		self.server.write(data)

if __name__=='__main__':

	if len(sys.argv)==2:
		listen_addr=''
		listen_port=17817
	elif len(sys.argv)==4:
		listen_addr=sys.argv[2]
		listen_port=int(sys.argv[3])
	else:
		print("Usage: http_server.py <prefix> [<listen_addr> <listen_port>]")
		sys.exit(-1)

	prefix=sys.argv[1]

	HTTPChaliceDispatcher(mcast_addr=('224.0.0.1',1249),listen=(listen_addr,listen_port),prefix=prefix)

