from django.db import models

class SongDB(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    lyrics = models.TextField()
    cover_image = models.URLField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} — {self.artist}"

    @property
    def rating(self):
        total = self.likes + self.dislikes
        return (self.likes / total) * 100 if total > 0 else 100

    def should_be_deleted(self):
        total = self.likes + self.dislikes
        return total >= 3 and self.rating < 50

    def register_feedback(self, liked: bool):
        if liked:
            self.likes += 1
        else:
            self.dislikes += 1

        if self.should_be_deleted():
            print(f"Удаление из БД: {self.title} — {self.artist} (рейтинг {self.rating:.1f}%)")
            self.delete()
        else:
            self.save()
