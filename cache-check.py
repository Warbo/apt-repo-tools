import sys
import lxml.etree

def exit(message):
	print message
	sys.exit(1)

# READ INPUT
infile = None
for arg in sys.argv:
	if arg.startswith("-f="):
		infile = open(arg[3:])
if infile is None:
	print "Please specify a file to check with '-f=filename'"
else:
	instring = ''
	for line in infile.readlines():
		instring = instring + line

	# FINISH READING INPUT

	# See if we're dealing with an XML document
	try:
		root = lxml.etree.fromstring(instring)
	except Exception, e:
		print e
		exit("Could not read input as XML.")

	# Check the top-level node
	if root.tag != "repositories":
		exit("Top element should be 'repositories', not " + root.tag)

	for repo in root:
		if repo.tag != "repository":
			exit("Second level elements should be 'repository', not " + repo.tag)

	for repo in root:
		for child in repo:
			if child.tag == 'architecture':
				try:
					child.get('arch')
				except KeyError:
					exit("Architecture with no 'arch' attribute")
				arch = child.get('arch')
				for char in arch:
					if (not char.isalnum()) and (char != '-'):
						exit("Invalid architecture " + arch)
				for subchild in child:
					if subchild.tag != 'package':
						exit("Architectures only contain 'package' elements, not " + subchild.tag)
					else:
						try:
							subchild.get('name')
						except KeyError:
							exit('Package with no name')
						try:
							subchild.get('version')
						except:
							exit("Package " + subchild.get('name') + " has no version.")

	print "No errors found"
