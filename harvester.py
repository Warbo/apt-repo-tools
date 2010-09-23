import sys
import urllib2
import httplib
import socket
import lxml.etree
from lxml.etree import Element, SubElement
import cache_check
import StringIO
import gzip
import bz2

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

def get_base(line):
	if line.text.split(' ')[1] is not None:
		return line.text.split(' ')[1]
	return ''

def get_release(line):
	if line.text.split(' ')[2] is not None:
		return line.text.split(' ')[2]
	return ''

def get_components(line):
	if line.text.split(' ')[3:] is not None:
		return line.text.split(' ')[3:]
	return ['']

def list_string(l):
	s = ''
	for element in l:
		s = s + str(element) + ' '
	return s[:-1]

def get_source(line):
	# Here we fetch the page
	http_handler = MyHTTPHandler(timeout = 20)
	opener = urllib2.build_opener(http_handler)
	req = urllib2.Request(get_base(line)+'/dists/'+line.get('release')+'/'+line.get('component')+'/source/Sources.bz2')
	try:
		f = opener.open(req)
		compresseddata = f.read()
		compressedstream = StringIO.StringIO(compresseddata)
		bzipper = bz2.BZ2File(fileobj=compressedstream)
		data = bzipper.read()
		return data
	except Exception, e:
		pass
	req = urllib2.Request(get_base(line)+'/dists/'+line.get('release')+'/'+line.get('component')+'/source/Sources.gz')
	try:
		f = opener.open(req)
		compresseddata = f.read()
		compressedstream = StringIO.StringIO(compresseddata)
		gzipper = gzip.GzipFile(fileobj=compressedstream)
		data = gzipper.read()
		return data
	except Exception, e:
		pass
	req = urllib2.Request(get_base(line)+'/dists/'+line.get('release')+'/'+line.get('component')+'/source/Sources')
	f = opener.open(req)
	data = f.read()
	return data

def get_binary(line, arch):
	url = get_base(line)+'/dists/'+line.get('release')+'/'+line.get('component')+'/binary-'+arch+'/Packages'
	# Here we fetch the page
	http_handler = MyHTTPHandler(timeout = 20)
	opener = urllib2.build_opener(http_handler)
	req = urllib2.Request(url+'.bz2')
	try:
		f = opener.open(req)
		compresseddata = f.read()
		compressedstream = StringIO.StringIO(compresseddata)
		bzipper = bz2.BZ2File(fileobj=compressedstream)
		data = bzipper.read()
		return data
	except Exception, e:
		pass
	req = urllib2.Request(url+'.gz')
	try:
		f = opener.open(req)
		compresseddata = f.read()
		compressedstream = StringIO.StringIO(compresseddata)
		gzipper = gzip.GzipFile(fileobj=compressedstream)
		data = gzipper.read()
		return data
	except Exception, e:
		pass
	req = urllib2.Request(url)
	f = opener.open(req)
	data = f.read()
	return data

def parse_package(package_strings):
	##FORMAT
	#Package: 3dchess
	#Binary: 3dchess
	#Version: 0.8.1-11
	#Priority: optional
	#Section: games
	#Maintainer: Stephen Stafford <bagpuss@debian.org>
	#Build-Depends: debhelper, xaw3dg-dev, xlibs-dev
	#Architecture: any
	#Standards-Version: 3.5.9.0
	#Format: 1.0
	#Directory: pool/main/3/3dchess
	#Files:
	# ee24555acce059e14a8756cd5635593a 580 3dchess_0.8.1-11.dsc
	# 5390c60953446e541d9455d9c4e38ca1 46371 3dchess_0.8.1.orig.tar.gz
	# 9eac46d2c1664dd09b1e0c9d5e7a72ae 4747 3dchess_0.8.1-11.diff.gz
	if len(package_strings) == 0:
		raise ValueError()
	package = {}
	for line in package_strings:
		if 'Package:' in line \
			or 'Architecture:' in line \
			or 'Version:' in line:
			cpy = line
			cpy = cpy.strip()
			sections = cpy.split(':')
			package[sections[0].strip()] = sections[1].strip()

	return package

def split_source(text):
	packs = []
	current_pack = []
	for line in text.split('\n'):
		if line.strip() == '':
			packs.append(current_pack)
			current_pack = []
		else:
			current_pack.append(line)
	packs.append(current_pack)
	return packs

def split_binary(text):
	return split_source(text)

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

count = len(repositories.findall('repository'))

# Go through each repository and flesh it out
for repository in repositories:
	print str(count)
	count -= 1

	# Look for source lines
	for child in repository:
		if child.tag == "line":
			# Add the release if it's not set
			if 'release' not in child.keys():
				child.set('release', get_release(child))

			# Add the component if it's not set (copy lines with > 1)
			if 'component' not in child.keys():
				done = False
				for component in get_components(child):
					if not done:
						child.set('component', component)
						done = True
					else:
						new_child = child.__copy__()
						new_child.set('component', component)
						child.getparent().append(new_child)

			# If this is a source line then add source packages to the all architecture
			if child.get('type') == 'source':
				# Assume we have no 'all' architecture
				source_arch = None
				# Look for one
				for arch in repository.findall('architecture'):
					if arch.get('arch') == 'all':
						source_arch = arch
				# If we didn't find one, make one'
				if source_arch is None:
					source_arch = SubElement(repository, 'architecture', attrib={'arch':'all'})

				# Grab the repository's Sources(.gz/.bz2) file
				# decompress it if necessary and split into dictionaries
				# based on the contents
				try:
					src = get_source(child)
					for package in split_source(src):
						try:
							pack = None
							p = parse_package(package)
							for child in source_arch.findall('package'):
								if child.get('name') == p['package']:
									pack = child
							if pack == None:
								pack = SubElement(source_arch, 'package')
							pack.set('type', 'source')
							for key in p.keys():
								if key == 'package':
									pack.set('name', p[key])
								else:
									pack.set(key, p[key])
						except KeyError:
							pass
						except ValueError:
							pass
				except urllib2.URLError:
					print "Couldn't get source'"
				except IOError:
					print "Couldn't get source"

			# If this is a binary line then add binary packages to the relevant architectures
			elif child.get('type') == 'binary':
				# Go through each of the repository's supported architectures'
				for arch in repository.findall('architecture'):
					# Grab the appropriate Packages(.bz2/gz) file and split
					# it into dictionaries of package properties
					try:
						bins = get_binary(child, arch.get('arch'))
						for package in split_binary(bins):
							try:
								p = parse_package(package)
								pack = None
								for child in arch.findall('package'):
									if child.get('name') == p['package']:
										pack = child
								if pack is None:
									pack = SubElement(arch, 'package')
								pack.set('type', 'binary')
								for key in p.keys():
									if key == 'package':
										pack.set('name', p[key])
									else:
										pack.set(key, p[key])
							except KeyError:
								pass
							except ValueError:
								pass
					except urllib2.URLError:
						print "Couldn't get Package file"
					except IOError:
						print "Couldn't get Package file"

outfile = open('OUT', 'w')
outfile.write(lxml.etree.tostring(repositories))
outfile.close()
