from django.contrib import admin

from .models import (
    Appointment,
    ContactMessage,
    DoctorProfile,
    Medicine,
    Patient,
    Prescription,
    PrescriptionMedicine,
    SpecialistDoctor,
)


class PrescriptionMedicineInline(admin.TabularInline):
    model = PrescriptionMedicine
    extra = 1


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "specialization", "hospital_name", "bmdc_no", "phone_number")
    search_fields = ("name", "user__first_name", "user__last_name", "user__email", "specialization", "bmdc_no")


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "dosage", "created_at")
    search_fields = ("name", "type", "dosage")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "name", "age", "gender", "phone_number")
    search_fields = ("patient_id", "name", "phone_number", "email")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_code", "patient", "doctor", "date", "follow_up_date")
    search_fields = ("patient_code", "patient__name", "doctor__name", "doctor__user__first_name", "doctor__user__last_name")
    inlines = [PrescriptionMedicineInline]


@admin.register(SpecialistDoctor)
class SpecialistDoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "phone_number", "experience")
    search_fields = ("name", "specialization", "email")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient_name", "preferred_date", "preferred_time", "specialist", "status")
    list_filter = ("status", "preferred_date")
    search_fields = ("patient_name", "phone_number", "email")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "email", "created_at")
    search_fields = ("name", "email", "subject")

# Register your models here.
