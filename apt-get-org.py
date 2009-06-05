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

	# Don't tax the server too much
	time.sleep(0.1)

	# Show and decrement the counter
	global count
	print str(count)
	count -= 1

	# Our repo needs two lists and a dictionary initialised
	repo = {'deb_lines':[], 'debsrc_lines':[], 'packages':{}}

	# Walk through the given HTML
	for line in text:

		# This finds the sources.list lines, either "deb " or "deb-src "
		# NOTE: This must skip descriptions containing "deb"
		if ("deb" in line) and \
			("<a href=" in line) and \
			not ("&" in line):

			# Take links out of the line
			temp2 = line.split('<a href="',1)[1]
			temp = line.split('<a href="')[0] + temp2[temp2.find('>')+1:]
			temp = temp.split('</a>')[0] + temp.split('</a>',1)[1]

			# Take "span" elements out of the line
			if '<span class="url' in temp:
				temp = temp.split('<span class="url">')[0]+temp.split('<span class="url">',1)[1]

			# Find binary lines
			if temp.startswith("deb "):
				repo['deb_lines'].append(temp.strip())

			# Find source lines
			elif temp.startswith("deb-src "):
				repo['debsrc_lines'].append(temp.strip())

		# This finds repository descriptions
		if '<span class="descr">' in line:
			try:
				# Simply takes the content inside the span element
				desc = line[line.find('<span class="descr">'):]
				repo['description'] = (desc[desc.find('>')+1:desc.find('</span')]).strip()
			except Exception, e:
				print e

		# This finds a link to a repository's description page
		if '<a href="/list/?site=' in line:
			url = line.replace('<span class="packages">','')
			url = url.replace('<a href="', '')
			url = url[:url.find('"')]
			# Here we fetch the page
			http_handler = MyHTTPHandler(timeout = 20)
			opener = urllib2.build_opener(http_handler)
			req = urllib2.Request('http://www.apt-get.org'+url)

			# Now we parse this page too
			try:
				package_page = opener.open(req)
				parse_package_page(package_page, repo)
			except Exception, e:
				print e

	# Give back the now complete repo data
	return repo

def parse_package_page(page, repo):
	"""Finds properties about a repository from the page given (a
	repository description page from apt-get.org) and gives the
	properties to the repo supplied."""
	# replace_links replaces "<a href=A_URL>text</a>" with "text (A_URL)"
	def replace_links(text):
		if '<a' in text and 'href=' in text:
			# Recurse if more links are found
			to_return = text.split('<a href=')[0] + text.split('<a href=')[1].split('>')[1][:-3] + " (" + text.split('href=')[1].split('>')[0] + ")" + replace_links(text.split("</a>",1)[1])
		else:
			# Escape the recursion
			to_return = text

		return to_return

	# name_version splits a string in two at a space
	def name_version(text):
		return text.split(' ')

	# check_arch removes architectures with invalid characters
	def check_arch(arch):
		ok = True
		# This list probably needs expanding upon
		for char in ["'", '"', "<", ">", "&"]:
			if char in arch:
				ok = False
		return ok

	# Walk through the repository page
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
	# Split it into lines based on line break elements
	r = ''
	for line in results_page.readlines():
		r = r + line
	r = r.replace('\n','')
	rs = r.split('<br/>')

	# Break apart lines containing <li> and </li> into two
	results_list = []
	for part in rs:
		if '</li>' in part:
			results_list.append(part[:part.find('</li>')+5])
			results_list.append(part[part.find('</li>')+5:])
		else:
			results_list.append(part)

	### Parse the resulting lines

	## Initialise some state for the parser
	# in_list is true when we're reading lines from the repo list
	in_list = False
	# in_repo is true when we're reading a repository description
	in_repo = False
	# repos holds the repositories we're making
	repos = []
	# current_repo is the one we're building at any given time
	current_repo = []

	# Walk through the lines
	for line in results_list:

		# Parse the repository list
		if in_list:

			# Check for the end of the repository list
			if "</ul" in line:
				in_list = False

			# Parse a repository description
			if in_repo:

				# Check for the end of this repository description
				if "</li>" in line:
					# Add the finished repo lines to the list
					repos.append(current_repo)
					# Start a new one containing the end of this line
					current_repo = [line.split('i>',1)[1]]
					# Exit the repository description
					in_repo = False

				# If we're not at the end then add this line to the repo
				else:
					current_repo.append(line)

			# Otherwise look for the start of a repository description
			else:
				if "<li" in line:
					in_repo = True
					current_repo.append(line)

		# Otherwise look for the start of the repository list
		else:
			if "<ul" in line:
				in_list = True

	# Now we have a set of repos, each of which contains the lines
	# describing it

	# Set the size of our counter from the number we've found
	global count
	count = len(repos)

	# Extract the information we want from these lines
	repositories = map(get_repo, repos)

	# Set up the output data
	reposxml = Element('repositories')
	outxml = ElementTree(reposxml)

	# Step through each dictionary of repository data
	for repo in repositories:

		# Make a repository element to contain this data
		current_repo = SubElement(reposxml, 'repository')

		# Add a description element if we have a desciption
		if 'description' in repo.keys():
			desc = SubElement(current_repo, 'description')
			desc.text = XMLescape(repo['description'])

		# Add every binary sources.list line
		try:
			for deb in repo['deb_lines']:
				current_binary = SubElement(current_repo, 'line', attrib={'type':'binary'})
				try:
					current_binary.text = deb
				except ValueError:
					print "Couldn't add source " + deb
		except KeyError:
			print "No binaries"

		# Add every source sources.list line
		try:
			for debsrc in repo['debsrc_lines']:
				current_source = SubElement(current_repo, 'line', attrib={'type':'source'})
				try:
					current_source.text = debsrc
				except ValueError:
					print "Couldn't add source " + deb
		except KeyError:
			print "No sources"

		# Add every supported architecture
		try:
			for arch in repo['archs']:
				current_arch = SubElement(current_repo, 'architecture', attrib={'arch':arch})
		except KeyError:
			print "No archs"

		# Go through the packages, grouped per architecture
		for arch in repo['packages']:

			# Look for a corresponding architecture element
			for child in current_repo.getchildren():
				if child.tag == 'architecture' and child.get('arch') == arch:
					architecture = child

			# If we have one then add each package to it
			if architecture is not None:
				for package in repo['packages'][arch]:
					try:
						p = SubElement(architecture, 'package', attrib={'name':package[0], 'version':package[1]})
					except IndexError:
						print "Didn't add package " + str(package)

	# Now write this XML to the given output file
	outfile.write(lxml.etree.tostring(outxml, pretty_print=True))

### EXECUTION STARTS HERE

# See if we've been told to download the data again
if 'resync' in sys.argv:

	# If so then check if an output has been specified
	outfile = None
	for arg in sys.argv:
		if arg.startswith('-o='):
			outfile = open(arg[3:], 'w')

	# If not then exit
	if outfile is None:
		print "No output file specified! Use the option '-o=filename'."

	# Otherwise scrape the data into the given file
	else:
		apt_get_org(outfile)
