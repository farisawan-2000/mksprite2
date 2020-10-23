#!/usr/bin/env python3
from PIL import Image
import argparse
import enum
import sys, os
try:
    import argcomplete  # type: ignore
except ModuleNotFoundError:
    argcomplete = None

# My lib/ functions
from lib.img_converters import to5551, to8888
from lib.parser import get_parser


parser = get_parser()



if argcomplete:
    argcomplete.autocomplete(parser)

class Mode(enum.Enum):
	SPRITE = 0
	ANI_SPRITE = 1
	BGRECT = 2


args = parser.parse_args()


mode = Mode.SPRITE


# Make sure paths are correct
if os.path.isdir(args.input_file):
    mode = Mode.ANI_SPRITE
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


ls = lambda x : [name for name in os.listdir(args.input_file)]

convert_rgba16 = lambda x : to5551(x)
convert_rgba32 = lambda x : to8888(x)
convert_texel = convert_rgba16
if args.fmt == "RGBA32":
	print("WARNING: RGBA32 is supported, but WILL NOT work!")
	print("\tFeel free to try to make it work, however, and be sure to PR the changes!")
	convert_texel = convert_rgba32

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

def get_image_size():
	if args.fmt =="RGBA16":
		return "G_IM_SIZ_16b"
	if args.fmt =="RGBA32":
		return "G_IM_SIZ_32b"

def get_image_ultratype():
	if args.fmt =="RGBA16":
		return ["u16", "0x%04X"]
	if args.fmt =="RGBA32":
		return ["u32", "0x%08X"]

def get_image_header(i):
	rt = "ALIGNED8 %s " % get_image_ultratype()[0]
	return rt + get_image_sym(i, img_count)+"[] = {"

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
				# print(img.getpixel((j, i)))
				# print((get_image_ultratype()[1] % convert_texel(img.getpixel((j, i)))))
				imstr+= (get_image_ultratype()[1] % convert_texel(img.getpixel((j, i))))+", "

	imstr+= "};\n\n"
	return imstr

def handle_mode_1(infile):
	global width
	global height
	imstr=get_image_header(args.sprite_name)
	with Image.open(args.input_file+infile) as img:
		width, height = img.size
		for i in range(height):
			for j in range(width):
				imstr+= (get_image_ultratype()[1] % convert_texel(img.getpixel((j, i))))+", "

	imstr+= "};\n\n"
	return imstr

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

def make_init_matrix():
	return '\n'.join([
		"uObjMtx %s_mtx =" % args.sprite_name,
		"{",
		"	0x10000,  0,              /* A,B */",
		"	0,        0x10000,        /* C,D */",
		"	50,        50,            /* X,Y */",
		"	1<<10,    1<<10           /* BaseScaleX, BaseScaleY */",
		"};"
		])

def make_s2d_init_dl():
	istr = "Gfx s2d_init_dl[] = {\n"+\
	'\n'.join([
	"\tgsDPPipeSync(),",
	"\tgsDPSetTexturePersp(G_TP_NONE),",
	"\tgsDPSetTextureLOD(G_TL_TILE),",
	"\tgsDPSetTextureLUT(G_TT_NONE),",
	"\tgsDPSetTextureConvert(G_TC_FILT),",
	"\tgsDPSetAlphaCompare(G_AC_THRESHOLD),",
	"\tgsDPSetBlendColor(0, 0, 0, 0x01),",
	"\tgsDPSetCombineMode(G_CC_DECALRGBA, G_CC_DECALRGBA),",
	"\tgsSPEndDisplayList(),",
	])+"\n};\n\n"
	return istr

def make_bg_dl():
	imstr = "Gfx %s_bg_dl[] = {\n" % args.sprite_name
	imstr += '\n'.join([
	"\tgsDPPipeSync(),",
	"\tgsSPDisplayList(s2d_init_dl)," if args.init_dl else "",
	"\tgsDPSetCycleType(G_CYC_1CYCLE),",
	"\tgsDPSetRenderMode(G_RM_XLU_SPRITE, G_RM_XLU_SPRITE2),",
	"\tgsSPObjRenderMode(G_OBJRM_XLU | G_OBJRM_BILERP),",
	"\tgsSPBgRect1Cyc(&%s_bg)," % args.sprite_name,
	"\tgsSPEndDisplayList(),",
	])
	imstr+="\n};"
	return imstr

def make_sprite_dl(args, icount):
	imstr = "Gfx %s_sprite_dl[] = {\n" % args.sprite_name
	imstr += '\n'.join([
	"\tgsDPPipeSync(),",
	"\tgsSPDisplayList(s2d_init_dl)," if args.init_dl else "",
	"\tgsDPSetCycleType(G_CYC_1CYCLE),",
	"\tgsDPSetRenderMode(G_RM_XLU_SPRITE, G_RM_XLU_SPRITE2),",
	"\tgsSPObjRenderMode(G_OBJRM_XLU | G_OBJRM_BILERP),",
	"\tgsSPObjLoadTxtr(&%s_tex%s)," % (args.sprite_name,"[0]" if icount > 0 else ""),
	"\tgsSPObjMatrix(&%s_mtx)," % args.sprite_name,
	"\tgsSPObjSprite(&%s_obj)," % args.sprite_name,
	"\tgsSPEndDisplayList(),",
	])
	imstr+="\n};"
	return imstr


def make_ani_sprite_dl():
	imstr = "void call_%s_sprite_dl(int idx) {\n" % args.sprite_name
	imstr += '\n'.join([
	"\tgDPPipeSync(%s++);" % args.dl_head,
	''.join(["\tgSPDisplayList(%s++, s2d_init_dl);" % args.dl_head]) if args.init_dl else "",
	"\tgDPSetCycleType(%s++, G_CYC_1CYCLE);" % args.dl_head,
	"\tgDPSetRenderMode(%s++, G_RM_XLU_SPRITE, G_RM_XLU_SPRITE2);" % args.dl_head,
	"\tgSPObjRenderMode(%s++, G_OBJRM_XLU | G_OBJRM_BILERP);" % args.dl_head,
	"\tgSPObjLoadTxtr(%s++, &%s_tex[idx]);" % (args.dl_head, args.sprite_name),
	"\tgSPObjMatrix(%s++, &%s_mtx);" % (args.dl_head, args.sprite_name),
	"\tgSPObjSprite(%s++, &%s_obj);" % (args.dl_head, args.sprite_name),
	])
	imstr+="\n};"
	return imstr

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


from lib.gs2dex import *

output_buffer = ""
if mode == Mode.SPRITE:
	output_buffer += handle_mode_0(args.input_file)
	print(width, height)
	output_buffer += str(UObjTxtr(width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += make_init_matrix()
	output_buffer += str(UObjSprite(width, height, get_image_fmt(), get_image_size(), args.sprite_name))
	if args.create_dl:
		output_buffer += make_sprite_dl(args, img_count)
elif mode == Mode.ANI_SPRITE:
	print("Warning: When using animated sprites with SM64 Decomp, due to space restraints,")
	print("\tyou might have to split up the output file.\n")
	output_buffer += "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	for i in ls(args.input_file):
		output_buffer += handle_mode_1(i)
		output_buffer += "\n\n"
		img_count+=1
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += str(UObjAniTxtr(len(ls(args.input_file)), width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
	output_buffer += make_init_matrix()
	output_buffer += str(UObjSprite(width, height, get_image_fmt(), get_image_size(), args.sprite_name))
	if args.create_dl:
		if img_count > 0:
			output_buffer += make_ani_sprite_dl()
		else:
			output_buffer += make_sprite_dl(args, img_count)
elif mode == Mode.BGRECT:
	output_buffer += handle_mode_0(args.input_file)
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += make_bg()
	if args.create_dl:
		output_buffer += make_bg_dl()


if args.header_file:
	with open(args.header_file, "w+") as f:
		f.write(gen_header(args))

with open(args.output_file, "w+") as f:
	f.write(output_buffer)
	f.write("// "+str(width)+" "+str(height))

print("Done.")