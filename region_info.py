#For autodetecting regions, languages, etc from filenames
#It's okay for a region to have None for its language if you can't make a reasonable assumption about the language
#For my own reference: Refer to http://www.bubblevision.com/PAL-NTSC.htm https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes to add new regions/languages that might end up needing to be here

from enum import Enum, auto
class TVSystem(Enum):
	NTSC = auto()
	PAL = auto()
	Agnostic = auto()
	Indeterminate = auto()

class Language():
	def __init__(self, english_name, native_name, short_code):
		self.english_name = english_name
		self.native_name = native_name
		self.short_code = short_code

class Region():
	def __init__(self, name, short_code, tv_system, language):
		self.name = name
		self.short_code = short_code
		self.tv_system = tv_system
		self.language = language

languages = [
	#These languages are specified in the No-Intro convention as being in this order, in case that ends up mattering:
	Language('English', 'English', 'En'),
	Language('Japanese', '日本語', 'Ja'),
	Language('French', 'Français', 'Fr'),
	Language('German', 'Deutsch', 'De'),
	Language('Spanish', 'Español', 'Es'),
	Language('Italian', 'Italiano', 'It'),
	Language('Dutch', 'Nederlands', 'Nl'),
	Language('Portugese', 'Português', 'Pt'),
	Language('Swedish', 'Svenska', 'Sv'),
	Language('Norwegian', 'Norsk', 'No'),
	Language('Danish', 'Dansk', 'Da'),
	Language('Finnish', 'Suomi', 'Fi'),
	Language('Chinese', '中文', 'Zh'),
	Language('Korean', '한국인', 'Ko'),
	Language('Polish', 'Polskie', 'Pl'),
	
	Language('Russian', 'Pусский', 'Ru'),
	Language('Greek', 'ελληνικά', 'El'),
]

regions = [
	Region('Asia', 'AS', TVSystem.Indeterminate, None),
	Region('Australia', 'AU', TVSystem.PAL, 'English'),
	Region('Brazil', 'BR', TVSystem.NTSC, 'Portugese'),
	Region('Canada', 'CA', TVSystem.NTSC, None), #Might have English or French
	Region('China', 'CN', TVSystem.PAL, 'Chinese'),
	Region('Denmark', 'DK', TVSystem.PAL, 'Danish'),
	Region('Europe', 'EU', TVSystem.PAL, 'English'), #Actually could be any number of languages, but in filenames (by No-Intro's convention anyway) it's assumed to be English unless otherwise specified
	Region('Finland', 'FI', TVSystem.PAL, 'Finnish'),
	Region('France', 'FR', TVSystem.PAL, 'French'),
	Region('Germany', 'DE', TVSystem.PAL, 'German'),
	Region('Greece', 'GR', TVSystem.PAL, 'Greek'),
	Region('Hong Kong', 'HK', TVSystem.PAL, None), #Might have Chinese or English
	Region('Italy', 'IT', TVSystem.PAL, 'Italian'),
	Region('Japan', 'JP', TVSystem.NTSC, 'Japanese'),
	Region('Korea', 'KR', TVSystem.NTSC, 'Korean'), #For the purpose of video games, we can assume South Korea is the only Korea and North Korea doesn't exist. Oof, that sounds horrible, doesn't it? (If North Korea ever does have games, they use PAL)
	Region('Netherlands', 'NL', TVSystem.PAL, 'Dutch'),
	Region('Norway', 'NO', TVSystem.PAL, 'Norwegian'),
	Region('Poland', 'PL', TVSystem.PAL, 'Polish'),
	Region('Portugal', 'PT', TVSystem.PAL, 'Portugese'),
	Region('Russia', 'RU', TVSystem.PAL, 'Russian'),
	Region('Spain', 'ES', TVSystem.PAL, 'Spanish'),
	Region('Sweden', 'SE', TVSystem.PAL, 'Swedish'),
	Region('Taiwan', 'TW', TVSystem.NTSC, 'Chinese'),
	Region('UK', 'GB', TVSystem.PAL, 'English'),
	Region('USA', 'US', TVSystem.NTSC, 'English'),

	Region('World', None, TVSystem.Agnostic, None), 
	#Though it's probably in English; No-Intro uses this as shorthand for (Japan, USA, Europe) because nobody told them that's not the only three regions in the world. It is safe to say that anything released in those three regions would indeed need to be TV-agnostic though
]
