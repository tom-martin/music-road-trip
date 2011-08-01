import urllib2
import urllib
import logging
import xml.etree.ElementTree as etree

logger = logging.getLogger(__name__)

class LastFmService:
    def __init__(self, api_key, cache, service_lock):
        self.loading_failures = []
        self.cache_count = 0
        self.last_count = 0
        self.lock = service_lock
        self.cache = cache
        self.api_key = api_key


    def get_from_cache(self, artist_name):
        cached = self.cache.get(artist_name)
        if cached != None:
            return cached['similar_artists']

        return None

    def write_to_cache(self, artist_name, similar_artists):
        cached_artist = {   "artist_name": artist_name,
                            "similar_artists": similar_artists}

        self.cache.put(artist_name, cached_artist)

    def escape_artist_name(self, artist_name):
        # quote_plus THEN quote, seems to be the only thing that works, also manually replace
        # . with %2E before the last quote
        return urllib.quote(urllib.quote_plus(artist_name.encode('utf-8')).replace('.', '%2E'))

    def get_similar_for_artist(self, artist_name):
        artist_name_esc = self.escape_artist_name(artist_name)

        logger.debug("Searching for " + artist_name)

        cached = self.get_from_cache(artist_name)

        if cached != None and cached.has_key('similar'):
            self.cache_count += 1
            return cached['similar']

        try:
            self.lock.acquire()
            url = 'http://ws.audioscrobbler.com/2.0/artist/' + artist_name_esc + '/similar.txt'
            result = urllib2.urlopen(url)
        except Exception, e:
            logger.warning("Failed to load " + artist_name + ": " + str(e))
            self.loading_failures.append(artist_name + ": " + str(e))
            return []
        finally:
            self.lock.release()

        similar_feed = result.read()

        self.last_count += 1
        logger.debug("Got from last.fm")
    
    
        to_cache = cached if cached != None else {}
        similar = []
        lines = similar_feed.splitlines()
        for line in lines:
            line_split = line.split(',')
            similarity = float(line_split[0])
            if similarity < 0.2:
                break

            artist = line_split[2]
            for i in range(3, len(line_split)):
                artist += "," + line_split[i]

            artist = artist.replace('&amp;', '&')
            artist = artist.replace('&quot;', '\'')
            similar.append(artist.decode('utf-8'))

        to_cache['name'] = artist_name
        to_cache['similar'] = similar
        self.write_to_cache(artist_name, to_cache)
    
        return similar

    def get_artist_info(self, artist_name):
        artist_name_esc = urllib.quote(artist_name.encode('utf-8'))

        logger.debug("Searching for artist info " + artist_name)

        cached = self.get_from_cache(artist_name)
        if cached != None and cached.has_key('image'):
            logger.debug("Got " + artist_name + " info from cache")
            return cached


        try:
            self.lock.acquire()
            url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=' + artist_name_esc +'&api_key=' + self.api_key
            result = urllib2.urlopen(url)
        except Exception, e:
            logger.warning("Failed to load " + artist_name + ": " + str(e))
            self.loading_failures.append(artist_name + ": " + str(e))
            return None
        finally:
            self.lock.release()
    
        to_cache = cached if cached != None else {}
        artist_details = etree.fromstring(result.read())

        artist = artist_details.find('artist')
        to_cache['name'] = artist.find('name').text

        images = filter(lambda c: c.tag == 'image', artist.getchildren())
        for image in images:
            if image.attrib['size'] == 'large':
                to_cache['image'] = image.text.replace('126', '126s')
                break

        logger.debug("Got " + artist_name + " info from last.fm")
        self.write_to_cache(artist_name, to_cache)
        return to_cache
        

        

    def get_cache_percentage(self):
        return (float(self.cache_count) / (self.cache_count + self.last_count)) * 100

