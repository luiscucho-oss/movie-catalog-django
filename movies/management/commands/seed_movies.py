from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Genre, Movie, Person, Rating

GENRES = {
    "Drama": "Historias centradas en el desarrollo de los personajes.",
    "Ciencia ficción": "Futuros posibles, tecnología y otros mundos.",
    "Animación": "Películas realizadas con técnicas de animación.",
    "Crimen": "Delitos, investigaciones y bajos fondos.",
}

PEOPLE = {
    "Christopher Nolan": date(1970, 7, 30),
    "Francis Ford Coppola": date(1939, 4, 7),
    "Hayao Miyazaki": date(1941, 1, 5),
    "Denis Villeneuve": date(1967, 10, 3),
    "Bong Joon-ho": date(1969, 9, 14),
    "Quentin Tarantino": date(1963, 3, 27),
    "Pete Docter": date(1968, 10, 9),
    "Leonardo DiCaprio": date(1974, 11, 11),
    "Al Pacino": date(1940, 4, 25),
    "Song Kang-ho": date(1967, 1, 17),
    "Uma Thurman": date(1970, 4, 29),
    "Ryan Gosling": date(1980, 11, 12),
}

# título, año, duración, director, géneros, reparto, sinopsis
MOVIES = [
    ("Origen", 2010, 148, "Christopher Nolan", ["Ciencia ficción", "Crimen"],
     ["Leonardo DiCaprio"], "Un ladrón roba secretos infiltrándose en los sueños."),
    ("Interstellar", 2014, 169, "Christopher Nolan", ["Ciencia ficción", "Drama"],
     [], "Un grupo de exploradores viaja a través de un agujero de gusano."),
    ("El padrino", 1972, 175, "Francis Ford Coppola", ["Crimen", "Drama"],
     ["Al Pacino"], "La saga de la familia Corleone."),
    ("El viaje de Chihiro", 2001, 125, "Hayao Miyazaki", ["Animación"],
     [], "Una niña queda atrapada en un mundo de espíritus."),
    ("Mi vecino Totoro", 1988, 86, "Hayao Miyazaki", ["Animación"],
     [], "Dos hermanas descubren criaturas mágicas en el bosque."),
    ("Blade Runner 2049", 2017, 164, "Denis Villeneuve", ["Ciencia ficción", "Drama"],
     ["Ryan Gosling"], "Un replicante descubre un secreto enterrado."),
    ("Parásitos", 2019, 132, "Bong Joon-ho", ["Drama", "Crimen"],
     ["Song Kang-ho"], "Una familia pobre se infiltra en la vida de una rica."),
    ("Pulp Fiction", 1994, 154, "Quentin Tarantino", ["Crimen"],
     ["Uma Thurman"], "Historias entrelazadas del hampa de Los Ángeles."),
    ("Del revés", 2015, 95, "Pete Docter", ["Animación", "Drama"],
     [], "Las emociones de una niña toman el control de su mente."),
    ("La llegada", 2016, 116, "Denis Villeneuve", ["Ciencia ficción", "Drama"],
     [], "Una lingüista intenta comunicarse con visitantes alienígenas."),
]

# Valoraciones en 7 de las 10 películas (el enunciado pide al menos 5).
RATINGS = {
    "Origen": [("Ana", 5, "Obra maestra."), ("Luis", 4, "Muy entretenida.")],
    "Interstellar": [("María", 5, "Emocionante."), ("Pedro", 4, "")],
    "El padrino": [("Luis", 5, "Imprescindible."), ("Ana", 5, "")],
    "El viaje de Chihiro": [("Sofía", 5, "Preciosa."), ("Pedro", 4, "")],
    "Blade Runner 2049": [("María", 4, "Visualmente impecable.")],
    "Parásitos": [("Sofía", 5, "Sorprendente."), ("Luis", 4, "")],
    "Pulp Fiction": [("Pedro", 3, "Diálogos geniales.")],
}


class Command(BaseCommand):
    help = "Carga datos de prueba: 10 películas, 4 géneros y valoraciones."

    @transaction.atomic
    def handle(self, *args, **options):
        genres = {
            name: Genre.objects.get_or_create(name=name, defaults={"description": d})[0]
            for name, d in GENRES.items()
        }
        people = {
            name: Person.objects.get_or_create(name=name, defaults={"birth_date": b})[0]
            for name, b in PEOPLE.items()
        }
        for title, year, duration, director, genre_names, cast, synopsis in MOVIES:
            movie, created = Movie.objects.get_or_create(
                title=title,
                year=year,
                defaults={
                    "duration": duration,
                    "director": people[director],
                    "synopsis": synopsis,
                },
            )
            movie.genres.set(genres[g] for g in genre_names)
            movie.cast.set(people[p] for p in cast)
            if created:
                for reviewer, score, comment in RATINGS.get(title, []):
                    Rating.objects.create(
                        movie=movie, reviewer=reviewer, score=score, comment=comment
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos cargados: {Movie.objects.count()} películas, "
                f"{Genre.objects.count()} géneros, {Person.objects.count()} personas, "
                f"{Rating.objects.count()} valoraciones."
            )
        )
