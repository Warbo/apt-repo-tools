#!/usr/bin/env python

import urllib2
import httplib
import socket
import time
import sys
import lxml
from lxml.etree import ElementTree, Element, SubElement
import xml.dom.minidom
import re

global count
count = 0

def XMLescape(txt):
	"""Replaces FORM FEED, ESC and other invalid XML characters in the
	given text, as well as converting as much as possible to UTF-8."""

	# This will store the encoded version
	text = ''

	# Step through each character of the text
	for char in txt:
		# Attempt to add a UTF-8 encoded version to the result
		try:
			text = text + char.encode("utf-8")
		except UnicodeDecodeError:
			# Ignore errors
			print 'not adding ' + char

	# Replace characters
	to_return = text.replace("&", "&amp;").replace("<", "&lt;").\
		replace(">", "&gt;").replace('"', "&quot;").\
		replace(u'\x0C', "").replace(u'\x1B', "")

	# Send the result to the caller
	return to_return

#### TAKEN FROM THE LAZYWEB ####
class MyHTTPConnection(httplib.HTTPConnection):
	"""A customised HTTPConnection allowing a per-connection
	timeout, specified at construction."""

	def __init__(self, host, port=None, strict=None, timeout=None):
		httplib.HTTPConnection.__init__(self, host, port, strict)
		self.timeout = timeout

	def connect(self):
		"""Override HTTPConnection.connect to connect to
		host/port specified in __init__."""

		msg = "getaddrinfo returns an empty list"
		for res in socket.getaddrinfo(self.host, self.port, \
			0, socket.SOCK_STREAM):
			af, socktype, proto, canonname, sa = res
			try:
				self.sock = socket.socket(af, socktype, proto)
				if self.timeout:   # this is the new bit
					self.sock.settimeout(self.timeout)
				self.sock.connect(sa)
			except socket.error, msg:
				if self.sock:
					self.sock.close()
				self.sock = None
				continue
			break
		if not self.sock:
			raise socket.error, msg

class MyHTTPHandler(urllib2.HTTPHandler):
	"""A customised HTTPHandler which times out connection
	after the duration specified at construction."""

	def __init__(self, timeout=None):
		urllib2.HTTPHandler.__init__(self)
		self.timeout = timeout

	def http_open(self, req):
		"""Override http_open."""

		def makeConnection(host, port=None, strict=None):
			return MyHTTPConnection(host, port, strict, \
				timeout = self.timeout)

		return self.do_open(makeConnection, req)

#### END LAZYWEB ####

def get_repo(text):
	"""Gets the repository data from HTML taken from apt-get.org. The
	argument should be a list of HTML"""

	time.sleep(0.1)

	# Show and decrement the counter
	global count
	print str(count)
	count -= 1

	repo = {'deb_lines':[], 'debsrc_lines':[], 'packages':{}}
	for line in text:
		temp = ''
		if ("deb" in line) and \
			("<a href=" in line) and \
			not ("&" in line):
			temp2 = line.split('<a href="',1)[1]
			temp = line.split('<a href="')[0] + temp2[temp2.find('>')+1:]
			temp = temp.split('</a>')[0] + temp.split('</a>',1)[1]
			if '<span class="url' in temp:
				temp = temp.split('<span class="url">')[0]+temp.split('<span class="url">',1)[1]
			if temp.startswith("deb "):
				repo['deb_lines'].append(temp.strip())
			elif temp.startswith("deb-src "):
				repo['debsrc_lines'].append(temp.strip())
		if '<span class="descr">' in line:
			try:
				desc = line[line.find('<span class="descr">'):]
				repo['description'] = (desc[desc.find('>')+1:desc.find('</span')]).strip()
			except Exception, e:
				print e
		if '<a href="/list/?site=' in line:
			url = line.replace('<span class="packages">','')
			url = url.replace('<a href="', '')
			url = url[:url.find('"')]
			# Now let's fetch a URL
			http_handler = MyHTTPHandler(timeout = 20)
			opener = urllib2.build_opener(http_handler)

			req = urllib2.Request('http://www.apt-get.org'+url)
			try:
			    package_page = opener.open(req)
			    parse_package_page(package_page, repo)
			except Exception, e:
			    print e
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
	r = ''
	for line in results_page.readlines():
		r = r + line
	r = r.replace('\n','')
	rs = r.split('<br/>')
	results_list = []
	for part in rs:
		if '</li>' in part:
			results_list.append(part[:part.find('</li>')+5])
			results_list.append(part[part.find('</li>')+5:])
		else:
			results_list.append(part)

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
					current_repo = [line.split('i>',1)[1]]
					in_repo = False
				else:
					current_repo.append(line)
			else:
				if "<li" in line:
					in_repo = True
					current_repo.append(line)

		else:
			if "<ul" in line:
				in_list = True

	# Set the size of our counter
	global count
	count = len(repos)

	repositories = map(get_repo, repos)
	reposxml = Element('repositories')
	outxml = ElementTree(reposxml)
	for repo in repositories:
		current_repo = SubElement(reposxml, 'repository')

		if 'description' in repo.keys():
			desc = SubElement(current_repo, 'description')
			desc.text = XMLescape(repo['description'])

		try:
			for deb in repo['deb_lines']:
				current_binary = SubElement(current_repo, 'line', attrib={'type':'binary'})
				try:
					current_binary.text = deb
				except ValueError:
					print "Couldn't add source " + deb
		except KeyError:
			print "No binaries"

		try:
			for debsrc in repo['debsrc_lines']:
				current_source = SubElement(current_repo, 'line', attrib={'type':'source'})
				try:
					current_source.text = debsrc
				except ValueError:
					print "Couldn't add source " + deb
		except KeyError:
			print "No sources"

		try:
			for arch in repo['archs']:
				current_arch = SubElement(current_repo, 'architecture', attrib={'arch':arch})
		except KeyError:
			print "No archs"

		for arch in repo['packages']:
			for child in current_repo.getchildren():
				if child.tag == 'architecture' and child.get('arch') == arch:
					architecture = child
			if architecture is not None:
				for package in repo['packages'][arch]:
					try:
						p = SubElement(architecture, 'package', attrib={'name':package[0], 'version':package[1]})
					except IndexError:
						print "Didn't add package " + str(package)

	outfile.write(lxml.etree.tostring(outxml, pretty_print=True))

if 'resync' in sys.argv:
	outfile = None
	for arg in sys.argv:
		if arg.startswith('-o='):
			outfile = open(arg[3:], 'w')
	if outfile is None:
		print "No output file specified! Use the option '-o=filename'."
	else:
		apt_get_org(outfile)
