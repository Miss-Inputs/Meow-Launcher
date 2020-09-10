not_necessarily_equivalent_arcade_names = [
	#Some arcade games that have names that are too common, there are home games with the same name that aren't necessarily related other than the same franchise potentially, and it's better to avoid messing around there since this whole find_equivalent_arcade_games thing is mostly a hack to see if we can get nice icons and genres for things
	#I don't really like this solution overall, but it will do, unless I want to manually go through like every software list item and create a mapping of game to arcade game? Which maybe I will one day

	'arcadecl', #That could be anyone's arcade classics… the arcade arcade classics was by Atari (and unreleased), but there's nothing stopping other companies compiling their own alleged classics, which happened
	'blasto',
	'btoads',
	'checkmat',
	'dlair', #So many home ports that were just in name only for technical limitations, so they're not related…
	'hero', #Matches against H.E.R.O. which is different
	'inca',
	'qwak',
	'spaceace', #Same situation as dlair
	'witch',

	#Franchises where the title is used for multiple adaptations
	'avsp',
	'batman',
	'fotns',
	'gijoe',
	'godzilla',
	'golgo13',
	'hook',
	'jdredd',
	'jpark',
	'macross',
	'pepsiman',
	'rambo',
	'starwars',
	'superman',
	'term2', #There are home ports of this (Terminator 2: Judgement Day), but they are called "T2: The Arcade Game" to avoid confusion with the unrelated tie ins which aren't conversions of the arcade which are called "Terminator 2: Judgement Day", even though that doesn't avoid confusion at all and merely creates it. Anyway, there are probably ways I could handle this case, but I don't feel like doing them for now.
	'tmnt', #Same problem where someone thought putting "The Arcade Game" subtitle on the home ports would solve the problem
	'ultraman',
	'xmen',
	
]
