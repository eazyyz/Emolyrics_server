from django.http import JsonResponse
from .lyrics import get_song_data
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from .models import SongDB

def csrf_token_view(request):
    return JsonResponse({'csrfToken': get_token(request)})

def give_3lastsongs_view(request):
    last_songs = SongDB.objects.order_by('-timestamp')[:3]
    data = []
    for song in last_songs:
        data.append({
            "title": song.title,
            "artist": song.artist,
            "cover_image": song.cover_image,
        })
    return JsonResponse({"songs": data})

def get_lyrics_view(request):
    # python manage.py runserver localhost:8000
    title = request.GET.get('title')
    artist = request.GET.get('artist')

    if not title or not artist:
        return JsonResponse({"error": "Both 'title' and 'artist' are required."}, status=400)

    song_data = get_song_data(artist, title,False)

    # сохраняем песню в БД, если её там ещё нет
    SongDB.objects.get_or_create(
        title=song_data['title'],
        artist=song_data['artist'],
        lyrics=song_data['lyrics'],
        defaults={
            'cover_image': song_data['cover_image'],
            'url': song_data['url']
        }
    )

    return JsonResponse({"song_data": song_data})

@ensure_csrf_cookie
def csrf_cookie_view(request):
    return JsonResponse({'csrfToken': get_token(request)})

@csrf_protect
@require_http_methods(["POST"])
def feedback_view(request):
    csrf_token = request.headers.get('X-CSRFToken')
    print(f"получен CSRF токен: {csrf_token}")

    try:
        data = json.loads(request.body)
        liked = data.get('liked')
        title = data.get('songTitle')
        artist = data.get('songArtist')
        lyrics = data.get('lyrics')

        song = SongDB.objects.filter(title=title, artist=artist, lyrics=lyrics).first()
        # song = SongDB.objects.filter(title=title, artist=artist).first()

        if not song:
            return JsonResponse({'error': 'Song not found'}, status=404)

        song.register_feedback(liked)

        # если дизлайк, ищем следующую песню или генерим новую
        if not liked:
            # next_song = (
            #     SongDB.objects
            #     .exclude(id=song.id)
            #     .order_by('-likes', 'dislikes')
            #     .first()
            # )
            #
            # if next_song:
            #     return JsonResponse({
            #         'status': 'ok',
            #         'next_song_data': {
            #             'title': next_song.title,
            #             'artist': next_song.artist,
            #             'lyrics': next_song.lyrics,
            #             'cover_image': next_song.cover_image,
            #             'url': next_song.url
            #         }
            #     })

            new_song_data = get_song_data(artist, title, True)
            print(new_song_data)
            return JsonResponse({
                'generated_song': new_song_data,
            }, status=200)

        return 0
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Проблемы:
# 1 при "нет" новая песня появляется на сайте, но
# в дальнейшем неправильно feedback работает, неправильно отправляется с клиента
# возможно там не меняется lyrics
# можно забить уже

# 2 Надо сделать лоадер (сделал) можно приколы найти

# 3 расстояние между строчками добавить (сделал)

# 4 полученный текст с нейронки должен быть больше чем текст, песни который туда загружался
#  он также не должен сохраняться в бд