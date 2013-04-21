
== Welcome ==
{{https://bitbucket.org/yougov/pmxbot/raw/8af8328a91ce/pmxbotweb/templates/pmxbot.png|pmxbot skynet logo}}{{https://bitbucket.org/yougov/pmxbot/raw/tip/horrible-logos-pmxbot.gif|pmxbot horrible logo}}

Welcome to pmxbot!

== Feature List ==
While pmxbot's feature set is always growing and changing, here's a list of the current features included as part of version 1004.4.

|= Command |= Aliases |= Description |
| anchorman | Quote Anchorman. | [] |
| bender | Quote Bender, a la http://en.wikiquote.org/wiki/Futurama | [<pmxbot.core.AliasHandler object at 0x0000000003824208>] |
| excuse | Provide a convenient excuse | [<pmxbot.core.AliasHandler object at 0x000000000381F518>] |
| grail | I questing baby | [] |
| hal | HAL 9000 | [<pmxbot.core.AliasHandler object at 0x0000000003824438>] |
| hangover | Quote hangover. | [] |
| log | Enable or disable logging for a channel; use 'please' to start logging and 'stop please' to stop. | [] |
| logs | Where can one find the logs? | [] |
| quote | If passed with nothing then get a random quote. If passed with some string then search for that. If prepended with "add:" then add it to the db, eg "!quote add: drivers: I only work here because of pmxbot!" | [<pmxbot.core.AliasHandler object at 0x000000000381FE80>] |
| r | Quote the R mailing list | [<pmxbot.core.AliasHandler object at 0x0000000003824630>] |
| simpsons | Quote the Simpsons, a la http://snpp.com/ | [<pmxbot.core.AliasHandler object at 0x0000000003824390>] |
| strike | Strike last <n> statements from the record | [] |
| where | When did pmxbot last see <nick> speak? | [<pmxbot.core.AliasHandler object at 0x00000000037B95F8>, <pmxbot.core.AliasHandler object at 0x00000000037B9B38>, <pmxbot.core.AliasHandler object at 0x00000000037B9B70>] |
| zoidberg | Quote Zoidberg, a la http://en.wikiquote.org/wiki/Futurama | [<pmxbot.core.AliasHandler object at 0x00000000038242E8>] |

== Example Session ==
It's sometimes hard to get a sense of what pmxbot is like if you've never used it, so here's an example IRC discussion where we heavily use pmxbot.

{{{
< chmullig> cperry: in cologne?
< cperry> !m chmullig
<@pmxbot> you're doing good work, chmullig!
< cperry> indeed
< chmullig> awesome
< cperry> yeah
< chmullig> I'm recording a little chat for the pmxbot website
< cperry> ooooo
< cperry> is this getting recorded?
< chmullig> !8ball is pmxbot awesome?
<@pmxbot> Most likely.
< chmullig> yes, yes it is
< cperry> good thing I didn't insult the person I was going to insult
< cperry> because I love everyone!
< cperry> !bless
< chmullig> !cheer everyone
 * pmxbot blesses the day!
 * pmxbot cheers for everyone!
< cperry> !curse insulting people
 * pmxbot curses insulting people!
< chmullig> !w Washington, DC | Cologne
<@pmxbot> Washington D.C., DC. Currently: 70F/21C, Cloudy.    Mon: 73F/22C, Thunderstorm
<@pmxbot> Cologne, North Rhine-Westphalia. Currently: 43F/6C, Mostly Cloudy.    Mon: 46F/7C, Chance of Rain
< cperry> in fact, every time I think about insulting people, I just want to
< cperry> !dance
<@pmxbot> O-\-<
<@pmxbot> O-|-<
<@pmxbot> O-/-<
< chmullig> !def dancing
<@pmxbot> Wikipedia says: Dance (from French danser, perhaps from Frankish) is an art form that generally
          refers to movement of the body, usually rhythmic and to music, used as a form of expression,
          social interaction or presented in a spiritual or performance setting.
< cperry> hmm
< cperry> !urb dancing
<@pmxbot> Urban Dictionary says dancing: Formal term meaning: to move with unhindered grace around an area
          with the presence of another enjoying the same activity.  Urban term: Humping someone in public
          Sad world isn't it.
< cperry> ewwww
< chmullig> !g salsa dancing classes in washington, dc
<@pmxbot> http://www.findoutdc.com/gym/dance.shtml - Dance Lessons and Studios - Latin Salsa Merengue
          Tango Ballroom
< cperry> !otrail dancing
<@pmxbot> dancing made it to oregon. Time to party with schmichael.
< chmullig> !ylunch Washington, DC 10m
<@pmxbot> Tonic at Quigley's Pharmacy @ 2036 G St Nw -
          http://local.yahoo.com/info-38772621-tonic-at-quigley-s-pharmacy-washington
< cperry> yes! my favorite!
< chmullig> Are you teaching the germans sql on rails?
<@pmxbot> Only 76,417 lines...
< cperry> nah, they prefer spss
< chmullig> thank you, pmxbot
<@pmxbot> I'm afraid that would violate the fire code.

}}}
