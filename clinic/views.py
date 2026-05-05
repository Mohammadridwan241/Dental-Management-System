from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    AppointmentForm,
    ContactMessageForm,
    DoctorProfileCompletionForm,
    DoctorRegistrationForm,
    MedicineForm,
    PrescriptionForm,
    PrescriptionMedicineFormSet,
    SpecialistDoctorForm,
    get_public_specialists_queryset,
)
from .models import Appointment, Medicine, Prescription, SpecialistDoctor
from .utils import render_prescription_pdf


def get_doctor_profile_or_redirect(request):
    profile = getattr(request.user, "doctor_profile", None)
    if profile:
        return profile
    messages.warning(request, "Please complete your doctor profile before using the dashboard.")
    return HttpResponseRedirect(reverse("complete_profile"))


def home(request):
    context = {
        "appointment_form": AppointmentForm(),
        "contact_form": ContactMessageForm(),
        "services": [
            {"title": "General Dentistry", "description": "Preventive care, consultations, and oral health guidance."},
            {"title": "Cosmetic Dentistry", "description": "Smile design, whitening, and confidence-boosting treatments."},
            {"title": "Root Canal Therapy", "description": "Relief-focused treatment to preserve natural teeth."},
            {"title": "Orthodontic Support", "description": "Alignment planning and long-term bite correction guidance."},
            {"title": "Dental Surgery", "description": "Tooth extraction and surgical support with careful follow-up."},
            {"title": "Pediatric Care", "description": "Gentle dental care tailored for children and families."},
        ],
    }
    return render(request, "clinic/home.html", context)


def doctor_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = DoctorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save()
            login(request, profile.user)
            messages.success(request, "Registration completed successfully.")
            return redirect("dashboard")
    else:
        form = DoctorRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def complete_profile(request):
    if hasattr(request.user, "doctor_profile"):
        return redirect("dashboard")
    if request.method == "POST":
        form = DoctorProfileCompletionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor profile completed successfully.")
            return redirect("dashboard")
    else:
        form = DoctorProfileCompletionForm(user=request.user)
    return render(
        request,
        "clinic/form_page.html",
        {"form": form, "title": "Complete Doctor Profile"},
    )


@login_required
def dashboard(request):
    doctor = get_doctor_profile_or_redirect(request)
    if isinstance(doctor, HttpResponseRedirect):
        return doctor
    public_specialists = get_public_specialists_queryset()
    context = {
        "doctor": doctor,
        "medicine_count": Medicine.objects.count(),
        "specialist_count": public_specialists.count(),
        "appointment_count": Appointment.objects.count(),
        "prescription_count": Prescription.objects.filter(doctor=doctor).count(),
        "recent_appointments": Appointment.objects.select_related("specialist")[:5],
        "recent_prescriptions": Prescription.objects.filter(doctor=doctor).select_related("patient")[:5],
        "appointment_breakdown": Appointment.objects.values("status").annotate(total=Count("id")),
    }
    return render(request, "clinic/dashboard.html", context)


@login_required
def medicine_list(request):
    return render(request, "clinic/medicine_list.html", {"medicines": Medicine.objects.all()})


@login_required
def medicine_create(request):
    if request.method == "POST":
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine added successfully.")
            return redirect("medicine_list")
    else:
        form = MedicineForm()
    return render(request, "clinic/form_page.html", {"form": form, "title": "Add Medicine"})


@login_required
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine updated successfully.")
            return redirect("medicine_list")
    else:
        form = MedicineForm(instance=medicine)
    return render(request, "clinic/form_page.html", {"form": form, "title": "Edit Medicine"})


@login_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == "POST":
        medicine.delete()
        messages.success(request, "Medicine deleted successfully.")
        return redirect("medicine_list")
    return render(
        request,
        "clinic/confirm_delete.html",
        {"object": medicine, "title": "Delete Medicine", "cancel_url": reverse("medicine_list")},
    )


@login_required
def specialist_list(request):
    return render(
        request,
        "clinic/specialist_list.html",
        {"specialists": get_public_specialists_queryset()},
    )


@login_required
def specialist_create(request):
    if request.method == "POST":
        form = SpecialistDoctorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Specialist added successfully.")
            return redirect("specialist_list")
    else:
        form = SpecialistDoctorForm()
    return render(request, "clinic/form_page.html", {"form": form, "title": "Add Specialist"})


@login_required
def specialist_update(request, pk):
    specialist = get_object_or_404(SpecialistDoctor, pk=pk)
    if request.method == "POST":
        form = SpecialistDoctorForm(request.POST, request.FILES, instance=specialist)
        if form.is_valid():
            form.save()
            messages.success(request, "Specialist updated successfully.")
            return redirect("specialist_list")
    else:
        form = SpecialistDoctorForm(instance=specialist)
    return render(request, "clinic/form_page.html", {"form": form, "title": "Edit Specialist"})


@login_required
def specialist_delete(request, pk):
    specialist = get_object_or_404(SpecialistDoctor, pk=pk)
    if request.method == "POST":
        specialist.delete()
        messages.success(request, "Specialist deleted successfully.")
        return redirect("specialist_list")
    return render(
        request,
        "clinic/confirm_delete.html",
        {"object": specialist, "title": "Delete Specialist", "cancel_url": reverse("specialist_list")},
    )


def book_appointment(request):
    if request.method != "POST":
        return redirect("home")
    form = AppointmentForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Appointment request submitted successfully.")
    else:
        messages.error(request, "Please correct the appointment form errors and try again.")
    return redirect("home")


@login_required
def appointment_list(request):
    appointments = Appointment.objects.select_related("specialist")
    return render(request, "clinic/appointment_list.html", {"appointments": appointments})


@login_required
@require_POST
def appointment_status_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    status = request.POST.get("status")
    valid_statuses = {choice[0] for choice in Appointment.STATUS_CHOICES}
    if status in valid_statuses:
        appointment.status = status
        appointment.save(update_fields=["status"])
        messages.success(request, "Appointment status updated.")
    return redirect("appointment_list")


def contact_message_create(request):
    if request.method != "POST":
        return redirect("home")
    form = ContactMessageForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Your message has been sent successfully.")
    else:
        messages.error(request, "Please correct the contact form errors and try again.")
    return redirect("home")


@login_required
def prescription_list(request):
    doctor = get_doctor_profile_or_redirect(request)
    if isinstance(doctor, HttpResponseRedirect):
        return doctor
    query = request.GET.get("q", "").strip()
    prescriptions = (
        Prescription.objects.filter(doctor=doctor)
        .select_related("patient", "doctor__user")
    )
    if query:
        prescriptions = prescriptions.filter(
            Q(patient__name__icontains=query)
            | Q(patient_code__icontains=query)
            | Q(chief_complaint__icontains=query)
            | Q(diagnosis__icontains=query)
        )
    return render(
        request,
        "clinic/prescription_list.html",
        {"prescriptions": prescriptions, "query": query},
    )


@login_required
def prescription_create(request):
    doctor = get_doctor_profile_or_redirect(request)
    if isinstance(doctor, HttpResponseRedirect):
        return doctor
    if request.method == "POST":
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(doctor=doctor)
            formset = PrescriptionMedicineFormSet(request.POST, instance=prescription)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Prescription created successfully.")
                return redirect("prescription_detail", pk=prescription.pk)
            prescription.patient.delete()
            prescription.delete()
        else:
            formset = PrescriptionMedicineFormSet(request.POST)
    else:
        form = PrescriptionForm()
        formset = PrescriptionMedicineFormSet()
    return render(
        request,
        "clinic/prescription_form.html",
        {"form": form, "formset": formset, "doctor": doctor},
    )


@login_required
def prescription_detail(request, pk):
    doctor = get_doctor_profile_or_redirect(request)
    if isinstance(doctor, HttpResponseRedirect):
        return doctor
    prescription = get_object_or_404(
        Prescription.objects.select_related("doctor__user", "patient"),
        pk=pk,
        doctor=doctor,
    )
    return render(request, "clinic/prescription_detail.html", {"prescription": prescription})


@login_required
def prescription_pdf(request, pk):
    doctor = get_doctor_profile_or_redirect(request)
    if isinstance(doctor, HttpResponseRedirect):
        return doctor
    prescription = get_object_or_404(
        Prescription.objects.select_related("doctor__user", "patient"),
        pk=pk,
        doctor=doctor,
    )
    return render_prescription_pdf(prescription)
