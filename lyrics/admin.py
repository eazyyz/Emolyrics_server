from django.contrib import admin
from .models import SongDB

@admin.register(SongDB)
class SongDBAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'lyrics', 'rating', 'timestamp')
    list_filter = ('artist',)
    search_fields = ('title', 'artist')