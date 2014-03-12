#!/usr/bin/python

# example filechooser.py

import pygtk
pygtk.require('2.0')

import gtk
# Check for new pygtk: this is new class in PyGtk 2.4
if gtk.pygtk_version < (2,3,90):
   print "PyGtk 2.3.90 or later required for this example"
   raise SystemExit

def call():
	dialog = gtk.FileChooserDialog("Open..",
        	                       None,
                	               gtk.FILE_CHOOSER_ACTION_OPEN,
                        	       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                	gtk.STOCK_OPEN, gtk.RESPONSE_OK))
	dialog.set_default_response(gtk.RESPONSE_OK)

	filter = gtk.FileFilter()
	filter.set_name("All files")
	filter.add_pattern("*")
	dialog.add_filter(filter)

	filter = gtk.FileFilter()
	filter.set_name("Wav Files")
	filter.add_mime_type("sound/wav")
	filter.add_pattern("*.wav")
	dialog.add_filter(filter)

	response = dialog.run()
	if response == gtk.RESPONSE_OK:
    		stri= dialog.get_filename()
	elif response == gtk.RESPONSE_CANCEL:
    		stri=None
	dialog.destroy()
	return stri

def get():
	stri=call()
	return stri
