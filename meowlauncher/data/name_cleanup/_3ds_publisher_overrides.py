consistentified_manufacturers = {
	'ATLUS': 'Atlus',
	'Atlus U.S.A.': 'Atlus USA',
	'Bigben Interactive': 'BigBen Interactive',  # Other way around might also be correct
	'CAPCOM': 'Capcom',
	'CIRCLE Ent.': 'Circle Entertainment',
	'Disney Interactive Studios': 'Disney',
	'INTI CREATES': 'Inti Creates',
	'Konami Digital Entertainment': 'Konami',
	'MAQL Europe Limited': 'Marvelous AQL',  # Or maybe this should be "Marvelous AQL Europe" specifically
	'SEGA': 'Sega',
	'SQUARE ENIX': 'Square Enix',
	'TATE Multimedia': 'Tate Multimedia',
	'Unspecified Author': None,  # Homebrew might do this
	'VD-DEV': 'VD-Dev',
	'WB Games': 'Warner Bros',
	'YouTube': 'Google',  # Maybe I should change nintendo_licensee_codes WB to YouTube. Oh well. Either way, this is the YouTube app, and hence Google
}
"""When getting publisher from SMDH, sometimes things are formatted in different ways than wanted (e.g. YELLING CASE), this is here to smooth things out
It's why we try to use licensee code instead, but that's not always there on 3DS
For what it's worth, it seems each publisher will format its own name consistently across all games it publishes, it just looks weird compared to how names are formatted elsewhere"""
