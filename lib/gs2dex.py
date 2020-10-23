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
	def sprite_dim(w, h):
		return Gs2dex.sprite_dim_pos(0, 0, w, h)

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
		self.data_type = "uObjTxtr"
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
	
	def get_img_stride(self):
		return "\t"+Gs2dex.gs_pix2tmem(self.width, self.tex_bitsize) + " /* imageStride */\n"

	def get_img_addr(self):
		return "\t"+Gs2dex.gs_pix2tmem(0, self.tex_bitsize) + " /* imageAdrs */\n"


	def __str__(self):
		s_str =  ' '.join([self.data_type, self.name + "_obj",'=','{'])+'\n'
		s_str += Gs2dex.sprite_dim(self.width, self.height)
		s_str += self.get_img_stride()
		s_str += self.get_img_addr()
		s_str += self.get_img_fmt()
		s_str += self.get_img_siz()
		s_str += self.get_img_pal()
		s_str += self.get_img_flags()
		s_str += "};\n"
		return s_str
