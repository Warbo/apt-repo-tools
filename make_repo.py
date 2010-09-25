#!/usr/bin/env python
"""This will build a Debian repository in a folder called 'data' and insert any
packages it finds in a folder called 'packages'"""

import os

def makeRepoControlFile():
	'''This makes the configuration file for the repository which is
	going to be made.'''
	# The reprepro program uses a text configuration file to specify repository
	# details
	# FIXME: Other architectures and distribution should be added if specified
	# as includes
	originLine = 'Origin: Repository generator'		# FIXME: How to get a meaningful name when run under gksudo?
	labelLine = 'Label: repository list'
	# The 'codename' is the release name, for example Debian 4.0 is "etch",
	# Ubuntu 7.04 is "feisty".
	# Here we only grab the current system's, although this should be expanded
	# in the future to allow includes like 'Distro:etch' for including mutliple
	# repositories (compression should sort out space issues of redundant data)
	codenameOut = os.popen('lsb_release -c', 'r')
	for line in codenameOut:
		codename = line
		codename = codename[10:]
		if codename.endswith('\n'):
			codename = codename[:-1]
		while codename.startswith(' '):
			codename = codename[1:]
		while codename.endswith(' '):
			codename = codename[:-1]
	codenameLine = 'Codename: ' + codename
	# The next bit finds the version of the current distribution
	versionOut = os.popen('lsb_release -r', 'r')
	for line in versionOut:
		version = line
		version = version[9:]
		if version.endswith('\n'):
			version = version[:-2]
		while version.startswith(' ') or version.startswith('	'):
			version = version[1:]
		while version.endswith(' ') or version.endswith('	'):
			version = version[:-1]
	versionLine = 'Version: ' + version
	# The following code determines the current processor architecture. It should also handle keyword includes in the future like 'Arch:ppc'
	arch = os.popen('uname -m', 'r')
	for line in arch:
		if '64' in line:
			architecture = 'amd64'
		elif ('i' in line) and ('86' in line):
			architecture = 'i386'
		elif 'ppc' in line:
			architecture = 'ppc'
	architecturesLine = 'Architectures: ' + architecture
	# FIXME: Add some more architectures here

	componentsLine = 'Components: main'		# FIXME: Is it worth specifying these according to included packages?
	descriptionLine = 'Description: This package repository contains packages which enable Debian repositories'

	# Now the data is written
	if 'data' in os.listdir(os.getcwd()) and 'conf' in os.listdir(os.getcwd()+'/data'):
		pass
	else:
		os.makedirs(os.getcwd() + '/data/conf')		# This folder is needed by the reprepro tool
	distribConf = open(os.getcwd() + '/data/conf/distributions', 'w')
	distribConf.write(originLine + '\n' + labelLine + '\n' + codenameLine + '\n' + versionLine + '\n' + architecturesLine + '\n' + componentsLine + '\n' + descriptionLine + '\n')
	distribConf.close()

	# Now build the repository
	for current in [os.getcwd()+'/packages/'+p for p in os.listdir(os.getcwd() + '/packages') if p.endswith('.deb')]:
		os.popen('cd ' + os.getcwd() + '/data && reprepro --ignore=extension includedeb ' + codename + ' ' + current, 'r')

# Run the above if we've been called as a program
if __name__ == '__main__':
	makeRepoControlFile()
