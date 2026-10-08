from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Avg, Count

from .models import Genre, Movie, Person, Rating

admin.site.site_header = "Cinemateca · Administración"
admin.site.site_title = "Cinemateca"
admin.site.index_title = "Gestión del catálogo"


class RatingInline(admin.TabularInline):
    """Permite dar de alta valoraciones desde el formulario de la película."""

    model = Rating
    extra = 1
    fields = ("reviewer", "score", "comment", "created_at")
    readonly_fields = ("created_at",)
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 2, "cols": 50})},
    }


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "year",
        "director",
        "genre_list",
        "average_score",
        "ratings_count",
        "updated_at",
    )
    list_display_links = ("title",)
    list_filter = ("genres", "year")
    search_fields = ("title", "director__name", "cast__name")
    filter_horizontal = ("genres", "cast")
    autocomplete_fields = ("director",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [RatingInline]
    list_per_page = 20
    fieldsets = (
        (None, {"fields": ("title", "year", "duration", "synopsis", "poster")}),
        ("Equipo", {"fields": ("director", "cast")}),
        ("Clasificación", {"fields": ("genres",)}),
        (
            "Auditoría",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("director")
            .prefetch_related("genres")
            .annotate(
                _average_score=Avg("ratings__score"),
                _ratings_count=Count("ratings", distinct=True),
            )
        )

    @admin.display(description="géneros")
    def genre_list(self, obj):
        return ", ".join(genre.name for genre in obj.genres.all())

    @admin.display(description="nota media", ordering="_average_score")
    def average_score(self, obj):
        if obj._average_score is None:
            return "—"
        return f"{obj._average_score:.1f} ★"

    @admin.display(description="valoraciones", ordering="_ratings_count")
    def ratings_count(self, obj):
        return obj._ratings_count


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "movie_count")
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_movie_count=Count("movies"))

    @admin.display(description="películas", ordering="_movie_count")
    def movie_count(self, obj):
        return obj._movie_count


class PersonRoleFilter(admin.SimpleListFilter):
    """Separa a quienes dirigen de quienes actúan, que es como se busca a una persona."""

    title = "rol"
    parameter_name = "rol"

    def lookups(self, request, model_admin):
        return [("director", "Dirección"), ("reparto", "Reparto")]

    def queryset(self, request, queryset):
        if self.value() == "director":
            return queryset.filter(_directed_count__gt=0)
        if self.value() == "reparto":
            return queryset.filter(_acted_count__gt=0)
        return queryset


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date", "directed_count", "acted_count")
    list_filter = (PersonRoleFilter,)
    search_fields = ("name",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _directed_count=Count("directed_movies", distinct=True),
                _acted_count=Count("acted_movies", distinct=True),
            )
        )

    @admin.display(description="películas dirigidas", ordering="_directed_count")
    def directed_count(self, obj):
        return obj._directed_count

    @admin.display(description="películas en reparto", ordering="_acted_count")
    def acted_count(self, obj):
        return obj._acted_count


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("movie", "reviewer", "score", "short_comment", "created_at")
    list_filter = ("score", "movie__genres")
    search_fields = ("movie__title", "reviewer", "comment")
    autocomplete_fields = ("movie",)
    readonly_fields = ("created_at",)

    @admin.display(description="comentario")
    def short_comment(self, obj):
        # Permite moderar desde el listado sin abrir cada valoración.
        if len(obj.comment) > 60:
            return f"{obj.comment[:60]}…"
        return obj.comment or "—"
