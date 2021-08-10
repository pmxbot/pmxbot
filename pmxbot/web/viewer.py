import os
import random
import calendar
import datetime
import textwrap
import html
import urllib.parse
import operator
import contextlib
import functools

import cherrypy
import jinja2.loaders
import pytz
import inflect
import importlib_resources as resources

import pmxbot.core
import pmxbot.logging
import pmxbot.util

jenv = jinja2.Environment(loader=jinja2.loaders.PackageLoader('pmxbot.web'))
TIMEOUT = 10.0


colors = [
    "06F",
    "900",
    "093",
    "F0C",
    "C30",
    "0C9",
    "666",
    "C90",
    "C36",
    "F60",
    "639",
    "630",
    "966",
    "69C",
    "039",
    '7e1e9c',
    '15b01a',
    '0343df',
    'ff81c0',
    '653700',
    'e50000',
    '029386',
    'f97306',
    'c20078',
    '75bbfd',
]
random.shuffle(colors)


def get_context():
    c = pmxbot.config
    d = dict(
        request=cherrypy.request,
        name=c.bot_nickname,
        config=c,
        base=c.web_base,
        logo=c.logo,
    )
    if 'web byline' in c:
        d['byline'] = c['web byline']
    return d


def make_anchor(line):
    time, nick = line
    return "%s.%s" % (str(time).replace(':', '.'), nick)


def pmon(month):
    """
    P the month

    >>> print(pmon('2012-08'))
    August, 2012
    """
    year, month = month.split('-')
    return '{month_name}, {year}'.format(
        month_name=calendar.month_name[int(month)], year=year
    )


def pday(dayfmt):
    """
    P the day

    >>> print(pday('2012-08-24'))
    Friday the 24th
    """

    year, month, day = map(int, dayfmt.split('-'))
    return '{day} the {number}'.format(
        day=calendar.day_name[calendar.weekday(year, month, day)],
        number=inflect.engine().ordinal(day),
    )


class ChannelPage:
    month_ordinal = dict((calendar.month_name[m_ord], m_ord) for m_ord in range(1, 13))

    @cherrypy.expose
    def default(self, channel):
        page = jenv.get_template('channel.html')

        db = pmxbot.logging.Logger.store
        context = get_context()
        contents = db.get_channel_days(channel)
        months = {}
        for fn in sorted(contents, reverse=True):
            mon_des, day = fn.rsplit('-', 1)
            months.setdefault(pmon(mon_des), []).append((pday(fn), fn))
        context['months'] = sorted(months.items(), key=self.by_date, reverse=True)
        context['channel'] = channel
        return page.render(**context).encode('utf-8')

    @classmethod
    def by_date(cls, month_item):
        month_string, days = month_item
        return cls.date_key(month_string)

    @classmethod
    def date_key(cls, month_string):
        """
        Return a key suitable for sorting by month.

        >>> k1 = ChannelPage.date_key('September, 2012')
        >>> k2 = ChannelPage.date_key('August, 2013')
        >>> k2 > k1
        True
        """
        month, year = month_string.split(',')
        month_ord = cls.month_ordinal[month]
        return year, month_ord


class DayPage:
    @cherrypy.expose
    def default(self, channel, day):
        page = jenv.get_template('day.html')
        db = pmxbot.logging.Logger.store
        context = get_context()
        day_logs = db.get_day_logs(channel, day)
        data = [(t, n, make_anchor((t, n)), html.escape(m)) for (t, n, m) in day_logs]
        usernames = [x[1] for x in data]
        color_map = {}
        clrs = colors[:]
        for u in usernames:
            if u not in color_map:
                try:
                    color = clrs.pop(0)
                except IndexError:
                    color = "000"
                color_map[u] = color
        context['color_map'] = color_map
        context['history'] = data
        context['channel'] = channel
        context['pdate'] = "{pday} of {days}".format(
            pday=pday(day), days=pmon(day.rsplit('-', 1)[0])
        )
        return page.render(**context).encode('utf-8')


class KarmaPage:
    @cherrypy.expose
    def default(self, term=""):
        page = jenv.get_template('karma.html')
        context = get_context()
        karma = pmxbot.karma.Karma.store
        term = term.strip()
        if term:
            context['lookup'] = self.karma_comma(karma.search(term)) or [
                ('NO RESULTS FOUND', '')
            ]
        context['top100'] = self.karma_comma(karma.list(select=100))
        context['bottom100'] = self.karma_comma(karma.list(select=-100))
        return page.render(**context).encode('utf-8')

    @staticmethod
    def karma_comma(karma_results):
        """
        (say that 5 times fast)

        Take the results of a karma query (keys, value) and return the same
        result with the keys joined by commas.
        """
        return [(', '.join(keys), value) for keys, value in karma_results]


class SearchPage:
    @cherrypy.expose
    def default(self, term=''):
        page = jenv.get_template('search.html')
        context = get_context()
        db = pmxbot.logging.Logger.store

        # a hack to enable the database to create anchors when building search
        #  results
        db.make_anchor = make_anchor

        if not term:
            raise cherrypy.HTTPRedirect(cherrypy.request.base)
        terms = term.strip().split()
        results = sorted(db.search(*terms), key=lambda x: x[1], reverse=True)
        context['search_results'] = results
        context['num_results'] = len(results)
        context['term'] = term
        return page.render(**context).encode('utf-8')


class HelpPage:
    @cherrypy.expose
    def default(self):
        page = jenv.get_template('help.html')
        return page.render(**self.get_context()).encode('utf-8')

    @staticmethod
    @functools.lru_cache()
    def get_context():
        context = get_context()
        commands = []
        contains = []
        by_name = operator.attrgetter('name')
        for handler in sorted(pmxbot.core.Handler._registry, key=by_name):
            if type(handler) is pmxbot.core.CommandHandler:
                commands.append(handler)
            elif isinstance(handler, pmxbot.core.ContainsHandler):
                contains.append(handler)
        context['commands'] = commands
        context['contains'] = contains
        return context


class LegacyPage:
    """
    Forwards legacy /day/{channel}/{date}#{time}.{nick} in local time to
    the proper page at /day (in UTC).
    """

    timezone = pytz.timezone('US/Pacific')

    @cherrypy.expose
    def default(self, channel, date_s):
        """
        Return a web page that will get the fragment out and pass it to
        us so we can parse it.
        """
        return textwrap.dedent(
            """
            <html>
            <head>
            <script type="text/javascript">
                window.onload = function() {
                    fragment = parent.location.hash;
                    window.location.pathname=window.location.pathname.replace(
                        'legacy', 'legacy/forward')
                        + "/" + window.location.hash.slice(1);
                };
            </script>
            </head>
            <body></body>
            </html>
        """
        ).lstrip()

    @cherrypy.expose
    def forward(self, channel, date_s, fragment):
        """
        Given an HREF in the legacy timezone, redirect to an href for UTC.
        """
        time_s, sep, nick = fragment.rpartition('.')
        time = datetime.datetime.strptime(time_s, '%H.%M.%S')
        date = datetime.datetime.strptime(date_s, '%Y-%m-%d')
        dt = datetime.datetime.combine(date, time.time())
        loc_dt = self.timezone.localize(dt)
        utc_dt = loc_dt.astimezone(pytz.utc)
        url_tmpl = '/day/{channel}/{target_date}#{target_time}.{nick}'
        url = url_tmpl.format(
            target_date=utc_dt.date().isoformat(),
            target_time=utc_dt.time().strftime('%H.%M.%S'),
            **locals()
        )
        raise cherrypy.HTTPRedirect(url, 301)


class PmxbotPages:
    channel = ChannelPage()
    day = DayPage()
    karma = KarmaPage()
    search = SearchPage()
    help = HelpPage()
    legacy = LegacyPage()

    @cherrypy.expose
    def default(self):
        page = jenv.get_template('index.html')
        db = pmxbot.logging.Logger.store
        context = get_context()
        chans = []
        for chan in sorted(db.list_channels(), key=str.lower):
            last = db.last_message(chan)
            summary = [
                chan,
                last['datetime'].strftime("%Y-%m-%d %H:%M"),
                last['datetime'].date(),
                last['datetime'].time(),
                last['nick'],
                html.escape(last['message'][:75]),
                make_anchor([last['datetime'].time(), last['nick']]),
            ]
            chans.append(summary)
        context['chans'] = chans
        return page.render(**context).encode('utf-8')


def patch_compat(config):
    """
    Support older config values.
    """
    if 'web_host' in config:
        config['host'] = config.pop('web_host')
    if 'web_port' in config:
        config['port'] = config.pop('web_port')


def _setup_logging():
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False
    pmxbot.core._setup_logging()


def init_config(config={}):
    config.setdefault('web_base', '/')
    config.setdefault('host', '::0')
    config.setdefault('port', int(os.environ.get('PORT', 8080)))

    config = pmxbot.core.init_config(config)

    if not config.web_base.startswith('/'):
        config['web_base'] = '/' + config.web_base
    if config.web_base.endswith('/'):
        config['web_base'] = config.web_base.rstrip('/')
    if 'logo' not in config:
        web_base = config.web_base or '/'
        config['logo'] = urllib.parse.urljoin(web_base, 'pmxbot.png')

    return config


def resolve_file(mgr, filename):
    """
    Given a file manager (ExitStack), load the filename
    and set the exit stack to clean up. See
    https://importlib-resources.readthedocs.io/en/latest/migration.html#pkg-resources-resource-filename
    for more details.
    """
    path = resources.files('pmxbot.web.templates') / filename
    return str(mgr.enter_context(resources.as_file(path)))


def startup(config):
    patch_compat(config)

    config = init_config(config)

    _setup_logging()

    pmxbot.core._load_library_extensions()

    file_manager = contextlib.ExitStack()
    static = functools.partial(resolve_file, file_manager)

    # Cherrypy configuration here
    app_conf = {
        'global': {
            'server.socket_port': config.port,
            'server.socket_host': config.host,
            'server.environment': 'production',
            'engine.autoreload.on': False,
            # 'tools.encode.on': True,
            'tools.encode.encoding': 'utf-8',
        },
        '/pmxbot.png': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': static('pmxbot.png'),
        },
        '/Autolinker.js': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': static('Autolinker.js'),
        },
    }

    with file_manager:
        cherrypy.quickstart(PmxbotPages(), config.web_base, config=app_conf)


def run():
    startup(pmxbot.core.get_args().config)
