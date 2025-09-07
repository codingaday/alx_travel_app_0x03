from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Listing, Payment, Booking

# Register your models here.
class CustomUserAdmin(UserAdmin):
    # You can add customizations here in the future if needed
    pass

# Register your models
admin.site.register(User)
admin.site.register(Listing)
admin.site.register(Booking)
admin.site.register(Payment)
