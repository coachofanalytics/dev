# How to add the `communities` app to another copy of this project

This document describes step-by-step how to add the full `communities` app into another copy of the project and all the related files/paths it depends on. It assumes the target machine's project root will be similar to this repo and that you have a working Python/Django environment.

Source folder (copy this whole folder into the other computer):

- `C:\Users\Fadhiri\Desktop\Work\Copies\DC48K_prod\dev\communities`

What this folder contains (important files & folders inside `communities`):

- `communities/` (app root)
  - `__init__.py`
  - `admin.py` — admin registrations
  - `apps.py`
  - `forms.py`
  - `models.py`
  - `views.py` — app views (create if missing)
  - `urls.py` — URL patterns (create if missing)
  - `templates/communities/` or `templates/` — app templates, notably `home.html`
  - `migrations/` — prebuilt migrations (optional to copy; if not copied, run `makemigrations`)

Other project files/paths this app depends on (verify on the target project):

- Django project settings: `coda_project/settings.py` — add `'communities'` to `INSTALLED_APPS`.
- Root/project URLs: `coda_project/urls.py` — include the `communities` urls (see step below).
- Base template referenced by `home.html`: `main/base_templates/base.html` (template name used: `main/base_templates/base.html`). Typical locations to check:
  - `main/templates/main/base_templates/base.html`
  - `main/base_templates/base.html`
- Static assets used by the templates (copy these):
  - `static/community/img/img1.png`
  - `static/community/img/img2.png`
  - `static/community/img/img3.png`
  - (any other paths referenced by `home.html` or other templates — search for `static 'community/` occurrences).
- Global `templates` directory and `TEMPLATES` setting in `coda_project/settings.py` (ensure `APP_DIRS: True` or your app templates path is in `TEMPLATES['DIRS']`).
- `manage.py` at project root — for running migrations/dev server.
- `requirements.txt` — install same dependencies.

Step-by-step copy + integration guide

1) Copy the folder

- Copy the entire `communities` folder into the target project's app directory. Keep the same relative path inside the project root: e.g., `<project-root>/communities`.
- Also copy `static/community` into the target project's `static` directory (e.g., `<project-root>/static/community/img/...`).

2) Install dependencies and prepare environment

- Make sure Python and pip are installed.
- (Optional) Create and activate a virtual environment.

  Windows example:

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

3) Update project settings

- Open `coda_project/settings.py` and add `communities` to `INSTALLED_APPS` if not present:

  ```py
  INSTALLED_APPS = [
      # existing apps
      'main',
      'accounts',
      # ...
      'communities',
  ]
  ```

- Ensure template discovery is enabled so Django finds `communities/templates`:

  ```py
  TEMPLATES = [
      {
          'BACKEND': 'django.template.backends.django.DjangoTemplates',
          'DIRS': [os.path.join(BASE_DIR, 'templates')],  # if using project-level templates
          'APP_DIRS': True,
          'OPTIONS': { ... },
      },
  ]
  ```

- Ensure `STATIC_URL` and `STATICFILES_DIRS` are configured, e.g.: 

  ```py
  STATIC_URL = '/static/'
  STATICFILES_DIRS = [
      os.path.join(BASE_DIR, 'static'),
  ]
  ```

4) Wire URLs

- Open `coda_project/urls.py` and include the `communities` urls. Example:

  ```py
  from django.urls import path, include

  urlpatterns = [
      path('admin/', admin.site.urls),
      # other includes
      path('', include('main.urls')),
      path('communities/', include('communities.urls')),
  ]
  ```

- If `communities/urls.py` does not exist, create it with at least a home route that renders the template. Example `communities/urls.py`:

  ```py
  from django.urls import path
  from . import views

  urlpatterns = [
      path('', views.home, name='communities_home'),
  ]
  ```

5) Create or verify the `home` view

- If `communities/views.py` is missing or lacks a home view, add one. Example:

  ```py
  from django.shortcuts import render

  def home(request):
      return render(request, 'home.html')
  ```

  Notes: `home.html` in this project is located at `communities/templates/home.html`. Because `APP_DIRS` is True, `render(request, 'home.html')` will find it.

6) Templates and `extends` dependencies

- `communities/templates/home.html` extends `main/base_templates/base.html`. Ensure the `main` app and that base template exist. If the base template path differs, either adjust the extends path in `home.html` or copy the base template to the expected location.

7) Static files and CSS issues (important)

- The hero header used an inline style with a `{% static %}` tag. If you edit inline styles, use quoting that won't break HTML/CSS parsing:

  ```html
  <header style='background-image: url("{% static "community/img/img1.png" %}");'>
  ```

  Or better: move the background CSS to a stylesheet and reference a CSS class:

  ```css
  /* static/css/community.css */
  .community-hero { 
      background-image: url('../img/img1.png');
      background-size: cover;
      background-position: center;
      min-height: 400px;
  }
  ```

  Then in the template:

  ```html
  <header class="community-hero"> ... </header>
  ```

- After copying static assets, run `python manage.py collectstatic` if you're deploying to production (and your settings require it).

8) Database migrations

- If the `migrations/` folder was copied, run:

  ```powershell
  python manage.py migrate
  ```

- If you did not copy migrations, create them for the `communities` app and apply:

  ```powershell
  python manage.py makemigrations communities
  python manage.py migrate
  ```

9) Admin and model registration

- If `communities/admin.py` exists, it likely registers models. If not, and you want admin access, add registrations in `communities/admin.py`:

  ```py
  from django.contrib import admin
  from .models import YourModel

  admin.site.register(YourModel)
  ```

10) Optional: Forms and views

- If `forms.py` is present, import and use forms in views where required.
- If the `home.html` template references URL names (for example `join`, `forum_home`, `event_calendar`, `contact`) ensure those named URL patterns exist somewhere in the project. They may belong to other apps (`accounts`, `communities`, `main`, etc.). If missing, either:
  - create corresponding views + URL patterns using the same names, or
  - update the template to point to available pages.

11) Run the development server and test

- From project root run:

  ```powershell
  python manage.py runserver
  ```

- Open `http://127.0.0.1:8000/communities/` (or whichever path you wired) and verify the page loads.

12) Troubleshooting common issues

- Template not found: confirm `APP_DIRS` is True in `TEMPLATES` and the app is in `INSTALLED_APPS`.
- Static 404s: confirm `STATICFILES_DIRS` includes your `static` folder and that `static/community/img/...` files exist.
- CSS linter errors in editors: inline style with `{% static %}` can confuse CSS parser in some editors; prefer moving background-image to a CSS file or use consistent quoting (see step 7).
- Missing `base.html`: if `home.html` extends `main/base_templates/base.html` but `main` app isn't present, either copy that base or change the `extends` line to a base template available in your project.

13) Final checklist

- [ ] `communities` folder copied to `<project-root>/communities`
- [ ] Static assets copied to `<project-root>/static/community/img/` (or another static dir in settings)
- [ ] `'communities'` added to `INSTALLED_APPS` in `coda_project/settings.py`
- [ ] `coda_project/urls.py` includes `path('communities/', include('communities.urls'))`
- [ ] `communities/urls.py` contains a route for the home view
- [ ] `communities/views.py` has a `home` view that returns `home.html`
- [ ] Run `python manage.py migrate` successfully
- [ ] Start server and verify `http://127.0.0.1:8000/communities/`

If you want, I can:

- generate a ready-to-use `communities/urls.py` and `communities/views.py` examples and add them to this repo;
- create a small `static/css/community.css` and reference it from `home.html` to avoid inline-style linter problems.

Tell me if you want me to add those sample files automatically now.
