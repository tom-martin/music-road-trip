import urllib2
import urllib
import xml.etree.ElementTree as etree
from time import time, sleep
import json

import sys

base_url = sys.argv[1]
api_key = sys.argv[2]

def get_artist_names(method='chart.gettopartists'):

    page = 1
    total_pages = 10000

    artist_names = []

    while page < total_pages:
        url = 'http://ws.audioscrobbler.com/2.0/?method=' + method + '&api_key=' + api_key+ '&limit=100&page=' + str(page)
        print("Loading url " + url)
        result = urllib2.urlopen(url)

        print("Sleeping for 1 second")
        sleep(1)

        root = etree.fromstring(result.read())
        artists_node = root.find('artists')

        total_pages = int(artists_node.attrib['totalPages'])

        artist_nodes = filter(lambda c: c.tag == 'artist', artists_node.getchildren())    
        new_artist_names = map(lambda artist: artist.find('name').text, artist_nodes)
        print("Found " + str(new_artist_names))
        artist_names.extend(new_artist_names)

        page+=1

    return artist_names

def is_ready(artist_one, artist_two):
    url = base_url+'musictour/' + urllib.quote(artist_one.encode('utf-8')) + '/to/' + urllib.quote(artist_two.encode('utf-8')) + '/10-tracks/ready.json'
    print("Loading url " + url)
    result = urllib2.urlopen(url)

    ready = json.loads(result.read())

    return ready['ready']

def request_search(artist_one, artist_two):
    print("Searching for " + artist_one + " to " + artist_two)
    url = base_url+'musictour/' + urllib.quote(artist_one.encode('utf-8')) + '/to/' + urllib.quote(artist_two.encode('utf-8')) + '/10-tracks/'
    result = urllib2.urlopen(url)
    result.read()




all_artists = get_artist_names()
previous_artist = all_artists.pop(0)

count = 0
total_time = 0

incomplete = []

for artist in all_artists:
    start_time = time()
    print "---------------------------------------------------------------------"
    print "Searching for " + previous_artist + " to " + artist

    if not is_ready(previous_artist, artist):
        request_search(previous_artist, artist)

        sleep_time = 1
        while not (is_ready(previous_artist, artist) or (time() - start_time) > 120):
            print("Not ready yet, sleeping " + str(sleep_time))
            sleep(sleep_time)
            sleep_time = min(sleep_time * 2, 10)


        total_time += (time() - start_time)
        count+=1

        print "Running average time per search " + str(total_time / count) + " seconds"

        if (time() - start_time) >= 120:
            incomplete.append((previous_artist, artist))
            print("Gave up!")
        else:
            print("Ready")

    previous_artist = artist

print("Incomplete " + str(incomplete))

