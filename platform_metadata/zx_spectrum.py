from enum import Enum, auto

from software_list_info import get_software_list_entry

class ZXJoystick(Enum):
	Cursor = 0
	Kempton = 1
	SinclairLeft = 2 #For .z80 v3 this is user defined
	SinclairRight = 3

class ZXMachine(Enum):
	ZX16k = auto()
	ZX48k = auto()
	ZX128k = auto()
	SpectrumPlus2 = auto()
	SpectrumPlus2A = auto()
	SpectrumPlus3 = auto()
	#Unofficial machines
	Pentagon = auto() #128K
	Scorpion = auto() #256K
	DidaktikKompakt = auto()
	TimexComputer2048 = auto()
	TimexComputer2068 = auto()
	TimexSinclair2068 = auto() #48K

class ZXExpansion(Enum):
	Interface1 = auto()
	Interface2 = auto()
	MGT = auto()
	SamRam = auto()
	Multiface = auto()
	Kempton = auto()
	Opus = auto()
	Protek = auto()
	TRBeta = auto()

zx_hardware = {
	#For .z80 header
	0: (ZXMachine.ZX48k, None),
	1: (ZXMachine.ZX48k, ZXExpansion.Interface1),
	2: (ZXMachine.ZX48k, ZXExpansion.SamRam),
	3: (ZXMachine.ZX48k, ZXExpansion.MGT),
	4: (ZXMachine.ZX128k, None),
	5: (ZXMachine.ZX128k, ZXExpansion.Interface1),
	6: (ZXMachine.ZX128k, ZXExpansion.MGT),
	7: (ZXMachine.SpectrumPlus3, None),
	9: (ZXMachine.Pentagon, None),
	10: (ZXMachine.Scorpion, None),
	11: (ZXMachine.DidaktikKompakt, None),
	12: (ZXMachine.SpectrumPlus2, None),
	13: (ZXMachine.SpectrumPlus2A, None),
	14: (ZXMachine.TimexComputer2048, None),
	15: (ZXMachine.TimexComputer2068, None),
	16: (ZXMachine.TimexSinclair2068, None),
}

def add_z80_metadata(game):
	#https://www.worldofspectrum.org/faq/reference/z80format.htm
	header = game.rom.read(amount=86)
	flags = header[29]
	joystick_flag = (flags & 0b_1100_0000) >> 6
	game.metadata.specific_info['Joystick-Type'] = ZXJoystick(joystick_flag)
	#Does joystick_flag == 1 imply expansion == Kempston?

	program_counter = int.from_bytes(header[6:8], 'little')
	if program_counter != 0:
		header_version = 1
		#v1 can only save 48k snapshots
		machine = ZXMachine.ZX48k
		expansion = None #Presumably
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
		elif hardware_mode in zx_hardware:
			machine, expansion = zx_hardware[hardware_mode]

		if hardware_modifier_flag and machine == ZXMachine.ZX48k:
			machine = ZXMachine.ZX16k
		elif hardware_modifier_flag and machine == ZXMachine.ZX128k:
			machine = ZXMachine.SpectrumPlus2
		elif hardware_modifier_flag and machine == ZXMachine.SpectrumPlus3:
			machine = ZXMachine.SpectrumPlus2A

	game.metadata.specific_info['Machine'] = machine
	if expansion:
		game.metadata.specific_info['Expansion'] = expansion

	game.metadata.specific_info['ROM-Format'] = 'Z80 v%d' % header_version

def _set_mame_driver(game, machine):
	driver = {
		ZXMachine.ZX16k: 'spectrum',
		ZXMachine.ZX48k: 'spectrum',
		ZXMachine.ZX128k: 'spec128',
		ZXMachine.SpectrumPlus2: 'specpls2',
		ZXMachine.SpectrumPlus2A: 'specpl2a',
		ZXMachine.SpectrumPlus3: 'specpls3',
		ZXMachine.Pentagon: 'pentagon',
		ZXMachine.Scorpion: 'scorpio',
		ZXMachine.DidaktikKompakt: 'didaktk',
		ZXMachine.TimexComputer2048: 'tc2048',
		#ZXMachine.TimexComputer2068: '', #???
		ZXMachine.TimexSinclair2068: 'ts2068',
	}.get(machine)
	if driver:
		game.metadata.mame_driver = driver

def add_speccy_metadata(game):
	if game.rom.extension == 'z80':
		add_z80_metadata(game)

	if 'Machine' not in game.metadata.specific_info:
		for tag in game.filename_tags:
			if tag == '(16K)':
				game.metadata.specific_info['Machine'] = ZXMachine.ZX16k
				break
			if tag == '(48K)':
				game.metadata.specific_info['Machine'] = ZXMachine.ZX48k
				break
			if tag in ('(48K-128K)', '(128K)'):
				game.metadata.specific_info['Machine'] = ZXMachine.ZX128k
				break

	software = get_software_list_entry(game)
	if software:
		software.add_generic_info(game)
		usage = software.get_info('usage')
		if usage == 'Requires Multiface':
			game.metadata.specific_info['Expansion'] = ZXExpansion.Multiface
		elif usage == 'Requires Gun Stick light gun':
			#This could either go into the Sinclair Interface 2 or Kempton expansions, so.. hmm
			game.metadata.specific_info['Uses-Gun'] = True
		else:
			#Side B requires Locomotive CP/M+
			#Requires manual for password protection
			#Disk has no autorun menu, requires loading each game from Basic.
			game.metadata.notes = usage

	_set_mame_driver(game, game.metadata.specific_info.get('Machine'))
