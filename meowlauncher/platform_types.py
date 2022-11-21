#Enums etc to be used between platform_info and emulator_command_lines

from enum import Enum, IntEnum, auto


class AppleIIHardware(Enum):
	AppleII = auto()
	AppleIIPlus = auto()
	AppleIIE = auto()
	AppleIIC = auto()
	AppleIIEEnhanced = auto()
	AppleIIgs = auto()
	AppleIICPlus = auto()
	AppleIII = auto()
	AppleIIIPlus = auto()

class Atari2600Controller(Enum):
	Nothing = auto()
	Joystick = auto()
	Paddle = auto() #2 players per port
	Mouse = auto() #2 buttons, Stella lists an AMIGAMOUSE and ATARIMOUSE (ST mouse) and I dunno if those are functionally different
	Trackball = auto() #Functionally 1 button, but has 2 physical buttons to be ambidextrous; see atari_8_bit.py
	KeyboardController = auto() #This is... 2 keypads joined together (12 keys each)
	Compumate = auto() #42-key keyboard (part of a whole entire computer)
	MegadriveGamepad = auto() #See megadrive.py
	Boostergrip = auto() #Effectively a 3-button joystick, passes through to the standard 2600 joystick and adds 2 buttons
	DrivingController = auto() #Has 360 degree movement, so not quite like a paddle. MAME actually calls it a trackball
	Mindlink = auto()
	LightGun = auto() #Presumably this is the XEGS XG-1, which has 1 button (see atari_8_bit.py)
	Other = auto()
	#Light pen would also be possible

	#Not controllers but plug into the controller port:
	AtariVox = auto()
	SaveKey = auto()
	KidVid = auto()

class GameBoyColourFlag(IntEnum):
	No = 0
	Yes = 0x80
	Required = 0xc0
	#Ah yes, the three boolean values

class SMSPeripheral(Enum):
	StandardController = auto()
	Lightgun = auto()
	Paddle = auto()
	Tablet = auto()
	SportsPad = auto()

class MegadriveRegionCodes(Enum):
	Japan = auto() #J
	USA = auto() #U
	Europe = auto() #E

	#These might _not_ actually be valid, but they show up in retail games sometimes:
	World = auto() #F, I have seen some documentation say this is France but that doesn't seem to be how it's used
	Japan1 = auto() #1.. not sure what's different than normal J but I've only seen it in 32X so far
	BrazilUSA = auto() #4
	EuropeA = auto() #A, not sure what makes this different from normal Europe? But it happens
	JapanUSA = auto() #5, sometimes this is used in place of J and U together for some reason
	Europe8 = auto() #8, not sure what's different than normal Europe?
	USAEurope = auto() #C, not sure what's different than World?

class NESPeripheral(Enum):
	NormalController = auto()
	Zapper = auto()
	ArkanoidPaddle = auto() #AKA Vaus
	PowerPad = auto() #AKA Family Trainer in Japan, and Family Fun Fitness in Europe (and in early rare USA releases)
	PowerGlove = auto() #It's so bad
	ROB = auto()
	FamicomKeyboard = auto() #Used with the Famicom expansion port with Famicom BASIC
	SuborKeyboard = auto() #Different from the Famicom keyboard, this requires sb486 driver (there are other Subor famiclones but that will do) although seemingly is a Famicom expansion port device
	Piano = auto() #Miracle Piano Teaching System thingy

class SaturnRegionCodes(Enum):
	Japan = auto() #J
	USA = auto() #U
	Europe = auto() #E

class SNESExpansionChip(Enum):
	DSP_1 = auto()
	SuperFX = auto()
	SuperFX2 = auto()
	OBC_1 = auto()
	SA_1 = auto()
	S_DD1 = auto()
	SuperGB = auto() #For Super GB BIOS carts
	BSX = auto() #For Satellaview BIOS carts
	CX4 = auto()
	ST018 = auto()
	ST010 = auto()
	ST011 = auto()
	SPC7110 = auto()
	DSP_2 = auto()
	DSP_3 = auto()
	DSP_4 = auto()

class SwitchContentMetaType(IntEnum):
	Unknown = 0
	SystemProgram = 1
	SystemData = 2
	SystemUpdate = 3
	BootImagePackage = 4
	BootImagePackageSafe = 5
	Application = 0x80
	Patch = 0x81
	AddOnContent = 0x82
	Delta = 0x83

class WiiTitleType(IntEnum):
	System = 0x00000001
	Game = 0x00010000 #Seems to be only used for disc games, WiiWare and VC games are still Channel
	Channel = 0x00010001
	SystemChannel = 0x00010002
	GameWithChannel = 0x00010004 #Channels that come with games, e.g. Wii Fit Plus Channel or whatevs
	DLC = 0x00010005
	HiddenChannel = 0x00010008

class ZXJoystick(IntEnum):
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
