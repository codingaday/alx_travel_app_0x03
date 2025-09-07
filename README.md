# ALX Travel App 0x03: Asynchronous Booking Notifications

This project enhances the ALX Travel App by integrating a robust background task processing system using Celery and RabbitMQ. The primary goal is to improve user experience and application performance by offloading time-consuming tasks, such as sending email notifications, to a background worker process.

When a user creates a booking, the application now provides an immediate response and delegates the task of sending a confirmation email to Celery. This ensures the user is not left waiting for external services (like an SMTP server) to respond.

## Key Features

-   **Booking Management:** Full CRUD (Create, Read, Update, Delete) functionality for property bookings.
-   **Asynchronous Email Notifications:** Upon successful booking creation, a confirmation email is sent to the user in the background without blocking the API response.
-   **Scalable Task Queuing:** Utilizes an industry-standard stack (Celery and RabbitMQ) for managing background jobs, ensuring reliability and scalability.

## Technology Stack

-   **Backend:** Django, Django REST Framework
-   **Task Queue:** Celery
-   **Message Broker:** RabbitMQ
-   **Database:** SQLite3 (default)

---

## Setup and Installation

Follow these steps to get the project up and running on your local machine.

### 1. Prerequisites

Make sure you have the following installed:
-   Python 3.8+
-   `pip` and `virtualenv`
-   Git
-   Docker and Docker Compose (Recommended for easily running RabbitMQ)

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/alx_travel_app_0x03.git
cd alx_travel_app_0x03
```

### 3. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (on Linux/macOS)
source venv/bin/activate

# On Windows
# venv\Scripts\activate
```

### 4. Install Dependencies

Install all the required Python packages.

```bash
pip install -r requirements.txt
```

### 5. Set Up the Message Broker (RabbitMQ)

The easiest way to run RabbitMQ is with Docker.

```bash
# This command will download the RabbitMQ image with a management plugin
# and run it in the background.
docker run -d --hostname my-rabbit --name alx-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
-   The application will connect to RabbitMQ on port `5672`.
-   You can access the RabbitMQ management dashboard at `http://localhost:15672` (default user: `guest`, password: `guest`).

### 6. Apply Database Migrations

Initialize your database with the necessary tables.

```bash
python manage.py migrate
```

### 7. Create a Superuser (Optional)

This is useful for accessing the Django admin interface.

```bash
python manage.py createsuperuser
```

---

## Running the Application

To run the full application, you will need to have **three separate terminals** open and running concurrently.

### Terminal 1: Start the Django Development Server

This terminal will run your main web application.

```bash
# Make sure your virtual environment is activated
python manage.py runserver
```Your Django API will be available at `http://127.0.0.1:8000/`.

### Terminal 2: Start the Celery Worker

This terminal runs the worker process that listens for and executes background tasks from the RabbitMQ queue.

```bash
# Navigate to the same project directory
# Make sure your virtual environment is activated
celery -A alx_travel_app worker -l info
```
Keep this terminal open to see logs of tasks being received and processed.

### Terminal 3: (Verification) Ensure RabbitMQ is Running

You don't need to run a command here, but just make sure the Docker container you started in the setup step is still running.

```bash
docker ps
```
You should see the `alx-rabbit` container in the list.

---

## How to Test the Feature

1.  **Create a User:**
    -   Register a new user through your API endpoint or create one using the Django admin (`/admin`).
    -   Ensure the user has a valid email address.

2.  **Create a Booking:**
    -   Using an API client like Postman or `curl`, make a `POST` request to your bookings endpoint (e.g., `/api/bookings/`).
    -   Provide the necessary data for a new booking.

3.  **Verify the Results:**
    -   **Immediate API Response:** Your API client should receive a `201 Created` success response almost instantly.
    -   **Celery Worker Log:** Look at the terminal running the Celery worker. You will see output logs indicating that a task `listings.tasks.send_booking_confirmation_email` was received and then succeeded.
    -   **Django Server Log:** Look at the terminal running `manage.py runserver`. Since the project is configured with the `console.EmailBackend` for development, the **full content of the confirmation email will be printed directly to this terminal**. This confirms that the email was generated successfully.
