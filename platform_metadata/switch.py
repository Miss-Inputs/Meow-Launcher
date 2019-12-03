try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import io

def add_nacp_metadata(game, nacp):
	#There are a heckload of different flags here so just see https://switchbrew.org/wiki/NACP_Format
	#TODO Instead of just getting American English, get the first one which is filled (or first supported?)
	#print(game.rom.path, 'ISBN', nacp[0x3000:0x3025]) Is this filled in on retail games? That could be interesting
	#TODO 0x302c:0x3030 SupportedLanguages - See also https://gbatemp.net/threads/bigbluebox-says-all-the-other-nsps-are-wrong.515145/page-10
	#0x3040:0x3060 RatingAge - I wonder if this is the same format as the previous consoles (but this probably won't mean anything until we get NACPs from non-homebrew games)
	try:
		game.metadata.specific_info['Banner-Title'] = nacp[0:0x200].decode('utf-8').rstrip()
	except UnicodeDecodeError:
		pass
	try:
		game.metadata.publisher = nacp[0x200:0x300].decode('utf-8').rstrip()
	except UnicodeDecodeError:
		pass

def add_nro_metadata(game):
	header = game.rom.read(amount=0x50, seek_to=16)
	if header[:4] != b'NRO0':
		#Invalid magic
		return
	#Ox4:0x8 - NRO format version
	nro_size = int.from_bytes(header[8:12], 'little')
	#0x30:0x50 - Build ID
	asset_header = game.rom.read(nro_size, 0x38)
	if asset_header[:4] != b'ASET':
		#Might only be a homebrew thing?
		return
	#Asset section version: 0
	icon_offset = int.from_bytes(asset_header[8:16], 'little')
	icon_size = int.from_bytes(asset_header[16:24], 'little')
	nacp_offset = int.from_bytes(asset_header[24:32], 'little')
	nacp_size = int.from_bytes(asset_header[32:40], 'little')
	#RomFS offset/size: 40:48, 48:56
	if icon_size > 0:
		#256x256 JPEG
		icon = game.rom.read(seek_to=nro_size + icon_offset, amount=icon_size)
		icon_io = io.BytesIO(icon)
		game.metadata.images['Icon'] = Image.open(icon_io)
	if nacp_size > 0:
		nacp = game.rom.read(seek_to=nro_size + nacp_offset, amount=nacp_size)
		add_nacp_metadata(game, nacp)

def add_switch_metadata(game):
	if game.rom.extension == 'nro':
		add_nro_metadata(game)
