from pymongo import Connection
from datetime import datetime
from socket import gethostname;

from os import getpid
import threading
from time import time, sleep
import logging

logger = logging.getLogger(__name__)

class SimpleMongoServiceLock:
    def __init__(self, mongo_host, mongo_port, db_name, lock_name, time_to_wait, stale_lock_timeout):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.db_name = db_name
        self.time_to_wait = time_to_wait
        self.lock_name = lock_name
        self.stale_lock_timeout = stale_lock_timeout

    def create_connection(self):
        return Connection(self.mongo_host, self.mongo_port)

    def get_lock_state(self, locks):
        return locks.find_one({'lock_name': self.lock_name})

    def get_worker_id(self):
        return gethostname() + str(getpid()) + str(threading.current_thread().ident)
        

    def acquire(self):
        lock_acquired = False
        connection = self.create_connection()
        locks = connection[self.db_name]["smsl_lock"]

        worker_id = self.get_worker_id()

        while not lock_acquired:
            lock_state = self.get_lock_state(locks)

            logger.debug("Lock state " + str(lock_state))

            if lock_state != None and (time() - lock_state['time']) > self.stale_lock_timeout:
                logger.warn("Stale lock detected")
                locks.remove(lock_state)
                lock_state = None

            if lock_state == None:
                logger.warn("Creating fresh lock. Must have been a stale lock or empty db")
                fresh_lock = {'lock_name': self.lock_name, 'worker_id': 'worker_id_init', 'state': 'released', 'time': time()} 
                locks.insert(fresh_lock)
                continue

            if lock_state['state'] == 'acquired' and lock_state['worker_id'] == worker_id:
                logger.debug(self.lock_name + "Acquired")
                lock_acquired = True
                continue

            if lock_state['state'] == 'released' and (time() - lock_state['time']) > self.time_to_wait:
                lock_request = {'lock_name': self.lock_name, 'worker_id': worker_id, 'state': 'acquired', 'time': time()} 
                locks.find_and_modify({'lock_name': self.lock_name, 'worker_id': lock_state['worker_id']}, lock_request)
                continue
        
            logger.debug('Waiting for ' + self.lock_name + ' lock')
            sleep(self.time_to_wait)
    
        connection.disconnect()
        
    def release(self):
        connection = self.create_connection()
        locks = connection[self.db_name]["smsl_lock"]
        locks.find_and_modify({'lock_name': self.lock_name, 'worker_id': self.get_worker_id()}, {"$set": {'state': 'released'}})
        connection.disconnect()


