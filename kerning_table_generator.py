from PIL import Image, GifImagePlugin
import sys, os

def get_image_width(fname):
	arr = []
	earliest_start = []
	with Image.open(fname) as img:
		width, height = img.size
		for i in range(height):
			a1 = [img.getpixel((o, i)) for o in range(width)]
			a2 = a1[::-1]
			start = -1
			end = -1
			for l in range(width):
				if a1[l][-1] != 0:
					earliest_start.append(l)
					start = l
					break
			for l in range(width):
				if a2[l][-1] != 0:
					end = width - l
					break
			if start == -1 or end == -1:
				arr.append(0)
			else:
				arr.append(end - start)



	toReturn = max(arr)
	if toReturn == 0:
		return width / 2
	return toReturn + 1 + min(earliest_start)
				



def get_kerning_table(name, idir):
	ret = ""
	ret += "char %s_kerning_table[] = {\n" % name
	ret += "\t// unprintable characters\n"
	ret += "\t8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,\n"
	ret += "\t8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8,\n\n"
		
	for i in range(32, 127):
		ret += "\t/* %c */  %d,\n" % (i, get_image_width(idir+str(i)+".png"))
	ret += "};\n"
	return ret

print(get_kerning_table(sys.argv[1], sys.argv[2]))