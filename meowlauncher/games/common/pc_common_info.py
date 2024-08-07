import datetime
import io
import logging
import struct
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

try:
	import pefile

	have_pefile = True
except ModuleNotFoundError:
	have_pefile = False

try:
	from PIL import Image

	have_pillow = True
except ModuleNotFoundError:
	have_pillow = False

from meowlauncher.info import Date
from meowlauncher.util.utils import junk_suffixes

if TYPE_CHECKING:
	from meowlauncher.info import GameInfo

logger = logging.getLogger(__name__)

# Hmm, are other extensions going to work as icons in a file manager
icon_extensions = {'png', 'ico', 'xpm', 'svg'}


def _get_pe_string_table(pe: 'pefile.PE') -> 'Mapping[str, str] | None':
	try:
		for file_info in pe.FileInfo:
			for info in file_info:
				if hasattr(info, 'StringTable'):
					for string_table in info.StringTable:
						return {
							k.decode('ascii', 'backslashreplace'): v.rstrip(b'\0').decode(
								'ascii', 'backslashreplace'
							)
							for k, v in string_table.entries.items()
						}
	except AttributeError:
		pass
	return None


def get_exe_properties(path: Path) -> tuple['Mapping[str, str] | None', datetime.datetime | None]:
	if have_pefile:
		try:
			pe = pefile.PE(str(path), fast_load=True)
			pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])
			try:
				timestamp = datetime.datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp)
			except AttributeError:
				timestamp = None
			try:
				return _get_pe_string_table(pe), timestamp
			except Exception:  # pylint: disable=broad-except
				logger.exception('Something weird happened in get_exe_properties for %s', path)
		except pefile.PEFormatError:
			pass
	return None, None


def add_info_for_raw_exe(path: Path, game_info: 'GameInfo') -> None:
	props, timedatestamp = get_exe_properties(path)

	if props:
		# Possible values to expect: https://docs.microsoft.com/en-us/windows/win32/api/winver/nf-winver-verqueryvaluea#remarks
		if not game_info.publisher and not game_info.developer:
			company_name = props.get('CompanyName')
			if company_name:
				while junk_suffixes.search(company_name):
					company_name = junk_suffixes.sub('', company_name)
				game_info.publisher = company_name

		product_name = props.get('ProductName')
		if product_name:
			game_info.add_alternate_name(product_name, 'Product Name')
		copyright_string = props.get('LegalCopyright')
		if copyright_string:
			game_info.specific_info['Copyright'] = copyright_string
		description = props.get('FileDescription')
		if description and description != product_name:
			game_info.descriptions['File Description'] = description
		comments = props.get('Comments')
		if comments and comments != product_name:
			game_info.specific_info['File Comment'] = comments
		trademarks = props.get('LegalTrademarks')
		if trademarks and trademarks != copyright_string:
			game_info.specific_info['Trademarks'] = trademarks

	if timedatestamp:
		if not (timedatestamp.year < 1993 or timedatestamp > datetime.datetime.now()):
			# If the date has not even happened yet, or is before Windows NT 3.1 and hence the PE format was even invented, I think the fuck not
			build_date = Date(timedatestamp.year, timedatestamp.month, timedatestamp.day)
			game_info.specific_info['Build Date'] = build_date
			guessed_date = Date(build_date.year, build_date.month, build_date.day, is_guessed=True)
			if guessed_date.is_better_than(game_info.release_date):
				game_info.release_date = guessed_date


def _pe_directory_to_dict(
	directory: 'pefile.ResourceDirData',
) -> 'Mapping[str | int, pefile.ResourceDirEntryData]':
	return {
		entry.name if entry.name else entry.id: _pe_directory_to_dict(entry.directory)
		if hasattr(entry, 'directory')
		else entry
		for entry in directory.entries
	}


def _get_pe_resources(
	pe: 'pefile.PE', resource_type: int
) -> 'Mapping[str | int, pefile.ResourceDirEntryData] | None':
	if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
		# weirdo has no resources
		return None
	for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
		if entry.id == resource_type:
			return _pe_directory_to_dict(entry.directory)
	return None


def _get_first_pe_resource(
	resource_dict: 'Mapping[str | int, pefile.ResourceDirEntryData]',
) -> tuple[str | int | None, 'pefile.ResourceDirEntryData | None']:
	for k, v in resource_dict.items():
		if isinstance(v, Mapping):
			return _get_first_pe_resource(v)
		return k, v
	return None, None


def _parse_pe_group_icon_directory(data: bytes) -> 'Mapping[int, Mapping[str, int]]':
	# TODO: Use dataclass
	struct_format = '<BBBBHHIH'
	_, _, count = struct.unpack('<HHH', data[:6])  # don't need type I think
	return {
		entry_id: {
			'width': width,
			'height': height,
			'colour_count': colour_count,
			'planes': planes,
			'bit_count': bit_count,
			'bytes_in_res': bytes_in_res,
		}
		for width, height, colour_count, _, planes, bit_count, bytes_in_res, entry_id in struct.iter_unpack(
			struct_format, data[6 : 6 + (struct.calcsize(struct_format) * count)]
		)
	}


def get_icon_from_pe(pe: 'pefile.PE') -> 'Image.Image | None':
	group_icons = _get_pe_resources(pe, pefile.RESOURCE_TYPE['RT_GROUP_ICON'])
	if not group_icons:
		return None
	_, first_group_icon = _get_first_pe_resource(group_icons)
	if not first_group_icon:
		return None

	first_group_icon_data = pe.get_data(
		first_group_icon.data.struct.OffsetToData, first_group_icon.data.struct.Size
	)
	header = first_group_icon_data[:6]
	group_icon_entries = _parse_pe_group_icon_directory(first_group_icon_data)
	icons_dir = _get_pe_resources(pe, pefile.RESOURCE_TYPE['RT_ICON'])
	if not icons_dir:
		return None
	ico_entry_format = '<BBBBHHII'
	offset = 6 + (len(group_icon_entries) * struct.calcsize(ico_entry_format))
	data = b''
	for k, v in group_icon_entries.items():
		icon_resource = icons_dir.get(k)
		# if not icon_resource:
		# #Odd, this should not happen
		# continue
		if isinstance(icon_resource, dict):
			icon_resource = next(iter(icon_resource.values()))
		icon_resource_data = pe.get_data(
			icon_resource.data.struct.OffsetToData, icon_resource.data.struct.Size
		)
		# This is the raw bytes so we need to make the .ico ourselves
		ico_entry = struct.pack(
			ico_entry_format,
			v['width'],
			v['height'],
			v['colour_count'],
			0,
			v['planes'],
			v['bit_count'],
			v['bytes_in_res'],
			offset,
		)
		offset += v['bytes_in_res']
		header += ico_entry
		data += icon_resource_data
	ico = header + data
	return Image.open(io.BytesIO(ico), formats=('ICO',))


def get_icon_inside_exe(path: Path) -> 'Image.Image | None':
	if have_pefile:
		try:
			pe = pefile.PE(str(path), fast_load=True)
			pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])
			try:
				icon = get_icon_from_pe(pe)
			except Exception:  # pylint: disable=broad-except
				logger.exception('Something weird happened in get_icon_from_pe for %s', path)
				return None
			if icon:
				return icon
		except pefile.PEFormatError:
			pass
	return None


def look_for_icon_for_file(path: Path) -> 'Path | Image.Image | None':
	exe_icon = get_icon_inside_exe(path)
	if exe_icon:
		return exe_icon

	parent_folder = path.parent
	return next(
		(
			f
			for f in parent_folder.iterdir()
			if f.stem.lower() == path.stem.lower() and f.suffix[1:].lower() in icon_extensions
		),
		look_for_icon_in_folder(parent_folder, look_for_any_ico=False),
	)


def look_for_icon_in_folder(folder: Path, look_for_any_ico: bool = True) -> Path | None:
	for f in folder.iterdir():
		if f.name == 'gfw_high.ico':
			# Some kind of older GOG icon? Except not in actual GOG games, just stuff that was distributed elsewhere I guess
			return f

		if f.suffix[1:].lower() in icon_extensions:
			if f.stem.lower() == 'icon':
				return f
			if f.name.startswith('goggame-'):
				return f

	if look_for_any_ico:
		# Just get the first ico if we didn't find anything specific
		return next((f for f in folder.iterdir() if f.suffix.lower() == '.ico'), None)
	return None


def check_for_interesting_things_in_folder(
	folder: Path, game_info: 'GameInfo', find_wrappers: bool = False
) -> None:
	"""Let's check for things existing because we can (there's not really any other reason to do this, it's just fun)
	Not sure if any of these are in lowercase? Or they might be in a different directory"""
	dir_entries = tuple(folder.iterdir())
	files = {f.name.lower() for f in dir_entries if f.is_file()}
	subdirs = {f.name.lower() for f in dir_entries if f.is_dir()}

	if 'libdiscord-rpc.so' in files or 'discord-rpc.dll' in files:
		game_info.specific_info['Discord Rich Presence?'] = True

	if find_wrappers:
		# This is only really relevant for Steam etc
		if 'dosbox' in subdirs or any(f.startswith('dosbox') for f in files):
			game_info.specific_info['Wrapper'] = 'DOSBox'

		if any(f.startswith('scummvm_') for f in subdirs) or any(
			f.startswith('scummvm') for f in files
		):
			game_info.specific_info['Wrapper'] = 'ScummVM'

		if folder.joinpath('support', 'UplayInstaller.exe').is_file():
			game_info.specific_info['Launcher'] = 'uPlay'
