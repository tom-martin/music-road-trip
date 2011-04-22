import urllib2
import urllib
import logging

logger = logging.getLogger(__name__)

class LastFmService:
    def __init__(self, cache, service_lock):
        self.loading_failures = []
        self.cache_count = 0
        self.last_count = 0
        self.lock = service_lock
        self.cache = cache


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

        if cached != None:
            self.cache_count += 1
            return cached

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

        self.write_to_cache(artist_name, similar)
    
        return similar

    def get_cache_percentage(self):
        return (float(self.cache_count) / (self.cache_count + self.last_count)) * 100

