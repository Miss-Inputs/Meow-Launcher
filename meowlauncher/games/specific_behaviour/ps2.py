import logging
import re
import struct  # To handle struct.error
from typing import TYPE_CHECKING

try:
	from pycdlib import PyCdlib
	from pycdlib.pycdlibexception import PyCdlibInvalidInput, PyCdlibInvalidISO
	have_pycdlib = True
except ModuleNotFoundError:
	have_pycdlib = False

from meowlauncher.metadata import Date, Metadata
from meowlauncher.util.region_info import TVSystem

from .common.playstation_common import parse_product_code

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom_game import ROMGame

logger = logging.getLogger(__name__)

_boot_line_regex = re.compile(r'^BOOT2\s*=\s*cdrom0:\\(.+);1$')
_other_systemcnf_line_regex = re.compile(r'^([^=\s]+?)\s*=\s*(\S+)$')
_boot_file_regex = re.compile(r'^(.{4})_(.{3})\.(.{2})$')

def add_info_from_system_cnf(metadata: Metadata, system_cnf: str) -> None:
	for line in system_cnf.splitlines():
		boot_line_match = _boot_line_regex.match(line)
		if boot_line_match:
			filename = boot_line_match[1]
			metadata.specific_info['Executable Name'] = filename
			boot_file_match = _boot_file_regex.match(filename)
			if boot_file_match:
				metadata.product_code = boot_file_match[1] + '-' + boot_file_match[2] + boot_file_match[3]
				#Can look this up in /usr/local/share/games/PCSX2/GameIndex.dbf to get PCSX2 compatibility I guess
		else:
			other_line_match = _other_systemcnf_line_regex.match(line)
			if other_line_match:
				key = other_line_match[1]
				value = other_line_match[2]
				if key == 'VER':
					metadata.specific_info['Version'] = value
				elif key == 'VMODE':
					try:
						metadata.specific_info['TV Type'] = TVSystem[value]
					except ValueError:
						pass

def add_ps2_custom_info(game: 'ROMGame') -> None:
	#.bin/cue also has this system.cnf but I'd need to know how to get pycdlib to work with that
	if game.rom.extension == 'iso' and have_pycdlib:
		iso = PyCdlib()
		try:
			try:
				iso.open(str(game.rom.path))
				try:
					#I dunno what the ;1 is for
					with iso.open_file_from_iso(iso_path='/SYSTEM.CNF;1') as system_cnf_file:
						system_cnf = system_cnf_file.read().decode('utf-8', errors='backslashreplace')
					add_info_from_system_cnf(game.metadata, system_cnf)
					date_record = iso.get_record(iso_path='/SYSTEM.CNF;1').date
					#This would be more like a build date (seems to be the same across all files) rather than the release date, but it seems to be close enough
					year = date_record.years_since_1900 + 1900
					month = date_record.month
					day = date_record.day_of_month
					build_date = Date(year, month, day)
					game.metadata.specific_info['Build Date'] = build_date
					guessed_date = Date(year, month, day, True)
					if guessed_date.is_better_than(game.metadata.release_date):
						game.metadata.release_date = guessed_date
				except PyCdlibInvalidInput:
					logger.info('%s has no SYSTEM.CNF inside', game.rom)
				#Modules are in IOP, MODULES or IRX but I don't know if we can get any interesting info from that
				#TODO: Sometimes there is a system.ini that looks like this:
				#[SYSTEM]
				#NUMBER = SLUS-21448
				#VERSION = 100
				#VMODE = NTSC
				#COUNTRY = AMERICA
				#LANGUAGE = ENGLISH
				#WARNING = NO
			finally:
				iso.close()	
		except PyCdlibInvalidISO:
			logger.info('%s is invalid ISO', game.rom, exc_info=True)
		except struct.error:
			logger.info('%s is invalid ISO and has some struct.error', game.rom, exc_info=True)
	#.elf is just a standard ordinary whole entire .elf
	if game.metadata.product_code:
		parse_product_code(game.metadata, game.metadata.product_code)
