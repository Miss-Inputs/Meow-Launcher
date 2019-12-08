manufacturer_overrides = {
	#Stuff that appears in machines/software lists but it's the same company but formatted in different ways (suffixes/punctuation/spacing/whatnot), and maybe neither is more correct but it's no fun to have inconsistent naming

	#Anyway. Some of these are bit... contentious? Is that the right word? Like, some of these are definitely different ways of spelling the same company and that's definitely a valid thing to deal with, but then some of these might well just be different brands used by the same company, because companies are weird like that. So at some point I'll probably need to clean this up. Hmm...
	#Yeah let's make this a big TODO to verify what formatting companies actually use themselves

	#TODO: Are ATW > ATW USA the same or a regional branch?
	#Should NEC Avenue just be called NEC?
	#Toshiba EMI > Toshiba? Or is that a combination of the things
	#Are CBS Electronics and CBS Software the same? Seems like they're both owned by CBS the American TV company, the former is for various Atari 2600/5200/7800 games they published and distributing the ColecoVision outside USA; and the latter is basically licensed Sesame Street games?
	#Are Fox Interactive, Fox Video Games, 20th Century Fox all the same?
	#Human == Human Amusement?
	#Universal (the one that published Mr. Do) == Universal Video Games? Not the same as Universal Interactive / the media conglomerate, are now known as Aruze
	#BBC Worldwide == BBC Multimedia? I mean they're obviously both the BBC
	#Empire Entertainment == Empire Interactive?
	#New Image Technologies == New Image?
	#Naxat == Naxat Soft?
	#RCM Group == RCM?

	#The SNES game Super Godzilla (USA) has a publisher of literally "Super Godzilla". Wait what? That can't be right. Should be Toho right? Same with Tetris (Japan) for Megadrive. Unless they meant The Tetris Company there. But then I dunno
	#Leave Atari Games > Atari and Midway Games > Midway alone, because if I try to comperehend the timeline of which is what and who owned the rights to which brand name and who owned who at any given time, I would die of confusion
	#Marvelous Entertainment and Marvelous Interactive also are different (due to mergers) and I gotta remember that
	
	'20th Century Fox Video Games': '20th Century Fox',
	'3DO Company': '3DO',
	'Absolute': 'Absolute Entertainment', #Hmm, not sure if it'd be better to do this the other way around
	'Acclaim Entertainment': 'Acclaim',
	'American Softworks Company': 'American Softworks',
	'APF Electronics': 'APF',
	'ASCII Entertainment': 'ASCII',
	'Bally Midway Mfg.': 'Bally Midway',
	'Bally Midway MFG.': 'Bally Midway',
	'Bit Corp': 'Bit Corporation',
	'BPS': 'Bullet-Proof Software', #I hope nobody else uses that acronym
	'Broderbund': 'Brøderbund',
	'Broderbund Software': 'Brøderbund',
	'Brøderbund Software': 'Brøderbund',
	'Broderbund software': 'Brøderbund',
	'California Pacific Computer': 'California Pacific',
	'Coconuts Japan Entertainment': 'Coconuts Japan',
	'Commodore Business Machines': 'Commodore',
	'Creative Electronics And Software': 'Creative Electronics & Software',
	'Creative Software': 'Creative',
	'Cryo': 'Cryo Interactive',
	'D3 Publishing': 'D3 Publisher',
	'Data East Corporation': 'Data East',
	'DataSoft': 'Datasoft',
	'Dempa Shinbunsha': 'Dempa',
	'Digital Equipment Corporation': 'DEC',
	'Ectron Eletrônica Ltda.': 'Ectron Eletrônica',
	'Eidos Interactive': 'Eidos',
	'Electronics Arts': 'Electronic Arts',
	'Elite': 'Elite Systems',
	'Entex Industries': 'Entex',
	'First Star': 'First Star Software',
	'Funtech Entertainment': 'Funtech',
	'General Consumer Electronics': 'GCE',
	'Gradiente Entertainment Ltda.': 'Gradiente Entertainment',
	'Grandslam Entertainments': 'Grandslam',
	'Gremlin Interactive': 'Gremlin Graphics',
	'HAL Kenkyuujo': 'HAL', #Literally "HAL Laboratory"
	'HAL Laboratory': 'HAL',
	'Hasbro Interactive': 'Hasbro',
	'Hewlett-Packard': 'HP',
	'HiCom': 'Hi-Com',
	'Hudson': 'Hudson Soft',
	'Human Entertainment': 'Human',
	'International Business Machines': 'IBM',
	'JoWooD Entertainment AG': 'JoWooD Entertainment',
	'Kaneko Elc.': 'Kaneko',
	'Kyugo': 'Kyugo Boueki',
	'K-Tel Vision': 'K-Tel',
	'Laser Beam': 'Laser Beam Entertainment',
	'Loriciel Software': 'Loriciel',
	'MicroCabin': 'Micro Cabin', #Annoying alternate spelling because they officially use both just to be annoying
	'Microdigital': 'Micro Digital',
	'Microlab': 'Micro Lab',
	'Microprose Games': 'MicroProse',
	'NEC Home Electronics': 'NEC',
	'Nihon Telenet': 'Telenet', #I guess
	'Nippon System': 'Nihon System',
	'Ocean Software': 'Ocean',
	'Ocean Software Limited': 'Ocean',
	'Omage Micott': 'Omega Micott', #I have a feeling I'm the one who's wrong here. Never did quality check the Wonderswan licensees
	'Omori Electric': 'Omori',
	'Palm Inc': 'Palm',
	'Petaco S.A.': 'Petaco',
	'Playmates Interactive': 'Playmates',
	'PonyCa': 'Pony Canyon',
	'ProSoft': 'Prosoft',
	'Rare Coin-It': 'Rare',
	'Sales Curve': 'The Sales Curve',
	'Sales Curve Interactive': 'The Sales Curve',
	'Sammy Entertainment': 'Sammy',
	'Sega Enterprises': 'Sega',
	'Seta Corporation': 'Seta',
	'Sierra Entertainment': 'Sierra',
	'Sierra On-Line': 'Sierra',
	'Sigma Enterprises': 'Sigma', #Every time I see this line I keep thinking "sigma balls", just thought you should know
	'Software Toolworks': 'The Software Toolworks', #It doesn't seem right that the "correct" one is the latter, but it's used more often, so I guess it is
	'Spinnaker Software': 'Spinnaker',
	'Spinnaker Software ': 'Spinnaker', #bah should I start doing .rstrip() before the thing
	'Sunrise Software': 'Sunrise',
	'Swing! Entertainment Media': 'Swing! Entertainment',
	'System 3 Software': 'System 3',
	'Taito Corporation': 'Taito',
	'Taito Corporation Japan': 'Taito',
	'Taito America Corporation': 'Taito America',
	'Team 17': 'Team17',
	'TecMagik Entertainment': 'TecMagik',
	'Techno Soft': 'Technosoft',
	'TecToy': 'Tec Toy',
	'Telenet Japan': 'Telenet',
	'T*HQ': 'THQ', #Why.
	'Tiger Electronics': 'Tiger', #Or should this be other way around
	'Titus Software': 'Titus',
	'UA Limited': 'UA',
	'V.Fame': 'Vast Fame',
	'Visco Corporation': 'Visco',
	'Walt Disney': 'Disney',
	'Warner Bros. Games': 'Warner Bros',
	'Williams Entertainment': 'Williams',

	#Sometimes companies go by two different names and like... maybe I should leave those alone, bleh I hate decision making
	'DSI Games': 'Destination Software',
	'dtp Entertainment': 'Digital Tainment Pool',
	'Square': 'Squaresoft', #Which is the frickin' right one?

	#This isn't a case of a company formatting its name in different ways, but it's where a company's renamed itself, and maybe I shouldn't do this...
	'Alpha Denshi': 'ADK', #Renamed in 1993
	'Ubi Soft': 'Ubisoft', #I hate that they used to spell their name with a space so this is valid. But then, don't we all hate Ubisoft for one reason or another?
	'Video Technology': 'VTech',

	#Brand names that are definitely the same company but insist on using some other name... maybe I shouldn't change these either, but then, I'm going to
	'Atarisoft': 'Atari', #Atarisoft is just a brand name and not an actual company, so I guess I'll do this
	'Bally Gaming': 'Bally',
	'Bally Manufacturing': 'Bally',
	'Disney Interactive': 'Disney',
	'Disney Interactive Studios': 'Disney',
	'Disney Software': 'Disney',
	'Dreamworks Games': 'DreamWorks',
	'LEGO Media': 'Lego',
	'Mattel Electronics': 'Mattel',
	'Mattel Interactive': 'Mattel',
	'Mattel Media': 'Mattel',
	'Nihon Bussan': 'Nichibutsu',
	'Nihonbussan': 'Nichibutsu', #In the event that we figure out we shouldn't change the above, we should at least consistentify this formatting
	'Sony Computer Entertainment': 'Sony',
	'Sony Imagesoft': 'Sony',
	'Strata/Incredible Technologies': 'Incredible Technologies',
	'Tandy Radio Shack': 'Tandy',
	'Viacom New Media': 'Viacom',
	'Virgin Games': 'Virgin',
	'Virgin Interactive': 'Virgin',
	'Vivendi Universal': 'Vivendi',

	#For some reason, some Japanese computer software lists have the Japanese name and then the English one in brackets. Everywhere else the English name is used even when the whole thing is Japanese. Anyway I guess we just want the English name then, because otherwise for consistency, I'd have to convert every single English name into Japanese
	'B·P·S (Bullet-Proof Software)': 'Bullet-Proof Software',
	'HOT・B': 'Hot-B',
	'アートディンク (Artdink)': 'Artdink',
	'アイレム (Irem)': 'Irem',
	'アスキー (ASCII)': 'ASCII',
	'イマジニア (Imagineer)': 'Imagineer',
	'エニックス (Enix)': 'Enix',
	'カプコン (Capcom)': 'Capcom',
	'コナミ (Konami)': 'Konami',
	'コンプティーク (Comptiq)': 'Comptiq',
	'システムサコム (System Sacom)': 'System Sacom',
	'システムソフト (System Soft)': 'System Soft',
	'シャープ (Sharp)': 'Sharp',
	'シンキングラビット (Thinking Rabbit)': 'Thinking Rabbit',
	'スタークラフト (Starcraft)': 'Starcraft',
	'ソフトプロ (Soft Pro)': 'Soft Pro',
	'タイトー (Taito)': 'Taito',
	'デービーソフト (dB-Soft)': 'dB-Soft',
	'ニデコム (Nidecom)': 'Nidecom',
	'パックスエレクトロニカ (Pax Electronica)': 'Pax Electronica',
	'ハドソン (Hudson Soft)': 'Hudson Soft',
	'バンダイ (Bandai)': 'Bandai',
	'ブラザー工業 (Brother Kougyou)': 'Brother Kougyou',
	'ブローダーバンドジャパン (Brøderbund Japan)': 'Brøderbund Japan',
	'ホームデータ (Home Data)': 'Home Data',
	'ポニカ (Pony Canyon)': 'Pony Canyon',
	'ポニカ (PonyCa)': 'Pony Canyon',
	'マイクロネット (Micronet)': 'Micronet',
	'マカダミアソフト (Macadamia Soft)': 'Macadamia Soft',
	'工画堂スタジオ (Kogado Studio)': 'Kogado Studio',
	'日本ソフトバンク (Nihon SoftBank)': 'Nihon SoftBank',
	'日本テレネット (Nihon Telenet)': 'Telenet',
	'日本ファルコム (Nihon Falcom)': 'Nihon Falcom',
	'電波新聞社 (Dempa Shinbunsha)': 'Dempa',

	#YELLING CASE / other capitalisation stuff
	'BEC': 'Bec',
	'Dreamworks': 'DreamWorks',
	'enix': 'Enix',
	'EPYX': 'Epyx',
	'Microprose': 'MicroProse',
	'RazorSoft': 'Razorsoft',
	'SONY': 'Sony',
	'SpectraVideo': 'Spectravideo',
	'Spectrum HoloByte': 'Spectrum Holobyte',
	'SunSoft': 'Sunsoft',
	'SWING! Entertainment': 'Swing! Entertainment',
	'VAP': 'Vap',

	#Maybe typos?
	'ChinSoft': 'Chunsoft', #gbcolor/furaish2
	'Elite System': 'Elite Systems',
	'Hi-Tech Expression': 'Hi-Tech Expressions',
	'Hi Tech Expressions': 'Hi-Tech Expressions',
	'Jungle\'s Soft': 'Jungle Soft',
	'Pack-In-Video': 'Pack-In Video',
	'Take Two Interactive': 'Take-Two Interactive',
	'Watera': 'Watara',

	#Definitely typos
	'Activison': 'Activision',
	'Commonweaalth': 'Commonwealth',
	'Connonwealth': 'Commonwealth',
	'Mindscapce': 'Mindscape',
	'Sydney Developmeent ': 'Sydney Development',
	'unknown': '<unknown>', #This shows up in sv8000 software list, so it might actually just be Bandai, but when you presume you make a pres out of u and me, so we'll just lump it in with the other unknowns
}

dont_remove_suffix = [
	#Normally we run junk_suffixes on stuff to remove "Corporation" "Co." at the end but sometimes we shouldn't
	'Bit Corp', #We will then fix that up later
	'Zonov and Co.',
]
