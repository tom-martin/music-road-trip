import urllib2
import urllib
from time import time, sleep
import logging
from pymongo import Connection
from datetime import datetime
logger = logging.getLogger('mongo_cache')

class MongoCache:
    def __init__(self, mongo_host, mongo_port, db_name, collection_name, cache_ttl):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.db_name = db_name
        self.collection_name = collection_name
        self.hit_count = 0
        self.miss_count = 0
        self.cache_ttl = cache_ttl

    def create_connection(self):
        return Connection(self.mongo_host, self.mongo_port)
        

    def get(self, cache_key):
        connection = self.create_connection()
        collection = connection[self.db_name][self.collection_name]
        cached = collection.find_one({"cache_key": cache_key})
        if cached != None:
            if (cached['created_date'] + self.cache_ttl) > datetime.utcnow():
                logger.debug("Found from cache " + cache_key)

                connection.disconnect()

                self.hit_count += 1
                return cached
            else:
                logger.info("Cache expired " + cache_key + ", removing")
                cache.remove(cached)
        
        connection.disconnect()
        self.miss_count += 1
        return None

    def put(self, cache_key, to_cache):
        connection = self.create_connection()
        collection = connection[self.db_name][self.collection_name]
        to_cache['cache_key'] = cache_key
        to_cache['created_date'] = datetime.utcnow()
        collection.insert(to_cache)
        connection.disconnect()
        
