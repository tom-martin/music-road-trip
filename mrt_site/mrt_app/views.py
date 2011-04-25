from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from music_tour.music_tour import MusicTourService
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response
from tasks import find_path
from time import time, sleep
from results import ResultsService
import json


music_tour = MusicTourService('localhost', 27017)
results_service = ResultsService('localhost', 27017, 'music_tour')

def index(request):
    return render_to_response('mrt_templates/index.html', {'error': request.GET.get('error')})

def results_redirect(request):
    if 'from_artist' not in request.GET or 'to_artist' not in request.GET:
        return HttpResponseRedirect(reverse('mrt_app.views.index') + "?error=Please%20specify%20two%20artists")

    return HttpResponseRedirect(reverse('mrt_app.views.results', args=(request.GET['from_artist'], request.GET['to_artist'])))
    
def results(request, from_artist, to_artist):
    route = results_service.get(from_artist, to_artist)
    if route != None:
        tracks = music_tour.get_random_tracks_for_route(route)
        return render_to_response('mrt_templates/results.html', {'route': route, 'tracks': tracks, 'from_artist': from_artist, 'to_artist': to_artist})
    else:
        route_result = find_path.delay(from_artist, to_artist)
        return render_to_response('mrt_templates/loading.html', {'from_artist': from_artist, 'to_artist': to_artist}, context_instance=RequestContext(request))

def ready_json(request, from_artist, to_artist):
    route = results_service.get(from_artist, to_artist)
    return HttpResponse(json.dumps({'ready': route != None}))



