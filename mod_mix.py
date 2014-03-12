#!/usr/bin/python

def scale(x,f):
	y=[]
	i=0
	a=f*i
	while(a<len(x)):
		if a.is_integer():
			y.append(x[int(a)])
		else:
			y.append(0)
		i=i+1
		a=f*i
	return y

def sepChannels(x):
	a=[]
	b=[]
	for i in range(0,len(x),2):
		a.append(x[i])
		b.append(x[i+1])
	return a,b

def joinChannels(x,y):
	a=[]
	for i in range(len(x)):
		a.append(x[i])
		a.append(y[i])
	return a
