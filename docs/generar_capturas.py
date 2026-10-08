"""Genera las capturas de docs/capturas con Playwright.

Requiere el servidor en marcha (python manage.py runserver) con los datos de
seed_movies y setup_roles. Uso:

    python docs/generar_capturas.py antes   docs/capturas  # con el admin.py básico
    python docs/generar_capturas.py crud    docs/capturas
    python docs/generar_capturas.py despues docs/capturas

Variable opcional CHROMIUM_PATH para usar un Chromium ya instalado.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = sys.argv[2]
MODE = sys.argv[1]


def login(page, user, pwd):
    page.context.clear_cookies()
    page.add_init_script("try{localStorage.setItem('django.admin.navSidebarIsOpen','false')}catch(e){}")
    page.goto(f"{BASE}/admin/login/")
    page.fill("#id_username", user)
    page.fill("#id_password", pwd)
    page.click("input[type=submit]")
    page.wait_for_url(f"{BASE}/admin/")


def shot(page, name, full=True):
    page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
    print("ok", name)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
    page = browser.new_page(viewport={"width": 1500, "height": 860}, locale="es-ES")

    if MODE == "antes":
        login(page, "admin", "admin12345")
        page.goto(f"{BASE}/admin/movies/movie/")
        shot(page, "01-admin-antes")
        page.goto(f"{BASE}/admin/movies/movie/1/change/")
        shot(page, "01b-formulario-antes")

    elif MODE == "crud":
        # Verificación de las cuatro operaciones básicas desde el panel.
        login(page, "admin", "admin12345")
        page.goto(f"{BASE}/admin/movies/genre/add/")
        page.fill("#id_name", "Comedia")
        page.click("input[name=_save]")
        shot(page, "crud-1-crear", full=False)
        page.click("text=Comedia")
        page.fill("#id_description", "Películas para reír.")
        page.click("input[name=_save]")
        shot(page, "crud-2-editar", full=False)
        page.goto(f"{BASE}/admin/movies/genre/?q=Comedia")
        page.click("table#result_list a:text('Comedia')")
        page.click("a.deletelink")
        shot(page, "crud-3-confirmar-eliminar", full=False)
        page.click("input[type=submit]")
        shot(page, "crud-4-eliminado", full=False)

    else:
        login(page, "admin", "admin12345")
        shot(page, "06-superusuario-inicio")
        page.goto(f"{BASE}/admin/movies/movie/")
        shot(page, "02-admin-despues")
        page.goto(f"{BASE}/admin/movies/movie/?genres__id__exact=2&q=Nolan")
        shot(page, "03-filtros-busqueda")
        page.goto(f"{BASE}/admin/movies/movie/1/change/")
        # Desplegar el bloque de auditoría para que se vean los campos.
        page.click("fieldset.collapse summary, fieldset.collapse h2 a", timeout=3000)
        shot(page, "04-inline-y-readonly")
        page.locator("fieldset.collapse").screenshot(path=f"{OUT}/05-readonly-auditoria.png")
        print("ok 05-readonly-auditoria")
        page.locator(".inline-group").screenshot(path=f"{OUT}/04b-inline-valoraciones.png")
        print("ok 04b-inline-valoraciones")

        login(page, "editor", "editor12345")
        shot(page, "07-editor-inicio")
        page.goto(f"{BASE}/admin/movies/movie/1/change/")
        shot(page, "08-editor-sin-eliminar")
        page.goto(f"{BASE}/admin/movies/movie/")
        shot(page, "08b-editor-listado-sin-acciones", full=False)
        page.goto(f"{BASE}/admin/movies/movie/1/delete/")
        shot(page, "08c-editor-eliminar-403", full=False)
        page.goto(f"{BASE}/admin/movies/genre/1/change/")
        shot(page, "08d-editor-genero-solo-lectura", full=False)

        page.goto(f"{BASE}/peliculas/")
        shot(page, "09a-catalogo-publico")
        page.goto(f"{BASE}/peliculas/1/recomendaciones/")
        shot(page, "09-recomendaciones")
    browser.close()
