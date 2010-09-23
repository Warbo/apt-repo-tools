#!/usr/bin/env python

import os
import shutil
import time

def get_id(lines):
	"""Gets a nice ID for the repo in the given lines (ie. one without dodgy
	characters)"""
	id = ''		# This will be the repo ID
	to_return = ''		# This is what we'll output (sanitised further)
	# Look through what we've been given for an actual repo line
	for line in lines:
		if line.startswith("deb ") or line.startswith('deb-src '):
			# We want to lose the first bit (deb/deb-src) and focus on the rest
			for bit in line.split(' ', 1)[1].split(' '):
				# Sanitise by getting rid of uppercase, spaces and protocols
				x = bit.lower().strip().replace("http://", "")
				# Get rid of slashes, dots and colons
				x = x.replace("/","-").replace(".","-").replace(":","-")
				# Now stick this piece onto the repo ID
				id = (id + x + "-").lower()
			# Now loop through the ID we just made
			for char in id:
				# Sanitise further by only allowing alphanumeric characters
				if char.isalnum() and (not char == '~'):
					to_return = to_return + char
				else:
					to_return = to_return + '-'
			# Now strip prefixed hyphens
			while to_return.startswith('-'):
				to_return = to_return[1:]
			# Then suffixed hyphens
			while to_return.endswith('-'):
				to_return = to_return[:-1]
			# Finally give back the ID
			return to_return

def makeControl(name):
	"""Package details are kept in a structured text file called 'control'"""
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
	controlFile.write('Maintainer: unknown@unknown.com\n')		# FIXME ;)
	controlFile.write('Architecture: all\n')
	controlFile.write('Version: '+time.strftime("%Y%m%d", time.gmtime())+'\n')
	controlFile.write('Description: This package provides the ' + name + ' repository.\n')
	controlFile.close()

def makeDebianFile():
	"""This is required by dpkg"""
	debianFile = open('temp/package/DEBIAN/debian-binary', 'w')
	debianFile.write('2.0')		# Always use 2.0
	debianFile.close()

def buildPackage(filename):
	"""Builds the package"""
	# Wipe out any leftovers from a previous build and start fresh
	try:
		shutil.rmtree('temp/package/etc/apt/sources.list.d')
		os.makedirs('temp/package/etc/apt/sources.list.d')
	except OSError:
		pass
	print filename		# Give progress
	# Now take all of our generated sources.list files and put them in the build
	# area
	shutil.copy('temp/lists/'+filename, 'temp/package/etc/apt/sources.list.d')
	# This builds the package
	os.popen('dpkg-deb -b ' + 'temp/package temp/'+filename+'.deb', 'r')
	# Now wait for the build to complete
	try:
		os.wait()
	except OSError:
		pass

# Run the following if we're a program, rather than being imported
if __name__ == '__main__':
	# Run through each set of package lists we've got
	for filename in os.listdir('temp/lists'):
		# Open it
		f = open('temp/lists/'+filename, 'r')
		# Build its package data
		makeControl(get_id(f.readlines()))
		# Give it a package version
		makeDebianFile()
		# Build a package for it
		buildPackage(filename)
		# Move on
		f.close()
