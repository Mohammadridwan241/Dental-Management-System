from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.doctor_register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("complete-profile/", views.complete_profile, name="complete_profile"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/add/", views.medicine_create, name="medicine_create"),
    path("medicines/<int:pk>/edit/", views.medicine_update, name="medicine_update"),
    path("medicines/<int:pk>/delete/", views.medicine_delete, name="medicine_delete"),
    path("specialists/", views.specialist_list, name="specialist_list"),
    path("specialists/add/", views.specialist_create, name="specialist_create"),
    path("specialists/<int:pk>/edit/", views.specialist_update, name="specialist_update"),
    path("specialists/<int:pk>/delete/", views.specialist_delete, name="specialist_delete"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/<int:pk>/status/", views.appointment_status_update, name="appointment_status_update"),
    path("appointments/book/", views.book_appointment, name="book_appointment"),
    path("contact/", views.contact_message_create, name="contact_message_create"),
    path("prescriptions/", views.prescription_list, name="prescription_list"),
    path("prescriptions/create/", views.prescription_create, name="prescription_create"),
    path("prescriptions/<int:pk>/", views.prescription_detail, name="prescription_detail"),
    path("prescriptions/<int:pk>/pdf/", views.prescription_pdf, name="prescription_pdf"),
]
