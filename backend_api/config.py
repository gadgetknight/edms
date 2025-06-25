# backend_api/config.py

"""
EDMS Backend API Configuration
Version: 1.0.0
Purpose: Centralized configuration for the EDMS backend microservice.
Last Updated: June 24, 2025
Author: Gemini

Changelog:
- v1.0.0 (2025-06-24):
    - Initial creation of the backend configuration file.
    - Defines a placeholder for a Flask secret key (if session management or API security is needed).
    - Defines a placeholder for the backend's own SQLite database path (for internal logging/state).
"""

import os


class BackendConfig:
    # Flask secret key for session management or API security
    # IMPORTANT: Change this to a strong, random value in production!
    SECRET_KEY = os.environ.get(
        "FLASK_SECRET_KEY", "your_super_secret_flask_key_CHANGE_THIS"
    )

    # Path for the backend's internal SQLite database (e.g., for webhook logs)
    # This database is separate from the desktop application's database.
    # It will be created in the 'backend_api/data' directory.
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    DATABASE_PATH = os.path.join(DATA_DIR, "backend_api.db")

    # Ensure the data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # --- Other potential future configurations ---
    # API_KEYS = {
    #     "doctor1_api_key": "xyzabc123",
    #     "doctor2_api_key": "defghi456",
    # }
    # STRIPE_PUBLISHABLE_KEY = "pk_live_..." # If your API itself has a Stripe key for a central purpose
    # STRIPE_SECRET_KEY = "sk_live_..." # If your API itself has a Stripe key for a central purpose
    # STRIPE_WEBHOOK_SECRET = "whsec_..." # If your API uses one central webhook secret for all doctors
