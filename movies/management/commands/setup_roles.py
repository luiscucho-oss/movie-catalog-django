from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction

GROUP_NAME = "editores"

# Pueden añadir y modificar películas (y sus valoraciones en línea), pero no
# eliminarlas. Géneros y personas solo en modo consulta.
PERMISSIONS = [
    "view_movie",
    "add_movie",
    "change_movie",
    "view_rating",
    "add_rating",
    "change_rating",
    "view_genre",
    "view_person",
]


class Command(BaseCommand):
    help = "Crea el grupo «editores» y un usuario de ejemplo dentro de él."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="editor")
        parser.add_argument("--password", default="editor12345")

    @transaction.atomic
    def handle(self, *args, username, password, **options):
        group, _ = Group.objects.get_or_create(name=GROUP_NAME)
        group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="movies", codename__in=PERMISSIONS
            )
        )

        user, created = User.objects.get_or_create(
            username=username, defaults={"email": f"{username}@cinemateca.local"}
        )
        # is_staff permite entrar al panel; NO es superusuario.
        user.is_staff = True
        user.is_superuser = False
        if created:
            user.set_password(password)
        user.save()
        user.groups.add(group)

        self.stdout.write(
            self.style.SUCCESS(
                f"Grupo «{GROUP_NAME}» con {group.permissions.count()} permisos; "
                f"usuario «{username}» {'creado' if created else 'actualizado'}."
            )
        )
