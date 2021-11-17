import os
from collections.abc import Callable
from typing import Optional

from meowlauncher.common_types import MediaType
from meowlauncher.games.roms.rom import FolderROM


def is_wii_homebrew_folder(folder: FolderROM) -> Optional[MediaType]:
	have_boot_dol = False
	have_meta_xml = False
	for f in folder.path.iterdir():
		if f.is_file() and f.suffix.lower() in (os.path.extsep + 'dol', os.path.extsep + 'elf'):
			folder.relevant_files['boot.dol'] = f
			have_boot_dol = True
		if f.is_file() and f.name.lower() == 'meta.xml':
			folder.relevant_files['meta.xml'] = f
			have_meta_xml = True
	#I dunno if icon is _always_ needed but eh
	return MediaType.Digital if (have_meta_xml and have_boot_dol) else None

def is_wii_u_folder(folder: FolderROM) -> Optional[MediaType]:
	#If we find a digital dump we stop there instead of descending into it
	#Note: If there are two rpxes (I swear I've seen that once) you want the one referred to in cos.xml, is that file always there?
	code_subfolder = folder.get_subfolder('code')
	if code_subfolder and folder.has_subfolder('content') and folder.has_subfolder('meta'):
		for f in code_subfolder.iterdir():
			if f.is_file() and f.name.endswith('.rpx'):
				folder.relevant_files['rpx'] = f
				#Also applicable to extracted disc dumps, but that's just how my file type thing works, and I kinda wonder if I should have done that
				return MediaType.Digital
	return None

def is_ps3_folder(folder: FolderROM) -> Optional[MediaType]:
	if folder.has_subfolder('PS3_GAME') and folder.has_file('PS3_DISC.SFB'):
		#exe = PS3_GAME/USRDIR/EBOOT.BIN (PS3_GAME has PARAM.SFO and fun stuff)
		return MediaType.OpticalDisc
	if folder.has_file('PARAM.SFO') and folder.has_subfolder('USRDIR'):
		#Hmm this technically applies to the PS3_GAME subfolder of a disc game
		return MediaType.Digital
	return None

folder_checks: dict[str, Callable[[FolderROM], Optional[MediaType]]] = {
	'PS3': is_ps3_folder,
	'Wii': is_wii_homebrew_folder,
	'Wii U': is_wii_u_folder,
}
