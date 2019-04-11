#For autodetecting regions, languages, etc from filenames
#It's okay for a region to have None for its language if you can't make a reasonable assumption about the language
#For my own reference: Refer to http://www.bubblevision.com/PAL-NTSC.htm https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes to add new regions/languages that might end up needing to be here

from enum import Enum, auto
class TVSystem(Enum):
	NTSC = auto()
	PAL = auto()
	Agnostic = auto()

class Language():
	def __init__(self, english_name, native_name, short_code):
		self.english_name = english_name
		self.native_name = native_name
		self.short_code = short_code

	def __str__(self):
		return '{0} ({1}) ({2})'.format(self.native_name, self.english_name, self.short_code)

	def __repr__(self):
		return 'Language({1!r}, {0!r}, {2!r})'.format(self.native_name, self.english_name, self.short_code)


class Region():
	def __init__(self, name, short_code, tv_system, language):
		self.name = name
		self.short_code = short_code
		self.tv_system = tv_system
		self.language = language

	def __str__(self):
		return '{0} ({1}) ({2}) ({3})'.format(self.name, self.short_code, self.tv_system, self.language)

	def __repr__(self):
		return 'Region({0!r}, {1!r}, {2!r}, {3!r})'.format(self.name, self.short_code, self.tv_system, self.language)

languages = [
	#These languages are specified in the No-Intro convention as being in this order, in case that ends up mattering:
	Language('English', 'English', 'En'),
	Language('Japanese', '日本語', 'Ja'),
	Language('French', 'Français', 'Fr'),
	Language('German', 'Deutsch', 'De'),
	Language('Spanish', 'Español', 'Es'),
	Language('Italian', 'Italiano', 'It'),
	Language('Dutch', 'Nederlands', 'Nl'),
	Language('Portuguese', 'Português', 'Pt'),
	Language('Swedish', 'Svenska', 'Sv'),
	Language('Norwegian', 'Norsk', 'No'),
	Language('Danish', 'Dansk', 'Da'),
	Language('Finnish', 'Suomi', 'Fi'),
	Language('Chinese', '中文', 'Zh'),
	Language('Korean', '한국인', 'Ko'),
	Language('Polish', 'Polski', 'Pl'),

	Language('Russian', 'Pусский', 'Ru'),
	Language('Greek', 'ελληνικά', 'El'),
	Language('Indonesian', 'Bahasa Indonesia', 'In'),
	Language('Turkish', 'Türkçe', 'Tr'),
	Language('Czech', 'Čeština', 'Cs'),
	Language('Arabic', 'العربية', 'Ar'),
	Language('Catalan', 'Català', 'Ca'),
	Language('Hungarian', 'Magyar', 'Hu'),
	Language('Romanian', 'Română', 'Ro'),
	Language('Croatian', 'Hrvatski jezik', 'Hr'),
	Language('Slovak', 'Slovenčina', 'Sk'),
	Language('Thai', 'ไทย', 'Th'),
	Language('Bulgarian', 'български език', 'Bg'),
	Language('Ukrainian', 'Українська', 'Uk'),
	Language('Vietnamese', 'Tiếng Việt', 'Vn'),

	Language('Traditional Chinese', '漢語', None),
	#Dialects of other languages where different translations exist
	Language('Brazilian Portguese', 'Português do Brasil', None),
	Language('Latin American Spanish', 'Español-Latinoamérica', None),
]

regions = [
	Region('Argentina', 'AR', TVSystem.PAL, 'Spanish'),
	Region('Asia', 'AS', None, None), #No-Intro filenames using this as a region seem to always mean East Asia specifically, although that's still a lot of countries so it doesn't mean much
	Region('Australia', 'AU', TVSystem.PAL, 'English'),
	Region('Brazil', 'BR', TVSystem.NTSC, 'Brazilian Portguese'), #Uses PAL-M actually, but we'll call it NTSC because it's 60Hz
	Region('Bulgaria', 'BG', TVSystem.PAL, 'Bulgarian'),
	Region('Canada', 'CA', TVSystem.NTSC, 'French'), #Filenames tagged as (Canada) specifically indicate French, as (USA) is used to mean North America i.e. USA + Canada even though that seems a bit wrong
	Region('China', 'CN', TVSystem.PAL, 'Chinese'),
	Region('Czech Republic', 'CZ', TVSystem.PAL, 'Czech'),
	Region('Denmark', 'DK', TVSystem.PAL, 'Danish'),
	Region('Europe', 'EU', TVSystem.PAL, 'English'),
	#Actually could be any number of languages, but in filenames (by No-Intro's convention anyway) it's assumed to be English unless otherwise specified
	Region('Finland', 'FI', TVSystem.PAL, 'Finnish'),
	Region('France', 'FR', TVSystem.PAL, 'French'), #Uses SECAM actually, but we'll call it PAL because it's 50Hz
	Region('Germany', 'DE', TVSystem.PAL, 'German'),
	Region('Greece', 'GR', TVSystem.PAL, 'Greek'),
	Region('Hong Kong', 'HK', TVSystem.PAL, 'Traditional Chinese'), #Seems to always be Chinese for video game purposes, although English is also a national language
	Region('Indonesia', 'ID', TVSystem.PAL, 'Indonesian'),
	Region('Italy', 'IT', TVSystem.PAL, 'Italian'),
	Region('Japan', 'JP', TVSystem.NTSC, 'Japanese'),
	Region('Korea', 'KR', TVSystem.NTSC, 'Korean'),
	#For the purpose of video games, we can assume South Korea is the only Korea and North Korea doesn't exist. Oof, that sounds horrible, doesn't it? (If North Korea ever does have games, they use PAL)
	Region('Netherlands', 'NL', TVSystem.PAL, 'Dutch'),
	Region('Norway', 'NO', TVSystem.PAL, 'Norwegian'),
	Region('Poland', 'PL', TVSystem.PAL, 'Polish'),
	Region('Portugal', 'PT', TVSystem.PAL, 'Portugese'),
	Region('Russia', 'RU', TVSystem.PAL, 'Russian'),
	Region('Spain', 'ES', TVSystem.PAL, 'Spanish'),
	Region('Sweden', 'SE', TVSystem.PAL, 'Swedish'),
	Region('Taiwan', 'TW', TVSystem.NTSC, 'Traditional Chinese'),
	Region('Thailand', 'TH', TVSystem.PAL, 'Thai'),
	Region('Turkey', 'TR', TVSystem.PAL, 'Turkish'),
	Region('UK', 'GB', TVSystem.PAL, 'English'),
	Region('Ukraine', 'UA', TVSystem.PAL, 'Ukrainian'),
	Region('USA', 'US', TVSystem.NTSC, 'English'),

	Region('World', None, TVSystem.Agnostic, None),
	#Though it's probably in English; No-Intro uses this as shorthand for (Japan, USA, Europe) because nobody told them that's not the only three regions in the world. It is safe to say that anything released in those three regions would indeed need to be TV-agnostic though
]
