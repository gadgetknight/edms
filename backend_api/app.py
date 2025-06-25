# backend_api/app.py

"""
EDMS Centralized Backend API for Stripe Integration
Version: 1.0.3
Purpose: A Flask microservice to securely handle Stripe API calls (e.g., creating
         Payment Links) and receive Stripe webhook events for payment confirmations.
         Designed to be hosted centrally by the developer, abstracting complexity
         from the end-user desktop application.
Last Updated: June 25, 2025
Author: Gemini

Changelog:
- v1.0.3 (2025-06-25):
    - **BUG FIX**: Explicitly set `stripe.api_version` in `backend_api/app.py` to match the webhook endpoint's API version.
      This resolves the `Invalid signature: No signatures found matching the expected signature for payload` error
      even when the secret is correct, due to potential API version mismatches.
- v1.0.2 (2025-06-25):
    - **BUG FIX**: Added missing `from typing import Dict, Optional` import statement to resolve `NameError` for `Dict` and `Optional` type hints.
- v1.0.1 (2025-06-25):
    - **BUG FIX**: Added missing `import sys` statement to resolve `NameError` in logging configuration.
- v1.0.0 (2025-06-25):
    - Initial creation of the centralized Flask backend application.
    - Implemented `/create-payment-link` endpoint:
        - Receives invoice details and *doctor's Stripe Secret Key* from desktop app.
        - Uses the provided key to create Stripe Payment Links.
        - Embeds `internal_invoice_id` and doctor's identifier as metadata.
    - Implemented `/stripe-webhook` endpoint:
        - Receives all Stripe webhook events (e.g., `checkout.session.completed`).
        - Performs Stripe signature verification for security.
        - Processes successful payment events (`checkout.session.completed`) to log payment.
    - Includes basic logging and database (SQLite) setup for webhook event logging.
    - This replaces the previous local_webhook_listener.py and direct Stripe calls from desktop.
"""

import os
import json
import logging
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from flask import Flask, request, jsonify, abort
import stripe
import sqlite3

from backend_api.config import BackendConfig

# --- Logging Setup for Backend API ---
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(_LOG_DIR, "backend_api.log"), mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(BackendConfig)

# --- IMPORTANT: Set Stripe API Version for Webhook Verification ---
# This must match the API Version configured for your webhook endpoint in the Stripe Dashboard.
# Find this version in Stripe Dashboard -> Developers -> Webhooks -> [Your Endpoint] -> API Version.
stripe.api_version = (
    "2024-06-20"  # <--- REPLACE WITH YOUR ACTUAL API VERSION FROM STRIPE!
)
# --- END IMPORTANT ---


# --- Backend's Internal Database (for webhook logging/status) ---
def init_db():
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stripe_event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            internal_invoice_id INTEGER,
            doctor_identifier TEXT
        )
    """
    )
    conn.commit()
    conn.close()
    logger.info(f"Backend database initialized at {app.config['DATABASE_PATH']}")


with app.app_context():
    init_db()


def log_webhook_event(
    stripe_event_id: str,
    event_type: str,
    payload: Dict,
    status: str,
    internal_invoice_id: Optional[int] = None,
    doctor_identifier: Optional[str] = None,
):
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO webhook_events (stripe_event_id, event_type, payload_json, status, internal_invoice_id, doctor_identifier)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                stripe_event_id,
                event_type,
                json.dumps(payload),
                status,
                internal_invoice_id,
                doctor_identifier,
            ),
        )
        conn.commit()
        logger.info(
            f"Logged webhook event {stripe_event_id} ({event_type}) with status: {status}"
        )
    except sqlite3.IntegrityError:
        logger.warning(
            f"Webhook event {stripe_event_id} already logged. Skipping duplicate entry."
        )
    except Exception as e:
        logger.error(
            f"Failed to log webhook event {stripe_event_id}: {e}", exc_info=True
        )
    finally:
        conn.close()


# --- API Endpoints ---


@app.route("/create-payment-link", methods=["POST"])
def create_payment_link():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Required parameters from the desktop app
    doctor_stripe_secret_key = data.get("stripe_secret_key")
    invoice_id = data.get("internal_invoice_id")
    amount_decimal = data.get("amount")
    description = data.get("description")
    customer_email = data.get("customer_email")
    doctor_identifier = data.get("doctor_identifier")

    if not all(
        [
            doctor_stripe_secret_key,
            invoice_id,
            amount_decimal,
            description,
            doctor_identifier,
        ]
    ):
        return (
            jsonify(
                {
                    "error": "Missing required parameters (stripe_secret_key, internal_invoice_id, amount, description, doctor_identifier)"
                }
            ),
            400,
        )

    try:
        amount = Decimal(str(amount_decimal))
        if amount <= 0:
            return (
                jsonify({"error": "Payment link amount must be greater than zero."}),
                400,
            )
        stripe_amount = int(amount * 100)

        # Set the Stripe API key for this specific request based on the doctor's key
        stripe.api_key = doctor_stripe_secret_key

        # --- Re-use logic for generic invoice product on the central API ---
        if not app.config.get("GENERIC_INVOICE_PRODUCT_ID"):
            products = stripe.Product.list(limit=100)
            generic_product = None
            for product in products.data:
                if "Invoice Payment" in product.name:
                    generic_product = product
                    break

            if not generic_product:
                logger.info(
                    "Generic 'Invoice Payment' product not found in Stripe. Creating it."
                )
                generic_product = stripe.Product.create(
                    name="Invoice Payment",
                    type="service",
                    description="Generic product for EDMS Veterinary System invoice payments.",
                    metadata={
                        "source_app": "EDMS_Backend",
                        "type": "generic_invoice_product",
                    },
                )
            app.config["GENERIC_INVOICE_PRODUCT_ID"] = generic_product.id
            logger.info(
                f"Using Stripe Product ID: {app.config['GENERIC_INVOICE_PRODUCT_ID']} for invoice payments."
            )

        generic_product_id = app.config["GENERIC_INVOICE_PRODUCT_ID"]
        if not generic_product_id:
            return (
                jsonify(
                    {"error": "Failed to get/create generic Stripe invoice product."}
                ),
                500,
            )

        # Create a Price for the generic Product
        price = stripe.Price.create(
            unit_amount=stripe_amount,
            currency="usd",
            product=generic_product_id,
        )

        payment_link_params = {
            "line_items": [
                {
                    "price": price.id,
                    "quantity": 1,
                },
            ],
            "metadata": {
                "internal_invoice_id": str(invoice_id),
                "doctor_identifier": doctor_identifier,
                "source_app": "EDMS_Backend_API",
            },
            "customer_creation": "always",
        }

        payment_link = stripe.PaymentLink.create(**payment_link_params)

        logger.info(
            f"Stripe Payment Link created for Invoice {invoice_id} by {doctor_identifier}: {payment_link.url}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Stripe Payment Link created successfully.",
                    "payment_link_url": payment_link.url,
                }
            ),
            200,
        )

    except stripe.error.StripeError as e:
        logger.error(
            f"Stripe API Error creating payment link for Invoice {invoice_id} (Doctor: {doctor_identifier}): {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {"success": False, "message": f"Stripe API Error: {e.user_message}"}
            ),
            400,
        )
    except ValueError as e:
        logger.error(
            f"Validation error for payment link creation for Invoice {invoice_id} (Doctor: {doctor_identifier}): {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Validation Error: {str(e)}",
                    "error_details": str(e),
                }
            ),
            400,
        )
    except Exception as e:
        logger.error(
            f"Unexpected error creating payment link for Invoice {invoice_id} (Doctor: {doctor_identifier}): {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"An unexpected error occurred: {str(e)}",
                    "error_details": str(e),
                }
            ),
            500,
        )


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("stripe-signature")
    event = None

    WEBHOOK_ENDPOINT_SECRET = os.environ.get(
        "STRIPE_WEBHOOK_ENDPOINT_SECRET",
        "whsec_cwRR66sGhaSEJ8AQpoZXUfI1nf8Zm0YZ",
    )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_ENDPOINT_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        log_webhook_event("N/A", "N/A", json.loads(payload), "failed_invalid_payload")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        log_webhook_event(
            "N/A", "N/A", json.loads(payload), "failed_signature_verification"
        )
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        log_webhook_event("N/A", "N/A", json.loads(payload), "failed_unknown_error")
        return jsonify({"error": "Webhook processing error"}), 500

    event_id = event["id"]
    event_type = event["type"]
    internal_invoice_id = (
        event["data"]["object"].get("metadata", {}).get("internal_invoice_id")
    )
    doctor_identifier = (
        event["data"]["object"].get("metadata", {}).get("doctor_identifier")
    )

    # Handle the event
    if event_type == "checkout.session.completed":
        session_data = event["data"]["object"]
        logger.info(
            f"Received checkout.session.completed event for session ID: {session_data['id']}"
        )

        if internal_invoice_id and session_data.get("payment_status") == "paid":
            logger.info(
                f"Payment confirmed for internal invoice ID: {internal_invoice_id} (Doctor: {doctor_identifier}). Session ID: {session_data['id']}"
            )
            log_webhook_event(
                event_id,
                event_type,
                event,
                "processed_paid",
                internal_invoice_id,
                doctor_identifier,
            )
        else:
            logger.warning(
                f"checkout.session.completed received but payment_status not 'paid' or missing internal_invoice_id. Session ID: {session_data['id']}"
            )
            log_webhook_event(
                event_id,
                event_type,
                event,
                "processed_not_paid_or_missing_id",
                internal_invoice_id,
                doctor_identifier,
            )

    elif event_type == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        logger.info(
            f"PaymentIntent {payment_intent['id']} succeeded (Doctor: {doctor_identifier})."
        )
        log_webhook_event(
            event_id,
            event_type,
            event,
            "processed_succeeded",
            internal_invoice_id,
            doctor_identifier,
        )
    elif event_type == "charge.refunded":
        charge = event["data"]["object"]
        logger.info(f"Charge {charge['id']} refunded (Doctor: {doctor_identifier}).")
        log_webhook_event(
            event_id,
            event_type,
            event,
            "processed_refunded",
            internal_invoice_id,
            doctor_identifier,
        )
    else:
        logger.info(f"Unhandled event type: {event_type}. Event ID: {event_id}")
        log_webhook_event(
            event_id,
            event_type,
            event,
            "unhandled_type",
            internal_invoice_id,
            doctor_identifier,
        )

    return jsonify({"status": "success"}), 200


@app.route(
    "/get-payment-status/<string:doctor_identifier>/<int:internal_invoice_id>",
    methods=["GET"],
)
def get_payment_status(doctor_identifier: str, internal_invoice_id: int):
    conn = sqlite3.connect(app.config["DATABASE_PATH"])
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) FROM webhook_events
            WHERE internal_invoice_id = ? AND doctor_identifier = ? AND event_type = 'checkout.session.completed' AND status = 'processed_paid'
        """,
            (internal_invoice_id, doctor_identifier),
        )

        is_paid = cursor.fetchone()[0] > 0

        return (
            jsonify(
                {
                    "invoice_id": internal_invoice_id,
                    "is_paid": is_paid,
                    "doctor_identifier": doctor_identifier,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(
            f"Error checking payment status for invoice {internal_invoice_id} (Doctor: {doctor_identifier}): {e}",
            exc_info=True,
        )
        return jsonify({"error": "Failed to retrieve payment status."}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("Starting EDMS Centralized Backend API...")
    logger.info(
        "Ensure you replace 'whsec_YOUR_STRIPE_WEBHOOK_SECRET_FOR_THIS_ENDPOINT' with your actual webhook secret!"
    )
    app.run(debug=True, port=5000)
