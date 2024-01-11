from typing import TYPE_CHECKING, NamedTuple

from meowlauncher.common_types import ByteAmount
from meowlauncher.platform_types import ZXExpansion, ZXJoystick, ZXMachine

if TYPE_CHECKING:
	from collections.abc import Collection

	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.info import GameInfo

class ZXHardware(NamedTuple):
	machine: ZXMachine
	expansion: ZXExpansion | None

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
	128: ZXHardware(ZXMachine.TimexSinclair2068, None),
}

def add_z80_metadata(rom: 'FileROM', game_info: 'GameInfo') -> None:
	"""https://www.worldofspectrum.org/faq/reference/z80format.htm"""
	header = rom.read(amount=86)
	flags = header[29]
	joystick_flag = (flags & 0b_1100_0000) >> 6
	game_info.specific_info['Joystick Type'] = ZXJoystick(joystick_flag)
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

	game_info.specific_info['Machine'] = machine
	if expansion:
		game_info.specific_info['Expansion'] = expansion

	game_info.specific_info['ROM Format'] = f'Z80 v{header_version}'

def add_speccy_software_list_info(software: 'Software', game_info: 'GameInfo') -> None:
	software.add_standard_info(game_info)
	usage = software.infos.get('usage')
	if usage == 'Requires Multiface':
		game_info.specific_info['Expansion'] = ZXExpansion.Multiface
	elif usage == 'Requires Gun Stick light gun':
		#This could either go into the Sinclair Interface 2 or Kempton expansions, so.. hmm
		game_info.specific_info['Uses Gun?'] = True
	else:
		#Side B requires Locomotive CP/M+
		#Requires manual for password protection
		#Disk has no autorun menu, requires loading each game from Basic.
		game_info.add_notes(usage)

def _machine_from_tag(tag: str) -> ZXMachine | None:
	if tag == '(+2)':
		return ZXMachine.SpectrumPlus2
	if tag == '(+2a)':
		return ZXMachine.SpectrumPlus2A
	if tag == '(+3)':
		return ZXMachine.SpectrumPlus3

	return None	

def _ram_requirement_from_tag(tag: str)	-> tuple[ByteAmount, ByteAmount] | None:
	"""Minimum, recommended
	TODO: Should this be a more generic function somewhere else?"""
	if tag == '(16K)':
		return ByteAmount(16 * 1024), ByteAmount(16 * 1024)
	if tag == '(48K)':
		return ByteAmount(48 * 1024), ByteAmount(48 * 1024)
	if tag == '(48K-128K)':
		#I _think_ that's what this means… or is it maximum?
		return ByteAmount(48 * 1024), ByteAmount(128 * 1024)
	if tag == '(128K)':
		return ByteAmount(128 * 1024), ByteAmount(128 * 1024)
	return None

def add_speccy_filename_tags_info(tags: 'Collection[str]', game_info: 'GameInfo') -> None:
	for tag in tags:
		if 'Machine' not in game_info.specific_info:
			machine = _machine_from_tag(tag)
			if machine:
				game_info.specific_info['Machine'] = machine
				break
		ram_requirement = _ram_requirement_from_tag(tag)
		if ram_requirement:
			game_info.specific_info['Minimum RAM'], game_info.specific_info['Recommended RAM'] = ram_requirement
			break

def add_speccy_rom_info(rom: 'FileROM', game_info: 'GameInfo') -> None:
	if rom.extension == 'z80':
		add_z80_metadata(rom, game_info)
