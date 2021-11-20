
#For info_helpers.static_info_funcs
from typing import TYPE_CHECKING

from meowlauncher.input_metadata import CombinedController, Keyboard, Keypad, NormalController, Paddle, Touchscreen
from meowlauncher.common_types import SaveType

if TYPE_CHECKING:
	from meowlauncher.metadata import Metadata

def add_game_gear_info(metadata: 'Metadata'):
	#Because there's no accessories to make things confusing, we can assume the Game Gear's input info, but not the Master System's
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #'1' on left, '2' on right
	metadata.input_info.add_option(builtin_gamepad)

def add_entex_adventure_vision_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	metadata.input_info.add_option(builtin_gamepad)

	#I don't think so mate
	metadata.save_type = SaveType.Nothing

def add_game_pocket_computer_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_gamate_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_casio_pv1000_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)
	#(Start, select,) A, and B. And to think some things out there say it only has 1 button... Well, I've also heard start and select are on the console, so maybe MAME is being a bit weird

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_mega_duck_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)
	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_watara_supervision_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_arcadia_info(metadata: 'Metadata'):
	keypad = Keypad() #2 controllers hardwired into the system. If MAME is any indication, the buttons on the side don't do anything or are equivalent to keypad 2?
	keypad.keys = 12 #MAME mentions 16 here... maybe some variant systems have more
	stick = NormalController()
	stick.analog_sticks = 1 #According to MAME it's an analog stick but everywhere else suggests it's just digital?
	#controller.face_buttons = 2 #???? Have also heard that the 2 buttons do the same thing as each other
	controller = CombinedController([keypad, stick])
	metadata.input_info.add_option(controller)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_astrocade_info(metadata: 'Metadata'):
	joystick = NormalController()
	joystick.dpads = 1
	joystick.face_buttons = 1 #Sort of a trigger button, as it's a gun-shaped grip
	#Controller also integrates a paddle

	keypad = Keypad() #Mounted onto the system
	keypad.keys = 24

	controller = CombinedController([joystick, keypad, Paddle()])
	metadata.input_info.add_option(controller)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_vc4000_info(metadata: 'Metadata'):
	normal_controller = NormalController()
	normal_controller.analog_sticks = 1
	normal_controller.face_buttons = 2

	keypad = Keypad()
	keypad.keys = 12

	controller = CombinedController([normal_controller, keypad])
	metadata.input_info.add_option(controller)

	#Until proven otherwise
	metadata.save_type = SaveType.Nothing

def add_hartung_game_master_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

def add_vz200_info(metadata: 'Metadata'):
	keyboard = Keyboard()
	keyboard.keys = 45
	#There are in theory joysticks, but they don't seem to ever be a thing
	metadata.input_info.add_option(keyboard)

def add_bandai_sv8000_info(metadata: 'Metadata'):
	keypad = Keypad() #2 of these
	keypad.keys = 12 #Digits + # *
	joystick = NormalController()
	joystick.dpads = 1 #Keypad with a disc thing on it

	metadata.save_type = SaveType.Nothing #I think not

	controller = CombinedController([keypad, joystick])
	metadata.input_info.add_option(controller)

def add_nichibutsu_my_vision_info(metadata: 'Metadata'):
	buttons = NormalController() #Not normal, but closest there is
	#It's like a keyboard except not; MAME defines it as 14-button "mahjong" + 8-way joystick with 1 button and hmm
	buttons.face_buttons = 19 #Numbered 1 to 14 in a row, then A B C D arranged in directions above that, and an E button next to that
	metadata.input_info.add_option(buttons)

def add_bbc_bridge_companion_info(metadata: 'Metadata'):
	buttons = NormalController()
	buttons.face_buttons = 10 #According to the MAME driver, I'm too lazy to look at pictures of the thing
	metadata.input_info.add_option(buttons)

	metadata.save_type = SaveType.Nothing #Yeah nah

def add_cd32_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)

def add_neogeo_cd_info(metadata: 'Metadata'):
	#Apparently there is a mahjong controller too, but... meh
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	metadata.input_info.add_option(builtin_gamepad)

def add_juicebox_info(metadata: 'Metadata'):
	#Hmm... apparently there's 0x220 bytes at the beginning which need to be copied from retail carts to get homebrew test ROMs to boot
	builtin_gamepad = NormalController()
	builtin_gamepad.face_buttons = 5 #Rewind/forward/stop/play/function
	metadata.input_info.add_option(builtin_gamepad)

	metadata.save_type = SaveType.Nothing #Nope!

def add_super_cassette_vision_info(metadata: 'Metadata'):
	keypad = Keypad() #Part of main body of console
	keypad.keys = 12 #Digits + CL EN

	joystick = NormalController() #2 of them hardwired in
	joystick.face_buttons = 2

	metadata.input_info.add_option([keypad, joystick])

def add_super_acan_info(metadata: 'Metadata'):
	controller = NormalController()
	controller.shoulder_buttons = 2
	controller.dpads = 1
	controller.face_buttons = 4 #Also Select + Start
	metadata.input_info.add_option(controller)

def add_vsmile_info(metadata: 'Metadata'):
	controller = NormalController()
	controller.analog_sticks = 1 #Hmm MAME has it as a digital joystick with 8 buttons but Wikipedia says analog, whomst is correct? I dunno
	controller.face_buttons = 4 #Also enter + Learning Zone + exit + help

	metadata.input_info.add_option(controller)

def add_vsmile_babby_info(metadata: 'Metadata'):
	controller = NormalController()
	controller.face_buttons = 6 #5 shapes + "fun button" (aka cloud) + apparently the ball is actually just a button; also exit

	metadata.input_info.add_option(controller)

def add_pokemini_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()

	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 1 #C
	metadata.input_info.add_option(builtin_gamepad)
	#Technically you could say Motion Controls because of the shake detection, but not all games use it, and you can't really tell which do and which don't programmatically

def add_gba_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B
	builtin_gamepad.shoulder_buttons = 2 #L R
	metadata.input_info.add_option(builtin_gamepad)

def add_benesse_v2_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 3 #I don't know what they're called
	metadata.input_info.add_option(builtin_gamepad)

def add_wonderswan_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	#Because of the rotation, it's hard to say which one of the sets of 4 buttons is the one used for directional control; but one of them will be
	builtin_gamepad.face_buttons = 6
	metadata.input_info.add_option(builtin_gamepad)

def add_gamecom_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #A B C D
	touchscreen = Touchscreen()
	metadata.input_info.add_option(CombinedController((builtin_gamepad, touchscreen)))

def add_vectrex_info(metadata: 'Metadata'):
	gamepad = NormalController()
	gamepad.face_buttons = 4 #All arranged in a row, not rectangle
	gamepad.analog_sticks = 1
	metadata.input_info.add_option(gamepad)
	#There's also a light pen but I dunno stuff about it or how to detect it so there's not a lot that can be done about it

def add_ngp_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 2 #A B, also Option (Option is just Start really but they have to be special and unique and not like the other girls)
	metadata.input_info.add_option(builtin_gamepad)

def add_virtual_boy_info(metadata: 'Metadata'):	
	gamepad = NormalController()
	gamepad.face_buttons = 2
	gamepad.shoulder_buttons = 2
	gamepad.dpads = 2
	metadata.input_info.add_option(gamepad)

def add_3ds_info(metadata: 'Metadata'):
	#Although we can't know for sure if the game uses the touchscreen, it's safe to assume that it probably does
	builtin_gamepad = NormalController()
	builtin_gamepad.analog_sticks = 1
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4
	builtin_gamepad.shoulder_buttons = 2

	controller = CombinedController([builtin_gamepad, Touchscreen()])
	metadata.input_info.add_option(controller)

def add_lynx_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.face_buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	metadata.input_info.add_option(builtin_gamepad)

def add_psp_info(metadata: 'Metadata'):
	builtin_gamepad = NormalController()
	builtin_gamepad.dpads = 1
	builtin_gamepad.analog_sticks = 1
	builtin_gamepad.face_buttons = 4 #also Start, Select, which I don't count because I just never have I guess
	builtin_gamepad.shoulder_buttons = 2
	metadata.input_info.add_option(builtin_gamepad)
