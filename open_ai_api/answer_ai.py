import config

from openai import AsyncOpenAI

client_async = AsyncOpenAI(api_key=config.settings.OPENAI_APIKEY)


# ИИ отвечает на вопрос
async def def_openai_api_question(question: str):
    completion = await client_async.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": question}
      ]
    )
    return completion.choices[0].message.content
