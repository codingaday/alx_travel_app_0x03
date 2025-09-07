# ALX Travel App

## Description

The ALX Travel App is a platform for listing and discovering travel destinations. It provides a RESTful API for managing listings, bookings, reviews, and user accounts.

## Features

* User authentication and authorization
* Listing management (create, read, update, delete)
* Booking management (users can view and create their own bookings)
* Review management
* API documentation using Swagger and ReDoc

## Technologies Used

* Python 3.12+
* Django 5.2.4
* Django REST Framework 3.16.0
* MySQLclient 2.2.7
* drf-yasg 1.21.10
* django-cors-headers 4.7.0
* django-environ 0.12.0
* Other dependencies listed in [requirements.txt](alx_travel_app/requirements.txt)


## Setup Instructions

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd alx_travel_app
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    -   On Windows:

        ```bash
        .\venv\Scripts\activate
        ```

    -   On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Create a `.env` file:**

    Create a `.env` file in the project root directory with the following variables:

    ```
    DEBUG=True
    SECRET_KEY=<your_secret_key>
    DATABASE_URL=mysql://user:password@host:port/database_name
    ```

    Replace `<your_secret_key>`, `user`, `password`, `host`, `port`, and `database_name` with your actual values.

6.  **Apply migrations:**

    ```bash
    python manage.py migrate
    ```

7.  **Create a superuser:**

    ```bash
    python manage.py createsuperuser
    ```

8.  **(Optional) Seed the database with sample data:**

    ```bash
    python manage.py seed
    ```

9.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

## API Endpoints

* **Listings**: `/api/listings/`
  Supports full CRUD. Creating a listing automatically associates it with the authenticated user as the host.

* **Bookings**: `/api/bookings/`
  Users can view and create bookings. Bookings returned are limited to those made by the authenticated user.


## API Documentation

* Swagger UI: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
* Swagger JSON/YAML: [http://localhost:8000/swagger.json](http://localhost:8000/swagger.json)
* ReDoc: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)

## Models

### [`User`](alx_travel_app/listings/models.py)

Custom user model extending Django's AbstractUser.

-   `user_id`: UUID, primary key
-   `first_name`: CharField
-   `last_name`: CharField
-   `email`: EmailField, unique
-   `phone_number`: CharField, optional
-   `role`: CharField, choices: `guest`, `host`, `admin`
-   `created_at`: DateTimeField

### [`Listing`](alx_travel_app/listings/models.py)

Represents a property listing.

-   `property_id`: UUID, primary key
-   `host`: ForeignKey to [`User`](alx_travel_app/listings/models.py), related name: `listings`
-   `name`: CharField
-   `description`: TextField
-   `location`: CharField
-   `pricepernight`: DecimalField
-   `created_at`: DateTimeField
-   `updated_at`: DateTimeField

### [`Booking`](alx_travel_app/listings/models.py)

Represents a booking for a listing.

-   `booking_id`: UUID, primary key
-   `property`: ForeignKey to [`Listing`](alx_travel_app/listings/models.py), related name: `bookings`
-   `user`: ForeignKey to [`User`](alx_travel_app/listings/models.py), related name: `bookings`
-   `start_date`: DateField
-   `end_date`: DateField
-   `total_price`: DecimalField
-   `status`: CharField, choices: `pending`, `confirmed`, `canceled`
-   `created_at`: DateTimeField

### [`Review`](alx_travel_app/listings/models.py)

Represents a review for a listing.

-   `review_id`: UUID, primary key
-   `property`: ForeignKey to [`Listing`](alx_travel_app/listings/models.py), related name: `reviews`
-   `user`: ForeignKey to [`User`](alx_travel_app/listings/models.py), related name: `reviews`
-   `rating`: IntegerField
-   `comment`: TextField
-   `created_at`: DateTimeField

## Management Commands

### `seed`

Seeds the database with sample data.

```bash
python manage.py seed