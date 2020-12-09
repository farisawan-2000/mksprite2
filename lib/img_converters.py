
clamp = lambda x : (int(x) & 0x1F)
def to5551(t):
	r = (t[0] / 255) * 31
	g = (t[1] / 255) * 31
	b = (t[2] / 255) * 31
	a = 1
	if len(t) == 4:
		if t[3] <= 50:
			a = 0
	return ((clamp(r) << 11)) | (clamp(g) << 6) | (clamp(b) << 1) | a

u8 = lambda x : (x & 0xFF)

def to8888(t):
	return (u8(t[0]) << 24) | (u8(t[1]) << 16) | (u8(t[2]) << 8) | u8(t[3])

u4 = lambda x : (int(x) & 0xF)
avg3 = lambda x : ((x[0] + x[1] + x[2]) / 3)

def toia8(t):
	if len(t) == 4:
		return ((u4(avg3(t) / 16) << 4) | (u4(t[3] / 16)))
	elif len(t) == 3:
		return ((u4(avg3(t) / 16) << 4) | (u4(0xFF / 16)))
	elif len(t) == 2:
		return ((u4(t[0] / 16) << 4) | (u4(t[1] / 16)))
	else:
		return ((u4(t[0] / 16) << 4) | (u4(0xFF / 16)))

def toci4(t1, t2, pal_list):
	if t1 not in pal_list:
		pal_list.append(t1)
	if t2 not in pal_list:
		pal_list.append(t2)
	return (u4(pal_list.index(t1)) << 4 | u4(pal_list.index(t2)))