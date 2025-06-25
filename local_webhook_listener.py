# local_webhook_listener.py

"""
EDSI Veterinary Management System - Local Stripe Webhook Listener
Version: 1.0.0
Purpose: A lightweight Flask application to listen for Stripe webhook events
         (e.g., successful payments) and update the local database.
Last Updated: June 23, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-06-23):
    - Initial creation of the Flask application for Stripe webhook reception.
    - Implemented `/stripe-webhook` endpoint to handle POST requests.
    - Includes Stripe webhook signature verification for security.
    - Processes `checkout.session.completed` events to update invoice status in the local database.
    - Configured to run on a local port, intended for use with tunneling services like ngrok.
"""

import sys
import os
import json
import logging
from decimal import Decimal

# Add project root to sys.path to allow imports from config and controllers
_PROJECT_ROOT_FOR_PATHING = os.path.abspath(os.path.dirname(__file__))
if _PROJECT_ROOT_FOR_PATHING not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT_FOR_PATHING)

# Configure basic logging for the listener script
log_file_path = os.path.join(_PROJECT_ROOT_FOR_PATHING, "logs", "webhook_listener.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode="a"),  # Append to log file
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

try:
    from flask import Flask, request, jsonify, abort
    import stripe
    from config.database_config import db_manager
    from controllers.financial_controller import FinancialController
except ImportError as e:
    logger.critical(f"Failed to import necessary modules: {e}")
    logger.critical(
        "Please ensure 'flask' and 'stripe' are installed: pip install Flask stripe"
    )
    sys.exit(1)

app = Flask(__name__)

# --- IMPORTANT CONFIGURATION ---
# Replace with your actual Stripe Webhook Secret from your Stripe Dashboard.
# You can find this in Stripe Dashboard -> Developers -> Webhooks -> Add endpoint -> Reveal secret.
# This secret is used to verify that webhooks actually come from Stripe.
# NEVER hardcode this in a production application directly if distributing the source.
# For this local listener, it's acceptable for demonstration, but secure it in a real deployment.
WEBHOOK_SECRET = "whsec_YOUR_STRIPE_WEBHOOK_SECRET"  # REPLACE THIS!
# --- END IMPORTANT CONFIGURATION ---


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("stripe-signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {e}")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {e}")
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return jsonify({"error": "Webhook processing error"}), 500

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info(
            f"Received checkout.session.completed event for session ID: {session['id']}"
        )

        # Extract metadata
        internal_invoice_id = session.get("metadata", {}).get("internal_invoice_id")
        payment_status = session.get("payment_status")
        amount_total = session.get("amount_total")  # Amount in cents

        if internal_invoice_id and payment_status == "paid":
            logger.info(
                f"Processing payment for internal invoice ID: {internal_invoice_id}"
            )
            try:
                # Initialize FinancialController to update the invoice
                financial_controller = FinancialController()

                # Fetch the invoice from your local DB
                invoice = financial_controller.get_invoice_by_id(
                    int(internal_invoice_id)
                )

                if invoice:
                    if invoice.status != "Paid" and invoice.balance_due > 0:
                        # Convert amount from Stripe's cents to your Decimal format
                        amount_received = Decimal(amount_total) / 100

                        # Record the payment. We can create a "Stripe" payment method.
                        payment_data = {
                            "invoice_id": invoice.invoice_id,
                            "amount": amount_received,
                            "payment_date": datetime.now().date(),  # Current date
                            "payment_method": "Stripe (Online)",
                            "reference_number": session[
                                "id"
                            ],  # Use Stripe Session ID as reference
                            "notes": f"Online payment via Stripe Session {session['id']}",
                            "user_id": "STRIPE_WEBHOOK",  # System user for webhook payments
                        }

                        success, msg = financial_controller.record_payment(payment_data)
                        if success:
                            logger.info(
                                f"Successfully marked invoice {internal_invoice_id} as paid. Payment: ${amount_received:.2f}"
                            )
                        else:
                            logger.error(
                                f"Failed to mark invoice {internal_invoice_id} as paid: {msg}"
                            )
                    else:
                        logger.info(
                            f"Invoice {internal_invoice_id} is already paid or has no balance due. Skipping update."
                        )
                else:
                    logger.warning(
                        f"Internal invoice ID {internal_invoice_id} not found in local DB."
                    )
            except Exception as e:
                logger.error(
                    f"Error updating local invoice {internal_invoice_id}: {e}",
                    exc_info=True,
                )
        else:
            logger.warning(
                f"Received checkout.session.completed but payment_status is not 'paid' or missing internal_invoice_id. Session ID: {session['id']}"
            )

    # Add other event types you want to handle (e.g., 'payment_intent.succeeded', 'charge.refunded')
    elif event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        logger.info(f"PaymentIntent {payment_intent['id']} succeeded.")
        # Further processing can go here if direct PaymentIntents are used, not Payment Links.

    else:
        logger.info(f"Unhandled event type: {event['type']}")

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    logger.info("Starting local Stripe Webhook Listener...")
    logger.info(
        "This listener is intended for development and local testing with tools like ngrok."
    )
    logger.info(f"Listening on http://127.0.0.1:5000/stripe-webhook")
    logger.info(f"Make sure to replace 'whsec_cwRR66sGhaSEJ8AQpoZXUfI1nf8Zm0YZ")

    # Run the Flask app
    # In a production environment, you would use a WSGI server like Gunicorn
    app.run(port=5000)
