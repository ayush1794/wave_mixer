#!/usr/bin/python

import pyaudio,os,sys,wave,signal

chunk=1024

#flags [0:No File 1:Playing 2:Pause 3:Over]

class Player(object):
	def __init__(self):
		self.stream=None
		self.p=pyaudio.PyAudio()
		self.data=None
		self.fil=None
		self.flag=0
	def streamPath(self,path):
		self.fil=wave.open(path,"rb")
		self.stream=self.p.open(format=self.p.get_format_from_width(self.fil.getsampwidth()),
					channels=self.fil.getnchannels(),
					rate=self.fil.getframerate(),
					output=True)
		self.data=self.fil.readframes(chunk)
		while self.data!='':
			self.stream.write(self.data)
			self.data=self.fil.readframes(chunk)
		self.stream.close()
		self.p.terminate()
