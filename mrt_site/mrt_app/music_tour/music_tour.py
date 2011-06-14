from last_fm import LastFmService
from spotify import SpotifyMetaService
import random
from mongo_cache import MongoCache
import logging
from datetime import timedelta
from simple_mongo_service_lock import SimpleMongoServiceLock


logger = logging.getLogger(__name__)

class MusicTourService:
    def __init__(self, mongo_host, mongo_port):

        last_lock = SimpleMongoServiceLock(mongo_host, mongo_port, 'music_tour', 'last_lock', 1, 30)
        self.last_fm = LastFmService(MongoCache(mongo_host, mongo_port, 'music_tour', 'last_cache', timedelta(weeks=24)), last_lock)
        spotify_lock = SimpleMongoServiceLock(mongo_host, mongo_port, 'music_tour', 'spotify_lock', 1, 30)
        self.spotify = SpotifyMetaService(MongoCache(mongo_host, mongo_port, 'music_tour', 'spotify_cache',timedelta(weeks=24)), spotify_lock)

    def search_for_artist(self, artist_name):
        return self.spotify.get_tracks(artist_name)

    def find_path(self, artist_one, artist_two, blacklist):
        logger.debug("Black list" + str(blacklist))

        artist_one_out = set()
        artist_one_out.add(artist_one)
        artist_one_parent = {artist_one: None}

        artist_two_out = set()
        artist_two_out.add(artist_two)
        artist_two_parent = {artist_two: None}

        step_count = 0

        linking_artist = None

        queue_one = [artist_one]
        queue_two = [artist_two]
        while len(queue_one) > 0 and len(queue_two) > 0 and linking_artist == None:
            step_count+=1
            parent = queue_one[0]
            queue_one.remove(parent)

            artists = self.last_fm.get_similar_for_artist(parent)
            for artist in artists:
                if not artist in artist_one_out:
                    artist_one_out.add(artist)
                    if not artist in blacklist:
                        queue_one.append(artist)
                        artist_one_parent[artist] = parent

                        if artist in artist_two_out:
                            linking_artist = artist
                            break;

            if linking_artist != None:
                break

            parent = queue_two[0]
            queue_two.remove(parent)

            artists = self.last_fm.get_similar_for_artist(parent)
            for artist in artists:
                if not artist in artist_two_out:
                    artist_two_out.add(artist)
                    if not artist in blacklist:
                        queue_two.append(artist)
                        artist_two_parent[artist] = parent

                        if artist in artist_one_out:
                            linking_artist = artist
                            break;

            if linking_artist != None:
                break

        route = []
        if linking_artist != None:

            current = linking_artist
            while current != None:
                route.insert(0, current)
                current = artist_one_parent[current]

            current = artist_two_parent[linking_artist]
            while current != None:
                route.append(current)
                current = artist_two_parent[current]

            logger.debug(linking_artist + " is in both graphs (" + str(step_count) + ")")

        return route

    def find_spotify_path(self, artist_one, artist_two, blacklist):
        if len(self.spotify.get_tracks(artist_one)['matching_tracks']) == 0:
            raise Exception("No spotify tracks found for " + artist_one)

        if len(self.spotify.get_tracks(artist_two)['matching_tracks']) == 0:
            raise Exception("No spotify tracks found for " + artist_two)

        # Copy the blacklist so the param needn't be a set
        blacklist = set(blacklist)

        route = []
        retry = 0    
        while len(route) == 0 and retry < 100:
            retry += 1
            route = self.find_path(artist_one, artist_two, blacklist)
            logger.debug("Cache hit percentage " + str(self.last_fm.get_cache_percentage()))

            if len(self.last_fm.loading_failures) > 0:
                logger.warning(self.last_fm.loading_failures)


            if len(route) == 0:
                # TODO exception class
                raise Exception("No path found")

            for artist in route:
                artist_tracks = self.spotify.get_tracks(artist)
                if len(artist_tracks['matching_tracks']) == 0:
                    route = []
                    logger.debug("Blacklisting " + artist + " (no spotify tracks found) and starting over")
                    tracks = []
                    blacklist.add(artist)
                    break

        if len(route) == 0:
            # TODO exception class
            raise Exception("No path found")
        return route

    def get_random_tracks_for_route(self, route, track_count):
        tracks = []
        chosen_tracks = {}
        
        tracks_per_artist = max(1, track_count / len(route))

        remaining_tracks_req = track_count

        all_artists_tracks = []
        for artist in route:
            artist_tracks = self.spotify.get_tracks(artist)
            all_artists_tracks.append(artist_tracks)
            chosen_tracks[artist.lower()] = []
            for i in range(0, min(len(artist_tracks['matching_tracks']), tracks_per_artist)):
                chosen_tracks[artist.lower()].append(select_random_and_remove(artist_tracks['matching_tracks']))
                remaining_tracks_req -= 1

        print "random artists: "
        # Randomly pad out the list if it's not full yet and we haven't run out of available tracks
        while remaining_tracks_req > 0 and sum(map(lambda at: len(at['matching_tracks']), all_artists_tracks)) > 0:
            random_artist_tracks = random.choice(all_artists_tracks)['matching_tracks']
            if remaining_tracks_req > 0 and len(random_artist_tracks) > 0:
                random_track = select_random_and_remove(random_artist_tracks)
                chosen_tracks[random_track['artist_name'].lower()].append(random_track)
                remaining_tracks_req -= 1

        for artist in route:
            tracks += chosen_tracks[artist.lower()]
        return tracks

def select_random_and_remove(tracks):
    random_track = random.choice(tracks)
    tracks.remove(random_track)
    return random_track

