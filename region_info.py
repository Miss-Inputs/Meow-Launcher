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

class Region():
	def __init__(self, name, tv_system, language):
		self.name = name
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
	Region('Australia', TVSystem.PAL, 'English'),
	Region('Brazil', TVSystem.NTSC, 'Portugese'),
	Region('Canada', TVSystem.NTSC, None), #Might have English or French
	Region('China', TVSystem.PAL, 'Chinese'),
	Region('Denmark', TVSystem.PAL, 'Danish'),
	Region('Europe', TVSystem.PAL, 'English'), #Actually could be any number of languages, but in filenames (by No-Intro's convention anyway) it's assumed to be English unless otherwise specified
	Region('Finland', TVSystem.PAL, 'Finnish'),
	Region('France', TVSystem.PAL, 'French'),
	Region('Germany', TVSystem.PAL, 'German'),
	Region('Greece', TVSystem.PAL, 'Greek'),
	Region('Hong Kong', TVSystem.PAL, None), #Might have Chinese or English
	Region('Italy', TVSystem.PAL, 'Italian'),
	Region('Japan', TVSystem.NTSC, 'Japanese'),
	Region('Korea', TVSystem.NTSC, 'Korean'), #For the purpose of video games, we can assume South Korea is the only Korea and North Korea doesn't exist. Oof, that sounds horrible, doesn't it? (If North Korea ever does have games, they use PAL)
	Region('Netherlands', TVSystem.PAL, 'Dutch'),
	Region('Norway', TVSystem.PAL, 'Norwegian'),
	Region('Poland', TVSystem.PAL, 'Polish'),
	Region('Portugal', TVSystem.PAL, 'Portugese'),
	Region('Russia', TVSystem.PAL, 'Russian'),
	Region('Spain', TVSystem.PAL, 'Spanish'),
	Region('Sweden', TVSystem.PAL, 'Swedish'),
	Region('Taiwan', TVSystem.NTSC, 'Chinese'),
	Region('UK', TVSystem.PAL, 'English'),
	Region('USA', TVSystem.NTSC, 'English'),

	Region('World', TVSystem.Agnostic, None), 
	#Though it's probably in English; No-Intro uses this as shorthand for (Japan, USA, Europe) because nobody told them that's not the only three regions in the world. It is safe to say that anything released in those three regions would indeed need to be TV-agnostic though
	
	#(Asia) is interesting too, might be NTSC or PAL but probably not agnostic
]