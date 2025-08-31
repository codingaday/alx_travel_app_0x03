
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="ALX Travel App API",
        default_version="v1",
        description="""
        API for the ALX Travel App - A platform for booking travel accommodations.
        
        ## Authentication
        This API uses session authentication by default. Make sure to include the session cookie 
        in your requests when authentication is required.
        
        ## Endpoints
        - `/api/listings/` - Manage travel listings
        - `/api/bookings/` - Manage bookings
        - `/api/docs/` - Interactive API documentation
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@alx.com"),
        license=openapi.License(name="ALX License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin site
    path("admin/", admin.site.urls),
    # API endpoints
    path(
        "api/",
        include(
            [
                # API v1
                path(
                    "v1/",
                    include(
                        [
                            # Listings app
                            path("listings/", include("listings.urls")),
                            # Add more app URLs here as needed
                        ]
                    ),
                ),
                # JWT Authentication
                path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
                path(
                    "token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
                ),
                # API documentation
                path(
                    "docs/",
                    schema_view.with_ui("swagger", cache_timeout=0),
                    name="schema-swagger-ui",
                ),
                path(
                    "redoc/",
                    schema_view.with_ui("redoc", cache_timeout=0),
                    name="schema-redoc",
                ),
            ]
        ),
    ),
]
