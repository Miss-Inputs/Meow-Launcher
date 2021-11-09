from meowlauncher import input_metadata
from meowlauncher.common_types import SaveType
from meowlauncher.metadata import Date
from meowlauncher.software_list_info import get_software_list_entry

atari_5200_charset = {
	#Lowercase here is used to represent rainbow characters, because how else am I gonna represent them? No really, I dunno
	0x00: ' ', #Maybe it's a rainbow space
	0x01: '!', #Rainbow
	0x07: '\'', #Rainbow
	0x0d: '-', #Rainbow
	0x0e: '.', #Rainbow
	0x10: '0', #Rainbow
	0x11: '1', #Rainbow
	0x12: '2', #Rainbow
	0x13: '3', #Rainbow
	0x14: '4', #Rainbow
	0x15: '5', #Rainbow
	0x16: '6', #Rainbow
	0x17: '7', #Rainbow
	0x18: '8', #Rainbow
	0x19: '9', #Rainbow
	0x20: '@', #Rainbow
	0x21: 'a',
	0x22: 'b',
	0x23: 'c',
	0x24: 'd',
	0x25: 'e',
	0x26: 'f',
	0x27: 'g',
	0x28: 'h',
	0x29: 'i',
	0x2a: 'j',
	0x2b: 'k',
	0x2c: 'l',
	0x2d: 'm',
	0x2e: 'n',
	0x2f: 'o',
	0x30: 'p',
	0x31: 'q',
	0x32: 'r',
	0x33: 's',
	0x34: 't',
	0x35: 'u',
	0x36: 'v',
	0x37: 'w',
	0x38: 'x',
	0x39: 'y',
	0x3a: 'z',
	0x40: ' ',
	0x41: '!',
	0x47: '\'',
	0x4e: '.',
	0x50: '0',
	0x51: '1',
	0x52: '2',
	0x53: '3',
	0x54: '4',
	0x55: '5',
	0x56: '6',
	0x57: '7',
	0x58: '8',
	0x59: '9',
	0x5a: ':',
	0x61: 'A',
	0x62: 'B',
	0x63: 'C',
	0x64: 'D',
	0x65: 'E',
	0x66: 'F',
	0x67: 'G',
	0x68: 'H',
	0x69: 'I',
	0x6a: 'J',
	0x6b: 'K',
	0x6c: 'L',
	0x6d: 'M',
	0x6e: 'N',
	0x6f: 'O',
	0x70: 'P',
	0x71: 'Q',
	0x72: 'R',
	0x73: 'S',
	0x74: 'T',
	0x75: 'U',
	0x76: 'V',
	0x77: 'W',
	0x78: 'X',
	0x79: 'Y',
	0x7a: 'Z',
	0xe1: ' ', #Not sure about this one, but it really does display as blank. Maybe all unknown characters just display as blank?
}

def add_crap_from_rom_header(rom, metadata):
	footer = rom.read(seek_to=rom.get_size() - 24, amount=24)
	year = footer[20:22] #Y2K incompliant whee
	#Entry point: 22-23, lil' endian
	if year[1] != 255: #If set to this, the BIOS is skipped?
		title_bytes = footer[:20].rstrip(b'\0')
		if title_bytes:
			title = ''.join([atari_5200_charset.get(b, '\0x{0:x}'.format(b)) for b in title_bytes])
			metadata.add_alternate_name(title.strip(), 'Banner-Title')
		try:
			year_first_digit = int(atari_5200_charset[year[0]])
			year_second_digit = int(atari_5200_charset[year[1]])
			terrible_date = Date(year=1900 + (year_first_digit * 10) + year_second_digit, is_guessed=True)
			if terrible_date.is_better_than(metadata.release_date):
				metadata.release_date = terrible_date
		except (ValueError, KeyError):
			pass
		
def add_atari_5200_metadata(game):
	add_crap_from_rom_header(game.rom, game.metadata)

	uses_trackball = False
	software = get_software_list_entry(game)
	if software:
		software.add_standard_metadata(game.metadata)
		uses_trackball = software.get_part_feature('peripheral') == 'trackball'

	game.metadata.save_type = SaveType.Nothing #Probably

	#This doesn't really matter anyway, because MAME doesn't let you select controller type by slot device yet; and none of the other 5200 emulators are cool
	game.metadata.specific_info['Uses-Trackball'] = uses_trackball

	if uses_trackball:
		game.metadata.input_info.add_option(input_metadata.Trackball())
	else:
		normal_controller = input_metadata.NormalController()
		normal_controller.face_buttons = 2 #1, 2, (Pause, Reset, Start) I think? I think it works the same way for trackballs
		normal_controller.analog_sticks = 1
		game.metadata.input_info.add_option(normal_controller)
