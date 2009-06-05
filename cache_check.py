import sys
import lxml.etree

def exit(message):
	print message
	sys.exit()

def check(root):
	# Check the top-level node
	if root.tag != "repositories":
		return("Top element should be 'repositories', not " + root.tag)

	for repo in root:
		if repo.tag != "repository":
			return("Second level elements should be 'repository', not " + repo.tag)

	for repo in root:
		for child in repo:
			if child.tag == 'architecture':
				try:
					child.get('arch')
				except KeyError:
					return("Architecture with no 'arch' attribute")
				arch = child.get('arch')
				for char in arch:
					if (not char.isalnum()) and (char != '-'):
						return("Invalid architecture " + arch)
				for subchild in child:
					if subchild.tag != 'package':
						return("Architectures only contain 'package' elements, not " + subchild.tag)
					else:
						try:
							subchild.get('name')
						except KeyError:
							return('Package with no name')
						try:
							subchild.get('version')
						except:
							return("Package " + subchild.get('name') + " has no version.")

	return "No errors found"

if __name__ == '__main__':
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
		exit(check(root))
