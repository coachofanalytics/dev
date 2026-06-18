# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from main.models import Bookings
import json
from datetime import datetime

@require_POST
def create_booking(request):
    data = json.loads(request.body)

    booking = Bookings.objects.create(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        service_type=data["service_type"],
        preferred_date=data["preferred_date"],
        preferred_time=data["preferred_time"],
        additional_info=data.get("additional_info")
    )

    return JsonResponse({"id": booking.id}, status=201)