# Disable ChromaDB telemetry globally
import os
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"

# Import the app
from .main import app

