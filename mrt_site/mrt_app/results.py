import logging
from pymongo import Connection
from music_tour.mongo_cache import MongoCache
from datetime import timedelta

logger = logging.getLogger(__name__)

def create_key(artist_one, artist_two):
    if artist_one.lower() <= artist_two.lower():
        return False, artist_one.lower() + "|" + artist_two.lower()
    else:
        return True, artist_two.lower() + "|" + artist_one.lower()

class ResultsService:
    def __init__(self, mongo_host, mongo_port, db_name):
        self.mongo_cache = MongoCache(mongo_host, mongo_port, db_name, 'results_cache', timedelta(weeks=1))

    def get(self, artist_one, artist_two):
        key_reversed, key = create_key(artist_one, artist_two)

        results_cache = self.mongo_cache.get(key)
        if results_cache == None:
            return None

        results = results_cache['results']

        if key_reversed and results != None:
            results.reverse()

        return results

    def put(self, artist_one, artist_two, results):
        key_reversed, key = create_key(artist_one, artist_two)
        # Copy in case we need to reverse
        results = list(results)

        if key_reversed:
            results.reverse()

        self.mongo_cache.put(key, {'results': results})
    
    
        
