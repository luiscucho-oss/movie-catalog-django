from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render

from .models import Movie


def with_scores(queryset):
    return queryset.annotate(
        avg_score=Avg("ratings__score"),
        ratings_count=Count("ratings", distinct=True),
    )


def movie_list(request):
    movies = (
        with_scores(Movie.objects.all())
        .select_related("director")
        .prefetch_related("genres")
    )
    return render(request, "movies/movie_list.html", {"movies": movies})


def recommendations(request, pk, limit=5):
    """Películas mejor valoradas que comparten género con la película dada."""
    movie = get_object_or_404(
        Movie.objects.select_related("director").prefetch_related("genres"), pk=pk
    )
    recommended = (
        with_scores(
            Movie.objects.filter(genres__in=movie.genres.all())
            .exclude(pk=movie.pk)
            .distinct()
        )
        .filter(avg_score__isnull=False)
        .order_by("-avg_score", "-ratings_count", "title")
        .prefetch_related("genres")[:limit]
    )
    return render(
        request,
        "movies/recommendations.html",
        {"movie": movie, "recommended": recommended},
    )
