from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction

# Cada grupo representa un rol real del equipo de la cinemateca. Los permisos
# se asignan al grupo y no al usuario: dar de alta a otra persona con el mismo
# rol es solo añadirla al grupo.
ROLES = {
    "editores": {
        # Mantienen el catálogo: añaden y corrigen películas y sus valoraciones,
        # pero no eliminan, porque borrar una película elimina en cascada sus
        # valoraciones. Géneros y personas son datos maestros: solo consulta.
        "permissions": [
            "view_movie",
            "add_movie",
            "change_movie",
            "view_rating",
            "add_rating",
            "change_rating",
            "view_genre",
            "view_person",
        ],
        "user": ("editor", "editor12345"),
    },
    "moderadores": {
        # Revisan las reseñas: corrigen o eliminan valoraciones inapropiadas,
        # pero no tocan el catálogo (las películas solo las consultan).
        "permissions": [
            "view_movie",
            "view_rating",
            "change_rating",
            "delete_rating",
        ],
        "user": ("moderador", "moderador12345"),
    },
}


class Command(BaseCommand):
    help = "Crea los grupos «editores» y «moderadores» con un usuario de prueba en cada uno."

    @transaction.atomic
    def handle(self, *args, **options):
        for group_name, role in ROLES.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.set(
                Permission.objects.filter(
                    content_type__app_label="movies",
                    codename__in=role["permissions"],
                )
            )

            username, password = role["user"]
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@cinemateca.local"}
            )
            # is_staff permite entrar al panel; NO es superusuario.
            user.is_staff = True
            user.is_superuser = False
            if created:
                user.set_password(password)
            user.save()
            user.groups.set([group])

            self.stdout.write(
                self.style.SUCCESS(
                    f"Grupo «{group_name}» con {group.permissions.count()} permisos; "
                    f"usuario «{username}» {'creado' if created else 'actualizado'}."
                )
            )
