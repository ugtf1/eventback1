import json
import os
import uuid
from datetime import datetime
from decimal import Decimal

import requests
import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Hall, Booking, Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
    halls = Hall.objects.all().order_by("id")[:8]
    return render(request, "rentals/home.html", {
        "halls": halls,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
        "PAYPAL_CLIENT_ID": settings.PAYPAL["CLIENT_ID"],
        "PAYPAL_CURRENCY": settings.PAYPAL["CURRENCY"],
        "PAYSTACK_PUBLIC_KEY": settings.PAYSTACK_PUBLIC_KEY,
        "SITE_URL": settings.SITE_URL,
    })

def halls_api(request):
    data = [{
        "id": h.id,
        "name": h.name,
        "description": h.description,
        "capacity": h.capacity,
        "price_per_day": str(h.price_per_day),
        "image_url": h.image_url,
    } for h in Hall.objects.all()]
    return JsonResponse({"halls": data})

def _dates_overlap(a_start, a_end, b_start, b_end):
    return a_start <= b_end and b_start <= a_end

def check_availability(request):
    try:
        hall_id = int(request.GET.get("hall_id"))
        start_date = datetime.strptime(request.GET.get("start_date"), "%Y-%m-%d").date()
        end_date = datetime.strptime(request.GET.get("end_date"), "%Y-%m-%d").date()
    except Exception:
        return HttpResponseBadRequest("Invalid input")

    hall = get_object_or_404(Hall, pk=hall_id)
    conflicts = Booking.objects.filter(hall=hall, status__in=["pending", "confirmed"])
    available = all(not _dates_overlap(b.start_date, b.end_date, start_date, end_date) for b in conflicts)
    return JsonResponse({"available": available})

def create_booking(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    payload = json.loads(request.body.decode())
    try:
        hall = Hall.objects.get(pk=payload["hall_id"])
        start_date = datetime.strptime(payload["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(payload["end_date"], "%Y-%m-%d").date()
        customer_name = payload["customer_name"]
        customer_email = payload["customer_email"]
        days = (end_date - start_date).days + 1
        total = hall.price_per_day * days
    except Exception:
        return HttpResponseBadRequest("Invalid data")

    # Availability simple check
    conflicts = Booking.objects.filter(hall=hall, status__in=["pending", "confirmed"])
    for b in conflicts:
        if _dates_overlap(b.start_date, b.end_date, start_date, end_date):
            return JsonResponse({"error": "Hall not available for selected dates"}, status=409)

    booking = Booking.objects.create(
        hall=hall,
        customer_name=customer_name,
        customer_email=customer_email,
        start_date=start_date,
        end_date=end_date,
        total_amount=total,
        status="pending",
    )
    return JsonResponse({"booking_id": booking.id, "total_amount": str(total)})

# ---------- PayPal ----------
def _paypal_access_token():
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token" if settings.PAYPAL["MODE"] == "sandbox" else "https://api-m.paypal.com/v1/oauth2/token"
    resp = requests.post(url, data={"grant_type": "client_credentials"}, auth=(settings.PAYPAL["CLIENT_ID"], settings.PAYPAL["CLIENT_SECRET"]))
    resp.raise_for_status()
    return resp.json()["access_token"]

def paypal_create_order(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    payload = json.loads(request.body.decode())
    booking = get_object_or_404(Booking, pk=payload.get("booking_id"))
    access_token = _paypal_access_token()
    base = "https://api-m.sandbox.paypal.com" if settings.PAYPAL["MODE"] == "sandbox" else "https://api-m.paypal.com"
    order = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": str(booking.id),
            "amount": {"currency_code": settings.PAYPAL["CURRENCY"], "value": str(booking.total_amount)}
        }],
    }
    r = requests.post(f"{base}/v2/checkout/orders", json=order, headers={"Authorization": f"Bearer {access_token}"})
    data = r.json()
    Payment.objects.update_or_create(
        booking=booking,
        defaults={"provider": "paypal", "provider_ref": data.get("id", ""), "amount": booking.total_amount, "raw_response": data}
    )
    return JsonResponse(data)

def paypal_capture_order(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    payload = json.loads(request.body.decode())
    order_id = payload.get("orderID")
    access_token = _paypal_access_token()
    base = "https://api-m.sandbox.paypal.com" if settings.PAYPAL["MODE"] == "sandbox" else "https://api-m.paypal.com"
    r = requests.post(f"{base}/v2/checkout/orders/{order_id}/capture", headers={"Authorization": f"Bearer {access_token}"})
    data = r.json()
    # Update payment/booking
    try:
        ref = data["id"]
        purchase = data["purchase_units"][0]
        booking_id = int(purchase["reference_id"])
        booking = Booking.objects.get(id=booking_id)
        payment = booking.payment
        payment.status = "succeeded"
        payment.raw_response = data
        payment.save()
        booking.status = "confirmed"
        booking.save()
    except Exception:
        pass
    return JsonResponse(data)

@csrf_exempt
def paypal_webhook(request):
    # For production: validate transmission (PayPal webhook signature).
    return HttpResponse(status=200)

# ---------- Stripe ----------
def stripe_create_checkout_session(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    payload = json.loads(request.body.decode())
    booking = get_object_or_404(Booking, pk=payload.get("booking_id"))
    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=f"{settings.SITE_URL}?success=true&booking_id={booking.id}",
        cancel_url=f"{settings.SITE_URL}?cancelled=true&booking_id={booking.id}",
        customer_email=booking.customer_email,
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"Hall: {booking.hall.name}"},
                "unit_amount": int(Decimal(booking.total_amount) * 100),
            },
            "quantity": 1,
        }],
        metadata={"booking_id": str(booking.id)},
    )
    Payment.objects.update_or_create(
        booking=booking,
        defaults={"provider": "stripe", "provider_ref": session.id, "amount": booking.total_amount, "raw_response": {"session": session.id}}
    )
    return JsonResponse({"id": session.id, "url": session.url})

@csrf_exempt
def stripe_webhook(request):
    # For production: verify signature with STRIPE_WEBHOOK_SECRET
    event = json.loads(request.body.decode())
    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        booking_id = session.get("metadata", {}).get("booking_id")
        if booking_id:
            try:
                booking = Booking.objects.get(id=int(booking_id))
                booking.status = "confirmed"
                booking.save()
                p = booking.payment
                p.status = "succeeded"
                p.save()
            except Exception:
                pass
    return HttpResponse(status=200)

# ---------- Paystack ----------
def paystack_initialize(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    payload = json.loads(request.body.decode())
    booking = get_object_or_404(Booking, pk=payload.get("booking_id"))
    ref = f"PSK_{uuid.uuid4().hex[:18]}"
    Payment.objects.update_or_create(
        booking=booking,
        defaults={"provider": "paystack", "provider_ref": ref, "amount": booking.total_amount}
    )
    return JsonResponse({
        "reference": ref,
        "email": booking.customer_email,
        "amount_kobo": int(Decimal(booking.total_amount) * 100),
        "public_key": settings.PAYSTACK_PUBLIC_KEY
    })

@csrf_exempt
def paystack_webhook(request):
    # For production: verify X-Paystack-Signature using PAYSTACK_SECRET_KEY
    event = json.loads(request.body.decode())
    if event.get("event") == "charge.success":
        data = event.get("data", {})
        ref = data.get("reference")
        try:
            payment = Payment.objects.get(provider="paystack", provider_ref=ref)
            payment.status = "succeeded"
            payment.raw_response = event
            payment.save()
            booking = payment.booking
            booking.status = "confirmed"
            booking.save()
        except Exception:
            pass
    return HttpResponse(status=200)
