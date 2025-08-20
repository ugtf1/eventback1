from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/halls/", views.halls_api, name="halls_api"),
    path("api/availability/", views.check_availability, name="check_availability"),
    path("api/book/", views.create_booking, name="create_booking"),

    # PayPal
    path("api/paypal/create-order/", views.paypal_create_order, name="paypal_create_order"),
    path("api/paypal/capture-order/", views.paypal_capture_order, name="paypal_capture_order"),
    path("webhooks/paypal/", views.paypal_webhook, name="paypal_webhook"),

    # Stripe
    path("api/stripe/create-checkout-session/", views.stripe_create_checkout_session, name="stripe_checkout"),
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),

    # Paystack
    path("api/paystack/initialize/", views.paystack_initialize, name="paystack_initialize"),
    path("webhooks/paystack/", views.paystack_webhook, name="paystack_webhook"),
]
