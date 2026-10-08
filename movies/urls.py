from django.urls import path

from . import views

app_name = "movies"

urlpatterns = [
    path("", views.movie_list, name="list"),
    path("<int:pk>/recomendaciones/", views.recommendations, name="recommendations"),
]
