from groq import Groq
from django.conf import settings

def generate_article_summary(content):
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)

        response = client.chat.completions.create(
            model="moonshotai/kimi-k2-instruct",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write a detailed 3-sentence summary of the following "
                        f"news article. Make it professional and ensure it ends "
                        f"with a complete sentence. "
                        f"Article content: {content}"
                    )
                }
            ],
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"AI Error: {e}")
        return "Summary currently unavailable. Visit our site for the full story."
