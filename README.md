# VGClinic

A modern clinic management system built with Django and React for the Costa Rican market, focused on odontology clinics.

## Project Overview

VGClinic is designed to manage:
- Appointments
- Billing
- Procedures
- Patients
- Clinic administration

The system supports both clinic owners and independent doctors who work across multiple clinics.

## Technical Architecture

### Backend
- **Framework**: Django 5.1.4
- **Database**: PostgreSQL (production), SQLite (development)
- **API**: Django REST Framework with JWT authentication
- **Internationalization**: Full support for English and Spanish

### Key Models

#### User Management (`platform_users`)
- Custom User model using email for authentication
- Support for both Cédula (9 digits) and DIMEX (11-12 digits) IDs
- Role-based access control

#### Account Management (`platform_accounts`)
- Flexible clinic account model
- Support for both platform clients and external clinics
- Role-based user-account relationships

## Setup Instructions

1. Clone the repository
2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables (see `.env.example`)
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Translation Workflow

The project supports multiple languages through Django's translation system:

1. Mark strings for translation using `gettext_lazy` (imported as `_`):
   ```python
   from django.utils.translation import gettext_lazy as _
   
   class MyModel(models.Model):
       name = models.CharField(_('Name'), max_length=100, help_text=_('Enter a name'))
   ```

2. Generate translation files:
   ```bash
   python manage.py makemessages -l es
   ```

3. Edit the `.po` file in `locale/es/LC_MESSAGES/django.po` to add translations

4. Compile translations:
   ```bash
   python manage.py compilemessages
   ```

5. Repeat steps 2-4 whenever new translatable content is added

## Model Design Decisions

### User Model
- Uses email as login credential instead of username
- Includes ID type field to distinguish between Cédula and DIMEX
- Uses standard auto-incrementing ID as primary key (not the ID number)
- Normalizes ID numbers by padding with zeros internally

### Account/Clinic Management
- Single Account model for both platform clients and external clinics
- `is_platform_account` flag to differentiate between full clients and external references
- Intermediary AccountUser model for flexible role assignment and clinic relationships

### Role System
- Predefined roles with configurable permissions
- Allows users to have different roles in different clinics
- Supports appointment color coding per doctor per clinic

## Development Guidelines

1. Make incremental changes and test thoroughly
2. Keep models focused and modular
3. Use Django's built-in features for authentication and permissions
4. Maintain translations as new features are added
5. Follow Django best practices for query optimization

## Planned Apps

- **Core Platform**
  - ✅ `platform_users`
  - ✅ `platform_accounts`
  - ✅ `platform_contracts`
  - ✅ `platform_services`
  - ⬜ `platform_billing`
  - ⬜ `platform_notifications`
  - ⬜ `platform_analytics`

- **Clinic Operations**
  - ✅ `clinic_catalog`
  - ✅ `clinic_locations`
  - ✅ `clinic_patients`
  - ✅ `clinic_billing`
  - ✅ `clinic_treatments`
  - ⬜ `clinic_appointments`
  - ⬜ `clinic_notifications`
  - ⬜ `clinic_analytics`