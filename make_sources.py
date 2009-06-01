#!/usr/bin/env python
import hashlib
import sys

def get_identifier(text):
	# Gets a friendly identifier for the given source list text
	# This is the URL, for example
	# deb http://www.debian-multimedia.org stable main
	# Will give "debian-multimedia"
	try:
		for line in text.split("\n"):
			d = False
			if line[:7] == "deb-src":
				ident = line[7:].strip().split(" ")[0].strip()
				d = True
			elif line[:3] == "deb":
				ident = line[3:].strip().split(" ")[0].strip()
				d = True
			if d:
				ident = ident.split('://')[1].strip()
				if '/' in ident:
					ident = ident.split('/')[0].strip()
				ident_list = ident.split('.')
				l = len(ident_list[0])
				for i in ident_list:
					l = max([l, len(i)])
					if len(i) == l and (not i in ["www", "com", "org", "net", "ftp"]):
						to_return = i
				return to_return
	except:
		return ''

def get_repos(text):
	# This splits the given string into a list of repositories delimited
	# by "STARTREPO" and "ENDREPO"
	repos = []
	current_repo = []
	for line in text.split("\n"):
		if "STARTREPO" in line:
			current_repo = []
		elif "ENDREPO" in line:
			repos.append(current_repo)
		else:
			current_repo.append(line)
	return repos

def get_sections(repo):
	# Turns a given list of lines (from a repo definition) and puts the
	# contained values into a dictionary
	features = {}
	current_feature = None
	currently_in = (None, None)
	for line in repo:
		if not line.strip() == "":
			if "END" in line:
				if "DEBS" in line:
					features['deb'] = current_feature
					current_feature = None
				elif "SOURCES" in line:
					features['debsrc'] = current_feature
					current_feature = None
				elif "ARCHS" in line:
					features['archs'] = current_feature
					current_feature = None
				elif "PACKAGES" in line:
					features['packages'] = current_feature
					current_feature = None
			elif "START" in line:
				if "DEBS" in line:
					current_feature = []
					currently_in = ("DEBS", None)
				elif "SOURCES" in line:
					current_feature = []
					currently_in = ("SOURCES", None)
				elif "ARCHS" in line:
					current_feature = []
					currently_in = ("ARCHS", None)
				elif "PACKAGES" in line:
					current_feature = {}
					currently_in = ("PACKAGES", None)
			else:
				if currently_in[0] in ("DEBS", "SOURCES", "ARCHS"):
					current_feature.append(line[2:])
				elif currently_in[0] == "PACKAGES":
					if line.startswith("\t\t\t"):
						current_feature[currently_in[1]].append(line[3:].split(' '))
					elif line.startswith("\t\t"):
						currently_in = (currently_in[0], line[2:])
						try:
							len(current_feature[currently_in[1]])
						except KeyError:
							current_feature[currently_in[1]] = []
	return features

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
	for deb in repo['deb']:
		key = get_args(deb)
		if key in lists.keys():
			lists[key] = lists[key] + "## Binary\n" + deb + "\n"
		else:
			lists[key] = "### AUTOMATICALLY GENERATED SOURCE LIST\n\n## Binary\n" + deb + "\n"
	for debsrc in repo['debsrc']:
		key = get_args(debsrc)
		if key in lists.keys():
			lists[key] = lists[key] + "## Source\n" + debsrc + "\n"
		else:
			lists[key] = "### AUTOMATICALLY GENERATED SOURCE LIST\n\n## Source\n" + debsrc + "\n"
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

	# Split the text into lines for each repo
	repo_text = get_repos(inline)
	# Get a dictionary for each repo, containing its features
	repos = []
	for repo in repo_text:
		repos.append(get_sections(repo))

	# Make a list of sources.list strings from the repo features
	sources = []
	for repo in repos:
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

