import statistics
from collections.abc import Iterable, Mapping
from enum import Flag
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
	from meowlauncher.metadata import Metadata

class WiiU3DSRegionCode(Flag):
	Japan = 1
	USA = 2
	Europe = 4
	Australia = 8 #Not used, Europe is used in its place
	China = 16
	Korea = 32
	Taiwan = 64
	RegionFree = 0x7fffffff
	WiiURegionFree = 0xffffffff

def parse_ratings(metadata: 'Metadata', ratings_bytes: bytes, invert_has_rating_bit=False, use_bit_6=True):
	ratings = {}
	for i, rating in enumerate(ratings_bytes):
		has_rating = (rating & 0b1000_0000) == 0 #For 3DS and DSi, the meaning of this bit is inverted
		if invert_has_rating_bit:
			has_rating = not has_rating
		if use_bit_6:
			banned = rating & 0b0100_0000 #Seems to only mean this for Wii (MadWorld (Europe) has this bit set for Germany rating); on Wii U it seems to be "this rating is unused" and 3DS and DSi I dunno but it probably doesn't work that way
		else:
			banned = False
		#Bit 5 I'm not even sure about (on Wii it seems to be "includes online interactivity"), but we can ignore it
		#The last 4 bits are the actual rating
		if has_rating and not banned:
			ratings[i] = rating & 0b0001_1111

	if 0 in ratings:
		metadata.specific_info['CERO Rating'] = ratings[0]
	if 1 in ratings:
		metadata.specific_info['ESRB Rating'] = ratings[1]
	if 3 in ratings:
		metadata.specific_info['USK Rating'] = ratings[3]
	if 4 in ratings:
		metadata.specific_info['PEGI Rating'] = ratings[4]
	if 8 in ratings:
		metadata.specific_info['AGCB Rating'] = ratings[8]
	if 9 in ratings:
		metadata.specific_info['GRB Rating'] = ratings[9]
	#There are others but that will do for now

	ratings_list = set(ratings.values())
	if not ratings_list:
		return

	#If there is only one rating or they are all the same, this covers that; otherwise if ratings boards disagree this is probably the best way to interpret that situation
	try:
		rating = statistics.mode(ratings_list)
	except statistics.StatisticsError:
		rating = max(ratings_list)

	metadata.specific_info['Age Rating'] = rating

def add_info_from_local_titles(metadata: 'Metadata', short_titles: Mapping[str, str], long_titles: Mapping[str, str], publishers: Mapping[str, Optional[str]], region_codes: Iterable[WiiU3DSRegionCode]):
	local_short_title = None
	local_long_title = None
	local_publisher: Optional[str] = None
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
		local_short_title = short_titles.get('Simplified Chinese')
		local_long_title = long_titles.get('Simplified Chinese')
		local_publisher = publishers.get('Simplified Chinese')
	elif WiiU3DSRegionCode.Korea in region_codes:
		local_short_title = short_titles.get('Korean')
		local_long_title = long_titles.get('Korean')
		local_publisher = publishers.get('Korean')
	elif WiiU3DSRegionCode.Taiwan in region_codes:
		local_short_title = short_titles.get('Traditional Chinese')
		local_long_title = long_titles.get('Traditional Chinese')
		local_publisher = publishers.get('Traditional Chinese')
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
			metadata.add_alternate_name(localized_short_title, '{0} Banner Short Title'.format(lang.replace(' ', '-')))
	for lang, localized_long_title in long_titles.items():
		if localized_long_title != local_long_title:
			metadata.add_alternate_name(localized_long_title, '{0} Banner Title'.format(lang.replace(' ', '-')))
	for lang, localized_publisher in publishers.items():
		if localized_publisher not in (metadata.publisher, local_publisher):
			metadata.specific_info[f"{lang} Publisher"] = localized_publisher
