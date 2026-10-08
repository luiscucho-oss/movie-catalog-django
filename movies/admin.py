from django.contrib import admin

from .models import Genre, Movie, Person, Rating

admin.site.register(Genre)
admin.site.register(Person)
admin.site.register(Movie)
admin.site.register(Rating)
