#!/usr/bin/env python
import hashlib
import lxml.etree
#import sys

def get_identifier(line):
	"""Gets a friendly identifier for the given source list text
	This is the URL, for example
	deb http://www.debian-multimedia.org stable main
	Will give "www-debian-multimedia-org-stable-main" """

	# Get rid of the protocol, we only want the host
	id = line.split('://')[1]

	# Don't use spaces
	id = id.replace(' ', '-')
	# or colons
	id = id.replace(':', '-')
	# or slashes
	id = id.replace('/', '-')

	# Now do a more thorough check, building the output character by character
	to_return = ''
	for char in id:
		# We want letters, numbers and hyphens
		if (not char.isalnum()) and (char != '-'):
			# Otherwise use a hyphen
			to_return = to_return + '-'
		else:
			to_return = to_return + char
	# However, we don't want to start or end with garbage
	while to_return.endswith('-'):
		to_return = to_return[:-1]
	while to_return.startswith('-'):
		to_return = to_return[1:]

	# Now that we've got a valid string, we'd also like it to be pretty
	id = ''
	count = 0
	# Go through each character again
	for char in to_return:
		# Notice hyphens
		if char == '-':
			# Don't bother remembering it if we've just seen one
			if count > 0:
				count += 1
			# Otherwise remember it, and remember that we've just seen one
			else:
				id = id + char
				count += 1
		# Remember non-hyphen characters and allow hyphens to come after
		else:
			count = 0
			id = id + char
	# Now return what we end up with
	return id.lower().strip()

def get_repos(repos):
	"""This splits the given element into a list of repository elements"""
	to_return = []		# This will hold our findings
	# Loop through the given repository's elements 
	for child in repos:
		# Add any repositories we find to the list
		if child.tag == 'repository':
			to_return.append(child)
	# Return the list
	return to_return

def get_args(line):
	"""Gets the values following a deb or deb-src line's URL"""
	# Split off "deb-src " from the start of a sources.list line
	if "deb-src" in line:
		args = line[8:]
	# Split off "deb " from the start of a sources.list line
	elif "deb" in line:
		args = line[4:]
	# Now break off the next word and discard it
	args = args.strip().split(' ', 1)[1]
	# Return what's left
	return args.strip()

def make_source_lists(repo):
	"""Returns a list of strings, representing the possible sources which
	the given repo dictinary could provide"""
	lists = {}
	handled_args = []
	# Grab sources.list lines for this repo
	for deb in repo.findall('line'):
		# See which distros, releases and components this provides
		key = get_args(deb.text)
		# See if we've found this combination before
		if key not in lists.keys():
			# If not then give a suitable header
			lists[key] = "### AUTOMATICALLY GENERATED SOURCE LIST\n\n"
		# Then follow it by the appropriate line
		if deb.get('type') == "binary":
			lists[key] = lists[key] + "## Binary\n" + deb.text + "\n"
		elif deb.get('type') == "source":
			lists[key] = lists[key] + "## Source\n" + deb.text + "\n"
	# Give back all of the sets of repo lines
	return lists.values()

# If we've been called as a program (as opposed to being imported as a module)
# then run the following
if __name__ == '__main__':
	# Get a file to read
	import sys		# For reading our arguments
	infile = None		# This will be our input file
	# Look for an argument of the form "-f=filename"
	for arg in sys.argv:
		if arg.startswith("-f="):
			# Open the specified filename
			infile = open(arg[3:], 'r')
	# If we reach here without a file, we've not been called correctly
	if infile is None:
		print "Please supply a file to check using the -f=something option"

	# Otherwise we're good to go
	else:
	
		# Get all of the text from the input file
		inline = "".join(infile.readlines())
	
		# Get the XML root
		root = lxml.etree.fromstring(inline)
	
		# Make a list of sources.list strings from the repo features
		sources = []
		for repo in root:
			sources.extend(make_source_lists(repo))
	
		# Write out the source files
		for source in sources:
			# Only act if we've got something to write
			if not source.strip() == "":
				# To keep conflicts to a minimum we add a hash to the filename
				m = hashlib.md5()
				m.update(source)
				hash = m.hexdigest()
				# We have to give up on repos which we can't name!
				if get_identifier(source) is None:
					print source
				# Otherwise we write a temporary sources.list file
				f = open('temp/lists/'+get_identifier(source)+'_'+hash+'.list', 'w')
				# Fill it with repo data
				f.write(source)
				# Then finish
				f.close()
	
