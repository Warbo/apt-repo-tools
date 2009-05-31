import sys

infile = None
for arg in sys.argv:
	if arg.startswith("-f="):
		infile = open(arg[3:])
if infile is None:
	print "Please specify a file to check with '-f=filename'"
else:
	currently_in = ["FILE"]
	for x, line in enumerate(infile.readlines()):
		n = x+1		# Lines start at 1, enumerate starts at 0
		# Escape sections
		if "ENDREPO" in line:
			if not currently_in[-1] == "REPO":
				print "line "+str(n)+": ENDREPO used out of scope."
				sys.exit(1)
			currently_in.pop()
		elif "ENDDEBS" in line:
			if not currently_in[-1] == "DEBS":
				print "line "+str(n)+": ENDDEBS used out of scope."
				sys.exit(1)
			currently_in.pop()
		elif "ENDSOURCES" in line:
			if not currently_in[-1] == "SOURCES":
				print "line "+str(n)+": ENDSOURCES used out of scope."
				sys.exit(1)
			currently_in.pop()
		elif "ENDARCHS" in line:
			if not currently_in[-1] == "ARCHS":
				print "line "+str(n)+": ENDARCHS used out of scope."
				sys.exit(1)
			currently_in.pop()
		elif "ENDPACKAGES" in line:
			if (not currently_in[-1] == "PACKAGES") and (not currently_in[-1] == "PACKARCH"):
				print "line "+str(n)+": ENDPACKAGES used out of scope."
				sys.exit(1)
			if currently_in[-1] == "PACKAGES":
				currently_in.pop()
			elif currently_in[-1] == "PACKARCH":
				currently_in.pop()
				currently_in.pop()

		# Check contents
		if not line.strip() == "":
			if currently_in[-1] == "FILE":
				if (not "START" in line) and (not "END" in line) or (not "REPO" in line):
					print "line "+str(n)+": Line doesn't belong in top level."
					sys.exit(1)
				if line[0] == "\t":
					print "line "+str(n)+": Wrong indentation (should be none)"
					sys.exit(1)
			elif currently_in[-1] == "REPO":
				if (not "START" in line) and (not "END" in line):
					print "line "+str(n)+": Line doesn't belong at repo level."
					sys.exit(1)
				if (not line[0] == "\t") or (line[1] == "\t"):
					print "line "+str(n)+": Wrong indentation (should be 1 tab)"
					sys.exit(1)
			elif currently_in[-1] == "DEBS":
				if (not line[:2] == "\t\t") or (line[2] == "\t"):
					print "line "+str(n)+": Wrong indentation (should be 2 tabs)"
					sys.exit(1)
				elif not line.strip()[:4] == "deb ":
					print "line "+str(n)+": Deb lines must begin 'deb '"
					sys.exit(1)
				for char in ["&", "<", ">", "'", '"']:
					if char in line:
						print "line "+str(n)+": Deb lines cannot contain &, <, >, ' or "+'"'
						sys.exit(1)
			elif currently_in[-1] == "SOURCES":
				if (not line[:2] == "\t\t") or (line[2] == "\t"):
					print "line "+str(n)+": Wrong indentation (should be 2 tabs)"
					sys.exit(1)
				elif not line.strip()[:8] == "deb-src ":
					print "line "+str(n)+": Source lines must begin 'deb-src '"
					sys.exit(1)
				for char in ["&", "<", ">", "'", '"']:
					if char in line:
						print "line "+str(n)+": Source lines cannot contain &, <, >, ' or "+'"'
						sys.exit(1)
			elif currently_in[-1] == "ARCHS":
				if " " in line.strip():
					print "line "+str(n)+": Arch lines must contain one word"
					sys.exit(1)
				for char in ["&", "<", ">", "'", '"']:
					if char in line:
						print "line "+str(n)+": Arch lines cannot contain &, <, >, ' or "+'"'
						sys.exit(1)
			elif currently_in[-1] == "PACKARCH":
				if (not line[:3] == "\t\t\t") or (line[3] == "\t"):
					if line[:2] == "\t\t":
						currently_in.pop()
					else:
						print "line "+str(n)+": Wrong indentation (should be 3 tabs)"
						sys.exit(1)
				elif not len(line.strip().split(" ")) == 2:
					print "line "+str(n)+": Packages must have a name and a version, space separated"
					sys.exit(1)
				else:
					for char in ["&", "<", ">", "'", '"']:
						if char in line:
							print "line "+str(n)+": Packages cannot contain &, <, >, ' or "+'"'
							sys.exit(1)
			if currently_in[-1] == "PACKAGES":
				if (not line[:2] == "\t\t") or (line[2] == "\t"):
					print "line "+str(n)+": Wrong indentation (should be 2 tabs)"
					sys.exit(1)
				if " " in line.strip():
					print "line "+str(n)+": Package architectures must be one word"
					sys.exit(1)
				for char in ["&", "<", ">", "'", '"']:
					if char in line:
						print "line "+str(n)+": Package architectures cannot contain &, <, >, ' or "+'"'
						sys.exit(1)
				currently_in.append("PACKARCH")

		# Enter sections
		if "STARTREPO" in line:
			if not currently_in[-1] == "FILE":
				print "line "+str(n)+": Repo started within another section."
				sys.exit(1)
			currently_in.append("REPO")

		elif "STARTDEBS" in line:
			if not currently_in[-1] == "REPO":
				print "line "+str(n)+": Deb lines started within another section."
				sys.exit(1)
			currently_in.append("DEBS")

		elif "STARTSOURCES" in line:
			if not currently_in[-1] == "REPO":
				print "line "+str(n)+": Source lines started within another section."
				sys.exit(1)
			currently_in.append("SOURCES")

		elif "STARTARCHS" in line:
			if not currently_in[-1] == "REPO":
				print "line "+str(n)+": Arch lines started within another section."
				sys.exit(1)
			currently_in.append("ARCHS")

		elif "STARTPACKAGES" in line:
			if not currently_in[-1] == "REPO":
				print "line "+str(n)+": Package lines started within another section."
				sys.exit(1)
			currently_in.append("PACKAGES")

	print "No errors found"
