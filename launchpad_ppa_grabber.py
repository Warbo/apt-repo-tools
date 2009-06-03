#!/usr/bin/env python
import urllib2
import sys
import lxml.etree
import lxml.html
from lxml.etree import Element, SubElement

def parse_index():
	list_page = urllib2.urlopen('http://ppa.launchpad.net')
	list_list = [line for line in list_page]

	temp = ''
	repos = []
	current_repo = {}
	for x, line in enumerate(list_list):
		if len(list_list) - x < 5:
			return repos
		if '<tr>' in line:
			current_repo = {}
			temp = line[line.find('<a'):line.find('</a>')]
			while temp.endswith('/'):
				temp = temp[:-1]
			while not temp.startswith('"'):
				temp = temp[1:]
			temp = temp[1:]
			current_repo['url'] = temp.split('/">')[0]
			current_repo['name'] = temp.split('">')[1]
			repos.append(current_repo)
			current_repo = {}

def parse_page(name, repo):
	"""Extracts information from a PPA's description page."""
	# Open the page as a HTML document
	try:
		page = urllib2.urlopen('https://launchpad.net/~'+name+'/+archive/ppa')
	except urllib2.HTTPError:
		return
	lines = [line for line in page]
	s = ''
	for line in lines:
		s = s + line

	doc = lxml.html.document_fromstring(s)

	# Get the PPA's title
	for element in doc:
		if element.tag == "head":
			for subelement in element:
				if subelement.tag == "title":
					repo['title'] = subelement.text

	# Get the description
	for x in doc.xpath('//div/@id'):
		if x == 'description':
			for element in x.getparent():
				for subelement in element:
					if subelement.tag == 'p':
						repo['description'] = subelement.text

	for div in doc.xpath('//div/@id'):
		if div == "series-widget-div":
			options = div.getparent().xpath('//option')
			distros = []
			for option in options:
				distros.append(option.get('value'))

	for pre in doc.xpath('//pre/@id'):
		if pre == 'sources-list-entries':
			try:
				repo['lines'] = get_sources(pre.getparent(), distros)
			except UnboundLocalError:
				print "Could not add sources for " + repo['title']

	return repo

def get_sources(element, distros):
	#<pre id="sources-list-entries">
	#deb <a href="http://ppa.launchpad.net/chromium-daily/ppa/ubuntu">http://ppa.launchpad.net/chromium-daily/ppa/ubuntu</a> <span id="series-deb">karmic</span> main
	#deb-src <a href="http://ppa.launchpad.net/chromium-daily/ppa/ubuntu">http://ppa.launchpad.net/chromium-daily/ppa/ubuntu</a> <span id="series-deb-src">karmic</span> main</pre>
	text = lxml.etree.tostring(element)
	text = text.split('>', 1)[1].strip().replace('</pre>','')
	while '<' in text:
		x = text.split('<a href="', 1)
		text = x[0] + x[1][x[1].find('>')+1:]
		text = text.replace('</a>','')
		x = text.split('<span', 1)
		text = x[0] + '::release::' + x[1][x[1].find('</span>')+7:]
	lines = text.split('\n')
	sources = []
	for distro in distros:
		for line in lines:
			sources.append((line.strip().replace('::release::', distro), distro))
	return sources

filename = None
for arg in sys.argv:
	if arg.startswith("-f="):
		filename = arg[3:]

if filename is None:
	print "Please give an output filename with the '-f=something' option."
	sys.exit()

repos1 = parse_index()
repos2 = []
for repo in repos1:
	repos2.append(parse_page(repo['url'], repo))

outxml = Element('repositories')
#print str(repos2)
for repo in repos2:
	if repo is not None:
		current_repo = SubElement(outxml, 'repository')

		current_title = SubElement(current_repo, 'title')
		try:
			current_title.text = repo['title']
		except KeyError:
			pass

		try:
			for line in repo['lines']:
				if line[0].startswith('deb '):
					current_line = SubElement(current_repo, 'line', attrib={'type':'binary', 'release':line[1]})
					current_line.text = line[0]
				elif line[0].startswith('deb-src '):
					current_line = SubElement(current_repo, 'line', attrib={'type':'source', 'release':line[1]})
					current_line.text = line[0]
				else:
					print "Couldn't add source " + line[0]
		except KeyError:
			pass

		current_description = SubElement(current_repo, 'description')
		try:
			current_description.text = repo['description']
		except KeyError:
			pass


outfile = open(filename, 'w')
outfile.write(lxml.etree.tostring(outxml, pretty_print=True))
outfile.close()
