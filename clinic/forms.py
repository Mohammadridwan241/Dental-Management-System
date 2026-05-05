from django import forms
from django.contrib.auth.models import User
from django.forms import BaseInlineFormSet
from django.forms import inlineformset_factory
from django.utils import timezone

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


class DateInput(forms.DateInput):
    input_type = "date"


class TimeInput(forms.TimeInput):
    input_type = "time"


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} {css_class}".strip()


def get_public_specialists_queryset():
    doctor_emails = DoctorProfile.objects.select_related("user").values_list("user__email", flat=True)
    admin_emails = [email for email in User.objects.filter(is_staff=True).values_list("email", flat=True) if email]
    admin_names = [
        " ".join(name_parts).strip()
        for name_parts in User.objects.filter(is_staff=True).values_list("first_name", "last_name")
        if " ".join(name_parts).strip()
    ]
    queryset = SpecialistDoctor.objects.exclude(email__in=doctor_emails).exclude(email__in=admin_emails)
    if admin_names:
        queryset = queryset.exclude(name__in=admin_names)
    return queryset.order_by("name")


class DoctorRegistrationForm(StyledFormMixin, forms.ModelForm):
    doctor_name = forms.CharField(max_length=150)
    doctor_name_bn = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = DoctorProfile
        fields = [
            "doctor_name",
            "doctor_name_bn",
            "email",
            "degrees",
            "degrees_bn",
            "phone_number",
            "address",
            "specialization",
            "specialization_bn",
            "training_details",
            "training_details_bn",
            "designation",
            "designation_bn",
            "hospital_name",
            "hospital_name_bn",
            "bmdc_no",
            "visiting_hours",
            "chamber_info",
            "experience",
            "profile_image",
            "signature_image",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        full_name = self.cleaned_data["doctor_name"].strip()
        first_name, _, last_name = full_name.partition(" ")
        user = User(
            username=self.cleaned_data["email"],
            email=self.cleaned_data["email"],
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        profile = super().save(commit=False)
        profile.user = user
        profile.name = full_name
        profile.name_bn = self.cleaned_data["doctor_name_bn"]
        if commit:
            profile.save()
        return profile


def sync_specialist_from_doctor(profile, full_name=None):
    return None


class DoctorProfileCompletionForm(StyledFormMixin, forms.ModelForm):
    doctor_name = forms.CharField(max_length=150)
    doctor_name_bn = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(disabled=True, required=False)

    class Meta:
        model = DoctorProfile
        fields = [
            "doctor_name",
            "doctor_name_bn",
            "email",
            "degrees",
            "degrees_bn",
            "phone_number",
            "address",
            "specialization",
            "specialization_bn",
            "training_details",
            "training_details_bn",
            "designation",
            "designation_bn",
            "hospital_name",
            "hospital_name_bn",
            "bmdc_no",
            "visiting_hours",
            "chamber_info",
            "experience",
            "profile_image",
            "signature_image",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        profile = kwargs.get("instance")
        self.fields["doctor_name"].initial = (
            getattr(profile, "name", "") or self.user.get_full_name() or self.user.username
        )
        self.fields["doctor_name_bn"].initial = getattr(profile, "name_bn", "")
        self.fields["email"].initial = self.user.email

    def save(self, commit=True):
        full_name = self.cleaned_data["doctor_name"].strip()
        first_name, _, last_name = full_name.partition(" ")
        self.user.first_name = first_name
        self.user.last_name = last_name
        if commit:
            self.user.save(update_fields=["first_name", "last_name"])
        profile = super().save(commit=False)
        profile.user = self.user
        profile.name = full_name
        profile.name_bn = self.cleaned_data["doctor_name_bn"]
        if commit:
            profile.save()
        return profile


class MedicineForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["type", "name", "dosage", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class SpecialistDoctorForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SpecialistDoctor
        fields = [
            "name",
            "email",
            "phone_number",
            "address",
            "specialization",
            "experience",
            "profile_image",
        ]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class AppointmentForm(StyledFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["specialist"].queryset = get_public_specialists_queryset()

    class Meta:
        model = Appointment
        fields = [
            "patient_name",
            "phone_number",
            "preferred_date",
            "preferred_time",
            "specialist",
            "problem_description",
        ]
        widgets = {
            "preferred_date": DateInput(),
            "preferred_time": TimeInput(),
            "problem_description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data["preferred_date"]
        if preferred_date < timezone.localdate():
            raise forms.ValidationError("Preferred date cannot be in the past.")
        return preferred_date


class ContactMessageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone_number", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}


class PrescriptionForm(StyledFormMixin, forms.ModelForm):
    patient_name = forms.CharField(max_length=150)
    patient_age = forms.IntegerField(min_value=0)
    patient_gender = forms.ChoiceField(choices=Patient.GENDER_CHOICES)
    patient_weight = forms.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    patient_phone_number = forms.CharField(max_length=20)
    patient_email = forms.EmailField(required=False)

    class Meta:
        model = Prescription
        fields = [
            "patient_name",
            "patient_age",
            "patient_gender",
            "patient_weight",
            "patient_phone_number",
            "patient_email",
            "date",
            "chief_complaint",
            "diagnosis",
            "advice",
            "follow_up_date",
        ]
        widgets = {
            "date": DateInput(),
            "chief_complaint": forms.Textarea(attrs={"rows": 4}),
            "diagnosis": forms.Textarea(attrs={"rows": 3}),
            "advice": forms.Textarea(attrs={"rows": 3}),
            "follow_up_date": DateInput(),
        }

    def save(self, doctor, commit=True):
        patient_data = {
            "name": self.cleaned_data["patient_name"],
            "age": self.cleaned_data["patient_age"],
            "gender": self.cleaned_data["patient_gender"],
            "weight": self.cleaned_data["patient_weight"],
            "phone_number": self.cleaned_data["patient_phone_number"],
            "email": self.cleaned_data["patient_email"],
        }
        patient = Patient.objects.create(**patient_data)
        prescription = super().save(commit=False)
        prescription.patient = patient
        prescription.patient_code = patient.patient_id
        prescription.doctor = doctor
        if commit:
            prescription.save()
        return prescription


class RequiredPrescriptionMedicineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False) and form.cleaned_data.get("medicine"):
                active_forms += 1
        if active_forms == 0:
            raise forms.ValidationError("Add at least one medicine to the prescription.")


PrescriptionMedicineFormSet = inlineformset_factory(
    Prescription,
    PrescriptionMedicine,
    formset=RequiredPrescriptionMedicineFormSet,
    fields=[
        "medicine",
        "dose",
        "duration",
        "instruction",
    ],
    extra=1,
    can_delete=True,
    widgets={
        "dose": forms.TextInput(attrs={"placeholder": "1 + 0 + 1"}),
        "duration": forms.TextInput(attrs={"placeholder": "10 days"}),
        "instruction": forms.TextInput(attrs={"placeholder": "After meal"}),
    },
)
