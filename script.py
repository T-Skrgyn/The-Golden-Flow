import asyncio
import aiohttp
import json
import os
import ssl
import certifi
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("Weather Key:", WEATHER_API_KEY)
print("OpenAI Key:", OPENAI_API_KEY)

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# SSL fix
ssl_context = ssl.create_default_context(cafile=certifi.where())

# NVIDIA client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=OPENAI_API_KEY
)

# Load orders
with open("orders.json", "r") as f:
    orders = json.load(f)


# 🔹 WEATHER
async def fetch_weather(session, city):
    try:
        params = {"q": city, "appid": WEATHER_API_KEY}

        async with session.get(WEATHER_URL, params=params) as res:
            if res.status != 200:
                print("Weather Error:", city)
                return None

            data = await res.json()
            print("Weather:", city, data["weather"][0])
            return data["weather"][0]

    except Exception as e:
        print("Weather Exception:", city, e)
        return None


# 🔹 AI (STREAMING GEMMA)
async def generate_ai_message(customer, city, weather):
    try:
        prompt = f"""
Write ONE short polite apology sentence.

Customer: {customer}
City: {city}
Weather: {weather["description"]}

Return only one sentence.
"""

        def call_ai():
            completion = client.chat.completions.create(
                model="google/gemma-3-1b-it",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                top_p=0.7,
                max_tokens=100,
                stream=True
            )

            full_text = ""

            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    full_text += chunk.choices[0].delta.content

            return full_text.strip()

        result = await asyncio.to_thread(call_ai)

        # Clean result
        if result:
            # Remove extra lines
            result = result.replace("\n", " ").strip()

            # Keep only first sentence
            if "." in result:
                result = result.split(".")[0] + "."

            return result

        # fallback
        return f"Hi {customer}, your order to {city} is delayed due to {weather['description']}. We appreciate your patience."

    except Exception as e:
        print("AI error:", e)
        return f"Hi {customer}, your order to {city} is delayed due to {weather['description']}. We appreciate your patience."


# 🔹 MAIN
async def process_orders():
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:

        weather_tasks = [fetch_weather(session, o["city"]) for o in orders]
        weather_results = await asyncio.gather(*weather_tasks)

        ai_tasks = []
        indexes = []

        for i, (order, weather) in enumerate(zip(orders, weather_results)):

            if weather is None:
                continue

            if weather["main"] in ["Rain", "Snow", "Extreme"]:
                order["status"] = "Delayed"
                indexes.append(i)

                ai_tasks.append(
                    generate_ai_message(
                        order["customer"],
                        order["city"],
                        weather
                    )
                )

        results = await asyncio.gather(*ai_tasks)

        for idx, msg in zip(indexes, results):
            orders[idx]["message"] = msg

    with open("orders.json", "w") as f:
        json.dump(orders, f, indent=2)

    print("FINAL OUTPUT SAVED")


# RUN
if __name__ == "__main__":
    asyncio.run(process_orders())