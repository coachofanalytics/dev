from google import genai
from decouple import config

client = genai.Client(api_key=config('GEMINI_API_KEY'))

print("Available models:")
for m in client.models.list():
    print(m.name)