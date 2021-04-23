try:
	import machfs
	have_machfs = True
except ImportError:
	have_machfs = False

def get_path(volume, path):
	return volume[tuple(path.split(':'))]

def does_exist(hfv_path, path):
	if not have_machfs:
		#I guess it might just be safer to assume it's still there
		return True
	v = machfs.Volume()
	try:
		with open(hfv_path, 'rb') as f:
		#Hmm, this could be slurping very large (maybe gigabyte(s)) files all at once
			v.read(f.read())
			try:
				get_path(v, path)
				return True
			except KeyError:
				return False
	except FileNotFoundError:
		return False
