#!/usr/bin/env python

import os
import shutil
import time

def get_id(lines):
	id = ''
	to_return = ''
	for line in lines:
		if line.startswith("deb ") or line.startswith('deb-src '):
			for bit in line.split(' ', 1)[1].split(' '):
				x = bit.lower().strip().replace("http://", "")
				x = x.replace("/","-").replace(".","-").replace(":","-")
				id = (id + x + "-").lower()
			for char in id:
				if char.isalnum() and (not char == '~'):
					to_return = to_return + char
				else:
					to_return = to_return + '-'
			while to_return.startswith('-'):
				to_return = to_return[1:]
			while to_return.endswith('-'):
				to_return = to_return[:-1]
			return to_return

def makeControl(name):
	# Package details are kept in a structured text file called 'control'
	# First we make some folders to work in
	try:
		os.makedirs('temp/package/DEBIAN')
	except OSError:
		pass
	controlFile = open('temp/package/DEBIAN/control', 'w')
	# Then we add relevant information
	controlFile.write('Package: ' + name + '\n')
	controlFile.write('Priority: extra\n')
	controlFile.write('Section: repositories\n')
	controlFile.write('Installed-Size: 1\n')		# FIXME
	controlFile.write('Maintainer: chriswarbo@gmail.com\n')
	controlFile.write('Architecture: all\n')
	controlFile.write('Version: '+time.strftime("%Y%m%d", time.gmtime())+'\n')
	controlFile.write('Description: This package provides the ' + name + ' repository.\n')
	controlFile.close()

def makeDebianFile():
	# This is required by dpkg
	debianFile = open('temp/package/DEBIAN/debian-binary', 'w')
	debianFile.write('2.0')
	debianFile.close()

def buildPackage(filename):
	# Builds the package
	try:
		shutil.rmtree('temp/package/etc/apt/sources.list.d')
		os.makedirs('temp/package/etc/apt/sources.list.d')
	except OSError:
		pass
	print filename
	shutil.copy('temp/lists/'+filename, 'temp/package/etc/apt/sources.list.d')
	os.popen('dpkg-deb -b ' + 'temp/package temp/'+filename+'.deb', 'r')		# This builds the package
	try:
		os.wait()
	except OSError:
		pass

for filename in os.listdir('temp/lists'):
	f = open('temp/lists/'+filename, 'r')
	makeControl(get_id(f.readlines()))
	makeDebianFile()
	buildPackage(filename)
	f.close()
