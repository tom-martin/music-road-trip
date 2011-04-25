from celery.task import task
from music_tour.music_tour import MusicTourService
from results import ResultsService

music_tour = MusicTourService('localhost', 27017)
results = ResultsService('localhost', 27017, 'music_tour')

@task
def find_path(from_artist, to_artist):
    path = music_tour.find_spotify_path(from_artist, to_artist, set())
    results.put(from_artist, to_artist, path)

