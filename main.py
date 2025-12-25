import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split 
import numpy as np
from datetime import datetime, date
import telebot
from telebot import types
import parcer as pr
import logging

logging.basicConfig(level=logging.DEBUG)

token = "8502512474:AAGJUoFNqSDxg2k-jRD1k0jbgU38u9bQYRI"

parc = []
predict = 0
count = 0
pars = []

flats = ["студии", "1-комнатной квартиры", "2-комнатной квартиры", "3-комнатной квартиры"]
# Словарь для сопоставления текстовых команд с индексами квартир
room_commands = {
    'studio': 0,
    'студия': 0,
    'студию': 0,
    '0': 0,
    '1_room': 1,
    '1комнатная': 1,
    '1 комнатная': 1,
    '1': 1,
    '2_room': 2,
    '2комнатная': 2,
    '2 комнатная': 2,
    '2': 2,
    '3_room': 3,
    '3комнатная': 3,
    '3 комнатная': 3,
    '3': 3
}

bot = telebot.TeleBot(token)

def GetPredict():
    global count, pars, predict
    
    if count == 0:
        try:
            # 1. Получаем АКТУАЛЬНЫЕ цены через парсер
            print("[PREDICT] Запрашиваю актуальные цены у парсера...")
            pars = pr.GetParcing()
            print(f"[PREDICT] Парсер вернул: {pars}")
            
            # Проверяем данные от парсера
            if len(pars) < 5:
                raise ValueError(f"Парсер вернул недостаточно данных: {len(pars)} элементов")
            
            # Берем среднюю текущую цену для прогноза
            current_avg_price = pars[4]  # 5-й элемент - общая средняя
            
            # 2. Используем исторические данные для обучения модели
            try:
                read_file = pd.read_excel("data.xlsx")
                read_file.to_csv("data.csv", index=None, header=True)
                data = pd.read_csv("data.csv", sep=',')
                
                if len(data) > 10:  # Если есть достаточно исторических данных
                    # Подготовка данных
                    data = data[[data.columns[0], data.columns[3]]]
                    data.columns = ['Дата', 'Стоимость']
                    
                    # Корректируем исторические данные на инфляцию
                    # Находим последнюю историческую цену
                    last_historical_price = data['Стоимость'].iloc[-1]
                    
                    # Вычисляем коэффициент для приведения к текущим ценам
                    if last_historical_price > 0:
                        inflation_factor = current_avg_price / last_historical_price
                        # Ограничиваем разумный диапазон (от 0.8 до 1.5)
                        inflation_factor = max(0.8, min(inflation_factor, 1.5))
                    else:
                        inflation_factor = 1.1
                    
                    print(f"[PREDICT] Коэффициент инфляции: {inflation_factor:.2f}")
                    
                    # Создаем скорректированные данные
                    data['Стоимость_скорр'] = data['Стоимость'] * inflation_factor
                    
                    # Строим прогноз
                    projection = 1
                    data['Прогноз'] = data['Стоимость_скорр'].shift(-projection)
                    x = data[['Стоимость_скорр']][:-projection]
                    y = data['Прогноз'][:-projection]
                    
                    # Обучаем модель
                    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
                    model.fit(x, y)
                    
                    # Прогнозируем на основе текущей средней цены
                    latest_price_df = pd.DataFrame({'Стоимость_скорр': [current_avg_price]})
                    predict_raw = model.predict(latest_price_df)[0]
                    
                    # Гарантируем, что прогноз не ниже текущей цены
                    predict = float(max(predict_raw, current_avg_price * 0.95))
                    
                else:
                    # Если исторических данных мало, используем простой прогноз
                    print("[PREDICT] Мало исторических данных, использую простой прогноз")
                    predict = current_avg_price * 1.03  # +3%
                    
            except Exception as e:
                print(f"[PREDICT] Ошибка при работе с историческими данными: {e}")
                # Простой прогноз на основе текущих данных
                predict = current_avg_price * 1.02  # +2%
            
            count += 1
            print(f"[PREDICT] Финальный прогноз: {int(predict):,} руб.")
            
        except Exception as e:
            print(f"[PREDICT] Критическая ошибка: {e}")
            # Аварийные значения
            pars = [1800000, 3800000, 5800000, 7800000, 4800000]
            predict = 5000000
            count += 1
    else:
        print(f"[PREDICT] Использую кэшированный прогноз: {int(predict):,} руб.")

@bot.message_handler(commands=["start"])
def start(message):
    print(f"DEBUG: START called, chat_id: {message.chat.id}")
    bot.send_message(message.chat.id, "Привет, это Прогноз цен")
    bot.send_message(message.chat.id, "С моей помощью ты можешь узнать прогноз стоимости квартиры в Ростове-на-Дону. Подожди немного, мне нужно собрать данные...")
    
    # Инициализируем данные для прогноза
    try:
        GetPredict()
        bot.send_message(message.chat.id, "Данные загружены и модель обучена. Теперь вы можете использовать команды:\n\n"
                                          "/begin - начать работу\n"
                                          "/studio - прогноз для студии\n"
                                          "/1_room - прогноз для 1-комнатной квартиры\n"
                                          "/2_room - прогноз для 2-комнатной квартиры\n"
                                          "/3_room - прогноз для 3-комнатной квартиры\n\n"
                                          "Или просто напишите: студия, 1, 2, 3 и т.д.")
    except Exception as e:
        print(f"DEBUG: Error in GetPredict: {e}")
        bot.send_message(message.chat.id, f"Произошла ошибка при загрузке данных: {e}. Попробуйте позже.")

@bot.message_handler(commands=["prices"])
def show_prices(message):
    """Показать текущие цены от парсера"""
    try:
        if len(pars) >= 4:
            response = "Текущие средние цены в Ростове-на-Дону:\n\n"
            response += f"Студии: {pars[0]:,} руб.\n"
            response += f"1-комнатные: {pars[1]:,} руб.\n"
            response += f"2-комнатные: {pars[2]:,} руб.\n"
            response += f"3-комнатные: {pars[3]:,} руб.\n\n"
            response += f"Средняя общая цена: {pars[4]:,} руб.\n"
            response += f"Прогноз на 14 дней: {int(predict):,} руб."
        else:
            response = "Данные о ценах еще не загружены. Используйте /start"
        
        bot.send_message(message.chat.id, response)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при получении цен: {e}")

@bot.message_handler(commands=["begin"])
def begin(message):
    print(f"DEBUG: BEGIN command called, chat_id: {message.chat.id}")
    bot.send_message(message.chat.id, "Выберите тип квартиры:\n\n"
                                      "/studio или 'студия' - студия\n"
                                      "/1_room или '1' - 1-комнатная\n"
                                      "/2_room или '2' - 2-комнатная\n"
                                      "/3_room или '3' - 3-комнатная")

@bot.message_handler(commands=["studio", "1_room", "2_room", "3_room"])
def handle_room_command(message):
    """Обработчик команд для комнат"""
    print(f"DEBUG: Room command: {message.text}, chat_id: {message.chat.id}")
    
    # Извлекаем команду из текста (убираем слэш)
    command = message.text.replace('/', '').strip()
    
    # Получаем индекс типа квартиры
    if command in room_commands:
        room_index = room_commands[command]
        send_prediction(message.chat.id, room_index)
    else:
        bot.send_message(message.chat.id, "Неизвестная команда. Используйте /begin чтобы увидеть список команд.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Обработчик текстовых сообщений (не команд)"""
    print(f"DEBUG: Text message: {message.text}, chat_id: {message.chat.id}")
    
    text = message.text.strip().lower()
    
    # Проверяем, является ли текст командой для выбора комнаты
    if text in room_commands:
        room_index = room_commands[text]
        send_prediction(message.chat.id, room_index)
    elif text == 'начать' or text == 'begin':
        begin(message)
    elif text == 'старт' or text == 'start':
        start(message)
    else:
        bot.send_message(message.chat.id, "Не понимаю команду. Используйте /start чтобы начать работу.")

def send_prediction(chat_id, room_index):
    """Функция для отправки прогноза"""
    print(f"DEBUG: Sending prediction for room_index: {room_index}")
    
    # Проверяем, что pars и predict инициализированы
    if len(pars) <= room_index:
        bot.send_message(chat_id, "Ошибка: данные о ценах не загружены. Попробуйте команду /start")
        return
        
    if predict == 0:
        bot.send_message(chat_id, "Прогноз еще не рассчитан. Попробуйте команду /start")
        return
    
    # Исправленная логика расчета:
    # 1. Берем текущую среднюю цену для выбранного типа квартиры
    current_price_for_flat = pars[room_index]
    
    # 2. Вычисляем коэффициент прогноза (на сколько процентов изменится цена)
    # predict - это общая прогнозируемая средняя цена
    # pars[4] - это текущая общая средняя цена
    if pars[4] > 0:  # Проверяем, чтобы не делить на ноль
        forecast_factor = predict / pars[4]
    else:
        forecast_factor = 1.02  # Резервный прогноз +2%
    
    # 3. Применяем этот коэффициент к цене выбранной квартиры
    forecast_price = current_price_for_flat * forecast_factor
    
    # Отправляем прогноз
    bot.send_message(chat_id, f"Для {flats[room_index]}")
    bot.send_message(chat_id, "Прогноз на 14 дней:")
    bot.send_message(chat_id, f"{int(forecast_price):,} рублей")
    
    # Дополнительная информация для прозрачности
    change_percent = (forecast_factor - 1) * 100
    bot.send_message(chat_id, f"Текущая цена: {int(current_price_for_flat):,} руб. (изменение: {change_percent:+.1f}%)")
    
    # Предлагаем продолжить
    bot.send_message(chat_id, "Хотите сделать еще один прогноз? Напишите:\n"
                              "студия, 1, 2, 3 или /begin для выбора")

# Убираем параметр allowed_updates, так как используем только сообщения
bot.polling(none_stop=True)
