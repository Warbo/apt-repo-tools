#!/usr/bin/env python
"""This will build a Debian repository in a folder called 'data' and insert any
packages it finds in a folder called 'packages'"""

import os

def makeRepoControlFile():
	'''This makes the configuration file for the repository which is
	going to be made.'''
	# The reprepro program uses a text configuration file to specify repository
	# details. Start with a blank one
	conf = ''
	# Each release has its own section (except for 'all')
	for release in [dir for dir in os.listdir(os.getcwd()+'/packages') if (not dir.endswith('.deb') and dir is not 'all')]:
		originLine = 'Origin: Repository generator'		# FIXME: How to get a meaningful name when run under gksudo?
		labelLine = 'Label: repository list'
		# The 'codename' is the release name, for example Debian 4.0 is "etch",
		# Ubuntu 7.04 is "feisty".
		codenameLine = 'Codename: ' + codename
		versionLine = 'Version: ' + time.strftime("%Y%m%d", time.gmtime())+'\n'
		architecturesLine = 'Architectures: all'
		# FIXME: Add some more architectures here

		componentsLine = 'Components: main'		# FIXME: Is it worth specifying these according to included packages?
		descriptionLine = 'Description: This package repository contains packages which enable Debian repositories'
		conf = conf + '\n' + '\n'.join([originLine,labelLine,codenameLine,versionLine,architecturesLine,componentsLine,descriptionLine])
	# Now the data is written
	if 'data' in os.listdir(os.getcwd()) and 'conf' in os.listdir(os.getcwd()+'/data'):
		pass
	else:
		os.makedirs(os.getcwd() + '/data/conf')		# This folder is needed by the reprepro tool
	distribConf = open(os.getcwd() + '/data/conf/distributions', 'w')
	distribConf.write(conf)
	distribConf.close()

def add_packages()
	# Now build the repositories
	for release in [dir for dir in os.listdir(os.getcwd()+'/packages') if (not dir.endswith('.deb') and dir is not 'all')]:
		for package in [os.getcwd()+'/packages/'+release+'/'+n for n in os.listdir(oc.getcwd()+'/packages/'+release) if n.endswith('.deb')]:
			os.popen('cd ' + os.getcwd() + '/data && reprepro --ignore=extension includedeb ' + release + ' ' + package, 'r')
		for package in [os.getcwd()+'/packages/all/'+n for n in os.listdir(oc.getcwd()+'/packages/all') if n.endswith('.deb')]:
			os.popen('cd ' + os.getcwd() + '/data && reprepro --ignore=extension includedeb ' + release + ' ' + package, 'r')


# Run the above if we've been called as a program
if __name__ == '__main__':
	makeRepoControlFile()
