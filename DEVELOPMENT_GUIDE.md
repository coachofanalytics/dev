# Biashara Bridges - Development Guide

## Quick Start for Local Development

```bash
# 1. Activate virtual environment
cd C:\Users\Mwongela\projects\biashara_bridges
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Create superuser (if needed)
python manage.py createsuperuser

# 5. Start development server
python manage.py runserver
```

Access the app at: http://localhost:8000

## Development Workflow

### Step 1: Create a Feature Branch (Recommended)
```bash
git checkout -b feature/your-feature-name
```

### Step 2: Make Your Changes

#### Adding a New Model
```python
# In accounts/models.py or relevant app
class YourNewModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

#### Create Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Register in Admin (Optional)
```python
# In accounts/admin.py
from .models import YourNewModel

@admin.register(YourNewModel)
class YourNewModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
```

#### Create Views
```python
# In accounts/views.py
from django.shortcuts import render
from .models import YourNewModel

def your_view(request):
    items = YourNewModel.objects.all()
    return render(request, 'your_template.html', {'items': items})
```

#### Add URLs
```python
# In accounts/urls.py
from . import views

urlpatterns = [
    path('your-url/', views.your_view, name='your_view'),
]
```

### Step 3: Test Locally

```bash
# Run the development server
python manage.py runserver

# Visit http://localhost:8000 and test your changes

# Run tests (if you have them)
python manage.py test

# Check for any issues
python manage.py check
```

### Step 4: Commit Changes

```bash
# See what changed
git status

# Add files
git add .

# Commit with descriptive message
git commit -m "Add feature: description of your feature"
```

### Step 5: Deploy to Heroku

```bash
# Merge to main branch
git checkout Main
git merge feature/your-feature-name

# Push to Heroku
git push heroku Main:main

# Migrations run automatically via Procfile
# Check deployment
heroku logs --tail -a codadev

# Open the app
heroku open -a codadev
```

## Common Tasks

### Adding New Python Dependencies

```bash
# 1. Install locally
pip install package-name

# 2. Update requirements
pip freeze > requirements.txt

# 3. Commit and deploy
git add requirements.txt
git commit -m "Add package-name dependency"
git push heroku Main:main
```

### Adding Static Files (CSS, JS, Images)

```bash
# 1. Add files to static/ directory
# Example: static/css/new-style.css

# 2. Collect static files locally (test)
python manage.py collectstatic

# 3. Commit and deploy
git add static/
git commit -m "Add new CSS styles"
git push heroku Main:main

# 4. Collect on Heroku
heroku run python collect_static.py -a codadev
```

### Database Changes

```bash
# 1. Modify models in models.py

# 2. Create migrations
python manage.py makemigrations

# 3. Test migration locally
python manage.py migrate

# 4. Check the migration file
cat accounts/migrations/000X_your_migration.py

# 5. Commit migration
git add accounts/migrations/
git commit -m "Add migration for new model field"

# 6. Deploy (migrations run automatically)
git push heroku Main:main
```

### Creating Management Commands

```bash
# Create directory
mkdir -p accounts/management/commands

# Create __init__.py files
touch accounts/management/__init__.py
touch accounts/management/commands/__init__.py

# Create your command
# File: accounts/management/commands/your_command.py
```

```python
from django.core.management.base import BaseCommand
from accounts.models import Category

class Command(BaseCommand):
    help = 'Description of your command'

    def handle(self, *args, **options):
        # Your command logic here
        self.stdout.write(self.style.SUCCESS('Command completed!'))
```

```bash
# Run locally
python manage.py your_command

# Run on Heroku
heroku run python manage.py your_command -a codadev
```

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test accounts
python manage.py test payments
```

### Create Tests
```python
# In accounts/tests.py
from django.test import TestCase
from .models import Category

class CategoryTestCase(TestCase):
    def setUp(self):
        Category.objects.create(name="Test", slug="test")

    def test_category_creation(self):
        cat = Category.objects.get(slug="test")
        self.assertEqual(cat.name, "Test")
```

## Debugging

### Local Debugging
```bash
# Use Django Debug Toolbar (optional)
pip install django-debug-toolbar

# Check for errors
python manage.py check

# View detailed errors
DEBUG=True python manage.py runserver
```

### Heroku Debugging
```bash
# View real-time logs
heroku logs --tail -a codadev

# View last 100 lines
heroku logs -n 100 -a codadev

# Run Django shell
heroku run python manage.py shell -a codadev

# Check database
heroku pg:info -a codadev
```

## Environment Variables

### Local (.env file)
```bash
# .env
DEBUG=True
SECRET_KEY=your-local-secret-key
DATABASE_URL=postgresql://user:pass@localhost/biashara_bridges
```

### Heroku
```bash
# View config
heroku config -a codadev

# Set variable
heroku config:set VARIABLE_NAME=value -a codadev

# Unset variable
heroku config:unset VARIABLE_NAME -a codadev
```

## Best Practices

1. **Always test locally before deploying**
2. **Use descriptive commit messages**
3. **Create migrations for model changes**
4. **Keep requirements.txt updated**
5. **Use environment variables for secrets**
6. **Regular backups of production database**
7. **Use feature branches for major changes**
8. **Document new features in README**

## Rollback (If Something Goes Wrong)

### Rollback Code Deployment
```bash
# View releases
heroku releases -a codadev

# Rollback to previous version
heroku rollback -a codadev
```

### Rollback Migrations
```bash
# Migrate backwards
heroku run python manage.py migrate accounts 0001 -a codadev

# Or specify migration number
heroku run python manage.py migrate accounts 0003 -a codadev
```

### Restore Database
```bash
# List backups
heroku pg:backups -a codadev

# Restore from backup
heroku pg:backups:restore b001 DATABASE_URL -a codadev
```

## Useful Commands Reference

```bash
# Local Development
python manage.py runserver              # Start dev server
python manage.py makemigrations         # Create migrations
python manage.py migrate                # Apply migrations
python manage.py createsuperuser        # Create admin user
python manage.py collectstatic          # Collect static files
python manage.py shell                  # Django shell

# Heroku Deployment
git push heroku Main:main               # Deploy
heroku logs --tail -a codadev          # View logs
heroku run python manage.py migrate    # Run migrations
heroku restart -a codadev              # Restart app
heroku ps -a codadev                   # Check dynos
heroku open -a codadev                 # Open in browser

# Database
heroku pg:info -a codadev              # Database info
heroku pg:backups:capture -a codadev   # Create backup
heroku run python manage.py dbshell    # Access database
```

## Getting Help

- Django Documentation: https://docs.djangoproject.com/
- Heroku Documentation: https://devcenter.heroku.com/
- Project README: README.md
- Check logs: `heroku logs --tail -a codadev`

---

Happy coding! 🚀
