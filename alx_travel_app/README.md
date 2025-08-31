# ALX Travel App Backend with Chapa Payment Integration

The ALX Travel App is a Django-based backend for a travel listing platform with integrated Chapa payment processing, designed with industry best practices for scalability, maintainability, and secure payment handling.

## Features

- **RESTful API** built with Django REST Framework
- **Chapa Payment Integration** for secure payment processing
- **Comprehensive Documentation** with Swagger UI and ReDoc
- **Secure Authentication** (Session-based)
- **Background Tasks** with Celery for email notifications
- **Data Validation** with DRF serializers
- **Versioned API** (v1)
- **Filtering & Search** for listings and bookings
- **MySQL Database** for production
- **Environment-based** configuration
- **CORS Support** for cross-domain requests
- **Payment Webhooks** for real-time payment status updates

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Chapa Setup](#chapa-setup)
- [API Documentation](#api-documentation)
- [Payment Flow](#payment-flow)
- [Testing Payment Integration](#testing-payment-integration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)

## Prerequisites

- Python 3.12+
- MySQL 8.0+
- Redis (for Celery background tasks)
- Git
- Chapa API Account ([https://developer.chapa.co/](https://developer.chapa.co/))

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/alx_travel_app_0x02.git
   cd alx_travel_app_0x02
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
   Copy `.env.example` to `.env` and update the values:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your actual values:

   ```env
   # Django Settings
   SECRET_KEY='your-secret-key-here'
   DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

   # Database
   MYSQL_DATABASE=alx_travel_db
   MYSQL_USER=alx_user
   MYSQL_PASSWORD=your_secure_password
   MYSQL_HOST=localhost
   MYSQL_PORT=3306

   # Chapa Payment API
   CHAPA_SECRET_KEY=your-chapa-secret-key
   CHAPA_PUBLIC_KEY=your-chapa-public-key
   CHAPA_BASE_URL=https://api.chapa.co/v1/

   # Email Configuration
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password

   # Celery
   CELERY_BROKER_URL=redis://localhost:6379/0
   ```

2. **Database Setup**

   ```sql
   CREATE DATABASE alx_travel_db;
   CREATE USER 'alx_user'@'localhost' IDENTIFIED BY 'your_secure_password';
   GRANT ALL PRIVILEGES ON alx_travel_db.* TO 'alx_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Run Migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Chapa Setup

1. **Create Chapa Account**
   - Go to [https://developer.chapa.co/](https://developer.chapa.co/)
   - Sign up for a developer account
   - Get your API keys from the dashboard

2. **Configure Webhook URL**
   - In your Chapa dashboard, set the webhook URL to:
   - `http://your-domain.com/api/v1/payments/webhook/`
   - For local testing: `http://localhost:8000/api/v1/payments/webhook/`

3. **Test Mode**
   - Use Chapa's sandbox environment for testing
   - Switch to production keys when ready to go live

## API Documentation

### Interactive Documentation

- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

### Authentication

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
   "username": "your_username",
   "password": "your_password"
}
```

### Payment Endpoints

#### Initiate Payment

```http
POST /api/v1/bookings/{id}/initiate_payment/
Authorization: Bearer <your_token>
Content-Type: application/json

{
   "customer_phone": "+251911234567",
   "return_url": "http://localhost:3000/payment-success"
}
```

#### Verify Payment

```http
POST /api/v1/payments/verify/
Authorization: Bearer <your_token>
Content-Type: application/json

{
   "tx_ref": "ALX_TRAVEL_ABC123"
}
```

## Payment Flow

1. **Create Booking**

   ```http
   POST /api/v1/bookings/
   {
     "listing": 1,
     "start_date": "2025-08-15",
     "end_date": "2025-08-22"
   }
   ```

2. **Initiate Payment**

   ```http
   POST /api/v1/bookings/1/initiate_payment/
   {
     "customer_phone": "+251911234567"
   }
   ```

3. **User Completes Payment**
   - User is redirected to Chapa checkout page
   - User completes payment using their preferred method

4. **Payment Verification**
   - Webhook automatically updates payment status
   - Or manually verify using `/payments/verify/`

5. **Confirmation**
   - Email confirmation sent automatically
   - Booking status updated to "confirmed"

## Testing Payment Integration

### Using Chapa Sandbox

1. **Test Card Numbers**
   - Successful payment: `4000 0000 0000 0002`
   - Failed payment: `4000 0000 0000 0127`

2. **Test Mobile Money**
   - Use test phone numbers provided in Chapa documentation
   - Test different scenarios (success, failure, pending)

3. **Webhook Testing**
   - Use ngrok for local webhook testing:

   ```bash
   ngrok http 8000
   ```

   - Update webhook URL in Chapa dashboard to ngrok URL

### Example Test Scenarios

```bash
# 1. Create a test booking
curl -X POST http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"listing": 1, "start_date": "2025-08-15", "end_date": "2025-08-22"}'

# 2. Initiate payment
curl -X POST http://localhost:8000/api/v1/bookings/1/initiate_payment/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"customer_phone": "+251911234567"}'

# 3. Verify payment
curl -X POST http://localhost:8000/api/v1/payments/verify/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"tx_ref": "ALX_TRAVEL_ABC123"}'
```

## Running the Application

### Start Django Development Server

```bash
python manage.py runserver
```

### Start Celery Worker (New Terminal)

```bash
celery -A alx_travel_app worker --loglevel=info
```

### Start Redis Server

```bash
redis-server
```

### Monitor Tasks (Optional)

```bash
celery -A alx_travel_app flower
```

Visit <http://localhost:5555> for Celery monitoring dashboard.

## Project Structure

```text
alx_travel_app/
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── manage.py                # Django management script
├── requirements.txt         # Project dependencies
│
├── alx_travel_app/          # Main project package
│   ├── __init__.py
│   ├── settings.py          # Project settings
│   ├── urls.py             # Main URL configuration
│   ├── wsgi.py             # WSGI config
│   └── celery.py           # Celery configuration
│
└── listings/               # Listings application
    ├── migrations/         # Database migrations
    ├── services/          # Business logic services
    │   ├── __init__.py
    │   └── chapa_service.py
    ├── __init__.py
    ├── admin.py          # Admin configuration
    ├── apps.py           # App configuration
    ├── models.py         # Database models
    ├── serializers.py    # API serializers
    ├── tasks.py          # Celery tasks
    ├── tests.py          # Application tests
    ├── urls.py           # App URL routes
    └── views.py          # API views
```

## Key Integration Features

### Payment Model

- Secure payment tracking with UUID primary keys
- Integration with Chapa transaction references
- Support for multiple payment methods
- Comprehensive audit trail

### Chapa Service

- Centralized payment processing logic
- Error handling and retry mechanisms
- Support for payment initiation and verification
- Webhook processing for real-time updates

### Background Tasks

- Email notifications for payment confirmations
- Failure notifications with error details
- Retry mechanism for failed email sends
- Scalable task processing with Celery

### Security Features

- User-specific payment access control
- Secure API key management
- Input validation and sanitization
- Comprehensive logging for audit trails

## Testing Checklist

- [ ] Payment initiation works with valid booking
- [ ] Payment verification updates status correctly
- [ ] Webhook processing handles all status types
- [ ] Email notifications are sent successfully
- [ ] Failed payments are handled gracefully
- [ ] User can only access their own payments
- [ ] Admin can view all payments in Django admin

## Deployment Notes

1. **Environment Variables**: Ensure all production keys are set
2. **Webhook URL**: Update Chapa webhook URL to production domain
3. **Email Configuration**: Configure production email settings
4. **Redis**: Set up Redis for Celery in production
5. **SSL**: Ensure HTTPS is enabled for webhook security

## License

This project is for educational purposes within the ALX ProDEV program.
