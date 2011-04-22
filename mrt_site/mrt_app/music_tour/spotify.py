import urllib2
import urllib
import logging
import xml.etree.ElementTree as etree

logger = logging.getLogger(__name__)

class SpotifyMetaService:
    def __init__(self, cache, service_lock):
        self.REQUIRED_TERRITORY = "GB"
        self.MAX_TRACKS = 5
        self.lock = service_lock
        self.cache = cache


    def get_from_cache(self, artist_name):
        cached = self.cache.get(artist_name)
        if cached is not None:
            return cached['tracks']

        return None

    def write_to_cache(self, artist_name, tracks):
        to_cache = {'artist_name': artist_name,
                    'tracks': tracks}

        self.cache.put(artist_name, to_cache)
    
    def get_tracks(self, artist_name):

        artist_name_esc = urllib.quote(artist_name.encode('utf-8'))
        tracks_cached = self.get_from_cache(artist_name)

        if tracks_cached != None:
            return tracks_cached
        else:

            url = 'http://ws.spotify.com/search/1/track?q=' + artist_name_esc
            try:
                self.lock.acquire()
                logger.debug("Loading " + url)
                result = urllib2.urlopen(url)
                tracks_string = result.read()

            except Exception, e:
                logger.warning("Failed to load " + artist_name + ": " + str(e))
                # TODO
                #self.loading_failures.append(artist_name + ": " + str(e))
                return []
            finally:
                self.lock.release()

        tracks = etree.fromstring(tracks_string)
        # Fucking namespaces!
        tracks = filter(lambda c: c.tag == '{http://www.spotify.com/ns/music/1}track', tracks)

        matching_tracks = []
        for track in tracks:
            track_artist_name = self.get_artist_name(track)
            if track_artist_name != None and track_artist_name.lower() == artist_name.lower() and self.track_available_in_req_territories(track):
                matching_tracks.append(track.attrib['href'])
        
            if len(matching_tracks) >= self.MAX_TRACKS:
                break

        self.write_to_cache(artist_name, matching_tracks)

        return matching_tracks

    def track_available_in_req_territories(self, track):
        album = track.find('{http://www.spotify.com/ns/music/1}album') 
        availability = None
        if album != None:
            availability = album.find('{http://www.spotify.com/ns/music/1}availability')
        territories = None
        if availability != None:
            territories = availability.find('{http://www.spotify.com/ns/music/1}territories')

        if territories != None:
            return territories.text != None and "GB" in territories.text

    def get_artist_name(self, track):
        track_artist = track.find('{http://www.spotify.com/ns/music/1}artist')
        if track_artist:
            return track_artist.find('{http://www.spotify.com/ns/music/1}name').text.encode('utf-8')

