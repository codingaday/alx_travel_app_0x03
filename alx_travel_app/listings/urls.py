
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from . import views

# Create a router for API endpoints
router = DefaultRouter()
router.register(r"listings", views.ListingViewSet, basename="listing")
router.register(r"bookings", views.BookingViewSet, basename="booking")
router.register(r"payments", views.PaymentViewSet, basename="payment")

# Schema view for app-specific documentation
app_schema_view = get_schema_view(
    openapi.Info(
        title="ALX Travel App API",
        default_version="v1",
        description="""
        API endpoints for managing travel listings, bookings, and payments.
        
        ## Available Endpoints
        
        ### Listings
        - `/listings/` - Manage travel listings (GET, POST)
        - `/listings/{id}/` - Manage a specific listing (GET, PUT, PATCH, DELETE)
        - `/listings/{id}/reviews/` - Get reviews for a listing (GET)
        
        ### Bookings  
        - `/bookings/` - Manage bookings (GET, POST)
        - `/bookings/{id}/` - Manage a specific booking (GET, PUT, PATCH, DELETE)
        - `/bookings/{id}/initiate_payment/` - Initiate payment for a booking (POST)
        
        ### Payments
        - `/payments/` - View payments (GET)
        - `/payments/{id}/` - View specific payment (GET)
        - `/payments/initiate/` - Initiate new payment (POST)
        - `/payments/verify/` - Verify payment status (POST)
        - `/payments/webhook/` - Chapa webhook endpoint (POST)
        
        ## Payment Flow
        1. Create a booking
        2. Initiate payment using `/bookings/{id}/initiate_payment/` or `/payments/initiate/`
        3. User completes payment on Chapa checkout page
        4. Verify payment using `/payments/verify/` or wait for webhook notification
        5. Payment confirmation email sent automatically
        
        ## Filtering
        - Listings can be filtered by `max_price`
        - Bookings can be filtered by `listing_id`
        - Payments are automatically filtered by user (non-admin users see only their own)
        
        ## Authentication
        - Most endpoints require authentication
        - Webhook endpoint is public for Chapa notifications
        - Users can only access their own bookings and payments
        """,
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path("", include(router.urls)),
    ],
)

app_name = "listings"

urlpatterns = [
    # API endpoints
    path("", include(router.urls)),
    # Documentation
    path(
        "docs/",
        app_schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        app_schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]
