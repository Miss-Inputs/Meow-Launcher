from typing import TYPE_CHECKING

from meowlauncher.common_types import MediaType
if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FolderROM


def is_wii_homebrew_folder(folder: 'FolderROM') -> MediaType | None:
	have_boot_dol = False
	have_meta_xml = False
	for f in folder.path.iterdir():
		if f.is_file() and f.suffix[1:].lower() in {'dol', 'elf'}:
			folder.relevant_files['boot.dol'] = f
			have_boot_dol = True
		if f.is_file() and f.name.lower() == 'meta.xml':
			folder.relevant_files['meta.xml'] = f
			have_meta_xml = True
			
		if have_boot_dol and have_meta_xml:
			return MediaType.Digital
	#I dunno if icon is always there, so we will leave that alone
	return MediaType.Digital if (have_meta_xml and have_boot_dol) else None

def is_wii_u_folder(folder: 'FolderROM') -> MediaType | None:
	#If we find a digital dump we stop there instead of descending into it
	#Note: If there are two rpxes (I swear I've seen that once) you want the one referred to in cos.xml, is that file always there?
	code_subfolder = folder.get_subfolder('code')
	if code_subfolder and folder.has_subfolder('content') and folder.has_subfolder('meta'):
		for f in code_subfolder.iterdir():
			if f.is_file() and f.suffix == '.rpx':
				folder.relevant_files['rpx'] = f
				#Also applicable to extracted disc dumps, but that's just how my file type thing works, and I kinda wonder if I should have done that
				return MediaType.Digital
	return None

def is_ps3_folder(folder: 'FolderROM') -> MediaType | None:
	usrdir_subfolder = folder.get_subfolder('USRDIR')
	param_sfo = folder.get_file('PARAM.SFO')
	if param_sfo and usrdir_subfolder:
		folder.relevant_files['PARAM.SFO'] = param_sfo
		folder.relevant_files['USRDIR'] = usrdir_subfolder
		return MediaType.Digital
	if folder.has_file('PS3_DISC.SFB'):
		ps3_game_subfolder = folder.get_subfolder('PS3_GAME')
		if ps3_game_subfolder:
			ps3_extra_subfolder = folder.get_subfolder('PS3_EXTRA')
			if ps3_extra_subfolder:
				#Not sure if this is just for PSP remasters?
				folder.relevant_files['PARAM.SFO'] = ps3_extra_subfolder / 'PARAM.SFO'
				folder.relevant_files['USRDIR'] = ps3_extra_subfolder / 'USRDIR' #Might not exist?
			else:
				#I hope that these files exist or I will look like quite the fool I guess	
				folder.relevant_files['PARAM.SFO'] = ps3_game_subfolder / 'PARAM.SFO'
				folder.relevant_files['USRDIR'] = ps3_game_subfolder / 'USRDIR'
		return MediaType.OpticalDisc
	return None

def is_psp_homebrew_folder(folder: 'FolderROM') -> MediaType | None:
	pbp = folder.get_file('EBOOT.PBP')
	if pbp:
		folder.relevant_files['pbp'] = pbp
		return MediaType.Digital
	return None
