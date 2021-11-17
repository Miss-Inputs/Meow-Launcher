import collections
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union
from xml.etree import ElementTree

from meowlauncher.common_types import MediaType, SaveType
from meowlauncher.input_metadata import InputInfo
from meowlauncher.util.region_info import Language, Region

if TYPE_CHECKING:
	from PIL.Image import Image

#FIXME! Section names should not be here - we need to rewrite to_info_fields to make more sense, it's just to make sure a circular import doesn't happen
metadata_section_name = 'X-Meow Launcher Metadata'
id_section_name = 'X-Meow Launcher ID'
junk_section_name = 'X-Meow Launcher Junk'
image_section_name = 'X-Meow Launcher Images'
name_section_name = 'X-Meow Launcher Names'
document_section_name = 'X-Meow Launcher Documents'
description_section_name = 'X-Meow Launcher Descriptions'

class CPU():
	#TODO I only give a shit about this info for MAME machines, move it there
	#TODO These should also take a constructor with xml, not be created and then loaded, that's silly
	def __init__(self):
		self.chip_name: Optional[str] = None
		self.clock_speed: Optional[int] = None
		self.tag: Optional[str] = None

	@staticmethod
	def format_clock_speed(hertz: int, precision: int=4) -> str:
		if hertz >= 1_000_000_000:
			return ('{0:.' + str(precision) + 'g} GHz').format(hertz / 1_000_000_000)
		if hertz >= 1_000_000:
			return ('{0:.' + str(precision) + 'g} MHz').format(hertz / 1_000_000)
		if hertz >= 1_000:
			return ('{0:.' + str(precision) + 'g} KHz').format(hertz / 1_000)

		return ('{0:.' + str(precision) + 'g} Hz').format(hertz)

	def get_formatted_clock_speed(self):
		if self.clock_speed:
			return CPU.format_clock_speed(self.clock_speed)
		return None

	def load_from_xml(self, xml: ElementTree.Element):
		self.chip_name = xml.attrib.get('name')
		self.tag = xml.attrib.get('tag')
		if xml.attrib['name'] != 'Netlist CPU Device' and 'clock' in xml.attrib:
			try:
				self.clock_speed = int(xml.attrib['clock'])
			except ValueError:
				pass

def _format_count(list_of_something: Iterable):
	counter = collections.Counter(list_of_something)
	if len(counter) == 1:
		if list(counter.keys())[0] is None:
			return None
	return ' + '.join([value if count == 1 else f'{value} * {count}' for value, count in counter.items() if value])

class CPUInfo():
	def __init__(self):
		self.cpus = []
		self._inited = False

	@property
	def is_inited(self):
		return self.cpus or self._inited

	def set_inited(self):
		self._inited = True

	@property
	def main_chip(self):
		if not self.cpus:
			return None
		return self.cpus[0]

	@property
	def number_of_cpus(self):
		return len(self.cpus)

	@property
	def chip_names(self):
		return _format_count([cpu.chip_name for cpu in self.cpus])

	@property
	def clock_speeds(self):
		return _format_count([cpu.get_formatted_clock_speed() for cpu in self.cpus])

	@property
	def tags(self):
		return _format_count([cpu.tag for cpu in self.cpus])

	def add_cpu(self, cpu):
		self.cpus.append(cpu)

class Screen():
	def __init__(self):
		self.width = None
		self.height = None
		self.type = None
		self.tag = None
		self.refresh_rate = None

	def get_screen_resolution(self):
		if self.type in {'raster', 'lcd'}:
			return '{0:.0f}x{1:.0f}'.format(self.width, self.height)
		#Other types are vector (Asteroids, etc) or svg (Game & Watch games, etc)
		return self.type.capitalize() if self.type else None

	def load_from_xml(self, xml):
		self.type = xml.attrib['type']
		self.tag = xml.attrib['tag']
		if self.type in {'raster', 'lcd'}:
			self.width = float(xml.attrib['width'])
			self.height = float(xml.attrib['height'])

		if 'refresh' in xml.attrib:
			try:
				self.refresh_rate = float(xml.attrib['refresh'])
			except ValueError:
				pass

	def get_formatted_refresh_rate(self):
		if self.refresh_rate:
			return CPU.format_clock_speed(self.refresh_rate)
		return None

	def get_aspect_ratio(self):
		if self.width and self.height:
			return Screen.find_aspect_ratio(self.width, self.height)
		return None

	@staticmethod
	def find_aspect_ratio(width, height):
		for i in reversed(range(1, max(int(width), int(height)) + 1)):
			if (width % i) == 0 and (height % i) == 0:
				return '{0:.0f}:{1:.0f}'.format(width // i, height // i)

		#This wouldn't happen unless one of the arguments is 0 or something silly like that
		return None

class ScreenInfo():
	def __init__(self):
		self.screens = []

	def get_number_of_screens(self):
		return len(self.screens)

	def load_from_xml_list(self, xmls):
		for display in xmls:
			screen = Screen()
			screen.load_from_xml(display)
			self.screens.append(screen)

	def get_screen_resolutions(self):
		return _format_count([screen.get_screen_resolution() for screen in self.screens if screen.get_screen_resolution()])

	def get_refresh_rates(self):
		return _format_count([screen.get_formatted_refresh_rate() for screen in self.screens if screen.get_formatted_refresh_rate()])

	def get_aspect_ratios(self):
		return _format_count([screen.get_aspect_ratio() for screen in self.screens if screen.get_aspect_ratio()])

	def get_display_types(self):
		return _format_count([screen.type for screen in self.screens if screen.type])

	def get_display_tags(self):
		return _format_count([screen.tag for screen in self.screens if screen.tag])

class Date():
	#Class to hold a maybe-incorrect/maybe-guessed/maybe-incomplete date, but I thought MaybeIncompleteMaybeGuessedDate was a bit too much of a mouthful and I'm not clever enough to know what else to call it
	def __init__(self, year=None, month=None, day=None, is_guessed: bool=False):
		self.year = str(year) if year else None
		self.month = str(month) if month else None
		self.day = str(day) if day else None
		self.is_guessed = is_guessed

	@property
	def is_partly_unknown(self) -> bool:
		if not self.month:
			return True
		if not self.day:
			return True
		if not self.year:
			return True
		#pylint: disable=unsupported-membership-test #Seems to be unaware that I have already tested them to not be None, so actually they do… just leave this one to the type checkers, buddy
		return 'x' in self.year or 'x' in self.month or 'x' in self.day or '?' in self.year or '?' in self.month or '?' in self.day
	
	def is_better_than(self, other_date: Optional['Date']) -> bool:
		if not other_date:
			return True
		if other_date.is_guessed and not self.is_guessed:
			return True
		if (other_date.is_partly_unknown and not self.is_partly_unknown) and not self.is_guessed:
			return True

		return False

	def __str__(self):
		parts = [self.year if self.year else '????']
		if self.month or self.day:
			if self.month:
				parts.append(self.month.rjust(2, '0'))
			else:
				parts.append('??')
			if self.day:
				parts.append(self.day.rjust(2, '0'))
			else:
				parts.append('??')
		s = '-'.join(parts)
		if self.is_guessed:
			s += '?'
		return s

class Metadata():
	def __init__(self) -> None:
		self.platform: Optional[str] = None
		self.categories: list[str] = []
		self.release_date: Optional[Date] = None
		self.emulator_name: Optional[str] = None #Hmm is this needed now?
		self.extension: Optional[str] = None

		self.genre: Optional[str] = None
		self.subgenre: Optional[str] = None
		self.languages: list[Language] = []
		self.developer: Optional[str] = None
		self.publisher: Optional[str] = None
		self.save_type = SaveType.Unknown
		self.product_code: Optional[str] = None
		self.regions: list[Region] = []
		self.media_type: Optional[MediaType] = None
		self.notes: Optional[str] = None
		self.disc_number: Optional[int] = None
		self.disc_total: Optional[int] = None
		self.series: Optional[str] = None
		self.series_index: Union[str, int, None] = None

		#Set this up later with the respective objects
		self.cpu_info = CPUInfo()
		self.screen_info: Optional[ScreenInfo] = None
		self.input_info = InputInfo()

		self.specific_info: dict[str, Any] = {} #Stuff that's too specific to put as an attribute here

		self.images: dict[str, Union[Path, 'Image']] = {}
		#TODO: The override name shenanigans in Wii/PSP: Check for name = None in launchers, and set name = None if overriding it to something else, and put the overriden name in here
		self.names: dict[str, str] = {}
		self.documents: dict[str, Union[str, Path]] = {} #Paths of either variety, or URLs
		self.descriptions: dict[str, str] = {}

	def add_alternate_name(self, name: str, field: str='Alternate-Name'):
		if field in self.names:
			self.names[field + '-1'] = self.names[field]
			self.names[field + '-2'] = name
			self.names.pop(field)
			return
		if field + '-1' in self.names:
			i = 2
			while f'{field}-{i}' in self.names:
				i += 1
			self.names[f'{field}-{i}'] = name
			return
		self.names[field] = name

	def add_notes(self, notes: Optional[str]):
		if not notes:
			return
		if not self.notes:
			self.notes = notes
		elif self.notes != notes:
			self.notes += ';' + notes

	def to_launcher_fields(self) -> dict[str, dict[str, Any]]:
		fields = {}

		metadata_fields = {
			'Genre': self.genre,
			'Subgenre': self.subgenre,
			'Languages': [language.native_name for language in self.languages if language],
			'Release-Date': self.release_date,
			'Emulator': self.emulator_name,
			'Extension': self.extension,
			'Categories': self.categories,
			'Platform': self.platform,
			'Save-Type': ('Memory Card' if self.save_type == SaveType.MemoryCard else self.save_type.name) if self.save_type else 'Nothing',
			'Publisher': self.publisher,
			'Developer': self.developer,
			'Product-Code': self.product_code,
			'Regions': [region.name if region else 'None!' for region in self.regions] if self.regions else [],
			'Media-Type': ('Optical Disc' if self.media_type == MediaType.OpticalDisc else self.media_type.name) if self.media_type else None,
			'Notes': self.notes,
			'Disc-Number': self.disc_number,
			'Disc-Total': self.disc_total,
			'Series': self.series,
			'Series-Index': self.series_index,
		}
		if self.release_date and self.release_date.year:
			metadata_fields['Year'] = self.release_date.year + '?' if self.release_date.is_guessed else self.release_date.year

		if self.cpu_info.is_inited:
			metadata_fields['Number-of-CPUs'] = self.cpu_info.number_of_cpus
			if self.cpu_info.number_of_cpus:
				metadata_fields['Main-CPU'] = self.cpu_info.chip_names
				metadata_fields['Clock-Speed'] = self.cpu_info.clock_speeds
				metadata_fields['CPU-Tags'] = self.cpu_info.tags

		if self.screen_info:
			num_screens = self.screen_info.get_number_of_screens()
			metadata_fields['Number-of-Screens'] = num_screens

			if num_screens:
				metadata_fields['Screen-Resolution'] = self.screen_info.get_screen_resolutions()
				metadata_fields['Refresh-Rate'] = self.screen_info.get_refresh_rates()
				metadata_fields['Aspect-Ratio'] = self.screen_info.get_aspect_ratios()

				metadata_fields['Screen-Type'] = self.screen_info.get_display_types()
				metadata_fields['Screen-Tag'] = self.screen_info.get_display_tags()

		if self.input_info.is_inited:
			metadata_fields['Standard-Input'] = self.input_info.has_standard_inputs
			metadata_fields['Input-Methods'] = self.input_info.describe()

		metadata_fields.update(self.specific_info)

		fields[metadata_section_name] = metadata_fields
		fields[junk_section_name] = {}

		if self.images:
			fields[image_section_name] = {}
			for k, image in self.images.items():
				fields[image_section_name][k] = image
		
		if self.names:
			fields[name_section_name] = {}
			for k, name in self.names.items():
				fields[name_section_name][k] = name
			
		if self.documents:
			fields[document_section_name] = {}
			for k, document in self.documents.items():
				fields[document_section_name][k] = document

		if self.descriptions:
			fields[description_section_name] = {}
			for k, description in self.descriptions.items():
				fields[description_section_name][k] = description

		return fields
