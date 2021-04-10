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
			for f in os.path.scandir(self.path):
				if f.is_dir() and f.name.lower() == subpath.lower():
					return f.path
		return path
	
	def get_file(self, subpath, ignore_case=False):
		path = os.path.join(self.path, subpath)
		if os.path.isfile(path):
			return path
		if ignore_case and subpath:
			for f in os.path.scandir(self.path):
				if f.is_file() and f.name.lower() == subpath.lower():
					return f.path
		return path

	def has_subfolder(self, subpath):
		return os.path.isdir(os.path.join(self.path, subpath))
	
	def has_file(self, subpath):
		return os.path.isfile(os.path.join(self.path, subpath))
	
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

def is_wii_u_folder(folder):
	#If we find a digital dump we stop there instead of descending into it
	if folder.has_subfolder('code') and folder.has_subfolder('content') and folder.has_subfolder('meta'):
		for f in os.scandir(folder.get_subfolder('code')):
			if f.is_file() and f.name.endswith('.rpx'):
				folder.relevant_files['rpx'] = f.path
				return MediaType.Digital
	return None

folder_checks = {
	'Wii U': is_wii_u_folder,
}

