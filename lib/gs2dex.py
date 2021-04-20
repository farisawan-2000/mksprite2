class Gs2dex:
	def gs_tb_tsize(w, h, bitsize):
		return "GS_TB_TSIZE(%d*%d,  %s),  /* tsize   */\n" % (w, h, bitsize)
	def gs_tb_tline(w, bitsize):
		return "GS_TB_TLINE(%d,     %s),  /* tline   */\n" % (w, bitsize)
	def gs_pix2tmem(off, bitsize):
		return "GS_PIX2TMEM(%s, %s)," % (off, bitsize)
	def sprite_dim_pos(x, y, w, h):
		ret =  "\t%d<<2, 1<<10, %d<<5, 0,          /* objX, scaleX, imageW, unused */\n" % (x, w)
		ret += "\t%d<<2, 1<<10, %d<<5, 0,          /* objY, scaleY, imageH, unused */\n" % (y, h)
		return ret
	def sprite_dim_centered(w, h):
		ret =  "\t%d<<2, 1<<10, %d<<5, 0,          /* objX, scaleX, imageW, unused */\n" % (-(w / 2), w)
		ret += "\t%d<<2, 1<<10, %d<<5, 0,          /* objY, scaleY, imageH, unused */\n" % (-(h / 2), h)
		return ret
	def sprite_dim_centered_shadow(w, h):
		ret =  "\t%d<<2, 1<<10, %d<<5, 0,          /* objX, scaleX, imageW, unused */\n" % ((-(w / 2)) + 8, w)
		ret += "\t%d<<2, 1<<10, %d<<5, 0,          /* objY, scaleY, imageH, unused */\n" % ((-(h / 2)) + 8, h)
		return ret
	def sprite_dim(w, h):
		return Gs2dex.sprite_dim_pos(0, 0, w, h)
	def gs_pal_head(o):
		return "GS_PAL_HEAD(%s), /* phead */\n" % o
	def gs_pal_num(o):
		return "GS_PAL_NUM(%s), /* pnum */\n" % o

class S2dType:
	width = 0
	height = 0
	data_type = ""
	tex_pointer = ""
	tex_format = ""
	tex_bitsize = ""
	name = ""
	def get_img_fmt(self):
		return "\t"+self.tex_format+', /* imageFmt */\n'
	def get_img_siz(self):
		return "\t"+self.tex_bitsize+', /* imageSiz */\n'
	def get_img_pal(self):
		return '\t0, /* imagePal */\n' # TODO: implement CI textures
	def get_img_flags(self):
		return '\t0, /* imageFlags */\n'

# Extend this class if you want to use LoadTile
class UObjTxtr(S2dType):
	load_type = "G_OBJLT_TXTRBLOCK"
	def __init__(self, w, h, fmt, bitsize, tp, name):
		self.data_type = "uObjTxtrBlock_t"
		self.width = w
		self.height = h
		self.tex_format = fmt
		self.tex_bitsize = bitsize
		self.tex_pointer = tp
		self.name = name

	def get_load_type(self):
		return "\t"+self.load_type+", \n"

	def get_img_addr(self):
		return "\t"+Gs2dex.gs_pix2tmem(0, self.tex_bitsize) + " /* tmem */\n"

	def get_img_ptr(self, typ):
		return "\t(%s) &%s," % (typ, self.tex_pointer)

	def get_image(self):
		return self.get_img_ptr("u64 *")+" /* image */\n"

	def get_flag(self):
		return self.get_img_ptr("u32")+" /* flag */\n"

	def __str__(self):
		s_str =  ' '.join([self.data_type, self.name + "_tex",'=','{'])+'\n'
		s_str += self.get_load_type()
		s_str += self.get_image()
		s_str += self.get_img_addr()
		s_str += "\t"+Gs2dex.gs_tb_tsize(self.width, self.height, self.tex_bitsize)
		s_str += "\t"+Gs2dex.gs_tb_tline(self.width, self.tex_bitsize)
		s_str += "\t0, /* sid */\n"
		s_str += self.get_flag()
		s_str += "\t0xFFFFFFFF, /* mask */\n"
		s_str += "};\n"
		return s_str

class UObjTLUT(UObjTxtr):
	load_type = "G_OBJLT_TLUT"
	def __init__(self, tp, name, psize):
		self.data_type = "uObjTxtrTLUT_t"
		self.tex_pointer = tp
		self.name = name
		self.psize = psize

	def get_load_type(self):
		return "\t"+self.load_type+", \n"

	def get_img_ptr(self, typ):
		return "\t(%s) &%s," % (typ, self.tex_pointer)

	def get_image(self):
		return self.get_img_ptr("u64 *")+" /* image */\n"

	def get_flag(self):
		return self.get_img_ptr("u32")+" /* flag */\n"

	def __str__(self):
		s_str =  ' '.join([self.data_type, self.name + "_TLUT",'=','{'])+'\n'
		s_str += self.get_load_type()
		s_str += self.get_image()
		s_str += "\t"+Gs2dex.gs_pal_head(0)
		s_str += "\t"+Gs2dex.gs_pal_num(self.psize + 1)
		s_str += "\t0,\n"
		s_str += "\t0, /* sid */\n"
		s_str += self.get_flag()
		s_str += "\t0xFFFFFFFF, /* mask */\n"
		s_str += "};\n"
		return s_str

class UObjAniTLUT(UObjTxtr):
	load_type = "G_OBJLT_TLUT"
	def __init__(self, tp, name, psize, lst):
		self.data_type = "uObjTxtrTLUT_t"
		self.tex_pointer = tp
		self.name = name
		self.psize = psize
		self.lst = lst

	def get_load_type(self):
		return "\t"+self.load_type+", \n"

	def get_img_ptr(self, typ, i):
		return "\t(%s) &%s," % (typ, self.name+"_tex_"+str(i))

	def get_image(self, i):
		return self.get_img_ptr("u64 *", i)+" /* image */\n"

	def get_flag(self, count):
		return self.get_img_ptr("u32", count)+" /* flag */\n"

	def __str__(self):
		s_str =  ' '.join([self.data_type, self.name + "_TLUT[]",'=','{'])+'\n'
		for i in range(len(self.lst)):
			s_str += "{\n"
			s_str += self.get_load_type()
			s_str += self.get_image(i)
			# s_str += "\t"+Gs2dex.gs_pal_head(i)
			s_str += "\t"+Gs2dex.gs_pal_head(0)
			s_str += "\t"+Gs2dex.gs_pal_num(len(self.lst[i]))
			s_str += "\t0,\n"
			s_str += "\t0, /* sid */\n"
			s_str += self.get_flag(i)
			s_str += "\t0xFFFFFFFF, /* mask */\n"
			s_str += "},\n"
		s_str += "};\n"
		return s_str

class UObjAniTxtr(UObjTxtr):
	count = 0
	def __init__(self, count, w, h, fmt, bitsize, tp, name):
		self.data_type = "uObjTxtr"
		self.count = count
		self.width = w
		self.height = h
		self.tex_format = fmt
		self.tex_bitsize = bitsize
		self.tex_pointer = tp
		self.name = name

	def get_img_ptr(self, typ, i):
		return "\t(%s) &%s," % (typ, self.name+"_tex_"+str(i))
	def get_image(self, c):
		return self.get_img_ptr("u64 *", c)+" /* image */\n"
	def get_flag(self, c):
		return self.get_img_ptr("u32", c)+" /* flag */\n"

	def __str__(self):
		print(self.name)
		s_str =  ' '.join([self.data_type, self.name + "_tex[]",'=','{'])+'\n'
		for i in range(self.count):
			s_str += "{\n"
			s_str += self.get_load_type()
			s_str += self.get_image(i)
			s_str += self.get_img_addr()
			s_str += "\t"+Gs2dex.gs_tb_tsize(self.width, self.height, self.tex_bitsize)
			s_str += "\t"+Gs2dex.gs_tb_tline(self.width, self.tex_bitsize)
			s_str += "\t0, /* sid */\n"
			s_str += self.get_flag(i)
			s_str += "\t0xFFFFFFFF, /* mask */\n"
			s_str += "},\n"
		s_str += "};\n"
		return s_str

class UObjSprite(S2dType):
	def __init__(self, w, h, fmt, bitsize, name):
		self.data_type = "uObjSprite"
		self.width = w
		self.height = h
		self.tex_format = fmt
		self.tex_bitsize = bitsize
		self.name = name
	
	def get_img_stride_16(self):
		return "\t"+Gs2dex.gs_pix2tmem(self.width, self.tex_bitsize) + " /* imageStride */\n"

	def get_img_stride_32(self):
		return "\t"+Gs2dex.gs_pix2tmem(self.width / 2, self.tex_bitsize) + " /* imageStride */\n"

	def get_img_addr(self):
		return "\t"+Gs2dex.gs_pix2tmem(0, self.tex_bitsize) + " /* imageAdrs */\n"

	def __str__(self):
		s_str =  ' '.join([self.data_type, self.name + "_obj",'=','{'])+'\n'
		s_str += Gs2dex.sprite_dim_centered(self.width, self.height)
		if self.tex_bitsize == "32":
			s_str += self.get_img_stride_32()
		else:
			s_str += self.get_img_stride_16()
		s_str += self.get_img_addr()
		s_str += self.get_img_fmt()
		s_str += self.get_img_siz()
		s_str += self.get_img_pal()
		s_str += self.get_img_flags()
		s_str += "};\n"
		return s_str

class UObjSpriteDropShadow(UObjSprite):
	def __str__(self):
		s_str =  ' '.join([self.data_type, self.name + "_obj_dropshadow",'=','{'])+'\n'
		s_str += Gs2dex.sprite_dim_centered_shadow(self.width, self.height)
		if self.tex_bitsize == "32":
			s_str += self.get_img_stride_32()
		else:
			s_str += self.get_img_stride_16()
		s_str += self.get_img_addr()
		s_str += self.get_img_fmt()
		s_str += self.get_img_siz()
		s_str += self.get_img_pal()
		s_str += self.get_img_flags()
		s_str += "};\n"
		return s_str


class UObjMtx:
	sx = 1;
	sy = 1;
	x = 0;
	y = 0;
	name = ""
	def __init__(self, sx, sy, x, y, name):
		self.data_type = "uObjMtx"
		self.sx = sx;
		self.sy = sy;
		self.x = x;
		self.y = y;
		self.name = name

	def __str__(self):
		s_str = ' '.join([self.data_type, self.name + "_mtx",'=','{'])+'\n'
		s_str += "\t0x10000,  0,              /* A,B */\n"
		s_str += "\t0,        0x10000,        /* C,D */\n"
		s_str += "\t%d,        %d,            /* X,Y */\n" % (self.x, self.y)
		s_str += "\t%d<<10,    %d<<10           /* BaseScaleX, BaseScaleY */\n" % (self.sx, self.sy)
		s_str += "};\n"
		return s_str