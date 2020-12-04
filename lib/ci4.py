import argparse
from lib.img_converters import to5551, toci4
from PIL import Image
from lib.gs2dex import *
from lib.dl_handler import *

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

def get_image_header(i, t):
	rt = "ALIGNED8 %s " % get_image_ultratype(t)[0]
	return rt + get_image_sym(i, 0)+"[] = {"

def make_palette(lst, nm):
	o = get_image_header(nm+"_pal", 1)
	for el in lst:
		o+=(get_image_ultratype(1)[1] % convert_rgba16(el))+", "
	o += "};\n"
	return o;



def handle_ci4(infile, lst, nm):
	global width
	global height
	imstr=get_image_header(nm, 0)
	with Image.open(infile) as img:
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


def make_ci4_sprite(args):
	o_buf = ""
	o_buf += "#include <PR/ultratypes.h>\n#include <PR/gs2dex.h>\n"
	pal_list = []
	o_buf += handle_ci4(args.input_file, pal_list, args.sprite_name)
	o_buf+=make_palette(pal_list, args.sprite_name)
	print(width, height)
	o_buf += str(UObjTxtr(width, height, get_image_fmt(), get_image_size(), get_image_sym(args.sprite_name, 0), args.sprite_name))
	o_buf += str(UObjTLUT(get_image_sym(args.sprite_name+"_pal", 0), args.sprite_name+"_pal", len(pal_list)))
	if args.init_dl:
		o_buf += make_s2d_init_dl()
	o_buf += str(UObjMtx(1, 1, 50, 50, args.sprite_name))
	o_buf += str(UObjSprite(width, height, get_image_fmt(), get_image_size(), args.sprite_name))
	if args.create_dl:
		o_buf += make_sprite_dl_ci(args, 0)
	return o_buf