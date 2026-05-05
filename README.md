# Shafique's Dental Care

A Django-based Dental Management System for clinic homepage management, doctor registration, appointments, medicine management, specialist management, and printable PDF prescriptions.

## Features

- Doctor/admin registration and login
- Responsive clinic homepage with services, specialists, appointment, about, and contact sections
- Appointment booking for patients without login
- Dashboard for managing medicines, specialists, appointments, and prescriptions
- Prescription creation with multiple medicines
- Prescription history, print view, and PDF download
- Django admin configuration for all major models

## Stack

- Django
- Django Templates
- Bootstrap 5
- HTML, CSS, JavaScript
- SQLite
- ReportLab for PDF export

## Run Locally

```powershell
py -3 -m pip install -r requirements.txt
py -3 manage.py migrate
py -3 manage.py runserver
```

Open `http://127.0.0.1:8000/`

## Optional Admin User

```powershell
py -3 manage.py createsuperuser
```
