import logging
from collections.abc import Collection, Mapping
from xml.etree import ElementTree

from meowlauncher.common_types import SaveType
from meowlauncher.data.name_cleanup.gametdb_company_name_cleanup import company_name_cleanup
from meowlauncher.info import Date, GameInfo
from meowlauncher.util.utils import junk_suffixes

logger = logging.getLogger(__name__)


class TDB:
	def __init__(self, xml: ElementTree.ElementTree):
		self.xml = xml

		genre_element = xml.find('genres')
		if genre_element is None:
			return
		# Can assume all genres not in maingenres are subgenres
		self.genres = {
			main_genre.attrib['name']: [
				subgenre.attrib['name'] for subgenre in main_genre.iter('subgenre')
			]
			for main_genre in genre_element.iter('maingenre')
		}

	def find_game(self, search_key: str) -> ElementTree.Element | None:
		return next(
			(game for game in self.xml.iter('game') if game.findtext('id') == search_key), None
		)

	def _organize_genres(self, genres: Collection[str]) -> Mapping[str, Collection[str]]:
		main_genres: dict[str, set[str]] = {}
		for genre in genres:
			if genre in self.genres.keys():
				if genre not in main_genres:
					main_genres[genre] = set()
			else:
				for main_genre, subgenres in self.genres.items():
					for subgenre in subgenres:
						if genre == subgenre:
							if main_genre in {'general', 'theme', 'traditional', 'others'}:
								if subgenre not in main_genres:
									main_genres[subgenre] = set()
							else:
								main_genres.setdefault(main_genre, set()).add(
									'driving' if genre == 'racing' else genre
								)
								break
		return main_genres

	def parse_genre(self, game_info: GameInfo, genre_list: str) -> None:
		# genres = [g.title() for g in genre_list.split(',')]
		genres = genre_list.split(',')
		if 'software' in genres:
			# This isn't really a genre so much as a category
			genres.remove('software')

		if not genres:
			return

		items = tuple(self._organize_genres(genres).items())
		if items:
			game_info.genre = items[0][0].title()
			subgenres = items[0][1]
			if subgenres:
				game_info.subgenre = ', '.join(s.title() for s in subgenres)
			if len(items) > 1:
				game_info.specific_info['Additional Genres'] = ', '.join(
					g[0].title() for g in items[1:]
				)
				additional_subgenres = {s.title() for g in items[1:] for s in g[1]}
				if additional_subgenres:
					game_info.specific_info['Additional Subgenres'] = ', '.join(
						additional_subgenres
					)


def _clean_up_company_name(company_name: str) -> str:
	whaa = {
		"Take2 / Den'Z / Global Star": 'Global Star Software',  # Someone's trying to just read the licensee code according to the database and calling it a day…
		'HAL/Sora/Harox': 'Sora / HAL Laboratory',  # wat? What the heck is Harox? Where did that one even come from?
	}

	names = whaa.get(company_name, company_name).split(' / ')
	cleaned_names = set()
	for name in names:
		name = name.rstrip()
		while junk_suffixes.search(name):
			name = junk_suffixes.sub('', name).rstrip()
		name = company_name_cleanup.get(name, name)
		cleaned_names.add(name)

	return ', '.join(sorted(cleaned_names))


def _add_info_from_tdb_entry(tdb: TDB, db_entry: ElementTree.Element, game_info: GameInfo) -> None:
	"""id: What we just found
	(it thinks I need an indented block) type: 3DS, 3DSWare, VC, etc (we probably don't need to worry about that)
	region: PAL, etc (we can see region code already)
	languages: "EN" "JA" etc (I guess we could parse this if the filename isn't good enough for us)
	rom: What they think the ROM should be named
	case: Has "color" and "versions" attribute? I don't know what versions does but I presume it all has to do with the game box"""
	game_info.add_alternate_name(db_entry.attrib['name'], 'GameTDB Name')

	for element in db_entry:
		if element.tag not in {
			'developer',
			'publisher',
			'date',
			'rating',
			'id',
			'type',
			'region',
			'languages',
			'locale',
			'genre',
			'wi-fi',
			'input',
			'rom',
			'case',
			'save',
		}:
			logger.debug('uwu %s has unknown %s tag', db_entry.attrib['name'], element)

	developer = db_entry.findtext('developer')
	if developer and developer != 'N/A':
		game_info.developer = _clean_up_company_name(developer)
	publisher = db_entry.findtext('publisher')
	if publisher:
		game_info.publisher = _clean_up_company_name(publisher)
	date = db_entry.find('date')
	if date is not None:
		year = date.attrib.get('year')
		month = date.attrib.get('month')
		day = date.attrib.get('day')
		if any([year, month, day]):
			game_info.release_date = Date(year, month, day)

	genre = db_entry.findtext('genre')
	if genre:
		tdb.parse_genre(game_info, genre)

	for locale in db_entry.iter('locale'):
		synopsis = locale.findtext('synopsis')
		if synopsis:
			key_name = (
				f"Synopsis-{locale.attrib.get('lang')}" if 'lang' in locale.attrib else 'Synopsis'
			)
			game_info.descriptions[key_name] = synopsis

	rating = db_entry.find('rating')
	if rating is not None:
		# Rating board (attrib "type") is implied by region (game released in e.g. both Europe and Australia just tend to not have this here)
		value = rating.attrib.get('value')
		if value:
			game_info.specific_info['Age Rating'] = value

		descriptors = {e.text for e in rating.iter('descriptor')}
		if descriptors:
			game_info.specific_info['Content Warnings'] = descriptors

	# This stuff will depend on platform…

	save = db_entry.find('save')
	if save is not None:
		blocks = save.attrib.get('blocks')
		# Other platforms may have "size" instead, also there are "copy" and "move" attributes which we'll ignore
		if blocks:
			if game_info.platform == 'Wii':
				game_info.save_type = SaveType.Internal
			elif game_info.platform == 'GameCube':
				game_info.save_type = SaveType.MemoryCard
		# Have not seen a db_entry with blocks = 0 or missing blocks or size

	if game_info.platform != 'GameCube':
		wifi = db_entry.find('wi-fi')
		if wifi:
			features = {feature.text for feature in wifi.iter('feature')}
			game_info.specific_info['Wifi Features'] = features
			# online, download, score, nintendods

	input_element = db_entry.find('input')
	if input_element is not None:
		# TODO: DS has players-multi-cart and players-single-cart instead (which one do I want?)
		number_of_players = input_element.attrib.get('players', None)
		if (
			number_of_players is not None
		):  # Maybe 0 could be a valid amount? For like demos or something
			game_info.specific_info['Number of Players'] = number_of_players

		if game_info.platform != 'GameCube':
			# wiimote, nunchuk, motionplus, db_entrycube, nintendods, classiccontroller, wheel, zapper, balanceboard, wiispeak, microphone, guitar, drums, dancepad, keyboard, draw
			optional_controls = set()
			required_controls = set()
			for control in input_element.iter('control'):
				control_type = control.attrib.get('type')
				if control.attrib.get('required', 'false') == 'true':
					required_controls.add(control_type)
				else:
					optional_controls.add(control_type)

				# cbf setting up input_info just yet
				game_info.specific_info['Optional Additional Controls'] = optional_controls
				game_info.specific_info['Required Additional Controls'] = required_controls


def add_info_from_tdb(tdb: TDB | None, game_info: GameInfo, search_key: str) -> None:
	if not tdb:
		return

	game = tdb.find_game(search_key)
	if game is not None:
		_add_info_from_tdb_entry(tdb, game, game_info)
