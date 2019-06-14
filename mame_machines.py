#!/usr/bin/env python3

import subprocess
import os
import sys
import re
import time
import datetime

import launchers
from info import emulator_command_lines
from config import main_config
from mame_helpers import get_mame_xml, consistentify_manufacturer, iter_mame_entire_xml, get_icons
from mame_metadata import add_metadata, mame_statuses
from metadata import Metadata, EmulationStatus
from common_types import SaveType

class MediaSlot():
	def __init__(self, xml):
		self.type = xml.attrib.get('type')
		self.tag = xml.attrib.get('tag')
		self.fixed_image = xml.attrib.get('fixed_image')
		self.mandatory = xml.attrib.get('mandatory', '0') == '1'
		self.interface = xml.attrib.get('interface')
		
		#This is the actual thing you see in -listmedia and use to insert media
		self.instances = [(instance_xml.attrib.get('name'), instance_xml.get('briefname')) for instance_xml in xml.findall('instance')]
		self.extensions = {extension_xml.attrib.get('name') for extension_xml in xml.findall('extension')}

class ArcadeSystem():
	def __init__(self, source_files=None, source_file=None, bioses=None, bios_used=None):
		if source_file and not source_files:
			source_files = [source_file]
		self.source_files = source_files

		if bios_used and not bioses:
			bioses = [bios_used]
		self.bioses = bioses

	def contains_machine(self, machine):
		use_source_file_match = self.source_files is not None
		use_bios_match = self.bioses is not None

		source_file_match = not use_source_file_match #If we don't care about the source file (not a part of how we define this arcade system), then we are happy with whatever machine's source file is, if that made any sense
		bios_match = not use_bios_match

		if use_source_file_match:
			source_file_match = machine.source_file in self.source_files
		if use_bios_match:
			machine_bios = machine.bios
			if not machine_bios:
				bios_match = None in self.bioses
			else:
				bios_match = machine_bios.basename in self.bioses
		return source_file_match and bios_match

arcade_systems = {
	#Right now, this is kiinda pointless and only really used by 1) disambiguate 2) the user's own interest, but one day when there are non-MAME emulators in here, it would make sense for this list to be as big as it is... but anyway, I do what I want
	
	'3DO': ArcadeSystem(source_file='3do', bios_used='3dobios'), #Used for the 3DO console as well, but there are 3DO-based arcade games with the system seemingly just called that; non-working
	'Acclaim PSX': ArcadeSystem(source_file='zn', bios_used='coh1000a'), #PS1 based
	'Arcadia System': ArcadeSystem(source_file='arsystems'), #Amiga 500 based
	'Aristocrat MK4': ArcadeSystem(source_file='aristmk4'), #Gambling
	'Aristocrat MK5': ArcadeSystem(source_file='aristmk5'), #Gambling, Acorn Archimedes based purrhaps
	'Aristocrat MK6': ArcadeSystem(source_file='aristmk6'), #Gambling, non-working
	'Astrocade': ArcadeSystem(source_file='astrocde'), #The home console used the same hardware, I can't remember the names of all the different things
	'Atari CoJag': ArcadeSystem(source_file='jaguar'), #This is the same source file used for the Jaguar console too
	'Atari G1': ArcadeSystem(source_file='atarig1'),
	'Atari G42': ArcadeSystem(source_file='atarig42'),
	'Atari GT': ArcadeSystem(source_file='atarigt'),
	'Atari GX2': ArcadeSystem(source_file='atarigx2'),
	'Atari Media GX': ArcadeSystem(source_file='mediagx'), #Based on Cyrix multimedia PC
	'Atari PSX': ArcadeSystem(source_file='zn', bios_used='coh1000w'), #PS1 based, non-working
	'Atari System 1': ArcadeSystem(source_file='atarisy1'),
	'Atari System 2': ArcadeSystem(source_file='atarisy2'),
	'Atari System IV': ArcadeSystem(source_file='atarisy4'),
	'ATILLA Video System': ArcadeSystem(source_file='policetr'),
	'Atlus PSX': ArcadeSystem(source_file='zn', bios_used='coh1001l'), #PS1 based
	'Atomiswave': ArcadeSystem(source_file='naomi', bios_used='awbios'),
	'AUSCOM System 1': ArcadeSystem(source_file='calchase'), #PC (Windows 98, Cyrix 686MX + Trident TGUI9680) based; non-working
	'Bally/Sente SAC-1': ArcadeSystem(source_file='balsente'),
	'Bally/Sente SAC-III': ArcadeSystem(source_file='mquake'), #Amiga 500 based
	'Bally V8000': ArcadeSystem(source_file='gammagic'), #Pentium PC based, skeleton
	'Bell-Fruit/ATD RasterSpeed': ArcadeSystem(source_file='rastersp'),
	'Bemani DJ Main': ArcadeSystem(source_file='djmain'), #Konami GX with hard drive
	'Bemani Firebeat': ArcadeSystem(source_file='firebeat'), #Non-working
	'Brezzasoft Crystal System': ArcadeSystem(source_file='crystal', bios_used='crysbios'),
	'Capcom Medalusion': ArcadeSystem(source_file='alien'), #Non-working
	'Capcom ZN1': ArcadeSystem(source_file='zn', bios_used='coh1000c'), #PS1 based
	'Capcom ZN2': ArcadeSystem(source_file='zn', bios_used='coh3002c'), #PS1 based
	'Cave CV1000B': ArcadeSystem(source_file='cv1k'), #Also CV1000D (only differentiated by cv1k_d constructor)
	'Cedar Magnet System': ArcadeSystem(source_file='cedar_magnet'),
	'Century CVS System': ArcadeSystem(source_file='cvs'),
	'Chihiro': ArcadeSystem(source_file='chihiro'), #Based on Xbox, seemingly non-working
	'CPS-1': ArcadeSystem(source_file='cps1'),
	'CPS-2': ArcadeSystem(source_file='cps2'),
	'CPS-3': ArcadeSystem(source_file='cps3'),
	'Cubo CD32': ArcadeSystem(source_file='cubo'), #Amiga CD32 + JAMMA
	'Data East MLC System': ArcadeSystem(source_file='deco_mlc'),
	'Deco 156': ArcadeSystem(source_file='deco156'),
	'Deco Casette': ArcadeSystem(source_file='decocass'),
	'Deco Simple 156': ArcadeSystem(source_file='simpl156'),
	'dgPIX VRender0': ArcadeSystem(source_file='dgpix'),
	'Eolith Ghost': ArcadeSystem(source_file='ghosteo'),
	'Eolith Gradation 2D System': ArcadeSystem(source_file='eolith'),
	'Eolith Vega System': ArcadeSystem(source_file='vegaeo'),
	'Exidy 440': ArcadeSystem(source_file='exidy440'),
	'Exidy Max-a-Flex': ArcadeSystem(source_file='maxaflex'), #Basically an Atari 600XL with ordinary Atari 8-bit games but coins purchase time. Weird maxaflex but okay
	'Exidy Universal Game Board v1': ArcadeSystem(source_file='circus'),
	'Exidy Universal Game Board v2': ArcadeSystem(source_file='exidy'),
	'FACE Linda': ArcadeSystem(source_file='mcatadv'),
	'F-E1-32': ArcadeSystem(source_file='f-32'),
	'Fun World Series 7000': ArcadeSystem(source_file='funworld'),
	'Fuuki FG-2': ArcadeSystem(source_file='fuukifg2'),
	'Fuuki FG-3': ArcadeSystem(source_file='fuukifg3'),
	'Gaelco CG-1V/GAE1': ArcadeSystem(source_file='gaelco2'),
	'Gottlieb System 1': ArcadeSystem(source_file='gts1'), #Pinball, I think?
	'Hyper Neo Geo 64': ArcadeSystem(source_file='hng64'), #Barely working
	'IBM PC-XT': ArcadeSystem(source_file='pcxt'), #Games running off a PC-XT (mostly bootlegs, but not necessarily)
	'Incredible Technologies Eagle': ArcadeSystem(source_file='iteagle'),
	'Irem M107': ArcadeSystem(source_file='m107'),
	'Irem M27': ArcadeSystem(source_file='redalert'),
	'Irem M52': ArcadeSystem(source_file='m52'),
	'Irem M58': ArcadeSystem(source_file='m58'),
	'Irem M62': ArcadeSystem(source_file='m62'),
	'Irem M63': ArcadeSystem(source_file='m63'),
	'Irem M72': ArcadeSystem(source_file='m72'), #Also M81, M82, M84, M85
	'Irem M75': ArcadeSystem(source_file='vigilant'), #Also M77 (maybe?)
	'Irem M90': ArcadeSystem(source_file='m90'), #Also M97 I guess
	'Irem M92': ArcadeSystem(source_file='m92'),
	'ISG Selection Master Type 2006': ArcadeSystem(source_file='segas16b', bios_used='isgsm'),
	'Jaleco Mega System 1': ArcadeSystem(source_file='megasys1'),
	'Jaleco Mega System 32': ArcadeSystem(source_file='ms32'),
	'Kaneko EXPRO-02': ArcadeSystem(source_file='expro02'),
	'Kaneko Super Nova System': ArcadeSystem(source_file='suprnova'),
	'Konami Bemani Twinkle': ArcadeSystem(source_file='twinkle'), #PS1 based (but not System 573 related)
	'Konami Bubble System': ArcadeSystem(source_file='nemesis', bios_used='bubsys'),
	'Konami Cobra System': ArcadeSystem(source_file='cobra'),
	'Konami GQ': ArcadeSystem(source_file='konamigq'), #Based on PS1
	'Konami GV': ArcadeSystem(source_file='konamigv'), #Based on PS1
	'Konami GX': ArcadeSystem(source_file='konamigx'),
	'Konami Hornet': ArcadeSystem(source_file='hornet'),
	'Konami M2': ArcadeSystem(source_file='konamim2'), #Based on unreleased Panasonic M2
	'Konami NWK-TR': ArcadeSystem(source_file='nwk-tr'),
	'Konami Polygonet': ArcadeSystem(source_file='plygonet'),
	'Konami Python': ArcadeSystem(source_file='pyson'), #Also called Pyson, I guess... Japan-English transliteration error? PS2 based
	'Konami System 573': ArcadeSystem(source_file='ksys573'), #Based on PS1
	'Konami Twin 16': ArcadeSystem(source_file='twin16'),
	'Konami Ultra Sports': ArcadeSystem(source_file='ultrsprt'),
	'Konami Viper': ArcadeSystem(source_file='viper'), #3Dfx (PPC) based
	'Konami ZR107': ArcadeSystem(source_file='zr107'),
	'Limenko Power System 2': ArcadeSystem(source_file='limenko'),
	'Mega Drive Bootleg': ArcadeSystem(source_file='megadriv_acbl'), #Mega Drive based ofc
	'Mega-Play': ArcadeSystem(source_file='megaplay'), #Megadrive based (home games converted to arcade format, coins buy lives)
	'Mega-Tech': ArcadeSystem(source_file='megatech'), #Megadrive games with timer
	'Midway Atlantis': ArcadeSystem(source_file='atlantis'), #Linux based (on MIPS CPU); sorta working
	'Midway MCR-3': ArcadeSystem(source_file='mcr3'), #Also "MCR-Scroll", "MCR-Monobard"
	'Midway MCR-68k': ArcadeSystem(source_file='mcr68'),
	'Midway Quicksilver': ArcadeSystem(source_file='midqslvr'), #PC based, non-working
	'Midway Seattle': ArcadeSystem(source_file='seattle'),
	'Midway T-Unit': ArcadeSystem(source_file='midtunit'),
	'Midway Vegas': ArcadeSystem(source_file='vegas'),
	'Midway V-Unit': ArcadeSystem(source_file='midvunit'),
	'Midway Wolf Unit': ArcadeSystem(source_file='midwunit'), #Also known as W-Unit
	'Midway X-Unit': ArcadeSystem(source_file='midxunit'),
	'Midway Y-Unit': ArcadeSystem(source_file='midyunit'),
	'Midway Zeus': ArcadeSystem(source_file='midzeus'),
	'Multi Amenity Casette System': ArcadeSystem(source_file='macs'),
	'Namco Anniversary': ArcadeSystem(source_file='20pacgal'),
	'Namco System 10': ArcadeSystem(source_file='namcos10'), #Based on PS1; seems this one isn't working as much as the other PS1 derivatives?
	'Namco System 11': ArcadeSystem(source_file='namcos11'), #Based on PS1
	'Namco System 12': ArcadeSystem(source_file='namcos12'), #Based on PS1
	'Namco System 16 Universal': ArcadeSystem(source_file='toypop'),
	'Namco System 1': ArcadeSystem(source_file='namcos1'),
	'Namco System 21': ArcadeSystem(source_files=['namcos21', 'namcos21_c67', 'namcos21_de']),
	'Namco System 22': ArcadeSystem(source_file='namcos22'),
	'Namco System 23': ArcadeSystem(source_file='namcos23'), #Also Gorgon / "System 22.5"; not really working yet
	'Namco System 2': ArcadeSystem(source_file='namcos2'),
	'Namco System 86': ArcadeSystem(source_file='namcos86'),
	'Namco System FL': ArcadeSystem(source_file='namcofl'),
	'Namco System NA-1': ArcadeSystem(source_file='namcona1'), #Also NA-2
	'Namco System NB-1': ArcadeSystem(source_file='namconb1'), #Also NB-2
	'Namco System ND-1': ArcadeSystem(source_file='namcond1'),
	'Naomi 2': ArcadeSystem(source_file='naomi', bios_used='naomi2'),
	'Naomi': ArcadeSystem(source_file='naomi', bioses=['naomi', 'hod2bios', 'f355dlx', 'f355bios', 'airlbios']), #Based on Dreamcast. Sort of working, but slow.
	'Naomi GD-ROM': ArcadeSystem(source_file='naomi', bios_used='naomigd'),
	'Neo-Geo': ArcadeSystem(source_file='neogeo', bios_used='neogeo'),
	'Neo Print': ArcadeSystem(source_file='neoprint'),
	'Nichibutsu High Rate DVD': ArcadeSystem(source_file='csplayh5'),
	'Nintendo Super System': ArcadeSystem(source_file='nss'), #SNES games with timer
	'Philips CD-i': ArcadeSystem(source_file='cdi'), #Literally a CD-i player with a JAMMA adapter (used for some quiz games)
	'Photon IK-3': ArcadeSystem(source_file='photon2'), #Leningrad-1 based (Russian ZX Spectrum clone)
	'Photon System': ArcadeSystem(source_file='photon'), #PK8000 based (Russian PC that was supposed to be MSX1 compatible)
	'PlayChoice-10': ArcadeSystem(source_file='playch10'), #NES games with timer
	'PolyGame Master 2': ArcadeSystem(source_file='pgm2'),
	'PolyGame Master 3': ArcadeSystem(source_file='pgm3'), #Non-working
	'PolyGame Master': ArcadeSystem(source_file='pgm'),
	'PS Arcade 95': ArcadeSystem(source_file='zn', bios_used='coh1002e'), #PS1 based, used by Eighting/Raizing?
	'Psikyo PS4': ArcadeSystem(source_file='psikyo4'),
	'Sammy Medal Game System': ArcadeSystem(source_file='sigmab98', bios_used='sammymdl'),
	'Sega Atom': ArcadeSystem(source_file='segaatom'), #Basically a skeleton
	'Sega G-80 Raster': ArcadeSystem(source_file='segag80r'),
	'Sega G-80 Vector': ArcadeSystem(source_file='segag80v'),
	'Sega Hikaru': ArcadeSystem(source_file='hikaru'), #Based on souped up Naomi and in turn Dreamcast, non-working
	'Sega Lindbergh': ArcadeSystem(source_file='lindbergh'), #(modern) PC based, very non-working
	'Sega M1': ArcadeSystem(source_file='segam1'), #Gambling
	'Sega Model 1': ArcadeSystem(source_file='model1'),
	'Sega Model 2': ArcadeSystem(source_file='model2'), #Barely working
	'Sega Model 3': ArcadeSystem(source_file='model3'), #Barely working
	'Sega SG-1000': ArcadeSystem(source_file='sg1000a'), #Same hardware as the home system
	'Sega ST-V': ArcadeSystem(source_file='stv'), #Based on Saturn
	'Sega System 16A': ArcadeSystem(source_file='segas16a'), #Similar to Megadrive
	'Sega System 16B': ArcadeSystem(source_file='segas16b', bios_used=None),
	'Sega System 18': ArcadeSystem(source_file='segas18'),
	'Sega System 24': ArcadeSystem(source_file='segas24'),
	'Sega System 32': ArcadeSystem(source_file='segas32'),
	'Sega System C2': ArcadeSystem(source_file='segac2'), #Similar to Megadrive
	'Sega System E': ArcadeSystem(source_file='segae'), #Similar to Master System
	'Sega System H1': ArcadeSystem(source_file='coolridr'),
	'Sega System SP': ArcadeSystem(source_file='segasp'), #Dreamcast based, for medal games; non-working
	'Sega UFO Board': ArcadeSystem(source_file='segaufo'), #Mechanical
	'Sega X-Board': ArcadeSystem(source_file='segaxbd'),
	'Sega Y-Board': ArcadeSystem(source_file='segaybd'),
	'Seibu SPI': ArcadeSystem(source_file='seibuspi'),
	'Seta Aleck64': ArcadeSystem(source_file='aleck64'), #Based on N64
	'Sigma B-98': ArcadeSystem(source_file='sigmab98', bios_used=None),
	'SNES Bootleg': ArcadeSystem(source_file='snesb'), #SNES based, natch
	'SSV': ArcadeSystem(source_file='ssv'), #Sammy Seta Visco
	'Super Famicom Box': ArcadeSystem(source_file='sfcbox'), #Arcadified SNES sorta; non-working
	'Taito Air System': ArcadeSystem(source_file='taitoair'),
	'Taito B System': ArcadeSystem(source_file='taito_b'),
	'Taito F2 System': ArcadeSystem(source_file='taito_f2'), #Also F1
	'Taito F3 System': ArcadeSystem(source_file='taito_f3'),
	'Taito FX1': ArcadeSystem(source_file='zn', bios_used='coh1000t'), #PS1 based, there are actually Taito FX-1A and Taito FX-1B
	'Taito G-NET': ArcadeSystem(source_file='taitogn'),
	'Taito H System': ArcadeSystem(source_file='taito_h'),
	'Taito JC': ArcadeSystem(source_file='taitojc'),
	'Taito L System': ArcadeSystem(source_file='taito_l'),
	'Taito O System': ArcadeSystem(source_file='taito_o'),
	'Taito Power-JC': ArcadeSystem(source_file='taitopjc'),
	'Taito SJ': ArcadeSystem(source_file='taitosj'),
	'Taito Type X': ArcadeSystem(source_file='taitotx'), #Modern PC based, very non-working
	'Taito Type-Zero': ArcadeSystem(source_file='taitotz'), #PPC based
	'Taito Wolf': ArcadeSystem(source_file='taitowlf'), #3Dfx (Pentium) based, not working
	'Taito X System': ArcadeSystem(source_file='taito_x'),
	'Taito Z System': ArcadeSystem(source_file='taito_z'),
	'Tecmo TPS': ArcadeSystem(source_file='zn', bios_used='coh1002m'), #PS1 based
	'TIA-MC1': ArcadeSystem(source_file='tiamc1'),
	'Triforce': ArcadeSystem(source_file='triforce'), #GameCube based
	'Vectrex': ArcadeSystem(source_file='vectrex'), #Also used for actual Vectrex console
	'VIC Dual': ArcadeSystem(source_file='vicdual'),
	'Video System PSX': ArcadeSystem(source_file='zn', bios_used='coh1002v'), #PS1 based
	'VS Unisystem': ArcadeSystem(source_file='vsnes'),

	#Arcade platforms that don't have a name or anything, but companies consistently use them
	'American Laser Games 3DO Hardware': ArcadeSystem(source_file='3do', bios_used='alg3do'), #Non-working
	'American Laser Games Hardware': ArcadeSystem(source_file='alg'), #Amiga 500 based (w/ laserdisc player)
	'Art & Magic Hardware': ArcadeSystem(source_file='artmagic'),
	'Cave 68K Hardware': ArcadeSystem(source_file='cave'),
	'Cave PC Hardware': ArcadeSystem(source_file='cavepc'), #Athlon 64 X2 + Radeon 3200 based; non-working
	'Cinematronics Vector Hardware': ArcadeSystem(source_file='cinemat'),
	'Cosmodog Hardware': ArcadeSystem(source_file='cmmb'),
	'Data East 16-bit Hardware': ArcadeSystem(source_file='dec0'), #Have heard some of these games called "Data East MEC-M1" but I dunno where that name comes from
	'Data East 32-bit Hardware': ArcadeSystem(source_file='deco32'), #Or "Data East ARM6", if you prefer
	'Data East 8-bit Hardware': ArcadeSystem(source_file='dec8'),
	'Enerdyne Technologies Trivia Hardware': ArcadeSystem(source_file='ettrivia'),
	'Eolith 16-bit Hardware': ArcadeSystem(source_file='eolith16'),
	'ESD 16-bit Hardware': ArcadeSystem(source_file='esd16'),
	'Gaelco 3D Hardware': ArcadeSystem(source_file='gaelco3d'),
	'Gaelco Hardware': ArcadeSystem(source_file='gaelco'), #Specifically from 1991-1996 apparently?
	'Game Plan Hardware': ArcadeSystem(source_file='gameplan'),
	'Gottlieb Hardware': ArcadeSystem(source_file='gottlieb'),
	'Greyhound Electronics Hardware': ArcadeSystem(source_file='gei'),
	'Home Data Hardware': ArcadeSystem(source_file='homedata'),
	'IGS011 Blitter Based Hardware': ArcadeSystem(source_file='igs011'),
	'Incredible Technologies 32-bit Blitter Hardware': ArcadeSystem(source_file='itech32'),
	'Incredible Technologies 8-bit Blitter Hardware': ArcadeSystem(source_file='itech8'),
	'Kaneko 16-bit Hardware': ArcadeSystem(source_file='kaneko16'),
	'Leland Hardware': ArcadeSystem(source_file='leland'),
	'Meadows S2650 Hardware': ArcadeSystem(source_file='meadows'),
	'Metro Hardware': ArcadeSystem(source_file='metro'),
	'Microprose 3D Hardware': ArcadeSystem(source_file='micro3d'),
	'Midway 8080 Black & White Hardware': ArcadeSystem(source_file='mw8080bw'),
	'Newer Seta Hardware': ArcadeSystem(source_file='seta2'),
	'Newer Toaplan Hardware': ArcadeSystem(source_file='toaplan2'),
	'Nintendo 8080 Hardware': ArcadeSystem(source_file='n8080'),
	'NMK 16-bit Hardware': ArcadeSystem(source_file='nmk16'),
	'Playmark Hardware': ArcadeSystem(source_file='playmark'),
	'Psikyo Hardware': ArcadeSystem(source_file='psikyo'),
	'Psikyo SH-2 Hardware': ArcadeSystem(source_file='psikyosh'), #Psikyo PS3, PS5
	'Semicom 68020 Hardware': ArcadeSystem(source_file='dreamwld'),
	'Seta Hardware': ArcadeSystem(source_file='seta'),
	'Seta ST-0016 Based Hardware': ArcadeSystem(source_file='simple_st0016'),
	'SNK 68K Hardware': ArcadeSystem(source_file='snk68'),
	'SNK Alpha 68K Hardware': ArcadeSystem(source_file='alpha68k'),
	'SNK Hardware': ArcadeSystem(source_file='snk'),
	'Status Trivia Hardware': ArcadeSystem(source_file='statriv2'),
	'Subsino Newer Tilemaps Hardware': ArcadeSystem(source_file='subsino2'),
	'Toaplan Hardware': ArcadeSystem(source_file='toaplan1'),
	'Unico Hardware': ArcadeSystem(source_file='unico'),
	'Williams 6809 Hardware': ArcadeSystem(source_file='williams'),
	'Yun Sung 16 Bit Hardware': ArcadeSystem(source_file='yunsun16'),

	#Arcade platforms that don't really have a name except a game that uses them; I try not to fill this up with every single remaining source file, just where it's notable for having other games on it or some other reason (because it's based on a home console/computer perhaps, or because it's 3D or modern and therefore interesting), or maybe I do because I feel like it sometimes, oh well
	'Ambush Hardware': ArcadeSystem(source_file='ambush'),
	'Arkanoid Hardware': ArcadeSystem(source_file='arkanoid'),
	'Armed Formation Hardware': ArcadeSystem(source_file='armedf'),
	'Backfire! Hardware': ArcadeSystem(source_file='backfire'),
	'Battle Rangers Hardware': ArcadeSystem(source_file='battlera'), #PC Engine based
	'Battletoads Hardware': ArcadeSystem(source_file='btoads'),
	'Beathead Hardware': ArcadeSystem(source_file='beathead'),
	'Billiard Academy Real Break Hardware': ArcadeSystem(source_file='realbrk'),
	'Bishi Bashi Champ Hardware': ArcadeSystem(source_file='bishi'),
	'BurgerTime Hardware': ArcadeSystem(source_file='btime'),
	'Cisco Heat Hardware': ArcadeSystem(source_file='cischeat'),
	'Cool Pool Hardware': ArcadeSystem(source_file='coolpool'),
	'Crazy Climber Hardware': ArcadeSystem(source_file='cclimber'),
	'Destiny Hardware': ArcadeSystem(source_file='deshoros'),
	'Don Den Lover Hardware': ArcadeSystem(source_file='ddenlovr'),
	'Donkey Kong Hardware': ArcadeSystem(source_file='dkong'),
	'Erotictac Hardware': ArcadeSystem(source_file='ertictac'), #Acorn Archimedes based
	'Exterminator Hardware': ArcadeSystem(source_file='exterm'),
	'Final Crash Hardware': ArcadeSystem(source_file='fcrash'), #Bootleg of Final Fight; this is used for other bootlegs too
	'Galaga Hardware': ArcadeSystem(source_file='galaga'),
	'Galaxian Hardware': ArcadeSystem(source_files=['galaxian', 'galaxold']), #Was used for a lot of games and bootlegs, actually; seems that Moon Cresta hardware has the same source file; there's a comment in galaxold saying it'll be merged in galaxian eventually (seems it has all the bootlegs and such)
	'Go! Go! Connie Hardware': ArcadeSystem(source_file='ggconnie'), #Supergrafx based
	'G-Stream G2020 Hardware': ArcadeSystem(source_file='gstream'),
	'GTI Club Hardware': ArcadeSystem(source_file='gticlub'),
	'Hang-On Hardware': ArcadeSystem(source_file='segahang'),
	"Hard Drivin' Hardware": ArcadeSystem(source_file='harddriv'),
	'High Seas Havoc Hardware': ArcadeSystem(source_file='hshavoc'), #Megadrive based
	'Killer Instinct Hardware': ArcadeSystem(source_file='kinst'),
	'Last Fighting Hardware': ArcadeSystem(source_file='lastfght'),
	'Lethal Justice Hardware': ArcadeSystem(source_file='lethalj'),
	'Liberation Hardware': ArcadeSystem(source_file='liberate'),
	'Macross Plus Hardware': ArcadeSystem(source_file='macrossp'),
	'Metal Maniax Hardware': ArcadeSystem(source_file='metalmx'),
	'Nemesis Hardware': ArcadeSystem(source_file='nemesis', bios_used=None),
	'Out Run Hardware': ArcadeSystem(source_file='segaorun'),
	'Pac-Man Hardware': ArcadeSystem(source_file='pacman'),
	'Pong Hardware': ArcadeSystem(source_file='pong'),
	'Qix Hardware': ArcadeSystem(source_file='qix'),
	'Quake Arcade Tournament Hardware': ArcadeSystem(source_file='quakeat'), #Unknown PC based
	'Quiz Do Re Mi Fa Grand Prix Hardware': ArcadeSystem(source_file='qdrmfgp'),
	'Raiden 2 Hardware': ArcadeSystem(source_file='raiden2'),
	'Rally-X Hardware': ArcadeSystem(source_file='rallyx'),
	'Scramble Hardware': ArcadeSystem(source_file='scramble'), #Apparently also to be merged into galaxian
	'See See Find Out Hardware': ArcadeSystem(source_file='ssfindo'), #RISC PC based
	'Slap Shot Hardware': ArcadeSystem(source_file='slapshot'),
	'Snow Bros Hardware': ArcadeSystem(source_file='snowbros'),
	'Space Invaders / Qix Silver Anniversary Edition Hardware': ArcadeSystem(source_file='invqix'),
	'Street Games Hardware': ArcadeSystem(source_file='pcat_nit'), #PC-AT 386 based
	'Super Pac-Man Hardware': ArcadeSystem(source_file='mappy'), #While the source file is called mappy, this seems to be more commonly known as the Super Pac-Man board
	'Tatsunoko vs. Capcom Hardware': ArcadeSystem(source_file='tvcapcom'), #Wii based
	'The NewZealand Story Hardware': ArcadeSystem(source_file='tnzs'),
	'TMNT Hardware': ArcadeSystem(source_file='tmnt'),
	'Tournament Table Hardware': ArcadeSystem(source_file='tourtabl'), #Atari 2600 based
	'Tumble Pop Bootleg Hardware': ArcadeSystem(source_file='tumbleb'),
	'Turret Tower Hardware': ArcadeSystem(source_file='turrett'),
	'TX-1 Hardware': ArcadeSystem(source_file='tx1'),
	'Vamp x1/2 Hardware': ArcadeSystem(source_file='vamphalf'), #I guess the source file is for Hyperstone based games but I dunno if I should call it that
	'Wheels & Fire Hardware': ArcadeSystem(source_file='wheelfir'),
	'Zaxxon Hardware': ArcadeSystem(source_file='zaxxon'),

	#Multiple things stuffed into one source file, so there'd have to be something else to identify it (that isn't BIOS used) or it doesn't matter
	'Irem M10/M11/M15': ArcadeSystem(source_file='m10'),
	'Midway MCR-1/MCR-2': ArcadeSystem(source_file='mcr'),
	'Namco System 246/256': ArcadeSystem(source_file='namcops2'), #Based on PS2
	'Sega System 1/2': ArcadeSystem(source_file='system1'),
	'Play Mechanix VP50/VP100/VP101': ArcadeSystem(source_file='vp101'),
}

licensed_arcade_game_regex = re.compile(r'^(.+?) \((.+?) license\)$')
licensed_from_regex = re.compile(r'^(.+?) \(licensed from (.+?)\)$')
hack_regex = re.compile(r'^hack \((.+)\)$')
bootleg_with_publisher_regex = re.compile(r'^bootleg \((.+)\)$')
class Machine():
	def __init__(self, xml, init_metadata=False):
		self.xml = xml
		#This can't be an attribute because we might need to override it later! Bad Megan!
		self.name = self.xml.findtext('description')
		self.metadata = Metadata()
		self._has_inited_metadata = False
		if init_metadata:
			self._add_metadata_fields()

	def _add_metadata_fields(self):
		self._has_inited_metadata = True
		self.metadata.specific_info['Source-File'] = self.source_file
		self.metadata.specific_info['Family-Basename'] = self.family
		self.metadata.specific_info['Family'] = self.family_name
		self.metadata.specific_info['Has-Parent'] = self.has_parent

		self.metadata.year = self.xml.findtext('year')

		self.metadata.specific_info['Number-of-Players'] = self.number_of_players
		self.metadata.specific_info['Is-Mechanical'] = self.is_mechanical
		self.metadata.specific_info['Dispenses-Tickets'] = self.uses_device('ticket_dispenser')
		self.metadata.specific_info['Coin-Slots'] = self.coin_slots
		self.metadata.specific_info['Requires-CHD'] = self.requires_chds
		self.metadata.specific_info['Romless'] = self.romless
		self.metadata.specific_info['Slot-Names'] = [slot.instances[0][0] for slot in self.media_slots if slot.instances]
		self.metadata.specific_info['Software-Lists'] = self.software_lists
		bios = self.bios
		if bios:
			self.metadata.specific_info['BIOS-Used'] = bios.basename
			self.metadata.specific_info['BIOS-Used-Full-Name'] = bios.name
		if self.samples_used:
			self.metadata.specific_info['Samples-Used'] = self.samples_used
		arcade_system = self.arcade_system
		if arcade_system:
			self.metadata.specific_info['Arcade-System'] = arcade_system

		licensed_from = self.licensed_from
		if self.licensed_from:
			self.metadata.specific_info['Licensed-From'] = licensed_from

		hacked_by = self.hacked_by
		if self.hacked_by:
			self.metadata.specific_info['Hacked-By'] = hacked_by

		self.metadata.developer, self.metadata.publisher = self.developer_and_publisher

	@property
	def basename(self):
		return self.xml.attrib['name']

	@property
	def has_parent(self):
		return 'cloneof' in self.xml.attrib

	@property
	def parent(self):
		parent_name = self.xml.attrib.get('cloneof')
		if not parent_name:
			return None
		return Machine(get_mame_xml(parent_name), True)

	@property
	def family(self):
		return self.xml.attrib.get('cloneof', self.basename)

	@property
	def family_name(self):
		return self.parent.name if self.has_parent else self.name

	@property
	def source_file(self):
		return os.path.splitext(self.xml.attrib['sourcefile'])[0]

	@property
	def arcade_system(self):
		for name, arcade_system in arcade_systems.items():
			#Ideally, this should only match one, otherwise it means I'm doing it wrong I guess
			if arcade_system.contains_machine(self):
				return name
		return None

	@property
	def icon(self):
		icons = get_icons()
		if not icons:
			return None

		basename_icon = icons.get(self.basename)
		if basename_icon:
			return basename_icon

		family_icon = icons.get(self.family)
		if family_icon:
			return family_icon

		if self.bios:
			bios_icon = icons.get(self.bios.basename)
			if bios_icon:
				return bios_icon

		return None

	def make_launcher(self):
		if not self._has_inited_metadata:
			self._add_metadata_fields()

		slot_options = {}
		if self.metadata.save_type == SaveType.MemoryCard and self.source_file == 'neogeo' and main_config.memcard_path:
			memory_card_path = os.path.join(main_config.memcard_path, self.basename + '.neo')
			if os.path.isfile(memory_card_path):
				slot_options['memc'] = memory_card_path
			else:
				memory_card_path = os.path.join(main_config.memcard_path, self.family + '.neo')
				if os.path.isfile(memory_card_path):
					slot_options['memc'] = memory_card_path

		params = launchers.LaunchParams('mame', emulator_command_lines.mame_base(self.basename, slot_options=slot_options))
		#TODO: Let's put this in emulator_info, even if only MAME exists as the singular arcade emulator for now; and clean this up some more
		launchers.make_launcher(params, self.name, self.metadata, 'MAME machine', self.basename, self.icon)

	@property
	def is_mechanical(self):
		return self.xml.attrib.get('ismechanical', 'no') == 'yes'

	@property
	def input_element(self):
		return self.xml.find('input')

	@property
	def coin_slots(self):
		return self.input_element.attrib.get('coins', 0) if self.input_element is not None else 0

	@property
	def number_of_players(self):
		if self.input_element is None:
			#This would happen if we ended up loading a device or whatever, so let's not crash the whole dang program. Also, since you can't play a device, they have 0 players. But they won't have launchers anyway, this is just to stop the NoneType explosion.
			return 0
		return int(self.input_element.attrib.get('players', 0))

	@property
	def driver_element(self):
		return self.xml.find('driver')

	@property
	def overall_status(self):
		#Hmm, so how this works according to https://github.com/mamedev/mame/blob/master/src/frontend/mame/info.cpp: if any particular feature is preliminary, this is preliminary, if any feature is imperfect this is imperfect, unless protection = imperfect then this is preliminary
		#It even says it's for the convenience of frontend developers, but since I'm an ungrateful piece of shit and I always feel the need to take matters into my own hands, I'm gonna get the other parts of the emulation too
		if self.driver_element is None:
			return EmulationStatus.Unknown
		return mame_statuses.get(self.driver_element.attrib.get('status'), EmulationStatus.Unknown)

	@property
	def emulation_status(self):
		if self.driver_element is None:
			return EmulationStatus.Unknown
		return mame_statuses.get(self.driver_element.attrib.get('emulation'), EmulationStatus.Unknown)

	@property
	def feature_statuses(self):
		features = {}
		for feature in self.xml.findall('feature'):
			feature_type = feature.attrib['type']
			if 'status' in feature.attrib:
				feature_status = feature.attrib['status']
			elif 'overall' in feature.attrib:
				#wat?
				feature_status = feature.attrib['overall']
			else:
				continue
			
			features[feature_type] = feature_status
			#Known types according to DTD: protection, palette, graphics, sound, controls, keyboard, mouse, microphone, camera, disk, printer, lan, wan, timing
			#Note: MAME 0.208 has added capture, media, tape, punch, drum, rom, comms; although because I have been somewhat clever in writing this code, I don't need to hardcode any of that anyway
		return features

	@property
	def is_skeleton_driver(self):
		#Actually, we're making an educated guess here, as MACHINE_IS_SKELETON doesn't appear directly in the XML...
		#What I actually want to happen is to tell us if a machine will just display a blank screen and nothing else (because nobody wants those in a launcher). Right now that's not really possible without the false positives of games which don't have screens as such but they do display things via layouts (e.g. wackygtr) so the best we can do is say everything that doesn't have any kind of controls, which tends to be the case for a lot of these.
		#MACHINE_IS_SKELETON is actually defined as MACHINE_NO_SOUND and MACHINE_NOT_WORKING, so we'll look for that too
		return self.number_of_players == 0 and self.emulation_status in (EmulationStatus.Broken, EmulationStatus.Unknown) and self.feature_statuses.get('sound') == 'unemulated'

	def uses_device(self, name):
		for device_ref in self.xml.findall('device_ref'):
			if device_ref.attrib['name'] == name:
				return True

		return False

	@property
	def requires_chds(self):
		#Hmm... should this include where all <disk> has status == "nodump"? e.g. Dragon's Lair has no CHD dump, would it be useful to say that it requires CHDs because it's supposed to have one but doesn't, or not, because you have a good romset without one
		#I guess I should have a look at how the MAME inbuilt UI does this
		#Who really uses this kind of thing, anyway?
		return self.xml.find('disk') is not None

	@property
	def romless(self):
		if self.requires_chds:
			return False
		if self.xml.find('rom') is None:
			return True

		for rom in self.xml.findall('rom'):
			if rom.attrib.get('status', 'good') != 'nodump':
				return False
		return True

	@property
	def bios(self):
		romof = self.xml.attrib.get('romof')
		if self.has_parent and romof == self.family:
			return self.parent.bios
		if romof:
			return Machine(get_mame_xml(romof), True)
		return None

	@property
	def samples_used(self):
		return self.xml.attrib.get('sampleof')

	@property
	def media_slots(self):
		return [MediaSlot(device_xml) for device_xml in self.xml.findall('device')]

	@property
	def has_mandatory_slots(self):
		return any(slot.mandatory for slot in self.media_slots)

	@property
	def software_lists(self):
		return [software_list.attrib.get('name') for software_list in self.xml.findall('softwarelist')]


	@property
	def manufacturer(self):
		return self.xml.findtext('manufacturer')

	@property
	def is_hack(self):
		return bool(self.hacked_by)

	@property
	def licensed_from(self):
		licensed_from_match = licensed_from_regex.fullmatch(self.manufacturer)
		if licensed_from_match:
			return licensed_from_match[2]
		return None

	@property
	def hacked_by(self):
		hack_match = hack_regex.fullmatch(self.manufacturer)
		if hack_match:
			return hack_match[1]
		return None

	@property
	def developer_and_publisher(self):
		if not self.manufacturer:
			#Not sure if this ever happens, but still
			return None, None

		license_match = licensed_arcade_game_regex.fullmatch(self.manufacturer)
		if license_match:
			developer = consistentify_manufacturer(license_match[1])
			publisher = consistentify_manufacturer(license_match[2])
			return developer, publisher
	
		manufacturer = self.manufacturer
		licensed_from_match = licensed_from_regex.fullmatch(manufacturer)
		if licensed_from_match:
			manufacturer = licensed_from_match[1]
		
		bootleg_match = bootleg_with_publisher_regex.fullmatch(manufacturer)
		if manufacturer in ('bootleg', 'hack') or self.is_hack:
			if self.has_parent:
				developer = self.parent.metadata.developer
				publisher = self.parent.metadata.publisher
			else:
				developer = None #It'd be the original not-bootleg/hack game's developer but we can't get that programmatically without a parent etc
				publisher = None
		elif bootleg_match:
			developer = None
			if self.has_parent:
				developer = self.parent.metadata.developer
				publisher = self.parent.metadata.publisher
			
			publisher = consistentify_manufacturer(bootleg_match[1])
		else:
			if ' / ' in manufacturer:
				#Let's try and clean up things a bit when this happens
				manufacturers = [consistentify_manufacturer(m) for m in manufacturer.split(' / ')]

				if len(manufacturers) == 2 and manufacturers[0] == 'bootleg':
					developer = publisher = manufacturers[1]
				else:
					#TODO: Try and cleverly figure out which ones are developers and which are publishers, but... hmm
					developer = publisher = ', '.join(manufacturers)
			else:
				developer = publisher = consistentify_manufacturer(manufacturer)
		return developer, publisher

def get_machine(driver):
	return Machine(get_mame_xml(driver))

def mame_verifyroms(basename):
	try:
		#Note to self: Stop wasting time thinking you can make this faster
		subprocess.run(['mame', '-verifyroms', basename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
		return True
	except subprocess.CalledProcessError:
		return False

#Normally we skip over machines that have software lists because it generally indicates they're consoles/computers that should be used with software, these are software lists where the original thing is fine to boot by itself
#Hmm... it's tricky but one might want to blacklist machines that technically can boot by themselves but there's no point doing so (e.g. megacd, gba, other game consoles that don't have inbuilt games), especially once we add software list games into here and it's gonna be a hot mess
#Hold that thought, I might end up actually doing something like that. Get rid of anything with slots, maybe, except:
	#- Arcade machines (as they are most definitely standalone other than category == Utilities, and may have cdrom/harddisk slots which are just there for the game to be stored on)
	#- Anything that just has memcard slots as those are usually just for save data (then again gp32 uses it for a thing, and should be skipped over)
	#- MIDI ports or printout slots probably don't count as anything either
	#- If anything is in okay_software_lists it is also okay here
	#- Popira and DDR Family Mat are okay but base ekara is not okay (just displays error message if you boot without a cart, those two have builtin songs), and that's why I have ekara in okay_software_lists
#TODO: Probably makes sense to skip anything that is a MAME driver for anything in system_info.systems
#These are prefixes (otherwise I'd have to list every single type of Jakks gamekey thingo)
okay_software_lists = ('vii', 'jakks_gamekey', 'ekara', 'snspell', 'tntell')

def is_actually_machine(machine):
	if machine.xml.attrib.get('runnable', 'yes') == 'no':
		return False

	if machine.xml.attrib.get('isbios', 'no') == 'yes':
		return False

	if machine.xml.attrib.get('isdevice', 'no') == 'yes':
		return False

	return True

def is_machine_launchable(machine):
	if machine.has_mandatory_slots:
		return False
	
	return True

def process_machine(machine):
	if machine.is_skeleton_driver:
		#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
		#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up

		#We'll do this check _after_ mame_verifyroms so we don't spam debug print for a bunch of skeleton drivers we don't have
		if main_config.debug:
			print('Skipping %s (%s, %s) as it is probably a skeleton driver' % (machine.name, machine.basename, machine.source_file))
		return

	add_metadata(machine)
	if main_config.exclude_non_arcade and machine.metadata.platform == 'Non-Arcade':
		return
	if main_config.exclude_pinball and machine.metadata.platform == 'Pinball':
		return
	if main_config.exclude_standalone_systems and machine.metadata.platform == 'Standalone System':
		return

	machine.make_launcher()

def no_longer_exists(game_id):
	#This is used to determine what launchers to delete if not doing a full rescan
	return not mame_verifyroms(game_id)

def process_machine_element(machine_element):
	machine = Machine(machine_element)
	if machine.source_file in main_config.skipped_source_files:
		return

	if not is_actually_machine(machine):
		return

	if not is_machine_launchable(machine):
		return

	if main_config.exclude_non_working and machine.emulation_status == EmulationStatus.Broken and machine.basename not in main_config.non_working_whitelist:
		#This will need to be refactored if anything other than MAME is added
		#The code behind -listxml is of the opinion that protection = imperfect should result in a system being considered entirely broken, but I'm not so sure if that works out
		return

	if not mame_verifyroms(machine.basename):
		#We do this as late as we can after checks to see if we want to actually add this machine or not, because it takes a while (in a loop of tens of thousands of machines), and hence if we can get out of having to do it we should
		return

	process_machine(machine)

def process_arcade():
	time_started = time.perf_counter()

	for machine_name, machine_element in iter_mame_entire_xml():
		if not main_config.full_rescan:
			if launchers.has_been_done('MAME machine', machine_name):
				continue

		process_machine_element(machine_element)

	if main_config.print_times:
		time_ended = time.perf_counter()
		print('Arcade finished in', str(datetime.timedelta(seconds=time_ended - time_started)))

def main():
	if '--drivers' in sys.argv:
		arg_index = sys.argv.index('--drivers')
		if len(sys.argv) == 2:
			print('--drivers requires an argument')
			return

		driver_list = sys.argv[arg_index + 1].split(',')
		for driver_name in driver_list:
			process_machine_element(get_mame_xml(driver_name))
		return

	process_arcade()

if __name__ == '__main__':
	main()
