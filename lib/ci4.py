import argparse
from lib.img_converters import to5551, toci4
from PIL import Image
from lib.gs2dex import *
from lib.dl_handler import *
import enum, os

ls = lambda x : [name for name in os.listdir(x)]
convert_texel = lambda x, y, z: toci4(x, y, z)
convert_rgba16 = lambda x: to5551(x)

def get_image_sym(i, x):
	return str(i)+"_tex_"+str(x)
def get_obj_sym(i):
	return str(i)+"_obj"
def get_bg_sym(i):
	return str(i)+"_bg"

def get_image_fmt():
	return "G_IM_FMT_CI"

def get_image_size():
	return "G_IM_SIZ_4b"

def get_image_ultratype(t):
	if t == 0:
		return ["u8", "0x%02X"]
	if t == 1:
		return ["u16", "0x%04X"]

def get_image_header(i, t, c):
	rt = "__attribute__((aligned(8))) %s " % get_image_ultratype(t)[0]
	return rt + get_image_sym(i, c)+"[] = {"

def make_palette(lst, nm):
	o = get_image_header(nm+"_pal", 1, 0)
	for el in lst:
		o+=(get_image_ultratype(1)[1] % convert_rgba16(el))+", "
	o += "};\n"
	return o;

def make_ani_palette(lst, nm):
	o = ""
	d = 0
	for list_el in lst:
		o += get_image_header(nm+"_pal", 1, d)
		for el in list_el:
			o+=(get_image_ultratype(1)[1] % convert_rgba16(el))+", "
		o += "};\n"
		d+=1
	return o;


def handle_ci4(infile, lst, nm):
	global width
	global height
	imstr=get_image_header(nm, 0, 0)
	with Image.open(infile) as img:
		img = img.convert('RGBA')
		width, height = img.size
		for i in range(height):
			for j in range(width)[::2]:
				imstr+= (get_image_ultratype(0)[1] % convert_texel(
					img.getpixel((j, i)),
					img.getpixel((j + 1, i)),
					lst
					))+", "
	# print(lst)
	imstr+= "};\n"

	return imstr

def handle_ci4_animated(infile, lst, nm, count):
	global width
	global height
	imstr=get_image_header(nm, 0, count)
	print(infile+str(count)+".png")
	with Image.open(infile+str(count)+".png") as img:
		img = img.convert('RGBA')
		width, height = img.size
		for i in range(height):
			for j in range(width)[::2]:
				imstr+= (get_image_ultratype(0)[1] % convert_texel(
					img.getpixel((j, i)),
					img.getpixel((j + 1, i)),
					lst
					))+", "
	# print(lst)
	imstr+= "};\n"

	return imstr

class Mode(enum.Enum):
	SPRITE = 0
	ANI_SPRITE = 1
	BGRECT = 2
	GIF = 3

def align_tex(n, x):
	return "Gfx "+n+"_align_"+str(x)+"[] = {gsSPEndDisplayList()};\n"

def make_ci4_sprite(args, anim):
	print(anim)
	o_buf = ""
	o_buf += "#include <ultra64.h>\n#include <PR/gs2dex.h>\n"
	pal_list = []
	if anim == 1:
		for i in range(len(ls(args.input_file))):
			if args.pal_split:
				gal_list = []
				o_buf += handle_ci4_animated(args.input_file, gal_list, args.sprite_name, i)
				o_buf += align_tex(args.sprite_name, i) + "\n"
				pal_list.append(gal_list)
			else:
				o_buf += handle_ci4_animated(args.input_file, pal_list, args.sprite_name, i)
				o_buf += align_tex(args.sprite_name, i) + "\n"
				print(pal_list)
		if args.pal_split:
			o_buf+=make_ani_palette(pal_list, args.sprite_name)
		else:
			o_buf += make_palette(pal_list, args.sprite_name)
		o_buf += "\n"
		# print(set(pal_list))
	else:
		o_buf += handle_ci4(args.input_file, pal_list, args.sprite_name)
		o_buf+=make_palette(pal_list, args.sprite_name)
	print(width, height)
	if anim == 1:
		o_buf += str(UObjAniTxtr(len(ls(args.input_file)), width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
		o_buf += "\n"
		if args.pal_split:
			o_buf += str(UObjAniTLUT(get_image_sym(args.sprite_name+"_pal", 0), args.sprite_name+"_pal", len(pal_list), pal_list))
		else:
			o_buf += str(UObjTLUT(get_image_sym(args.sprite_name+"_pal", 0), args.sprite_name+"_pal", len(pal_list)))
	else:
		o_buf += str(UObjTxtr(width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
		o_buf += "\n"
		o_buf += str(UObjTLUT(get_image_sym(args.sprite_name+"_pal", 0), args.sprite_name+"_pal", len(pal_list)))
	if args.init_dl:
		o_buf += make_s2d_init_dl(args.sprite_name)
	o_buf += str(UObjMtx(1, 1, 50, 50, args.sprite_name))
	o_buf += str(UObjSprite(width, height, get_image_fmt(), get_image_size(), args.sprite_name))
	if args.create_dl:
		if anim == 1:
			o_buf += make_ani_sprite_dl_ci(args)
		else:
			o_buf += make_sprite_dl_ci(args, 0)
	return o_buf