import sys
import demo_config
from music_tour import MusicTourService
import logging

logging.basicConfig(level=logging.DEBUG)

if len(sys.argv) < 3:
    print "Usage find.py <artist name> <other artist name>"
    exit()

service = MusicTourService(demo_config.mongo_host, demo_config.mongo_port)

artist_one = sys.argv[1]
artist_two = sys.argv[2]

blacklist = set()
if len(sys.argv) > 3:
    for blacklisted in sys.argv[3].split(','):
        blacklist.add(blacklisted)

print "Searching for " + artist_one + " to " + artist_two

tracks = []
route = service.find_spotify_path(artist_one, artist_two, blacklist)
tracks = service.get_random_tracks_for_route(route)

if len(tracks) > 0:
    print route
    print
    print "Playlist:"
    for track in tracks:
        print track  
