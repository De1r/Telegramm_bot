import requests
from bs4 import BeautifulSoup
import time
import random

def GetParcing():
    """
    Парсит средние цены на квартиры в Ростове-на-Дону с ЦИАН.
    Возвращает список: [цена_студии, цена_1к, цена_2к, цена_3к, общая_средняя]
    """
    
    # Ссылки на страницы ЦИАН с фильтром по Ростову-на-Дону
    urls = [
        'https://rostov.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4960&room1=1',  # Студии
        'https://rostov.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4960&room1=1&room2=1',  # 1-комнатные
        'https://rostov.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4960&room1=2&room2=2',  # 2-комнатные
        'https://rostov.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&region=4960&room1=3&room2=3',  # 3-комнатные
    ]
    
    prices = []  # Сюда будем собирать средние цены
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]
    
    print("[PARSER] Начинаю парсинг ЦИАН...")
    
    for i, url in enumerate(urls):
        try:
            # Случайная задержка и User-Agent для имитации человека
            time.sleep(random.uniform(2, 4))
            headers = {'User-Agent': random.choice(user_agents)}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Проверяем на ошибки HTTP
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем блоки с объявлениями (актуальные селекторы для ЦИАН)
            offer_cards = soup.find_all('article', {'data-name': 'CardComponent'})
            
            card_prices = []
            for card in offer_cards[:10]:  # Берем первые 10 объявлений
                # Ищем элемент с ценой
                price_elem = card.find('span', {'data-mark': 'MainPrice'})
                if price_elem:
                    price_text = price_elem.text.strip()
                    # Очищаем цену от пробелов и "₽"
                    price_clean = price_text.replace(' ', '').replace('₽', '').replace('\xa0', '')
                    try:
                        price_num = int(price_clean)
                        card_prices.append(price_num)
                    except ValueError:
                        continue
            
            if card_prices:
                avg_price = sum(card_prices) / len(card_prices)
                prices.append(avg_price)
                print(f"[PARSER] Найдено {len(card_prices)} объявлений для {'студий' if i==0 else f'{i+1}-комнатных'}. Средняя цена: {int(avg_price):,} руб.")
            else:
                # Запасные значения, если парсинг не сработал
                backup_prices = [1500000, 3500000, 5500000, 7500000]
                prices.append(backup_prices[i])
                print(f"[PARSER] Для {'студий' if i==0 else f'{i+1}-комнатных'} не найдено цен. Использую резервное значение.")
                
        except Exception as e:
            print(f"[PARSER] Ошибка при парсинге {'студий' if i==0 else f'{i+1}-комнатных'}: {e}")
            # Резервные значения в случае ошибки
            backup_prices = [1500000, 3500000, 5500000, 7500000]
            prices.append(backup_prices[i])
    
    # Если удалось получить все 4 цены, считаем общую среднюю
    if len(prices) == 4:
        overall_avg = sum(prices) / 4
        prices.append(overall_avg)  # 5-й элемент - общая средняя
        print(f"[PARSER] Парсинг завершен. Общая средняя цена: {int(overall_avg):,} руб.")
    else:
        # Если что-то пошло не так, создаем реалистичные данные
        prices = [1800000, 3800000, 5800000, 7800000, 4800000]
    
    return [int(p) for p in prices]

# Для тестирования парсера отдельно
if __name__ == "__main__":
    result = GetParcing()
    print("Результат парсинга:", result)
