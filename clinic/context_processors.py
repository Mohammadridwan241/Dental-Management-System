from .forms import get_public_specialists_queryset
from .models import DoctorProfile


def site_context(request):
    primary_doctor = DoctorProfile.objects.select_related("user").first()
    specialists = get_public_specialists_queryset()[:6]
    return {
        "site_name": "Dr. Shafique's Dental Care",
        "primary_doctor": primary_doctor,
        "home_specialists": specialists,
    }
