#!/usr/bin/env python

### PAY NO ATTENTION TO THIS YET! I COPY-PASTA'D IT FROM ANOTHER TOOL!

def makeRepoControlFile():
	'''This makes the configuration file for the repository which is
	going to be made.'''
	# The reprepro program uses a text configuration file to specify repository
	# details
	# FIXME: Other architectures and distribution should be added if specified
	# as includes
	originLine = 'Origin: Repository generator'		# FIXME: How to get a meaningful name when run under gksudo?
	labelLine = 'Label: ' + self.metaPackage.getName()
	# The 'codename' is the release name, for example Debian 4.0 is "etch",
	# Ubuntu 7.04 is "feisty".
	# Here we only grab the current system's, although this should be expanded
	# in the future to allow includes like 'Distro:etch' for including mutliple
	# repositories (compression should sort out space issues of redundant data)
	codenameOut = os.popen('lsb_release -c', 'r')
	for line in codenameOut:
		self.codename = line
		self.codename = self.codename[10:]
		if self.codename.endswith('\n'):
			self.codename = self.codename[:-1]
		while self.codename.startswith(' '):
			self.codename = self.codename[1:]
		while self.codename.endswith(' '):
			self.codename = self.codename[:-1]
	codenameLine = 'Codename: ' + self.codename
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
			self.architecture = 'amd64'
		elif ('i' in line) and ('86' in line):
			self.architecture = 'i386'
		elif 'ppc' in line:
			self.architecture = 'ppc'
	architecturesLine = 'Architectures: ' + self.architecture
	# FIXME: Add some more architectures here
	componentsLine = 'Components: main'		# FIXME: Is it worth specifying these according to included packages?
	descriptionLine = 'Description: This package repository contains packages for the ' + self.metaPackage.getName() + ' service pack.'
	# Now the data is written
	self.distribConf.write(originLine + '\n' + labelLine + '\n' + codenameLine + '\n' + versionLine + '\n' + architecturesLine + '\n' + componentsLine + '\n' + descriptionLine + '\n')
	self.distribConf.close()
