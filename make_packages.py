#!/usr/bin/env python

import os
import shutil
import time

def get_id(lines):
	"""Gets a nice ID for the repo in the given lines (ie. one without dodgy
	characters)"""
	results = {'name':'','sections':[],'release':'','type':''}		# Repo details
	# Look through what we've been given for an actual repo line
	for line in lines:
		if line.startswith("deb ") or line.startswith('deb-src '):
			# Split apart the line
			bits = line.strip().split(' ')

			# Grab the type
			if 'deb' in bits:
				results['type'] = 'deb'
				bits.remove('deb')
			elif 'deb-src':
				results['type'] = 'deb-src'
				bits.remove('deb-src')

			# Grab the host
			results['name'] = bits[0]
			# Sanitise it
			results['name'] = results['name'].split('://')[1]
			results['name'] = results['name'].replace('.','-')
			results['name'] = results['name'].replace(':','-')
			results['name'] = results['name'].replace('/','-')
			results['name'] = ''.join([char for char in results['name'] if (char.isalnum() or char == '-')])
			while '--' in results['name']:
				results['name'] = results['name'].replace('--','-')

			# Now grab any other data we can
			for bit in bits[1:]:
				# See if we have a debootstrap script for this bit
				if bit in os.listdir('/usr/share/debootstrap/scripts'):
					# if so then it's an OS release name
					results['release'] = bit

				else:
					# Otherwise let's take it to be a section
					results['sections'].append(''.join([char for char in bit if char.isalnum()]))

			# Stick the sections onto the name
			results['name'] = results['name'] + '-' + '-'.join(results['sections'])
			while results['name'].endswith('-'):
				results['name'] = results['name'][:-1]
			
			# Finally give back the results
			return results

def makeControl(results):
	"""Package details are kept in a structured text file called 'control'"""
	# First we make some folders to work in
	try:
		os.makedirs('temp/package/DEBIAN')
	except OSError:
		pass
	controlFile = open('temp/package/DEBIAN/control', 'w')
	# Then we add relevant information
	controlFile.write('Package: ' + results['name'] + '\n')
	controlFile.write('Priority: extra\n')
	controlFile.write('Section: repositories\n')
	controlFile.write('Installed-Size: 1\n')		# FIXME
	controlFile.write('Maintainer: unknown@unknown.com\n')		# FIXME ;)
	controlFile.write('Architecture: all\n')
	controlFile.write('Version: '+time.strftime("%Y%m%d", time.gmtime())+'\n')
	controlFile.write('Description: This package provides the ' + results['name'] + ' repository.\n')
	controlFile.close()
	return results

def makeDebianFile():
	"""This is required by dpkg"""
	debianFile = open('temp/package/DEBIAN/debian-binary', 'w')
	debianFile.write('2.0')		# Always use 2.0
	debianFile.close()

def buildPackage(filename, details):
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
	if details['release'] is '':
		details['release'] = 'all'
	if details['release'] not in os.listdir(os.getcwd()+'/packages'):
		os.makedirs(os.getcwd()+'/packages/'+details['release'])
		
	os.popen('dpkg-deb -b ' + 'temp/package packages/'+details['release']+'/'+filename+'.deb', 'r')
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
		details = makeControl(get_id(f.readlines()))
		# Give it a package version
		makeDebianFile()
		# Build a package for it
		buildPackage(filename, details)
		# Move on
		f.close()
