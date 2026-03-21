from google import genai
from django.conf import settings
import time


def generate_article_summary(content):
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = (
            f"Write a detailed 3-sentence summary of the following news article. "
            f"Make it professional and ensuring it ends with a complete sentence. "
            f"Article content: {content}"
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-1.5-flash-8b',
                    contents=prompt,
                )
                if response.text:
                    return response.text.strip()
                else:
                    return "Summary currently unavailable. Visit our site for the full story."

            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg:
                    wait_time = (attempt + 1) * 15  # 15s, 30s, 45s
                    print(f"Rate limited. Waiting {wait_time}s — retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    raise e

        return "Summary currently unavailable. Visit our site for the full story."

    except Exception as e:
        print(f"AI Error: {e}")
        return "New Update available! Read the full details on DC48K"