import google.generativeai as genai
from django.conf import settings


def generate_article_summary(content):
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

    prompt = (
        f"Write a detailed 3-sentence summary of the following news article. "
        f"Make it professional and ensuring it ends with a complete sentence. "
        f" Article content:{content}"
    )

    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text.strip()
        else:
            return "Summary currently unavailable. Visit our site for the full story. "
    except Exception as e:
        print(f"AI Error: {e}")
        return "New Update available! Read the full details on DC48K"
