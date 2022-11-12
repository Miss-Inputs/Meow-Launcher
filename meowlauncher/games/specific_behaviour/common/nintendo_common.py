import statistics
from collections.abc import Collection, Mapping, Sequence
from enum import Enum, IntFlag, auto
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
	from meowlauncher.info import GameInfo

class WiiU3DSRegionCode(IntFlag):
	Japan = 1
	USA = 2
	Europe = 4
	Australia = 8 #Not used, Europe is used in its place
	China = 16
	Korea = 32
	Taiwan = 64
	RegionFree = 0x7fffffff
	WiiURegionFree = 0xffffffff

class NintendoAgeRatingBytes(NamedTuple):
	CERO: int
	ESRB: int
	ReservedRating3: int #The relative ordering in Wii U XMLs could indicate this is BBFC
	USK: int
	PEGI: int
	PEGIFinland: int #In Wii games, this is possibly FBFC?
	PEGIPortugal: int
	PEGIUK: int
	AGCB: int
	GRB: int
	CGSRR: int #3DS only?
	ReservedRating12: int
	ReservedRating13: int
	ReservedRating14: int
	ReservedRating15: int

class AgeRatingStatus(Enum):
	Missing = auto()
	Banned = auto()
	RatingPending = auto()
	Present = auto()
	NoAgeRestriction = auto()

class NintendoAgeRatings():
	def __init__(self, ratings_bytes: Sequence[int]) -> None:
		self.bytes = ratings_bytes
	
	@staticmethod
	def _get_rating_status(byte: int) -> AgeRatingStatus:
		if byte & 0b1000_0000:
			return AgeRatingStatus.Missing
		return AgeRatingStatus.Present

	@staticmethod
	def _get_rating_value(byte: int) -> int:
		return byte & 0b0001_1111

	def get_rating(self, index: int) -> int | AgeRatingStatus | None:
		byte = self.bytes[index]
		status = self._get_rating_status(byte)
		if status == AgeRatingStatus.Present:
			return byte
		if status == AgeRatingStatus.Missing:
			return None
		return status

	@property
	def all_present_ratings(self) -> Collection[int | AgeRatingStatus]:
		return [b if status == AgeRatingStatus.Present else status for b, status in ((b, self._get_rating_status(b)) for b in self.bytes) if status != AgeRatingStatus.Missing]

	@property
	def common_rating(self) -> int | AgeRatingStatus | None:
		'If there is only one rating or they are all the same, this covers that; otherwise if ratings boards disagree this is probably the best way to interpret that situation'
		all_present_ratings = self.all_present_ratings
		try:
			return statistics.mode(all_present_ratings)
		except statistics.StatisticsError:
			try:
				return max(b for b in all_present_ratings if isinstance(b, int))
			except ValueError:
				return None

	def __getitem__(self, index: int)  -> int | AgeRatingStatus | None:
		byte = self.bytes[index]
		status = self._get_rating_status(byte)
		if status == AgeRatingStatus.Present:
			return byte
		if status == AgeRatingStatus.Missing:
			return None
		return status

class DSi3DSAgeRatings(NintendoAgeRatings):
	@staticmethod
	def _get_rating_status(byte: int) -> AgeRatingStatus:
		#For some reason it is inverted
		if byte & 0b1000_0000:
			return AgeRatingStatus.Present
		if byte & 0b0100_0000:
			return AgeRatingStatus.RatingPending
		return AgeRatingStatus.Missing

def add_ratings_info(metadata: 'GameInfo', ratings: NintendoAgeRatings) -> None:
	metadata.specific_info['CERO Rating'] = ratings[0]
	metadata.specific_info['ESRB Rating'] = ratings[1]
	metadata.specific_info['USK Rating'] = ratings[3]
	metadata.specific_info['PEGI Rating'] = ratings[4]
	metadata.specific_info['AGCB Rating'] = ratings[8]
	metadata.specific_info['GRB Rating'] = ratings[9]
	#There are others but that will do for now

	metadata.specific_info['Age Rating'] = ratings.common_rating

def add_info_from_local_titles(metadata: 'GameInfo', short_titles: Mapping[str, str], long_titles: Mapping[str, str], publishers: Mapping[str, str | None], region_codes: Collection[WiiU3DSRegionCode]) -> None:
	local_short_title = None
	local_long_title = None
	local_publisher: str | None = None
	if WiiU3DSRegionCode.RegionFree in region_codes or WiiU3DSRegionCode.USA in region_codes or WiiU3DSRegionCode.Europe in region_codes:
		#We shouldn't assume that Europe is English-speaking but we're going to
		local_short_title = short_titles.get('English')
		local_long_title = long_titles.get('English')
		local_publisher = publishers.get('English')
	elif WiiU3DSRegionCode.Japan in region_codes:
		local_short_title = short_titles.get('Japanese')
		local_long_title = long_titles.get('Japanese')
		local_publisher = publishers.get('Japanese')
	elif WiiU3DSRegionCode.China in region_codes:
		local_short_title = short_titles.get('Chinese (Simplified)')
		local_long_title = long_titles.get('Chinese (Simplified)')
		local_publisher = publishers.get('Chinese (Simplified)')
	elif WiiU3DSRegionCode.Korea in region_codes:
		local_short_title = short_titles.get('Korean')
		local_long_title = long_titles.get('Korean')
		local_publisher = publishers.get('Korean')
	elif WiiU3DSRegionCode.Taiwan in region_codes:
		local_short_title = short_titles.get('Chinese (Traditional)')
		local_long_title = long_titles.get('Chinese (Traditional)')
		local_publisher = publishers.get('Chinese (Traditional)')
	else: #If none of that is in the region code? Unlikely but I dunno maybe
		if short_titles:
			local_short_title = next(iter(short_titles.values()))
		if long_titles:
			local_long_title = next(iter(long_titles.values()))
		if publishers:
			local_publisher = next(iter(publishers.values()))

	if local_short_title:
		metadata.add_alternate_name(local_short_title, 'Banner Short Title')
	if local_long_title:
		metadata.add_alternate_name(local_long_title, 'Banner Title')
	if local_publisher and not metadata.publisher:
		metadata.publisher = local_publisher

	for lang, localized_short_title in short_titles.items():
		if localized_short_title != local_short_title:
			metadata.add_alternate_name(localized_short_title, f'{lang} Banner Short Title')
	for lang, localized_long_title in long_titles.items():
		if localized_long_title != local_long_title:
			metadata.add_alternate_name(localized_long_title, f'{lang} Banner Title')
	for lang, localized_publisher in publishers.items():
		if localized_publisher not in (metadata.publisher, local_publisher):
			metadata.specific_info[f'{lang} Publisher'] = localized_publisher
