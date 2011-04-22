from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from music_tour.music_tour import MusicTourService
from django.template import Context, loader
from django.shortcuts import render_to_response


music_tour = MusicTourService('localhost', 27017)

def index(request):
    return render_to_response('mrt_templates/index.html', {'error': request.GET.get('error')})

def results_redirect(request):
    if 'from_artist' not in request.GET or 'to_artist' not in request.GET:
        return HttpResponseRedirect(reverse('mrt_app.views.index') + "?error=Please%20specify%20two%20artists")

    return HttpResponseRedirect(reverse('mrt_app.views.results', args=(request.GET['from_artist'], request.GET['to_artist'])))
    
def results(request, from_artist, to_artist):
    route = music_tour.find_spotify_path(from_artist, to_artist, set())
    tracks = music_tour.get_random_tracks_for_route(route)

    return render_to_response('mrt_templates/results.html', {'route': route, 'tracks': tracks, 'from_artist': from_artist, 'to_artist': to_artist})


