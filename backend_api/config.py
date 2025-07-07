# backend_api/config.py

"""
EDMS Centralized Backend API Configuration
Version: 1.0.1
Purpose: Stores configuration settings for the backend Flask application,
         including paths and Stripe API keys from environment variables.
Last Updated: July 1, 2025
Author: Gemini

Changelog:
- v1.0.1 (2025-07-01):
    - Added `STRIPE_SUCCESS_REDIRECT_URL` constant to `BackendConfig` class,
      providing a configurable URL for post-payment redirection.
- v1.0.0 (2025-06-25):
    - Initial creation of backend configuration.
"""

import os


class BackendConfig:
    # Database for webhook logging (relative path within the backend API's directory)
    DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "backend_api.db"
    )

    # Stripe API Key (for the developer's central account, NOT the doctor's key)
    # This key is used for operations like creating generic products if needed,
    # or for webhook verification when the WEBHOOK_ENDPOINT_SECRET isn't sufficient for context.
    # For create-payment-link, the doctor's key is passed dynamically.
    STRIPE_SECRET_KEY = os.environ.get(
        "STRIPE_SECRET_KEY", "sk_test_YOUR_DEVELOPER_STRIPE_SECRET_KEY"
    )

    # Webhook Endpoint Secret (from Stripe Dashboard -> Developers -> Webhooks)
    # Used to verify incoming Stripe webhook signatures.
    STRIPE_WEBHOOK_ENDPOINT_SECRET = os.environ.get(
        "STRIPE_WEBHOOK_ENDPOINT_SECRET", "whsec_cwRR66sGhaSEJ8AQpoZXUfI1nf8Zm0YZ"
    )

    # URL where Stripe should redirect the user after a successful payment link completion
    # This should be a publicly accessible URL on your domain (e.g., a "Thank You" page)
    # You will replace this with your actual production URL.
    STRIPE_SUCCESS_REDIRECT_URL = os.environ.get(
        "STRIPE_SUCCESS_REDIRECT_URL", "https://yourdomain.com/payment-success"
    )  # NEW

    # Add any other configuration variables here (e.g., for logging, other services)
