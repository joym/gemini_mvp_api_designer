from google import genai

client = genai.Client()
for m in client.models.list():
    print(getattr(m, "name", m))