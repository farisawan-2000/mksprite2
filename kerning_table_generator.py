def get_kerning_table(name):
	ret = ""
	ret += "char %s_kerning_table = {\n" % name
	ret += "\t// unprintable characters\n"
	ret += "\t8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,\n"
	ret += "\t8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,\n\n"
		
	for i in range(32, 127):
		ret += "\t/* %c */  8,\n" % i
	ret += "};\n"
	return ret