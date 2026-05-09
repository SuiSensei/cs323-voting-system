import os
import time
import uuid
import random
import socket
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/vote")
EDGE_ID = f"edge-{socket.gethostname()}-{random.randint(1000, 9999)}"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
MIN_DELAY = float(os.getenv("MIN_DELAY", 1))
MAX_DELAY = float(os.getenv("MAX_DELAY", 3))

