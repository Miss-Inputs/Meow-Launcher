#For mildly uninteresting systems that I still want to add system info for etc

from metadata import PlayerInput, InputType, SaveType
from info.region_info import TVSystem
from .software_list_info import add_generic_software_list_info, get_software_info, get_software_list_entry, get_part_feature

def add_entex_adventure_vision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	game.metadata.input_info.players.append(player)

	#I don't think so mate
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_game_pocket_computer_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4
	game.metadata.input_info.players.append(player)

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_gamate_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_casio_pv1000_info(game):
	game.metadata.tv_type = TVSystem.NTSC #Japan only. I won't assume the region in case some maniac decides to make homebrew for it or something, but it could only ever be NTSC
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Start, select, A, and B. And to think some things out there say it only has 1 button... Well, I've also heard start and select are on the console, so maybe MAME is being a bit weird
	game.metadata.input_info.players += [player] * 2

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_mega_duck_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
	
def add_watara_supervision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing
	
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_apfm1000_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#There's not really anything in there which tells us if we need the Imagination Machine for a particular cart. There's something about RAM, though.

def add_arcadia_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#Nothing really here other than alt titles (for other languages). I guess this proves that the Bandai Arcadia really isn't different.

def add_astrocade_info(game):
	#TODO: Input info should always be keypad... I think?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)

def add_casio_pv2000_info(game):
	#Input info is keyboard and joystick I guess? Maybe only one of them sometimes?

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_channel_f_info(game):
	#Input info is uhhh that weird twisty thing I guess

	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)

def add_msx_info(game):
	#I'll use this for MSX2 as well for now
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)	
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#Other info you can get from carts here: PCB, slot (something like ascii8 or whatever), mapper

def add_pc88_info(game):
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Floppy-ID'] = get_part_feature(part, 'part_id')

def add_sg1000_info(game):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	uses_tablet = False
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		uses_tablet = get_part_feature(part, 'peripheral') == 'tablet'
		#There doesn't seem to be a way to know if software is a SC-3000 cart, unless I just say whichever one has the .sc extension. Maybe Uranai Angel Cutie is just compatible anyway? I forgot
	
	player = PlayerInput()
	if uses_tablet:
		#A drawing tablet, but that's more or less a touchscreen
		#No buttons here?
		player.inputs = [InputType.Touchscreen]
	else:
		player.inputs = [InputType.Digital]
		player.buttons = 2
	game.metadata.input_info.players += [player] * 2
	game.metadata.input_info.console_buttons = 2 #Reset, Pause/Hold

def add_sharp_x1_info(game):
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Floppy-ID'] = get_part_feature(part, 'part_id')

def add_sharp_x68k_info(game):
	#Many games are known to have SaveType.Floppy, but can't tell programmatically...
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Floppy-ID'] = get_part_feature(part, 'part_id')

def add_tomy_tutor_info(game):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_vc4000_info(game):
	#Until proven otherwise
	game.metadata.save_type = SaveType.Nothing

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_vic10_info(game):
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#What the heck is an "assy"?

def add_vic20_info(game):
	#TODO: Is it possible that .a0 etc might have the header too? It shouldn't, but y'know
	#This won't work with >8KB carts at the moment, because MAME stores those in the software list as two separate ROMs. But then they won't have launchers anyway because our only emulator for VIC-20 is MAME itself, and it doesn't let us just put the two ROMs together ourselves, those games are basically software list only at the moment (because it won't let us have one single file above 8KB).
	has_header = game.rom.extension in ('prg', 'crt') and (game.rom.get_size() % 256) == 2
	software, part = get_software_list_entry(game, skip_header=2 if has_header else 0)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#TODO: Get sharedfeat = compatibility to get TV type		

def add_sord_m5_info(game):
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		#Take note of info > usage = requiring 36K RAM, though we just set our M5 to have max RAM anyway, seems to be harmless

def add_gx4000_info(game):
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)

#-- Beyond this point, there may be unexplored things which may result in these systems being spun off into their own module. Maybe. It just seems likely. Or maybe I do know full well they have a header, and either I haven't explored it yet, or I'm just a lazy bugger

def add_juicebox_info(game):
	#Hmm... apparently there's 0x220 bytes at the beginning which need to be copied from retail carts to get homebrew test ROMs to boot
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_atari_5200_info(game):
	#Can get the title screen information from inside the ROM to get the year (and also title). But that's hella unreliable, won't work properly for homebrews released after 2000, and requires implementing the 5200 title screen's custom character set (which I do know, it's just a pain in the arse)

	uses_trackball = False
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
		uses_trackball = get_part_feature(part, 'peripheral') == 'trackball'

	game.metadata.save_type = SaveType.Nothing #Probably
	
	#This doesn't really matter anyway, because MAME doesn't let you select controller type by slot device yet; and none of the other 5200 emulators are cool
	game.metadata.specific_info['Uses-Trackball'] = uses_trackball
	player = PlayerInput()
	if uses_trackball:
		player.inputs = [InputType.Trackball]
	else:
		player.inputs = [InputType.Analog]
	player.buttons = 5 #1, 2, Pause, Reset, Start I think? I think it works the same way for trackballs
	game.metadata.input_info.players += [player] * 4 #wew
	#No console buttons actually, apart from power which hardly counts

def add_uzebox_info(game):
	#TODO: .uze files have 512-byte header, just not much info that we can't already get from software lists
	#But there is an icon at 0x4e:0x14d, just apparently never used; and SNES mouse usage at 0x152

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_pce_info(game):
	#Input could be 2 buttons or 6 buttons, usually the former. Might be other types too?
	#Some games should have saving via TurboBooster-Plus (Wii U VC seems to let me save in Neutopia anyway without passwords or savestates), which I guess would be SaveType.Internal
	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#Other info: alt_title, release (that seems to be a date, I'm not sure if it always is though)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_game_com_info(game):
	#Could have its own header. I think it does, but like.. who's gonna document such a thing? The wide community of Game.com enthusiasts?
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #A B C D
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 3 #Menu Sound Pause
	
	#Might have saving, actually. I'm just not sure about how it works.

	software, part = get_software_list_entry(game)
	if software:
		add_generic_software_list_info(game, software)
		#This will tell you that nothing is supported. I think that sometimes the MAME devs are too hard on themselves. Someone needs to cheer them up a bit.
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')

def add_lynx_info(game):
	#TODO .lnx files should have a header with something in them, so eventually, Lynx will get its own module here
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 1 #Pause

	software, part = get_software_list_entry(game, skip_header=64)
	if software:
		add_generic_software_list_info(game, software)
		game.metadata.specific_info['Product-Code'] = get_software_info(software, 'serial')
