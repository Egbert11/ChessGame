#!/usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# netstream.py - network data stream operation interface
#
# NOTE: The Replacement of TcpClient 
#
#======================================================================

import socket
import select
import struct
import time
import sys
import errno


#======================================================================
# RC4 cryption
#======================================================================
class rc4crypt(object):
	def __init__ (self, key = ''):
		self._key = key
		box = [ x for x in xrange(256) ]
		x = y = 0
		if len(key) > 0:
			for i in xrange(256):
				x = (x + box[i] + ord(key[i % len(key)])) & 255
				box[i], box[x] = box[x], box[i]
			x = y = 0
		self._box = box
		self._x = x
		self._y = y
	def crypt (self, data):
		box = self._box
		x, y = self._x, self._y
		if len(self._key) == 0:
			return data
		out = []
		for ch in data:
			x = (x + 1) & 255
			y = (y + box[x]) & 255
			box[x], box[y] = box[y], box[x]
			out.append(chr(ord(ch) ^ box[(box[x] + box[y]) & 255]))
		self._x, self._y = x, y
		return ''.join(out)


#======================================================================
# format of headers
#======================================================================
HEAD_WORD_LSB           = 0    # 2 bytes little endian (x86)
HEAD_WORD_MSB           = 1    # 2 bytes big endian (sparc)
HEAD_DWORD_LSB          = 2    # 4 bytes little endian (x86)
HEAD_DWORD_MSB          = 3    # 4 bytes big endian (sparc)
HEAD_BYTE_LSB           = 4    # 1 byte little endian
HEAD_BYTE_MSB           = 5    # 1 byte big endian
HEAD_WORD_LSB_EXCLUDE   = 6    # 2 bytes little endian, exclude itself
HEAD_WORD_MSB_EXCLUDE   = 7    # 2 bytes big endian, exclude itself
HEAD_DWORD_LSB_EXCLUDE  = 8    # 4 bytes little endian, exclude itself
HEAD_DWORD_MSB_EXCLUDE  = 9    # 4 bytes big endian, exclude itself
HEAD_BYTE_LSB_EXCLUDE   = 10   # 1 byte little endian, exclude itself
HEAD_BYTE_MSB_EXCLUDE   = 11   # 1 byte big endian, exclude itself
HEAD_BYTE_LSB_MASK		= 12   # 4 bytes little endian (x86) with mask

HEAD_HDR = (2, 2, 4, 4, 1, 1, 2, 2, 4, 4, 1, 1)
HEAD_INC = (0, 0, 0, 0, 0, 0, 2, 2, 4, 4, 1, 1)
HEAD_FMT = ('<H', '>H', '<I', '>I', '<B', '>B')

NET_STATE_STOP = 0				# state: init value
NET_STATE_CONNECTING = 1		# state: connecting
NET_STATE_ESTABLISHED = 2		# state: connected


#======================================================================
# netstream - basic tcp stream
#======================================================================
class netstream(object):

	def __init__(self, head = HEAD_WORD_LSB):
		self.sock = None		# socket object
		self.send_buf = ''		# send buffer
		self.recv_buf = ''		# recv buffer
		self.state = NET_STATE_STOP
		self.errd = ( errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK )
		self.conn = ( errno.EISCONN, 10057, 10053 )
		self.errc = 0
		self.headmsk = False
		self.__head_init(head)
		self.crypts = None
		self.cryptr = None
	
	def __head_init(self, head):
		if head == HEAD_BYTE_LSB_MASK:
			head = HEAD_DWORD_LSB
			self.headmsk = True
		if (head < 0) or (head >= 12): head = 0
		mode = head % 6
		self.__head_mode = head
		self.__head_hdr = HEAD_HDR[head]
		self.__head_inc = HEAD_INC[head]
		self.__head_fmt = HEAD_FMT[mode]
		self.__head_int = mode
		return 0

	def __try_connect(self):
		if (self.state == NET_STATE_ESTABLISHED):
			return 1
		if (self.state != NET_STATE_CONNECTING):
			return -1
		try:
			self.sock.recv(0)
		except socket.error, (code, strerror):
			if code in self.conn:
				return 0
			if code in self.errd:
				self.state = NET_STATE_ESTABLISHED
				self.recv_buf = ''
				return 1
			#sys.stderr.write('[TRYCONN] '+strerror+'\n')
			self.close()
			return -1
		self.state = NET_STATE_ESTABLISHED
		return 1

	# try to receive all the data into recv_buf
	def __try_recv(self):
		rdata = ''
		while 1:
			text = ''
			try:
				text = self.sock.recv(1024)
				if not text:
					self.errc = 10000
					self.close()
					return -1
			except socket.error,(code, strerror):
				if not code in self.errd:
					#sys.stderr.write('[TRYRECV] '+strerror+'\n')
					self.errc = code
					self.close()
					return -1
			if text == '':
				break
			if self.cryptr:
				text = self.cryptr.crypt(text)
			rdata += text
		self.recv_buf += rdata
		return len(rdata)

	# send data from send_buf until block (reached system buffer limit)
	def __try_send(self):
		wsize = 0
		if (len(self.send_buf) == 0):
			return 0
		try:
			wsize = self.sock.send(self.send_buf)
		except socket.error,(code, strerror):
			if not code in self.errd:
				#sys.stderr.write('[TRYSEND] '+strerror+'\n')
				self.errc = code
				self.close()
				return -1
		self.send_buf = self.send_buf[wsize:]
		return wsize

	# connect the remote server
	def connect(self, address, port, head = -1):
		self.close()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.sock.connect_ex((address, port))
		self.state = NET_STATE_CONNECTING
		self.send_buf = ''
		self.recv_buf = ''
		self.errc = 0
		if head >= 0 and head < 12:
			self.__head_init(head)
		return 0

	# close connection
	def close(self):
		self.state = NET_STATE_STOP
		if not self.sock:
			return 0
		try:
			self.sock.close()
		except:
			pass
		self.sock = None
		self.crypts = None
		self.cryptr = None
		return 0
	
	# assign a socket to netstream
	def assign(self, sock, head = -1):
		self.close()
		self.sock = sock
		self.sock.setblocking(0)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.state = NET_STATE_ESTABLISHED
		if head >= 0 and head < 12:
			self.__head_init(head)
		self.send_buf = ''
		self.recv_buf = ''
		return 0
	
	# update 
	def process(self):
		if self.state == NET_STATE_STOP:
			return 0
		if self.state == NET_STATE_CONNECTING:
			self.__try_connect()
		if self.state == NET_STATE_ESTABLISHED:
			self.__try_recv()
		if self.state == NET_STATE_ESTABLISHED:
			self.__try_send()
		return 0

	# return state
	def status(self):
		return self.state
	
	# get errno
	def error(self):
		return self.errc
	
	# append data to send_buf then try to send it out (__try_send)
	def __send_raw(self, data):
		self.send_buf += data
		self.process()
		return 0
	
	# peek data from recv_buf (read without delete it)
	def __peek_raw(self, size):
		self.process()
		if len(self.recv_buf) == 0:
			return ''
		if size > len(self.recv_buf):
			size = len(self.recv_buf)
		rdata = self.recv_buf[0:size]
		return rdata
	
	# read data from recv_buf (read and delete it from recv_buf)
	def __recv_raw(self, size):
		rdata = self.__peek_raw(size)
		size = len(rdata)
		self.recv_buf = self.recv_buf[size:]
		return rdata
	
	# append data into send_buf with a size header
	def send(self, data, category = 0):
		size = len(data) + self.__head_hdr - self.__head_inc
		if self.headmsk:
			if category < 0: category = 0
			if category > 255: category = 255
			size = (category << 24) | size
		wsize = struct.pack(self.__head_fmt, size)
		packet = wsize + data
		if self.crypts:
			packet = self.crypts.crypt(packet)
		self.__send_raw(packet)
		return 0
	
	# recv an entire message from recv_buf
	def recv(self):
		rsize = self.__peek_raw(self.__head_hdr)
		if (len(rsize) < self.__head_hdr):
			return ''
		size = struct.unpack(self.__head_fmt, rsize)[0] + self.__head_inc
		if (len(self.recv_buf) < size):
			return ''
		self.__recv_raw(self.__head_hdr)
		return self.__recv_raw(size - self.__head_hdr)

	# set tcp nodelay flag
	def nodelay(self, nodelay = 0):
		if not 'TCP_NODELAY' in socket.__dict__:
			return -1
		if self.state != NET_STATE_ESTABLISHED:
			return -2
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, nodelay)
		return 0
	
	# set rc4 key for sending encryption
	def setskey (self, rc4key = ''):
		if not rc4key:
			self.crypts = None
		else:
			self.crypts = rc4crypt(rc4key)
		return 0
	
	# set rc4 key for recving decryption
	def setrkey (self, rc4key = ''):
		if not rc4key:
			self.cryptr = None
		else:
			self.cryptr = rc4crypt(rc4key)
		return 0


#======================================================================
# nethost - basic tcp host
#======================================================================
NET_NEW =		0	# new connection£º(id,tag) ip/d,port/w   <hid>
NET_LEAVE =		1	# lost connection£º(id,tag)   		<hid>
NET_DATA =		2	# data comming£º(id,tag) data...	<hid>
NET_TIMER =		3	# timer event: (none, none) 


#======================================================================
# nethost - basic tcp host
#======================================================================
class nethost(object):

	def __init__ (self, head = HEAD_WORD_LSB):
		self.host = 0
		self.state = 0
		self.clients = []
		self.index = 1
		self.queue = []
		self.count = 0
		self.sock = 0
		self.port = 0
		self.head = head
		self.timeout = 70.0
		self.timeslap = long(time.time() * 1000)
		self.period = 0
	
	# start listenning
	def startup(self, port = 0):
		self.shutdown()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try: self.sock.bind(('0.0.0.0', port))
		except: 
			try: self.sock.close()
			except: pass
			return -1
		self.sock.listen(65536)
		self.sock.setblocking(0)
		self.port = self.sock.getsockname()[1]
		self.state = 1
		self.timeslap = long(time.time() * 1000)
		return 0

	# shutdown service
	def shutdown(self):
		if self.sock: 
			try: self.sock.close()
			except: pass
		self.sock = 0
		self.index = 1
		for n in self.clients:
			if not n: continue
			try: n.close()
			except: pass
		self.clients = []
		self.queue = []
		self.state = 0
		self.count = 0
	
	# private: close hid
	def __close(self, hid, code = 0):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -2
		if client.hid != hid: return -3
		client.close()
		return 0
	
	def __send(self, hid, data):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -2
		if client.hid != hid: return -3
		client.send(data)
		client.process()
		return 0

	# update: process clients and handle accepting
	def process(self):
		current = time.time()
		if self.state != 1: return 0
		sock = None
		try: 
			sock, remote = self.sock.accept()
			sock.setblocking(0)
		except: pass
		if self.count >= 0x10000:
			try: sock.close()
			except: pass
			sock = None
		if sock:
			pos = -1
			for i in xrange(len(self.clients)):
				if self.clients[i] == None:
					pos = i
					break
			if pos < 0:
				pos = len(self.clients)
				self.clients.append(None)
			hid = (pos & 0xffff) | (self.index << 16)
			self.index += 1
			if self.index >= 0x7fff: self.index = 1
			client = netstream(self.head)
			client.assign(sock, self.head)
			client.hid = hid
			client.tag = 0
			client.active = current
			client.peername = sock.getpeername()
			self.clients[pos] = client
			self.count += 1
			self.queue.append((NET_NEW, hid, 0, repr(client.peername)))
		for pos in xrange(len(self.clients)):
			client = self.clients[pos]
			if not client: continue
			client.process()
			while client.status() == 2:
				data = client.recv()
				if data == '': break
				self.queue.append((NET_DATA, client.hid, client.tag, data))
				client.active = current
			timeout = current - client.active
			if (client.status() == 0) or (timeout >= self.timeout):
				hid, tag = client.hid, client.tag
				self.queue.append((NET_LEAVE, hid, tag, ''))
				self.clients[pos] = None
				client.close()
				del client
				self.count -= 1
		current = long(time.time() * 1000)
		if current - self.timeslap > 100000:
			self.timeslap = current
		period = self.period
		if period > 0:
			while self.timeslap < current:
				self.queue.append((NET_TIMER, 0, 0, ''))
				self.timeslap += period
		return 0

	# send data to hid
	def send(self, hid, data):
		return self.__send(hid, data)
	
	# close client
	def close(self, hid):
		return self.__close(hid, hid)
	
	# set tag
	def settag(self, hid, tag = 0):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -2
		if hid != client.hid: return -3
		client.tag = tag
		return 0
	
	# get tag
	def gettag(self, hid):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -1
		if hid != client.hid: return -1
		return client.tag
	
	# read event
	def read(self):
		if len(self.queue) == 0:
			return (-1, 0, 0, '')
		event = self.queue[0]
		self.queue = self.queue[1:]
		return event
	
	def settimer(self, millisec = 1000):
		if millisec <= 0: 
			millisec = 0
		self.period = millisec
		self.timeslap = long(time.time() * 1000)

	def nodelay (self, hid, nodelay = 0):
		pos = hid & 0xffff
		if (pos < 0) or (pos >= len(self.clients)): return -1
		client = self.clients[pos]
		if client == None: return -1
		if hid != client.hid: return -1
		return client.nodelay(nodelay)


#----------------------------------------------------------------------
# psyco speedup
#----------------------------------------------------------------------
def _psyco_speedup():
	try:
		import psyco
		psyco.bind(rc4crypt)
		psyco.bind(netstream)
		psyco.bind(nethost)
	except:
		return False
	return True

_psyco_speedup()


#----------------------------------------------------------------------
# testing case
#----------------------------------------------------------------------
if __name__ == '__main__':
	host = nethost(8)
	host.startup(2000)
	sock = netstream(8)
	last = time.time()
	sock.connect('127.0.0.1', 2000)
	sock.send('Hello, world !!')
	stat = 0
	last = time.time()
	print 'service startup at port', host.port
	host.settimer(5000)
	sock.nodelay(0)
	sock.nodelay(1)
	while 1:
		time.sleep(0.1)
		host.process()
		sock.process()
		if stat == 0:
			if sock.status() == 2:
				stat = 1
				sock.send('Hello, world !!')
				last = time.time()
		elif stat == 1:
			if time.time() - last >= 3.0:
				sock.send('VVVV')
				stat = 2
		elif stat == 2:
			if time.time() - last >= 5.0:
				sock.send('exit')
				stat = 3
		event, wparam, lparam, data = host.read()
		if event < 0: continue
		print 'event=%d wparam=%xh lparam=%xh data="%s"'%(event, wparam, lparam, data)
		if event == NET_DATA:
			host.send(wparam, 'RE: ' + data)
			if data == 'exit': 
				print 'client request to exit'
				host.close(wparam)
		elif event == NET_NEW:
			host.send(wparam, 'HELLO CLIENT %X'%(wparam))
			host.settag(wparam, wparam)
			host.nodelay(wparam, 1)


