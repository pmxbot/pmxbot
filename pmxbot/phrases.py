import pathlib


ball8_opts = {
    "Signs point to yes.": 21,
    "Yes.": 21,
    "Most likely.": 21,
    "Without a doubt.": 21,
    "Yes - definitely.": 21,
    "As I see it, yes.": 21,
    "You may rely on it.": 18,
    "Outlook good.": 18,
    "It is certain.": 18,
    "It is decidedly so.": 18,
    "Reply hazy, try again.": 1,
    "Better not tell you now.": 1,
    "Ask again later.": 1,
    "Concentrate and ask again.": 1,
    "Cannot predict now.": 1,
    "Six of one, half-dozen of another.": 1,
    "Hold on, let me check the latest polls.": 1,
    "Would you like fries with that?": 1,
    "Will you go to lunch? Go to lunch. Will you go to lunch?": 1,
    "I grow weary of your questions.": 1,
    "Get away from me, kid, you bother me.": 1,
    "Go, and never darken my towels again.": 1,
    "Your question fills a much-needed gap.": 1,
    "I have heard your question and much like it.": 1,
    "Only reading entrails can answer that.": 1,
    "That is alas a mystery.  Unless you ask again.": 1,
    "Your question makes my circuits hurt.": 1,
    "You say 'tom ay to,' I say 'no way, Joe.'": 1,
    "Doubt it.": 10,
    "No.": 10,
    "Indeed.": 10,
    "Yes, please.": 10,
    "Inevitably.": 10,
    "Probably.": 10,
    "Unquestionably.": 10,
    "Nay.": 1,
    "When pigs fly.": 1,
    "Whatever happened to crossing my palms with silver?": 1,
    "Ask the NSA.": 1,
    "Not likely before the heat death of the universe.": 1,
    "Not if wishes were horses.  Neigh.": 1,
    "A little birdie told me no.": 1,
    "Pipe down in the peanut gallery, willya?": 1,
    "My sources say no.": 18,
    "Very doubtful.": 18,
    "My reply is no.": 18,
    "Outlook not so good.": 18,
    "Don't count on it.": 18,
    "Not a chance.": 18,
    "Highly unlikely.": 18,
    "NFW.": 25,
    "You're more likely to get rich off you.l.": 18,
    "Not a chance, buddy.": 18,
    "p < .05": 18,
    "Sample size too small.": 18,
    "Tentatively confirmed.": 18,
}

certainty_opts = [
    "definitely",
    "probably",
    "maybe",
    "possibly",
    "perhaps",
    "certainly",
    "questionably",
    "unquestionably",
    "without doubt",
    "absolutely",
]

weapon_opts = [
    'shiv',
    'shank',
    'knife',
    'spork',
    'razor',
    'cocktail sword',
    'spatula',
    'scimitar',
    'pipe',
    'bat',
    'stickbat',
    'wooden pallet',
]

weapon_adjs = [
    'rusty',
    'dirty',
    'broken',
    'gleaming',
    'serrated',
    'dull',
    'sharp',
    'bent',
    'flaming',
]

violent_acts = [
    'stabs',
    'cuts',
    'maims',
    'sticks',
    'shivs',
    'shanks',
    'disembowels',
    'minces',
    'perforates',
    'lobotomizes',
    'slashes',
    'furiously pokes',
]

fight_victories = [
    'defeats',
    'destroys',
    'dominates',
    'edges',
    'pwns',
    'crushes',
    'obliviates',
    'trounces',
    'sneaks by',
    'hires a hitman to take care of',
]

fight_descriptions = [
    'a barroom brawl',
    'a cagematch',
    'a fight in the octagon',
    'a fight to the death',
    'a fight to the pain',
    'a slapfest',
    'a thumbwrestling match',
    'a battle with dull, flaming scimitars',
    'a gentlemanly game of chess',
    'a bat fight',
    'a stickbat fight',
    'with a crowbar to the kneee.',
]

dowski_praises = [
    "and I defer to your distinguished discernment",
    "and I honor your legacy",
    "and I'm always astounded by your acumen",
    "cursing those who would deny you deference",
    "greeting your grand gloriousness with groveling",
    "humbled by your unbelievable understanding",
    "long live your long-leggedness",
    "may all respect you and your recognized renowned remarkableness",
    "may all of your successes be glorious",
    "may your burdens be light upon your back",
    "may the road rise up to meet you",
    "may the wind be always at your back",
    "may the sun shine warm upon your face",
    "may all of your enemies be !shivved",
    "oh great ruler of all things IS",
    "oh wondrous wonderboy of the midwest",
    "oh phenomenal prodigy of python programming",
    "oh loquacious liege",
    "oh happy harbinger of happiness",
    "saluting your supreme superiority",
    "with my obeisance to your ohioness",
    "viva la dowski",
    "(everyone knows you're the best)",
    "you're much more splendorous than windowsill to me",
    "chowski or dowski, your prowess is unparalleled",
    "dowski manor may be in canton, but it must be heavenly",
]

holger_dawg = [
    "WAZZUP DAWG?",
    "wassup, my dawg brotha?",
    "you be trippin', my homey dawg",
    "you be comin' to liberate, holger the dane dawg?",
    (
        "you can put my dawg holger into da hood, but "
        "you'll never put da hood into my dawg holger"
    ),
]

yuckvl = [
    'grinds teeth',
    'shudders',
    'gags',
    'blinks away tears',
    'coughs',
    'stares',
    'drops to the ground curled in the fetal position',
    'spits',
    'wards off the evil eye',
    'dies a little more inside',
    'contemplates suicide',
    'cackles maniacally and slowly goes mad',
    'starts to reread Ecclesiastes',
    'blames this fiasco on Carl Friedrich Gauss',
    'ponders a career change',
    'twitches',
    'considers alcoholism',
    'remains very, very still',
    'hisses',
    'groans',
]

clapvl = ['slowly', 'sadly', 'quietly', 'briefly', 'halfheartedly']

advl = ['clearly', 'likely', 'utterly', 'deeply', 'profoundly']

adjl = ['unimpressed', 'overwhelmed', 'verklemmt', 'distracted', 'awed']

fcverbs = [
    'aggregate',
    'architect',
    'benchmark',
    'brand',
    'cultivate',
    'deliver',
    'deploy',
    'disintermediate',
    'drive',
    'e-enable',
    'embrace',
    'empower',
    'enable',
    'engage',
    'engineer',
    'enhance',
    'envisioneer',
    'evolve',
    'expedite',
    'exploit',
    'extend',
    'facilitate',
    'generate',
    'grow',
    'harness',
    'implement',
    'incentivize',
    'incubate',
    'innovate',
    'integrate',
    'iterate',
    'leverage',
    'matrix',
    'maximize',
    'mesh',
    'monetize',
    'morph',
    'optimize',
    'orchestrate',
    'productize',
    'recontextualize',
    'redefine',
    'reintermediate',
    'reinvent',
    'repurpose',
    'revolutionize',
    'scale',
    'seize',
    'strategize',
    'streamline',
    'syndicate',
    'synergize',
    'synthesize',
    'target',
    'transform',
    'transition',
    'unleash',
    'utilize',
    'visualize',
    'whiteboard',
]

fcadjectives = [
    '24/365',
    '24/7',
    'B2B',
    'B2C',
    'back-end',
    'best-of-breed',
    'bleeding-edge',
    'bricks-and-clicks',
    'clicks-and-mortar',
    'collaborative',
    'compelling',
    'cross-platform',
    'cross-media',
    'customized',
    'cutting-edge',
    'distributed',
    'dot-com',
    'dynamic',
    'e-business',
    'efficient',
    'end-to-end',
    'enterprise',
    'extensible',
    'frictionless',
    'front-end',
    'global',
    'granular',
    'holistic',
    'impactful',
    'innovative',
    'integrated',
    'interactive',
    'intuitive',
    'killer',
    'leading-edge',
    'magnetic',
    'mission-critical',
    'next-generation',
    'one-to-one',
    'open-source',
    'out-of-the-box',
    'plug-and-play',
    'proactive',
    'real-time',
    'revolutionary',
    'rich',
    'robust',
    'scalable',
    'seamless',
    'sexy',
    'sticky',
    'strategic',
    'synergistic',
    'transparent',
    'turn-key',
    'ubiquitous',
    'user-centric',
    'value-added',
    'vertical',
    'viral',
    'virtual',
    'visionary',
    'web-enabled',
    'wireless',
    'world-class',
]

fcnouns = [
    'action-items',
    'applications',
    'architectures',
    'bandwidth',
    'channels',
    'communities',
    'content',
    'convergence',
    'deliverables',
    'e-business',
    'e-commerce',
    'e-markets',
    'e-services',
    'e-tailers',
    'experiences',
    'eyeballs',
    'functionalities',
    'infomediaries',
    'infrastructures',
    'initiatives',
    'interfaces',
    'markets',
    'methodologies',
    'metrics',
    'mindshare',
    'models',
    'networks',
    'niches',
    'paradigms',
    'partnerships',
    'platforms',
    'portals',
    'relationships',
    'ROI',
    'synergies',
    'web-readiness',
    'schemas',
    'solutions',
    'supply-chains',
    'systems',
    'technologies',
    'users',
    'portals',
    'web services',
]

jobs1 = [
    "Assistant",
    "Internal",
    "External",
    "Foreign",
    "Domestic",
    "Deputy",
    "Junior",
    "Senior",
    "Regional",
    "Level B",
    "Level C",
    "Inter",
    "Intra",
    "YouGov",
    "Executive",
    "Special",
    "Polimetrix",
    "Primary",
    "Lead",
    "Backup",
    "Chief",
]

jobs2 = [
    "Project",
    "Systems",
    "Marketing",
    "Purchasing",
    "Communications",
    "Sales",
    "Financial",
    "Accounting",
    "Personnel",
    "Engineering",
    "Information",
    "Customer Service",
    "Operations",
    "Development",
    "Surveys",
    "Panel",
    "Database",
    "Projects",
    "Analytics",
]

jobs3 = [
    "Manager",
    "Specialist",
    "Coordinator",
    "Administrator",
    "Analyst",
    "Planner",
    "Processor",
    "Consultant",
    "Clerk",
    "Officer",
    "Monitor",
    "Associate",
    "Trainee",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VP",
    "EVP",
    "SVP",
    "Director",
    "Developer",
    "Trainer",
    "Contractor",
    "Consultant",
    "Executive",
]

otrail_actions = (
    ['has'] * 6
    + ['has died from'] * 6
    + [
        'lost the trail. Lose 3 days.',
        'took the ferry across the river safely.',
        'forded the river safely.',
        'capsized while floating across the river.',
        'drowned.',
        'killed a bear.',
        'killed a buffalo.',
        'lost an ox.',
        'made it to oregon. Time to party with schmichael.',
        'finds wild fruit.',
        'traded with Indians.',
        'passes a gravesite.',
        'had no trouble floating the wagon across.',
        'is taking the rapids.',
        'is attacked by ninjas. Lose 8 days.',
        'is attacked by reavers and dies.',
    ]
)

otrail_issues = [
    'a fever',
    'dysentery',
    'measles',
    'cholera',
    'typhoid',
    'exhaustion',
    'a snake bite',
    'a broken leg',
    'a broken arm',
    'swine flu',
]


def text_lines(name):
    pkg_root = pathlib.Path(__file__).parent
    filename = '{name}.txt'.format_map(locals())
    path = pkg_root / filename
    with path.open() as strm:
        return list(map(str.rstrip, strm))


klingonisms = text_lines('klingonisms')

murphys_laws = text_lines("murphy's laws")

socialstrategies = text_lines("social strategies")

# passive-aggresive statement generator
adj_intros = [
    'your %s is legendary',
    'I love how your %s shows up in your work',
    'dream big, because %s is going to pay off for you big-time',
    'somehow your %s always manages to shine through',
    'if only we all possessed your %s',
    'you have rare %s',
    'even if I tried, I couldn\'t replicate your %s',
    'few can compete with your epic %s',
    'I always stop and smile at the telltale %s when correcting your mistakes',
]

adjs = [
    'incompetence',
    'laziness',
    'ignorance',
    'frailty',
    'lack of attention to detail',
    'BO',
    'stupidity',
    'lack of personality',
    'clever decision',
    'ability to "introcude a failure"',
]

farewells = [
    'Hugs and kisses',
    'Keep up the good work',
    'Chin up',
    'I hope you rot',
    'Have a great day',
    'Must get back to work',
    'Thanks for everything',
    'Your BFF',
    'Don\'t ever change',
    'Have a nice life',
    'Don\' stop bragplaining',
]

direct_apologies = [
    "%(a)s profusely apologizes to %(b)s",
    "%(a)s sincerely apologizes to %(b)s",
    (
        "%(a)s would like to apologize to %(b)s for any physical, "
        "emotional, or mental anguish %(a)s's action, justified as "
        "they may have been, caused."
    ),
    (
        "%(a)s would like to apologize to %(b)s for any physical, "
        "emotional, or mental anguish %(a)s's action, caused."
    ),
    "%(b)s: %(a)s is like sorry or something.",
]

apologies = [
    "%(a)s is sorry.",
    (
        "%(a)s would like to tearfully apologize to everyone in "
        "a widely publicized press conference."
    ),
    "%(a)s profusely apologizes.",
    "%(a)s sincerely apologizes.",
    (
        "%(a)s would like to apologize for any physical, emotional, "
        "or mental anguish that %(a)s's actions may have caused."
    ),
    (
        "%(a)s apologizes and would like to point out there is no "
        "reason legal action to be taken."
    ),
    "%(a)s is sorry or something.",
]

interview_excuses = [
    "I need to go to the Dentist",
    "I have a Doctor's appointment",
    (
        "my little brother got his arm stuck in the microwave, and my "
        "mom had to take him to the hospital and my grandma freaked out "
        "and dropped acid and hijacked a busload of penguins, so it's kind "
        "of a family crisis."
    ),
    "I need to go car shopping",
    "I have an appointment with an attorney to make a will",
    "my grandmother's funeral is today",
    "I need to go to the DMV",
    "I have a terrible case of diarrhea",
    "I need to get some allergy shots",
    "the power went out in Tennessee",
    "um, a huge snowpocalypse hit DC",
    '''I'm getting lunch with a "friend"''',
    "I'm heading off to a concert",
    '''It looks like I'll be "working" from "home" today''',
    (
        "I've been maliciously sunburned, and need to stay home and "
        "get jumped by my chihuahuas"
    ),
    "I need to go get a haircut",
    "I stepped out to get my marriage license",
    "I, um...",
    "I, um... won't be in...",
    'my VPN connectiond dropped, so I took the opportunity to grab some food.',
    'sorry, I ran over a beer bottle on the way in and flatted',
    'I exceeded my internet quota, so I needed to find another connection',
    'I took the wrong bus this morning. Again.',
    'I was held up by CalTrain delays',
    'CalTrain decided to help our overpopulation problem this morning',
]
