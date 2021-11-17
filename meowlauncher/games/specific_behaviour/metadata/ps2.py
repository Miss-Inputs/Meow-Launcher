import io
import re

from meowlauncher.config.main_config import main_config
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Date, Metadata
from meowlauncher.util.region_info import TVSystem

from .common.playstation_common import parse_product_code

try:
	import struct  # To handle struct.error

	from pycdlib import PyCdlib
	from pycdlib.pycdlibexception import PyCdlibInvalidInput, PyCdlibInvalidISO
	have_pycdlib = True
except ModuleNotFoundError:
	have_pycdlib = False

boot_line_regex = re.compile(r'^BOOT2\s*=\s*cdrom0:\\(.+);1$')
vmode_line_regex = re.compile(r'^VMODE\s*=\s*(\S+)$')
boot_file_regex = re.compile(r'^(.{4})_(.{3})\.(.{2})$')

def add_info_from_system_cnf(metadata: Metadata, system_cnf: str):
	for line in system_cnf.splitlines():
		boot_line_match = boot_line_regex.match(line)
		if boot_line_match:
			filename = boot_line_match[1]
			boot_file_match = boot_file_regex.match(filename)
			if boot_file_match:
				metadata.product_code = boot_file_match[1] + '-' + boot_file_match[2] + boot_file_match[3]
				#Can look this up in /usr/local/share/games/PCSX2/GameIndex.dbf to get PCSX2 compatibility I guess
		#Other lines: VER (disc revision e.g. 1.00)
		else:
			vmode_line_match = vmode_line_regex.match(line)
			if vmode_line_match:
				try:
					metadata.specific_info['TV Type'] = TVSystem[vmode_line_match[1]]
				except ValueError:
					pass

def add_ps2_metadata(game: ROMGame):
	#.bin/cue also has this system.cnf but I'd need to know how to get pycdlib to work with that
	if game.rom.extension == 'iso' and have_pycdlib:
		iso = PyCdlib()
		try:
			iso.open(game.rom.path)
			system_cnf_buf = io.BytesIO()
			try:
				#I dunno what the ;1 is for
				iso.get_file_from_iso_fp(system_cnf_buf, iso_path='/SYSTEM.CNF;1')
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

				system_cnf = system_cnf_buf.getvalue().decode('utf-8', errors='backslashreplace')
				add_info_from_system_cnf(game.metadata, system_cnf)
			except PyCdlibInvalidInput:
				if main_config.debug:
					print(game.rom.path, 'has no SYSTEM.CNF inside')
			#Sometimes there is a system.ini that looks like this:
			#[SYSTEM]
			#NUMBER = SLUS-21448
			#VERSION = 100
			#VMODE = NTSC
			#COUNTRY = AMERICA
			#LANGUAGE = ENGLISH
			#WARNING = NO
		except PyCdlibInvalidISO as ex:
			if main_config.debug:
				print(game.rom.path, 'is invalid ISO', ex)
		except struct.error as ex:
			print(game.rom.path, 'is invalid ISO and has some struct.error', ex)
	#.elf is just a standard ordinary whole entire .elf
	if game.metadata.product_code:
		parse_product_code(game.metadata, game.metadata.product_code)