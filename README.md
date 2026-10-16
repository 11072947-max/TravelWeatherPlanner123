
# Travel Weather Planner

Travel Weather Planner — помічник для планування міських подорожей,
який отримує прогноз погоди та формує персональний чекліст речей.

## Можливості

- Введення міста та дати подорожі.
- Отримання погодних даних через OpenWeatherMap API.
- Аналіз температури, опадів і вітру.
- Формування рекомендацій щодо одягу та необхідних речей.
- Надсилання прогнозу й чекліста через Telegram Bot API.

## Технології

- Python
- Requests
- python-dotenv
- OpenWeatherMap API
- Telegram Bot API

## Встановлення

1. Встановіть Python.
2. Встановіть залежності:

   ```bash
   py -m pip install -r requirements.txt
   ```

3. Створіть файл `.env` та додайте API-ключі:

   ```dotenv
   OPENWEATHERMAP_API_KEY=your_openweathermap_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

4. Запустіть програму:

   ```bash
   py main.py
   ```

## Безпека

Не публікуйте `.env` та не передавайте API-ключі іншим людям.
Файл `.env` має бути виключений із Git через `.gitignore`.
