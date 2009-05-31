#!/usr/bin/env python

import urllib2
import time
import sys

global count
count = 0

def get_repo(text):
	"""Gets the repository data from HTML taken from apt-get.org."""
	global count
	time.sleep(0.5)
	print str(count)
	count += 1
	repo = {'deb_lines':[], 'debsrc_lines':[], 'packages':{}}
	for line in text:
		if "deb " in line and "href" in line and (not "<" in line.replace("<a","a").replace("</a>","a")):
			repo['deb_lines'].append((line.split("<")[0] + line.split('>')[1].split('<')[0] + line.split('/a>')[1].split('<br/>')[0]).strip())
		elif "deb-src " in line and "href" in line:
			repo['debsrc_lines'].append(line.split("<")[0] + line.split('>')[1].split('<')[0] + line.split('/a>')[1].split('<br/>')[0])
		if '<a href="/list/?site=' in line:
			url = line.split('href=')[1]
			url = url[url.find('"')+1:]
			url = url[:url.find('"')]
			package_page = urllib2.urlopen('http://www.apt-get.org'+url)
			parse_package_page(package_page, repo)
	return repo

def parse_package_page(page, repo):
	"""Finds properties about a repository from the page given (a
	repository description page from apt-get.org) and gives the
	properties to the repo supplied."""
	# replace_links replaces "<a href=A_URL>text</a>" with "text (A_URL)"
	def replace_links(text):
		if '<a' in text and 'href=' in text:
			to_return = text.split('<a href=')[0] + text.split('<a href=')[1].split('>')[1][:-3] + " (" + text.split('href=')[1].split('>')[0] + ")" + replace_links(text.split("</a>",1)[1])
		else:
			to_return = text
		return to_return

	# name_version splits a string in two at a space
	def name_version(text):
		return text.split(' ')

	# check_arch removes architectures with invalid characters
	def check_arch(arch):
		ok = True
		for char in ["'", '"', "<", ">", "&"]:
			if char in arch:
				ok = False
		return ok

	for line in page.readlines():
		# Scrape the architectures listed
		if 'Architectures:' in line:
			arch_line = line.split('Architectures: ')[1].split('</span>')[0]
			repo['archs'] = filter(check_arch, map(str.strip, arch_line.split(',')))
		# Scrape the comment for this repo
		#elif 'class="comments"' in line:
		#	repo['comment'] = replace_links(line.split('class="comments">')[1].split('</span>')[0])
		# Scrape the package names and versions for each architecture
		elif 'class="packagelist"' in line:
			repo['packages'][line.split('</span>:')[0].split('"subheading">')[1]] = \
				map(name_version, line.split('<br/>')[0].split('</span>:')[1].strip().split(', '))

def apt_get_org(outfile):
	"""Scrapes data from apt-get.org."""
	# Load the page containing every repo
	results_page = urllib2.urlopen("http://www.apt-get.org/main/")
	# Save each line of HTML in to a list
	results_list = [line for line in results_page.readlines()]

	## Parse the list

	# We only care about the list of repositories
	in_list = False
	in_repo = False
	repos = []
	current_repo = []
	for line in results_list:
		if in_list:
			if "</ul" in line:
				in_list = False
			if in_repo:
				if "</li>" in line:
					repos.append(current_repo)
					current_repo = []
					in_repo = False
				else:
					current_repo.append(line)
			else:
				if "<li" in line:
					in_repo = True
					current_repo = []

		else:
			if "<ul" in line:
				in_list = True

	global count
	count = -1 * len(repos)
	repositories = map(get_repo, repos)
	for repo in repositories:
		#print str(repo)
		outfile.write("STARTREPO\n")

		#try:
		#	outfile.write("\tSTARTCOMMENT\n\t\t"+repo['comment']+"\n\tENDCOMMENT\n")
		#except KeyError:
		#	pass

		outfile.write("\tSTARTDEBS\n")
		try:
			for deb in repo['deb_lines']:
				outfile.write('\t\t'+deb+'\n')
		except:
			pass
		outfile.write("\tENDDEBS\n")

		outfile.write("\tSTARTSOURCES\n")
		try:
			for debsrc in repo['debsrc_lines']:
				outfile.write('\t\t'+debsrc+'\n')
		except:
			pass
		outfile.write("\tENDSOURCES\n")

		outfile.write("\tSTARTARCHS\n")
		try:
			for arch in repo['archs']:
				outfile.write("\t\t"+arch+"\n")
		except:
			pass
		outfile.write("\tENDARCHS\n")

		outfile.write("\tSTARTPACKAGES\n")
		try:
			for arch in repo['packages']:
				outfile.write("\t\t"+arch+"\n")
				for package in repo['packages'][arch]:
					outfile.write("\t\t\t"+package[0] + " " + package[1] + "\n")
		except:
			pass
		outfile.write("\tENDPACKAGES\n")

		outfile.write("ENDREPO\n\n")

if 'resync' in sys.argv:
	outfile = None
	for arg in sys.argv:
		if arg.startswith('-o='):
			outfile = open(arg[3:], 'w')
	if outfile is None:
		print "No output file specified! Use the option '-o=filename'."
	else:
		apt_get_org(outfile)
