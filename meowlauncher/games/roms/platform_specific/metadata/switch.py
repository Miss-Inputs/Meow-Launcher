try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

import hashlib
import io
import os
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from enum import Enum, Flag
from shutil import rmtree
from typing import NamedTuple, Optional, cast
from xml.etree import ElementTree

from meowlauncher.common_types import SaveType
from meowlauncher.config.main_config import main_config
from meowlauncher.games.roms.rom import FileROM
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.metadata import Metadata
from meowlauncher.platform_types import SwitchContentMetaType
from meowlauncher.util.region_info import get_language_by_english_name

from .wii import parse_ratings


class InvalidHFS0Exception(Exception):
	pass

class InvalidPFS0Exception(Exception):
	pass

class InvalidXCIException(Exception):
	pass

class InvalidNCAException(Exception):
	pass

class ExternalToolNotHappeningException(Exception):
	pass

game_card_size = {
	0xfa: '1GB',
	0xf8: '2GB',
	0xf0: '4GB',
	0xe0: '8GB',
	0xe1: '16GB',
	0xe2: '32GB',
}

class GamecardFlags(Flag):
	AutoBoot = 1
	HistoryErase = 2
	RepairTool = 4
	DifferentRegionCupToTerraDevice = 8
	DifferentRegionCupToGlobalDevice = 16

class ContentType(Enum):
	Meta = 0
	Program = 1
	Data = 2
	Control = 3
	HtmlDocument = 4
	LegalInformation = 5
	DeltaFragment = 6

nacp_languages = {
	#The names and their CamelCase formatting here aren't arbitrary, they're referred to in the icon files that way
	0: 'AmericanEnglish',
	1: 'BritishEnglish',
	2: 'Japanese',
	3: 'French',
	4: 'German',
	5: 'LatinAmericanSpanish',
	6: 'Spanish',
	7: 'Italian',
	8: 'Dutch',
	9: 'CanadianFrench',
	10: 'Portugese',
	11: 'Russian',
	12: 'Korean',
	13: 'TraditionalChinese',
	14: 'SimplifiedChinese',
	#There's space for #15 here (BrazilianPortugese?) but that never seems to be used
}

class Cnmt(NamedTuple):
	title_id: str
	version: int
	type: SwitchContentMetaType
	contents: dict[bytes, tuple[int, ContentType]]

def add_titles(metadata: Metadata, titles: Mapping[str, tuple[str, str]], icons: Mapping[str, bytes]=None):
	if not titles:
		return
	found_first_lang = False
	first_name = None
	first_publisher = None
	first_icon = None
	for i in range(15):
		#Just because it's naughty to enumerate dictionaries and expect an order, and we want to find the first supported language in that order and call that the "main" one
		#There's not really a region code to use otherwise
		lang_name = nacp_languages[i]
		if lang_name in titles:
			name, publisher = titles[lang_name]

			prefix = None
			if found_first_lang:
				#Do some shenanigans to make things look nice
				prefix = lang_name
				if i == 0:
					prefix = 'American-English' if 'BritishEnglish' in titles else 'English'
				if i == 1:
					prefix = 'British-English' if 'AmericanEnglish' in titles else 'English'
				#I really should just do a regex to convert camel case I guess…
				if i == 5:
					prefix = 'Latin-American-Spanish'
				if i == 9:
					prefix = 'Canadian-French'
				if i == 13:
					prefix = 'Traditional-Chinese'
				if i == 14:
					prefix = 'Chinese'

				if icons and lang_name in icons:
					local_icon = icons[lang_name]
					if local_icon != first_icon:
						metadata.images[prefix + '-Icon'] = Image.open(io.BytesIO(local_icon))
				if name != first_name:
					metadata.add_alternate_name(name, prefix + '-Banner-Title')
				if publisher != first_publisher:
					metadata.specific_info[prefix + '-Publisher'] = publisher
			else:
				first_name = name
				first_publisher = publisher
				found_first_lang = True
				if icons and lang_name in icons:
					first_icon = icons[lang_name]
					metadata.images['Icon'] = Image.open(io.BytesIO(first_icon))
				metadata.add_alternate_name(name, 'Banner-Title')
				#TODO: Cleanup publisher
				metadata.publisher = publisher

def add_nacp_metadata(metadata: Metadata, nacp: bytes, icons: Mapping[str, bytes]=None):
	#There are a heckload of different flags here and most aren't even known seemingly, see also https://switchbrew.org/wiki/NACP_Format
	
	title_entries = nacp[:0x3000]
	titles = {}
	for i, lang_name in nacp_languages.items():
		entry = title_entries[i * 0x300: (i * 0x300) + 0x300]
		if not any(entry):
			continue
		name = entry[:0x200].decode('utf-8', errors='ignore').rstrip('\0')
		publisher = entry[0x200:].decode('utf-8', errors='ignore').rstrip('\0')
		titles[lang_name] = name, publisher
	add_titles(metadata, titles, icons)

	isbn = nacp[0x3000:0x3025]
	if any(isbn):
		#Aww why isn't this ever filled in
		metadata.specific_info['ISBN'] = isbn

	supported_language_flag = int.from_bytes(nacp[0x302c:0x3030], 'little') #This might line up with nacp_languages	
	supported_languages = set()
	for k, v in nacp_languages.items():
		if supported_language_flag & (1 << k):
			if v in {'AmericanEnglish', 'BritishEnglish'}:
				#I want to avoid saying one language is the True English but at the same time it makes things a lot more complicated if I don't have a language in the list that just says English
				supported_languages.add(get_language_by_english_name('English'))
			elif v == 'LatinAmericanSpanish':
				supported_languages.add(get_language_by_english_name('Latin American Spanish'))
			elif v == 'CanadianFrench':
				supported_languages.add(get_language_by_english_name('Canadian French'))
			elif v == 'TraditionalChinese':
				supported_languages.add(get_language_by_english_name('Traditional Chinese'))
			elif v == 'SimplifiedChinese':
				supported_languages.add(get_language_by_english_name('Chinese'))
			else:
				supported_language = get_language_by_english_name(v)
				if v:
					supported_languages.add(supported_language)
	metadata.languages = list(supported_languages)

	#Screenshot = nacp[0x3034] sounds interesting?
	metadata.specific_info['Video-Capture-Allowed'] = nacp[0x3035] != 0 #2 (instead of 1) indicates memory is allocated automatically who cares

	rating_age = nacp[0x3040:0x3060]
	parse_ratings(metadata, rating_age)
	
	metadata.specific_info['Version'] = nacp[0x3060:0x3070].decode('utf-8', errors='ignore').rstrip('\0')

	user_account_save_size = int.from_bytes(nacp[0x3080:0x3088], 'little')
	device_save_size = int.from_bytes(nacp[0x3090:0x3098], 'little')
	metadata.save_type = SaveType.Internal if user_account_save_size or device_save_size else SaveType.Nothing

	application_error_code_category = nacp[0x30a8:0x30b0]
	if any(application_error_code_category):
		#For some reason this is sometimes here and the product code when it is (which doesn't seem to be anywhere else)
		metadata.product_code = application_error_code_category.decode('utf-8', errors='ignore')
		#TODO: Use switchtdb.xml although it won't be as useful when it uses the product code which we can only have sometimes

def add_cnmt_xml_metadata(xml: ElementTree.Element, metadata: Metadata):
	metadata.specific_info['Title-Type'] = xml.findtext('Type')
	title_id = xml.findtext('Id')
	if title_id:
		metadata.specific_info['Title-ID'] = title_id[2:]
	metadata.specific_info['Revision'] = xml.findtext('Version')
	#We also have RequiredDownloadSystemVersion, Digest, KeyGenerationMin, RequiredSystemVersion, PatchId if those are interesting/useful
	#Content contains Size, KeyGeneration, Hash, Type

def decrypt_control_nca_with_hactool(control_nca: bytes) -> dict[str, bytes]:
	if hasattr(decrypt_control_nca_with_hactool, 'failed'):
		raise ExternalToolNotHappeningException('No can do {0}'.format(decrypt_control_nca_with_hactool.failed)) #type: ignore[attr-defined]
	temp_folder = None
	try:
		#Ugly code time
		temp_folder = tempfile.mkdtemp()
		#If we could get it to read /dev/stdin that'd be great, but it seems to not terribly want to do that, so we'll have to write that to a file too… grrr
		handle, temp_filename = tempfile.mkstemp(dir=temp_folder)
		os.write(handle, control_nca)

		try:
			hactool = subprocess.run(['hactool', '-x', temp_filename, '--disablekeywarns', '--romfsdir', temp_folder], stdout=subprocess.DEVNULL, check=True, stderr=subprocess.PIPE)
			#If we could get the paths it outputs that'd be great, but it prints a bunch of junk to stdout
			stderr = hactool.stderr.strip()
			if stderr.decode('utf-8', errors='ignore') == 'Invalid NCA header! Are keys correct?':
				raise InvalidNCAException('Header wrong')
		except (subprocess.CalledProcessError, FileNotFoundError) as cactus:
			try:
				#Plan B, there is no reason why this can't be plan A I guess
				nstool = subprocess.run(['nstool', '-t', 'nca', '--part0', temp_folder, temp_filename], stdout=subprocess.PIPE, check=True, stderr=subprocess.DEVNULL)
				stdout = nstool.stdout.strip() #It prints error messages to stdout…
				if stdout.decode('utf-8', errors='ignore') == '[NcaProcess ERROR] NCA FS Header [':
					#I guess that's the error message
					raise InvalidNCAException('Header wrong')
			except (subprocess.CalledProcessError, FileNotFoundError):
				decrypt_control_nca_with_hactool.failed = cactus #type: ignore[attr-defined]
				raise ExternalToolNotHappeningException('No can do') from cactus

		files = {}
		for f in os.scandir(temp_folder):
			if f.is_file() and f.path != temp_filename:
				with open(f.path, 'rb') as ff:
					files[f.name] = ff.read()
		return files
	finally:
		if temp_folder:
			rmtree(temp_folder)

def decrypt_cnmt_nca_with_hactool(cnmt_nca: bytes) -> bytes:
	#Decrypting NCAs is hard, let's go shopping (and get an external tool to do it)
	if hasattr(decrypt_cnmt_nca_with_hactool, 'failed'):
		raise ExternalToolNotHappeningException('No can do {0}'.format(decrypt_cnmt_nca_with_hactool.failed)) #type: ignore[attr-defined]
	temp_folder = None
	try:
		#Ugly code time
		temp_folder = tempfile.mkdtemp()
		#If we could get it to read /dev/stdin that'd be great, but it seems to not terribly want to do that, so we'll have to write that to a file too… grrr
		handle, temp_filename = tempfile.mkstemp(dir=temp_folder)
		os.write(handle, cnmt_nca)

		try:
			#Since we're going through hactool anyway, might as well get it to find our actual cnmt for us so we don't have to parse the nca
			hactool = subprocess.run(['hactool', '-t', 'nca', '-x', temp_filename, '--disablekeywarns', '--section0dir', temp_folder], stdout=subprocess.DEVNULL, check=True, stderr=subprocess.PIPE)
			#If we could get the paths it outputs that'd be great, but it prints a bunch of junk to stdout
			stderr = hactool.stderr.strip()
			if stderr.decode('utf-8', errors='ignore') == 'Invalid NCA header! Are keys correct?':
				raise InvalidNCAException('Header wrong')
		except (subprocess.CalledProcessError, FileNotFoundError) as cactus:
			try:
				#Plan B
				nstool = subprocess.run(['nstool', '-t', 'nca', '--part0', temp_folder, temp_filename], stdout=subprocess.PIPE, check=True, stderr=subprocess.DEVNULL)
				stdout = nstool.stdout.strip() #It prints error messages to stdout…
				if stdout.decode('utf-8', errors='ignore') == '[NcaProcess ERROR] NCA FS Header [':
					#I guess that's the error message
					raise InvalidNCAException('Header wrong')
			except (subprocess.CalledProcessError, FileNotFoundError):
				decrypt_cnmt_nca_with_hactool.failed = cactus #type: ignore[attr-defined]
				raise ExternalToolNotHappeningException('No can do') from cactus

		for f in os.scandir(temp_folder):
			if f.name.endswith('.cnmt') and f.is_file():
				with open(f.path, 'rb') as ff:
					return ff.read()
		raise AssertionError('This should not happen')
	finally:
		if temp_folder:
			rmtree(temp_folder)

def list_cnmt(cnmt: Cnmt, rom: FileROM, metadata: Metadata, files: Mapping[str, tuple[int, int]], extra_offset: int=0):
	metadata.specific_info['Title-ID'] = cnmt.title_id
	metadata.specific_info['Revision'] = cnmt.version
	metadata.specific_info['Title-Type'] = cnmt.type
	for k, v in cnmt.contents.items():
		if v[1] == ContentType.Control:
			control_nca_filename = bytes.hex(k) + '.nca'
			control_nca_offset, control_nca_size = files[control_nca_filename]
			control_nca = rom.read(seek_to=control_nca_offset + extra_offset, amount=control_nca_size)
			try:
				control_nca_files = decrypt_control_nca_with_hactool(control_nca)
				#We have icons and a NACP! WOOOOO
				#The icons match up with the titles that exist in the titles section, not SupportedLanguageFlag
				icons = {}
				nacp = None
				for control_nca_filename, control_nca_file in control_nca_files.items():
					if not nacp and control_nca_filename == 'control.nacp':
						#We would expect only one
						nacp = control_nca_file
					elif have_pillow and control_nca_filename.startswith('icon_') and control_nca_filename.endswith('.dat'):
						icons[control_nca_filename.removeprefix('icon_').removesuffix('.dat')] = control_nca_file
				if nacp:
					add_nacp_metadata(metadata, nacp, icons)
				elif main_config.debug:
					print('Hmm no control.nacp in', rom.path)
			except InvalidNCAException:
				if main_config.debug:
					print('Unfortunate, invalid cnmt NCA in', rom.path)
			except ExternalToolNotHappeningException:
				pass
			break
		#ContentMetaType.AddOnContent seems to generally not have control data, only a single ContentType.Data

def list_cnmt_nca(data: bytes) -> Cnmt:
	# 0x12	0x2	Content Meta Count #Whazzat do
	# 0x14	0x1	Content Meta Attributes (0=None, 1=IncludesExFatDriver, 2=Rebootless) #Dunno what that does either
	# 0x18	0x4	Required Download System Version

	cnmt = decrypt_cnmt_nca_with_hactool(data)
	
	title_id = bytes.hex(cnmt[0:8][::-1]) #Not sure why this is backwards but it be like that
	version = int.from_bytes(cnmt[8:12], 'little')
	content_meta_type = SwitchContentMetaType(cnmt[12])
	extended_header_size = int.from_bytes(cnmt[14:16], 'little')
	content_count = int.from_bytes(cnmt[16:18], 'little')
	
	content_start = 32 + extended_header_size
	content_record_size = 56
	contents = {}
	for i in range(content_count):
		content_offset = content_start + (i * content_record_size)
		content = cnmt[content_offset: content_offset + content_record_size]
		content_id = content[32:48]
		content_size = int.from_bytes(content[48:54], 'little')
		content_type = ContentType(content[54])
		contents[content_id] = (content_size, content_type)
	return Cnmt(title_id, version, content_meta_type, contents)

def list_psf0(rom: FileROM) -> dict[str, tuple[int, int]]:
	header = rom.read(amount=16)
	magic = header[:4]
	if magic != b'PFS0':
		raise InvalidPFS0Exception(repr(magic))
	number_of_files = int.from_bytes(header[4:8], 'little')
	size_of_string_table = int.from_bytes(header[8:12], 'little')

	file_entry_table_size = 24 * number_of_files
	file_entry_table = rom.read(seek_to=16, amount=file_entry_table_size)
	if len(file_entry_table) != file_entry_table_size:
		raise InvalidPFS0Exception('Something went wrong, file_entry_table is wrong size')

	string_table = rom.read(seek_to=16 + file_entry_table_size, amount=size_of_string_table)
	data_offset = 16 + file_entry_table_size + size_of_string_table
	if len(string_table) != size_of_string_table:
		raise InvalidPFS0Exception('Something went wrong, string_table is wrong size')

	files = {}

	for i in range(number_of_files):
		entry = file_entry_table[24 * i: (24 * i) + 24]
		string_table_offset = int.from_bytes(entry[0x10:0x14], 'little')
		name = string_table[string_table_offset:]
		if b'\0' in name:
			name = name[:name.index(b'\0')]
		offset = int.from_bytes(entry[0:8], 'little')
		size = int.from_bytes(entry[8:16], 'little')
		files[name.decode('utf-8', errors='backslashreplace')] = (offset + data_offset, size)
	return files

def choose_main_cnmt(cnmts: Sequence[Cnmt]) -> Optional[Cnmt]:
	if not cnmts:
		return None
	if len(cnmts) == 1:
		return cnmts[0]
	#elif len(cnmts) > 1:
	#Sometimes you can have more than one if the cartridge includes an embedded patch
	application_cnmts = [c for c in cnmts if c.type == SwitchContentMetaType.Application]
	if len(application_cnmts) == 1:
		return application_cnmts[0]

	#Uh oh that didn't help, oh no what do we do I guess let's just take the first one
	return cnmts[0]

def add_nsp_metadata(rom: FileROM, metadata: Metadata):
	files = list_psf0(rom)
	cnmts = []
	cnmt_xml = None
	try_fallback_to_xml = False

	for filename, offsetsize in files.items():
		if filename.endswith('.cnmt.nca'):
			cnmt_nca = rom.read(amount=offsetsize[1], seek_to=offsetsize[0])
			try:
				cnmts.append(list_cnmt_nca(cnmt_nca))
			except InvalidNCAException:
				#if main_config.debug:
				#	print(filename, 'is an invalid cnmt.nca in', rom.path, ex)
				continue
			except ExternalToolNotHappeningException:
				try_fallback_to_xml = True
				break
		if filename.endswith('.cnmt.xml'):
			#I think the dumping tool for NSPs is actually what puts these here, but if we need a fallback, this will do
			cnmt_xml_data = rom.read(amount=offsetsize[1], seek_to=offsetsize[0])
			try:
				cnmt_xml = ElementTree.fromstring(cnmt_xml_data.decode('utf-8'))
			except UnicodeDecodeError:
				continue

	if try_fallback_to_xml and cnmt_xml is not None:
		#We could look at the list of contents in there, but there's not much point seeing as how we'd need to decrypt the content NCA anyway
		add_cnmt_xml_metadata(cnmt_xml, metadata)

	main_cnmt = choose_main_cnmt(cnmts)
	if main_cnmt:
		list_cnmt(main_cnmt, rom, metadata, files)
	#else:
	#	if main_config.debug:
	#		print('Uh oh no cnmt.nca in', rom.path, '?')

def read_hfs0(rom: FileROM, offset: int, max_size: int=None) -> dict[str, tuple[int, int]]:
	header = rom.read(offset, 16)

	magic = header[:4]
	if magic != b'HFS0':
		raise InvalidHFS0Exception('Invalid magic, expected HFS0 but got {0!r} at offset {1:x}'.format(magic, offset))

	number_of_files = int.from_bytes(header[4:8], 'little')
	string_table_size = int.from_bytes(header[8:12], 'little')
	
	file_entry_table_size = 64 * number_of_files
	file_entry_table = rom.read(16 + offset, file_entry_table_size)
	if len(file_entry_table) != file_entry_table_size:
		raise InvalidHFS0Exception('Something went wrong with file entry table, too small')
	
	string_table = rom.read(16 + file_entry_table_size + offset, string_table_size)
	if len(string_table) != string_table_size:
		raise InvalidHFS0Exception('Something went wrong with string table, too small')
	
	files = {}

	total_size = 16 + file_entry_table_size + string_table_size #Keep track of how big this HFS0 claims to be…
	#data_offset = total_size
	#real_data_offset = data_offset + offset

	for i in range(0, number_of_files):
		entry = file_entry_table[64 * i: (64 * i) + 64]

		file_offset = int.from_bytes(entry[0:8], 'little') # + data_offset #Offset into this HFS0
		if max_size and file_offset > max_size:
			raise InvalidHFS0Exception('Exceeded max_size! File offset is further off and therefore wrong')
		real_file_offset = file_offset + offset #Offset into the actual file, for seeking to

		size = int.from_bytes(entry[8:16], 'little')
		total_size += size
		if max_size and total_size > max_size:
			raise InvalidHFS0Exception('Exceeded max_size! File sizes are too big and therefore wrong total_size = {0} max_size = {1}'.format(total_size, max_size))
		
		offset_into_string_table = int.from_bytes(entry[16:20], 'little')
		
		name = string_table[offset_into_string_table:]
		if b'\0' in name:
			name = name[:name.index(b'\0')]

		hashed_region_size = int.from_bytes(entry[20:24], 'little')
		real_file_offset += hashed_region_size

		files[name.decode('utf-8', errors='ignore')] = (real_file_offset, size)

	return files

def add_xci_metadata(rom: FileROM, metadata: Metadata):
	header = rom.read(amount=0x200)
	magic = header[0x100:0x104]
	if magic != b'HEAD':
		raise InvalidXCIException('Not a XCI: {0!r}'.format(magic))

	metadata.specific_info['Gamecard-Size'] = game_card_size.get(header[0x10d], 'unknown 0x{0:x}'.format(header[0x10d]))
	flags = header[0x10f]
	if flags != 0:
		metadata.specific_info['Gamecard-Flags'] = GamecardFlags(flags)
	root_partition_offset = int.from_bytes(header[0x130:0x138], 'little') #Always 0xf000 innit? But just to be sure
	root_partition_header_size = int.from_bytes(header[0x138:0x140], 'little') #But that will always be 512
	root_partition_header_expected_hash = header[0x140:0x160]
	root_partition_header = rom.read(root_partition_offset, root_partition_header_size)
	if hashlib.sha256(root_partition_header).digest() != root_partition_header_expected_hash:
		raise InvalidXCIException('HFS0 hash in XCI header did not match')

	root_partition = read_hfs0(rom, root_partition_offset)
	if 'secure' in root_partition:
		#This one is always here and not sometimes empty like normal is, and also the cnmt is encrypted anyway, so whaddya do
		secure_offset, secure_size = root_partition['secure']
		#I've been nae naed
		real_secure_offset = int.from_bytes(header[0x104:0x108], 'little') * 0x200
		secure_offset_diff = secure_offset - real_secure_offset
		secure_files = read_hfs0(rom, real_secure_offset, secure_size)

		cnmts = []
		for k, v in secure_files.items():
			if k.endswith('.cnmt.nca'):
				cnmt = rom.read(v[0] + secure_offset_diff, v[1]) #I've been double nae naed
				try:
					cnmts.append(list_cnmt_nca(cnmt))
				#except ValueError as v:
				#	print('Bugger bugger bugger', v)
				except InvalidNCAException:
					#print(k, 'is an invalid cnmt.nca', ex)
					continue
				except ExternalToolNotHappeningException:
					#print(ex)
					return

		main_cnmt = choose_main_cnmt(cnmts)
		if main_cnmt:
			list_cnmt(main_cnmt, rom, metadata, secure_files, secure_offset_diff)
		#else:
		#	print('Uh oh no cnmt.nca?')

def add_nro_metadata(rom: FileROM, metadata: Metadata):
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

def add_switch_metadata(game: ROMGame):
	if game.rom.extension == 'nro':
		add_nro_metadata(cast(FileROM, game.rom), game.metadata)
	if game.rom.extension == 'xci':
		try:
			add_xci_metadata(cast(FileROM, game.rom), game.metadata)
		except InvalidXCIException as ex:
			if main_config.debug:
				print(game.rom.path, 'was invalid XCI: {0}'.format(ex))
		except InvalidHFS0Exception as ex:
			if main_config.debug:
				print(game.rom.path, 'had invalid HFS0: {0}'.format(ex))

	if game.rom.extension == 'nsp':
		try:
			add_nsp_metadata(cast(FileROM, game.rom), game.metadata)
		except InvalidPFS0Exception as ex:
			if main_config.debug:
				print(game.rom.path, 'was invalid PFS0: {0}'.format(ex))
