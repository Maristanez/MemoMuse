import os, asyncio, ssl
ssl.create_default_context = ssl._create_unverified_context
from dotenv import load_dotenv
load_dotenv()
from services.lyria_module import generate_instrumental

print("Testing lyria...")
generate_instrumental("A smooth jazz track", 100, "temp/test_lyria.wav")
print("Finished.")
