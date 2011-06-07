from django.http import HttpResponse
from django.shortcuts import render_to_response

def homepage(request):
    return render_to_response('trqlive/homepage.html')

def homepage_static(request):
    return render_to_response('trqlive/homepage_static.html')

# vi:ts=4:sw=4:expandtab
