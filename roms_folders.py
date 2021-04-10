import os
from common_types import MediaType

class FolderROM():
	def __init__(self, path):
		self.path = path
		self.relevant_files = {}
		self.name = os.path.basename(path)
		self.media_type = None
		self.ignore_name = False
	
	def get_subfolder(self, subpath, ignore_case=False):
		path = os.path.join(self.path, subpath)
		if os.path.isdir(path):
			return path
		if ignore_case and subpath:
			for f in os.scandir(self.path):
				if f.is_dir() and f.name.lower() == subpath.lower():
					return f.path
		return path
	
	def get_file(self, subpath, ignore_case=False):
		path = os.path.join(self.path, subpath)
		if os.path.isfile(path):
			return path
		if ignore_case and subpath:
			for f in os.scandir(self.path):
				if f.is_file() and f.name.lower() == subpath.lower():
					return f.path
		return path

	def has_subfolder(self, subpath):
		return os.path.isdir(os.path.join(self.path, subpath))
	
	def has_file(self, subpath):
		return os.path.isfile(os.path.join(self.path, subpath))

	def has_any_file_with_extension(self, extension, ignore_case=False):
		if ignore_case:
			extension = extension.lower()
		for f in os.scandir(self.path):
			name = f.name
			if ignore_case:
				name = name.lower()
			if f.is_file() and f.name.endswith(os.path.extsep + extension):
				return True
		return False
	
	#The rest here will just be to make sure it works with RomFile
	@property
	def is_folder(self):
		return True
	
	@property
	def extension(self):
		return None

	@property
	def is_compressed(self):
		return False
#Basically we are just putting this here for platform-specific stuff
#I don't necessarily like hardcoding certain system's behaviour in here but I start overthinking otherwise and this is probably the only real way to do it

def is_wii_homebrew_folder(folder):
	have_boot_dol = False
	have_meta_xml = False
	for f in os.scandir(folder.path):
		if f.is_file() and f.name.lower().endswith((os.path.extsep + 'dol', os.path.extsep + 'elf')):
			folder.relevant_files['boot.dol'] = f.path
			have_boot_dol = True
		if f.is_file() and f.name.lower() == 'meta.xml':
			folder.relevant_files['meta.xml'] = f.path
			have_meta_xml = True
	#I dunno if icon is _always_ needed but eh
	return MediaType.Digital if (have_meta_xml and have_boot_dol) else None

def is_wii_u_folder(folder):
	#If we find a digital dump we stop there instead of descending into it
	#TODO: You could have two rpxes which is tricky (see also Wii U Sports Club (but do I care))
	if folder.has_subfolder('code') and folder.has_subfolder('content') and folder.has_subfolder('meta'):
		for f in os.scandir(folder.get_subfolder('code')):
			if f.is_file() and f.name.endswith('.rpx'):
				folder.relevant_files['rpx'] = f.path
				#Also applicable to extracted disc dumps, but that's just how my file type thing works, and I kinda wonder if I should have done that
				return MediaType.Digital
	return None

def is_ps3_folder(folder):
	if folder.has_subfolder('PS3_GAME') and folder.has_file('PS3_DISC.SFB'):
		#exe = PS3_GAME/USRDIR/EBOOT.BIN (PS3_GAME has PARAM.SFO and fun stuff)
		return MediaType.OpticalDisc
	if folder.has_file('PARAM.SFO') and folder.has_subfolder('USRDIR'):
		#Hmm this technically applies to the PS3_GAME subfolder of a disc game
		return MediaType.Digital
	return None

folder_checks = {
	'PS3': is_ps3_folder,
	'Wii': is_wii_homebrew_folder,
	'Wii U': is_wii_u_folder,
}

