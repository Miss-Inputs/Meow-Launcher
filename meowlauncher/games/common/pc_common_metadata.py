import datetime
import io
import os
from pathlib import Path
import struct
from typing import Any, Optional, Union

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

from meowlauncher.config.main_config import main_config
from meowlauncher.metadata import Date, Metadata
from meowlauncher.util.utils import junk_suffixes

#Hmm, are other extensions going to work as icons in a file manager
icon_extensions = ('png', 'ico', 'xpm', 'svg')

def get_pe_file_info(pe: 'pefile.PE') -> Optional[dict[str, Any]]: #TODO refactor - Union[str, datetime.datetime] is a bit silly as it means you have to check for it every time if you have mypy, maybe we should return something else
	if not hasattr(pe, 'FileInfo'):
		return None
	for file_info in pe.FileInfo:
		for info in file_info:
			if hasattr(info, 'StringTable'):
				for string_table in info.StringTable:
					d = {k.decode('ascii', errors='ignore'): v.rstrip(b'\0').decode('ascii', errors='ignore') for k, v in string_table.entries.items()}
					if hasattr(pe, 'FILE_HEADER'):
						d['TimeDateStamp'] = datetime.datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp)
					return d
	return None

def get_exe_properties(path: str) -> Optional[dict[str, Any]]:
	if have_pefile:
		try:
			pe = pefile.PE(path, fast_load=True)
			pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])
			try:
				return get_pe_file_info(pe)
			#pylint: disable=broad-except
			except Exception as ex:
				if main_config.debug:
					print('Something weird happened in get_exe_properties', path, ex)
				return None
		except pefile.PEFormatError:
			pass
	return None

def add_metadata_for_raw_exe(path: str, metadata: Metadata):
	props = get_exe_properties(path)
	if not props:
		return
	
	#Possible values to expect: https://docs.microsoft.com/en-us/windows/win32/api/winver/nf-winver-verqueryvaluea#remarks

	# if props.get('InternalName'):
	# 	if props.get('InternalName') != props.get('OriginalFilename'):
	# 		print(path, props.get('InternalName'), props.get('OriginalFilename'))

	if not metadata.publisher and not metadata.developer:
		company_name = props.get('CompanyName')
		if company_name:
			while junk_suffixes.search(company_name):
				company_name = junk_suffixes.sub('', company_name)
			metadata.publisher = company_name

	product_name = props.get('ProductName')
	if product_name:
		metadata.add_alternate_name(product_name, 'Name')
	copyright_string = props.get('LegalCopyright')
	if copyright_string:
		metadata.specific_info['Copyright'] = copyright_string
	description = props.get('FileDescription')
	if description and description != product_name:
		metadata.descriptions['File-Description'] = description
	comments = props.get('Comments')
	if comments and comments != product_name:
		metadata.specific_info['File-Comment'] = comments
	trademarks = props.get('LegalTrademarks')
	if trademarks and trademarks != copyright_string:
		metadata.specific_info['Trademarks'] = trademarks
	
	timedatestamp = props.get('TimeDateStamp')
	if timedatestamp:
		if not (timedatestamp > datetime.datetime.now() or timedatestamp.year < 1993):
			#If the date has not even happened yet, or is before Windows NT 3.1 and hence the PE format was even invented, I think the fuck not

			build_date = Date(timedatestamp.year, timedatestamp.month, timedatestamp.day)
			metadata.specific_info['Build-Date'] = build_date
			guessed_date = Date(build_date.year, build_date.month, build_date.day, True)
			if guessed_date.is_better_than(metadata.release_date):
				metadata.release_date = guessed_date

def pe_directory_to_dict(directory) -> dict:
	d = {}
	for entry in directory.entries:
		d[entry.name if entry.name else entry.id] = pe_directory_to_dict(entry.directory) if hasattr(entry, 'directory') else entry
	return d

def get_pe_resources(pe: 'pefile.PE', resource_type) -> Optional[dict]:
	if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
		#weirdo has no resources
		return None
	for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
		if entry.id == resource_type:
			return pe_directory_to_dict(entry.directory)
	return None

def get_first_pe_resource(resource_dict):
	for k, v in resource_dict.items():
		if isinstance(v, dict):
			return get_first_pe_resource(v)
		return k, v

def parse_pe_group_icon_directory(data: bytes) -> dict[Any, dict[str, Any]]:
	struct_format = '<BBBBHHIH'
	_, _, count = struct.unpack('<HHH', data[:6]) #don't need type I think
	return {entry_id: {'width': width, 'height': height, 'colour_count': colour_count, 'planes': planes, 'bit_count': bit_count, 'bytes_in_res': bytes_in_res}
		for width, height, colour_count, _, planes, bit_count, bytes_in_res, entry_id in struct.iter_unpack(struct_format, data[6:6 + (struct.calcsize(struct_format) * count)])}

def get_icon_from_pe(pe: 'pefile.PE') -> Optional[Image.Image]:
	group_icons = get_pe_resources(pe, pefile.RESOURCE_TYPE['RT_GROUP_ICON'])
	if not group_icons:
		return None
	_, first_group_icon = get_first_pe_resource(group_icons)
	
	first_group_icon_data = pe.get_data(first_group_icon.data.struct.OffsetToData, first_group_icon.data.struct.Size)
	header = first_group_icon_data[:6]
	group_icon_entries = parse_pe_group_icon_directory(first_group_icon_data)
	icons_dir = get_pe_resources(pe, pefile.RESOURCE_TYPE['RT_ICON'])
	if not icons_dir:
		return None
	ico_entry_format = '<BBBBHHII'
	offset = 6 + (len(group_icon_entries) * struct.calcsize(ico_entry_format))
	data = b''
	for k, v in group_icon_entries.items():
		icon_resource = icons_dir.get(k)
		#if not icon_resource:
		#	#Odd, this should not happen
		#	continue
		if isinstance(icon_resource, dict):
			icon_resource = list(icon_resource.values())[0]
		icon_resource_data = pe.get_data(icon_resource.data.struct.OffsetToData, icon_resource.data.struct.Size)
		#This is the raw bytes so we need to make the .ico ourselves
		ico_entry = struct.pack(ico_entry_format, v['width'], v['height'], v['colour_count'], 0, v['planes'], v['bit_count'], v['bytes_in_res'], offset)
		offset += v['bytes_in_res']
		header += ico_entry
		data += icon_resource_data
	ico = header + data
	return Image.open(io.BytesIO(ico))

def get_icon_inside_exe(path: str) -> Optional['Image.Image']:
	if have_pefile:
		try:
			pe = pefile.PE(path, fast_load=True)
			pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])
			try:
				icon = get_icon_from_pe(pe)
			#pylint: disable=broad-except
			except Exception as ex:
				if main_config.debug:
					print('Something weird happened in get_icon_from_pe', path, ex)
				return None
			if icon:
				return icon
		except pefile.PEFormatError:
			pass
	return None

def look_for_icon_next_to_file(path: Path) -> Optional[Union[Path, 'Image.Image']]:
	exe_icon = get_icon_inside_exe(str(path))
	if exe_icon:
		return exe_icon

	parent_folder = path.parent
	for f in parent_folder.iterdir():
		for ext in icon_extensions:
			if f.name.lower() == path.with_suffix(os.path.extsep + ext).name.lower():
				return f

	return look_for_icon_in_folder(parent_folder, False)

def look_for_icon_in_folder(folder: Path, look_for_any_ico: bool=True) -> Optional[Path]:
	for f in folder.iterdir():
		if f.name == 'gfw_high.ico':
			#Some kind of older GOG icon? Except not in actual GOG games, just stuff that was distributed elsewhere I guess
			return f

		for ext in icon_extensions:
			if f.suffix == os.path.extsep + ext:
				if f.name.lower() == 'icon':
					return f
				if f.name.startswith('goggame-'):
					return f
			
	if look_for_any_ico:
		#Just get the first ico if we didn't find anything specific
		for f in folder.iterdir():
			if f.name.lower().endswith('.ico'):
				return f
	return None

def check_for_interesting_things_in_folder(folder: Path, metadata: Metadata, find_wrappers: bool=False):
	#Let's check for things existing because we can (there's not really any other reason to do this, it's just fun)
	#Not sure if any of these are in lowercase? Or they might be in a different directory
	dir_entries = list(folder.iterdir())
	files = [f.name.lower() for f in dir_entries if f.is_file()]
	subdirs = [f.name.lower() for f in dir_entries if f.is_dir()]
	
	if 'libdiscord-rpc.so' in files or 'discord-rpc.dll' in files:
		metadata.specific_info['Discord-Rich-Presence'] = True

	if find_wrappers:
		#This is only really relevant for Steam etc
		if 'dosbox' in subdirs or any(f.startswith('dosbox') for f in files):
			metadata.specific_info['Wrapper'] = 'DOSBox'

		if any(f.startswith('scummvm_') for f in subdirs) or any(f.startswith('scummvm') for f in files):
			metadata.specific_info['Wrapper'] = 'ScummVM'

		if folder.joinpath('support', 'UplayInstaller.exe').is_file():
			metadata.specific_info['Launcher'] = 'uPlay'
