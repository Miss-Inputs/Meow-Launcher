from common import junk_suffixes
from common_types import SaveType
from config.main_config import main_config
from data.name_cleanup.gametdb_company_name_cleanup import company_name_cleanup
from metadata import Date


class TDB():
	def __init__(self, xml):
		self.xml = xml
		
		genre_element = xml.find('genres')
		#Can assume this is here, and that all genres not in maingenres are subgenres
		self.genres = {main_genre.attrib['name']: [subgenre.attrib['name'] for subgenre in main_genre.findall('subgenre')] for main_genre in genre_element.findall('maingenre')}

	def find_game(self, search_key):
		return self.xml.find('game[id="{0}"]'.format(search_key))

	def parse_genre(self, metadata, genre_list):
		#genres = [g.title() for g in genre_list.split(',')]
		genres = genre_list.split(',')
		if 'software' in genres:
			#This isn't really a genre so much as a category
			genres.remove('software')
		
		if not genres:
			return
		
		main_genres = {}
		for genre in genres:
			if genre in self.genres.keys():
				if genre not in main_genres:
					main_genres[genre] = set()
			else:
				for main_genre, subgenres in self.genres.items():
					for subgenre in subgenres:
						if genre == subgenre:
							if main_genre in ('general', 'theme', 'traditional', 'others'):
								if subgenre not in main_genres:
									main_genres[subgenre] = set()
							else:
								if main_genre not in main_genres:
									main_genres[main_genre] = set()
								main_genres[main_genre].add(genre)
								break

		items = list(main_genres.items())
		if items:
			metadata.genre = items[0][0].title()
			subgenres = items[0][1]
			if subgenres:
				metadata.subgenre = ', '.join([s.title() for s in subgenres])
			if len(items) > 1:
				metadata.specific_info['Additional-Genres'] = ', '.join([g[0].title() for g in items[1:]])
				additional_subgenres = {s.title() for g in items[1:] for s in g[1]}
				if additional_subgenres:
					metadata.specific_info['Additional-Subgenres'] = ', '.join(additional_subgenres)
			

def clean_up_company_name(company_name):
	whaa = {
		"Take2 / Den'Z / Global Star": 'Global Star Software', #Someone's trying to just read the licensee code according to the database and calling it a day…
		'HAL/Sora/Harox': 'Sora / HAL Laboratory', #wat? What the heck is Harox? Where did that one even come from?
	}

	names = whaa.get(company_name, company_name).split(' / ')
	cleaned_names = []
	for name in names:
		while junk_suffixes.search(name):
			name = junk_suffixes.sub('', name)
		name = company_name_cleanup.get(name, name)
		cleaned_names.append(name)

	return ', '.join(sorted(cleaned_names))

def add_info_from_tdb(tdb, metadata, search_key):
	if not tdb:
		return

	game = tdb.find_game(search_key)
	if game is not None:
		metadata.add_alternate_name(game.attrib['name'], 'GameTDB-Name')
		#(Pylint is on drugs if I don't add more text here) id: What we just found
		#(it thinks I need an indented block) type: 3DS, 3DSWare, VC, etc (we probably don't need to worry about that)
		#region: PAL, etc (we can see region code already)
		#languages: "EN" "JA" etc (I guess we could parse this if the filename isn't good enough for us)
		#locale lang="EN" etc: Contains title (hmm) and synopsis (ooh, interesting) (sometimes) for each language
		#rom: What they think the ROM should be named
		#case: Has "color" and "versions" attribute? I don't know what versions does but I presume it all has to do with the game box
		
		if main_config.debug:
			for element in game:
				if element.tag not in ('developer', 'publisher', 'date', 'rating', 'id', 'type', 'region', 'languages', 'locale', 'genre', 'wi-fi', 'input', 'rom', 'case', 'save'):
					print('uwu', game.attrib['name'], 'has unknown', element, 'tag')

		developer = game.findtext('developer')
		if developer and developer != 'N/A':
			metadata.developer = clean_up_company_name(developer)
		publisher = game.findtext('publisher')
		if publisher:
			metadata.publisher =  clean_up_company_name(publisher)
		date = game.find('date')
		if date is not None:
			year = date.attrib.get('year')
			month = date.attrib.get('month')
			day = date.attrib.get('day')
			if any([year, month, day]):
				metadata.release_date = Date(year, month, day)

		genre = game.findtext('genre')
		if genre:
			tdb.parse_genre(metadata, genre)
		
		rating = game.find('rating')
		if rating is not None:
			#We can already get the actual rating value from the SMDH, but this has more fun stuff
			descriptors = [e.text for e in rating.findall('descriptor')]
			if descriptors:
				metadata.specific_info['Content-Warnings'] = descriptors

		#This stuff will depend on platform…

		save = game.find('save')
		if save is not None:
			blocks = save.attrib.get('blocks')
			#Other platforms may have "size" instead, also there are "copy" and "move" attributes which we'll ignore
			if blocks:
				if metadata.platform == 'Wii':
					metadata.save_type = SaveType.Internal
				elif metadata.platform == 'GameCube':
					metadata.save_type = SaveType.MemoryCard
			#Have not seen a game with blocks = 0 or missing blocks or size

		if metadata.platform != 'GameCube':
			wifi = game.find('wi-fi')
			supports_online = False
			if wifi:
				supports_online = any(e.text == 'online' for e in wifi.findall('feature'))
			metadata.specific_info['Supports-Online'] = supports_online
			#Other feature elements seen are "download" and "score" but I dunno what those do
		
		input_element = game.find('input')
		if input_element is not None:
			#TODO: DS has players-multi-cart and players-single-cart instead (which one do I want?)
			number_of_players = input_element.attrib.get('players', None)
			if number_of_players is not None: #Maybe 0 could be a valid amount? For like demos or something
				metadata.specific_info['Number-of-Players'] = number_of_players
			
			if metadata.platform != 'GameCube':
				controls = input_element.findall('control')
				if controls:
					#cbf setting up input_info just yet
					metadata.specific_info['Optional-Additional-Controls'] = [e.attrib.get('type') for e in controls if e.attrib.get('required', 'false') == 'false']
					metadata.specific_info['Required-Additional-Controls'] = [e.attrib.get('type') for e in controls if e.attrib.get('required', 'false') == 'true']
