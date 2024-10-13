import stripe
from app.config import STRIPE_API_KEY

stripe.api_key = STRIPE_API_KEY

class StripeService:
    @staticmethod
    def create_payment_intent(amount: float, currency: str):
        """
        Creates a Stripe payment intent.

         amount: Amount in float (will be converted to cents).
         currency: Currency code (e.g., 'usd', 'eur').
        :return: Stripe PaymentIntent object.
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in cents
                currency=currency
            )
            return intent
        except Exception as e:
            raise Exception(f"Error creating payment intent: {str(e)}")

    @staticmethod
    def confirm_payment_intent(intent_id: str):
        """
        Confirms a Stripe payment intent.

        :intent_id: The ID of the Stripe payment intent to confirm.
        :return: Confirmed PaymentIntent object.
        """
        try:
            intent = stripe.PaymentIntent.confirm(intent_id)
            return intent
        except Exception as e:
            raise Exception(f"Error confirming payment intent: {str(e)}")

"""Both methods in this class are marked as @staticmethod, meaning they don't 
depend on the state of the class instance and can be called directly 
via the class without needing to instantiate it."""