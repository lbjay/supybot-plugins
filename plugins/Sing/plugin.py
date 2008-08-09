
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import re, logging, time
from htmlentitydefs import name2codepoint
from urllib import urlencode
from urllib2 import Request, build_opener, HTTPError
from random import randint
from SOAPpy import SOAPProxy

from BeautifulSoup import \
    BeautifulStoneSoup as BSS, \
    BeautifulSoup as BS, StopParsing

logger = logging.getLogger('supybot')

def random_title(artist):
    searchurl = 'http://lyricsfly.com/search/search.php'
    postdata = urlencode({'sort': 1, 'options': 2, 'keywords': artist})
    soup = url2soup(searchurl, {}, postdata, xml=False)
    results = [a.string for a in soup.findAll('a', href=re.compile('^view.php'))]
    logger.info('num results: %d' % len(results))
    try:
        ret = results[randint(0, len(results) - 1)]
        return ret.encode('ascii', 'ignore')
    except:
        return 

def url2soup(url, qsdata={}, postdata=None, headers={}, xml=True):
    """
    Fetch a url and BeautifulSoup-ify the returned doc
    """
    ua = 'Zoia/1.0 (Supybot/0.83; Sing Plugin; http://code4lib.org/irc)'
    headers.update({'User-Agent': ua})

    params = urlencode(qsdata)
    if params:
        if '?' in url:
            url = "%s&%s" % (url,params)
        else:
            url = "%s?%s" % (url,params)
    logger.info('fetching %s, %s' % (url,postdata))
    req = Request(url,postdata,headers)
    opener = build_opener()
    doc = opener.open(req)
    data = doc.read()
    if xml:
        data = re.sub('&#[A-Za-z0-9]+;', '', data)
        soup = BSS(data, convertEntities=BSS.XML_ENTITIES)
    else:
        soup = BS(data, convertEntities=BS.HTML_ENTITIES)
    return soup

class Sing(callbacks.Plugin):
    """
    Usage: sing artist [:title|*] [:line|*] 
    """
    threaded = True

    def sotd(self, irc, msg, args):
        """
        Fetches song of the day from lyricswiki
        """
        try:
            server = SOAPProxy('http://lyricwiki.org/server.php')
            song = server.getSOTD()
            title = song['song']
            artist = song['artist']
            lyrics = song['lyrics']
            lyrics = re.sub(r'\n\n', ' ** ', lyrics)
            lyrics = re.sub(r'\n', ' / ', lyrics)
            irc.reply('%s by %s...' % (title, artist), prefixNick=False)
            time.sleep(2)
            irc.reply(lyrics, prefixNick=False)
            return
        except Exception, e:
            irc.reply('Error communicating with server: ' + e)
            return

    # get this here: http://lyricsfly.com/api/
    API_ID = 'f4c24c1183135cda8-temporary.API.access'

    def sing(self, irc, msg, args, input):
        """
        Fetches lyrics from the http://lyricsfly.com api --
        Usage: sing artist [:title|*] [:line|*] --
        Example: @sing bon jovi : wanted dead or alive
        """

        start_line = None
        try: 
            artist, title, start_line = map(lambda x: x.strip(), re.split('[:\-]', input))
            if start_line == '*':
                start_line = -1
            else:
                start_line = int(start_line)
            logger.info('%s, %s, %d' % (artist, title, start_line))
        except:
            try:
                artist, title = map(lambda x: x.strip(), re.split('[:\-]', input))
                logger.info('%s, %s' % (artist, title))
            except:
                artist = input
                try:
                    title = random_title(artist)
                    logger.info('%s, random title: %s' % (artist, title))
                except Exception, e:
                    irc.reply('Got exception %s: %s when searching for songs by %s' \
                    % (e.__class__, e, artist), prefixNick=True); 
                    return

        if title == '*':
            title = random_title(artist)

        # stoopid lyricsfly
        artist = artist.replace("'", '%')
        title = title.replace("'", '%')
        lyricsurl = 'http://lyricsfly.com/api/api.php?i=%s' % Sing.API_ID
        qsdata = {'a': artist, 't': title}

        try:
            soup = url2soup(lyricsurl, qsdata)
        except HTTPError, e:
            irc.reply('http error %s for %s' % (e.code, lyricsurl), prefixNick=True); return
        except StopParsing, e:
            irc.reply('parsing error %s for %s' % (e.code, lyricsurl), prefixNick=True); return

        songs = soup('sg')
        if not songs:
            irc.reply('No results for "%s"' % input); return
            return
        song = songs[randint(0, len(songs) - 1)]
        if not song('id'):
            irc.reply('No results for "%s"' % input); return
            return

        if re.search(r'expired', str(song.tx)):
            irc.reply('the dumb lyricsfly temporary API ID has expired')
            return

        lyrics = song.tx.string.replace('[br]','\n')

        if re.search('instrumental', lyrics, re.I):
            irc.reply("hums %s by %s" % (song.tt.string, song.ar.string),
                prefixNick=False, action=True)
            return

        titlematch = re.compile(title, re.I | re.MULTILINE)
        lines = re.split('[\n\r]+', lyrics) 
        meta = ['lyricsfly','written by','chorus']
        for m in meta:
            lines = [l for l in lines if not re.search(m, l, re.I)]
       
        if not start_line:
            try:
                start_line = [titlematch.search(x) and True for x in lines].index(True)
                logger.info('title matched line %d' % start_line)
            except:
                try:
                    start_line = randint(0,len(lines))
                    logger.info('using random line %d', start_line)
                except:
                    irc.reply("I got an empty song")
                    return

        end_line = len(lines)
        if start_line == -1:
            resp = lines
        else:
            end_line = start_line + 4
            while end_line >= len(lines):
                end_line -= 1; start_line -= 1
            resp = lines[start_line:end_line]

        logger.info('start:end = %d:%d' % (start_line, end_line))
        resp = ' / '.join([l for l in resp if re.search('\S', l)])
        resp = resp.encode('ascii', 'ignore')

        irc.reply(resp, prefixNick=False)

    sing = wrap(sing, ['text'])


Class = Sing


