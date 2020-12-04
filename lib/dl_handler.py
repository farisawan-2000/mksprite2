import argparse

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

def make_bg_dl(args):
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

def make_sprite_dl_ci(args, icount):
	imstr = "Gfx %s_sprite_dl[] = {\n" % args.sprite_name
	imstr += '\n'.join([
	"\tgsDPPipeSync(),",
	"\tgsSPDisplayList(s2d_init_dl)," if args.init_dl else "",
	"\tgsDPSetCycleType(G_CYC_1CYCLE),",
	"\tgsDPSetRenderMode(G_RM_XLU_SPRITE, G_RM_XLU_SPRITE2),",
	"\tgsDPSetTextureLUT(G_TT_RGBA16),"
	"\tgsSPObjRenderMode(G_OBJRM_XLU | G_OBJRM_BILERP),",
	"\tgsSPObjLoadTxtr(&%s_tex%s)," % (args.sprite_name,"[0]" if icount > 0 else ""),
	"\tgsSPObjLoadTxtr(&%s_pal_TLUT)," % args.sprite_name,
	"\tgsSPObjMatrix(&%s_mtx)," % args.sprite_name,
	"\tgsSPObjSprite(&%s_obj)," % args.sprite_name,
	"\tgsSPEndDisplayList(),",
	])
	imstr+="\n};"
	return imstr


def make_ani_sprite_dl(args):
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
