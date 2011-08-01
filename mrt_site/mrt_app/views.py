from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from music_tour.music_tour import MusicTourService
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response
from tasks import find_path
from time import time, sleep
from results import ResultsService
from django.conf import settings
import json
import random
from bg_info import bg_info


music_tour = MusicTourService(settings.LAST_FM_API_KEY, 'localhost', 27017)
results_service = ResultsService('localhost', 27017, 'music_tour')

def index(request):
    return render_to_response('mrt_templates/index.html', {'bg_info': random.choice(bg_info), 'error': request.GET.get('error')}, context_instance=RequestContext(request))

def results_redirect(request):
    if 'from_artist' not in request.GET or 'to_artist' not in request.GET:
        return HttpResponseRedirect(reverse('mrt_app.views.index') + "?error=Please%20specify%20two%20artists")

    track_count = 10
    if 'track_count' in request.GET:
        track_count = request.GET['track_count']

    return HttpResponseRedirect(reverse('mrt_app.views.results', args=(request.GET['from_artist'], request.GET['to_artist'], track_count)))
    
def results(request, from_artist, to_artist, track_count="10"):
    bg_index = random.choice(range(1, 15))
    track_count = min(int(track_count), 100)

    from_artist = music_tour.search_for_artist(from_artist)
    to_artist = music_tour.search_for_artist(to_artist)

    if len(from_artist['matching_tracks']) == 0 or len(to_artist['matching_tracks']) == 0:
        return render_to_response('mrt_templates/did_you_mean.html', {'from_artist': from_artist, 'to_artist': to_artist})

    route = results_service.get(from_artist['artist_name'], to_artist['artist_name'])
    if route != None:
        tracks = music_tour.get_random_tracks_for_route(route, track_count)
        return render_to_response('mrt_templates/results.html', {'bg_info': random.choice(bg_info), 'route': route, 'tracks': tracks, 'from_artist': from_artist['artist_name'], 'to_artist': to_artist['artist_name']}, context_instance=RequestContext(request))
    else:
        route_result = find_path.delay(from_artist['artist_name'], to_artist['artist_name'])
        return render_to_response('mrt_templates/loading.html', {'bg_info': random.choice(bg_info), 'from_artist': from_artist['artist_name'], 'to_artist': to_artist['artist_name']}, context_instance=RequestContext(request))

def ready_json(request, from_artist, to_artist):
    route = results_service.get(from_artist, to_artist)
    return HttpResponse(json.dumps({'ready': route != None}))

def suggestions_json(request):
    suggestions = music_tour.get_artist_suggestions(request.GET.get('term'))
    return HttpResponse(json.dumps(suggestions))



