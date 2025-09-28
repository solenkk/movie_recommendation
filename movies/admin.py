from django.contrib import admin
from .models import Movie

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'tmdb_id', 'release_date', 'vote_average', 'created_at')
    list_filter = ('release_date', 'vote_average', 'created_at')
    search_fields = ('title', 'overview', 'tmdb_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('tmdb_id', 'title', 'overview', 'release_date')
        }),
        ('Media', {
            'fields': ('poster_path', 'backdrop_path')
        }),
        ('Ratings', {
            'fields': ('vote_average', 'vote_count')
        }),
        ('Additional', {
            'fields': ('genres', 'created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('tmdb_id',)
        return self.readonly_fields