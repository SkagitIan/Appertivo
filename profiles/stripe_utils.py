import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_API_KEY

def create_customer(email):
    customer = stripe.Customer.create(email=email)
    return customer.id

def create_checkout_session(customer_id, success_url, cancel_url, price_id):
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session
