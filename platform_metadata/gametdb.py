from common import junk_suffixes
from config.main_config import main_config

def add_info_from_tdb(tdb, metadata, search_key):
	if not tdb:
		return

	game = tdb.find('game[id="{0}"]'.format(search_key))
	if game is not None:
		metadata.add_alternate_name(game.attrib['name'], 'GameTDB-Name')
		#(Pylint is on drugs if I don't add more text here) id: What we just found
		#(it thinks I need an indented block) type: 3DS, 3DSWare, VC, etc (we probably don't need to worry about that)
		#region: PAL, etc (we can see region code already)
		#languages: "EN" "JA" etc (I guess we could parse this if the filename isn't good enough for us)
		#locale lang="EN" etc: Contains title (hmm) and synopsis (ooh, interesting) (sometimes) for each language
		#rom: What they think the ROM should be named
		#case: Has "color" and "versions" attribute? I don't know what versions does but I presume it all has to do with the game box
		#save: How many blocks this has (wait maybe this can be save type) (but it's hardly used)
		if main_config.debug:
			for element in game:
				if element.tag not in ('developer', 'publisher', 'date', 'rating', 'id', 'type', 'region', 'languages', 'locale', 'genre', 'wi-fi', 'input', 'rom', 'case', 'save'):
					print('uwu', game.attrib['name'], 'has unknown', element, 'tag')

		developer = game.findtext('developer')
		if developer:
			metadata.developer = junk_suffixes.sub('', developer)
		publisher = game.findtext('publisher')
		if publisher:
			metadata.publisher =  junk_suffixes.sub('', publisher)
		date = game.find('date')
		if date is not None:
			year = date.attrib.get('year')
			month = date.attrib.get('month')
			day = date.attrib.get('day')
			if year:
				metadata.year = year
			if month:
				metadata.month = month
			if day:
				metadata.day = day

		genre = game.findtext('genre')
		if genre:
			if ',' not in genre:
				metadata.genre = genre.title()
			#TODO: If it is, figure out what's a "main genre" and what's a subgenre because there seems to be a distinction, and maybe some need to be combined
		
		rating = game.find('rating')
		if rating is not None:
			#We can already get the actual rating value from the SMDH, but this has more fun stuff
			descriptors = [e.text for e in rating.findall('descriptor')]
			if descriptors:
				metadata.specific_info['Content-Warnings'] = descriptors
		
		#This stuff will depend on platform…

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
