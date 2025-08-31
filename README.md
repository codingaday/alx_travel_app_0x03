# ALX Travel App Backend

The ALX Travel App is a Django-based backend for a travel listing platform with integrated payment processing. It's designed with industry best practices for scalability, maintainability, and team collaboration.

## Key Features

- **RESTful API** built with Django REST Framework
- **Chapa Payment Gateway** integration for secure payments
- **Comprehensive Documentation** with Swagger UI and ReDoc
- **Secure Authentication** (Session-based)
- **Data Validation** with DRF serializers
- **Versioned API** (v1)
- **Filtering & Search** for listings and bookings
- **MySQL/PostgreSQL** database support
- **Environment-based** configuration
- **CORS Support** for cross-domain requests
- **Asynchronous Email Notifications**

## Tech Stack

- **Backend**: Django 4.2+
- **Database**: PostgreSQL/MySQL
- **Payment Processing**: Chapa API
- **Task Queue**: Celery with Redis
- **API Documentation**: Swagger/ReDoc
- **Testing**: Django Test Framework

## Table of Contents

- [ALX Travel App Backend](#alx-travel-app-backend)
  - [Key Features](#key-features)
  - [Tech Stack](#tech-stack)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [API Documentation](#api-documentation)
    - [Interactive Documentation](#interactive-documentation)
    - [Available Endpoints](#available-endpoints)
      - [Listings](#listings)
      - [Bookings](#bookings)
      - [Payments](#payments)
  - [Payment Integration](#payment-integration)
    - [Payment Flow](#payment-flow)
  - [Testing](#testing)
    - [Running Tests](#running-tests)
  - [Project Structure](#project-structure)
  - [License](#license)

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/alx_travel_app.git
   cd alx_travel_app
   ```

2. **Set up virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Unix/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Environment Variables**
   Create a `.env` file in the project root based on `.env.example`:

   ```env
   # Django Settings
   SECRET_KEY='your-secret-key-here'
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Database
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=alx_travel_db
   DB_USER=db_user
   DB_PASSWORD=your_secure_password
   DB_HOST=localhost
   DB_PORT=5432

   # Chapa Payment Settings
   CHAPA_SECRET_KEY=your_chapa_secret_key
   CHAPA_WEBHOOK_DOMAIN=your_webhook_domain
   
   # Email Settings
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # For development
   DEFAULT_FROM_EMAIL=noreply@example.com
   ```

2. **Database Setup**
   - For PostgreSQL:

     ```sql
     CREATE DATABASE alx_travel_db;
     CREATE USER db_user WITH PASSWORD 'your_secure_password';
     GRANT ALL PRIVILEGES ON DATABASE alx_travel_db TO db_user;
     ```

3. **Run Migrations**

   ```bash
   python manage.py migrate
   ```

## API Documentation

### Interactive Documentation

- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

### Available Endpoints

#### Listings

- `GET /api/v1/listings/` - List all listings
- `POST /api/v1/listings/` - Create new listing
- `GET /api/v1/listings/{id}/` - Get listing details
- `PUT/PATCH /api/v1/listings/{id}/` - Update listing
- `DELETE /api/v1/listings/{id}/` - Delete listing
- `GET /api/v1/listings/{id}/reviews/` - Get reviews for listing

#### Bookings

- `GET /api/v1/bookings/` - List all bookings
- `POST /api/v1/bookings/` - Create new booking
- `GET /api/v1/bookings/{id}/` - Get booking details
- `PUT/PATCH /api/v1/bookings/{id}/` - Update booking
- `DELETE /api/v1/bookings/{id}/` - Delete booking

#### Payments

- `POST /api/v1/payments/initiate/` - Initiate payment
- `POST /api/v1/payments/verify/` - Verify payment status
- `POST /api/v1/payments/webhook/` - Chapa webhook (for payment callbacks)

## Payment Integration

The application integrates with Chapa payment gateway for processing payments. Key features:

- Multiple payment methods support (Telebirr, CBE Birr, Ebirr, M-Pesa)
- Secure payment processing with transaction verification
- Webhook support for payment status updates
- Email notifications for payment events

### Payment Flow

1. User creates a booking
2. System generates a payment request
3. User is redirected to Chapa checkout
4. After payment, Chapa sends a webhook notification
5. System updates payment and booking status
6. User receives confirmation email

## Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test case
python manage.py test listings.tests.ModelTests

# Run with coverage
coverage run manage.py test
coverage report
```

## Project Structure

```text
alx_travel_app/
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── manage.py               # Django management script
├── requirements.txt        # Project dependencies
│
├── alx_travel_app/         # Main project package
│   ├── __init__.py
│   ├── settings/           # Settings directory
│   │   ├── base.py         # Base settings
│   │   ├── development.py  # Development settings
│   │   └── production.py   # Production settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI config
│
└── listings/              # Listings application
    ├── migrations/        # Database migrations
    ├── management/        # Custom management commands
    ├── __init__.py
    ├── admin.py          # Admin configuration
    ├── apps.py           # App configuration
    ├── models.py         # Database models
    ├── serializers.py    # API serializers
    ├── tasks.py          # Celery tasks
    ├── tests.py          # Application tests
    ├── urls.py          # App URL routes
    └── views.py         # API views
```

## License

This project is for educational purposes within the ALX ProDEV program.
