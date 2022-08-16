from collections.abc import Collection
from typing import TYPE_CHECKING, NamedTuple, Optional
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.platform_types import ZXExpansion, ZXJoystick, ZXMachine

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom_game import ROMGame
	from meowlauncher.metadata import Metadata

class ZXHardware(NamedTuple):
	machine: ZXMachine
	expansion: Optional[ZXExpansion]

_zx_hardware: dict[int, ZXHardware] = {
	#For .z80 header
	0: ZXHardware(ZXMachine.ZX48k, None),
	1: ZXHardware(ZXMachine.ZX48k, ZXExpansion.Interface1),
	2: ZXHardware(ZXMachine.ZX48k, ZXExpansion.SamRam),
	3: ZXHardware(ZXMachine.ZX48k, ZXExpansion.MGT),
	4: ZXHardware(ZXMachine.ZX128k, None),
	5: ZXHardware(ZXMachine.ZX128k, ZXExpansion.Interface1),
	6: ZXHardware(ZXMachine.ZX128k, ZXExpansion.MGT),
	7: ZXHardware(ZXMachine.SpectrumPlus3, None),
	9: ZXHardware(ZXMachine.Pentagon, None),
	10: ZXHardware(ZXMachine.Scorpion, None),
	11: ZXHardware(ZXMachine.DidaktikKompakt, None),
	12: ZXHardware(ZXMachine.SpectrumPlus2, None),
	13: ZXHardware(ZXMachine.SpectrumPlus2A, None),
	14: ZXHardware(ZXMachine.TimexComputer2048, None),
	15: ZXHardware(ZXMachine.TimexComputer2068, None),
	16: ZXHardware(ZXMachine.TimexSinclair2068, None),
}

def add_z80_metadata(rom: 'FileROM', metadata: 'Metadata') -> None:
	#https://www.worldofspectrum.org/faq/reference/z80format.htm
	header = rom.read(amount=86)
	flags = header[29]
	joystick_flag = (flags & 0b_1100_0000) >> 6
	metadata.specific_info['Joystick Type'] = ZXJoystick(joystick_flag)
	#Does joystick_flag == 1 imply expansion == Kempston?

	program_counter = int.from_bytes(header[6:8], 'little')
	machine: ZXMachine = ZXMachine.ZX48k
	expansion = None
	if program_counter != 0:
		header_version = 1
		#v1 can only save 48k snapshots and presumably doesn't do expansions
	else:
		header_length = int.from_bytes(header[30:32], 'little')
		if header_length == 23:
			header_version = 2
		else:
			#header_length should be 54 or 55, apparently
			header_version = 3

		hardware_mode = header[34]
		hardware_flags = header[37]
		hardware_modifier_flag = hardware_flags & 0b_1000_0000

		if header_version == 2 and hardware_mode == 3:
			machine = ZXMachine.ZX128k
			expansion = None
		elif header_version == 2 and hardware_mode == 4:
			machine = ZXMachine.ZX128k
			expansion = ZXExpansion.Interface1
		elif hardware_mode in _zx_hardware:
			machine, expansion = _zx_hardware[hardware_mode]

		if hardware_modifier_flag and machine == ZXMachine.ZX48k:
			machine = ZXMachine.ZX16k
		elif hardware_modifier_flag and machine == ZXMachine.ZX128k:
			machine = ZXMachine.SpectrumPlus2
		elif hardware_modifier_flag and machine == ZXMachine.SpectrumPlus3:
			machine = ZXMachine.SpectrumPlus2A

	metadata.specific_info['Machine'] = machine
	if expansion:
		metadata.specific_info['Expansion'] = expansion

	metadata.specific_info['ROM Format'] = f'Z80 v{header_version}'

def add_speccy_software_list_metadata(software: 'Software', metadata: 'Metadata') -> None:
	software.add_standard_metadata(metadata)
	usage = software.infos.get('usage')
	if usage == 'Requires Multiface':
		metadata.specific_info['Expansion'] = ZXExpansion.Multiface
	elif usage == 'Requires Gun Stick light gun':
		#This could either go into the Sinclair Interface 2 or Kempton expansions, so.. hmm
		metadata.specific_info['Uses Gun?'] = True
	else:
		#Side B requires Locomotive CP/M+
		#Requires manual for password protection
		#Disk has no autorun menu, requires loading each game from Basic.
		metadata.add_notes(usage)

def add_speccy_filename_tags_info(tags: Collection[str], metadata: 'Metadata') -> None:
	if 'Machine' in metadata.specific_info:
		return

	for tag in tags:
		if tag == '(16K)':
			metadata.specific_info['Machine'] = ZXMachine.ZX16k
			break
		if tag == '(48K)':
			metadata.specific_info['Machine'] = ZXMachine.ZX48k
			break
		if tag in {'(48K-128K)', '(128K)'}:
			metadata.specific_info['Machine'] = ZXMachine.ZX128k
			break

def add_speccy_custom_info(game: 'ROMGame') -> None:
	if isinstance(game.rom, FileROM):
		if game.rom.extension == 'z80':
			add_z80_metadata(game.rom, game.metadata)

	add_speccy_filename_tags_info(game.filename_tags, game.metadata)

	software = game.get_software_list_entry()
	if software:
		add_speccy_software_list_metadata(software, game.metadata)
