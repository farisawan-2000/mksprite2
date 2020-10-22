#!/usr/bin/env python3
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
    metavar="FILE",
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
    "-f",
    dest="header_file",
    metavar="FILE",
    help="Optional header file with appropriate externs",
)

parser.add_argument(
	"-c",
    "--create-dl",
    dest="create_dl",
    action="store_true",
    help="Creates a simple displaylist to render the sprite or bg",
)

parser.add_argument(
	"-b",
    "--bgrect",
    dest="bgrect",
    action="store_true",
    help="Makes a BG rect instead of a sprite. Only compatible with single files.",
)

parser.add_argument(
	"-n",
    "--name",
    dest="sprite_name",
    help="Sprite/BGRect object name (Defaults to 'sprite')",
    default="sprite",
)

parser.add_argument(
	"-d",
    "--dlheadname",
    dest="dl_head",
    help="Name of gdl head (default gDisplayListHead for sm64 decomp)",
    default="gDisplayListHead",
)

parser.add_argument(
	"-t",
    "--makeinitdl",
    dest="init_dl",
    action="store_true",
    help="Creates an S2D init DL which sets up the RDP correctly",
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

if args.bgrect:
	mode = 2
	if not os.path.isfile(args.input_file):
		raise Exception("Error: Please specify a single image for BG Rect mode")

width = 0
height = 0

# TODO: implement image resizing if not in these widths (or just use loadtile???)
valid_loadblock_widths = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 64, 72, 76, 100, 108, 128, 144, 152, 164, 200, 216, 228, 256, 304, 328, 432, 456, 512, 684, 820, 912]

def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))] 

clamp = lambda x : (int(x) & 0x1F)

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
def get_bg_sym(i):
	return str(i)+"_bg"
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
				imstr+= ("0x%04X" % to5551(img.getpixel((j, i))))+", "

	imstr+= "};\n\n"
	return imstr


def make_textures(count):
	global img_count
	imstr = "\n\n"
	imstr += "uObjTxtr "+args.sprite_name+"_tex%s =\n" % ''.join('[]' if count > 1 else '')
	if count > 1:
		imstr += "{\n"
	if count == 0:
		imstr+="\n".join(["    {",
		"        G_OBJLT_TXTRBLOCK,                  /* type    */",
		"        (u64 *)&%s,                         /* image   */" % get_image_sym(args.sprite_name, img_count - count),
		"        GS_PIX2TMEM(0,      G_IM_SIZ_16b),  /* tmem    */",
		"        GS_TB_TSIZE(%d*%d,  G_IM_SIZ_16b),  /* tsize   */" % (width, height),
		"        GS_TB_TLINE(%d,     G_IM_SIZ_16b),  /* tline   */" % width,
		"        0,                                  /* sid     */",
		"        (u32)&%s,                           /* flag    */" % get_image_sym(args.sprite_name, img_count - count),
		"        -1                                  /* mask    */",
		"    };\n"])
	while count > 0:
		imstr+="\n".join(["    {",
		"        G_OBJLT_TXTRBLOCK,                  /* type    */",
		"        (u64 *)&%s,                         /* image   */" % get_image_sym(args.sprite_name, img_count - count),
		"        GS_PIX2TMEM(0,      G_IM_SIZ_16b),  /* tmem    */",
		"        GS_TB_TSIZE(%d*%d,  G_IM_SIZ_16b),  /* tsize   */" % (width, height),
		"        GS_TB_TLINE(%d,     G_IM_SIZ_16b),  /* tline   */" % width,
		"        0,                                  /* sid     */",
		"        (u32)&%s,                           /* flag    */" % get_image_sym(args.sprite_name, img_count - count),
		"        -1                                  /* mask    */",
		"    }%s\n" % ''.join([',' if count > 1 else ',\n};\n'])])
		count -= 1

	# if count > 1:
	# 	imstr += "};\n"
	return imstr

def make_obj():
	imstr = "\n\n"
	imstr+="uObjSprite "+args.sprite_name+"_obj =\n"
	imstr+="\n".join(["{",
	"\t0<<2, 1<<10, %d<<5, 0,          /* objX, scaleX, imageW, paddingX */\n" % width,
	"\t0<<2, 1<<10, %d<<5, 0,          /* objY, scaleY, imageH, paddingY */" % height,
	"\tGS_PIX2TMEM(32, G_IM_SIZ_16b),    /* imageStride */",
	"\tGS_PIX2TMEM(0, G_IM_SIZ_16b),     /* imageAdrs   */",
	"\tG_IM_FMT_RGBA,                    /* imageFmt    */",
	"\tG_IM_SIZ_16b,                     /* imageSiz    */",
	"\t0,                                /* imagePal    */",
	"\t0                                 /* imageFlags  */",
	"};\n"])
	return imstr

def make_bg():
	imstr = '\n\n'
	imstr+= '\n'.join([
	"uObjBg %s = {" % get_bg_sym(args.sprite_name),
	"\t0, %d<<2, 0<<2, 320<<2,  /* imageX, imageW, frameX, frameW */" % width,
	"\t0, %d<<2, 0<<2, 240<<2,  /* imageY, imageH, frameY, frameH */" % height,
	"\t(u64 *)&%s,                /* imagePtr                       */" % get_image_sym(args.sprite_name, 0),
	"\tG_BGLT_LOADBLOCK,     /* imageLoad */                      ",
	"\tG_IM_FMT_RGBA,        /* imageFmt                       */",
	"\tG_IM_SIZ_16b,         /* imageSiz                       */",
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
	])+"\n};"
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

def make_sprite_dl():
	imstr = "Gfx %s_sprite_dl[] = {\n" % args.sprite_name
	imstr += '\n'.join([
	"\tgsDPPipeSync(),",
	"\tgsSPDisplayList(s2d_init_dl)," if args.init_dl else "",
	"\tgsDPSetCycleType(G_CYC_1CYCLE),",
	"\tgsDPSetRenderMode(G_RM_XLU_SPRITE, G_RM_XLU_SPRITE2),",
	"\tgsSPObjRenderMode(G_OBJRM_XLU | G_OBJRM_BILERP),",
	"\tgsSPObjLoadTxtr(&%s_tex%s)," % (args.sprite_name,"[0]" if img_count > 0 else ""),
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

def gen_header():
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
		imstr += "extern u16 %s_tex_0[];\n" % args.sprite_name
	for i in range(img_count):
		imstr += "extern u16 %s_tex_%d[];\n" % (args.sprite_name, i)
	return imstr



output_buffer = ""
if mode == 0:
	output_buffer += handle_mode_0(args.input_file)
	print(width, height)
	output_buffer += make_textures(0)
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += make_init_matrix()
	output_buffer += make_obj()
	if args.create_dl:
		output_buffer += make_sprite_dl()
elif mode == 1:
	print("Warning: When using animated sprites with SM64 Decomp, due to space restraints,")
	print("\tyou might have to split up the output file.\n")
	output_buffer += "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	for i in ls(args.input_file):
		output_buffer += handle_mode_1(i)
		output_buffer += "\n\n"
		img_count+=1
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += make_textures(len(ls(args.input_file)))
	output_buffer += make_init_matrix()
	output_buffer += make_obj()
	if args.create_dl:
		if img_count > 0:
			output_buffer += make_ani_sprite_dl()
		else:
			output_buffer += make_sprite_dl()
elif mode == 2:
	output_buffer += handle_mode_0(args.input_file)
	if args.init_dl:
		output_buffer += make_s2d_init_dl()
	output_buffer += make_bg()
	if args.create_dl:
		output_buffer += make_bg_dl()


if args.header_file:
	with open(args.header_file, "w+") as f:
		f.write(gen_header())

with open(args.output_file, "w+") as f:
	f.write(output_buffer)
	f.write("// "+str(width)+" "+str(height))

print("Done.")