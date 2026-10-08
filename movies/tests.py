from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Genre, Movie, Person, Rating


class ModelTests(TestCase):
    def test_str_methods(self):
        genre = Genre.objects.create(name="Drama")
        person = Person.objects.create(name="Bong Joon-ho")
        movie = Movie.objects.create(title="Parásitos", year=2019, director=person)
        movie.genres.add(genre)
        rating = Rating.objects.create(movie=movie, reviewer="Ana", score=5)

        self.assertEqual(str(genre), "Drama")
        self.assertEqual(str(person), "Bong Joon-ho")
        self.assertEqual(str(movie), "Parásitos (2019)")
        self.assertEqual(str(rating), "Parásitos · 5/5 por Ana")
        self.assertEqual(list(genre.movies.all()), [movie])
        self.assertEqual(list(movie.ratings.all()), [rating])

    def test_audit_fields_are_set_automatically(self):
        movie = Movie.objects.create(title="Origen", year=2010)
        self.assertIsNotNone(movie.created_at)
        self.assertIsNotNone(movie.updated_at)


class RecommendationViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        drama = Genre.objects.create(name="Drama")
        anim = Genre.objects.create(name="Animación")
        cls.base = Movie.objects.create(title="Base", year=2000)
        cls.base.genres.add(drama)
        cls.best = Movie.objects.create(title="Mejor", year=2001)
        cls.best.genres.add(drama)
        cls.worse = Movie.objects.create(title="Peor", year=2002)
        cls.worse.genres.add(drama)
        cls.unrated = Movie.objects.create(title="Sin notas", year=2003)
        cls.unrated.genres.add(drama)
        cls.other = Movie.objects.create(title="Otro género", year=2004)
        cls.other.genres.add(anim)
        Rating.objects.create(movie=cls.best, reviewer="a", score=5)
        Rating.objects.create(movie=cls.worse, reviewer="a", score=2)
        Rating.objects.create(movie=cls.other, reviewer="a", score=5)
        Rating.objects.create(movie=cls.base, reviewer="a", score=5)

    def test_recommends_same_genre_ordered_by_score(self):
        response = self.client.get(
            reverse("movies:recommendations", args=[self.base.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["recommended"]), [self.best, self.worse])

    def test_unknown_movie_returns_404(self):
        response = self.client.get(reverse("movies:recommendations", args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_movie_list(self):
        response = self.client.get(reverse("movies:list"))
        self.assertContains(response, "Mejor")


class AdminAndRolesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_movies", stdout=StringIO())
        call_command("setup_roles", stdout=StringIO())
        cls.movie = Movie.objects.first()

    def test_seed_data(self):
        self.assertEqual(Movie.objects.count(), 10)
        self.assertEqual(Genre.objects.count(), 4)
        self.assertGreaterEqual(
            Movie.objects.filter(ratings__isnull=False).distinct().count(), 5
        )

    def test_editor_can_change_but_not_delete(self):
        editor = User.objects.get(username="editor")
        self.assertTrue(editor.groups.filter(name="editores").exists())
        self.client.force_login(editor)

        change_url = reverse("admin:movies_movie_change", args=[self.movie.pk])
        response = self.client.get(change_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "deletelink")

        delete_url = reverse("admin:movies_movie_delete", args=[self.movie.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 403)

    def test_superuser_sees_delete_and_readonly_audit_fields(self):
        admin = User.objects.create_superuser("root", "r@x.com", "pass")
        self.client.force_login(admin)
        url = reverse("admin:movies_movie_change", args=[self.movie.pk])
        response = self.client.get(url)
        self.assertContains(response, "deletelink")
        # Los campos de auditoría se muestran como texto, no como inputs.
        self.assertNotContains(response, 'name="created_at"')
        self.assertNotContains(response, 'name="updated_at"')

    def test_changelist_filters_and_search(self):
        admin = User.objects.create_superuser("root", "r@x.com", "pass")
        self.client.force_login(admin)
        url = reverse("admin:movies_movie_changelist")
        response = self.client.get(url, {"q": "Origen"})
        self.assertContains(response, "Origen")
        self.assertNotContains(response, "Pulp Fiction")
