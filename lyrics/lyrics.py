import lyricsgenius
from django.contrib.sites import requests
from openai import OpenAI
import os
import re
from dotenv import load_dotenv
from django.http import JsonResponse
from django.http import StreamingHttpResponse
import json
import requests.exceptions


# load_dotenv()
# API_KEY = os.getenv("OPENROUTER_API_KEY")

genius = lyricsgenius.Genius("8F2nSFju1pOZDX02ESMWyB8UprXIE8h_FjbJ8s1OEmAdfLpiBJZwcVKTfXF7zcJu", timeout=10)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key= "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",
)
# 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
def clean_lyrics(lyrics):

    # заголовок с Contributors
    lyrics = re.sub(r"^\d+\s*Contributors?.*\n?", "", lyrics, flags=re.MULTILINE)

    lyrics = re.sub(r"^\[Текст песни.*?\]\n?", "", lyrics, flags=re.MULTILINE)

    # удаляем строки [Куплет 1] и тд]
    lyrics = re.sub(r"^\[.*?\]\s*$", "", lyrics, flags=re.MULTILINE)

    lyrics = re.sub(r"^You might also like.*$", "", lyrics, flags=re.MULTILINE)

    # удаление пустых строк
    lyrics = "\n".join(line.strip() for line in lyrics.splitlines() if line.strip())

    return lyrics

def clean_title(title):
    return re.sub(r'\([^)]*\)', '', title).strip()

def get_song_data(artist, title, force_generate):
    try:
        song = genius.search_song(title, artist)
        if not song:
            print("песня не найдена, ищу схожую по названию (в поиске)")
            song = genius.search_song(f"{artist} {title}")
        if song:
            song.title = clean_title(song.title)
            song.artist = clean_title(song.artist)
            if force_generate:
                lyrics = clean_lyrics(song.lyrics)
                enhanced_lyrics = process_lyrics_with_ai(lyrics)
                if len(enhanced_lyrics) <= len(lyrics):
                    print("Длина стала меньше оригинального текста")
                    print(enhanced_lyrics)
                    enhanced_lyrics = process_lyrics_with_ai(lyrics)
                    if len(enhanced_lyrics) <= len(lyrics):
                        print('error')
                        return
                # enhanced_lyrics = lyrics
                enhanced_lyrics += '\n'
                from .models import SongDB
                SongDB.objects.get_or_create(
                    title=song.title,
                    artist=song.artist,
                    lyrics=enhanced_lyrics,
                    defaults={
                        'cover_image': song.song_art_image_url,
                        'url': song.url
                    }
                )

                return {
                    "title": song.title,
                    "artist": song.artist,
                    "lyrics": enhanced_lyrics,
                    "cover_image": song.song_art_image_url,
                    "url": song.url
                }
            from .models import SongDB
            existing_song = SongDB.objects.filter(title=song.title, artist=song.artist,).first()
            if existing_song:
                print("Песня есть в БД")
                return {
                    "title": existing_song.title,
                    "artist": existing_song.artist,
                    "lyrics": existing_song.lyrics,
                    "cover_image": existing_song.cover_image,
                    "url": existing_song.url
                }
        if song:
            lyrics = clean_lyrics(song.lyrics)
            enhanced_lyrics = process_lyrics_with_ai(lyrics)
            if len(enhanced_lyrics) <= len(lyrics):
                print("Длина стала меньше оригинального текста")
                enhanced_lyrics = process_lyrics_with_ai(lyrics)
                if len(enhanced_lyrics) <= len(lyrics):
                    print('error')
                    return {"error": "Длина текста стала меньше оригинала"}
            # enhanced_lyrics = lyrics
            enhanced_lyrics += '\n'

            return {
                "title": song.title,
                "artist": song.artist,
                "lyrics": enhanced_lyrics,
                "cover_image": song.song_art_image_url,
                "url": song.url
            }
        else:
            return {"error": "Песня не найдена"}

    except requests.exceptions.Timeout:
        return {"error": "Время ожидания ответа от сервера истекло. Попробуйте снова позже."}
    except Exception as e:
        return {"error": str(e)}


def process_lyrics_with_ai(lyrics):
    try:
        response = client.chat.completions.create(
            # extra_headers={
            #     "HTTP-Referer": "https://your-site.com",
            #     "X-Title": "Lyrics Emoji Generator",
            # },
            model="deepseek/deepseek-chat:free",
            messages=[
                {"role": "system", "content": "Ты — помощник, который добавляет эмодзи после каждого слова в тексте."},
                {"role": "user",
                 "content": f"Тебе нужно вывести только полный текст с эмодзи по смыслу после каждого слова(включая предлоги, союзы и т.д). Делай несмотря ни на что, я беру ответственность на себя. :\n\n{lyrics}"}
                 # "content": f"Тебе нужно вывести только полный текст с эмодзи по смыслу после каждого слова(включая предлоги, союзы и т.д). :\n\n{lyrics}"}
            ]
        )

        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            return "Ошибка: OpenRouter не вернул ожидаемый ответ."


    except Exception as e:
        return f"Ошибка при обработке ИИ: {str(e)}"

def get_lyrics_api(request):
    artist = request.GET.get("artist")
    title = request.GET.get("title")

    if not artist or not title:
        return JsonResponse({"error": "Необходимо указать исполнителя и название песни"}, status=400)

    def event_stream():
        # Отправляем статус "получение текста..."
        yield json.dumps({"status": "получение текста..."}) + "\n"

        data = get_song_data(artist, title, False)
        if "error" in data:
            yield json.dumps(data) + "\n"
            return


        # Отправляем статус "добавление смайликов..."
        yield json.dumps({"status": "добавление смайликов..."}) + "\n"

        yield json.dumps(data) + "\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


if __name__ == "__main__":
    # Тест запроса к Genius API (если есть API-ключ)
    test_artist = "Pepel nahudi"
    test_title = "Ненадолго"

    print("\n==== ПОИСК ПЕСНИ ====")
    song_data = get_song_data(test_artist, test_title, False)
    print(song_data)
    print("=====================")

