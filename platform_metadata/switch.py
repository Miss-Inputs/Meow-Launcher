try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import io
from xml.etree import ElementTree

from config.main_config import main_config

class NotPFS0Exception(Exception):
	pass

def add_nacp_metadata(metadata, nacp):
	#There are a heckload of different flags here so just see https://switchbrew.org/wiki/NACP_Format
	#TODO Instead of just getting American English, get the first one which is filled (or first supported?)
	#print(game.rom.path, 'ISBN', nacp[0x3000:0x3025]) Is this filled in on retail games? That could be interesting
	#TODO 0x302c:0x3030 SupportedLanguages - See also https://gbatemp.net/threads/bigbluebox-says-all-the-other-nsps-are-wrong.515145/page-10
	#0x3040:0x3060 RatingAge - I wonder if this is the same format as the previous consoles (but this probably won't mean anything until we get NACPs from non-homebrew games)
	try:
		metadata.add_alternate_name(nacp[0:0x200].decode('utf-8').rstrip(), 'Banner-Title')
	except UnicodeDecodeError:
		pass
	try:
		metadata.publisher = nacp[0x200:0x300].decode('utf-8').rstrip()
	except UnicodeDecodeError:
		pass

def add_cnmt_xml_metadata(xml, metadata):
	metadata.specific_info['Title-Type'] = xml.findtext('Type')
	title_id = xml.findtext('Id')
	if title_id:
		metadata.specific_info['Title-ID'] = title_id[2:]
	metadata.specific_info['Version'] = xml.findtext('Version')
	#We also have RequiredDownloadSystemVersion, Digest, KeyGenerationMin, RequiredSystemVersion, PatchId if those are interesting/useful
	#Content contains Size, KeyGeneration, Hash, Type

def add_nsp_metadata(rom, metadata):
	#Decrypting NCAs is hard, let's go shopping
	#Sometimes there is an xml there though so we can read that and it's not encrypted
	header = rom.read(amount=16)
	if header[:4] != b'PFS0':
		raise NotPFS0Exception(header[:4])
	number_of_files = int.from_bytes(header[4:8], 'little')
	size_of_string_table = int.from_bytes(header[8:12], 'little')

	file_entry_table_size = 24 * number_of_files
	file_entry_table = rom.read(seek_to=16, amount=file_entry_table_size)
	string_table = rom.read(seek_to=16 + file_entry_table_size, amount=size_of_string_table)
	data_offset = 16 + file_entry_table_size + size_of_string_table

	files = {}

	for i in range(number_of_files):
		entry = file_entry_table[0x18 * i: 0x18 * i + 0x18]
		string_table_offset = int.from_bytes(entry[0x10:0x14], 'little')
		name = string_table[string_table_offset:]
		if b'\x00' in name:
			name = name[:name.index(b'\x00')]
		offset = int.from_bytes(entry[0:8], 'little')
		size = int.from_bytes(entry[8:16], 'little')
		files[name.decode('utf-8', errors='backslashreplace')] = (offset + data_offset, size)

	for filename, offsetsize in files.items():
		if filename.endswith('.cnmt.xml'):
			xml_data = rom.read(seek_to=offsetsize[0], amount=offsetsize[1])
			try:
				xml = ElementTree.fromstring(xml_data.decode('utf-8'))
			except UnicodeDecodeError:
				continue
			add_cnmt_xml_metadata(xml, metadata)
			
def add_nro_metadata(rom, metadata):
	header = rom.read(amount=0x50, seek_to=16)
	if header[:4] != b'NRO0':
		#Invalid magic
		return
	#Ox4:0x8 - NRO format version
	nro_size = int.from_bytes(header[8:12], 'little')
	#0x30:0x50 - Build ID
	asset_header = rom.read(nro_size, 0x38)
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
		icon = rom.read(seek_to=nro_size + icon_offset, amount=icon_size)
		icon_io = io.BytesIO(icon)
		metadata.images['Icon'] = Image.open(icon_io)
	if nacp_size > 0:
		nacp = rom.read(seek_to=nro_size + nacp_offset, amount=nacp_size)
		add_nacp_metadata(metadata, nacp)

def add_switch_metadata(game):
	if game.rom.extension == 'nro':
		add_nro_metadata(game.rom, game.metadata)
	if game.rom.extension == 'nsp':
		try:
			add_nsp_metadata(game.rom, game.metadata)
		except NotPFS0Exception:
			if main_config.debug:
				print(game.rom.path, 'has .nsp extension but no PFS0')
