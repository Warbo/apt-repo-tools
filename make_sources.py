#!/usr/bin/env python

def get_repos(text):
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
	if "deb-src" in line:
		args = line[8:]
	elif "deb" in line:
		args = line[4:]
	args = args.split(' ', 1)[1]
	return args.strip()

def make_source_lists(repo):
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

infile = open("cache.txt", "r")
inline = ""
for line in infile.readlines():
	inline = inline + line

repo_text = get_repos(inline)
repos = []
for repo in repo_text:
	repos.append(get_sections(repo))

sources = []
for repo in repos:
	sources.extend(make_source_lists(repo))

for source in sources:
	print source
