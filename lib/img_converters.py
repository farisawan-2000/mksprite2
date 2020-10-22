
clamp = lambda x : (int(x) & 0x1F)
def to5551(t):
	r = (t[0] / 255) * 31
	g = (t[1] / 255) * 31
	b = (t[2] / 255) * 31
	a = 0
	if len(t) == 4:
		if t[3] == 255:
			a = 1
	return ((clamp(r) << 11)) | (clamp(g) << 6) | (clamp(b) << 1) | a

def to8888(t):
	return (t[0] << 24) | (t[1] << 16) | (t[2] << 8) | t[3]

