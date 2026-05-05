from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DoctorProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    name = models.CharField(max_length=180, blank=True)
    name_bn = models.CharField(max_length=180, blank=True)
    degrees = models.CharField(max_length=255, blank=True)
    degrees_bn = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    specialization = models.CharField(max_length=150)
    specialization_bn = models.CharField(max_length=150, blank=True)
    training_details = models.TextField(blank=True)
    training_details_bn = models.TextField(blank=True)
    designation = models.CharField(max_length=200, blank=True)
    designation_bn = models.CharField(max_length=200, blank=True)
    hospital_name = models.CharField(max_length=200, blank=True)
    hospital_name_bn = models.CharField(max_length=200, blank=True)
    bmdc_no = models.CharField(max_length=100, blank=True)
    visiting_hours = models.CharField(max_length=200, blank=True)
    chamber_info = models.TextField(blank=True)
    experience = models.PositiveIntegerField(help_text="Experience in years")
    profile_image = models.ImageField(upload_to="doctor_profiles/", blank=True, null=True)
    signature_image = models.ImageField(upload_to="doctor_signatures/", blank=True, null=True)

    class Meta:
        ordering = ["user__first_name"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.name or self.user.get_full_name() or self.user.username

    @property
    def display_name_bn(self):
        return self.name_bn or self.display_name

    @property
    def display_degrees_bn(self):
        return self.degrees_bn or self.degrees

    @property
    def display_specialization_bn(self):
        return self.specialization_bn or self.specialization

    @property
    def display_training_bn(self):
        return self.training_details_bn or self.training_details

    @property
    def display_designation_bn(self):
        return self.designation_bn or self.designation

    @property
    def display_hospital_bn(self):
        return self.hospital_name_bn or self.hospital_name


class Medicine(TimeStampedModel):
    TYPE_CHOICES = [
        ("Tablet", "Tablet"),
        ("Capsule", "Capsule"),
        ("Drop", "Drop"),
        ("Syrup", "Syrup"),
        ("Injection", "Injection"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=150, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="Tablet")
    dosage = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        suffix = f" {self.dosage}" if self.dosage else ""
        return f"{self.type} {self.name}{suffix}".strip()


class SpecialistDoctor(TimeStampedModel):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    specialization = models.CharField(max_length=150)
    experience = models.PositiveIntegerField(help_text="Experience in years")
    profile_image = models.ImageField(upload_to="specialists/", blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Patient(TimeStampedModel):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=150)
    patient_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.patient_id or self.age})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.patient_id:
            self.patient_id = f"SDC{timezone.localdate():%Y%m}{self.pk:04d}"
            Patient.objects.filter(pk=self.pk).update(patient_id=self.patient_id)


class Prescription(TimeStampedModel):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="prescriptions")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions")
    patient_code = models.CharField(max_length=20, blank=True)
    date = models.DateField(default=timezone.localdate)
    chief_complaint = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    advice = models.TextField(blank=True)
    follow_up_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prescription #{self.pk} - {self.patient.name}"

    def get_absolute_url(self):
        return reverse("prescription_detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if self.patient and not self.patient_code:
            self.patient_code = self.patient.patient_id
        super().save(*args, **kwargs)


class PrescriptionMedicine(models.Model):
    FOOD_CHOICES = [
        ("Before Food", "Before Food"),
        ("After Food", "After Food"),
    ]

    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="prescription_medicines"
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dose = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    instruction = models.CharField(max_length=200, blank=True)
    days = models.PositiveIntegerField(default=0)
    times_per_day = models.CharField(max_length=50, blank=True)
    food_instruction = models.CharField(max_length=20, choices=FOOD_CHOICES, blank=True)
    additional_instructions = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.medicine.name} for {self.prescription.patient.name}"

    @property
    def display_dose(self):
        return self.dose or self.times_per_day

    @property
    def display_duration(self):
        return self.duration or (f"{self.days} days" if self.days else "")

    @property
    def display_instruction(self):
        return self.instruction or self.food_instruction or self.additional_instructions


class Appointment(TimeStampedModel):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    patient_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    specialist = models.ForeignKey(
        SpecialistDoctor,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="appointments",
    )
    problem_description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    class Meta:
        ordering = ["preferred_date", "preferred_time"]

    def __str__(self):
        return f"{self.patient_name} - {self.preferred_date}"


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"

# Create your models here.
