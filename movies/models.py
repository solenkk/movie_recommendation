from django.db import models

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    backdrop_path = models.CharField(max_length=255, blank=True, null=True)
    vote_average = models.FloatField(blank=True, null=True)
    vote_count = models.IntegerField(blank=True, null=True)
    genres = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'movies_movie'
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['vote_average']),
        ]

    @property
    def full_poster_url(self):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    @property
    def full_backdrop_url(self):
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/w1280{self.backdrop_path}"
        return None