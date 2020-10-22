from PIL import Image
import argparse
import sys, os
try:
    import argcomplete  # type: ignore
except ModuleNotFoundError:
    argcomplete = None



parser = argparse.ArgumentParser(
    description="Makes a sprite or bgrect object compatible with N64 S2DEX microcodes.\n"+
    "N.I. stands for \"Not Implemented\""
)

parser.add_argument(
    "-i",
    dest="input_file",
    help="Input file (MUST be a .png). If a folder is specified, defaults to animation mode.",
    required=True,
)

parser.add_argument(
    "-o",
    dest="output_file",
    help="Output file (Stores texture data, and the S2DEX structure)",
    required=True,
)

parser.add_argument(
	"-c",
    "--create-dl",
    dest="create_dl",
    action="store_true",
    help="Creates a simple displaylist to render the sprite or bg",
)

parser.add_argument(
	"-n",
    "--name",
    dest="sprite_name",
    help="Sprite/BGRect object name (Defaults to 'sprite')",
    default="sprite",
)

parser.add_argument(
	"-a",
    "--autoresize",
    dest="autoresize",
    action="store_true",
    help="(N.I.) If a sprite/object isn't sized correctly for LoadBlock, resize it automatically",
)


if argcomplete:
    argcomplete.autocomplete(parser)



args = parser.parse_args()


mode = 0


# Make sure paths are correct
if os.path.isdir(args.input_file):
    mode = 1
elif not os.path.isfile(args.input_file):
    raise Exception("Input file is not a file or directory")

width = 0
height = 0

# TODO: implement image resizing if not in these widths (or just use loadtile???)
valid_loadblock_widths = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 64, 72, 76, 100, 108, 128, 144, 152, 164, 200, 216, 228, 256, 304, 328, 432, 456, 512, 684, 820, 912]

def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))] 

clamp = lambda x : (int(x) & 0x1F)

hs = lambda x : str(hex(x))

ls = lambda x : [name for name in os.listdir(args.input_file)]

def to5551(t):
	r = (t[0] / 255) * 31
	g = (t[1] / 255) * 31
	b = (t[2] / 255) * 31
	a = 0
	if len(t) == 4:
		if t[3] == 255:
			a = 1
	return ((clamp(r) << 11)) | (clamp(g) << 6) | (clamp(b) << 1) | a


img_count = 0

def get_image_sym(i, x):
	return str(i)+"_tex_"+str(x)
def get_obj_sym(i):
	return str(i)+"_obj"
def get_image_header(i):
	return "ALIGNED8 u16 "+get_image_sym(i, img_count)+"[] = {"



def handle_mode_0(infile):
	global width
	global height
	imstr = "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	imstr+=get_image_header(args.sprite_name)
	with Image.open(infile) as img:
		width, height = img.size
		# if width not in valid_loadblock_widths:
		# 	x = input("Warning: image doesn't have a valie LoadBlock width. Resize? [Y/N]")
		# 	if x.upper() in ["Y","N"]:
		# 		if x.upper() == "Y":
		# 			img = img.thumbnail()
		# 		else:
		# print(width,height)
		# print(img.getpixel((width-1,height-1)))
		for i in range(height):
			for j in range(width):
				imstr+= ("0x%04X" % to5551(img.getpixel((j, i))))+", "

	imstr+= "};"
	return imstr

def handle_mode_1(infile):
	global width
	global height
	imstr=get_image_header(args.sprite_name)
	with Image.open(args.input_file+infile) as img:
		width, height = img.size
		for i in range(height):
			for j in range(width):
				imstr+= ("0x%04X" % to5551(img.getpixel((j, i))))+", "

	imstr+= "};"
	return imstr


def make_textures(count):
	global img_count
	imstr = "\n\n"
	imstr += "uObjTxtr "+args.sprite_name+"_tex%s =\n" % ''.join('[]' if count > 1 else '')
	if count > 1:
		imstr += "{\n"
	while count > 0:
		imstr+="\n".join(["    {",
		"        G_OBJLT_TXTRBLOCK,                  /* type    */",
		"        (u64 *)&%s,               /* image   */" % get_image_sym(args.sprite_name, img_count - count),
		"        GS_PIX2TMEM(0,      G_IM_SIZ_16b),  /* tmem    */",
		"        GS_TB_TSIZE(%d*%d,  G_IM_SIZ_16b),  /* tsize   */" % (width, height),
		"        GS_TB_TLINE(%d,     G_IM_SIZ_16b),  /* tline   */" % width,
		"        0,                                  /* sid     */",
		"        (u32)&%s,                 /* flag    */" % get_image_sym(args.sprite_name, img_count - count),
		"        -1                                  /* mask    */",
		"    }%s\n" % ''.join([',' if count > 1 else '\n};'])])
		count -= 1

	if count > 1:
		imstr += "};\n"
	return imstr

def make_obj():
	imstr = "\n\n"
	imstr+="uObjSprite "+args.sprite_name+"_obj =\n"
	imstr+="\n".join(["    {",
	"        0<<2, 1<<10, %d<<5, 0,        /* objX, scaleX, imageW, paddingX */\n" % width,
	"        0<<2, 1<<10, %d<<5, 0,        /* objY, scaleY, imageH, paddingY */" % height,
	"        GS_PIX2TMEM(32, G_IM_SIZ_16b),    /* imageStride */",
	"        GS_PIX2TMEM(0, G_IM_SIZ_16b),     /* imageAdrs   */",
	"        G_IM_FMT_RGBA,            /* imageFmt    */",
	"        G_IM_SIZ_16b,             /* imageSiz    */",
	"        0,                    /* imagePal    */",
	"        0                 /* imageFlags  */",
	"    };\n"])
	return imstr




output_buffer = ""
if mode == 0:
	output_buffer += handle_mode_0(args.input_file)
	print(width, height)
	output_buffer += make_textures(1)
	output_buffer += make_obj()
else:
	output_buffer += "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	for i in ls(args.input_file):
		output_buffer += handle_mode_1(i)
		output_buffer += "\n\n"
		img_count+=1
	output_buffer += make_textures(len(ls(args.input_file)))
	output_buffer += make_obj()


with open(args.output_file, "w+") as f:
	f.write(output_buffer)
	f.write("// "+str(width)+" "+str(height))