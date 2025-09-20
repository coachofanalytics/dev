from django import template
from application.models import Rated
register = template.Library()


@register.simple_tag
def fetchurl(idval,topic):
    try:
        uploadlinkurl = Rated.objects.values_list("uploadlinkurl", flat=True).filter(employeename__id=idval,topic__icontains=topic)[0]
        return uploadlinkurl
    except:
        return False

    