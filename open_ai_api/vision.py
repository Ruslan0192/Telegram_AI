import base64

from openai import AsyncOpenAI

from config import settings

client_async = AsyncOpenAI(api_key=settings.OPENAI_APIKEY)


async def def_openai_vision(image_path: str):
    # Function to encode the image
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    completion = await client_async.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Какое настроение, чувства, эмоции у человека на фото?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
    )
    return completion.choices[0].message.content
