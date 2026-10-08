from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Genre(models.Model):
    name = models.CharField("nombre", max_length=50, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "género"
        verbose_name_plural = "géneros"

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField("nombre", max_length=120)
    birth_date = models.DateField("fecha de nacimiento", null=True, blank=True)
    biography = models.TextField("biografía", blank=True)
    photo = models.ImageField("foto", upload_to="people/", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "persona"
        verbose_name_plural = "personas"

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField("título", max_length=200)
    year = models.PositiveSmallIntegerField(
        "año",
        validators=[MinValueValidator(1888), MaxValueValidator(2100)],
    )
    synopsis = models.TextField("sinopsis", blank=True)
    duration = models.PositiveSmallIntegerField(
        "duración (min)", null=True, blank=True
    )
    poster = models.ImageField("póster", upload_to="posters/", blank=True)
    director = models.ForeignKey(
        Person,
        verbose_name="director",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="directed_movies",
    )
    cast = models.ManyToManyField(
        Person, verbose_name="reparto", blank=True, related_name="acted_movies"
    )
    genres = models.ManyToManyField(
        Genre, verbose_name="géneros", related_name="movies"
    )
    # Campos de auditoría: los rellena Django automáticamente.
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("última modificación", auto_now=True)

    class Meta:
        ordering = ["-year", "title"]
        verbose_name = "película"
        verbose_name_plural = "películas"

    def __str__(self):
        return f"{self.title} ({self.year})"

    def get_absolute_url(self):
        return reverse("movies:recommendations", args=[self.pk])


class Rating(models.Model):
    movie = models.ForeignKey(
        Movie,
        verbose_name="película",
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    reviewer = models.CharField("autor", max_length=100)
    score = models.PositiveSmallIntegerField(
        "puntuación",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="De 1 a 5 estrellas.",
    )
    comment = models.TextField("comentario", blank=True)
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "valoración"
        verbose_name_plural = "valoraciones"

    def __str__(self):
        return f"{self.movie.title} · {self.score}/5 por {self.reviewer}"
