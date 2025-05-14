import telebot
from telebot import types
import time
import os
import google.generativeai as genai
import requests
import json # Для отладки ответов API

# --- Настройка ---
BOT_TOKEN = "TOKEN" 
GEMINI_API_KEY = "API_KEY" 
YANDEX_API_KEY = "API_KEY" 

# Конфигурируем Google AI SDK
gemini_configured = False
if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
    print("!!! ВНИМАНИЕ: Не указан Google AI (Gemini) API ключ...")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("Google AI (Gemini) SDK успешно сконфигурирован.")
        gemini_configured = True
    except Exception as e:
        print(f"Ошибка конфигурации Google AI (Gemini) SDK: {e}")

# Проверка ключа Yandex
yandex_configured = False
if not YANDEX_API_KEY or YANDEX_API_KEY == "YOUR_YANDEX_ROUTING_API_KEY":
    print("!!! ВНИМАНИЕ: Не указан Yandex API ключ. Расчет точного расстояния и платных дорог не будет работать.")
else:
    print("Yandex API ключ указан.")
    yandex_configured = True


bot = telebot.TeleBot(BOT_TOKEN)

# --- УДАЛЕНИЕ WEBHOOK ---
print("Пытаюсь удалить вебхук...")
try:
    webhook_removed = bot.remove_webhook()
    if webhook_removed: print("Вебхук успешно удален.")
    else: print("Вебхук не был установлен или уже удален.")
    time.sleep(0.5)
except Exception as e:
    print(f"Ошибка при удалении вебхука: {e}")

# --- Управление состоянием пользователя ---
user_states = {}
user_data = {}
def set_user_state(chat_id, state): user_states[chat_id] = state; print(f"State for {chat_id} set: {state}")
def get_user_state(chat_id): return user_states.get(chat_id)
def clear_user_state(chat_id):
    user_states.pop(chat_id, None); user_data.pop(chat_id, None)
    print(f"State/data for {chat_id} cleared.")

# --- Тексты сообщений ---
texts = {
    "welcome": "Привет. Я могу ответить на твои вопросы, либо с помощью ИИ помочь тебе с логистикой! Что выберешь?",
    "questions_menu": "Какой вопрос тебя интересует?",
    "logistics_help_start": "Чтобы помочь с логистикой, мне нужны две точки на карте.",
    "ask_ai_prompt": "Задайте свой вопрос для AI (Gemini):",
    "ask_ai_processing": "⏳ Обрабатываю ваш вопрос с помощью AI (Gemini)...",
    "ask_ai_error": "😕 К сожалению, произошла ошибка при обращении к AI (Gemini). Попробуйте позже.",
    "ask_location_1": "📍 Пожалуйста, отправьте первую точку (начальную), используя вложение 'Геопозиция'.",
    "ask_location_2": "📍 Отлично! Теперь отправьте вторую точку (конечную), используя вложение 'Геопозиция'.",
    "logistics_processing": "⏳ Получаю данные о маршруте от Яндекс.Карт и анализирую логистику с помощью AI (Gemini)... Пожалуйста, подождите.",
    "logistics_error": "😕 Не удалось проанализировать логистику с помощью AI. Возможно, сервис временно недоступен или произошла ошибка.",
    "yandex_routing_error": "⚠️ Не удалось получить точные данные о маршруте от Яндекс.Карт. Расчет будет менее точным.",
    "location_unexpected": "Пожалуйста, используйте кнопку 'Помощь с логистикой' и отправьте геоточку через вложения.",
    "ai_unexpected": "Пожалуйста, используйте кнопку 'Спросить у AI', чтобы задать вопрос.",
    "advantages": "Какие основные преимущества внедрения AI и IoT в логистику?\nAI и IoT помогают оптимизировать маршруты, снижать операционные расходы, улучшить отслеживание в реальном времени и управлять запасами, что приводит к более быстрым и эффективным поставкам.",
    "integration_steps": "Какие шаги нужно предпринять для интеграции AI и IoT в существующие логистические процессы?\nДля успешной интеграции AI и IoT необходимо провести аудит текущих процессов, выбрать подходящие технологии, обучить персонал и начать с пилотных проектов. Важно выбрать поставщиков, которые могут обеспечить масштабируемость и совместимость с уже существующими системами.",
    "supply_chain": "Как AI и IoT помогают в управлении цепочками поставок?\nAI и IoT позволяют отслеживать товары в реальном времени, предсказывать возможные задержки и оптимизировать процессы закупок и доставки, обеспечивая более эффективное управление запасами и минимизацию излишков.",
    "roi": "Какова типичная окупаемость инвестиций (ROI) при внедрении AI и IoT в логистике?\nROI может быть значительным, благодаря экономии на оптимизации маршрутов, сокращению расхода топлива, снижению операционных сбоев и более эффективному распределению ресурсов. Время на возврат инвестиций будет зависеть от масштаба внедрения."
}

# --- Функции для создания клавиатур ---
def create_main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1); btn_questions = types.InlineKeyboardButton("Помощь с вопросами", callback_data="show_questions"); btn_logistics = types.InlineKeyboardButton("Помощь с логистикой", callback_data="start_logistics"); keyboard.add(btn_questions, btn_logistics); return keyboard
def create_questions_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2); btn_advantages = types.InlineKeyboardButton("Преимущества AI", callback_data="show_advantages"); btn_supply_chain = types.InlineKeyboardButton("AI в цепочках поставок", callback_data="show_supply_chain"); btn_integration = types.InlineKeyboardButton("Шаги интеграции", callback_data="show_integration_steps"); btn_roi = types.InlineKeyboardButton("Окупаемость", callback_data="show_roi"); btn_ask_ai = types.InlineKeyboardButton("🤖 Спросить у AI", callback_data="ask_ai"); btn_back_main = types.InlineKeyboardButton("⬅️ Вернуться", callback_data="back_to_main"); keyboard.add(btn_advantages, btn_supply_chain, btn_integration, btn_roi); keyboard.add(btn_ask_ai); keyboard.add(btn_back_main); return keyboard
def create_cancel_keyboard(cancel_callback="back_to_main"):
    keyboard = types.InlineKeyboardMarkup(row_width=1); btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=cancel_callback); keyboard.add(btn_cancel); return keyboard
def create_back_to_questions_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1); btn_back = types.InlineKeyboardButton("⬅️ Назад к вопросам", callback_data="back_to_questions"); keyboard.add(btn_back); return keyboard
def create_back_to_main_menu_keyboard():
     keyboard = types.InlineKeyboardMarkup(row_width=1); btn_back = types.InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main"); keyboard.add(btn_back); return keyboard

# --- Функция получения данных маршрута от Yandex Directions API ---
def get_yandex_route_info(start_lat, start_lon, end_lat, end_lon):
    if not yandex_configured:
        print("Yandex API не настроен, пропускаю запрос маршрута.")
        return None
    waypoints = f"{start_lon},{start_lat}|{end_lon},{end_lat}"
    api_url = "https://api.routing.yandex.net/v2/route"
    params = {"apikey": YANDEX_API_KEY, "waypoints": waypoints, "mode": "driving", "results": 1}
    print(f"Запрос к Yandex Directions API: waypoints={waypoints}")
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        routes = data.get("route", {}).get("legs", [])
        if not routes:
            print("Маршрут не найден в ответе Yandex Directions API.")
            return None
        summary = routes[0].get("summary", {})
        distance_meters = summary.get("distance", {}).get("value")
        has_tolls = summary.get("flags", {}).get("tolls", False)
        if distance_meters is None:
            print("Не удалось извлечь расстояние из ответа Yandex.")
            return None
        distance_km = round(distance_meters / 1000, 1)
        print(f"Yandex Route Info: Distance={distance_km} km, Has Tolls={has_tolls}")
        return {'distance_km': distance_km, 'has_tolls': has_tolls}
    except requests.exceptions.Timeout: print("Ошибка: Таймаут при запросе к Yandex Directions API"); return None
    except requests.exceptions.RequestException as e: print(f"Ошибка сети при запросе к Yandex Directions API: {e}"); return None
    except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e: print(f"Ошибка при обработке ответа от Yandex Directions API: {e}"); return None
    except Exception as e: print(f"Непредвиденная ошибка при запросе маршрута Yandex: {e}"); return None

# --- Обработчики ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    print(f"User {message.from_user.first_name} ({message.chat.id}) started the bot.")
    clear_user_state(message.chat.id); keyboard = create_main_menu_keyboard(); bot.send_message(message.chat.id, texts["welcome"], reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id; message_id = call.message.message_id; user_name = call.from_user.first_name; callback_data = call.data
    print(f"User {user_name} ({chat_id}) pressed button: {callback_data}"); bot.answer_callback_query(call.id)
    try:
        if callback_data == "ask_ai":
            if not gemini_configured: bot.answer_callback_query(call.id, "Сервис AI недоступен.", show_alert=True); return
            set_user_state(chat_id, 'awaiting_ai_question'); keyboard = create_cancel_keyboard("back_to_questions"); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["ask_ai_prompt"], reply_markup=keyboard)
        elif callback_data == "show_questions":
            clear_user_state(chat_id); keyboard = create_questions_menu_keyboard(); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["questions_menu"], reply_markup=keyboard)
        elif callback_data == "start_logistics":
            clear_user_state(chat_id); set_user_state(chat_id, 'awaiting_location_1'); user_data[chat_id] = {}; keyboard = create_cancel_keyboard("back_to_main"); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["ask_location_1"], reply_markup=keyboard)
        elif callback_data == "show_advantages": clear_user_state(chat_id); keyboard = create_back_to_questions_keyboard(); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["advantages"], reply_markup=keyboard)
        elif callback_data == "show_integration_steps": clear_user_state(chat_id); keyboard = create_back_to_questions_keyboard(); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["integration_steps"], reply_markup=keyboard)
        elif callback_data == "show_supply_chain": clear_user_state(chat_id); keyboard = create_back_to_questions_keyboard(); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["supply_chain"], reply_markup=keyboard)
        elif callback_data == "show_roi": clear_user_state(chat_id); keyboard = create_back_to_questions_keyboard(); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["roi"], reply_markup=keyboard)
        elif callback_data == "back_to_questions": clear_user_state(chat_id); keyboard = create_questions_menu_keyboard(); bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["questions_menu"], reply_markup=keyboard)
        elif callback_data == "back_to_main":
            clear_user_state(chat_id); keyboard = create_main_menu_keyboard()
            try: bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=texts["welcome"], reply_markup=keyboard)
            except telebot.apihelper.ApiTelegramException as e:
                 if "message can't be edited" in str(e) or "message to edit not found" in str(e): bot.send_message(chat_id, texts["welcome"], reply_markup=keyboard)
                 else: print(f"Ошибка API при возврате в главное меню (edit): {e}"); bot.send_message(chat_id, texts["welcome"], reply_markup=keyboard)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка API при обработке callback {callback_data}: {e}")
        err_text = "Произошла ошибка Telegram API."
        if "message is not modified" in str(e): err_text="Вы уже здесь."
        elif "message to edit not found" in str(e): err_text="Сообщение устарело."
        elif "Too Many Requests" in str(e): err_text="Слишком много запросов, попробуйте чуть позже."
        bot.answer_callback_query(call.id, text=err_text)
    except Exception as e:
        print(f"Непредвиденная ошибка при обработке callback {callback_data}: {e}"); bot.answer_callback_query(call.id, text="Произошла внутренняя ошибка.")


@bot.message_handler(content_types=['location'])
def handle_location(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    current_state = get_user_state(chat_id)
    location = message.location
    print(f"User {user_name} ({chat_id}) sent location: {location}. Current state: {current_state}")

    if current_state == 'awaiting_location_1':
        user_data[chat_id] = {'loc1': location}
        set_user_state(chat_id, 'awaiting_location_2')
        keyboard = create_cancel_keyboard("back_to_main")
        try:
             if message.reply_to_message: bot.delete_message(chat_id, message.reply_to_message.message_id)
        except Exception as del_err: print(f"Не удалось удалить сообщение: {del_err}")
        bot.send_message(chat_id, texts["ask_location_2"], reply_markup=keyboard)

    elif current_state == 'awaiting_location_2':
        if chat_id in user_data and 'loc1' in user_data[chat_id]:
            loc1 = user_data[chat_id]['loc1']
            loc2 = location
            print(f"Received locations for {chat_id}: Loc1=({loc1.latitude},{loc1.longitude}), Loc2=({loc2.latitude},{loc2.longitude})")

            processing_msg = bot.send_message(chat_id, texts["logistics_processing"])
            yandex_route_info = None
            yandex_error_occurred = False

            if yandex_configured:
                yandex_route_info = get_yandex_route_info(loc1.latitude, loc1.longitude, loc2.latitude, loc2.longitude)
                if yandex_route_info is None: yandex_error_occurred = True

            if not gemini_configured:
                bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id, text="Извините, сервис AI для анализа логистики сейчас недоступен.", reply_markup=create_back_to_main_menu_keyboard())
                clear_user_state(chat_id); return

            distance_text = "неизвестно (ошибка получения данных от Яндекс.Карт)"
            tolls_text = "неизвестно (ошибка получения данных от Яндекс.Карт)"
            tolls_clause_for_cost = "Возможно, на маршруте есть платные участки, учти это при оценке."
            distance_clause_for_prompt = "Оцени примерное расстояние самостоятельно."
            if yandex_route_info:
                distance_km = yandex_route_info['distance_km']
                has_tolls = yandex_route_info['has_tolls']
                distance_text = f"примерно {distance_km} км (рассчитано по Яндекс Картам)"
                tolls_text = "вероятно включает" if has_tolls else "вероятно НЕ включает"
                tolls_clause_for_cost = "Учти, что маршрут " + tolls_text + " платные участки при оценке стоимости."
                distance_clause_for_prompt = f"Используй расстояние {distance_km} км для расчета расхода топлива."

            # --- ИЗМЕНЕННЫЙ ПРОМПТ С УКАЗАНИЕМ НА HTML ---
            prompt = f"""
            Проанализируй логистический маршрут и дай рекомендации.

            Исходные данные:
            - Точка отправления (широта, долгота): {loc1.latitude}, {loc1.longitude}
            - Точка назначения (широта, долгота): {loc2.latitude}, {loc2.longitude}
            - Груз: 1 тонна, товар устойчивый к повреждениям (не хрупкий).
            - Приоритет: Минимизация стоимости перевозки. Скорость доставки менее важна.
            - РАССТОЯНИЕ ПО МАРШРУТУ: {distance_text}.
            - ПЛАТНЫЕ ДОРОГИ: Маршрут {tolls_text} платные участки (по данным Яндекс Карт).

            Задачи:
            1. Определи наиболее выгодный вид наземного транспорта (фургон, ГАЗель, среднетоннажный грузовик и т.п.), учитывая вес 1т и приоритет низкой стоимости.
            2. Оцени примерную ОБЩУЮ стоимость перевозки этим транспортом. {distance_clause_for_prompt} {tolls_clause_for_cost} Также учти примерную стоимость найма водителя (или амортизацию/аренду транспорта). Укажи, что это ОЦЕНКА.
            3. Опиши рекомендуемый маршрут в общих чертах (основные трассы, ключевые города).
            4. Представь ответ в структурированном виде. Используй ТОЛЬКО HTML-теги для форматирования (<b> для жирного, <i> для курсива, <code> для кода, <br> для переноса строки, если нужно). Не используй Markdown. Начни с краткого вывода.

            Примерный формат ответа (с HTML):
            <b>Рекомендация по логистике:</b><br>
            <ul>
            <li><b>Транспорт:</b> [Название транспорта]</li>
            <li><b>Примерная стоимость:</b> [Сумма] руб. (<i>ОЦЕНКА: включает топливо, водителя/аренду, возможные платные дороги</i>)</li>
            <li><b>Основные этапы маршрута:</b> [Краткое описание маршрута]</li>
            <li><b>Комментарий:</b> [Дополнительные пояснения, если есть]</li>
            </ul>
            """

            final_response_text = ""
            try:
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                # Добавляем параметры безопасности для снижения вероятности блокировки ответа
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                response = model.generate_content(prompt, safety_settings=safety_settings)

                if response.parts:
                    ai_response = response.text
                    if yandex_error_occurred: final_response_text = texts["yandex_routing_error"] + "\n\n" + ai_response
                    else: final_response_text = ai_response
                else: # Обработка блокировки или пустого ответа
                    block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "неизвестна"
                    final_response_text = texts["logistics_error"] + f"\n(Причина: Ответ AI был заблокирован [{block_reason}] или пуст)"
                    print(f"Gemini logistics response blocked/empty for chat {chat_id}. Reason: {block_reason}. Response: {response}")

            except Exception as e:
                print(f"Google AI (Gemini) API Error during logistics analysis: {e}")
                final_response_text = texts["logistics_error"]
                if yandex_error_occurred: final_response_text = texts["yandex_routing_error"] + "\n\n" + final_response_text

            # --- ОТПРАВКА РЕЗУЛЬТАТА С PARSE_MODE="HTML" И ОБРАБОТКОЙ ОШИБКИ ---
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id,
                                      text=final_response_text,
                                      reply_markup=create_back_to_main_menu_keyboard(),
                                      parse_mode="HTML") # <--- УСТАНОВЛЕН HTML
            except telebot.apihelper.ApiTelegramException as e:
                if "can't parse entities" in str(e): # Если даже HTML не спарсился (очень редкий случай)
                     print(f"!!! Ошибка парсинга HTML ответа Gemini: {e}. Отправляю без форматирования.")
                     try:
                          bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id,
                                                text=final_response_text, # Тот же текст, но без parse_mode
                                                reply_markup=create_back_to_main_menu_keyboard(),
                                                parse_mode=None) # <--- УБРАЛИ PARSE_MODE
                     except Exception as fallback_e:
                          print(f"Не удалось отправить сообщение даже без форматирования: {fallback_e}")
                          # Можно попытаться отправить стандартную ошибку
                          bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id,
                                                text=texts["logistics_error"],
                                                reply_markup=create_back_to_main_menu_keyboard())
                else: # Другая ошибка API Telegram при отправке
                     print(f"Ошибка Telegram API при отправке ответа логистики: {e}")
                     # Пытаемся отправить стандартную ошибку
                     bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id,
                                           text=texts["logistics_error"],
                                           reply_markup=create_back_to_main_menu_keyboard())

            clear_user_state(chat_id) # Очищаем состояние в любом случае после попытки отправки

        else: # Ошибка: нет данных о первой точке
            print(f"Error: State awaiting_location_2, but no loc1 found for chat {chat_id}")
            bot.send_message(chat_id, "Произошла ошибка, данные о первой точке потеряны...", reply_markup=create_main_menu_keyboard())
            clear_user_state(chat_id); keyboard = create_main_menu_keyboard(); bot.send_message(message.chat.id, texts["welcome"], reply_markup=keyboard)
    else: # Неожиданная геолокация
        bot.send_message(chat_id, texts["location_unexpected"])


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id; user_name = message.from_user.first_name; text = message.text; current_state = get_user_state(chat_id)
    print(f"User {user_name} ({chat_id}) sent text: '{text}'. Current state: {current_state}")

    if current_state == 'awaiting_ai_question':
        if not gemini_configured:
             bot.reply_to(message, "Извините, сервис AI (Gemini) сейчас недоступен."); clear_user_state(chat_id); keyboard = create_questions_menu_keyboard(); bot.send_message(chat_id, texts["questions_menu"], reply_markup=keyboard); return
        processing_msg = bot.reply_to(message, texts["ask_ai_processing"])
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            # --- ИЗМЕНЕННЫЙ ПРОМПТ С УКАЗАНИЕМ НА HTML ---
            prompt = f"Ты — ассистент по логистике и AI/IoT. Ответь на вопрос пользователя:\n\n{text}\n\nПожалуйста, используй ТОЛЬКО HTML-теги (<b>, <i>, <code>) для форматирования ответа, если это необходимо. Не используй Markdown."
            safety_settings=[ # Те же настройки безопасности
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},]
            response = model.generate_content(prompt, safety_settings=safety_settings)

            if response.parts: ai_response = response.text
            else:
                block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "неизвестна"
                ai_response = texts["ask_ai_error"] + f"\n(Причина: Ответ AI был заблокирован [{block_reason}] или пуст)"
                print(f"Gemini blocked/empty (text q): {chat_id}. Reason: {block_reason}. Prompt: '{prompt}'. Resp: {response}")

            # --- ОТПРАВКА РЕЗУЛЬТАТА С PARSE_MODE="HTML" И ОБРАБОТКОЙ ОШИБКИ ---
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id,
                                      text=ai_response,
                                      reply_markup=create_back_to_questions_keyboard(),
                                      parse_mode="HTML") # <--- УСТАНОВЛЕН HTML
            except telebot.apihelper.ApiTelegramException as e:
                 if "can't parse entities" in str(e):
                      print(f"!!! Ошибка парсинга HTML ответа Gemini (text q): {e}. Отправляю без форматирования.")
                      bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id,
                                            text=ai_response,
                                            reply_markup=create_back_to_questions_keyboard(),
                                            parse_mode=None) # <--- УБРАЛИ PARSE_MODE
                 else:
                      print(f"Ошибка Telegram API при отправке ответа на вопрос: {e}")
                      bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id,
                                            text=texts["ask_ai_error"],
                                            reply_markup=create_back_to_questions_keyboard())

        except Exception as e:
            print(f"Google AI (Gemini) API Error (text question): {e}")
            bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id, text=texts["ask_ai_error"], reply_markup=create_back_to_questions_keyboard())
        finally:
            clear_user_state(chat_id)

    elif current_state in ['awaiting_location_1', 'awaiting_location_2']:
        bot.reply_to(message, "Пожалуйста, отправьте геолокацию с помощью кнопки 'скрепка' -> 'Геопозиция'.")
    else:
        pass # Игнорируем остальной текст


# --- Запуск бота ---
if __name__ == '__main__':
    print("Бот запускается в режиме polling...")
    while True:
        try: bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except telebot.apihelper.ApiTelegramException as e:
             print(f"Ошибка Telegram API в infinity_polling: {e}")
             if "Conflict: terminated by other getUpdates request" in str(e): print("Обнаружен конфликт 'getUpdates'. Завершаю работу."); break
             else: print("Перезапуск через 15 секунд..."); time.sleep(15)
        except requests.exceptions.RequestException as e: print(f"Ошибка сети (requests) в infinity_polling: {e}"); print("Перезапуск через 30 секунд..."); time.sleep(30)
        except Exception as e: print(f"Критическая ошибка во время polling: {e}"); print("Перезапуск через 15 секунд..."); time.sleep(15)
        else: print("Infinity polling завершен без ошибок."); break
    print("Бот остановлен.")
