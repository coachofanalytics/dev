from .models import ( 
                        JobRole,FeaturedCategory,
                        FeaturedSubCategory,
                        FeaturedActivity,
                        ActivityLinks
                    )

def categories (request):
    # Define the desired categories in the required order
    required_categories = [
        'Course Overview',
        'Initiation & Planning',
        'Development',
        'Testing',
        'Deployment'
    ]

    # Fetch all categories
    categories = FeaturedCategory.objects.filter(title__in=required_categories)

    return {
        'categories': categories
    }

def subcategories (request):
    return {
        'subcategories': FeaturedSubCategory.objects.all()
    }
def activities (request):
    return {
        'activities': FeaturedActivity.objects.all()
    }
def links (request):
    return {
        'links': ActivityLinks.objects.all()
    }

def roles (request):
    return {
        'roles': JobRole.objects.all()
    }
