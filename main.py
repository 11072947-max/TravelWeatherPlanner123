
import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
API_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_forecast(city, travel_date):
    """Отримує прогноз для міста на обрану дату."""
    if not API_KEY:
        raise RuntimeError(
            "Не знайдено OPENWEATHERMAP_API_KEY у файлі .env"
        )

    response = requests.get(
        API_URL,
        params={
            "q": city,
            "appid": API_KEY,
            "units": "metric",
            "lang": "uk",
        },
        timeout=20,
    )

    if response.status_code == 404:
        raise ValueError(
            "Місто не знайдено. Перевір назву та спробуй ще раз."
        )

    if response.status_code == 401:
        raise ValueError(
            "API-ключ недійсний або ще не активувався."
        )

    response.raise_for_status()
    data = response.json()

    city_name = data["city"]["name"]
    timezone_offset = data["city"]["timezone"]
    city_timezone = timezone(timedelta(seconds=timezone_offset))

    forecasts = []

    for item in data["list"]:
        local_time = datetime.fromtimestamp(
            item["dt"], tz=city_timezone
        )

        if local_time.date() == travel_date:
            forecasts.append((local_time, item))

    if not forecasts:
        available_dates = sorted({
            datetime.fromtimestamp(
                item["dt"], tz=city_timezone
            ).date()
            for item in data["list"]
        })

        first_date = available_dates[0].isoformat()
        last_date = available_dates[-1].isoformat()

        raise ValueError(
            "Прогноз на цю дату недоступний. "
            f"Доступні дати прогнозу: {first_date} — {last_date}."
        )

    # Обираємо запис, найближчий до середини дня.
    local_time, representative = min(
        forecasts,
        key=lambda pair: abs(
            pair[0].hour * 60 + pair[0].minute - 12 * 60
        ),
    )

    temperatures = [
        item["main"]["temp"] for _, item in forecasts
    ]
    max_rain_probability = max(
        item.get("pop", 0) for _, item in forecasts
    )
    max_wind = max(
        item.get("wind", {}).get("speed", 0)
        for _, item in forecasts
    )
    has_rain = any(
        "rain" in item for _, item in forecasts
    )

    return {
        "city": city_name,
        "date": travel_date,
        "time": local_time.strftime("%H:%M"),
        "temperature": representative["main"]["temp"],
        "minimum": min(temperatures),
        "maximum": max(temperatures),
        "description": representative["weather"][0]["description"],
        "rain_probability": round(max_rain_probability * 100),
        "has_rain": has_rain,
        "wind_kmh": max_wind * 3.6,
    }


def make_checklist(weather):
    """Формує список речей для міської подорожі."""
    items = [
        "Документи та квитки",
        "Телефон і зарядний пристрій",
        "Гаманець і банківська картка",
        "Зручне взуття для прогулянок",
        "Пляшка води",
    ]

    temp = weather["temperature"]
    rain_probability = weather["rain_probability"]
    wind = weather["wind_kmh"]

    if temp < 5:
        items.append("Тепла куртка, шарф і рукавички")
    elif temp < 13:
        items.append("Куртка або теплий светр")
    elif temp < 20:
        items.append("Легка куртка або кофта")
    else:
        items.append("Легкий одяг, що добре пропускає повітря")

    if rain_probability >= 40 or weather["has_rain"]:
        items.append("Парасоля або дощовик")

    if temp >= 23:
        items.append("Сонцезахисні окуляри та головний убір")

    if wind >= 25:
        items.append("Вітрозахисний верхній одяг")

    return items


def send_telegram(message):
    """Надсилає повідомлення користувачеві в Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError(
            "Перевір TELEGRAM_BOT_TOKEN і TELEGRAM_CHAT_ID у .env"
        )

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=20,
    )
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError("Telegram не прийняв повідомлення.")


def main():
    print("\n🧳 Travel Weather Planner")
    print("Помічник для міських подорожей\n")

    city = input("Введи назву міста: ").strip()
    date_text = input(
        "Введи дату подорожі (РРРР-ММ-ДД): "
    ).strip()

    if not city:
        print("Помилка: введи назву міста.")
        return

    try:
        travel_date = datetime.strptime(
            date_text, "%Y-%m-%d"
        ).date()

        if travel_date < datetime.now().date():
            print("Помилка: дата подорожі не може бути в минулому.")
            return

        weather = get_forecast(city, travel_date)
        checklist = make_checklist(weather)

        print("\n" + "=" * 42)
        print("🌍 ПРОГНОЗ ДЛЯ ПОДОРОЖІ")
        print("=" * 42)
        print(f"Місто: {weather['city']}")
        print(f"Дата: {weather['date']}")
        print(f"Час прогнозу: близько {weather['time']}")
        print(f"Погода: {weather['description']}")
        print(
            f"Температура: {weather['temperature']:.1f} °C"
        )
        print(
            f"Діапазон за доступними прогнозами: "
            f"{weather['minimum']:.1f} — "
            f"{weather['maximum']:.1f} °C"
        )
        print(f"Імовірність опадів: {weather['rain_probability']}%")
        print(f"Максимальний вітер: {weather['wind_kmh']:.1f} км/год")

        print("\n📝 ЧЕКЛІСТ РЕЧЕЙ")
        for item in checklist:
            print(f"☐ {item}")

        telegram_message = (
            f"🧳 Travel Weather Planner\n"
            f"📍 Місто: {weather['city']}\n"
            f"📅 Дата: {weather['date']}\n\n"
            f"🌤 Погода: {weather['description']}\n"
            f"🌡 Температура: {weather['temperature']:.1f} °C\n"
            f"🌧 Імовірність опадів: "
            f"{weather['rain_probability']}%\n"
            f"💨 Вітер: {weather['wind_kmh']:.1f} км/год\n\n"
            f"📝 ЧЕКЛІСТ РЕЧЕЙ:\n"
            + "\n".join(f"☐ {item}" for item in checklist)
            + "\n\nЩасливої подорожі! ✈️"
        )

        send_telegram(telegram_message)
        print("Повідомлення успішно надіслано в Telegram!")

        print("\nЩасливої подорожі! ✈️")

    except ValueError as error:
        print(f"\nПомилка: {error}")
    except requests.RequestException as error:
        print(f"\nПомилка під час запиту до погодного сервісу: {error}")
    except (KeyError, IndexError, TypeError) as error:
        print(f"\nНе вдалося обробити відповідь API: {error}")
    except RuntimeError as error:
        print(f"\nПомилка налаштування: {error}")


if __name__ == "__main__":
    main()
