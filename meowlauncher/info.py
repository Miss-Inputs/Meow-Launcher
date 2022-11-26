from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from meowlauncher.common_types import MediaType, SaveType
from meowlauncher.input_info import InputInfo
from meowlauncher.util.region_info import Language, Region

if TYPE_CHECKING:
	from collections.abc import MutableMapping, Collection, Sequence
	from PIL.Image import Image

#FIXME! Section names should not be here - we need to rewrite to_info_fields to make more sense, it's just to make sure a circular import doesn't happen
#to_info_fields should probably be in desktop_files
_info_section_name = 'Game Info'
_junk_section_name = 'Junk'
_image_section_name = 'Images'
_name_section_name = 'Names'
_document_section_name = 'Documents'
_description_section_name = 'Descriptions'

class Date():
	"""Class to hold a maybe-incorrect/maybe-guessed/maybe-incomplete date, but I thought MaybeIncompleteMaybeGuessedDate was a bit too much of a mouthful and I'm not clever enough to know what else to call it"""
	def __init__(self, year: Union[int, str, None]=None, month: Union[int, str, None]=None, day: Union[int, str, None]=None, is_guessed: bool=False) -> None:
		self.year = str(year) if year else None
		self.month = str(month) if month else None
		self.day = str(day) if day else None
		self.is_guessed = is_guessed

	@property
	def is_partly_unknown(self) -> bool:
		"""If any component of this date is unknown"""
		if not self.month:
			return True
		if not self.day:
			return True
		if not self.year:
			return True
		#pylint: disable=unsupported-membership-test #Seems to be unaware that I have already tested them to not be None, so actually they do… just leave this one to the type checkers, buddy
		return 'x' in self.year or 'x' in self.month or 'x' in self.day or '?' in self.year or '?' in self.month or '?' in self.day
	
	def is_better_than(self, other_date: 'Date | None') -> bool:
		"""Is other_date guessed or only partially known, while this one isn't"""
		if not other_date:
			return True
		if other_date.is_guessed and not self.is_guessed:
			return True
		if (other_date.is_partly_unknown and not self.is_partly_unknown) and not self.is_guessed:
			return True

		return False

	def __str__(self) -> str:
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

class GameInfo():
	def __init__(self) -> None:
		self.platform: str | None = None
		self.categories: 'Sequence[str]' = [] #TODO: I kinda want this to be a union with Sequence | str | None, if we can do that
		self.release_date: Date | None = None
		self.emulator_name: str | None = None #TODO: Begone with this, if we are doing things correctly, or rather once we are, make_linux_desktop will set it automatically to whatever Runner object is used

		self.genre: str | None = None
		self.subgenre: str | None = None
		self.languages: 'Collection[Language]' = set() #TODO: Should this be mutable?
		self.developer: 'str | Collection[str] | None' = None
		self.publisher: 'str | Collection[str] | None' = None
		self.save_type: SaveType = SaveType.Unknown
		self.product_code: str | None = None
		self.regions: 'Collection[Region]' = set() #TODO: Should this be mutable?
		self.media_type: MediaType | None = None
		self.notes: str | None = None
		self.disc_number: int | None = None
		self.disc_total: int | None = None
		self.series: 'str | Collection[str] | None' = None
		self.series_index: Union[str, int, None] = None

		self.input_info = InputInfo() #hmm…

		self.specific_info: 'MutableMapping[str, Any]' = {} #Stuff that's too specific to put as an attribute here

		self.images: 'MutableMapping[str, Path | Image]' = {}
		#TODO: The override name shenanigans in Wii/PSP: Check for name = None in launchers, and set name = None if overriding it to something else, and put the overriden name in here
		self.names: 'MutableMapping[str, str]' = {}
		self.documents: 'MutableMapping[str, str | Path]' = {} #Paths of either variety, or URLs
		self.descriptions: 'MutableMapping[str, str]' = {}

	def add_alternate_name(self, name: str, field: str='Alternate Name') -> None:
		if field in self.names:
			self.names[field + ' 1'] = self.names[field]
			self.names[field + ' 2'] = name
			self.names.pop(field)
			return
		if field + ' 1' in self.names:
			i = 2
			while f'{field} {i}' in self.names:
				i += 1
			self.names[f'{field} {i}'] = name
			return
		self.names[field] = name

	def add_notes(self, notes: str | None) -> None:
		if not notes:
			return
		if not self.notes:
			self.notes = notes
		elif self.notes != notes:
			self.notes += ';' + notes

	def to_launcher_fields(self) -> 'MutableMapping[str, MutableMapping[str, Any]]':
		fields: 'MutableMapping[str, MutableMapping[str, Any]]' = {}

		info_fields: 'MutableMapping[str, Any]' = {
			'Genre': self.genre,
			'Subgenre': self.subgenre,
			'Languages': tuple(language.native_name for language in self.languages),
			'Release Date': self.release_date,
			'Emulator': self.emulator_name,
			'Categories': self.categories,
			'Platform': self.platform,
			'Save Type': 'Memory Card' if self.save_type == SaveType.MemoryCard else self.save_type.name,
			'Publisher': self.publisher,
			'Developer': self.developer,
			'Product Code': self.product_code,
			'Regions': tuple(region.name for region in self.regions),
			'Media Type': ('Optical Disc' if self.media_type == MediaType.OpticalDisc else self.media_type.name) if self.media_type else None,
			'Notes': self.notes,
			'Disc Number': self.disc_number,
			'Disc Total': self.disc_total,
			'Series': self.series,
			'Series Index': self.series_index,
		}
		if self.release_date and self.release_date.year:
			info_fields['Year'] = self.release_date.year + '?' if self.release_date.is_guessed else self.release_date.year
		if self.input_info.is_inited:
			info_fields['Standard Input'] = self.input_info.has_standard_inputs
			info_fields['Input Methods'] = self.input_info.describe()

		info_fields.update(self.specific_info)

		fields[_info_section_name] = info_fields
		fields[_junk_section_name] = {}

		if self.images:
			fields[_image_section_name] = {}
			for k, image in self.images.items():
				fields[_image_section_name][k] = image
		
		if self.names:
			fields[_name_section_name] = {}
			for k, name in self.names.items():
				fields[_name_section_name][k] = name
			
		if self.documents:
			fields[_document_section_name] = {}
			for k, document in self.documents.items():
				fields[_document_section_name][k] = document

		if self.descriptions:
			fields[_description_section_name] = {}
			for k, description in self.descriptions.items():
				fields[_description_section_name][k] = description

		return fields
