from xml.sax import parse

from django.urls import path
from lyrics import views

urlpatterns = [
    path('get-lyrics/', views.get_lyrics_view, name='get_lyrics'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('csrf/', views.csrf_cookie_view, name='csrf_cookie'),
    path('last-songs/', views.give_3lastsongs_view, name='last_songs')
]