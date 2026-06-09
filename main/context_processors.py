from .utils import image_view

#availabity of images in this app

def images(request):
    images,image_names=image_view(request)
    return {
        'images': images,
        "image_names":image_names
    }

def googledriveurl(request):
    return {
        'googledriveurl':'http://drive.google.com/uc?export=view&id'
    }