from collections.abc import Mapping
from typing import Optional

series_overrides: Mapping[str, tuple[Optional[str], Optional[str]]] = {
	#These names are too clever for my code to work properly, so I'll do them manually
	'Fantastic 4': ('Fantastic 4', '1'),
	'Fantastic 4 - Flame On': ('Fantastic 4', 'Flame On'), #Not sure what this is numerically
	'Killer 7': (None, None),
	'Mega Man X': ('Mega Man X', '1'),
	'Metal Slug X': ('Metal Slug', '2X'),
	'Pokemon X': ('Pokemon', 'X'),
}
