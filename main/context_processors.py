from .utils import image_view
from .models import Service
import os
from django.conf import settings


def healthcare_images(request):
    """Look for image files in the static healthcare_uploads folder and return static URLs.
    This function only uses the uploads folder (no admin/media). It accepts multiple
    filename conventions (hero/services/insurance or the exact names provided).
    """
    # relative path under static/ (use forward slashes for URL construction)
    uploads_rel = 'main/img/healthcare_uploads'
    uploads_fs = os.path.join(settings.BASE_DIR, 'main', 'static', *uploads_rel.split('/'))

    result = {
        'hero_image_url': None,
        'services_image_url': None,
        'insurance_image_url': None,
    }

    exts = ['jpg', 'jpeg', 'png', 'webp', 'gif']
    names = {
        'hero_image_url': ['hero', 'healthcarehero'],
        'services_image_url': ['services', 'healthcareservices'],
        'insurance_image_url': ['insurance', 'insuranceoptions'],
    }

    try:
        for key, bases in names.items():
            for base in bases:
                found = False
                for ext in exts:
                    filename = f"{base}.{ext}"
                    fs_path = os.path.join(uploads_fs, filename)
                    if os.path.exists(fs_path):
                        static_url = settings.STATIC_URL.rstrip('/') + '/' + '/'.join([uploads_rel, filename])
                        result[key] = static_url
                        found = True
                        break
                if found:
                    break
    except Exception:
        # Fail silently; template will use placeholders
        pass

    return result


# availabity of images in this app
def images(request):
    images, image_names = image_view(request)
    return {
        'images': images,
        'image_names': image_names,
    }


def googledriveurl(request):
    return {
        'googledriveurl': 'http://drive.google.com/uc?export=view&id'
    }


def services(request):
    """Expose services to all templates and a flag indicating whether a
    'healthcare' service exists. Templates can use this to toggle menu links.
    """
    try:
        services_qs = Service.objects.all()
        healthcare_exists = Service.objects.filter(title__icontains='healthcare').exists()
    except Exception:
        # In case migrations haven't run or DB isn't available yet
        services_qs = []
        healthcare_exists = False

    return {
        'services_menu': services_qs,
        'healthcare_available': healthcare_exists,
    }