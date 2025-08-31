
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Booking, Listing, Payment, Review


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "price_per_night", "max_guests", "created_at")
    list_filter = ("created_at", "max_guests")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Basic Information", {"fields": ("title", "description")}),
        ("Pricing & Capacity", {"fields": ("price_per_night", "max_guests")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = (
        "id",
        "transaction_id",
        "booking_reference",
        "status",
        "created_at",
        "updated_at",
        "completed_at",
    )
    fields = (
        "amount",
        "currency",
        "payment_method",
        "status",
        "customer_email",
        "customer_name",
        "customer_phone",
        "booking_reference",
        "transaction_id",
        "checkout_url",
        "created_at",
        "completed_at",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "listing_title",
        "start_date",
        "end_date",
        "status",
        "payment_status",
        "created_at",
    )
    list_filter = ("status", "created_at", "start_date")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "listing__title",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Booking Information",
            {
                "fields": (
                    "user",
                    "listing",
                    "start_date",
                    "end_date",
                    "status",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    readonly_fields = ("created_at", "payment_status")
    inlines = [PaymentInline]

    def listing_title(self, obj):
        return obj.listing.title

    listing_title.short_description = "Listing"
    listing_title.admin_order_field = "listing__title"

    def payment_status(self, obj):
        if hasattr(obj, "payment"):
            status = obj.payment.status
            colors = {
                "completed": "green",
                "processing": "orange",
                "pending": "blue",
                "failed": "red",
                "cancelled": "gray",
            }
            color = colors.get(status, "black")
            return format_html(
                '<span style="color: {};">{}</span>', color, status.title()
            )
        return format_html('<span style="color: gray;">No Payment</span>')

    payment_status.short_description = "Payment Status"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference",
        "booking_id",
        "customer_name",
        "amount",
        "currency",
        "status",
        "payment_method",
        "created_at",
    )
    list_filter = ("status", "payment_method", "currency", "created_at")
    search_fields = (
        "booking_reference",
        "transaction_id",
        "customer_email",
        "customer_name",
        "booking__id",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Payment Information",
            {"fields": ("booking", "amount", "currency", "payment_method", "status")},
        ),
        (
            "Customer Information",
            {"fields": ("customer_email", "customer_name", "customer_phone")},
        ),
        (
            "Chapa Details",
            {
                "fields": (
                    "booking_reference",
                    "transaction_id",
                    "checkout_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Response Data",
            {"fields": ("chapa_response_data",), "classes": ("collapse",)},
        ),
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "completed_at",
        "transaction_id",
        "booking_reference",
    )

    def booking_id(self, obj):
        if obj.booking:
            url = reverse("admin:listings_booking_change", args=[obj.booking.pk])
            return format_html('<a href="{}">{}</a>', url, obj.booking.id)
        return "No Booking"

    booking_id.short_description = "Booking"
    booking_id.admin_order_field = "booking__id"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ("booking",)
        return self.readonly_fields


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("listing", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__email", "listing__title", "comment")
    ordering = ("-created_at",)

    fieldsets = (
        ("Review Information", {"fields": ("listing", "user", "rating", "comment")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    readonly_fields = ("created_at",)
