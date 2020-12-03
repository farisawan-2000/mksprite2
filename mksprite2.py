#!/usr/bin/env python3
from PIL import Image, GifImagePlugin
import argparse
import enum
import sys, os
try:
	import argcomplete  # type: ignore
except ModuleNotFoundError:
    argcomplete = None

# My lib/ functions
from lib.img_converters import to5551, to8888, toia8
from lib.parser import get_parser
from lib.gs2dex import *
from lib.dl_handler import *

parser = get_parser()

if argcomplete:
    argcomplete.autocomplete(parser)

class Mode(enum.Enum):
	SPRITE = 0
	ANI_SPRITE = 1
	BGRECT = 2
	GIF = 3


args = parser.parse_args()

mode = Mode.SPRITE
# Make sure paths are correct
if os.path.isdir(args.input_file):
    mode = Mode.ANI_SPRITE
elif '.gif' in args.input_file:
	mode = Mode.GIF
	print("ERROR: GIF support not implemented")
	exit(1)
elif not os.path.isfile(args.input_file):
    raise Exception("Input file is not a file or directory")

if args.bgrect:
	mode = Mode.BGRECT
	if not os.path.isfile(args.input_file):
		raise Exception("Error: Please specify a single image for BG Rect mode")

width = 0
height = 0

# TODO: implement image resizing if not in these widths (or just use loadtile???)
valid_loadblock_widths = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 64, 72, 76, 100, 108, 128, 144, 152, 164, 200, 216, 228, 256, 304, 328, 432, 456, 512, 684, 820, 912]

def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))] 

ls = lambda x : [name for name in os.listdir(x)]

convert_rgba16 = lambda x : to5551(x)
convert_rgba32 = lambda x : to8888(x)
convert_ia8 = lambda x : toia8(x)
convert_texel = convert_rgba16
if args.fmt == "RGBA32":
	print("WARNING: RGBA32 is supported, but WILL NOT work!")
	print("\tFeel free to try to make it work, however, and be sure to PR the changes!")
	convert_texel = convert_rgba32
if args.fmt in ["IA8"]:
	convert_texel = convert_ia8

img_count = 0

def get_image_sym(i, x):
	return str(i)+"_tex_"+str(x)
def get_obj_sym(i):
	return str(i)+"_obj"
def get_bg_sym(i):
	return str(i)+"_bg"

def get_image_fmt():
	if args.fmt in ["RGBA16", "RGBA32"]:
		return "G_IM_FMT_RGBA"
	if args.fmt in ["IA16", "IA8", "IA4"]:
		return "G_IM_FMT_IA"

def get_image_size():
	if args.fmt =="RGBA16":
		return "G_IM_SIZ_16b"
	if args.fmt =="RGBA32":
		return "G_IM_SIZ_32b"
	if args.fmt =="IA8":
		return "G_IM_SIZ_8b"

def get_image_ultratype():
	if args.fmt =="RGBA16":
		return ["u16", "0x%04X"]
	if args.fmt =="RGBA32":
		return ["u32", "0x%08X"]
	if args.fmt == "IA8":
		return ["u8", "0x%02X"]

def get_image_header(i):
	rt = "ALIGNED8 %s " % get_image_ultratype()[0]
	return rt + get_image_sym(i, img_count)+"[] = {"

def align_tex(n, x):
	return "u32 "+n+"_align_"+str(x)+" = {gsSPEndDisplayList()};\n"

def handle_mode_0(infile):
	global width
	global height
	imstr = "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	imstr+=get_image_header(args.sprite_name)
	with Image.open(infile) as img:
		width, height = img.size
		for i in range(height):
			for j in range(width):
				imstr+= (get_image_ultratype()[1] % convert_texel(img.getpixel((j, i))))+", "

	imstr+= "};\n"
	imstr += align_tex(args.sprite_name, 0) + "\n"
	return imstr

def handle_mode_1(infile):
	global width
	global height
	imstr=get_image_header(args.sprite_name)
	with Image.open(infile) as img:
		width, height = img.size
		for i in range(height):
			for j in range(width):
				imstr+= (get_image_ultratype()[1] % convert_texel(img.getpixel((j, i))))+", "

	imstr+= "};\n"
	return imstr

def setup_mode_gif(infile):
	global width
	global height
	# imstr=get_image_header(args.sprite_name)
	with Image.open(infile) as img:
		print(img.is_animated)
		print(img.n_frames)
		width, height = img.size
		for frame in range(0, img.n_frames):
			img.seek(frame)
			img.save("./tmp/"+str(frame)+".png")

	# imstr+= "};\n\n"
	# return imstr


def make_bg():
	imstr = '\n\n'
	imstr+= '\n'.join([
	"uObjBg %s = {" % get_bg_sym(args.sprite_name),
	"\t0, %d<<2, 0<<2, 320<<2,  /* imageX, imageW, frameX, frameW */" % width,
	"\t0, %d<<2, 0<<2, 240<<2,  /* imageY, imageH, frameY, frameH */" % height,
	"\t(u64 *)&%s,                /* imagePtr                       */" % get_image_sym(args.sprite_name, 0),
	"\tG_BGLT_LOADBLOCK,     /* imageLoad */                      ",
	"\t%s,        /* imageFmt                       */" % get_image_fmt(),
	"\t%s,         /* imageSiz                       */" % get_image_size(),
	"\t0,                /* imagePal                       */",
	"\t0,             /* imageFlip                      */",
	"\t1 << 10,       /* scale W (s5.10) */",
	"\t1 << 10,       /* scale H (s5.10) */",
	"\t0,",
	"};",
	])
	return imstr+"\n\n"

def gen_header(args):
	imstr = ""
	imstr += "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	if args.init_dl:
		imstr += "extern Gfx s2d_init_dl[];\n"
	imstr += "extern uObjTxtr %s_tex%s;\n" % (args.sprite_name, "[]" if img_count > 0 else "")
	if not args.bgrect:
		imstr += "extern uObjMtx %s_mtx;\n" % args.sprite_name
		imstr += "extern uObjSprite %s_obj;\n" % args.sprite_name
		if img_count > 0:
			imstr += "extern void call_%s_sprite_dl(int idx);\n" % args.sprite_name
		else:
			imstr += "extern Gfx %s_sprite_dl[];\n" % args.sprite_name
	else:
		imstr += "extern uObjBg %s_bg;\n" % args.sprite_name
		imstr += "extern Gfx %s_bg_dl[];\n" % args.sprite_name
	if img_count == 0:
		imstr += "extern %s %s_tex_0[];\n" % (get_image_ultratype()[0], args.sprite_name)
	for i in range(img_count):
		imstr += "extern %s %s_tex_%d[];\n" % (get_image_ultratype()[0], args.sprite_name, i)
	return imstr


def print_warning(mode):
	print("Note: When using "+mode+" with SM64 Decomp, due to space restraints,")
	print("\tit's best to include your sprites in an assets file.\n")



output_buffer = ""
if mode == Mode.SPRITE:
	output_buffer += handle_mode_0(args.input_file)
	print(width, height)
	output_buffer += str(UObjTxtr(width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += str(UObjMtx(1, 1, 50, 50, args.sprite_name))
	output_buffer += str(UObjSprite(width, height, get_image_fmt(), get_image_size(), args.sprite_name))
	if args.create_dl:
		output_buffer += make_sprite_dl(args, img_count)
elif mode == Mode.ANI_SPRITE:
	print_warning("animated sprites")
	output_buffer += "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	for i in range(len(ls(args.input_file))):
		output_buffer += handle_mode_1(args.input_file+str(i)+".png")
		# output_buffer += "\n"
		output_buffer += align_tex(args.sprite_name, 0)
		output_buffer += "\n"
		img_count+=1
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += str(UObjAniTxtr(len(ls(args.input_file)), width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
	output_buffer += str(UObjMtx(1, 1, 50, 50, args.sprite_name))
	output_buffer += str(UObjSprite(width, height, get_image_fmt(), get_image_size(), args.sprite_name))
	if args.create_dl:
		if img_count > 0:
			output_buffer += make_ani_sprite_dl(args)
		else:
			output_buffer += make_sprite_dl(args, img_count)
elif mode == Mode.BGRECT:
	output_buffer += handle_mode_0(args.input_file)
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += make_bg()
	if args.create_dl:
		output_buffer += make_bg_dl(args)
elif mode == Mode.GIF:
	print_warning("gifs")
	output_buffer += "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	setup_mode_gif(args.input_file)
	# output_buffer += handle_mode_1("./tmp/")
	for i in range(len(ls('./tmp/'))):
		output_buffer += handle_mode_1("./tmp/"+str(i)+".png")
		output_buffer += "\n\n"
		img_count+=1
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += str(UObjAniTxtr(len(ls(args.input_file)), width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
	output_buffer += str(UObjMtx(1, 1, 50, 50, args.sprite_name))
	output_buffer += str(UObjSprite(width, height, get_image_fmt(), get_image_size(), args.sprite_name))
	if args.create_dl:
		if img_count > 0:
			output_buffer += make_ani_sprite_dl(args)
		else:
			output_buffer += make_sprite_dl(args, img_count)



if args.header_file:
	with open(args.header_file, "w+") as f:
		f.write(gen_header(args))

with open(args.output_file, "w+") as f:
	f.write(output_buffer)
	f.write("// "+str(width)+" "+str(height))

print("Done.")