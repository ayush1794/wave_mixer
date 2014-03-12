#!/usr/bin/python

import gobject,wave,struct,os,pyaudio,di,gtk,time,mod_mix,sys,signal,player,recording

AMP_MAX =(2**15)-1
AMP_MIN = -1*AMP_MAX
chunk=1024
child={}

def util(mix,i):
	return len(mix[i-1][0]),mix[i-1][1],mix[i-1][2]

def chk_pbars(win):
	for i in range(5):
		if win.frames_in_player[i]:
			if child[win.player_pid[i]]:
				win.pbars[i].pulse()
	else:
		for i in range(5):
			new_val=win.pbars[i].get_fraction()
			if win.frames_in_player[i] ==0:
				new_val=0.0
			elif child[win.player_pid[i]]:
				new_val= new_val+ (1600.0/win.frames_in_player[i])
				if new_val >=1.0:
					new_val=0.0
					child[win.player_pid[i]]=0
			win.pbars[i].set_fraction(new_val)
	return True

def gen_mod():
	i=0
	mod=[]
	params=(0,0,0,0,0,0)
	if(first.isPath() and first.isMod()):	
		i=i+1
		mod.append(first.playWithData())
		size,params,fmt=util(mod,i)	
	if(second.isPath() and second.isMod()):
		i=i+1
		mod.append(second.playWithData())
		if(mod[i-1][1][3]>params[3]):
			size,params,fmt=util(mod,i)	
	if(third.isPath() and third.isMod()):
		i=i+1
		mod.append(third.playWithData())
		if(mod[i-1][1][3]>params[3]):
			size,params,fmt=util(mod,i)	
	fi_data=[]
	if i>0:
		for j in range(size):
			to_mul=1
			for k in range(i):
				if(j<len(mod[k][0])):
					to_mul=to_mul*mod[k][0][j]
			if(to_mul>AMP_MAX):
				to_mul=AMP_MAX
			elif(to_mul<AMP_MIN):
				to_mul=AMP_MIN
			fi_data.append(to_mul)
		out=wave.open('mod.wav',"wb")
		out.setparams(params)
		conv=struct.pack(fmt,*fi_data)
		del fi_data
		out.writeframes(conv)
		out.close()
	return params[3]
	
def gen_mix():
	i=0
	mix=[]
	params=(0,0,0,0,0,0)
	if(first.isPath() and first.isMix()):
		i=i+1
		mix.append(first.playWithData())
		size,params,fmt=util(mix,i)
	if(second.isPath() and second.isMix()):
		i=i+1
		mix.append(second.playWithData())	
		if(mix[i-1][1][3]>params[3]):	
			size,params,fmt=util(mix,i)
	if(third.isPath() and third.isMix()):
		i=i+1
		mix.append(third.playWithData())
		if(mix[i-1][1][3]>params[3]):
			size,params,fmt=util(mix,i)
	fi_data=[]
	if i>0:
		for j in range(size):
			to_add=0
			for k in range(i):
				if(j<len(mix[k][0])):
					to_add=to_add+mix[k][0][j]
			fi_data.append(int(to_add/i))
		out=wave.open('mix.wav',"wb")
		print params
		out.setparams(params)
		conv=struct.pack(fmt,*fi_data)
		del fi_data
		out.writeframes(conv)
		out.close()
	return params[3]

class selection(object):
	def __init__(self):
		self.path=None
		self.wave=None
		self.ascale=1.0
		self.tscale=1.0
		self.tsh=0
		self.nchannels=None
		self.sampWidth=None
		self.frameRate=None
		self.nframes=None
		self.comptype=None
		self.compName=None
		self.data=None
		self.fmt=None
		self.mix=0
		self.modulate=0
		self.reverse=0
		self.params=()

	def isMod(self):
		return self.modulate
	
	def isMix(self):
		return self.mix
	
	def setPath(self,path):
		self.path=path
	
	def isPath(self):
		if(self.path==None):
			return 0
		return 1
	def isData(self):
		if(self.data==None):
			return 0
		return 1
	def setReverse(self,op):
		self.reverse=op

	def setMix(self,op):
		self.mix=op
	
	def setMod(self,op):
		self.modulate=op
	
	def setAScale(self,scale):
		self.ascale=scale

	def setTsh(self,tsh):
		self.tsh=tsh

	def setTScale(self,scale):
		self.tscale=scale

	def openPath(self):
		self.wave=wave.open(self.path,"rb")
		self.params=self.wave.getparams()
		self.nchannels,self.sampWidth,self.frameRate,self.nframes,self.compType,self.compName=self.params
		raw_data=self.wave.readframes(self.nframes)
		print self.nframes
		self.wave.close()
		if self.sampWidth==2:
			self.fmt="%ih" % self.nchannels*self.nframes
		else:
			raise ValueError('Not a 16 bit wav file')
		self.data=struct.unpack(self.fmt,raw_data)
		del raw_data

	def __attenuate__(self,data):
		new=list(data)
		for i in range(len(data)):
			if new[i]>AMP_MAX:
				new[i]=AMP_MAX
			elif new[i]<AMP_MIN:
				new[i]=AMP_MIN
		return tuple(new)


	def __amplify__(self,data):
		new=list(data)
		for i in range(len(data)):
			new[i]=int(self.ascale * new[i])
		return tuple(new)

	def __timeScale__(self,data):
		fi_data=mod_mix.scale(data,self.tscale)
		nframes=len(fi_data)
		params=(self.nchannels,self.sampWidth,self.frameRate,nframes,self.compType,self.compName)
		fmt = "%ih" % nframes*self.nchannels
		return fi_data,params,fmt

	def __timeShift__(self,data,params):
		if(self.tsh<0):
			fi_data=[0]*(int(self.tsh*(-1)))
			fi_data.extend(list(data))
			fi_data=tuple(fi_data)
		elif(self.tsh>0):
			fi_data=data[int(self.tsh):]
		new_params=list(params)
		new_params[3]=len(fi_data)
		fmt="%ih" %new_params[3]*self.nchannels
		return fi_data,tuple(new_params),fmt

	def playWithData(self):
		fi_data=self.data
		fi_data=self.__amplify__(fi_data)
		if(self.reverse==1):
			fi_data=tuple(reversed(fi_data))
		fi_data=self.__attenuate__(fi_data)
		params=self.params
		if(self.tsh!=0):
			fi_data,params,fmt=self.__timeShift__(fi_data,params)
		else:
			fmt=self.fmt
		if(self.tscale!=1.0):
			fi_data,params,fmt=self.__timeScale__(fi_data)
		return fi_data,params,fmt
		
	def genOutput(self,path):
		out=wave.open(path,'wb')
		fi_data,params,fmt=self.playWithData()
		out.setparams(params)
		conv=struct.pack(fmt,*fi_data)
		del fi_data
		out.writeframes(conv)
		out.close()
		return params[3]

class PyApp(gtk.Window):
	
	def __init__(self):
		super(PyApp, self).__init__()	
		self.set_title("Wave Mixer")
		self.set_size_request(750,550)
		self.set_position(gtk.WIN_POS_CENTER)
		try:
			self.set_icon_from_file("equalizer.png")
		except Exception, e:
			print e.message
			sys.exit(1)
		self.player_pid=[-2,-2,-2,-2,-2]
		self.frames_in_player=[0,0,0,0,0]	
		#Buttons	
		btn1=gtk.Button("Select File")
		btn1.connect("clicked",self.on_clicked1)
		btn2=gtk.Button("Select File")
		btn2.connect("clicked",self.on_clicked2)
		btn3=gtk.Button("Select File")
		btn3.connect("clicked",self.on_clicked3)
		play1=gtk.Button("Play/Stop")
		play1.connect("clicked",self.on_play1)
		play2=gtk.Button("Play/Stop")
		play2.connect("clicked",self.on_play2)
		play3=gtk.Button("Play/Stop")
		play3.connect("clicked",self.on_play3)
		pause1=gtk.Button("Pause")
		pause1.connect("clicked",self.on_pause1)
		pause2=gtk.Button("Pause")
		pause2.connect("clicked",self.on_pause2)
		pause3=gtk.Button("Pause")
		pause3.connect("clicked",self.on_pause3)
		pause4=gtk.Button("Pause")
		pause4.connect("clicked",self.on_pause4)
		pause5=gtk.Button("Pause")
		pause5.connect("clicked",self.on_pause5)
		mod_play_button=gtk.Button("Play/Stop Modulated")
		mod_play_button.connect("clicked",self.on_clicked_mod)
		mix_play_button=gtk.Button("Play/Stop Mixed")
		mix_play_button.connect("clicked",self.on_clicked_mix)
		record=gtk.Button("Record")
		record.connect("clicked",self.on_record)
		
		#Labels
		self.lab_fil1=gtk.Label("...")
		self.lab_fil2=gtk.Label("...")
		self.lab_fil3=gtk.Label("...")
		lab_amp1=gtk.Label("Amplitude")
		lab_amp2=gtk.Label("Amplitude")
		lab_amp3=gtk.Label("Amplitude")
		lab_tsh1=gtk.Label("Time Shift")
		lab_tsh2=gtk.Label("Time Shift")
		lab_tsh3=gtk.Label("Time Shift")
		lab_tsc1=gtk.Label("Time Scaling")
		lab_tsc2=gtk.Label("Time Scaling")
		lab_tsc3=gtk.Label("Time Scaling")
		rec_msg=gtk.Label("Recording stops when there is continued silence")
		
		#Bars
		#Amplitude Scaling Bars
		amp_sc1=gtk.HScale()
		amp_sc1.set_range(0,5)
		amp_sc1.set_value(1);
		amp_sc1.set_increments(1,2)
		amp_sc1.set_digits(1)
		amp_sc1.set_size_request(160,35)
		amp_sc1.connect("value-changed",self.on_changed_amp1)
		amp_sc2=gtk.HScale()
		amp_sc2.set_range(0,5)
		amp_sc2.set_value(1);
		amp_sc2.set_increments(1,2)
		amp_sc2.set_digits(1)
		amp_sc2.set_size_request(160,35)
		amp_sc2.connect("value-changed",self.on_changed_amp2)
		amp_sc3=gtk.HScale()
		amp_sc3.set_range(0,5)
		amp_sc3.set_value(1)
		amp_sc3.set_increments(1,2)
		amp_sc3.set_digits(1)
		amp_sc3.set_size_request(160,35)
		amp_sc3.connect("value-changed",self.on_changed_amp3)
	
		#Time Shift
		tm_sh1=gtk.HScale()
		tm_sh1.set_range(-16000,16000)
		tm_sh1.set_increments(1,2)
		tm_sh1.set_digits(0)
		tm_sh1.set_size_request(160,35)
		tm_sh1.connect("value-changed",self.on_changed_tmsh1)
		tm_sh2=gtk.HScale()
		tm_sh2.set_range(-16000,16000)
		tm_sh2.set_increments(1,2)
		tm_sh2.set_digits(0)
		tm_sh2.set_size_request(160,35)
		tm_sh2.connect("value-changed",self.on_changed_tmsh2)
		tm_sh3=gtk.HScale()
		tm_sh3.set_range(-16000,16000)
		tm_sh3.set_increments(1,2)
		tm_sh3.set_digits(0)
		tm_sh3.set_size_request(160,35)
		tm_sh3.connect("value-changed",self.on_changed_tmsh3)
		
		#Time Scaling Bars
		tm_sc1=gtk.HScale()
		tm_sc1.set_range(0.1,8)
		tm_sc1.set_increments(1.0,1.1)
		tm_sc1.set_digits(1)
		tm_sc1.set_value(1.0)
		tm_sc1.set_size_request(160,35)
		tm_sc1.connect("value-changed",self.on_changed_tmsc1)
		tm_sc2=gtk.HScale()
		tm_sc2.set_range(0.1,8)
		tm_sc2.set_increments(1.0,1.1)
		tm_sc2.set_digits(1)
		tm_sc2.set_value(1.0)
		tm_sc2.set_size_request(160,35)
		tm_sc2.connect("value-changed",self.on_changed_tmsc2)		
		tm_sc3=gtk.HScale()
		tm_sc3.set_range(0.1,8)
		tm_sc3.set_increments(1.0,1.1)
		tm_sc3.set_digits(1)
		tm_sc3.set_value(1.0)
		tm_sc3.set_size_request(160,35)
		tm_sc3.connect("value-changed",self.on_changed_tmsc3)

		#PBars
		self.pbars=[]
		for i in range(5):
			self.pbars.append(gtk.ProgressBar())
		self.timer=gobject.timeout_add(100,chk_pbars,self)

		#Time Reversal
		chk_rev1=gtk.CheckButton("Time Reversal")
		chk_rev1.connect("clicked",self.on_chk_rev1)
		chk_rev2=gtk.CheckButton("Time Reversal")
		chk_rev2.connect("clicked",self.on_chk_rev2)
		chk_rev3=gtk.CheckButton("Time Reversal")
		chk_rev3.connect("clicked",self.on_chk_rev3)
	
				
		#Select for Modulation
		chk_mod1=gtk.CheckButton("Select for Modulation")
		chk_mod1.connect("clicked",self.on_chk_mod1)
		chk_mod2=gtk.CheckButton("Select for Modulation")
		chk_mod2.connect("clicked",self.on_chk_mod2)
		chk_mod3=gtk.CheckButton("Select for Modulation")
		chk_mod3.connect("clicked",self.on_chk_mod3)
	
		#Select for Mixing
		chk_mix1=gtk.CheckButton("Select for Mixing")
		chk_mix1.connect("clicked",self.on_chk_mix1)
		chk_mix2=gtk.CheckButton("Select for Mixing")
		chk_mix2.connect("clicked",self.on_chk_mix2)
		chk_mix3=gtk.CheckButton("Select for Mixing")
		chk_mix3.connect("clicked",self.on_chk_mix3)	

		
		#Fixing Positions
		fixed = gtk.Fixed()
		fixed.put(self.lab_fil1,20,70)
		fixed.put(self.lab_fil2,270,70)
		fixed.put(self.lab_fil3,520,70)
		fixed.put(btn1,20,30)
		fixed.put(lab_amp1,20,100)
		fixed.put(lab_tsh1,20,170)
		fixed.put(lab_tsc1,20,240)
		fixed.put(btn2,270,30)
		fixed.put(lab_amp2,270,100)
		fixed.put(lab_tsh2,270,170)
		fixed.put(lab_tsc2,270,240)
		fixed.put(btn3,520,30)
		fixed.put(lab_amp3,520,100)
		fixed.put(lab_tsh3,520,170)
		fixed.put(lab_tsc3,520,240)
		fixed.put(amp_sc1,30,120)
		fixed.put(amp_sc2,280,120)
		fixed.put(amp_sc3,530,120)
		fixed.put(tm_sc1,30,260)
		fixed.put(tm_sc2,280,260)
		fixed.put(tm_sc3,530,260)
		fixed.put(tm_sh1,30,190)
		fixed.put(tm_sh2,280,190)
		fixed.put(tm_sh3,530,190)
		fixed.put(chk_rev1,20,300)
		fixed.put(chk_rev2,270,300)
		fixed.put(chk_rev3,520,300)
		fixed.put(chk_mod1,20,330)
		fixed.put(chk_mod2,270,330)
		fixed.put(chk_mod3,520,330)
		fixed.put(chk_mix1,20,360)
		fixed.put(chk_mix2,270,360)
		fixed.put(chk_mix3,520,360)
		fixed.put(play1,30,390)
		fixed.put(pause1,100,390)
		fixed.put(self.pbars[0],30,420)
		fixed.put(play2,280,390)
		fixed.put(pause2,350,390)
		fixed.put(self.pbars[1],280,420)
		fixed.put(play3,530,390)
		fixed.put(pause3,600,390)
		fixed.put(self.pbars[2],530,420)
		fixed.put(mod_play_button,30,470)
		fixed.put(pause4,170,470)
		fixed.put(self.pbars[3],30,500)
		fixed.put(mix_play_button,280,470)
		fixed.put(pause5,390,470)
		fixed.put(self.pbars[4],280,500)
		fixed.put(record,550,470)
		fixed.put(rec_msg,450,510)
		
		self.connect("destroy",gtk.main_quit)
		self.add(fixed)	
		self.show_all()
	
	def setPid(self,pid):
		self.player_pid=pid	
	
	#Listener Functions
	def on_record(self,widget):
		pid=os.fork()
		if pid==0:
			recorder=recording.Recorder()
			recorder.record_to_file()
			sys.exit(0)
		widget.set_sensitive(False)
		os.wait()
		widget.set_sensitive(True)

	def on_clicked1(self,widget):
		path=di.get()
		if(path):
			first.setPath(path)
			self.lab_fil1.set_text(os.path.basename(path))
			first.openPath()
	def on_clicked2(self,widget):
		path=di.get()
		if(path):
			second.setPath(path)
			self.lab_fil2.set_text(os.path.basename(path))	
			second.openPath()
	def on_clicked3(self,widget):
		path=di.get()
		if(path):
			third.setPath(path)
			self.lab_fil3.set_text(os.path.basename(path))
			third.openPath()
	
	def play_options(self,path,playing,index):
		try:
			os.kill(self.player_pid[index],9)
			os.wait()
			self.frames_in_player[index]=0
		except:
				if playing == 4:
					nframes=gen_mod()
				elif playing==5:
					nframes=gen_mix()
				else:
					nframes=playing.genOutput(path)
				pid=os.fork()
				if pid==0:
					if os.path.exists(path):
						print path
						play=player.Player()
						play.streamPath(path)
					os.kill(os.getppid(),signal.SIG_IGN)
					sys.exit(0)
				self.player_pid[index]=pid
				child[pid]=1
				self.frames_in_player[index]=nframes
				print self.frames_in_player[index]
	
	def pause(self,index):
		try:
			os.kill(self.player_pid[index],0)	
			if(child[self.player_pid[index]]==1):
				os.kill(self.player_pid[index],signal.SIGSTOP)
				child[self.player_pid[index]]=0
			else:
				os.kill(self.player_pid[index],signal.SIGCONT)
				child[self.player_pid[index]]=1
		except:
			return	

	def on_play1(self,widget):
		self.play_options('f1.wav',first,0)
	def on_play2(self,widget):
		self.play_options('f2.wav',second,1)
	def on_play3(self,widget):
		self.play_options('f3.wav',third,2)
	def on_clicked_mod(self,widget):
		self.play_options('mod.wav',4,3)
	def on_clicked_mix(self,widget):
		self.play_options('mix.wav',5,4)
	def on_pause1(self,widget):
		self.pause(0)
	def on_pause2(self,widget):
		self.pause(1)
	def on_pause3(self,widget):
		self.pause(2)
	def on_pause4(self,widget):
		self.pause(3)
	def on_pause5(self,widget):
		self.pause(4)
	def on_changed_amp1(self,widget):
		first.setAScale(widget.get_value())
	def on_changed_amp2(self,widget):
		second.setAScale(widget.get_value())
	def on_changed_amp3(self,widget):
		third.setAScale(widget.get_value())
	def on_changed_tmsc1(self,widget):
		first.setTScale(widget.get_value())
	def on_changed_tmsc2(self,widget):
		second.setTScale(widget.get_value())
	def on_changed_tmsc3(self,widget):
		third.setTScale(widget.get_value())
	def on_changed_tmsh1(self,widget):
		first.setTsh(widget.get_value())
	def on_changed_tmsh2(self,widget):
		second.setTsh(widget.get_value())
	def on_changed_tmsh3(self,widget):
		third.setTsh(widget.get_value())
	def on_chk_rev1(self,widget):
		if widget.get_active():
			first.setReverse(1)
		else:
			first.setReverse(0)
	def on_chk_rev2(self,widget):
		if widget.get_active():
			second.setReverse(1)
		else:
			second.setReverse(0)
	def on_chk_rev3(self,widget):
		if widget.get_active():
			third.setReverse(1)
		else:
			third.setReverse(0)
	def on_chk_mod1(self,widget):
		if widget.get_active():
			first.setMod(1)
		else:
			first.setMod(0)
	def on_chk_mod2(self,widget):
		if widget.get_active():
			second.setMod(1)
		else:
			second.setMod(0)
	def on_chk_mod3(self,widget):
		if widget.get_active():
			third.setMod(1)
		else:
			third.setMod(0)
	def on_chk_mix1(self,widget):
		if widget.get_active():
			first.setMix(1)
		else:
			first.setMix(0)
	def on_chk_mix2(self,widget):
		if widget.get_active():
			second.setMix(1)
		else:
			second.setMix(0)
	def on_chk_mix3(self,widget):
		if widget.get_active():
			third.setMix(1)
		else:
			third.setMix(0)

first=selection()
second=selection()
third=selection()
x=PyApp()
def sig_handler(signum, frame):
	os.waitpid(-1,0)

signal.signal(signal.SIG_IGN,sig_handler)
gtk.main()

if os.path.exists('mix.wav'):
	os.remove('mix.wav')
if os.path.exists('mod.wav'):
	os.remove('mod.wav')
if os.path.exists('f1.wav'):
	os.remove('f1.wav')
if os.path.exists('f2.wav'):
	os.remove('f2.wav')
if os.path.exists('f3.wav'):
	os.remove('f3.wav')
