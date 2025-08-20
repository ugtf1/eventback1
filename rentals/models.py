from django.db import models

class Hall(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name="bookings")
    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hall.name} ({self.start_date} → {self.end_date})"


class Payment(models.Model):
    PROVIDERS = [
        ("paypal", "PayPal"),
        ("stripe", "Stripe"),
        ("paystack", "Paystack"),
    ]
    STATUSES = [
        ("initiated", "Initiated"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    provider_ref = models.CharField(max_length=120, blank=True)  # order_id, session_id, reference
    status = models.CharField(max_length=20, choices=STATUSES, default="initiated")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
