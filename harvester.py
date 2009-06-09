import sys
import urllib2
import httplib
import socket
import lxml.etree
from lxml.etree import Element, SubElement
import cache_check

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

def get_release(line):
	return line.text.split(' ')[2]

def get_components(line):
	return line.text.split(' ')[3:]

def list_string(l):
	s = ''
	for element in l:
		s = s + str(element) + ' '
	return s[:-1]

def get_source(line):
	# Here we fetch the page
	http_handler = MyHTTPHandler(timeout = 20)
	opener = urllib2.build_opener(http_handler)
	req = urllib2.Request(get_base(line)+'/dists/'+line.get('release')+'/'+line.get('component')+'/source/Sources.gz')
	try:
		opener.open(req)
	except Exception, e:
		print e

## DEBIAN REPOSITORY STRUCTURE (taken from http://www.ibiblio.org/gferg/ldp/giles/repository/repository-2.html )

# deb something.com     stable     main non-free
#     ----base----- -distribution- --components-

#base/dists/distribution/component/binary-all/Packages.gz
#----       ------------ ---------           /admin/binary-packages
#                                            /base/binary-packages
#                                            /comm/binary-packages
#                                            ...
#                                            /Release
#                                 /binary-i386/Packages.gz
#                                             /admin/binary-packages
#                                             /base/binary-packages
#                                             /comm/binary-packages
#                                             ...
#                                             /Release
#                                 /binary-sparc/...
#                                 /binary-arm/...
#                                 /binary-ia86/...
#                                 /source/Sources.gz
#                                         /admin/binary-packages
#                                         /base/binary-packages
#                                         /comm/binary-packages
#                                         ...
#                                         /Release


### EXECUTION STARTS HERE

# Assume we've been given no filename or help option
infile = None
help = False

# Check the commandline arguments
for arg in sys.argv:
	# If we've been asked for help, remember it
	if arg == "-h":
		help = True
	# If we've been given a filename, remember it
	if arg.startswith('-f='):
		infile = arg[3:]

# If asked for help, print the help message and exit
if help:
	h="""This script gathers data about package repositories for Debian
	and its derivatives. It is given a file to process via the option
	"-f=filename". The file should be in the XML-esque format described
	in the README file. This can either be created manually or as
	output from some of the other included scripts.

	"Harvesting" a repository simply means visiting the repository and
	extracting as much information about it as possible, this includes
	source and binary packages, supported distributions, supported
	architectures, package contents and so on. This requires at least
	one "line" element (source or binary) in the input file.

	Once the data is gathered, it is written back to the output file,
	overwriting its previous contents.

	This help is available via the "-h" option."""

	print h
	sys.exit(0)

# If we've not been given a filename, print an error and exit
if infile is None:
	print "Please give a file to harvest with the '-f=filename' option."
	sys.exit(1)

# Put the contents of the given input in to a string
in_file = open(infile, 'r')
in_string = ''
for line in in_file.readlines():
	in_string = in_string + line
in_file.close()

# Attempt to parse the string as XML, exiting if it fails
try:
	repositories = lxml.etree.fromstring(in_string)
except Exception, e:
	print e
	sys.exit(1)

# Check the XML (using cache_check.py) and exit on errors
ok = cache_check.check(repositories)
if ok != "No errors found":
	print ok
	sys.exit(1)

for repository in repositories:
	for child in repository:
		if child.tag == "line":
			if 'release' not in child.keys():
				child.set('release', get_release(child))

			if 'component' not in child.keys():
				done = False
				for component in get_components(child):
					if not done:
						child.set('component', component)
						done = True
					else:
						new_child = child.__copy__()
						new_child.set('component', component)
						child.getparent.append(new_child)

print lxml.etree.tostring(repositories)
