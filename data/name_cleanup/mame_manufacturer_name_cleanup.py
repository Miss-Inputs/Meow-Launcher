manufacturer_name_cleanup = {
	#Stuff that appears in machines/software lists but it's the same company but formatted in different ways (suffixes/punctuation/spacing/whatnot), and maybe neither is more correct but it's no fun to have inconsistent naming

	#Anyway. Some of these are bit... contentious? Is that the right word? Like, some of these are definitely different ways of spelling the same company and that's definitely a valid thing to deal with, but then some of these might well just be different brands used by the same company, because companies are weird like that. So at some point I'll probably need to clean this up. Hmm...
	#Yeah let's make this a big TODO to verify what formatting companies actually use themselves

	#TODO: Are ATW > ATW USA the same or a regional branch?
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
	#Sammy Industries = Sammy?
	#Sir-Tech Software = Sir-Tech?
	#Is "Midway Home Entertainment" Midway or Midway Games oh shit oh fuck

	#The SNES game Super Godzilla (USA) has a publisher of literally "Super Godzilla". Wait what? That can't be right. Should be Toho right? Same with Tetris (Japan) for Megadrive. Unless they meant The Tetris Company there. But then I dunno
	#Leave Atari Games > Atari and Midway Games > Midway alone, because if I try to comperehend the timeline of which is what and who owned the rights to which brand name and who owned who at any given time, I would die of confusion
	#Marvelous Entertainment and Marvelous Interactive also are different (due to mergers) and I gotta remember that
	#Buena Vista Interactive seemingly not the same as Buena Vista Games, the former being used for things that _aren't_ Disney related and the latter is a different label for everything else (or something weird and unnecessary and proof that capitalism isn't efficient like that)
	
	'Absolute': 'Absolute Entertainment', #Hmm, not sure if it'd be better to do this the other way around
	'Big Ben Interactive': 'BigBen Interactive',
	'Bit Corp': 'Bit Corporation',
	'BPS': 'Bullet-Proof Software', #I hope nobody else uses that acronym
	'Broderbund': 'Brøderbund',
	'Creative Electronics And Software': 'Creative Electronics & Software',
	'Cryo': 'Cryo Interactive',
	'D3 Publishing': 'D3 Publisher',
	'DataSoft': 'Datasoft',
	'Davidson and Associates': 'Davidson & Associates',
	'Electronics Arts': 'Electronic Arts',
	'Elite': 'Elite Systems',
	'First Star': 'First Star Software',
	'Gremlin Interactive': 'Gremlin Graphics',
	'HiCom': 'Hi-Com',
	'Hudson': 'Hudson Soft',
	'Kyugo': 'Kyugo Boueki',
	'Laser Beam': 'Laser Beam Entertainment',
	'Loriciels': 'Loriciel',
	'Malibu Games': 'Malibu Interactive',
	'Metro 3D': 'Metro3D',
	'MicroCabin': 'Micro Cabin', #Annoying alternate spelling because they officially use both just to be annoying
	'Microdigital': 'Micro Digital',
	'Microlab': 'Micro Lab',
	'Nihon Telenet': 'Telenet', #I guess
	'Nippon System': 'Nihon System',
	'Omage Micott': 'Omega Micott', #I have a feeling I'm the one who's wrong here. Never did quality check the Wonderswan licensees
	'Palm Inc': 'Palm',
	'PonyCa': 'Pony Canyon',
	'ProSoft': 'Prosoft',
	'Sales Curve': 'The Sales Curve',
	'Software Toolworks': 'The Software Toolworks', #It doesn't seem right that the "correct" one is the latter, but it's used more often, so I guess it is
	'Team 17': 'Team17',
	'Techno Soft': 'Technosoft',
	'TecToy': 'Tec Toy',
	'T*HQ': 'THQ', #Why.
	'V.Fame': 'Vast Fame',
	'Walt Disney': 'Disney',

	#Suffixes where the suffix is often not used
	#"Company"
	'3DO Company': '3DO',
	'American Softworks Company': 'American Softworks',
	'LucasArts Entertainment Company': 'LucasArts',
	#"Corporation"
	'Bonsai Entertainment Corporation': 'Bonsai Entertainment',
	'Data East Corporation': 'Data East',
	'Leland Corporation': 'Leland',
	'Sammy USA Corporation': 'Sammy USA',
	'Seta Corporation': 'Seta',
	'Taito Corporation': 'Taito',
	'Taito Corporation Japan': 'Taito',
	'Taito America Corporation': 'Taito America',
	'Tandy Corporation': 'Tandy',
	'Visco Corporation': 'Visco',
	#"Electric"
	'Kaneko Elc.': 'Kaneko',
	'Omori Electric': 'Omori',
	#"Electronics"
	'APF Electronics': 'APF',
	'Tiger Electronics': 'Tiger', #Or should this be other way around
	#"Enterprises"
	'Sega Enterprises': 'Sega',
	'Sigma Enterprises': 'Sigma', #Every time I see this line I keep thinking "sigma balls", just thought you should know
	#"Entertainment"
	'Acclaim Entertainment': 'Acclaim',
	'ASCII Entertainment': 'ASCII',
	'Blizzard Entertainment': 'Blizzard',
	'Capcom Entertainment': 'Capcom',
	'Coconuts Japan Entertainment': 'Coconuts Japan',
	'Funtech Entertainment': 'Funtech',
	'Grandslam Entertainments': 'Grandslam',
	'Human Entertainment': 'Human',
	'Sammy Entertainment': 'Sammy',
	'Sierra Entertainment': 'Sierra',
	'TecMagik Entertainment': 'TecMagik',
	'Williams Entertainment': 'Williams',
	#"Games"
	'Microprose Games': 'MicroProse',
	'Warner Bros. Games': 'Warner Bros',
	#"Industries"
	'Entex Industries': 'Entex',
	'Merit Industries': 'Merit',
	'Sammy Industries': 'Sammy',
	#"Interactive"
	'Eidos Interactive': 'Eidos',
	'Hasbro Interactive': 'Hasbro',
	'Playmates Interactive': 'Playmates',
	'Sales Curve Interactive': 'The Sales Curve',
	#"Limited"
	'Ectron Eletrônica Ltda.': 'Ectron Eletrônica',
	'Gradiente Entertainment Ltda.': 'Gradiente Entertainment',
	'UA Limited': 'UA',
	#"Manufacturing"
	'Bally Midway Mfg.': 'Bally Midway',
	'Bally Midway MFG.': 'Bally Midway',
	#"Software"
	'ASCII Entertainment Software': 'ASCII',
	'Atlus Software': 'Atlus',
	'Broderbund Software': 'Brøderbund',
	'Brøderbund Software': 'Brøderbund',
	'Broderbund software': 'Brøderbund',
	'Creative Software': 'Creative',
	'Loriciel Software': 'Loriciel',
	'Ocean Software': 'Ocean',
	'Ocean Software Limited': 'Ocean',
	'Sirius Software': 'Sirius',
	'Sir-Tech Software': 'Sir-Tech',
	'Spinnaker Software': 'Spinnaker',
	'Spinnaker Software ': 'Spinnaker', #bah should I start doing .rstrip() before the thing
	'Sunrise Software': 'Sunrise',
	'System 3 Software': 'System 3',
	'Titus Software': 'Titus',
	'Ubi Soft Entertainment Software': 'Ubisoft',
	#"Studios"
	'Angel Studios': 'Angel',
	#"Video Games"
	'20th Century Fox Video Games': '20th Century Fox',	
	#Other junk
	'California Pacific Computer': 'California Pacific',
	'Commodore Business Machines': 'Commodore',
	'Dempa Shinbunsha': 'Dempa',
	'HAL Kenkyuujo': 'HAL', #Literally "HAL Laboratory"
	'HAL Laboratory': 'HAL',
	'Hal Labs': 'HAL',
	'JoWooD Entertainment AG': 'JoWooD Entertainment',
	'K-Tel Vision': 'K-Tel',
	'NEC Home Electronics': 'NEC',
	'Petaco S.A.': 'Petaco',
	'Sierra On-Line': 'Sierra',
	'Swing! Entertainment Media': 'Swing! Entertainment',

	#Acronyms that nobody actually expands
	'Digital Equipment Corporation': 'DEC',
	'General Consumer Electronics': 'GCE',
	'Hewlett-Packard': 'HP',
	'International Business Machines': 'IBM',
	
	#Sometimes companies go by two different names and like... maybe I should leave those alone, bleh I hate decision making
	'DSI Games': 'Destination Software',
	'dtp Entertainment': 'Digital Tainment Pool',
	'Square': 'Squaresoft', #Which is the frickin' right one?

	#This isn't a case of a company formatting its name in different ways, but it's where a company's renamed itself, and maybe I shouldn't do this...
	'Alpha Denshi': 'ADK', #Renamed in 1993
	'Ubi Soft': 'Ubisoft', #I hate that they used to spell their name with a space so this is valid. But then, don't we all hate Ubisoft for one reason or another?
	'Video Technology': 'VTech',
	'Rare Coin-It': 'Rare',

	#Brand names that are definitely the same company but insist on using some other name... maybe I shouldn't change these either, but then, I'm going to
	'Atarisoft': 'Atari', #Atarisoft is just a brand name and not an actual company, so I guess I'll do this
	'Bally Gaming': 'Bally',
	'Bally Manufacturing': 'Bally',
	'Disney Interactive': 'Disney',
	'Disney Interactive Studios': 'Disney',
	'Disney Software': 'Disney',
	'Dreamworks Games': 'DreamWorks',
	'HesWare': 'HES',
	'LEGO Media': 'Lego',
	'Mattel Electronics': 'Mattel',
	'Mattel Interactive': 'Mattel',
	'Mattel Media': 'Mattel',
	'Namco Hometek': 'Namco',
	'NEC Avenue': 'NEC',
	'NEC Interchannel': 'NEC',
	'Nihon Bussan': 'Nichibutsu',
	'Nihonbussan': 'Nichibutsu', #In the event that we figure out we shouldn't change the above, we should at least consistentify this formatting
	'Sony Computer Entertainment': 'Sony',
	'Sony Computer Entertainment America': 'Sony',
	'Sony Imagesoft': 'Sony',
	'Strata/Incredible Technologies': 'Incredible Technologies',
	'Tandy Radio Shack': 'Tandy',
	'Viacom New Media': 'Viacom',
	'Virgin Games': 'Virgin',
	'Virgin Interactive': 'Virgin',
	'Vivendi Universal': 'Vivendi',

	#For some reason, some Japanese computer software lists have the Japanese name and then the English one in brackets. Everywhere else the English name is used even when the whole thing is Japanese. Anyway I guess we just want the English name then, because otherwise for consistency, I'd have to convert every single English name into Japanese
	#Is there a way to just do this automatically? Detect Japanese characters and if it looks like this get the thing in brackets? And then fix up anything else that's inconsistent afterwards
	'B·P·S (Bullet-Proof Software)': 'Bullet-Proof Software',
	'HOT・B': 'Hot-B',
	'アートディンク (Artdink)': 'Artdink',
	'アイレム (Irem)': 'Irem',
	'アクティブ (Active)': 'Active',
	'アスキー (ASCII)': 'ASCII',
	'アモルファス (Amorphous)': 'Amorphous',
	'アリスソフト (AliceSoft)': 'AliceSoft',
	'イマジニア (Imagineer)': 'Imagineer',
	'ウルフチーム (WolfTeam)': 'Wolf Team',
	'エクステンド (Extend)': 'Extend',
	'エニックス (Enix)': 'Enix',
	'エルフ (Elf)': 'Elf',
	'エレクトロニック・アーツ・ビクター (Electronic Arts Victor)': 'Electronic Arts Victor',
	'カプコン (Capcom)': 'Capcom',
	'コナミ (Konami)': 'Konami',
	'コンプティーク (Comptiq)': 'Comptiq',
	'コスモス・コンピュータ (Cosmos Computer)': 'Cosmos Computer',
	'クエイト (Kueito)': 'Kueito',
	'システムサコム (System Sacom)': 'System Sacom',
	'システムソフト (System Soft)': 'System Soft',
	'シャープ (Sharp)': 'Sharp',
	'シンキングラビット (Thinking Rabbit)': 'Thinking Rabbit',
	'スタークラフト (Starcraft)': 'Starcraft',
	'ソフトプロ (Soft Pro)': 'Soft Pro',
	'タイトー (Taito)': 'Taito',
	'デービーソフト (dB-Soft)': 'dB-Soft',
	'ティーアンドイーソフト (T&E Soft)': 'T&E Soft',
	'ニデコム (Nidecom)': 'Nidecom',
	'パックスエレクトロニカ (Pax Electronica)': 'Pax Electronica',
	'ハドソン (Hudson Soft)': 'Hudson Soft',
	'バンダイ (Bandai)': 'Bandai',
	'ビング (Ving)': 'Ving',
	'ブラザー工業 (Brother Kougyou)': 'Brother Kougyou',
	'ブローダーバンドジャパン (Brøderbund Japan)': 'Brøderbund Japan',
	'ホームデータ (Home Data)': 'Home Data',
	'ポニカ (Pony Canyon)': 'Pony Canyon',
	'ポニカ (PonyCa)': 'Pony Canyon',
	'マイクロネット (Micronet)': 'Micronet',
	'マカダミアソフト (Macadamia Soft)': 'Macadamia Soft',
	'富士通 (Fujitsu)': 'Fujitsu',
	'工画堂スタジオ (Kogado Studio)': 'Kogado Studio',
	'日本ソフトバンク (Nihon SoftBank)': 'Nihon SoftBank',
	'日本テレネット (Nihon Telenet)': 'Telenet',
	'日本ファルコム (Nihon Falcom)': 'Nihon Falcom',
	'日本マイコン販売 (Nihon Micom Hanbai)': 'Nihon Micom Hanbai',
	'電波新聞社 (Dempa Shinbunsha)': 'Dempa',
	'サイベル (Cybelle)': 'Cybelle',
	'ジーエーエム (GAM)': 'GAM',
	'シグナワークス (Signa Works)': 'Signa Works',
	'シュールド・ウェーブ (Sur De Wave)': 'Sur De Wave',
	'スタジオみるく (Studio Milk)': 'Studio Milk',
	'トランスペガサス (Transpegasus)': 'Transpegasus',
	'バーディーソフト (Birdy Soft)': 'Birdy Soft',
	'ハード (Hard)': 'Hard',
	'ビクター音楽産業 (Victor Musical Industries)': 'Victor Musical Industries',
	'ファミリーソフト (Family Soft)': 'Family Soft',
	'フォーサイト (Foresight)': 'Foresight',
	'フォレスト (Forest)': 'Forest',
	'ポニーテールソフト (Ponytail Soft)': 'Ponytail Soft',
	'ミンク (Mink)': 'Mink',
	'富士通OA (Fujitsu OA)': 'Fujitsu',

	#YELLING CASE / other capitalisation stuff
	'BEC': 'Bec',
	'Dreamworks': 'DreamWorks',
	'DreamGear': 'dreamGEAR',
	'enix': 'Enix',
	'EPYX': 'Epyx',
	'HiTEC Software': 'HiTec Software',
	'Icom Simulations': 'ICOM Simulations',
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
	'Minscape': 'Mindscape',
	'Sydney Developmeent ': 'Sydney Development',
	'unknown': '<unknown>', #This shows up in sv8000 software list, so it might actually just be Bandai, but when you presume you make a pres out of u and me, so we'll just lump it in with the other unknowns
}

dont_remove_suffix = [
	#Normally we run junk_suffixes on stuff to remove "Corp" "Co." at the end but sometimes we shouldn't
	'Bit Corp', #We will then fix that up later
	'Zonov and Co.',
]
