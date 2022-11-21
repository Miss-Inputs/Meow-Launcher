import hashlib
import io
import logging
import subprocess
import tempfile
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from enum import Enum, Flag
from pathlib import Path, PurePath
from typing import TYPE_CHECKING
from xml.etree import ElementTree

try:
	from PIL import Image
	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.common_types import ByteAmount, SaveType
from meowlauncher.platform_types import SwitchContentMetaType
from meowlauncher.util.region_info import (get_language_by_english_name,
                                           languages_by_english_name)

from .common.nintendo_common import NintendoAgeRatings, add_ratings_info

if TYPE_CHECKING:
	from meowlauncher.games.roms.rom import FileROM
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

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
	0xfa: ByteAmount(1024 * 1024 * 1024),
	0xf8: ByteAmount(2 * 1024 * 1024 * 1024),
	0xf0: ByteAmount(4 * 1024 * 1024 * 1024),
	0xe0: ByteAmount(8 * 1024 * 1024 * 1024),
	0xe1: ByteAmount(16 * 1024 * 1024 * 1024),
	0xe2: ByteAmount(32 * 1024 * 1024 * 1024),
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
	10: 'Portuguese',
	11: 'Russian',
	12: 'Korean',
	13: 'TraditionalChinese',
	14: 'SimplifiedChinese',
	#There's space for #15 here (BrazilianPortuguese?) but that never seems to be used
}

@dataclass(frozen=True)
class Cnmt():
	title_id: str
	version: int
	type: SwitchContentMetaType
	contents: dict[bytes, tuple[int, ContentType]] = field(compare=False)

def _add_titles(game_info: 'GameInfo', titles: Mapping[str, tuple[str, str]], icons: Mapping[str, bytes] | None=None) -> None:
	if not titles:
		return
	found_first_lang = False
	first_name = None
	first_publisher = None
	first_icon = None
	other_icons: dict[str, bytes] = {}
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
					prefix = 'English (American)'
				if i == 1:
					prefix = 'English (British)'
				#I really should just do a regex to convert camel case I guess…
				if i == 5:
					prefix = 'Spanish (Latin American)'
				if i == 9:
					prefix = 'French (Canadian)'
				if i == 13:
					prefix = 'Chinese (Traditional)'
				if i == 14:
					prefix = 'Chinese (Simplified)'

				if icons and lang_name in icons:
					local_icon = icons[lang_name]
					if local_icon != first_icon and local_icon not in other_icons.values():
						other_icons[prefix] = local_icon
				if name != first_name:
					game_info.add_alternate_name(name, prefix + ' Banner Title')
				if publisher != first_publisher:
					game_info.specific_info[prefix + ' Publisher'] = publisher
			else:
				first_name = name
				first_publisher = publisher
				found_first_lang = True
				if icons and lang_name in icons:
					first_icon = icons[lang_name]
					game_info.images['Icon'] = Image.open(io.BytesIO(first_icon))
				game_info.add_alternate_name(name, 'Banner Title')
				#TODO: Cleanup publisher
				game_info.publisher = publisher
	for prefix, icon in other_icons.items():
		game_info.images[prefix + ' Icon'] = Image.open(io.BytesIO(icon))

def _add_nacp_metadata(metadata: 'GameInfo', nacp: bytes, icons: 'Mapping[str, bytes] | None'=None) -> None:
	#There are a heckload of different flags here and most aren't even known seemingly, see also https://switchbrew.org/wiki/NACP_Format
	
	title_entries = nacp[:0x3000]
	titles = {}
	for i, lang_name in nacp_languages.items():
		entry = title_entries[i * 0x300: (i * 0x300) + 0x300]
		if not any(entry):
			continue
		name = entry[:0x200].rstrip(b'\0').decode('utf-8', 'backslashreplace')
		publisher = entry[0x200:].rstrip(b'\0').decode('utf-8', 'backslashreplace')
		titles[lang_name] = name, publisher
	_add_titles(metadata, titles, icons)

	isbn = nacp[0x3000:0x3025]
	if any(isbn):
		#Aww why isn't this ever filled in
		metadata.specific_info['ISBN'] = isbn

	supported_language_flag = int.from_bytes(nacp[0x302c:0x3030], 'little') #This might line up with nacp_languages	
	supported_languages = set()
	for k, v in nacp_languages.items():
		if supported_language_flag & (1 << k):
			if v == 'AmericanEnglish':
				supported_languages.add(languages_by_english_name['English (American)'])
			elif v == 'BritishEnglish':
				supported_languages.add(languages_by_english_name['English (British)'])
			elif v == 'LatinAmericanSpanish':
				supported_languages.add(languages_by_english_name['Spanish (Latin American)'])
			elif v == 'CanadianFrench':
				supported_languages.add(languages_by_english_name['French (Canadian)'])
			elif v == 'TraditionalChinese':
				supported_languages.add(languages_by_english_name['Chinese (Traditional)'])
			elif v == 'SimplifiedChinese':
				supported_languages.add(languages_by_english_name['Chinese (Simplified)'])
			else:
				supported_language = get_language_by_english_name(v)
				if supported_language:
					supported_languages.add(supported_language)
	metadata.languages = supported_languages

	#Screenshot = nacp[0x3034] sounds interesting?
	metadata.specific_info['Video Capture Allowed?'] = nacp[0x3035] != 0 #2 (instead of 1) indicates memory is allocated automatically who cares


	add_ratings_info(metadata, NintendoAgeRatings(nacp[0x3040:0x3060]))
	
	metadata.specific_info['Version'] = nacp[0x3060:0x3070].rstrip(b'\0').decode('utf-8', errors='backslashreplace')

	user_account_save_size = int.from_bytes(nacp[0x3080:0x3088], 'little')
	device_save_size = int.from_bytes(nacp[0x3090:0x3098], 'little')
	metadata.save_type = SaveType.Internal if user_account_save_size or device_save_size else SaveType.Nothing

	application_error_code_category = nacp[0x30a8:0x30b0]
	if any(application_error_code_category):
		#For some reason this is sometimes here and the product code when it is (which doesn't seem to be anywhere else)
		metadata.product_code = application_error_code_category.decode('utf-8', errors='backslashreplace')
		#TODO: Use switchtdb.xml although it won't be as useful when it uses the product code which we can only have sometimes

def _add_cnmt_xml_metadata(xml: ElementTree.Element, game_info: 'GameInfo') -> None:
	game_info.specific_info['Title Type'] = xml.findtext('Type')
	title_id = xml.findtext('Id')
	if title_id:
		game_info.specific_info['Title ID'] = title_id[2:]
	game_info.specific_info['Revision'] = xml.findtext('Version')
	#We also have RequiredDownloadSystemVersion, Digest, KeyGenerationMin, RequiredSystemVersion, PatchId if those are interesting/useful
	#Content contains Size, KeyGeneration, Hash, Type

def _call_nstool_for_decrypt(temp_folder: Path, temp_filename: Path) -> None:
	#Plan B, there is no reason why this can't be plan A I guess
	nstool = subprocess.run(['nstool', '-t', 'nca', '--part0', temp_folder, temp_filename], stdout=subprocess.PIPE, check=True, stderr=subprocess.DEVNULL)
	stdout = nstool.stdout.strip() #It prints error messages to stdout…
	if stdout == b'[NcaProcess ERROR] NCA FS Header [':
		#I guess that's the error message
		raise InvalidNCAException('Header wrong')
	
def _decrypt_control_nca_with_hactool(control_nca: bytes) -> Mapping[str, bytes]:
	with tempfile.TemporaryDirectory() as temp_folder:
		temp_folder_path = Path(temp_folder)
		#If we could get it to read /dev/stdin that'd be great, but it seems to not terribly want to do that, so we'll have to write that to a file too… grrr
		with tempfile.NamedTemporaryFile(dir=temp_folder_path) as temp_file:
			temp_path = Path(temp_file.name)
			temp_path.write_bytes(control_nca)

			try:
				hactool = subprocess.run(['hactool', '-x', temp_path, '--disablekeywarns', '--romfsdir', temp_folder_path], stdout=subprocess.DEVNULL, check=True, stderr=subprocess.PIPE)
				#If we could get the paths it outputs that'd be great, but it prints a bunch of junk to stdout
				stderr = hactool.stderr.strip()
				if stderr == b'Invalid NCA header! Are keys correct?':
					raise InvalidNCAException('Header wrong')
			except (subprocess.CalledProcessError, FileNotFoundError) as cactus:
				try:
					_call_nstool_for_decrypt(temp_folder_path, temp_path)
				except (subprocess.CalledProcessError, FileNotFoundError):
					raise ExternalToolNotHappeningException('No can do') from cactus

			files = {}
			for f in temp_folder_path.iterdir():
				#Because I can't predict what filenames it will write… I guess
				if f.is_file() and f != temp_path:
					files[f.name] = f.read_bytes()
			return files

def _decrypt_cnmt_nca_with_hactool(cnmt_nca: bytes) -> bytes:
	"""Decrypting NCAs is hard, let's go shopping (and get an external tool to do it)"""
	with tempfile.TemporaryDirectory() as temp_folder:
		temp_folder_path = Path(temp_folder)
		#If we could get it to read /dev/stdin that'd be great, but it seems to not terribly want to do that, so we'll have to write that to a file too… grrr
		with tempfile.NamedTemporaryFile(dir=temp_folder_path) as temp_file:
			temp_path = Path(temp_file.name)
			temp_path.write_bytes(cnmt_nca)

			try:
				#Since we're going through hactool anyway, might as well get it to find our actual cnmt for us so we don't have to parse the nca
				#hactool = subprocess.run(['hactool', '-t', 'nca', '-x', temp_path, '--disablekeywarns', '--section0dir', temp_folder_path], stdout=subprocess.DEVNULL, check=True, stderr=subprocess.PIPE)
				hactool = subprocess.run(['hactool', '-t', 'nca', '-x', temp_path, '--disablekeywarns', '--section0dir', temp_folder_path], stdout=subprocess.DEVNULL, check=True, stderr=subprocess.PIPE)
				#If we could get the paths it outputs that'd be great, but we can't really use any of that stuff it prints to stdout I don't think
				stderr = hactool.stderr.strip().decode('utf-8', 'backslashreplace')
				if stderr == 'Invalid NCA header! Are keys correct?':
					raise InvalidNCAException('Header wrong')
			except (subprocess.CalledProcessError, FileNotFoundError) as cactus:
				try:
					#Plan B
					_call_nstool_for_decrypt(temp_folder_path, temp_path)
				except (subprocess.CalledProcessError, FileNotFoundError):
					raise ExternalToolNotHappeningException(f'No can do: {stderr}') from cactus

			for f in temp_folder_path.iterdir():
				if f.suffix == '.cnmt' and f.is_file():
					return f.read_bytes()
			raise ExternalToolNotHappeningException(f'Uh oh, something got boned and the decrypted file was never written to the temp folder: {stderr}')

def _list_cnmt(cnmt: Cnmt, rom: 'FileROM', game_info: 'GameInfo', files: Mapping[PurePath, tuple[int, int]], extra_offset: int=0) -> None:
	game_info.specific_info['Title ID'] = cnmt.title_id
	game_info.specific_info['Revision'] = cnmt.version
	game_info.specific_info['Title Type'] = cnmt.type
	for k, v in cnmt.contents.items():
		if v[1] == ContentType.Control:
			control_nca_filename = PurePath(bytes.hex(k) + '.nca')
			control_nca_offset, control_nca_size = files[control_nca_filename]
			control_nca = rom.read(seek_to=control_nca_offset + extra_offset, amount=control_nca_size)
			try:
				control_nca_files = _decrypt_control_nca_with_hactool(control_nca)
				#We have icons and a NACP! WOOOOO
				#The icons match up with the titles that exist in the titles section, not SupportedLanguageFlag
				icons = {}
				nacp: bytes | None = None
				for filename, control_nca_file in control_nca_files.items():
					if not nacp and filename == 'control.nacp':
						#We would expect only one
						nacp = control_nca_file
					elif have_pillow and filename.startswith('icon_') and PurePath(filename).suffix == '.dat':
						icons[PurePath(filename).stem.removeprefix('icon_')] = control_nca_file
				if nacp:
					_add_nacp_metadata(game_info, nacp, icons)
				else:
					logger.debug('Hmm no control.nacp in %s', rom.path)
			except InvalidNCAException:
				logger.debug('Unfortunate, invalid cnmt NCA in %s', rom.path)
			except ExternalToolNotHappeningException:
				pass
			break
		#ContentMetaType.AddOnContent seems to generally not have control data, only a single ContentType.Data

def _list_cnmt_nca(data: bytes) -> Cnmt:
	# 0x12	0x2	Content Meta Count #Whazzat do
	# 0x14	0x1	Content Meta Attributes (0=None, 1=IncludesExFatDriver, 2=Rebootless) #Dunno what that does either
	# 0x18	0x4	Required Download System Version

	cnmt = _decrypt_cnmt_nca_with_hactool(data)
	
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

def _list_psf0(rom: 'FileROM') -> Mapping[PurePath, tuple[int, int]]:
	header = rom.read(amount=16)
	magic = header[:4]
	if magic != b'PFS0':
		raise InvalidPFS0Exception(repr(magic))
	number_of_files = int.from_bytes(header[4:8], 'little')
	size_of_string_table = ByteAmount.from_bytes(header[8:12], 'little')

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
		files[PurePath(name.decode('utf-8', errors='backslashreplace'))] = (offset + data_offset, size)
	return files

def _choose_main_cnmt(cnmts: Collection[Cnmt]) -> Cnmt | None:
	if not cnmts:
		return None
	if len(cnmts) == 1:
		return next(cnmt for cnmt in cnmts)
	#elif len(cnmts) > 1:
	#Sometimes you can have more than one if the cartridge includes an embedded patch
	application_cnmts = {c for c in cnmts if c.type == SwitchContentMetaType.Application}
	if len(application_cnmts) == 1:
		return next(app_cnmt for app_cnmt in application_cnmts)

	#Uh oh that didn't help, oh no what do we do I guess let's just take the first one
	return next(cnmt for cnmt in cnmts)

def add_nsp_metadata(rom: 'FileROM', game_info: 'GameInfo') -> None:
	files = _list_psf0(rom)
	cnmts = set()
	cnmt_xml = None
	try_fallback_to_xml = False

	for filename, offsetsize in files.items():
		if filename.suffixes == ['.cnmt', '.nca']:
			cnmt_nca = rom.read(amount=offsetsize[1], seek_to=offsetsize[0])
			try:
				cnmts.add(_list_cnmt_nca(cnmt_nca))
			except InvalidNCAException:
				logger.debug('%s is an invalid cnmt.nca in %s', filename, rom.path, exc_info=True)
				continue
			except ExternalToolNotHappeningException:
				try_fallback_to_xml = True
				break
		if filename.suffixes == ['.cnmt', '.xml']:
			#I think the dumping tool for NSPs is actually what puts these here rather than this being an actual official thing on NSPs, but if we need a fallback, this will do
			cnmt_xml_data = rom.read(amount=offsetsize[1], seek_to=offsetsize[0])
			try:
				cnmt_xml = ElementTree.fromstring(cnmt_xml_data.decode('utf-8'))
			except UnicodeDecodeError:
				continue

	if try_fallback_to_xml and cnmt_xml is not None:
		#We could look at the list of contents in there, but there's not much point seeing as how we'd need to decrypt the content NCA anyway
		_add_cnmt_xml_metadata(cnmt_xml, game_info)

	main_cnmt = _choose_main_cnmt(cnmts)
	if main_cnmt:
		_list_cnmt(main_cnmt, rom, game_info, files)
	else:
		logger.debug('Uh oh no cnmt.nca in %s?', rom.path)
	
def _read_hfs0(rom: 'FileROM', offset: int, max_size: ByteAmount | None=None) -> 'Mapping[PurePath, tuple[int, ByteAmount]]':
	header = rom.read(offset, 16)

	magic = header[:4]
	if magic != b'HFS0':
		raise InvalidHFS0Exception(f'Invalid magic, expected HFS0 but got {magic!r} at offset {offset:x}')

	number_of_files = int.from_bytes(header[4:8], 'little')
	string_table_size = ByteAmount.from_bytes(header[8:12], 'little')
	
	file_entry_table_size = ByteAmount(64 * number_of_files)
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

		size = ByteAmount.from_bytes(entry[8:16], 'little')
		total_size += size
		if max_size and total_size > max_size:
			raise InvalidHFS0Exception(f'Exceeded max_size! File sizes are too big and therefore wrong total_size = {total_size} max_size = {max_size}')
		
		offset_into_string_table = int.from_bytes(entry[16:20], 'little')
		
		name = string_table[offset_into_string_table:]
		if b'\0' in name:
			name = name[:name.index(b'\0')]

		hashed_region_size = int.from_bytes(entry[20:24], 'little')
		real_file_offset += hashed_region_size

		try:
			files[PurePath(name.decode('utf-8'))] = (real_file_offset, size)
		except UnicodeDecodeError:
			logger.info('%s has invalid filename in string table: %s', rom, name, exc_info=True)

	return files

def add_xci_metadata(rom: 'FileROM', metadata: 'GameInfo') -> None:
	header = rom.read(amount=0x200)
	magic = header[0x100:0x104]
	if magic != b'HEAD':
		raise InvalidXCIException(f'Not a XCI: {magic!r}')

	metadata.specific_info['Gamecard Size'] = game_card_size.get(header[0x10d], f'unknown 0x{header[0x10d]:x}')
	flags = header[0x10f]
	if flags != 0:
		metadata.specific_info['Gamecard Flags'] = GamecardFlags(flags)
	root_partition_offset = int.from_bytes(header[0x130:0x138], 'little') #Always 0xf000 innit? But just to be sure
	root_partition_header_size = int.from_bytes(header[0x138:0x140], 'little') #But that will always be 512
	root_partition_header_expected_hash = header[0x140:0x160]
	root_partition_header = rom.read(root_partition_offset, root_partition_header_size)
	if hashlib.sha256(root_partition_header).digest() != root_partition_header_expected_hash:
		raise InvalidXCIException('HFS0 hash in XCI header did not match')

	root_partition = _read_hfs0(rom, root_partition_offset)
	secure = root_partition.get(PurePath('secure'))
	if secure:
		#This one is always here and not sometimes empty like normal is, and also the cnmt is encrypted anyway, so whaddya do
		secure_offset, secure_size = secure
		real_secure_offset = int.from_bytes(header[0x104:0x108], 'little') * 0x200
		secure_offset_diff = secure_offset - real_secure_offset
		secure_files = _read_hfs0(rom, real_secure_offset, secure_size)

		cnmts = []
		found_something = False
		for k, v in secure_files.items():
			if k.suffixes == ['.cnmt', '.nca']:
				found_something = True
				cnmt = rom.read(v[0] + secure_offset_diff, v[1])
				try:
					cnmts.append(_list_cnmt_nca(cnmt))
				except InvalidNCAException:
					logger.debug('%s is an invalid NCA in %s', k, rom.path, exc_info=True)
					continue
				except ExternalToolNotHappeningException:
					logger.debug('baaa trying to use external tool for inspecting NCA %s in XCI %s failed', k, rom.path, exc_info=True)
					continue

		main_cnmt = _choose_main_cnmt(cnmts)
		if main_cnmt:
			_list_cnmt(main_cnmt, rom, metadata, secure_files, secure_offset_diff)
		elif not found_something:
			logger.debug('Uh oh no cnmt.nca?')

def add_nro_metadata(rom: 'FileROM', metadata: 'GameInfo') -> None:
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
		_add_nacp_metadata(metadata, nacp)

def add_switch_rom_file_info(rom: 'FileROM', metadata: 'GameInfo') -> None:
	if rom.extension == 'nro':
		add_nro_metadata(rom, metadata)
	if rom.extension == 'xci':
		try:
			add_xci_metadata(rom, metadata)
		except InvalidXCIException:
			logger.info('%s was invalid XCI', rom.path, exc_info=True)
		except InvalidHFS0Exception:
			logger.info('%s had invalid HFS0', rom.path, exc_info=True)
		
	if rom.extension == 'nsp':
		try:
			add_nsp_metadata(rom, metadata)
		except InvalidPFS0Exception:
			logger.info('%s was invalid PFS0', rom.path, exc_info=True)
