from django.contrib import admin
from rentals.models import Hall, Booking, Payment

# Register your models here.
admin.site.register(Hall)
admin.site.register(Booking)
admin.site.register(Payment)