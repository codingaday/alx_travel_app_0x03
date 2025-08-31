
import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Booking, Listing, Review
from .serializers import BookingSerializer, ListingSerializer, ReviewSerializer

User = get_user_model()


class ModelTests(TestCase):
    """Test the models for the listings app."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        self.listing = Listing.objects.create(
            title="Test Listing",
            description="A test listing",
            price_per_night=Decimal("100.00"),
            max_guests=4,
        )

        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            status="pending",
        )

        self.review = Review.objects.create(
            listing=self.listing, user=self.user, rating=5, comment="Great place!"
        )

    def test_listing_creation(self):
        """Test that a listing can be created."""
        self.assertEqual(str(self.listing), "Test Listing")
        self.assertEqual(self.listing.max_guests, 4)
        self.assertEqual(self.listing.price_per_night, Decimal("100.00"))

    def test_booking_creation(self):
        """Test that a booking can be created."""
        self.assertEqual(str(self.booking), f"{self.user.email} - Test Listing")
        self.assertEqual(self.booking.status, "pending")
        self.assertTrue(self.booking.end_date > self.booking.start_date)

    def test_review_creation(self):
        """Test that a review can be created."""
        self.assertEqual(str(self.review), "5 stars for Test Listing")
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, "Great place!")


class SerializerTests(TestCase):
    """Test the serializers for the listings app."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.listing_data = {
            "title": "Test Listing",
            "description": "A test listing",
            "price_per_night": Decimal("100.00"),
            "max_guests": 4,
        }

        self.listing = Listing.objects.create(**self.listing_data)

        self.booking_data = {
            "listing": self.listing.pk,
            "user": self.user.pk,
            "start_date": date.today() + timedelta(days=1),
            "end_date": date.today() + timedelta(days=3),
            "status": "pending",
        }

        self.review_data = {
            "listing": self.listing.pk,
            "user": self.user.pk,
            "rating": 5,
            "comment": "Great place!",
        }

    def test_listing_serializer(self):
        """Test the listing serializer."""
        serializer = ListingSerializer(instance=self.listing)
        serializer_data = dict(serializer.data)
        self.assertEqual(serializer_data["title"], self.listing_data["title"])
        self.assertEqual(Decimal(serializer_data["price_per_night"]), Decimal("100.00"))

    def test_booking_serializer(self):
        """Test the booking serializer."""
        serializer = BookingSerializer(data=self.booking_data)
        self.assertTrue(serializer.is_valid())

        # Test invalid date range
        invalid_data = self.booking_data.copy()
        invalid_data["end_date"] = invalid_data["start_date"] - timedelta(days=1)
        serializer = BookingSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

    def test_review_serializer(self):
        """Test the review serializer."""
        serializer = ReviewSerializer(data=self.review_data)
        self.assertTrue(serializer.is_valid())

        # Test invalid rating
        invalid_data = self.review_data.copy()
        invalid_data["rating"] = 6  # Should be between 1-5
        serializer = ReviewSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class ListingAPITests(APITestCase):
    """Test the listing API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Create test listings
        self.listing1 = Listing.objects.create(
            title="Test Listing 1",
            description="First test listing",
            price_per_night=Decimal("100.00"),
            max_guests=2,
        )
        self.listing2 = Listing.objects.create(
            title="Test Listing 2",
            description="Second test listing",
            price_per_night=Decimal("200.00"),
            max_guests=4,
        )

        self.valid_payload = {
            "title": "New Test Listing",
            "description": "A new test listing",
            "price_per_night": "150.00",
            "max_guests": 3,
        }

        self.invalid_payload = {
            "title": "",  # Title cannot be blank
            "description": "Invalid listing",
            "price_per_night": "-100.00",  # Price cannot be negative
            "max_guests": 0,  # Must be at least 1
        }

    def test_get_listings(self):
        """Test retrieving a list of listings."""
        response = self.client.get(reverse("listings:listing-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()

        # Handle both paginated and non-paginated responses
        if isinstance(response_data, dict) and "results" in response_data:
            # Paginated response
            results = response_data["results"]
        else:
            # Non-paginated response (simple list)
            results = response_data

        self.assertEqual(len(results), 2)

    def test_get_single_listing(self):
        """Test retrieving a single listing."""
        # Use 'id' instead of 'pk' to match URL pattern
        response = self.client.get(
            reverse("listings:listing-detail", kwargs={"id": self.listing1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        self.assertEqual(response_data["title"], self.listing1.title)

    def test_create_valid_listing(self):
        """Test creating a listing with valid payload."""
        response = self.client.post(
            reverse("listings:listing-list"),
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_listing(self):
        """Test creating a listing with invalid payload."""
        response = self.client.post(
            reverse("listings:listing-list"),
            data=json.dumps(self.invalid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_listings_by_price(self):
        """Test filtering listings by maximum price."""
        response = self.client.get(
            reverse("listings:listing-list"), {"max_price": "150.00"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()

        # Handle both paginated and non-paginated responses
        if isinstance(response_data, dict) and "results" in response_data:
            results = response_data["results"]
        else:
            results = response_data

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Listing 1")


class BookingAPITests(APITestCase):
    """Test the booking API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Create a listing
        self.listing = Listing.objects.create(
            title="Test Listing",
            description="A test listing",
            price_per_night=Decimal("100.00"),
            max_guests=4,
        )

        # Create a booking
        self.booking = Booking.objects.create(
            listing=self.listing,
            user=self.user,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            status="pending",
        )

        # Use string format for dates in API requests
        self.valid_booking_data = {
            "listing": self.listing.pk,
            "start_date": (date.today() + timedelta(days=15)).isoformat(),
            "end_date": (date.today() + timedelta(days=17)).isoformat(),
        }

        self.invalid_booking_data = {
            "listing": self.listing.pk,
            "start_date": (date.today() + timedelta(days=5)).isoformat(),
            "end_date": date.today().isoformat(),  # End date before start date
        }

    def test_get_bookings(self):
        """Test retrieving a list of bookings."""
        response = self.client.get(reverse("listings:booking-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()

        # Handle both paginated and non-paginated responses
        if isinstance(response_data, dict) and "results" in response_data:
            results = response_data["results"]
        else:
            results = response_data

        self.assertEqual(len(results), 1)

    def test_create_booking(self):
        """Test creating a new booking."""
        response = self.client.post(
            reverse("listings:booking-list"),
            data=json.dumps(self.valid_booking_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_booking(self):
        """Test creating a booking with invalid dates."""
        response = self.client.post(
            reverse("listings:booking-list"),
            data=json.dumps(self.invalid_booking_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_bookings_by_listing(self):
        """Test filtering bookings by listing ID."""
        response = self.client.get(
            reverse("listings:booking-list"), {"listing_id": self.listing.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()

        # Handle both paginated and non-paginated responses
        if isinstance(response_data, dict) and "results" in response_data:
            results = response_data["results"]
        else:
            results = response_data

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.booking.pk)

    def test_cancel_booking(self):
        """Test canceling a booking."""
        # Use 'id' instead of 'pk' to match URL pattern
        # Include required fields for the serializer validation
        response = self.client.patch(
            reverse("listings:booking-detail", kwargs={"id": self.booking.pk}),
            data=json.dumps(
                {
                    "status": "cancelled",
                    "listing": self.listing.pk,
                    "start_date": self.booking.start_date.isoformat(),
                    "end_date": self.booking.end_date.isoformat(),
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "cancelled")


class ReviewModelIntegrationTests(APITestCase):
    """Test review model integration without API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Create a listing
        self.listing = Listing.objects.create(
            title="Test Listing",
            description="A test listing",
            price_per_night=Decimal("100.00"),
            max_guests=4,
        )

        # Create a review
        self.review = Review.objects.create(
            listing=self.listing,
            user=self.user,
            rating=5,
            comment="Great place!",
        )

        self.valid_review_data = {
            "listing": self.listing.pk,
            "rating": 4,
            "comment": "Good place to stay",
        }

        self.invalid_review_data = {
            "listing": self.listing.pk,
            "rating": 6,  # Invalid rating (should be 1-5)
            "comment": "Invalid rating",
        }

    def test_review_model_creation(self):
        """Test creating reviews through the model."""
        # Test valid review creation
        review = Review.objects.create(
            listing=self.listing,
            user=self.user,
            rating=4,
            comment="Good place to stay",
        )
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, "Good place to stay")
        self.assertEqual(str(review), "4 stars for Test Listing")

    def test_review_serializer_validation(self):
        """Test review serializer validation."""
        # Test valid review data
        serializer = ReviewSerializer(data=self.valid_review_data)
        self.assertTrue(serializer.is_valid())

        # Test invalid review data
        serializer = ReviewSerializer(data=self.invalid_review_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("rating", serializer.errors)

    def test_review_listing_relationship(self):
        """Test the relationship between reviews and listings."""
        # Create multiple reviews for the same listing
        Review.objects.create(
            listing=self.listing,
            user=self.user,
            rating=3,
            comment="Average place",
        )

        # Check that listing has multiple reviews
        reviews = Review.objects.filter(listing=self.listing)
        self.assertEqual(reviews.count(), 2)  # Including the one from setUp

        # Check average rating calculation (if implemented)
        total_rating = sum(review.rating for review in reviews)
        avg_rating = total_rating / reviews.count()
        self.assertEqual(avg_rating, 4.0)  # (5 + 3) / 2 = 4.0
