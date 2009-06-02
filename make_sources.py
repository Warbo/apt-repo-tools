#!/usr/bin/env python
import hashlib
import lxml.etree
import sys

def get_identifier(line):
	# Gets a friendly identifier for the given source list text
	# This is the URL, for example
	# deb http://www.debian-multimedia.org stable main
	# Will give "www-debian-multimedia-org-stable-main"
	id = line.split('://')[1]
	id = id.replace(' ', '-')
	id = id.replace(':', '-')
	id = id.replace('/', '-')
	to_return = ''
	for char in id:
		if (not char.isalnum()) and (char != '-'):
			to_return = to_return + '-'
		else:
			to_return = to_return + char
	while to_return.endswith('-'):
		to_return = to_return[:-1]
	while to_return.startswith('-'):
		to_return = to_return[1:]
	id = ''
	count = 0
	for char in to_return:
		if char == '-':
			if count > 0:
				count += 1
			else:
				id = id + char
				count += 1
		else:
			count = 0
			id = id + char
	return id.lower().strip()

def get_repos(repos):
	# This splits the given element into a list of repository elements
	to_return = []
	for child in repos:
		if child.tag == 'repository':
			to_return.append(child)
	return to_return

def get_args(line):
	# Gets the values following a deb or deb-src line's URL
	if "deb-src" in line:
		args = line[8:]
	elif "deb" in line:
		args = line[4:]
	args = args.split(' ', 1)[1]
	return args.strip()

def make_source_lists(repo):
	# Returns a list of strings, representing the possible sources which
	# the given repo dictinary could provide
	lists = {}
	handled_args = []
	for deb in repo.findall('line'):
		key = get_args(deb.text)
		if key not in lists.keys():
			lists[key] = "### AUTOMATICALLY GENERATED SOURCE LIST\n\n"
		if deb.get('type') == "binary":
			lists[key] = lists[key] + "## Binary\n" + deb.text + "\n"
		elif deb.get('type') == "source":
			lists[key] = lists[key] + "## Source\n" + deb.text + "\n"
	return lists.values()

# Get a file to read
infile = None
for arg in sys.argv:
	if arg.startswith("-f="):
		infile = open(arg[3:], 'r')
if infile is None:
	print "Please supply a file to check using the -f=something option"
else:

	# Get the text from the input file
	inline = ""
	for line in infile.readlines():
		inline = inline + line

	# Get the XML root
	root = lxml.etree.fromstring(inline)

	# Make a list of sources.list strings from the repo features
	sources = []
	for repo in root:
		sources.extend(make_source_lists(repo))

	# Write out the source files
	for source in sources:
		if not source.strip() == "":
			m = hashlib.md5()
			m.update(source)
			hash = m.hexdigest()
			if get_identifier(source) is None:
				print source
			f = open('temp/lists/'+get_identifier(source)+'_'+hash+'.list', 'w')
			f.write(source)
			f.close()
