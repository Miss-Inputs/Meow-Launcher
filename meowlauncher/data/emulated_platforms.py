from meowlauncher.common_types import MediaType
from meowlauncher.config_types import ConfigValueType
from meowlauncher.emulated_platform import (ManuallySpecifiedPlatform, PlatformConfigValue,
                                            StandardEmulatedPlatform)
from meowlauncher.games.specific_behaviour import folder_checks

from .format_info import (atari_2600_cartridge_extensions, cdrom_formats,
                          commodore_cart_formats, commodore_disk_formats,
                          generic_cart_extensions, generic_tape_extensions,
                          mame_floppy_formats)

msx_turbo_r_drivers = {'fsa1gt', 'fsa1st'} #Neither of these are working

working_msx2plus_drivers = {'hbf1xv', 'fsa1fx', 'fsa1wxa', 'fsa1wsx', 'hbf1xdj', 'phc70fd2', 'phc35j', 'hbf9sp'}
broken_msx2plus_drivers = {'expert3i', 'expert3t', 'expertac', 'expertdx'}
msx2plus_drivers = working_msx2plus_drivers.union(broken_msx2plus_drivers)

arabic_msx2_drivers = {'ax350', 'ax370'}
korean_msx2_drivers = {'cpc300', 'cpc300e', 'cpc330k', 'cpc400', 'cpc400s', 'cpc61'}
japanese_msx2_drivers = {'kmc5000', 'mlg10', 'fs5500f2', 'fs4500', 'fs4700', 'fs5000', 'fs4600', 'fsa1a', 'fsa1mk2', 'fsa1f', 'fsa1fm', 'nms8250j', 'hbf500', 'hbf900a', 'hx33', 'yis604', 'phc23', 'phc55fd2', 'hbf1xd', 'hbf1xdm2'}
other_msx2_drivers = {'canonv25', 'canonv30', 'fpc900', 'expert20', 'mlg1', 'mlg3', 'mlg30', 'nms8220a', 'vg8230', 'vg8235', 'vg8240', 'nms8245', 'nms8255', 'nms8280', 'mpc25fd', 'hx34i', 'fstm1', 'hbf5', 'hbf9p', 'hbf500p', 'hbf700p', 'hbg900ap', 'hbg900p', 'tpc310', 'tpp311', 'tps312', 'hx23i', 'cx7m128'}
working_msx2_drivers = other_msx2_drivers.union(arabic_msx2_drivers).union(korean_msx2_drivers).union(japanese_msx2_drivers)
broken_msx2_drivers = {'cpg120', 'y503iiir', 'y805256', 'mbh70', 'victhc95', 'hotbit20', 'mpc27', 'nms8260', 'mpc2300', 'mpc2500f', 'phc77', 'hbf1', 'hbf12'}
msx2_drivers = working_msx2_drivers.union(broken_msx2_drivers)

arabic_msx1_drivers = {'ax150', 'ax170', 'svi738ar'}
japanese_msx1_drivers = {'fmx', 'mbh2', 'mbh25', 'mbh50', 'mlf110', 'mlf120', 'cf1200', 'cf2000', 'cf2700', 'cf3000', 'cf3300', 'fs1300', 'fs4000', 'mpc64', 'hb701fd', 'hc7', 'cx5f'}
korean_msx1_drivers = {'cpc88', 'dpc200', 'gsfc80u', 'cpc51', 'gfc1080', 'gfc1080a', 'mx64'}
other_msx1_drivers = {'svi728', 'svi738', 'canonv8', 'canonv20', 'mx10', 'pv7', 'pv16', 'dpc200e', 'dgnmsx', 'fdpc200', 'fpc500', 'fspc800', 'bruc100', 'gsfc200', 'jvchc7gb', 'mlf48', 'mlf80', 'mlfx1', 'phc2', 'phc28', 'cf2700g', 'perfect1', 'nms801', 'vg8010', 'vg802020', 'piopx7', 'spc800', 'mpc100', 'mpc200', 'phc28l', 'phc28s', 'mpc10', 'hb10p', 'hb101p', 'hb20p', 'hb201p', 'hb501p', 'hb55p', 'hb75p', 'hx10', 'hx20', 'cx5m128', 'yis303', 'yis503', 'yc64', 'expert13', 'expertdp', 'expertpl', 'hotbi13p'} #Anything that isn't one of those other three (which are apparently specifically different or needed in some cases)
working_msx1_drivers = other_msx1_drivers.union(arabic_msx1_drivers).union(japanese_msx1_drivers).union(korean_msx1_drivers)
broken_msx1_drivers = {'hx21', 'hx22'}
msx1_drivers = working_msx1_drivers.union(broken_msx1_drivers)

platforms = {
	#Put all the "most normal people would be interested in" consoles up here, which is completely subjective and not even the same as my own personal view of notable, not to mention completely meaningless because it's a dict and the order shouldn't matter, and even if it did, ROMs are scanned in the order they're listed in platforms.ini anyway. I guess it makes this a bit easier to read than having a huge wall of text though
	platform.name: platform for platform in (
	StandardEmulatedPlatform('3DS',
		set(), set(), {'Citra'}, {MediaType.Cartridge: {'3ds'}, MediaType.Digital: {'cxi', 'cia'}, MediaType.Executable: {'3dsx', 'elf'}}, {
		'tdb_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB 3dstdb.xml file (https://www.gametdb.com/3dstdb.zip)'),
		'covers_path': PlatformConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after 4-letter product code'),
		}, #There is a Nintendo - Nintendo 3DS.dat that could go in datnames but it is indexed by 4-letter serial so I'd have to do some trickery and then the info is already in GameTDB anyway
	),
	StandardEmulatedPlatform('Atari 2600',
		{'a2600'}, {'a2600', 'a2600_cass'}, {'Stella', 'Stella (libretro)', 'MAME (Atari 2600)'}, {MediaType.Cartridge: {'a26'}.union(atari_2600_cartridge_extensions.union(generic_cart_extensions))}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('ColecoVision',
		{'coleco', 'bit90', 'czz50'}, {'coleco'}, {'blueMSX (libretro)', 'MAME (ColecoVision)'}, {MediaType.Cartridge: {'col'}.union(generic_cart_extensions)}, dat_names={'Coleco - ColecoVision'}
	),
	StandardEmulatedPlatform('Dreamcast',
		{'dcjp', 'dcdev'}, {'dc'}, {'Reicast', 'Flycast', 'MAME (Dreamcast)'}, {MediaType.OpticalDisc: cdrom_formats}, dat_names={'Sega - Dreamcast'}, dat_uses_serial=True
	),
	StandardEmulatedPlatform('DS',
		{'nds'}, set(), {'melonDS', 'Medusa'}, {MediaType.Cartridge: {'nds', 'dsi', 'ids', 'srl'}}, {
		'tdb_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB dstdb.xml file (https://www.gametdb.com/dstdb.zip)'),
		'covers_path': PlatformConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after 4-letter product code'),
		},
		dat_names={'Nintendo - Nintendo DS'}
	),
	StandardEmulatedPlatform('Game Boy',
		{'gameboy', 'gbcolor'}, {'gameboy', 'gbcolor'}, 
		{'SameBoy (libretro)', 'Gearboy (libretro)', 'Gambatte', 'mGBA', 'mGBA (libretro)', 'Mednafen (Game Boy)', 'MAME (Game Boy)', 'Medusa', 'GBE+', 'bsnes', 'bsnes (libretro)', 'bsnes-hd beta (libretro)'}, {MediaType.Cartridge: {'gb', 'gbc', 'gbx', 'sgb', 'cgb', 'dmg'}},
		{
			'super_game_boy_bios_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to Super Game Boy BIOS to use'),
			'set_gbc_as_different_platform': PlatformConfigValue(ConfigValueType.Bool, False, 'Set the platform of GBC games to Game Boy Color instead of leaving them as Game Boy'),
		},
		dat_names={'Nintendo - Game Boy', 'Nintendo - Game Boy Color'}
	),
	StandardEmulatedPlatform('GameCube',
		{'gcjp'}, set(), {'Dolphin'}, {MediaType.OpticalDisc: {'iso', 'gcm', 'tgc', 'gcz', 'ciso', 'rvz', 'm3u'}, MediaType.Executable: {'dol', 'elf'}}
		#dat_names could be Nintendo - GameCube but that doesn't give us any more info that isn't in GameTDB and also is indexed by 6-character code so I'd have to fiddle around I think
	),
	StandardEmulatedPlatform('Game Gear',
		{'gamegear'}, {'gamegear'}, {'Genesis Plus GX (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'Mednafen (Game Gear)', 'MAME (Game Gear)'}, {MediaType.Cartridge: {'sms', 'gg', 'bin'}}, dat_names={'Sega - Game Gear'}
	),
	StandardEmulatedPlatform('GBA',
		{'gba'}, {'gba'},
		{'mGBA', 'mGBA (libretro)', 'Mednafen (GBA)', 'MAME (GBA)', 'Medusa', 'GBE+'}, {MediaType.Cartridge: {'gba', 'bin', 'srl'}, MediaType.Executable: {'elf', 'mb'}},
		dat_names={'Nintendo - Game Boy Advance'}
	),
	StandardEmulatedPlatform('Intellivision',
		{'intv'}, {'intv', 'intvecs'}, {'MAME (Intellivision)', 'FreeIntv (libretro)'}, {MediaType.Cartridge: {'bin', 'int', 'rom', 'itv'}}, dat_names={'Mattel - Intellivision'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('Lynx',
		{'lynx'}, {'lynx'},
		{'Mednafen (Lynx)', 'MAME (Lynx)'}, {MediaType.Cartridge: {'lnx', 'lyx'}, MediaType.Executable: {'o'}}, dat_names={'Atari - Lynx'} #This will need header removed
	),
	StandardEmulatedPlatform('Master System',
		{'sms'}, {'sms'},
		{'Genesis Plus GX (libretro)', 'BlastEm (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'Mednafen (Master System)', 'MAME (Master System)'}, {MediaType.Cartridge: {'sms', 'gg', 'bin'}}, dat_names={'Sega - Master System - Mark III'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('Mega Drive',
		{'genesis', 'gen_nomd'}, {'megadriv'},
		{'BlastEm (libretro)', 'Genesis Plus GX (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'Mednafen (Mega Drive)', 'MAME (Mega Drive)'}, {MediaType.Cartridge: {'bin', 'gen', 'md', 'smd', 'sgd'}}, dat_names={'Sega - Mega Drive - Genesis'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('N64',
		{'n64'}, {'n64', 'ique'}, {'Mupen64Plus', 'Mupen64Plus-Next (libretro)', 'MAME (N64)'}, {MediaType.Cartridge: {'z64', 'v64', 'n64', 'bin'}}, 
		{'prefer_controller_pak_over_rumble': PlatformConfigValue(ConfigValueType.Bool, True, 'If a game can use both the Controller Pak and the Rumble Pak, use the Controller Pak')}, 
		dat_names={'Nintendo - Nintendo 64'}, databases_are_byteswapped=True, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('Neo Geo AES',
		#For software list usage
		{'aes'}, {'neogoeo'}, set(), {MediaType.Cartridge: {'bin'}}
	), 
	StandardEmulatedPlatform('Neo Geo Pocket',
		{'ngp'}, {'ngp', 'ngpc'},
		{'Beetle NeoPop (libretro)', 'Mednafen (Neo Geo Pocket)', 'MAME (Neo Geo Pocket)'}, {MediaType.Cartridge: {'ngp', 'npc', 'ngc', 'bin'}},
		dat_names={'SNK - Neo Geo Pocket', 'SNK - Neo Geo Pocket Color'}
	),
	StandardEmulatedPlatform('NES',
		{'nes', 'famicom', 'iq501', 'sb486'}, {'nes', 'nes_ade', 'nes_datach', 'nes_kstudio', 'nes_ntbrom', 'famicom_cass', 'famicom_flop'}, 
		{'Mesen (libretro)', 'Mednafen (NES)', 'MAME (NES)', 'cxNES'}, {MediaType.Cartridge: {'nes', 'unf', 'unif', 'fcn'}, MediaType.Floppy: {'fds', 'qd'}}, 
		{'set_fds_as_different_platform': PlatformConfigValue(ConfigValueType.Bool, False, 'Set the platform of FDS games to FDS instead of leaving them as NES')},
		dat_names={'Nintendo - Nintendo Entertainment System', 'Nintendo - Family Computer Disk System'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('PC Engine',
		{'pce'}, {'pce', 'sgx', 'tg16'}, {'Beetle PCE (libretro)', 'Beetle PCE Fast (libretro)', 'Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)', 'MAME (PC Engine)'}, {MediaType.Cartridge: {'pce', 'sgx', 'bin'}},
		dat_names={'NEC - PC Engine - TurboGrafx 16', 'NEC - PC Engine SuperGrafx'}
	),
	StandardEmulatedPlatform('PlayStation',
		{'psj'}, {'psx'},
		{'DuckStation', 'Beetle PSX HW (libretro)', 'Mednafen (PlayStation)', 'PCSX2'}, {MediaType.OpticalDisc: cdrom_formats, MediaType.Executable: {'exe', 'psx'}},
		dat_names={'Sony - PlayStation'}, dat_uses_serial=True
	),
	StandardEmulatedPlatform('PS2',
		{'ps2'}, set(), {'PCSX2'}, {MediaType.OpticalDisc: cdrom_formats.union({'cso', 'bin'}), MediaType.Executable: {'elf', 'irx'}},
		dat_names={'Sony - PlayStation 2'}, dat_uses_serial=True
	),
	StandardEmulatedPlatform('PS3',
		#Tech tip: Add ~/.config/rpcs3/dev_hdd0/game to rom paths
		set(), set(), {'RPCS3'}, {MediaType.OpticalDisc: {'iso'}, MediaType.Digital: {'pkg'}, MediaType.Executable: {'self', 'elf', 'bin'}}, dat_names={'Sony - PlayStation 3'}, dat_uses_serial=True, options={
			'covers_path': PlatformConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after product code'),
			'tdb_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB ps3tdb.xml file (https://www.gametdb.com/ps3tdb.zip)'),
		}, folder_check=folder_checks.is_ps3_folder
	),
	StandardEmulatedPlatform('PSP',
		set(), set(), {'PPSSPP'}, {MediaType.OpticalDisc: cdrom_formats.union({'cso'}), MediaType.Executable: {'pbp'}}, 
		dat_names={'Sony - PlayStation Portable'}, dat_uses_serial=True, folder_check=folder_checks.is_psp_homebrew_folder
	),
	StandardEmulatedPlatform('Saturn',
		{'saturn'}, {'saturn', 'sat_cart', 'sat_vccart'}, {'Beetle Saturn (libretro)', 'Mednafen (Saturn)', 'MAME (Saturn)'}, {MediaType.OpticalDisc: cdrom_formats},
		dat_names={'Sega - Saturn'}, dat_uses_serial=True
	),
	StandardEmulatedPlatform('SNES',
		{'snes'}, {'snes', 'snes_bspack', 'snes_strom'},
		{'Snes9x', 'Mednafen (SNES)', 'Mednafen (SNES-Faust)', 'MAME (SNES)', 'bsnes', 'bsnes (libretro)', 'bsnes-hd beta (libretro)'}, {MediaType.Cartridge: {'sfc', 'swc', 'smc', 'bs', 'st', 'bin'}}, 
		{
			'sufami_turbo_bios_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to Sufami Turbo BIOS, required to run Sufami Turbo carts'),
			'bsx_bios_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to BS-X BIOS, required to run Satellaview games'),
		},
		dat_names={'Nintendo - Super Nintendo Entertainment System', 'Nintendo - Satellaview', 'Nintendo - Sufami Turbo'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('Switch',
		set(), set(), {'Yuzu'}, {MediaType.Cartridge: {'xci'}, MediaType.Digital: {'nsp', 'nca'}, MediaType.Executable: {'nro', 'nso', 'elf'}}
	),
	StandardEmulatedPlatform('Virtual Boy',
		{'vboy'}, {'vboy'}, {'Beetle VB (libretro)', 'Mednafen (Virtual Boy)', 'MAME (Virtual Boy)'}, {MediaType.Cartridge: {'vb', 'vboy', 'bin'}}, dat_names={'Nintendo - Virtual Boy'}
	),
	StandardEmulatedPlatform('Vita',
		set(), set(), set(), {MediaType.Digital: {'vpk'}}
	),
	StandardEmulatedPlatform('Xbox',
		{'xbox'}, set(), {'Xemu'}, {MediaType.OpticalDisc: {'iso'}, MediaType.Executable: {'xbe'}}
	),
	StandardEmulatedPlatform('Xbox 360',
		set(), set(), set(), {MediaType.OpticalDisc: {'iso'}, MediaType.Executable: {'xex'}}
	),
	StandardEmulatedPlatform('Wii',(), set(), {'Dolphin'}, 
		{MediaType.OpticalDisc: {'iso', 'gcm', 'tgc', 'gcz', 'wbfs', 'ciso', 'wia', 'rvz'}, MediaType.Executable: {'dol', 'elf'}, MediaType.Digital: {'wad'}}, 
		{
			'tdb_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB wiitdb.xml file (https://www.gametdb.com/wiitdb.zip), note that GameCube will use this too!'),
			'common_key': PlatformConfigValue(ConfigValueType.String, '', 'Wii common key used for decrypting Wii discs which some projects are brave enough to hardcode but I am not'),
			'covers_path': PlatformConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after product code, used by GameCube too'),
		},
		dat_names={'Nintendo - Wii'}, dat_uses_serial=True, #Although WiiWare (Nintendo - Wii (Digital)) uses crc… hm, not important for now since there is not really any metadata
		folder_check=folder_checks.is_wii_homebrew_folder
	),
	StandardEmulatedPlatform('Wii U',
		#See roms_folders for how this mostly works
		set(), set(), {'Cemu'}, {MediaType.OpticalDisc: {'iso', 'wud', 'wux'}, MediaType.Executable: {'rpx', 'elf'}},
		{
			'tdb_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to GameTDB wiiutdb.xml file (https://www.gametdb.com/wiiutdb.zip)'),
			'covers_path': PlatformConfigValue(ConfigValueType.FolderPath, None, 'Path to folder containing covers named after 4-letter product code (or sometimes 6 letters)'),
		}
		, folder_check=folder_checks.is_wii_u_folder
	),
	StandardEmulatedPlatform('WonderSwan',
		{'wswan'}, {'wswan', 'wscolor'}, 
		{'Beetle Cygne (libretro)', 'Mednafen (WonderSwan)', 'MAME (WonderSwan)'}, {MediaType.Cartridge: {'ws', 'wsc', 'bin'}}, dat_names={'Bandai - WonderSwan', 'Bandai - WonderSwan Color'}
	),
	
	#Less notable stuff goes here
	StandardEmulatedPlatform('3DO',{'3do'}, set(), {'Opera (libretro)', 'MAME (3DO)'}, {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	StandardEmulatedPlatform('Amiga CD32',{'cd32'}, {'cd32'}, {'PUAE (libretro)', 'FS-UAE', 'MAME (Amiga CD32)'}, {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	StandardEmulatedPlatform('Atari 5200',
		#Does it actually have games on tapes or is MAME listing that as a type just a side effect of it being a spicy Atari 8-bit computer?
		{'a5200'}, {'a5200'},
		{'MAME (Atari 5200)'}, {MediaType.Cartridge: {'a52', 'car'}.union(generic_cart_extensions), MediaType.Tape: generic_tape_extensions}, dat_names={'Atari - 5200'}
	), 
	StandardEmulatedPlatform('Atari 7800',
		{'a7800'}, {'a7800'}, {'ProSystem (libretro)', 'A7800', 'MAME (Atari 7800)'}, {MediaType.Cartridge: {'a78'}.union(generic_cart_extensions)}, dat_names={'Atari - 7800'}, #Actually headered
		autodetect_tv_type=True
	),
	StandardEmulatedPlatform('Channel F',
		{'channelf', 'channlf2'}, {'channelf'},
		{'FreeChaF (libretro)', 'MAME (Channel F)'}, {MediaType.Cartridge: {'chf'}.union(generic_cart_extensions)}, dat_names={'Fairchild - Channel F'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('G7400',{'videopacp'}, {'videopac'}, {'O2EM (libretro)', 'MAME (G7400)'}, {MediaType.Cartridge: generic_cart_extensions}, autodetect_tv_type=True, dat_names={'Philips - Videopac+'}), #Uses same software list as Odyssey 2 currently, maybe should be considered part of that platform?
	StandardEmulatedPlatform('Game.com',{'gamecom'}, {'gamecom'}, {'MAME (Game.com)'}, {MediaType.Cartridge: {'tgc', 'bin'}}, dat_names={'Tiger - Game.com'}),
	StandardEmulatedPlatform('Jaguar',
		{'jaguar'}, {'jaguar'}, {'Virtual Jaguar (libretro)', 'MAME (Jaguar)'}, 
		{MediaType.Cartridge: {'j64'}.union(generic_cart_extensions), MediaType.Executable: {'abs', 'cof', 'jag', 'prg', 'bjl'}}, dat_names={'Atari - Jaguar'}, #j64
		autodetect_tv_type=True
	),
	StandardEmulatedPlatform('Magnavox Odyssey²',
		{'videopac'}, {'videopac'}, {'O2EM (libretro)', 'MAME (Magnavox Odyssey²)', 'MAME (G7400)'}, {MediaType.Cartridge: generic_cart_extensions}, dat_names={'Magnavox - Odyssey2'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('Microvision',{'microvsn'}, {'microvision'}, {'MAME (Microvision)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Neo Geo CD',{'neocdz'}, {'neocd'}, {'NeoCD (libretro)', 'MAME (Neo Geo CD)'}, {MediaType.OpticalDisc: cdrom_formats}),
	StandardEmulatedPlatform('PC-FX',{'pcfx'}, {'pcfx'}, {'Beetle PC-FX (libretro)', 'Mednafen (PC-FX)'}, {MediaType.OpticalDisc: cdrom_formats}),
	StandardEmulatedPlatform('Pokemon Mini',
		{'pokemini'}, {'pokemini'}, {'PokeMini (libretro)', 'PokeMini', 'MAME (Pokemon Mini)'}, {MediaType.Cartridge: {'min', 'bin'}}, dat_names={'Nintendo - Pokemon Mini'}
	),
	StandardEmulatedPlatform('SG-1000',
		{'sg1000', 'sc3000'}, {'sg1000', 'sc3000_cart', 'sc3000_cass', 'sf7000'},
		{'Genesis Plus GX (libretro)', 'blueMSX (libretro)', 'Kega Fusion', 'MAME (SG-1000)'}, {MediaType.Cartridge: {'sg', 'bin', 'sc'}, MediaType.Tape: {'wav', 'bit'}, MediaType.Floppy: mame_floppy_formats.union({'sf', 'sf7'})},
		dat_names={'Sega - SG-1000'}
	),
	StandardEmulatedPlatform('Vectrex',{'vectrex'}, {'vectrex'}, {'Vecx (libretro)', 'MAME (Vectrex)'}, {MediaType.Cartridge: {'vec', 'gam', 'bin'}}, dat_names={'GCE - Vectrex'}),
	StandardEmulatedPlatform('Watara Supervision',{'svision'}, {'svision'}, {'Potator (libretro)', 'MAME (Watara Supervision)'}, {MediaType.Cartridge: {'ws', 'sv', 'bin'}}, dat_names={'Watara - Supervision'}),
	
	#Consoles likely uncared about (I'm being subjective woohoo) just to make the list less of a chungus
	StandardEmulatedPlatform('3DO M2',(), {'3do_m2'}, set(), {MediaType.OpticalDisc: cdrom_formats}), #Was never actually released, but prototypes exist
	StandardEmulatedPlatform('APF-MP1000',{'apfm1000'}, {'apfm1000'}, {'MAME (APF-MP1000)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Arcadia 2001',
		{'arcadia', 'intmpt03', 'orbituvi', 'ormatu', 'plldium'}, {'arcadia'},
		{'MAME (Arcadia 2001)'}, {MediaType.Cartridge: generic_cart_extensions}, dat_names={'Emerson - Arcadia 2001'}, autodetect_tv_type=True
		),
	StandardEmulatedPlatform('Astrocade',{'astrocde'}, {'astrocde'}, {'MAME (Astrocade)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Bandai Playdia',(), set(), set(), {MediaType.OpticalDisc: cdrom_formats}),
	StandardEmulatedPlatform('Bandai Super Vision 8000',{'sv8000'}, {'sv8000'}, {'MAME (Bandai Super Vision 8000)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('C2 Color',{'c2color'}, {'c2color_cart'}, {'MAME (C2 Color)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Casio PV-1000',{'pv1000'}, {'pv1000'}, {'MAME (Casio PV-1000)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Champion 2711',{'unichamp'}, {'unichamp'}, {'MAME (Champion 2711)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('CreatiVision',
		{'crvision', 'lasr2001', 'manager'}, {'crvision', 'laser2001_cart'},
		{'MAME (CreatiVision)'}, {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: generic_tape_extensions}, dat_names={'VTech - CreatiVision'}
	),
	StandardEmulatedPlatform('Dreamcast VMU',{'svmu'}, {'svmu'}, {'VeMUlator (libretro)', 'MAME (Dreamcast VMU)'}, {MediaType.Executable: {'bin'}, MediaType.Digital: {'vms', 'dci'}}),
	StandardEmulatedPlatform('Entex Adventure Vision',{'advision'}, {'advision'}, {'MAME (Entex Adventure Vision)'}, {MediaType.Cartridge: generic_cart_extensions}, dat_names={'Entex - Adventure Vision'}),
	StandardEmulatedPlatform('Epoch Game Pocket Computer',{'gamepock'}, {'gamepock'}, {'MAME (Epoch Game Pocket Computer)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Gamate',{'gamate'}, {'gamate'}, {'MAME (Gamate)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('GameKing',{'gameking'}, {'gameking'}, {'MAME (GameKing)'}, {MediaType.Cartridge: {'gk'}.union(generic_cart_extensions)}),
	StandardEmulatedPlatform('GameKing 3',{'gamekin3'}, {'gameking3'}, {'MAME (GameKing 3)'}, {MediaType.Cartridge: {'gk3'}.union(generic_cart_extensions)}),
	StandardEmulatedPlatform('GoGo TV Video Vision',{'tvgogo'}, {'tvgogo'}, {'MAME (GoGo TV Video Vision)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('GP2X',{'gp2x'}, set(), set(), {}), #TODO: File formats and things
	StandardEmulatedPlatform('GP32',
		{'gp32'}, {'gp32'}, {'MAME (GP32)'}, {MediaType.Cartridge: {'smc'}, MediaType.Executable: {'gxb', 'sxf', 'bin', 'gxf', 'fxe'}, MediaType.Digital: {'fpk'}}, dat_names={'GamePark - GP32'}
	),
	StandardEmulatedPlatform('Hartung Game Master',{'gmaster'}, {'gmaster'}, {'MAME (Hartung Game Master)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Mattel HyperScan',{'hyprscan'}, {'hyperscan'}, {'MAME (Mattel HyperScan)'}, {MediaType.OpticalDisc: cdrom_formats}),
	StandardEmulatedPlatform('Mega Duck',{'megaduck', 'mduckspa'}, {'megaduck'}, {'SameDuck (libretro)', 'MAME (Mega Duck)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Monon Color',{'mononcol'}, {'monon_color'}, {'MAME (Monon Color)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Nuon',(), {'nuon'}, set(), {MediaType.OpticalDisc: {'iso'}}),
	StandardEmulatedPlatform('PocketStation',{'pockstat'}, set(), set(), {MediaType.Digital: {'gme', 'bin'}}),
	StandardEmulatedPlatform('RCA Studio 2',{'studio2'}, {'studio2'}, set(), {MediaType.Cartridge: {'st2'}.union(generic_cart_extensions)}, dat_names={'RCA - Studio II'}, autodetect_tv_type=True), #Headered
	StandardEmulatedPlatform('Select-a-Game',{'sag'}, {'entex_sag'}, {'MAME (Select-a-Game)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform("Super A'Can",{'supracan'}, {'supracan'}, {"MAME (Super A'Can)"}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Super Cassette Vision',
		{'scv'}, {'scv'}, {'MAME (Super Cassette Vision)'}, {MediaType.Cartridge: generic_cart_extensions}, dat_names={'Epoch - Super Cassette Vision'}
	),
	StandardEmulatedPlatform('VC 4000',{'vc4000', '1292apvs', 'database', 'elektor', 'h21', 'krvnjvtv', 'mpt05', 'rwtrntcs'}, {'vc4000', 'database'}, {'MAME (VC 4000)'}, {MediaType.Cartridge: generic_cart_extensions}, autodetect_tv_type=True), #Which one is the "main" platform, really, bit of a clusterfuck (well the software list is named vc4000 I guess)
	StandardEmulatedPlatform('ZAPit Game Wave',(), set(), set(), {MediaType.OpticalDisc: {'iso'}}),
	StandardEmulatedPlatform('Zeebo',{'zeebo'}, set(), set(), {}), #Folders with "mif" and "mod"?

	#Homebrew projects or whatever
	StandardEmulatedPlatform('Arduboy',(), set(), set(), {MediaType.Digital: {'arduboy'}, MediaType.Executable: {'hex'}}),
	StandardEmulatedPlatform('Uzebox',{'uzebox'}, {'uzebox'}, {'Uzem (libretro)', 'MAME (Uzebox)'}, {MediaType.Executable: {'bin', 'uze'}}, dat_names={'Uzebox'}),

	#Educational sort-of-game consoles
	StandardEmulatedPlatform('Advanced Pico Beena',{'beena'}, {'sega_beena_cart'}, {'MAME (Advanced Pico Beena)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('ClickStart',{'clikstrt'}, {'clickstart_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Copera',{'copera'}, {'copera'}, {'MAME (Copera)'}, {MediaType.Cartridge: {'bin', 'md'}}), #Pico-related, but not quite the same (software will show warning message on Pico)
	StandardEmulatedPlatform('Didj',{'didj'}, {'leapfrog_didj_cart'}, {'MAME (Didj)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('InnoTab',{'innotab2'}, {'vtech_innotab_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('InnoTV',{'innotv'}, {'vtech_innotv_innotabmax_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}), #The InnoTab MAX is another system that uses the same cartridges
	StandardEmulatedPlatform('iQuest',{'iquest'}, {'leapfrog_iquest_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('LeapPad',{'leappad'}, {'leapfrog_leappad_cart'}, {'MAME (LeapPad)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Leapster',{'leapster'}, {'leapster'}, {'MAME (Leapster)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Little Touch LeapPad',{'ltleappad'}, {'leapfrog_ltleappad_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('MobiGo',{'mobigo', 'mobigo2'}, {'mobigo_cart'}, {'MAME (MobiGo)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('My First LeapPad',{'mfleappad'}, {'leapfrog_mfleappad_cart'}, {'MAME (My First LeapPad)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Sawatte Pico',{'sawatte'}, {'sawatte'}, set(), {}),
	StandardEmulatedPlatform('Sega Pico',{'pico'}, {'pico'}, {'Genesis Plus GX (libretro)', 'Kega Fusion', 'MAME (Sega Pico)'}, {MediaType.Cartridge: {'bin', 'md'}}, dat_names={'Sega - PICO'}, autodetect_tv_type=True),
	StandardEmulatedPlatform('SmarTV Adventures',{'smartvad'}, {'smarttv_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Story Reader',{'pi_stry'}, {'pi_storyreader_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Story Reader 2',{'pi_stry2'}, {'pi_storyreader_v2_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Telestory',{'telestry'}, {'telestory_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Tomy Prin-C',{'princ'}, {'princ'}, {'MAME (Tomy Prin-C)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Turbo Extreme',{'turboex'}, {'leapfrog_turboextreme_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Turbo Twist Brain Quest',{'ttwistbq'}, {'leapfrog_turbotwistbrainquest_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Turbo Twist Math',{'ttwistm'}, {'leapfrog_turbotwistmath_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('V.Baby',{'vbaby'}, {'vbaby_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}), #Not compatible at all with V.Smile Baby which is confusing
	StandardEmulatedPlatform('V.Reader',{'vreader'}, {'vtech_storio_cart'}, {'MAME (V.Reader)'}, {MediaType.Cartridge: generic_cart_extensions}), 
	#Skeleton driver, apparently also known as Storio, or something like that
	StandardEmulatedPlatform('V.Smile Pro',{'vsmilpro'}, {'vsmile_cd'}, {'MAME (V.Smile Pro)'}, {MediaType.OpticalDisc: cdrom_formats}),
	StandardEmulatedPlatform('V.Smile',{'vsmile'}, {'vsmile_cart'}, {'MAME (V.Smile)'}, {MediaType.Cartridge: generic_cart_extensions}, dat_names={'VTech - V.Smile'}),
	StandardEmulatedPlatform('V.Smile Baby',{'vsmileb'}, {'vsmileb_cart'}, {'MAME (V.Smile Baby)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('V.Smile Motion',{'vsmilem'}, {'vsmilem_cart'}, {'MAME (V.Smile Motion)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('V.Tech Socrates',{'socrates'}, {'socrates'}, {'MAME (V.Tech Socrates)'}, {MediaType.Cartridge: generic_cart_extensions}),
	
	#Consoles that barely count as consoles because aren't for gaming or whatever (or games push the definition), but for the purposes of creating a launcher, might as well be consoles
	StandardEmulatedPlatform('BBC Bridge Companion',{'bbcbc'}, {'bbcbc'}, {'MAME (BBC Bridge Companion)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Benesse Pocket Challenge V2',(), {'pockchalv2'}, {'Beetle Cygne (libretro)', 'Mednafen (WonderSwan)', 'MAME (WonderSwan)'}, {MediaType.Cartridge: {'pc2', 'bin'}}), #Sort of WonderSwan with different controls
	StandardEmulatedPlatform('Buzztime Home Trivia System',{'buzztime'}, {'buzztime_cart'}, {'MAME (Buzztime Home Trivia System)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Casio Loopy',{'casloopy'}, {'casloopy'}, {'MAME (Casio Loopy)'}, {MediaType.Cartridge: generic_cart_extensions}, dat_names={'Casio - Loopy'}),
	StandardEmulatedPlatform('Design Master Denshi Mangajuku',{'bdesignm'}, {'bdesignm_design_cart', 'bdesignm_game_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}), #This will be interesting because you're supposed to use combinations of different design carts and game carts at the same time
	StandardEmulatedPlatform('Gachinko Contest! Slot Machine TV',{'gcslottv'}, {'gcslottv'}, {'MAME (Gachinko Contest! Slot Machine TV)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Koei PasoGo',{'pasogo'}, {'pasogo'}, {'MAME (Koei PasoGo)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Konami Picno',{'picno', 'picno2'}, {'picno'}, {'MAME (Konami Picno)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Mattel Juice Box',{'juicebox'}, {'juicebox'}, {'MAME (Mattel Juice Box)'}, {MediaType.Cartridge: {'smc'}}),
	StandardEmulatedPlatform('Nichibutsu My Vision',{'myvision'}, {'myvision'}, {'MAME (Nichibutsu My Vision)'}, {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Pocket Challenge W',{'pockchal'}, {'pockchalw'}, {'MAME (Pocket Challenge W)'}, {MediaType.Cartridge: {'bin', 'pcw'}}),
	
	#Multimedia consoles that also don't like to be classified as game consoles
	StandardEmulatedPlatform('CD-i',{'cdimono1', 'cdimono2', 'cdi490a', 'cdi910'}, {'cdi'}, {'MAME (CD-i)'}, {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	StandardEmulatedPlatform('Commodore CDTV',{'cdtv'}, {'cdtv'}, {'PUAE (libretro)', 'FS-UAE', 'MAME (Commodore CDTV)'}, {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),	
	StandardEmulatedPlatform('Memorex VIS',{'vis'}, set(), {'MAME (Memorex VIS)'}, {MediaType.OpticalDisc: cdrom_formats}),
	StandardEmulatedPlatform('Pippin',{'pippin'}, {'pippin', 'pippin_flop'}, {'MAME (Pippin)'}, {MediaType.OpticalDisc: cdrom_formats}),

	#Addons for other systems that we're going to treat as separate things because it seems to make more sense that way, until it doesn't
	StandardEmulatedPlatform('32X',{'32x'}, {'32x'}, {'PicoDrive (libretro)', 'Kega Fusion', 'MAME (32X)'}, {MediaType.Cartridge: {'32x', 'bin'}}, dat_names={'Sega - 32X'}, autodetect_tv_type=True),
	StandardEmulatedPlatform('64DD',{'n64dd'}, {'n64dd'}, set(), {MediaType.Floppy: {'ndd', 'ddd'}}, dat_names={'Nintendo - Nintendo 64DD'}),
	StandardEmulatedPlatform('e-Reader',{'gba'}, {'gba_ereader'}, set(), {MediaType.Barcode: {'bin', 'raw', 'bmp'}}),
	StandardEmulatedPlatform('Jaguar CD',{'jaguarcd'}, set(), {'MAME (Jaguar CD)'}, {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True),
	StandardEmulatedPlatform('Mega CD',
		#LaserActive counts as this for now
		{'segacd', '32x_scd', 'cdx', 'segacd2', 'xeye', 'laseract'}, {'megacd', 'megacdj', 'segacd'},
		{'Genesis Plus GX (libretro)', 'PicoDrive (libretro)', 'Kega Fusion', 'MAME (Mega CD)'}, {MediaType.OpticalDisc: cdrom_formats}, autodetect_tv_type=True, dat_names={'Sega - Mega-CD - Sega CD'}, dat_uses_serial=True
	),
	StandardEmulatedPlatform('PC Engine CD',
		{'pce'}, {'pcecd'}, {'Beetle PCE (libretro)', 'Beetle PCE Fast (libretro)', 'Mednafen (PC Engine)', 'Mednafen (PC Engine Fast)'}, {MediaType.OpticalDisc: cdrom_formats}
	),
	StandardEmulatedPlatform('Play-Yan',{'gba'}, set(), set(), {MediaType.Digital: {'asf'}}),

	#PDA type things that I don't really wanna put under computers
	StandardEmulatedPlatform('Cybiko',{'cybikov1'}, set(), set(), {MediaType.Digital: {'app'}}),
	#'Cybiko Xtreme': SystemInfo('cybikoxt', set(), set(), {MediaType.Digital: {'app'}}), #Does this really qualify as a different thing?
	StandardEmulatedPlatform('Gizmondo',{'gizmondo'}, set(), set(), {}), #Uses folders seemingly, so that may be weird with the file types
	StandardEmulatedPlatform('N-Gage',(), set(), set(), {MediaType.Digital: {'app'}}),
	StandardEmulatedPlatform('Sharp Wizard',{'iq7000'}, {'wizard_cart'}, set(), {MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('Tapwave Zodiac',(), set(), set(), {}), #File type is like, kinda .prc but kinda not (the device runs spicy PalmOS, would it be considered part of that if any of that was emulated?)
	
	#Computers that most people are here for (wew I'm being subjective again)
	StandardEmulatedPlatform('Acorn Electron',{'electron'}, {'electron_cass', 'electron_cart', 'electron_flop', 'electron_rom'}, set(), {MediaType.Tape: {'wav', 'csw', 'uef'}, MediaType.Floppy: {'ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl'}}),
	StandardEmulatedPlatform('Amiga',
		{'a1000', 'a1200', 'a2000', 'a3000', 'a4000', 'a4000t', 'a500', 'a500p', 'a600'}, {'amiga_a1000', 'amiga_a3000', 'amigaaga_flop', 'amiga_flop', 'amiga_apps', 'amiga_hardware', 'amigaecs_flop', 'amigaocs_flop', 'amiga_workbench'}, 
		{'PUAE (libretro)', 'FS-UAE'}, {MediaType.Floppy: {'adf', 'ipf', 'dms', 'adz', 'fdi', 'm3u'}, MediaType.HardDisk: {'hdf', 'hdz'}, MediaType.Digital: {'lha'}, MediaType.Executable: ['exe', 'bin'], MediaType.OpticalDisc: cdrom_formats},
		#TODO: m3u would be both Floppy and OpticalDisc there, and logically that is actually true, and an example of why this isn't how we should manage file extensions
		autodetect_tv_type=True, dat_names={'Commodore - Amiga'}
	),
	StandardEmulatedPlatform('Amstrad CPC',{'cpc464', 'cpc6128p', 'gx4000'}, {'cpc_cass', 'cpc_flop', 'gx4000'}, {'Caprice32 (libretro)', 'MAME (Amstrad GX4000)'}, {MediaType.Snapshot: {'sna'}, MediaType.Tape: {'wav', 'cdt'}, MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: {'cpr'}.union(generic_cart_extensions)}, dat_names={'Amstrad - CPC', 'Amstrad - GX4000'}),
	StandardEmulatedPlatform('Apple II',{'apple2', 'apple2c', 'apple2e', 'cece', 'cecg', 'ceci', 'cecm', 'cec2000'}, {'apple2', 'apple2_cass', 'apple2_flop_orig', 'apple2_flop_clcracked', 'apple2_flop_misc'}, {'MAME (Apple II)', 'Mednafen (Apple II)'}, {MediaType.Floppy: {'do', 'dsk', 'po', 'nib', 'woz', 'shk', 'bxy'}, MediaType.Tape: generic_tape_extensions, MediaType.Executable: {'prg'}}),
	StandardEmulatedPlatform('Apple IIgs',{'apple2gs'}, {'apple2gs'}, {'MAME (Apple IIgs)'}, {MediaType.Floppy: mame_floppy_formats.union({'2mg', '2img', 'dc', 'shk', 'bxy', 'woz'})}),
	StandardEmulatedPlatform('Atari 8-bit',
		{'a800', 'a400', 'a800xl', 'xegs'}, {'a800', 'a800_flop', 'xegs'}, 
		{'MAME (Atari 8-bit)'}, {MediaType.Floppy: {'atr', 'dsk', 'xfd', 'dcm'}, MediaType.Executable: {'xex', 'bas', 'com', 'exe'}, MediaType.Cartridge: {'bin', 'rom', 'car'}, MediaType.Tape: generic_tape_extensions}, 
		{'basic_path': PlatformConfigValue(ConfigValueType.FilePath, None, 'Path to BASIC ROM for floppy software which requires that, or use "basicc" to use software')
		}, autodetect_tv_type=True),
	StandardEmulatedPlatform('Atari ST',{'st', 'ste', 'tt030', 'falcon30'}, {'st_flop', 'st_cart'}, {'Hatari (libretro)'}, 
		{MediaType.Cartridge: {'bin', 'rom'}, MediaType.Floppy: mame_floppy_formats.union({'st', 'stx', 'msa', 'dim', 'm3u'}), MediaType.Executable: {'prg'}}, 
		autodetect_tv_type=True, dat_names={'Atari - ST'}),
	StandardEmulatedPlatform('BBC Master',{'bbcm', 'bbcmc'}, {'bbcm_cart', 'bbcm_cass', 'bbcmc_flop', 'bbcm_flop'}, set(), {MediaType.Tape: {'wav', 'csw', 'uef'}, MediaType.Floppy: {'ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'ima', 'ufi', '360'}.union(mame_floppy_formats), MediaType.Cartridge: {'rom', 'bin'}}, autodetect_tv_type=True),
	StandardEmulatedPlatform('BBC Micro',{'bbcb', 'bbcbp'}, {'bbca_cass', 'bbcb_cass', 'bbcb_cass_de', 'bbcb_flop', 'bbcb_flop_orig', 'bbc_flop_65c102', 'bbc_flop_6502', 'bbc_flop_32016', 'bbc_flop_68000', 'bbc_flop_80186', 'bbc_flop_arm', 'bbc_flop_torch', 'bbc_flop_z80'}, set(), {MediaType.Tape: {'wav', 'csw', 'uef'}, MediaType.Floppy: {'ssd', 'bbc', 'img', 'dsd', 'adf', 'ads', 'adm', 'adl', 'fds', 'dsk', 'ima', 'ufi', '360'}, MediaType.Cartridge: {'rom', 'bin'}}, autodetect_tv_type=True),
	StandardEmulatedPlatform('C64',
		{'c64'}, {'c64_cart', 'c64_cass', 'c64_flop', 'c64_flop_clcracked', 'c64_flop_orig', 'c64_flop_misc'}, 
		{'MAME (C64)', 'VICE (C64)', 'VICE (C64 Fast)'}, {MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: {'tap', 't64'}, MediaType.Executable: {'prg', 'p00'}, MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('FM Towns',{'fmtowns', 'fmtmarty'}, {'fmtowns_cd', 'fmtowns_flop_cracked', 'fmtowns_flop_misc', 'fmtowns_flop_orig'}, {'MAME (FM Towns)', 'MAME (FM Towns Marty)'}, {MediaType.Floppy: mame_floppy_formats.union({'bin', 'hdm'}), MediaType.OpticalDisc: cdrom_formats}), #Floppy list was just fmtowns_flop prior to 0.230
	StandardEmulatedPlatform('MSX',
		msx1_drivers, {'msx1_cart', 'msx1_cass', 'msx1_flop'},
		{'blueMSX (libretro)', 'fMSX (libretro)', 'MAME (MSX)', 'MAME (MSX2)'}, {MediaType.Floppy: mame_floppy_formats.union({'dmk', 'm3u'}), MediaType.Tape: {'wav', 'tap', 'cas'}, MediaType.Cartridge: generic_cart_extensions, MediaType.Executable: {'com'}},
		dat_names={'Microsoft - MSX'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('MSX2',
		msx2_drivers, {'msx2_cart', 'msx2_cass', 'msx2_flop'},
		{'blueMSX (libretro)', 'fMSX (libretro)', 'MAME (MSX2)'}, {MediaType.Floppy: mame_floppy_formats.union({'dmk', 'm3u'}), MediaType.Tape: {'wav', 'tap', 'cas'}, MediaType.Cartridge: generic_cart_extensions, MediaType.Executable: {'com'}},
		dat_names={'Microsoft - MSX 2'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('MSX2+',
		#Should this be considered the same system as MSX2? Oh dear, I've gotten confused
		msx2plus_drivers, {'msx2p_flop'},
		{'blueMSX (libretro)', 'fMSX (libretro)', 'MAME (MSX2+)'}, {MediaType.Floppy: mame_floppy_formats.union({'dmk', 'm3u'}), MediaType.Tape: {'wav', 'tap', 'cas'}, MediaType.Cartridge: generic_cart_extensions, MediaType.Executable: {'com'}},
		dat_names={'Microsoft - MSX 2'}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('MSX Turbo-R',msx_turbo_r_drivers, {'msxr_flop'}, set(), {MediaType.Floppy: mame_floppy_formats}),
	StandardEmulatedPlatform('PC-98',{'pc9801f', 'pc9801rs', 'pc9801ux', 'pc9821'}, {'pc98', 'pc98_cd'}, set(), {MediaType.Floppy: mame_floppy_formats, MediaType.OpticalDisc: cdrom_formats}, dat_names={'NEC - PC-98'}),
	StandardEmulatedPlatform('Sharp X68000',{'x68000'}, {'x68k_flop'}, {'PX68k (libretro)', 'MAME (Sharp X68000)'}, {MediaType.Floppy: mame_floppy_formats.union({'xdf', 'hdm', '2hd', 'dim', 'm3u'}), MediaType.HardDisk: {'hdf'}}, dat_names={'Sharp - X68000'}),
	StandardEmulatedPlatform('Tandy CoCo',{'coco'}, {'coco_cart', 'coco_flop'}, {'MAME (Tandy CoCo)'}, {MediaType.Cartridge: {'ccc', 'rom', 'bin'}, MediaType.Tape: {'wav', 'cas'}, MediaType.Floppy: mame_floppy_formats.union({'dmk', 'jvc'}), MediaType.HardDisk: {'vhd'}}),
	StandardEmulatedPlatform('TRS-80',{'trs80', 'trs80l2', 'trs80m3'}, set(), {'MAME (TRS-80)'}, {MediaType.Executable: {'cmd'}, MediaType.Tape: {'wav', 'cas'}, MediaType.Floppy: {'dmk'}.union(mame_floppy_formats)}),
	StandardEmulatedPlatform('ZX Spectrum',{'spectrum', 'spec128'}, {'spectrum_cart', 'spectrum_cass', 'specpls3_flop', 'pentagon_cass', 'spectrum_flop_opus', 'spectrum_mgt_flop', 'spectrum_microdrive', 'spectrum_wafadrive', 'timex_dock', 'timex_cass'}, {'FUSE (libretro)', 'MAME (ZX Spectrum)'}, {MediaType.Snapshot: {'z80', 'sna'}, MediaType.Tape: {'wav', 'cas', 'tap', 'tzx'}, MediaType.Executable: {'raw', 'scr'}, MediaType.Floppy: {'dsk', 'ipf', 'trd', 'td0', 'scl', 'fdi', 'opd', 'opu'}, MediaType.Cartridge: {'bin', 'rom'}}, dat_names={'Sinclair - ZX Spectrum', 'Sinclair - ZX Spectrum +3'}), #There's actually like a katrillion file formats so I won't bother with all of them until I see them in the wild tbh

	#Other computers that aren't as exciting
	StandardEmulatedPlatform('Acorn Archimedes',{'aa310', 'aa4000', 'aa5000'}, {'archimedes'}, set(), {MediaType.Floppy: mame_floppy_formats.union({'adf'})}), 
	StandardEmulatedPlatform('Apple III',{'apple3'}, {'apple3'}, {'MAME (Apple III)'}, {MediaType.Floppy: {'do', 'dsk', 'po', 'nib', 'woz'}}),
	StandardEmulatedPlatform('Apple Lisa',{'lisa', 'lisa2'}, {'lisa'}, set(), {MediaType.Floppy: mame_floppy_formats.union({'dc', 'dc42'})}),
	StandardEmulatedPlatform('C128',{'c128', 'c128p'}, {'c128_cart', 'c128_flop', 'c128_rom'}, {'VICE (C128)'},
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: {'tap', 't64'}, MediaType.Executable: {'prg', 'p00'}, MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('CBM-II',{'b128hp', 'b500', 'p500'}, {'cbm2_cart', 'cbm2_flop'}, set(), {MediaType.Floppy: {'d80', 'd88', 'd77'}.union(mame_floppy_formats), MediaType.Cartridge: {'20', '40', '60'}, MediaType.Executable: {'p00', 'prg', 't64'}}),
	StandardEmulatedPlatform('Commodore PET',{'pet2001', 'cbm8296', 'pet2001b', 'pet2001n', 'pet4016', 'pet4032b', 'pet8032'}, {'pet_cass', 'pet_flop', 'pet_hdd', 'pet_quik', 'pet_rom'}, {'VICE (Commodore PET)'}, {MediaType.Floppy: commodore_disk_formats, MediaType.Cartridge: {'bin', 'rom'}, MediaType.Executable: {'prg', 'p00'}, MediaType.Tape: {'wav', 'tap'}}),
	StandardEmulatedPlatform('Dragon',{'dragon32'}, {'dragon_cart', 'dragon_cass', 'dragon_flex', 'dragon_flop', 'dragon_os9'}, set(), {MediaType.Floppy: {'dmk', 'jvc', 'vdk', 'sdf', 'os9'}.union(mame_floppy_formats), MediaType.Cartridge: {'ccc', 'rom'}, MediaType.Tape: {'wav', 'cas'}}),
	StandardEmulatedPlatform('FM-7',{'fm7', 'fm8', 'fm11', 'fm16beta'}, {'fm7_cass', 'fm7_disk', 'fm77av'}, {'MAME (FM-7)'}, {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: {'wav', 't77'}}),
	StandardEmulatedPlatform('IBM PCjr',{'ibmpcjr', 'ibmpcjx'}, {'ibmpcjr_cart'}, {'MAME (IBM PCjr)'}, {MediaType.Cartridge: {'bin', 'jrc'}, MediaType.Floppy: mame_floppy_formats, MediaType.Executable: {'exe', 'com', 'bat'}}),
	#Most software is going to go under DOS or PC Booter, but this would be the carts… hmm… does this make sense, actually
	StandardEmulatedPlatform('PC Booter',{'ibm5150'}, {'ibm5150'}, {'MAME (IBM PCjr)', 'MAME (IBM PC)'}, {MediaType.Floppy: mame_floppy_formats.union({'img'}), MediaType.Executable: {'exe', 'com', 'bat'}}), #TODO: Reconsider this name; does it make more sense to be called "IBM PC"? Are PCjr carts not just PC booters that are carts instead of floppies (hot take)?
	StandardEmulatedPlatform('PC-6001',{'pc6001'}, set(), {'MAME (PC-6001)'}, {MediaType.Tape: {'cas', 'p6'}, MediaType.Cartridge: generic_cart_extensions}),
	StandardEmulatedPlatform('PC-88',{'pc8801', 'pc88va'}, {'pc8801_cass', 'pc8801_flop', 'pc8201', 'pc88va'}, {'MAME (PC-88)'}, {MediaType.Floppy: mame_floppy_formats.union('m3u'), MediaType.Tape: {'wav', 'cmt', 't88'}}, dat_names={'NEC - PC-8001 - PC-8801'}),
	StandardEmulatedPlatform('PDP-1',{'pdp1'}, set(), set(), {MediaType.Tape: {'tap', 'rim'}}),
	StandardEmulatedPlatform('Plus/4',{'c264'}, {'plus4_cart', 'plus4_cass', 'plus4_flop'}, {'VICE (Plus/4)'},
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: {'tap', 't64'}, MediaType.Executable: {'prg', 'p00'}, MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	), 	#Also includes C16 and C116 (I admit I am not cool enough to know the difference)
	StandardEmulatedPlatform('SAM Coupe',{'samcoupe'}, {'samcoupe_cass', 'samcoupe_flop'}, {'SimCoupe', 'MAME (SAM Coupe)'}, {MediaType.Floppy: {'mgt', 'sad', 'dsk', 'sdf'}, MediaType.Executable: {'sbt'}}),
	StandardEmulatedPlatform('Sharp X1',{'x1'}, {'x1_cass', 'x1_flop'}, {'X Millennium (libretro)', 'MAME (Sharp X1)'}, {MediaType.Floppy: {'2d', 'm3u'}.union(mame_floppy_formats), MediaType.Tape: {'wav', 'tap'}}),
	StandardEmulatedPlatform('TI-99',{'ti99_4', 'ti99_4a', 'ti99_8'}, {'ti99_cart'}, set(), {MediaType.Cartridge: {'bin', 'rpk', 'c', 'g'}, MediaType.Tape: {'wav'}, MediaType.Floppy: mame_floppy_formats}, autodetect_tv_type=True),
	StandardEmulatedPlatform('VIC-20',{'vic1001'}, {'vic1001_cart', 'vic1001_cass', 'vic1001_flop'}, {'MAME (VIC-20)', 'VICE (VIC-20)'},
		{MediaType.Cartridge: commodore_cart_formats, MediaType.Tape: {'wav', 'tap', 't64'}, MediaType.Executable: {'prg', 'p00'}, MediaType.Floppy: commodore_disk_formats}, autodetect_tv_type=True
	),
	StandardEmulatedPlatform('ZX81',{'zx81', 'zx80'}, {'zx80_cass', 'zx81_cass'}, {'81 (libretro)'}, {MediaType.Tape: {'wav', 'cas', 'p', '81', 'tzx', 't81'}}, dat_names={'Sinclair - ZX 81'}),
	
	#More obscure computers because otherwise the above section is long and hard to read
	StandardEmulatedPlatform('Acorn Atom',{'atom'}, {'atom_cass', 'atom_flop', 'atom_rom'}, set(), {MediaType.Floppy: {'40t', 'dsk'}, MediaType.Tape: {'wav', 'tap', 'csw', 'uef'}, MediaType.Executable: {'atm'}, MediaType.Cartridge: {'bin', 'rom'}}),
	StandardEmulatedPlatform('Alice 32',{'alice32'}, {'alice32', 'alice90'}, set(), {MediaType.Tape: {'wav', 'cas', 'c10', 'k7'}}),
	StandardEmulatedPlatform('Amstrad PCW',{'pcw8256'}, {'pcw'}, {'MAME (Amstrad PCW)'}, {MediaType.Floppy: mame_floppy_formats, MediaType.Executable: {'com'}}),
	StandardEmulatedPlatform('Amstrad PCW16',{'pcw16'}, {'pcw16'}, set(), {MediaType.Floppy: mame_floppy_formats}),
	StandardEmulatedPlatform('APF Imagination Machine',{'apfimag'}, {'apfimag_cass', 'apfm1000'}, set(), {MediaType.Cartridge: {'bin'}, MediaType.Tape: {'wav', 'cas', 'cpf', 'apt'}, MediaType.Floppy: mame_floppy_formats}), #Considered separate from APF-M1000 (same predicament as Coleco Adam) (or is it? (maybe?))
	StandardEmulatedPlatform('Apple I',{'apple1'}, {'apple1'}, set(), {MediaType.Tape: {'wav'}, MediaType.Snapshot: {'snp'}}), #Loading tapes would require parsing software list usage to figure out where to put load addresses and things to make an autoboot script, because otherwise it's just way too messy to warrant being in a frontend. Snapshots supposedly exist, but I haven't seen any whoops
	StandardEmulatedPlatform('Apogey BK-01',{'apogee'}, {'apogee'}, set(), {MediaType.Tape: {'wav', 'rka'}}), #Should this be rolled up into Radio 86?
	StandardEmulatedPlatform('Atari Portfolio',{'pofo'}, {'pofo'}, set(), {MediaType.Cartridge: {'bin', 'rom'}}),
	StandardEmulatedPlatform('Bandai RX-78',{'rx78'}, {'rx78_cart', 'rx78_cass'}, {'MAME (Bandai RX-78)'}, {MediaType.Cartridge: {'bin', 'rom'}, MediaType.Tape: {'wav'}}), #Software list was just rx78 prior to MAME 0.228
	StandardEmulatedPlatform('Bullet',{'wmbullet'}, {'wmbullet'}, set(), {MediaType.Floppy: mame_floppy_formats}),
	StandardEmulatedPlatform('C64DTV',{'c64dtv'}, set(), set(), {MediaType.Floppy: commodore_disk_formats, MediaType.Executable: {'prg'}}),
	StandardEmulatedPlatform('Cambridge Z88',{'z88'}, {'z88_cart'}, set(), {MediaType.Cartridge: {'epr', 'bin'}}),
	StandardEmulatedPlatform('Camputers Lynx',{'lynx48k'}, {'camplynx_cass', 'camplynx_flop'}, set(), {MediaType.Floppy: mame_floppy_formats.union({'ldf'}), MediaType.Tape: {'wav', 'tap'}}),
	#Convinced that whoever invented this system and the way it loads programs personally hates me, even though I wasn't born when it was made and so that's not really possible
	StandardEmulatedPlatform('Canon X07',{'x07'}, {'x07_card', 'x07_cass'}, set(), {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: {'wav', 'tap'}}),
	StandardEmulatedPlatform('Casio PV-2000',{'pv2000'}, {'pv2000'}, {'MAME (Casio PV-2000)'}, {MediaType.Cartridge: {'bin'}, MediaType.Tape: {'wav'}}),
	StandardEmulatedPlatform('Central Data 2650',{'cd2650'}, set(), set(), {MediaType.Tape: {'wav'}, MediaType.Executable: {'pgm'}}),
	StandardEmulatedPlatform('Coleco Adam',{'adam'}, {'adam_cart', 'adam_cass', 'adam_flop'}, {'MAME (Coleco Adam)'}, {MediaType.Cartridge: {'col', 'bin', 'rom'}, MediaType.Tape: {'wav', 'ddp'}, MediaType.Floppy: mame_floppy_formats, MediaType.Executable: {'lbr', 'com'}}), #Hmm should this just be part of ColecoVision
	StandardEmulatedPlatform('Colour Genie',{'cgenie'}, {'cgenie_cass', 'cgenie_flop_rom'}, set(), {MediaType.Tape: {'wav', 'cas'}, MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: {'rom'}}),
	StandardEmulatedPlatform('Commodore 65',{'c65'}, {'c65_flop'}, set(), {MediaType.Floppy: commodore_disk_formats}), #Never actually released, has software anyway; only good for software lists
	StandardEmulatedPlatform('Compis',{'compis'}, {'compis'}, set(), {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: {'wav'}}),
	StandardEmulatedPlatform('Cosmac VIP',{'vip'}, {'vip'}, set(), {MediaType.Tape: {'wav'}}), #Also a Chip-8 interpreter
	StandardEmulatedPlatform('Dream 6800',{'d6800'}, set(), set(), {MediaType.Tape: {'wav'}}), #Chip-8 interpreter
	StandardEmulatedPlatform('Electronika BK',{'bk0010'}, {'bk0010'}, set(), {MediaType.Tape: {'wav', 'tap'}, MediaType.Floppy: mame_floppy_formats, MediaType.HardDisk: {'hdi'}, MediaType.Executable: {'bin'}}),
	StandardEmulatedPlatform('Elf II',{'elf2'}, set(), set(), {MediaType.Tape: {'wav'}, MediaType.Executable: {'bin'}}),
	StandardEmulatedPlatform('Enterprise',{'ep64'}, {'ep64_cart', 'ep64_cass', 'ep64_flop'}, set(), {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: {'wav'}}),
	StandardEmulatedPlatform('ETI-660',{'eti660'}, {'eti660_quik'}, set(), {MediaType.Tape: {'wav'}}), #A Chip-8 interpreting machine
	StandardEmulatedPlatform('Exidy Sorcerer',{'sorcerer'}, {'sorcerer_cart', 'sorcerer_cass', 'sorcerer_flop'}, set(), {MediaType.Cartridge: {'bin', 'rom'}, MediaType.Tape: {'wav', 'tape'}, MediaType.Snapshot: {'snp'}, MediaType.Executable: {'bin'}}),
	StandardEmulatedPlatform('Galaksija',{'galaxy', 'galaxyp'}, {'galaxy'}, set(), {MediaType.Snapshot: {'gal'}, MediaType.Tape: {'wav', 'gtp'}}),
	StandardEmulatedPlatform('Goldstar FC-100',{'fc100'}, set(), set(), {MediaType.Cartridge: {'bin'}, MediaType.Tape: {'wav', 'cas'}}), #Some kind of PC-6001 clone or something, apparently
	StandardEmulatedPlatform('Pencil II',{'pencil2'}, {'pencil2'}, set(), {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: {'wav'}}),
	StandardEmulatedPlatform('Instructor 50',{'instruct'}, set(), set(), {MediaType.Tape: {'wav'}, MediaType.Executable: {'pgm'}}),
	StandardEmulatedPlatform('Interact',{'interact', 'hec2hrp'}, {'interact'}, set(), {MediaType.Tape: {'wav', 'k7', 'cin', 'for'}}),
	StandardEmulatedPlatform('Jupiter Ace',{'jupace'}, {'jupace_snap', 'jupace_cass'}, {'MAME (Jupiter Ace)'}, {MediaType.Tape: {'wav', 'tap', 'tzx'}, MediaType.Snapshot: {'ace'}}),
	StandardEmulatedPlatform('KC-85',{'kc85_2'}, {'kc_cart', 'kc_cass', 'kc_flop'}, {'MAME (KC-85)'}, {MediaType.Executable: {'kcc'}, MediaType.Tape: {'wav', 'kcb', 'tap', '853', '854', '855', 'tp2', 'kcm', 'sss'}, MediaType.Cartridge: {'bin'}}), #kcc might also be a tape format?? ehhhh???
	StandardEmulatedPlatform('Luxor ABC80',{'abc80'}, {'abc80_cass', 'abc80_flop'}, set(), {MediaType.Tape: {'wav'}, MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: {'bac'}}), 
	StandardEmulatedPlatform('Mattel Aquarius', {'aquarius'}, {'aquarius_cart', 'aquarius_cass'}, {'MAME (Mattel Aquarius)'}, {MediaType.Cartridge: generic_cart_extensions, MediaType.Tape: {'wav', 'caq'}}), #Software list was just "aquarius" prior to 0.226
	StandardEmulatedPlatform('Orao',{'orao'}, {'orao'}, set(), {MediaType.Tape: {'wav', 'tap'}}),
	StandardEmulatedPlatform('Memotech MTX',{'mtx512'}, {'mtx_cart', 'mtx_cass', 'mtx_rom'}, set(), {MediaType.Snapshot: {'mtx'}, MediaType.Executable: {'run'}, MediaType.Tape: {'wav'}, MediaType.Cartridge: {'bin', 'rom'}}),
	StandardEmulatedPlatform('Microbee',{'mbee'}, set(), {'MAME (Microbee)'}, {MediaType.Tape: {'wav', 'tap'}, MediaType.Floppy: mame_floppy_formats, MediaType.Executable: {'mwb', 'com', 'bee'}}), #Also a second .bin quickload?
	StandardEmulatedPlatform('Microtan 65',{'mt65'}, {'mt65_snap'}, {'MAME (Microtan 65)'}, {MediaType.Tape: {'wav'}, MediaType.Executable: {'hex'}, MediaType.Snapshot: {'dmp', 'm65'}}), #MAME driver was "microtan" prior to 0.212
	StandardEmulatedPlatform('MikroMikko 1',{'mm1m6'}, {'mm1_flop'}, set(), {MediaType.Floppy: mame_floppy_formats}),
	StandardEmulatedPlatform('Mikrosha',{'mikrosha'}, {'mikrosha_cart', 'mikrosha_cass'}, set(), {MediaType.Tape: {'wav', 'rkm'}, MediaType.Cartridge: {'bin', 'rom'}}), #Maybe should just be part of Radio 86?
	StandardEmulatedPlatform('Nascom',{'nascom1', 'nascom2'}, {'nascom_flop', 'nascom_snap', 'nascom_socket'}, set(), {MediaType.Tape: {'wav'}, MediaType.Floppy: mame_floppy_formats, MediaType.Snapshot: {'nas', 'chr'}}),
	StandardEmulatedPlatform('Oric',{'oric1'}, set(), set(), {MediaType.Tape: {'wav', 'tap'}}),
	StandardEmulatedPlatform('Orion-128',{'orion128'}, {'orion_cart', 'orion_cass', 'orion_flop'}, set(), {MediaType.Tape: {'wav', 'rkp'}, MediaType.Floppy: mame_floppy_formats.union({'odi'}), MediaType.Cartridge: {'bin'}}),
	StandardEmulatedPlatform('Panasonic JR-200',{'jr200'}, set(), set()),
	StandardEmulatedPlatform('Pasopia 7',{'pasopia7'}, set(), set(), {MediaType.Tape: {'wav'}, MediaType.Floppy: mame_floppy_formats}),
	StandardEmulatedPlatform('Pasopia 1600',{'paso1600'}, set(), set(), {}),
	StandardEmulatedPlatform('Partner 01.01',{'partner'}, {'partner_cass', 'partner_flop'}, set(), {MediaType.Tape: {'wav', 'rkp'}, MediaType.Floppy: mame_floppy_formats.union({'odi'})}), #Another Radio 86 clone?
	StandardEmulatedPlatform('PipBug',{'pipbug'}, set(), set(), {MediaType.Executable: {'pgm'}}),
	StandardEmulatedPlatform('PMD 85',{'pmd851'}, {'pmd85_cass'}, set(), {MediaType.Tape: {'wav', 'pmd', 'tap', 'ptp'}}),
	StandardEmulatedPlatform('Radio 86-RK',{'radio86'}, {'radio86_cart', 'radio86_cass'}, set(), {MediaType.Tape: {'wav', 'rk', 'rkr', 'gam', 'g16', 'pki'}}),
	StandardEmulatedPlatform('Robotron Z1013',{'z1013'}, set(), set(), {MediaType.Tape: {'wav'}, MediaType.Snapshot: {'z80'}}),
	StandardEmulatedPlatform('Sharp MZ-700',{'mz700'}, {'mz700'}, set(), {MediaType.Tape: {'wav', 'm12', 'mzf', 'mzt'}}),
	StandardEmulatedPlatform('Sharp MZ-800',{'mz800', 'mz1500'}, {'mz800'}, set(), {MediaType.Tape: {'wav', 'm12', 'mzf', 'mzt'}}),
	StandardEmulatedPlatform('Sharp MZ-2000',{'mz2000', 'mz80b'}, {'mz2000_cass', 'mz2000_flop', 'mz2200_cass'}, {'MAME (Sharp MZ-2000)'}, {MediaType.Tape: {'wav', 'm12', 'mzf', 'mzt'}, MediaType.Floppy: {'2d'}.union(mame_floppy_formats)}),
	StandardEmulatedPlatform('Sinclair QL',{'ql', 'tonto'}, {'ql_cart', 'ql_cass', 'ql_flop'}, set(), {MediaType.Tape: {'mdv'}, MediaType.Cartridge: {'bin', 'rom'}, MediaType.Floppy: mame_floppy_formats}),
	StandardEmulatedPlatform('Sony SMC-777',{'smc777'}, {'smc777'}, {'MAME (Sony SMC-777)'}, {MediaType.Floppy: mame_floppy_formats.union({'1dd'}), MediaType.Executable: {'com', 'cpm'}}),
	StandardEmulatedPlatform('Sord M5',{'m5'}, {'m5_cart', 'm5_cass', 'm5_flop'}, {'MAME (Sord M5)'}, {MediaType.Cartridge: {'bin', 'rom'}, MediaType.Floppy: mame_floppy_formats.union({'xdf', 'hdm', '2hd', 'dim'}), MediaType.Tape: {'wav', 'cas'}}),
	StandardEmulatedPlatform('Squale',{'squale'}, {'squale_cart'}, {'MAME (Squale)'}, {MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: {'bin'}}),
	StandardEmulatedPlatform('SVI-3x8',{'svi318', 'svi328'}, {'svi318_cart', 'svi318_cass', 'svi318_flop'}, {'MAME (SVI-3x8)'}, {MediaType.Tape: {'wav', 'cas'}, MediaType.Cartridge: {'bin', 'rom'}, MediaType.Floppy: {'dsk'}}),
	StandardEmulatedPlatform('Tandy MC-10', {'mc10'}, {'mc10'}, set(), {MediaType.Tape: {'wav', 'cas', 'c10'}}),
	StandardEmulatedPlatform('Tatung Einstein', {'einstein', 'einst256'}, {'einstein'}, set(), {MediaType.Floppy: mame_floppy_formats, MediaType.Tape: {'wav'}, MediaType.Executable: {'com'}}),
	StandardEmulatedPlatform('Thomson MO5',{'mo5', 'mo5nr'}, {'mo5_cart', 'mo5_cass', 'mo5_flop', 'mo5_qd'}, {'MAME (Thomson MO5)'}, {MediaType.Tape: {'wav', 'k5', 'k7'}, MediaType.Floppy: {'fd', 'sap', 'qd'}.union(mame_floppy_formats), MediaType.Cartridge: {'m5', 'bin', 'rom'}}, dat_names={'Thomson - MOTO'}),
	StandardEmulatedPlatform('Thomson MO6',{'mo6'}, {'mo6_cass', 'mo6_flop'}, set(), {MediaType.Tape: {'wav', 'k5', 'k7'}, MediaType.Floppy: {'fd', 'sap', 'qd'}.union(mame_floppy_formats), MediaType.Cartridge: {'m5', 'bin', 'rom'}}, dat_names={'Thomson - MOTO'}),
	StandardEmulatedPlatform('Thomson TO',{'to7', 'to770', 'to8', 'to9', 'to9p'}, {'to7_cart', 'to7_cass', 'to7_qd', 'to8_cass', 'to8_qd', 'to770a_cart', 'to770_cart'}, set(), {MediaType.Tape: {'wav', 'k7'}, MediaType.Floppy: {'fd', 'sap', 'qd'}.union(mame_floppy_formats), MediaType.Cartridge: {'m7', 'bin', 'rom'}}, dat_names={'Thomson - MOTO'}),
	StandardEmulatedPlatform('Tiki 100',{'kontiki'}, {'tiki100'}, set(), {MediaType.HardDisk: {'chd', 'hd', 'hdv', 'hdi'}, MediaType.Floppy: mame_floppy_formats, MediaType.Tape: {'wav'}}),
	StandardEmulatedPlatform('Tomy Tutor',{'tutor'}, {'tutor'}, {'MAME (Tomy Tutor)'}, {MediaType.Cartridge: {'bin'}, MediaType.Tape: {'wav'}}),
	StandardEmulatedPlatform('Toshiba Pasopia',{'pasopia'}, {'pasopia_cass'}, set(), {MediaType.Tape: {'wav'}, MediaType.Floppy: mame_floppy_formats}),	#Ow my freaking ears… every tape seems to take a long time to get anywhere
	StandardEmulatedPlatform('Vector-06C',{'vector06'}, {'vector06_cart', 'vector06_flop'}, set(), {MediaType.Tape: {'wav'}, MediaType.Floppy: mame_floppy_formats, MediaType.Cartridge: {'bin', 'emr'}}),
	StandardEmulatedPlatform('VIC-10',{'vic10'}, {'vic10'}, {'MAME (VIC-10)'}, {MediaType.Cartridge: {'crt', 'bin', '80', 'e0'}, MediaType.Tape: {'wav', 'tap', 't64'}, MediaType.Executable: {'prg'}}),
	StandardEmulatedPlatform('Videoton TVC',{'tvc64'}, {'tvc_cart', 'tvc_cass', 'tvc_flop'}, {'MAME (Videoton TVC)'}, {MediaType.Cartridge: {'bin', 'rom', 'crt'}, MediaType.Tape: {'wav', 'cas'}, MediaType.Floppy: {'dsk'}}), #.cas is also quickload? I donut understand
	StandardEmulatedPlatform('VideoBrain',{'vidbrain'}, {'vidbrain'}, {'MAME (VideoBrain)'}, {MediaType.Cartridge: {'bin'}}),
	StandardEmulatedPlatform('VZ-200',{'vz200', 'laser200', 'laser110', 'laser210', 'laser310'}, {'vz_cass', 'vz_snap'}, {'MAME (VZ-200)'}, {MediaType.Snapshot: {'vz'}, MediaType.Tape: {'wav', 'cas'}, MediaType.Floppy: {'dsk'}}), #There are many different systems in this family, but I'll go with this one, because the software list is named after it
	StandardEmulatedPlatform('Zorba',{'zorba'}, {'zorba'}, set(), {MediaType.Floppy: mame_floppy_formats}),

	#Hmm, not quite computers or any particular hardware so much as OSes which probably don't belong here anyway
	StandardEmulatedPlatform('Android',(), set(), set(), {MediaType.Digital: {'apk'}}),
	StandardEmulatedPlatform('PalmOS',(), set(), {'Mu (libretro)'}, {MediaType.Executable: {'prc', 'pqa'}}),

	#Interpreted virtual machine thingy…
	StandardEmulatedPlatform('Chip-8',(), {'chip8_quik'}, set(), {MediaType.Executable: {'bin', 'c8', 'ch8'}}), #Many interpreters available in MAME - Cosmac VIP, Dream 6800, ETI-660, etc; though I'm not sure if it makes sense to put them as the mame_driver for this, but when I get around to that I suppose they would be emulators for it

	#Stuff that isn't actually hardware but we can pretend it is one
	StandardEmulatedPlatform('ChaiLove',(), set(), {'ChaiLove (libretro)'}, {MediaType.Executable: {'chai'}, MediaType.Digital: {'chailove'}}, is_virtual=True, dat_names={'ChaiLove'}),
	StandardEmulatedPlatform('Dinothawr',(), set(), {'Dinothawr (libretro)'}, {MediaType.Executable: {'game'}}, is_virtual=True, dat_names={'Dinothawr'}),
	StandardEmulatedPlatform('Doom',
		set(), set(), {'PrBoom+'}, {MediaType.Digital: {'wad'}}, 
		{'save_dir': PlatformConfigValue(ConfigValueType.FolderPath, None, 'Folder to put save files in')},
		is_virtual=True, dat_names={'DOOM'}
	),
	StandardEmulatedPlatform('Flash',(), set(), {'Ruffle'}, {MediaType.Digital: {'swf'}}, is_virtual=True),
	StandardEmulatedPlatform('J2ME',(), set(), {'FreeJ2ME (libretro)'}, {MediaType.Executable: {'jar'}}, is_virtual=True),
	StandardEmulatedPlatform('LowRes NX',(), set(), {'LowRes NX (libretro)'}, {MediaType.Digital: {'nx'}}, is_virtual=True, dat_names={'LowRes NX'}),
	StandardEmulatedPlatform('Pico-8',(), set(), {'Pico-8'}, {MediaType.Cartridge: {'p8.png'}, MediaType.Executable: {'p8'}}, is_virtual=True),
)}

#For Machine.is_system_driver to work correctly
ibmpc_drivers = {'ibm5150', 'ibm5170', 'pcipc', 'pcipctx', 'nforcepc'}
mac_drivers = {'mac128k', 'macplus', 'macse', 'macsefd', 'macclasc', 'macii', 'mac2fdhd', 'macprtb', 'maciici', 'maciifx', 'maclc', 'maciisi', 'macpb100', 'macpb140', 'macclas2', 'maclc2', 'macpb160', 'macpd210', 'maccclas', 'maclc3', 'maciivx', 'maclc520', 'pmac6100', 'macqd700'}

all_mame_drivers = {d for s in platforms.values() for d in s.mame_drivers}
all_mame_drivers.update(ibmpc_drivers)
all_mame_drivers.update(mac_drivers)

#Things where I can't be fucked right now making a SystemInfo object:
#Altair 8800 (is 8800bt a different thing)
#TIC-80 (one of those non-existent systems) (Libretro dat: "TIC-80")
#TRS-80 Model 2 (trs80m2)
#TRS-80 MC-10 (mc10)
#Hitachi S1
#Virtual systems: TADS, Z-Machine, Adobe AIR
#Acorn System (acrnsys3, acrnsys5)
#Amstrad PC1512 (pc1512, pc1640)
#Indy (indy_4610, indigo2_4415)
#SSEM

#Confusing things:
#Which of TI calculators are software compatible with which (and hence which ones would be considered individual systems)?
	#TI-73, 81, 82, 83x, 84x, 85, 86 are Z80; 89, 92x are M68K
#Bandai Super Note Club (snotec, snotecu, snotecex): Part of VTech Genius Leader (supports glccolor software list), or its own thing (has snotec software list)?
#Amstrad PC20/Sinclair PC200: Is this just IBM PC compatible stuff? Have seen one demoscene prod which claims to be for it specifically
#Epoch (not Super) Cassette Vision isn't even in MAME, looks like all the circuitry is in the cartridges?
#DEC Rainbow: Uses DOS so maybe goes in pc_systems but maybe the CP/M part is its own thing

manually_specified_platforms = {
	'Mac': ManuallySpecifiedPlatform('Mac', 'mac', {'BasiliskII', 'SheepShaver'}),
	'DOS': ManuallySpecifiedPlatform('DOS', 'dos', {'DOSBox Staging', 'DOSBox-X'}, {
		'use_directory_as_fallback_name': PlatformConfigValue(ConfigValueType.Bool, False, 'Use base directory name for fallback name if you don\'t feel like providing a name in dos.json')
	}),
}
