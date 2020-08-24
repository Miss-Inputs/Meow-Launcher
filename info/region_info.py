#For autodetecting regions, languages, etc from filenames
#It's okay for a region to have None for its language if you can't make a reasonable assumption about the language
#For my own reference: Refer to http://www.bubblevision.com/PAL-NTSC.htm https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2 to add new regions/languages that might end up needing to be here

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
		self.language = language #This is just a singular language that can be inferred from software being released in this region, if zero or more than one language can be inferred it is left as none

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

	Language('Albanian', 'Shqip', 'Sq'),
	Language('Arabic', 'العربية', 'Ar'),
	Language('Bengali', 'বাংলা', 'Bn'),
	Language('Bulgarian', 'български език', 'Bg'),
	Language('Burmese', 'ဗမာစာ', 'My'),
	Language('Catalan', 'Català', 'Ca'),
	Language('Croatian', 'Hrvatski jezik', 'Hr'),
	Language('Czech', 'Čeština', 'Cs'),
	Language('Greek', 'ελληνικά', 'El'),
	Language('Hebrew', 'עברית', 'He'),
	Language('Hindi', 'हिन्दी', 'Hi'),
	Language('Hungarian', 'Magyar', 'Hu'),
	Language('Icelandic', 'Íslenska', 'Is'),
	Language('Indonesian', 'Bahasa Indonesia', 'In'),
	Language('Khmer', 'ភាសាខ្មែរ', 'Km'),
	Language('Lao', 'ພາສາລາວ', 'Lo'),
	Language('Malay', 'Bahasa Melayu', 'Ms'),
	Language('Mongolian', 'Монгол хэл', 'Mn'),
	Language('Persian', 'فارسی', 'Fa'),
	Language('Romanian', 'Română', 'Ro'),
	Language('Russian', 'Pусский', 'Ru'),
	Language('Serbian', 'српски језик', 'Sr'),
	Language('Slovak', 'Slovenčina', 'Sk'),
	Language('Swahili', 'Kiswahili', 'Sw'),
	Language('Thai', 'ไทย', 'Th'),
	Language('Turkish', 'Türkçe', 'Tr'),
	Language('Ukrainian', 'Українська', 'Uk'),
	Language('Vietnamese', 'Tiếng Việt', 'Vn'),

	Language('Traditional Chinese', '漢語', 'Zh-Hant'),
	#Dialects of other languages, where there's something that specifies it's that dialect specifically (Steam games do this, for example)
	Language('Brazilian Portguese', 'Português do Brasil', 'Pt-Br'),
	Language('Latin American Spanish', 'Español-Latinoamérica', 'Es-La'), #Actually I have never seen "Es-La" be used ever, I'm just assuming it would be
]

regions = [
	Region('Afghanistan', 'AF', TVSystem.PAL, None),
	Region('Albania', 'AL', TVSystem.PAL, 'Albanian'),
	Region('Algeria', 'DZ', TVSystem.PAL, 'Arabic'),
	Region('Andorra', 'AD', TVSystem.PAL, 'Catalan'),
	Region('Antigua', 'AG', TVSystem.NTSC, 'English'),
	Region('Argentina', 'AR', TVSystem.PAL, 'Spanish'),
	Region('Aruba', 'AW', TVSystem.NTSC, 'Dutch'),
	Region('Asia', 'AS', None, None), #No-Intro filenames using this as a region seem to always mean East Asia specifically, although that's still a lot of countries so it doesn't mean much
	Region('Australia', 'AU', TVSystem.PAL, 'English'),
	Region('Austria', 'AT', TVSystem.PAL, 'German'),
	Region('Bahamas', 'BS', TVSystem.NTSC, 'English'),
	Region('Bahrain', 'BH', TVSystem.PAL, 'Arabic'),
	Region('Bangladesh', 'BD', TVSystem.PAL, 'Bengali'),
	Region('Barbados', 'BB', TVSystem.NTSC, 'English'),
	Region('Belgium', 'BE', TVSystem.PAL, None),
	Region('Belize', 'BZ', TVSystem.NTSC, None),
	Region('Benin', 'BJ', TVSystem.PAL, 'French'),
	Region('Bermuda', 'BM', TVSystem.NTSC, 'English'),
	Region('Bolivia', 'BO', TVSystem.NTSC, 'Spanish'),
	Region('Botswana', 'BW', TVSystem.PAL, None),
	Region('Brazil', 'BR', TVSystem.NTSC, 'Brazilian Portguese'), #Uses PAL-M actually, but we'll call it NTSC because it's 60Hz
	Region('British Virgin Islands', 'VG', TVSystem.NTSC, 'English'),
	Region('Brunei', 'BN', TVSystem.PAL, 'Malay'),
	Region('Bulgaria', 'BG', TVSystem.PAL, 'Bulgarian'),
	Region('Burkina Faso', 'BF', TVSystem.PAL, None),
	Region('Burundi', 'BI', TVSystem.PAL, None),
	Region('Cambodia', 'KH', TVSystem.NTSC, 'Khmer'),
	Region('Cameroon', 'CM', TVSystem.PAL, None),
	Region('Canada', 'CA', TVSystem.NTSC, 'French'), #Filenames tagged as (Canada) specifically indicate French, as (USA) is used to mean North America i.e. USA + Canada even though that seems a bit wrong
	Region('Cayman Islands', 'KY', TVSystem.NTSC, 'English'),
	Region('Chad', 'TD', TVSystem.PAL, None),
	Region('Chile', 'CL', TVSystem.NTSC, 'Spanish'),
	Region('China', 'CN', TVSystem.PAL, 'Chinese'),
	Region('Colombia', 'CO', TVSystem.NTSC, 'Spanish'),
	Region('Congo', 'CG', TVSystem.PAL, None),
	Region('Costa Rica', 'CR', TVSystem.NTSC, 'Spanish'),
	Region('Cuba', 'CU', TVSystem.NTSC, 'Spanish'),
	Region('Curaçao', 'CW', TVSystem.NTSC, None),
	Region('Cyprus', 'CY', TVSystem.PAL, None),
	Region('Czech Republic', 'CZ', TVSystem.PAL, 'Czech'),
	Region('Democratic Republic of the Congo', 'CD', TVSystem.PAL, None),
	Region('Denmark', 'DK', TVSystem.PAL, 'Danish'),
	Region('Djibouti', 'DJ', TVSystem.PAL, None),
	Region('Dominician Republic', 'DO', TVSystem.NTSC, 'Spanish'),
	Region('Ecuador', 'EC', TVSystem.NTSC, 'Spanish'),
	Region('Egypt', 'EG', TVSystem.PAL, 'Arabic'),
	Region('El Salvador', 'SV', TVSystem.NTSC, 'Spanish'),
	Region('Equatorial Guinea', 'GQ', TVSystem.PAL, None),
	Region('Eswatini', 'SZ', TVSystem.PAL, None),
	Region('Ethiopia', 'ET', TVSystem.PAL, None),
	Region('Europe', 'EU', TVSystem.PAL, 'English'), #Actually could be any number of languages, but in filenames (by No-Intro's convention anyway) it's assumed to be English unless otherwise specified
	Region('Falkland Islands', 'FK', TVSystem.PAL, 'English'),
	Region('Faroe Islands', 'FO', TVSystem.PAL, None),
	Region('Fiji', 'FJ', TVSystem.NTSC, None),
	Region('Finland', 'FI', TVSystem.PAL, 'Finnish'),
	Region('France', 'FR', TVSystem.PAL, 'French'), #Uses SECAM actually, but we'll call it PAL because it's 50Hz
	Region('French Polynesia', 'PF', TVSystem.PAL, 'French'),
	Region('Gabon', 'GA', TVSystem.PAL, 'French'),
	Region('Germany', 'DE', TVSystem.PAL, 'German'),
	Region('Ghana', 'GH', TVSystem.PAL, 'English'),
	Region('Gibraltar', 'GI', TVSystem.PAL, 'English'),
	Region('Greece', 'GR', TVSystem.PAL, 'Greek'),
	Region('Greenland', 'GL', TVSystem.PAL, None),
	Region('Guadeloupe', 'GP', TVSystem.PAL, 'French'),
	Region('Guam', 'GU', TVSystem.NTSC, 'English'),
	Region('Guatemala', 'GT', TVSystem.NTSC, 'Spanish'),
	Region('Guinea', 'GN', TVSystem.PAL, 'French'),
	Region('Guyana', 'GY', TVSystem.NTSC, 'English'),
	Region('Haiti', 'HT', TVSystem.PAL, 'French'),
	Region('Honduras', 'HN', TVSystem.NTSC, 'Spanish'),
	Region('Hong Kong', 'HK', TVSystem.PAL, 'Traditional Chinese'), #Seems to always be Chinese for video game purposes, although English is also a national language
	Region('Hungary', 'HU', TVSystem.PAL, 'Hungarian'),
	Region('Iceland', 'IS', TVSystem.PAL, 'Icelandic'),
	Region('India', 'IN', TVSystem.PAL, 'Hindi'),
	Region('Indonesia', 'ID', TVSystem.PAL, 'Indonesian'),
	Region('Iran', 'IR', TVSystem.PAL, 'Persian'),
	Region('Iraq', 'IQ', TVSystem.PAL, None),
	Region('Ireland', 'IE', TVSystem.PAL, None),
	Region('Israel', 'IL', TVSystem.PAL, 'Hebrew'),
	Region('Italy', 'IT', TVSystem.PAL, 'Italian'),
	Region('Ivory Coast', 'CI', TVSystem.PAL, 'French'),
	Region('Jamaica', 'JM', TVSystem.NTSC, 'English'),
	Region('Japan', 'JP', TVSystem.NTSC, 'Japanese'),
	Region('Jordan', 'JO', TVSystem.PAL, 'Arabic'),
	Region('Kenya', 'KE', TVSystem.PAL, 'Swahili'),
	Region('Korea', 'KR', TVSystem.NTSC, 'Korean'), #South Korea specifically, but we're calling it just Korea because that's how it's used in the No-Intro convention
	Region('Kuwait', 'KW', TVSystem.PAL, 'Arabic'),
	Region('Laos', 'LA', TVSystem.PAL, 'Lao'),
	Region('Lebanon', 'LB', TVSystem.PAL, 'Arabic'),
	Region('Lesotho', 'LS', TVSystem.PAL, None),
	Region('Liberia', 'LR', TVSystem.PAL, 'English'),
	Region('Libya', 'LY', TVSystem.PAL, 'Arabic'),
	Region('Liechtenstein', 'LI', TVSystem.PAL, 'German'),
	Region('Luxembourg', 'LU', TVSystem.PAL, None),
	Region('Macau', 'MO', TVSystem.PAL, None),
	Region('Madagascar', 'MG', TVSystem.PAL, None),
	Region('Malaysia', 'MY', TVSystem.PAL, 'Malay'),
	Region('Maldives', 'MV', TVSystem.PAL, None),
	Region('Mali', 'ML', TVSystem.PAL, 'French'),
	Region('Malta', 'MT', TVSystem.PAL, None),
	Region('Mariana Islands', 'MP', TVSystem.NTSC, None),
	Region('Martinique', 'MQ', TVSystem.PAL, 'French'),
	Region('Mauritania', 'MR', TVSystem.PAL, 'Arabic'),
	Region('Mauritius', 'MU', TVSystem.PAL, None),
	Region('Mayotte', 'YT', TVSystem.PAL, 'French'),
	Region('Mexico', 'MX', TVSystem.NTSC, 'Latin American Spanish'),
	Region('Micronesia', 'FM', TVSystem.NTSC, 'English'),
	Region('Monaco', 'MC', TVSystem.PAL, 'French'),
	Region('Mongolia', 'MN', TVSystem.PAL, 'Mongolian'),
	Region('Montenegro', 'ME', TVSystem.PAL, None),
	Region('Montserrat', 'MS', TVSystem.NTSC, 'English'),
	Region('Morocco', 'MA', TVSystem.PAL, None),
	Region('Mozambique', 'MZ', TVSystem.PAL, 'Portugese'),
	Region('Myanmar', 'MM', TVSystem.NTSC, 'Burmese'),
	Region('Nepal', 'NP', TVSystem.PAL, None),
	Region('Netherlands', 'NL', TVSystem.PAL, 'Dutch'),
	Region('New Caledonia', 'NC', TVSystem.PAL, 'French'),
	Region('New Zealand', 'NZ', TVSystem.PAL, 'English'),
	Region('Nicaragua', 'NI', TVSystem.NTSC, None),
	Region('Nigeria', 'NG', TVSystem.PAL, 'English'),
	Region('Niger', 'NE', TVSystem.PAL, 'French'),
	Region('North Korea', 'KP', TVSystem.PAL, 'Korean'),
	Region('Norway', 'NO', TVSystem.PAL, 'Norwegian'),
	Region('Oman', 'OM', TVSystem.PAL, 'Arabic'),
	Region('Pakistan', 'PK', TVSystem.PAL, None),
	Region('Panama', 'PA', TVSystem.NTSC, 'Spanish'),
	Region('Papua New Guinea', 'PG', TVSystem.PAL, None),
	Region('Paraguay', 'PY', TVSystem.PAL, None),
	Region('Peru', 'PE', TVSystem.NTSC, 'Spanish'),
	Region('Philippines', 'PH', TVSystem.NTSC, None),
	Region('Poland', 'PL', TVSystem.PAL, 'Polish'),
	Region('Portugal', 'PT', TVSystem.PAL, 'Portugese'),
	Region('Qatar', 'QA', TVSystem.PAL, 'Arabic'),
	Region('Réunion', 'RE', TVSystem.PAL, 'French'),
	Region('Romania', 'RO', TVSystem.PAL, 'Romanian'),
	Region('Russia', 'RU', TVSystem.PAL, 'Russian'),
	Region('Samoa', 'WS', TVSystem.NTSC, None),
	Region('San Marino', 'SM', TVSystem.PAL, 'Italian'),
	Region('São Tomé and Príncipe', 'ST', TVSystem.PAL, 'Portugese'),
	Region('Saudi Arabia', 'SA', TVSystem.PAL, 'Arabic'),
	Region('Scandinavia', None, TVSystem.PAL, None), #This just kinda shows up in filenames sometimes, and it is a region I guess
	Region('Senegal', 'SN', TVSystem.PAL, 'French'),
	Region('Serbia', 'RS', TVSystem.PAL, 'Serbian'),
	Region('Seychelles', 'SC', TVSystem.PAL, None),
	Region('Sierra Leone', 'SL', TVSystem.PAL, 'English'),
	Region('Singapore', 'SG', TVSystem.PAL, None),
	Region('Slovakia', 'SK', TVSystem.PAL, 'Slovak'),
	Region('Somalia', 'SO', TVSystem.PAL, None),
	Region('South Africa', 'ZA', TVSystem.PAL, None),
	Region('Spain', 'ES', TVSystem.PAL, 'Spanish'),
	Region('Sri Lanka', 'LK', TVSystem.PAL, None),
	Region('Sudan', 'SD', TVSystem.PAL, 'Arabic'),
	Region('Suriname', 'SR', TVSystem.NTSC, 'Dutch'),
	Region('Sweden', 'SE', TVSystem.PAL, 'Swedish'),
	Region('Switzerland', 'CH', TVSystem.PAL, None),
	Region('Syria', 'SY', TVSystem.PAL, 'Arabic'),
	Region('Taiwan', 'TW', TVSystem.NTSC, 'Traditional Chinese'),
	Region('Tanzania', 'TZ', TVSystem.PAL, 'Swahili'),
	Region('Thailand', 'TH', TVSystem.PAL, 'Thai'),
	Region('Togo', 'TG', TVSystem.PAL, 'French'),
	Region('Trinidad & Tobago', 'TT', TVSystem.NTSC, 'English'),
	Region('Tunisia', 'TN', TVSystem.PAL, 'Arabic'),
	Region('Turkey', 'TR', TVSystem.PAL, 'Turkish'),
	Region('Uganda', 'UG', TVSystem.PAL, None),
	Region('UK', 'GB', TVSystem.PAL, 'English'),
	Region('Ukraine', 'UA', TVSystem.PAL, 'Ukrainian'),
	Region('United Arab Emirates', 'AE', TVSystem.PAL, 'Arabic'),
	Region('Uruguay', 'UY', TVSystem.PAL, None),
	Region('USA', 'US', TVSystem.NTSC, 'English'),
	Region('US Virgin Islands', 'VI', TVSystem.NTSC, 'English'),
	Region('Vatican City', 'VA', TVSystem.PAL, 'Italian'),
	Region('Venezuela', 'VE', TVSystem.NTSC, 'Spanish'),
	Region('Vietnam', 'VN', TVSystem.PAL, 'Vietnamese'),
	Region('Yemen', 'YE', TVSystem.PAL, 'Arabic'),
	Region('Zambia', 'ZM', TVSystem.PAL, 'English'),
	Region('Zimbabwe', 'ZW', TVSystem.PAL, None),

	Region('World', None, TVSystem.Agnostic, None),
	#Though it's probably in English; No-Intro uses this as shorthand for (Japan, USA, Europe) because nobody told them that's not the only three regions in the world. It is safe to say that anything released in those three regions would indeed need to be TV-agnostic though
]

def get_language_by_short_code(code):
	for language in languages:
		if language.short_code == code:
			return language

	return None

def get_language_by_english_name(name, case_insensitive=False):
	if case_insensitive:
		name = name.lower()
	for language in languages:
		if (language.english_name.lower() if case_insensitive else language.english_name) == name:
			return language

	return None

def get_region_by_name(name):
	for region in regions:
		if region.name == name:
			return region

	return None

def get_region_by_short_code(short_code):
	for region in regions:
		if region.short_code == short_code:
			return region

	return None

def get_language_from_regions(region_list):
	common_language = None
	#If all the regions here have the same language, we can infer the language of the game. Otherwise, we sorta can't
	#e.g. We know (USA, Australia) is English, but (Japan, USA) could be Japanese or English
	for region in region_list:
		if not common_language:
			common_language = get_language_by_english_name(region.language)
		else:
			if region.language != common_language.english_name:
				return None

	return common_language

def get_tv_system_from_regions(region_list):
	tv_systems = {region.tv_system for region in region_list if region.tv_system is not None}
	if not tv_systems:
		return None
	if len(tv_systems) == 1:
		return tv_systems.pop()

	#If there are multiple distinct systems, it must be agnostic (since we only have NTSC, PAL, and agnostic (both) for now)
	return TVSystem.Agnostic
	