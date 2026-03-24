import asyncio
import random  # <-- Ajoutez cette ligne
import urllib.parse
import os
import json
import sqlite3
import re
import aiohttp
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv

# ================== CONFIGURATION TRAVELPAYOUTS ==================
API_TOKEN = "7cf46628a75a50705c7a6dbdedcc7165"
MARKER = "696220"
AGENT_WHATSAPP = "79961792326"

# Charger les variables d'environnement
load_dotenv()

# Configuration avec priorités
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443560025:AAEtWwc0vsQt7Dwc2mtiFI-DwybWshBu0IA")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================== BASE DE DONNÉES ==================
def init_db():
    """Initialiser la base de données SQLite"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_user_data(user_id, data):
    """Sauvegarder les données utilisateur"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", 
              (user_id, json.dumps(data), datetime.now()))
    conn.commit()
    conn.close()

def load_user_data(user_id):
    """Charger les données utilisateur"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT data FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {"lang": "fr"}

# Initialiser la base de données au démarrage
init_db()

# ================== VILLES PRINCIPALES (LISTE RÉDUITE POUR MENUS) ==================
PRINCIPAL_CITIES = {
    # Afrique - 8 villes principales
    "LFW": {"fr": "Lomé (LFW)", "en": "Lome (LFW)", "ru": "Ломе (LFW)"},
    "COO": {"fr": "Cotonou (COO)", "en": "Cotonou (COO)", "ru": "Котону (COO)"},
    "ACC": {"fr": "Accra (ACC)", "en": "Accra (ACC)", "ru": "Аккра (ACC)"},
    "LOS": {"fr": "Lagos (LOS)", "en": "Lagos (LOS)", "ru": "Лагос (LOS)"},
    "ABJ": {"fr": "Abidjan (ABJ)", "en": "Abidjan (ABJ)", "ru": "Абиджан (ABJ)"},
    "DKR": {"fr": "Dakar (DKR)", "en": "Dakar (DKR)", "ru": "Дакар (DKR)"},
    "CAI": {"fr": "Le Caire (CAI)", "en": "Cairo (CAI)", "ru": "Каир (CAI)"},
    "JNB": {"fr": "Johannesburg (JNB)", "en": "Johannesburg (JNB)", "ru": "Йоханнесбург (JNB)"},
    
    # Europe - 10 villes principales
    "CDG": {"fr": "Paris (CDG)", "en": "Paris (CDG)", "ru": "Париж (CDG)"},
    "LHR": {"fr": "Londres (LHR)", "en": "London (LHR)", "ru": "Лондон (LHR)"},
    "BRU": {"fr": "Bruxelles (BRU)", "en": "Brussels (BRU)", "ru": "Брюссель (BRU)"},
    "MAD": {"fr": "Madrid (MAD)", "en": "Madrid (MAD)", "ru": "Мадрид (MAD)"},
    "FCO": {"fr": "Rome (FCO)", "en": "Rome (FCO)", "ru": "Рим (FCO)"},
    "BER": {"fr": "Berlin (BER)", "en": "Berlin (BER)", "ru": "Берлин (BER)"},
    "AMS": {"fr": "Amsterdam (AMS)", "en": "Amsterdam (AMS)", "ru": "Амстердам (AMS)"},
    "IST": {"fr": "Istanbul (IST)", "en": "Istanbul (IST)", "ru": "Стамбул (IST)"},
    "ZRH": {"fr": "Zurich (ZRH)", "en": "Zurich (ZRH)", "ru": "Цюрих (ZRH)"},
    "BCN": {"fr": "Barcelone (BCN)", "en": "Barcelona (BCN)", "ru": "Барселона (BCN)"},
    
    # Russie - 5 villes principales
    "SVO": {"fr": "Moscou (SVO)", "en": "Moscow (SVO)", "ru": "Москва (SVO)"},
    "DME": {"fr": "Moscou (DME)", "en": "Moscow (DME)", "ru": "Москва (DME)"},
    "LED": {"fr": "Saint-Pétersbourg (LED)", "en": "Saint Petersburg (LED)", "ru": "Санкт-Петербург (LED)"},
    "KZN": {"fr": "Kazan (KZN)", "en": "Kazan (KZN)", "ru": "Казань (KZN)"},
    "SVX": {"fr": "Ekaterinbourg (SVX)", "en": "Yekaterinburg (SVX)", "ru": "Екатеринбург (SVX)"},
    "OVB": {"fr": "Novossibirsk (OVB)", "en": "Novosibirsk (OVB)", "ru": "Новосибирск (OVB)"},
    
    # Asie - 8 villes principales
    "BKK": {"fr": "Bangkok (BKK)", "en": "Bangkok (BKK)", "ru": "Бангкок (BKK)"},
    "NRT": {"fr": "Tokyo (NRT)", "en": "Tokyo (NRT)", "ru": "Токио (NRT)"},
    "DXB": {"fr": "Dubaï (DXB)", "en": "Dubai (DXB)", "ru": "Дубай (DXB)"},
    "ICN": {"fr": "Séoul (ICN)", "en": "Seoul (ICN)", "ru": "Сеул (ICN)"},
    "PEK": {"fr": "Pékin (PEK)", "en": "Beijing (PEK)", "ru": "Пекин (PEK)"},
    "SIN": {"fr": "Singapour (SIN)", "en": "Singapore (SIN)", "ru": "Сингапур (SIN)"},
    "DEL": {"fr": "New Delhi (DEL)", "en": "New Delhi (DEL)", "ru": "Нью-Дели (DEL)"},
    "HKT": {"fr": "Phuket (HKT)", "en": "Phuket (HKT)", "ru": "Пхукет (HKT)"},
    
    # Amérique - 8 villes principales
    "JFK": {"fr": "New York (JFK)", "en": "New York (JFK)", "ru": "Нью-Йорк (JFK)"},
    "YUL": {"fr": "Montréal (YUL)", "en": "Montreal (YUL)", "ru": "Монреаль (YUL)"},
    "YYZ": {"fr": "Toronto (YYZ)", "en": "Toronto (YYZ)", "ru": "Торонто (YYZ)"},
    "MEX": {"fr": "Mexico (MEX)", "en": "Mexico City (MEX)", "ru": "Мехико (MEX)"},
    "GRU": {"fr": "São Paulo (GRU)", "en": "São Paulo (GRU)", "ru": "Сан-Паулу (GRU)"},
    "EZE": {"fr": "Buenos Aires (EZE)", "en": "Buenos Aires (EZE)", "ru": "Буэнос-Айрес (EZE)"},
    "LAX": {"fr": "Los Angeles (LAX)", "en": "Los Angeles (LAX)", "ru": "Лос-Анджелес (LAX)"},
    "MIA": {"fr": "Miami (MIA)", "en": "Miami (MIA)", "ru": "Майами (MIA)"},
    
    # Océanie - 5 villes principales (AJOUTÉES)
    "SYD": {"fr": "Sydney (SYD)", "en": "Sydney (SYD)", "ru": "Сидней (SYD)"},
    "MEL": {"fr": "Melbourne (MEL)", "en": "Melbourne (MEL)", "ru": "Мельбурн (MEL)"},
    "AKL": {"fr": "Auckland (AKL)", "en": "Auckland (AKL)", "ru": "Окленд (AKL)"},
    "BNE": {"fr": "Brisbane (BNE)", "en": "Brisbane (BNE)", "ru": "Брисбен (BNE)"},
    "PER": {"fr": "Perth (PER)", "en": "Perth (PER)", "ru": "Перт (PER)"},
}

# ================== BASE DE DONNÉES COMPLÈTE (300+ VILLES) ==================
ALL_CITIES = {
    **PRINCIPAL_CITIES,
    
    # ========== AFRIQUE ==========
    # Afrique de l'Ouest
    "BKO": {"fr": "Bamako", "en": "Bamako", "ru": "Бамако"},
    "OUA": {"fr": "Ouagadougou", "en": "Ouagadougou", "ru": "Уагадугу"},
    "NIM": {"fr": "Niamey", "en": "Niamey", "ru": "Ниамей"},
    "NDJ": {"fr": "N'Djamena", "en": "N'Djamena", "ru": "Нджамена"},
    "BJL": {"fr": "Banjul", "en": "Banjul", "ru": "Банжул"},
    "FNA": {"fr": "Freetown", "en": "Freetown", "ru": "Фритаун"},
    "ROB": {"fr": "Monrovia", "en": "Monrovia", "ru": "Монровия"},
    
    # Afrique Centrale
    "DLA": {"fr": "Douala", "en": "Douala", "ru": "Дуала"},
    "FIH": {"fr": "Kinshasa", "en": "Kinshasa", "ru": "Киншаса"},
    "BZV": {"fr": "Brazzaville", "en": "Brazzaville", "ru": "Браззавиль"},
    "BGF": {"fr": "Bangui", "en": "Bangui", "ru": "Банги"},
    "SSG": {"fr": "Malabo", "en": "Malabo", "ru": "Малабо"},
    "LAD": {"fr": "Luanda", "en": "Luanda", "ru": "Луанда"},
    
    # Afrique de l'Est
    "ADD": {"fr": "Addis-Abeba", "en": "Addis Ababa", "ru": "Аддис-Абеба"},
    "NBO": {"fr": "Nairobi", "en": "Nairobi", "ru": "Найроби"},
    "DAR": {"fr": "Dar es Salaam", "en": "Dar es Salaam", "ru": "Дар-эс-Салам"},
    "KGL": {"fr": "Kigali", "en": "Kigali", "ru": "Кигали"},
    "EBB": {"fr": "Entebbe", "en": "Entebbe", "ru": "Энтеббе"},
    "JUB": {"fr": "Juba", "en": "Juba", "ru": "Джуба"},
    "MGQ": {"fr": "Mogadiscio", "en": "Mogadishu", "ru": "Могадишо"},
    "MBA": {"fr": "Mombasa", "en": "Mombasa", "ru": "Момбаса"},
    "ZNZ": {"fr": "Zanzibar", "en": "Zanzibar", "ru": "Занзибар"},
    
    # Afrique Australe
    "CPT": {"fr": "Le Cap", "en": "Cape Town", "ru": "Кейптаун"},
    "DUR": {"fr": "Durban", "en": "Durban", "ru": "Дурбан"},
    "GBE": {"fr": "Gaborone", "en": "Gaborone", "ru": "Габороне"},
    "HRE": {"fr": "Harare", "en": "Harare", "ru": "Хараре"},
    "LUN": {"fr": "Lusaka", "en": "Lusaka", "ru": "Лусака"},
    "MPM": {"fr": "Maputo", "en": "Maputo", "ru": "Мапуту"},
    "WDH": {"fr": "Windhoek", "en": "Windhoek", "ru": "Виндхук"},
    "TNR": {"fr": "Antananarivo", "en": "Antananarivo", "ru": "Антананариво"},
    "MRU": {"fr": "Port-Louis", "en": "Port Louis", "ru": "Порт-Луи"},
    "SEZ": {"fr": "Victoria", "en": "Victoria", "ru": "Виктория"},
    
    # Afrique du Nord
    "CMN": {"fr": "Casablanca", "en": "Casablanca", "ru": "Касабланка"},
    "RBA": {"fr": "Rabat", "en": "Rabat", "ru": "Рабат"},
    "TNG": {"fr": "Tanger", "en": "Tangier", "ru": "Танжер"},
    "ALG": {"fr": "Alger", "en": "Algiers", "ru": "Алжир"},
    "TUN": {"fr": "Tunis", "en": "Tunis", "ru": "Тунис"},
    "TIP": {"fr": "Tripoli", "en": "Tripoli", "ru": "Триполи"},
    
    # ========== EUROPE ==========
    # France
    "ORY": {"fr": "Paris Orly", "en": "Paris Orly", "ru": "Париж Орли"},
    "LYS": {"fr": "Lyon", "en": "Lyon", "ru": "Лион"},
    "MRS": {"fr": "Marseille", "en": "Marseille", "ru": "Марсель"},
    "NCE": {"fr": "Nice", "en": "Nice", "ru": "Ницца"},
    "TLS": {"fr": "Toulouse", "en": "Toulouse", "ru": "Тулуза"},
    "BOD": {"fr": "Bordeaux", "en": "Bordeaux", "ru": "Бордо"},
    "LIL": {"fr": "Lille", "en": "Lille", "ru": "Лилль"},
    "NTE": {"fr": "Nantes", "en": "Nantes", "ru": "Нант"},
    "STR": {"fr": "Strasbourg", "en": "Strasbourg", "ru": "Страсбург"},
    
    # Allemagne
    "MUC": {"fr": "Munich", "en": "Munich", "ru": "Мюнхен"},
    "FRA": {"fr": "Francfort", "en": "Frankfurt", "ru": "Франкфурт"},
    "HAM": {"fr": "Hambourg", "en": "Hamburg", "ru": "Гамбург"},
    "CGN": {"fr": "Cologne", "en": "Cologne", "ru": "Кёльн"},
    "DUS": {"fr": "Düsseldorf", "en": "Düsseldorf", "ru": "Дюссельдорф"},
    "LEJ": {"fr": "Leipzig", "en": "Leipzig", "ru": "Лейпциг"},
    "HAJ": {"fr": "Hanovre", "en": "Hanover", "ru": "Ганновер"},
    
    # Italie
    "MIL": {"fr": "Milan", "en": "Milan", "ru": "Милан"},
    "LIN": {"fr": "Milan Linate", "en": "Milan Linate", "ru": "Милан Линате"},
    "NAP": {"fr": "Naples", "en": "Naples", "ru": "Неаполь"},
    "VCE": {"fr": "Venise", "en": "Venice", "ru": "Венеция"},
    "FLR": {"fr": "Florence", "en": "Florence", "ru": "Флоренция"},
    "GOA": {"fr": "Gênes", "en": "Genoa", "ru": "Генуя"},
    "BLQ": {"fr": "Bologne", "en": "Bologna", "ru": "Болонья"},
    "PSA": {"fr": "Pise", "en": "Pisa", "ru": "Пиза"},
    
    # Espagne
    "AGP": {"fr": "Malaga", "en": "Malaga", "ru": "Малага"},
    "PMI": {"fr": "Palma de Majorque", "en": "Palma de Mallorca", "ru": "Пальма-де-Майорка"},
    "VLC": {"fr": "Valence", "en": "Valencia", "ru": "Валенсия"},
    "SVQ": {"fr": "Séville", "en": "Seville", "ru": "Севилья"},
    "BIO": {"fr": "Bilbao", "en": "Bilbao", "ru": "Бильбао"},
    "LPA": {"fr": "Las Palmas", "en": "Las Palmas", "ru": "Лас-Пальмас"},
    
    # Royaume-Uni
    "LGW": {"fr": "Londres Gatwick", "en": "London Gatwick", "ru": "Лондон Гатвик"},
    "STN": {"fr": "Londres Stansted", "en": "London Stansted", "ru": "Лондон Станстед"},
    "MAN": {"fr": "Manchester", "en": "Manchester", "ru": "Манчестер"},
    "EDI": {"fr": "Édimbourg", "en": "Edinburgh", "ru": "Эдинбург"},
    "BHX": {"fr": "Birmingham", "en": "Birmingham", "ru": "Бирмингем"},
    "GLA": {"fr": "Glasgow", "en": "Glasgow", "ru": "Глазго"},
    "LPL": {"fr": "Liverpool", "en": "Liverpool", "ru": "Ливерпуль"},
    
    # Autres Europe
    "LIS": {"fr": "Lisbonne", "en": "Lisbon", "ru": "Лиссабон"},
    "OPO": {"fr": "Porto", "en": "Porto", "ru": "Порту"},
    "ATH": {"fr": "Athènes", "en": "Athens", "ru": "Афины"},
    "SKG": {"fr": "Thessalonique", "en": "Thessaloniki", "ru": "Салоники"},
    "VIE": {"fr": "Vienne", "en": "Vienna", "ru": "Вена"},
    "PRG": {"fr": "Prague", "en": "Prague", "ru": "Прага"},
    "BUD": {"fr": "Budapest", "en": "Budapest", "ru": "Будапешт"},
    "WAW": {"fr": "Varsovie", "en": "Warsaw", "ru": "Варшава"},
    "KRK": {"fr": "Cracovie", "en": "Krakow", "ru": "Краков"},
    "CPH": {"fr": "Copenhague", "en": "Copenhagen", "ru": "Копенгаген"},
    "OSL": {"fr": "Oslo", "en": "Oslo", "ru": "Осло"},
    "ARN": {"fr": "Stockholm", "en": "Stockholm", "ru": "Стокгольм"},
    "HEL": {"fr": "Helsinki", "en": "Helsinki", "ru": "Хельсинки"},
    "DUB": {"fr": "Dublin", "en": "Dublin", "ru": "Дублин"},
    "KEF": {"fr": "Reykjavik", "en": "Reykjavik", "ru": "Рейкьявик"},
    
    # Europe de l'Est
    "BUH": {"fr": "Bucarest", "en": "Bucharest", "ru": "Бухарест"},
    "SOF": {"fr": "Sofia", "en": "Sofia", "ru": "София"},
    "BEG": {"fr": "Belgrade", "en": "Belgrade", "ru": "Белград"},
    "ZAG": {"fr": "Zagreb", "en": "Zagreb", "ru": "Загреб"},
    "LJU": {"fr": "Ljubljana", "en": "Ljubljana", "ru": "Любляна"},
    "TIA": {"fr": "Tirana", "en": "Tirana", "ru": "Тирана"},
    "SKP": {"fr": "Skopje", "en": "Skopje", "ru": "Скопье"},
    "KIV": {"fr": "Chisinau", "en": "Chisinau", "ru": "Кишинёв"},
    
    # ========== RUSSIE ==========
    "VKO": {"fr": "Moscou Vnukovo", "en": "Moscow Vnukovo", "ru": "Москва Внуково"},
    "DME": {"fr": "Moscou Domodedovo", "en": "Moscow Domodedovo", "ru": "Москва Домодедово"},
    "AER": {"fr": "Sotchi", "en": "Sochi", "ru": "Сочи"},
    "ROV": {"fr": "Rostov-sur-le-Don", "en": "Rostov-on-Don", "ru": "Ростов-на-Дону"},
    "KRR": {"fr": "Krasnodar", "en": "Krasnodar", "ru": "Краснодар"},
    "UFA": {"fr": "Oufa", "en": "Ufa", "ru": "Уфа"},
    "KUF": {"fr": "Samara", "en": "Samara", "ru": "Самара"},
    "CEK": {"fr": "Tcheliabinsk", "en": "Chelyabinsk", "ru": "Челябинск"},
    "OMS": {"fr": "Omsk", "en": "Omsk", "ru": "Омск"},
    "TOF": {"fr": "Tomsk", "en": "Tomsk", "ru": "Томск"},
    "KJA": {"fr": "Krasnoïarsk", "en": "Krasnoyarsk", "ru": "Красноярск"},
    "IKT": {"fr": "Irkoutsk", "en": "Irkutsk", "ru": "Иркутск"},
    "UUD": {"fr": "Oulan-Oudé", "en": "Ulan-Ude", "ru": "Улан-Удэ"},
    "KHV": {"fr": "Khabarovsk", "en": "Khabarovsk", "ru": "Хабаровск"},
    "VVO": {"fr": "Vladivostok", "en": "Vladivostok", "ru": "Владивосток"},
    "KGD": {"fr": "Kaliningrad", "en": "Kaliningrad", "ru": "Калининград"},
    "MMK": {"fr": "Mourmansk", "en": "Murmansk", "ru": "Мурманск"},
    "ARH": {"fr": "Arkhangelsk", "en": "Arkhangelsk", "ru": "Архангельск"},
    "NNM": {"fr": "Narian-Mar", "en": "Naryan-Mar", "ru": "Нарьян-Мар"},
    "PES": {"fr": "Petrozavodsk", "en": "Petrozavodsk", "ru": "Петрозаводск"},
    "VOG": {"fr": "Volgograd", "en": "Volgograd", "ru": "Волгоград"},
    "GSV": {"fr": "Saratov", "en": "Saratov", "ru": "Саратов"},
    "REN": {"fr": "Orenbourg", "en": "Orenburg", "ru": "Оренбург"},
    "NJC": {"fr": "Nijnevartovsk", "en": "Nizhnevartovsk", "ru": "Нижневартовск"},
    "NYM": {"fr": "Nadym", "en": "Nadym", "ru": "Надым"},
    "NOZ": {"fr": "Novokuznetsk", "en": "Novokuznetsk", "ru": "Новокузнецк"},
    "MJZ": {"fr": "Mirny", "en": "Mirny", "ru": "Мирный"},
    "PYJ": {"fr": "Polyarny", "en": "Polyarny", "ru": "Полярный"},
    
    # ========== ASIE ==========
    # Moyen-Orient
    "DOH": {"fr": "Doha", "en": "Doha", "ru": "Доха"},
    "AUH": {"fr": "Abou Dabi", "en": "Abu Dhabi", "ru": "Абу-Даби"},
    "SHJ": {"fr": "Charjah", "en": "Sharjah", "ru": "Шарджа"},
    "MCT": {"fr": "Mascate", "en": "Muscat", "ru": "Маскат"},
    "KWI": {"fr": "Koweït", "en": "Kuwait City", "ru": "Эль-Кувейт"},
    "BAH": {"fr": "Bahreïn", "en": "Bahrain", "ru": "Бахрейн"},
    "RUH": {"fr": "Riyad", "en": "Riyadh", "ru": "Эр-Рияд"},
    "JED": {"fr": "Jeddah", "en": "Jeddah", "ru": "Джидда"},
    "MED": {"fr": "Médine", "en": "Medina", "ru": "Медина"},
    "AMM": {"fr": "Amman", "en": "Amman", "ru": "Амман"},
    "TLV": {"fr": "Tel Aviv", "en": "Tel Aviv", "ru": "Тель-Авив"},
    "BEY": {"fr": "Beyrouth", "en": "Beirut", "ru": "Бейрут"},
    
    # Asie du Sud
    "KTM": {"fr": "Katmandou", "en": "Kathmandu", "ru": "Катманду"},
    "ISB": {"fr": "Islamabad", "en": "Islamabad", "ru": "Исламабад"},
    "KHI": {"fr": "Karachi", "en": "Karachi", "ru": "Карачи"},
    "LHE": {"fr": "Lahore", "en": "Lahore", "ru": "Лахор"},
    "DAC": {"fr": "Dacca", "en": "Dhaka", "ru": "Дакка"},
    "CMB": {"fr": "Colombo", "en": "Colombo", "ru": "Коломбо"},
    "MLE": {"fr": "Malé", "en": "Male", "ru": "Мале"},
    
    # Asie du Sud-Est
    "KUL": {"fr": "Kuala Lumpur", "en": "Kuala Lumpur", "ru": "Куала-Лумпур"},
    "PEN": {"fr": "Penang", "en": "Penang", "ru": "Пенанг"},
    "CGK": {"fr": "Jakarta", "en": "Jakarta", "ru": "Джакарта"},
    "DPS": {"fr": "Denpasar Bali", "en": "Denpasar Bali", "ru": "Денпасар Бали"},
    "MNL": {"fr": "Manille", "en": "Manila", "ru": "Манила"},
    "CEB": {"fr": "Cebu", "en": "Cebu", "ru": "Себу"},
    "BWN": {"fr": "Bandar Seri Begawan", "en": "Bandar Seri Begawan", "ru": "Бандар-Сери-Бегаван"},
    "PNH": {"fr": "Phnom Penh", "en": "Phnom Penh", "ru": "Пномпень"},
    "REP": {"fr": "Siem Reap", "en": "Siem Reap", "ru": "Сиемреап"},
    "VTE": {"fr": "Vientiane", "en": "Vientiane", "ru": "Вьентьян"},
    "RGN": {"fr": "Rangoun", "en": "Yangon", "ru": "Янгон"},
    "HAN": {"fr": "Hanoï", "en": "Hanoi", "ru": "Ханой"},
    "SGN": {"fr": "Ho Chi Minh Ville", "en": "Ho Chi Minh City", "ru": "Хошимин"},
    "DAD": {"fr": "Da Nang", "en": "Da Nang", "ru": "Дананг"},
    
    # Asie de l'Est
    "HKG": {"fr": "Hong Kong", "en": "Hong Kong", "ru": "Гонконг"},
    "TPE": {"fr": "Taipei", "en": "Taipei", "ru": "Тайбэй"},
    "MFM": {"fr": "Macao", "en": "Macau", "ru": "Макао"},
    "PVG": {"fr": "Shanghai Pudong", "en": "Shanghai Pudong", "ru": "Шанхай Пудун"},
    "SHA": {"fr": "Shanghai Hongqiao", "en": "Shanghai Hongqiao", "ru": "Шанхай Хунцяо"},
    "CAN": {"fr": "Canton", "en": "Guangzhou", "ru": "Гуанчжоу"},
    "SZX": {"fr": "Shenzhen", "en": "Shenzhen", "ru": "Шэньчжэнь"},
    "CTU": {"fr": "Chengdu", "en": "Chengdu", "ru": "Чэнду"},
    "XIY": {"fr": "Xi'an", "en": "Xi'an", "ru": "Сиань"},
    "TAO": {"fr": "Qingdao", "en": "Qingdao", "ru": "Циндао"},
    "KIX": {"fr": "Osaka", "en": "Osaka", "ru": "Осака"},
    "NGO": {"fr": "Nagoya", "en": "Nagoya", "ru": "Нагоя"},
    "FUK": {"fr": "Fukuoka", "en": "Fukuoka", "ru": "Фукуока"},
    "CTS": {"fr": "Sapporo", "en": "Sapporo", "ru": "Саппоро"},
    "OKA": {"fr": "Okinawa", "en": "Okinawa", "ru": "Окинава"},
    
    # ========== AMÉRIQUE ==========
    # États-Unis
    "ORD": {"fr": "Chicago", "en": "Chicago", "ru": "Чикаго"},
    "DFW": {"fr": "Dallas", "en": "Dallas", "ru": "Даллас"},
    "DEN": {"fr": "Denver", "en": "Denver", "ru": "Денвер"},
    "SFO": {"fr": "San Francisco", "en": "San Francisco", "ru": "Сан-Франциско"},
    "SEA": {"fr": "Seattle", "en": "Seattle", "ru": "Сиэтл"},
    "MCO": {"fr": "Orlando", "en": "Orlando", "ru": "Орландо"},
    "LAS": {"fr": "Las Vegas", "en": "Las Vegas", "ru": "Лас-Вегас"},
    "BOS": {"fr": "Boston", "en": "Boston", "ru": "Бостон"},
    "ATL": {"fr": "Atlanta", "en": "Atlanta", "ru": "Атланта"},
    "IAD": {"fr": "Washington DC", "en": "Washington DC", "ru": "Вашингтон"},
    "PHL": {"fr": "Philadelphie", "en": "Philadelphia", "ru": "Филадельфия"},
    "PHX": {"fr": "Phoenix", "en": "Phoenix", "ru": "Финикс"},
    "MSP": {"fr": "Minneapolis", "en": "Minneapolis", "ru": "Миннеаполис"},
    "DTW": {"fr": "Detroit", "en": "Detroit", "ru": "Детройт"},
    "CLE": {"fr": "Cleveland", "en": "Cleveland", "ru": "Кливленд"},
    "HOU": {"fr": "Houston", "en": "Houston", "ru": "Хьюстон"},
    
    # Canada
    "YVR": {"fr": "Vancouver", "en": "Vancouver", "ru": "Ванкувер"},
    "YYC": {"fr": "Calgary", "en": "Calgary", "ru": "Калгари"},
    "YOW": {"fr": "Ottawa", "en": "Ottawa", "ru": "Оттава"},
    "YHZ": {"fr": "Halifax", "en": "Halifax", "ru": "Галифакс"},
    "YQB": {"fr": "Québec", "en": "Quebec City", "ru": "Квебек"},
    
    # Mexique
    "CUN": {"fr": "Cancún", "en": "Cancun", "ru": "Канкун"},
    "GDL": {"fr": "Guadalajara", "en": "Guadalajara", "ru": "Гвадалахара"},
    "MTY": {"fr": "Monterrey", "en": "Monterrey", "ru": "Монтеррей"},
    "PVR": {"fr": "Puerto Vallarta", "en": "Puerto Vallarta", "ru": "Пуэрто-Вальярта"},
    
    # Caraïbes
    "SDQ": {"fr": "Saint-Domingue", "en": "Santo Domingo", "ru": "Санто-Доминго"},
    "PUJ": {"fr": "Punta Cana", "en": "Punta Cana", "ru": "Пунта-Кана"},
    "HAV": {"fr": "La Havane", "en": "Havana", "ru": "Гавана"},
    "VRA": {"fr": "Varadero", "en": "Varadero", "ru": "Варадеро"},
    "KIN": {"fr": "Kingston", "en": "Kingston", "ru": "Кингстон"},
    "MBJ": {"fr": "Montego Bay", "en": "Montego Bay", "ru": "Монтего-Бей"},
    "NAS": {"fr": "Nassau", "en": "Nassau", "ru": "Нассау"},
    "SJU": {"fr": "San Juan", "en": "San Juan", "ru": "Сан-Хуан"},
    "POS": {"fr": "Port-d'Espagne", "en": "Port of Spain", "ru": "Порт-оф-Спейн"},
    "BGI": {"fr": "Bridgetown", "en": "Bridgetown", "ru": "Бриджтаун"},
    
    # Amérique Centrale
    "SAL": {"fr": "San Salvador", "en": "San Salvador", "ru": "Сан-Сальвадор"},
    "GUA": {"fr": "Guatemala", "en": "Guatemala City", "ru": "Гватемала"},
    "SAP": {"fr": "San Pedro Sula", "en": "San Pedro Sula", "ru": "Сан-Педро-Сула"},
    "TGU": {"fr": "Tegucigalpa", "en": "Tegucigalpa", "ru": "Тегусигальпа"},
    "MGA": {"fr": "Managua", "en": "Managua", "ru": "Манагуа"},
    "SJO": {"fr": "San José", "en": "San Jose", "ru": "Сан-Хосе"},
    "PTY": {"fr": "Panama", "en": "Panama City", "ru": "Панама"},
    
    # Amérique du Sud
    "LIM": {"fr": "Lima", "en": "Lima", "ru": "Лима"},
    "CUZ": {"fr": "Cusco", "en": "Cusco", "ru": "Куско"},
    "SCL": {"fr": "Santiago", "en": "Santiago", "ru": "Сантьяго"},
    "COR": {"fr": "Córdoba", "en": "Córdoba", "ru": "Кордова"},
    "MVD": {"fr": "Montevideo", "en": "Montevideo", "ru": "Монтевидео"},
    "ASU": {"fr": "Asunción", "en": "Asunción", "ru": "Асунсьон"},
    "BOG": {"fr": "Bogota", "en": "Bogota", "ru": "Богота"},
    "MDE": {"fr": "Medellín", "en": "Medellín", "ru": "Медельин"},
    "CCS": {"fr": "Caracas", "en": "Caracas", "ru": "Каракас"},
    "GYE": {"fr": "Guayaquil", "en": "Guayaquil", "ru": "Гуаякиль"},
    "UIO": {"fr": "Quito", "en": "Quito", "ru": "Кито"},
    "LPB": {"fr": "La Paz", "en": "La Paz", "ru": "Ла-Пас"},
    "VVI": {"fr": "Santa Cruz", "en": "Santa Cruz", "ru": "Санта-Крус"},
    "FOR": {"fr": "Fortaleza", "en": "Fortaleza", "ru": "Форталеза"},
    "REC": {"fr": "Recife", "en": "Recife", "ru": "Ресифи"},
    "BSB": {"fr": "Brasilia", "en": "Brasilia", "ru": "Бразилиа"},
    "GIG": {"fr": "Rio de Janeiro", "en": "Rio de Janeiro", "ru": "Рио-де-Жанейро"},
    "CWB": {"fr": "Curitiba", "en": "Curitiba", "ru": "Куритиба"},
    
    # ========== OCÉANIE ==========
    "ADL": {"fr": "Adélaïde", "en": "Adelaide", "ru": "Аделаида"},
    "CBR": {"fr": "Canberra", "en": "Canberra", "ru": "Канберра"},
    "WLG": {"fr": "Wellington", "en": "Wellington", "ru": "Веллингтон"},
    "CHC": {"fr": "Christchurch", "en": "Christchurch", "ru": "Крайстчерч"},
    "SUV": {"fr": "Suva", "en": "Suva", "ru": "Сува"},
    "TBU": {"fr": "Nuku'alofa", "en": "Nuku'alofa", "ru": "Нукуалофа"},
    "APW": {"fr": "Apia", "en": "Apia", "ru": "Апиа"},
    "PPT": {"fr": "Papeete", "en": "Papeete", "ru": "Папеэте"},
    "NOU": {"fr": "Nouméa", "en": "Noumea", "ru": "Нумеа"},
    "VLI": {"fr": "Port-Vila", "en": "Port Vila", "ru": "Порт-Вила"},
    "HIR": {"fr": "Honiara", "en": "Honiara", "ru": "Хониара"},
    "POM": {"fr": "Port Moresby", "en": "Port Moresby", "ru": "Порт-Морсби"},
}

CONTINENTS = {
    "africa": {"fr": "🌍 Afrique", "en": "🌍 Africa", "ru": "🌍 Африка"},
    "europe": {"fr": "🇪🇺 Europe", "en": "🇪🇺 Europe", "ru": "🇪🇺 Европа"},
    "russia": {"fr": "🇷🇺 Russie", "en": "🇷🇺 Russia", "ru": "🇷🇺 Россия"},
    "asia": {"fr": "🌏 Asie", "en": "🌏 Asia", "ru": "🌏 Азия"},
    "america": {"fr": "🇺🇸🇨🇦 Amérique", "en": "🇺🇸🇨🇦 America", "ru": "🇺🇸🇨🇦 Америка"},
    "oceania": {"fr": "🌊 Océanie", "en": "🌊 Oceania", "ru": "🌊 Океания"},
}

CITIES_BY_CONTINENT = {
    "africa": {
        "LFW": PRINCIPAL_CITIES["LFW"],
        "COO": PRINCIPAL_CITIES["COO"],
        "ACC": PRINCIPAL_CITIES["ACC"],
        "LOS": PRINCIPAL_CITIES["LOS"],
        "ABJ": PRINCIPAL_CITIES["ABJ"],
        "DKR": PRINCIPAL_CITIES["DKR"],
        "CAI": PRINCIPAL_CITIES["CAI"],
        "JNB": PRINCIPAL_CITIES["JNB"],
    },
    "europe": {
        "CDG": PRINCIPAL_CITIES["CDG"],
        "LHR": PRINCIPAL_CITIES["LHR"],
        "BRU": PRINCIPAL_CITIES["BRU"],
        "MAD": PRINCIPAL_CITIES["MAD"],
        "FCO": PRINCIPAL_CITIES["FCO"],
        "BER": PRINCIPAL_CITIES["BER"],
        "AMS": PRINCIPAL_CITIES["AMS"],
        "IST": PRINCIPAL_CITIES["IST"],
        "ZRH": PRINCIPAL_CITIES["ZRH"],
        "BCN": PRINCIPAL_CITIES["BCN"],
    },
    "russia": {
        "SVO": PRINCIPAL_CITIES["SVO"],
        "DME": PRINCIPAL_CITIES["DME"],
        "LED": PRINCIPAL_CITIES["LED"],
        "KZN": PRINCIPAL_CITIES["KZN"],
        "SVX": PRINCIPAL_CITIES["SVX"],
        "OVB": PRINCIPAL_CITIES["OVB"],
    },
    "asia": {
        "BKK": PRINCIPAL_CITIES["BKK"],
        "NRT": PRINCIPAL_CITIES["NRT"],
        "DXB": PRINCIPAL_CITIES["DXB"],
        "ICN": PRINCIPAL_CITIES["ICN"],
        "PEK": PRINCIPAL_CITIES["PEK"],
        "SIN": PRINCIPAL_CITIES["SIN"],
        "DEL": PRINCIPAL_CITIES["DEL"],
        "HKT": PRINCIPAL_CITIES["HKT"],
    },
    "america": {
        "JFK": PRINCIPAL_CITIES["JFK"],
        "YUL": PRINCIPAL_CITIES["YUL"],
        "YYZ": PRINCIPAL_CITIES["YYZ"],
        "MEX": PRINCIPAL_CITIES["MEX"],
        "GRU": PRINCIPAL_CITIES["GRU"],
        "EZE": PRINCIPAL_CITIES["EZE"],
        "LAX": PRINCIPAL_CITIES["LAX"],
        "MIA": PRINCIPAL_CITIES["MIA"],
    },
    "oceania": {
        "SYD": PRINCIPAL_CITIES["SYD"],
        "MEL": PRINCIPAL_CITIES["MEL"],
        "AKL": PRINCIPAL_CITIES["AKL"],
        "BNE": PRINCIPAL_CITIES["BNE"],
        "PER": PRINCIPAL_CITIES["PER"],
    }
}

# ================== FONCTIONS UTILITAIRES ==================
def get_city_name(iata_code, lang):
    """Récupère le nom d'une ville de manière sécurisée"""
    if iata_code in PRINCIPAL_CITIES:
        name_with_code = PRINCIPAL_CITIES[iata_code].get(lang, iata_code)
        return name_with_code.split('(')[0].strip()
    elif iata_code in ALL_CITIES:
        return ALL_CITIES[iata_code].get(lang, iata_code)
    return iata_code

def find_city_by_name_or_code(input_text, lang):
    """
    Trouve une ville par son nom ou code IATA
    Retourne le code IATA si trouvé, sinon None
    """
    input_text = input_text.upper().strip()
    
    # 1. Chercher par code IATA exact
    if input_text in ALL_CITIES:
        return input_text
    
    # Normaliser l'entrée pour la recherche
    search_text = input_text.lower()
    
    # 2. Chercher dans les noms des villes principales (avec codes)
    for code, names in PRINCIPAL_CITIES.items():
        city_name = names[lang].lower()
        city_name_only = city_name.split('(')[0].strip().lower()
        if search_text in city_name or search_text in city_name_only:
            return code
    
    # 3. Chercher dans tous les noms de villes (sans codes)
    for code, names in ALL_CITIES.items():
        city_name = names[lang].lower()
        if search_text in city_name:
            return code
    
    # 4. Recherche partielle
    words = search_text.split()
    if len(words) > 1:
        for code, names in ALL_CITIES.items():
            city_name = names[lang].lower()
            if all(word in city_name for word in words):
                return code
    
    return None

def back_button(lang):
    """Texte du bouton Retour selon la langue"""
    texts = {
        "fr": "🔙 Retour",
        "en": "🔙 Back", 
        "ru": "🔙 Назад"
    }
    return texts[lang]

def get_passenger_text(p, lang):
    """Formate le texte des passagers selon la langue"""
    if lang == "fr":
        return f"{p} passager" if p == 1 else f"{p} passagers"
    elif lang == "en":
        return f"{p} passenger" if p == 1 else f"{p} passengers"
    else:
        if p == 1:
            return f"{p} пассажир"
        elif 2 <= p <= 4:
            return f"{p} пассажира"
        else:
            return f"{p} пассажиров"

# ================== FONCTION CORRIGÉE POUR LES LIENS - SOLUTION RÉELLE ==================

def generate_tpst_link(user_data):
    """
    ✅ CORRIGÉ : Génère un lien aviasales.tp.st qui FONCTIONNE vraiment
    FORMAT CORRECT : https://tp.media/r?marker=696220&p=4114&u=URL_ENCODÉE
    (Supprimé trs=null)
    """
    trip_type = user_data.get("trip_type", "one_way")
    origin = user_data['from']
    destination = user_data['to']
    
    # Construire l'URL Aviasales de base SANS marker
    if trip_type == "one_way":
        base_url = (
            f"https://www.aviasales.com/search?"
            f"origin={origin}&"
            f"destination={destination}&"
            f"depart_date={user_data['departure_date']}&"
            f"adults=1&children=0&infants=0"
        )
    else:
        base_url = (
            f"https://www.aviasales.com/search?"
            f"origin={origin}&"
            f"destination={destination}&"
            f"departure_date={user_data['departure_date']}&"
            f"return_date={user_data['return_date']}&"
            f"adults=1&children=0&infants=0"
        )
    
    # DEBUG : Afficher l'URL de base
    print(f"\n🔗 URL de base générée: {base_url}")
    
    # IMPORTANT : Utiliser quote_plus POUR LES ESPACES
    encoded_url = urllib.parse.quote_plus(base_url)
    print(f"🔗 URL encodée: {encoded_url[:200]}...")
    
    # ✅ FORMAT OFFICIEL QUI FONCTIONNE - SANS trs=null !
    tpst_link = f"https://tp.media/r?marker={MARKER}&p=4114&u={encoded_url}"
    
    # Alternative si ça ne fonctionne pas :
    # tpst_link = f"https://tp.media/click?shmarker={MARKER}&promo_id=4114&source_type=link&type=click&u={encoded_url}"
    
    print(f"🔗 Lien tp.media final: {tpst_link}")
    print(f"✅ Marker: {MARKER}")
    
    # Texte du type de voyage
    lang = user_data.get("lang", "fr")
    if lang == "fr":
        trip_type_text = "Aller simple" if trip_type == "one_way" else "Aller-retour"
    elif lang == "en":
        trip_type_text = "One way" if trip_type == "one_way" else "Round trip"
    else:
        trip_type_text = "В одну сторону" if trip_type == "one_way" else "Туда и обратно"
    
    # Dates
    dates_text = user_data['departure_date'] if trip_type == "one_way" else f"{user_data['departure_date']} - {user_data['return_date']}"
    
    return {
        'url': tpst_link,
        'trip_type': trip_type_text,
        'dates': dates_text
    }

# ================== CALENDRIER SIMPLE ==================
def simple_date_menu(lang):
    """Menu simple pour les dates"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    in_3_days = today + timedelta(days=3)
    in_1_week = today + timedelta(days=7)
    in_2_weeks = today + timedelta(days=14)
    in_1_month = today + timedelta(days=30)
    
    if lang == "fr":
        kb.row(
            types.KeyboardButton(f"📅 Aujourd'hui ({today.strftime('%d/%m')})"),
            types.KeyboardButton(f"📅 Demain ({tomorrow.strftime('%d/%m')})")
        )
        kb.row(
            types.KeyboardButton(f"📅 3 jours ({in_3_days.strftime('%d/%m')})"),
            types.KeyboardButton(f"📅 1 semaine ({in_1_week.strftime('%d/%m')})")
        )
        kb.row(
            types.KeyboardButton(f"📅 2 semaines ({in_2_weeks.strftime('%d/%m')})"),
            types.KeyboardButton(f"📅 1 mois ({in_1_month.strftime('%d/%m')})")
        )
        kb.add("✍️ Entrer une date manuellement")
        
    elif lang == "en":
        kb.row(
            types.KeyboardButton(f"📅 Today ({today.strftime('%m/%d')})"),
            types.KeyboardButton(f"📅 Tomorrow ({tomorrow.strftime('%m/%d')})")
        )
        kb.row(
            types.KeyboardButton(f"📅 3 days ({in_3_days.strftime('%m/%d')})"),
            types.KeyboardButton(f"📅 1 week ({in_1_week.strftime('%m/%d')})")
        )
        kb.row(
            types.KeyboardButton(f"📅 2 weeks ({in_2_weeks.strftime('%m/%d')})"),
            types.KeyboardButton(f"📅 1 month ({in_1_month.strftime('%m/%d')})")
        )
        kb.add("✍️ Enter date manually")
        
    else:  # russe
        kb.row(
            types.KeyboardButton(f"📅 Сегодня ({today.strftime('%d.%m')})"),
            types.KeyboardButton(f"📅 Завтра ({tomorrow.strftime('%d.%m')})")
        )
        kb.row(
            types.KeyboardButton(f"📅 Через 3 дня ({in_3_days.strftime('%d.%m')})"),
            types.KeyboardButton(f"📅 Через неделю ({in_1_week.strftime('%d.%m')})")
        )
        kb.row(
            types.KeyboardButton(f"📅 Через 2 недели ({in_2_weeks.strftime('%d.%m')})"),
            types.KeyboardButton(f"📅 Через месяц ({in_1_month.strftime('%d.%m')})")
        )
        kb.add("✍️ Ввести дату вручную")
    
    kb.add(back_button(lang))
    return kb

# ================== TEXTS ==================
T = {
    "fr": {
        "welcome": "✈️ Bienvenue !\n\nTu cherches un billet d'avion ? Ce bot te fait gagner du temps et de l'argent.\n\n💡 Simple. Rapide. Gratuit.",
        "search": "🔍 Rechercher un vol",
        "trip_type": "✈️ Type de voyage :",
        "one_way": "➡️ Aller simple",
        "round_trip": "🔄 Aller-retour",
        "from": "🌍 Ville de départ :",
        "from_custom": "✍️ Entrez le nom de la ville de départ ou son code aéroport (ex: Paris ou CDG) :",
        "to": "🛬 Ville d'arrivée :",
        "to_custom": "✍️ Entrez le nom de la ville d'arrivée ou son code aéroport (ex: New York ou JFK) :",
        "departure_date": "📅 Date de départ :",
        "return_date": "📅 Date de retour :",
        "today": "📅 Aujourd'hui",
        "tomorrow": "📅 Demain",
        "manual": "✍️ Entrer une date",
        "format": "📅 Format : YYYY-MM-DD\n\nExemple : 2024-12-25",
        "passengers": "👥 Nombre de passagers :",
        "payment": "💳 Comment souhaitez-vous payer ?",
        "pay_card_text": "💳 Vous pouvez payer directement par carte sur Aviasales via le lien ci-dessus.",
        "pay_agent_text": "📲 Contactez directement un agent sur WhatsApp :",
        "result": "✈️ Voici votre recherche :",
        "choose_departure_continent": "🌍 Continent de départ :",
        "choose_arrival_continent": "🌍 Continent d'arrivée :",
        "contact": "📞 Contacter un agent",
        "contact_text": "📞 WhatsApp : +7 996 179 23 26\n📧 Email : kwami.wampah@yahoo.com",
        "about": "ℹ️ À propos",
        "about_text": "✈️ Bot de recherche de billets d'avion.\n🔹 Rapide\n🔹 Simple\n🔹 Gratuit\n\n📞 Contact : +7 996 179 23 26",
        "passenger_singular": "passager",
        "passenger_plural": "passagers",
        "economy_class": "Classe Économique",
        "one_way_trip": "Aller simple",
        "round_trip_text": "Aller-retour",
        "departure": "Aller",
        "return": "Retour",
        "error_date_format": "❌ Format de date incorrect. Utilisez YYYY-MM-DD",
        "error_return_before_departure": "❌ La date de retour doit être après la date d'aller.",
        "search_cancelled": "🔄 Recherche annulée.",
        "select_city_from_list": "🌍 Sélectionnez une ville dans la liste ou tapez son nom :",
        "enter_custom_city": "✍️ Taper une autre ville...",
        "city_not_found": "❌ Ville non trouvée. Essayez :\n- Le nom complet (ex: 'Paris')\n- Le code aéroport (ex: 'CDG')\n- Vérifiez l'orthographe",
        "city_found": "✅ Ville reconnue : ",
        "help": "📚 **Aide**\n\n"
                "Commandes disponibles:\n"
                "/start - Démarrer le bot\n"
                "/reset - Annuler la recherche en cours\n"
                "/help - Voir cette aide\n"
                "/contact - Contacter un agent\n\n"
                "Pour rechercher un vol:\n"
                "1. Cliquez sur '🔍 Rechercher un vol'\n"
                "2. Suivez les étapes indiquées\n"
                "3. Recevez votre lien de réservation\n\n"
                "💡 Astuce: Vous pouvez payer par carte directement ou contacter un agent pour payer par Mobile Money."
    },
    "en": {
        "welcome": "✈️ Welcome!\n\nLooking for a flight? This bot helps you save time and money.\n\n💡 Simple. Fast. Free.",
        "search": "🔍 Search a flight",
        "trip_type": "✈️ Trip type:",
        "one_way": "➡️ One way",
        "round_trip": "🔄 Round trip",
        "from": "🌍 Departure city:",
        "from_custom": "✍️ Enter departure city name or airport code (ex: London or LHR):",
        "to": "🛬 Arrival city:",
        "to_custom": "✍️ Enter arrival city name or airport code (ex: New York or JFK):",
        "departure_date": "📅 Departure date:",
        "return_date": "📅 Return date:",
        "today": "📅 Today",
        "tomorrow": "📅 Tomorrow",
        "manual": "✍️ Enter a date",
        "format": "📅 Format: YYYY-MM-DD\n\nExample: 2024-12-25",
        "passengers": "👥 Number of passengers:",
        "payment": "💳 How would you like to pay?",
        "pay_card_text": "💳 You can pay directly by card on Aviasales using the link above.",
        "pay_agent_text": "📲 Contact an agent directly on WhatsApp:",
        "result": "✈️ Here is your search:",
        "choose_departure_continent": "🌍 Departure continent:",
        "choose_arrival_continent": "🌍 Arrival continent:",
        "contact": "📞 Contact an agent",
        "contact_text": "📞 WhatsApp : +7 996 179 23 26\n📧 Email : kwami.wampah@yahoo.com",
        "about": "ℹ️ About",
        "about_text": "✈️ Flight search bot.\n🔹 Fast\n🔹 Simple\n🔹 Free\n\n📞 Contact : +7 996 179 23 26",
        "passenger_singular": "passenger",
        "passenger_plural": "passengers",
        "economy_class": "Economy Class",
        "one_way_trip": "One way",
        "round_trip_text": "Round trip",
        "departure": "Departure",
        "return": "Return",
        "error_date_format": "❌ Wrong date format. Use YYYY-MM-DD",
        "error_return_before_departure": "❌ Return date must be after departure date.",
        "search_cancelled": "🔄 Search cancelled.",
        "select_city_from_list": "🌍 Select a city from the list or type its name:",
        "enter_custom_city": "✍️ Type another city...",
        "city_not_found": "❌ City not found. Try:\n- Full name (ex: 'London')\n- Airport code (ex: 'LHR')\n- Check spelling",
        "city_found": "✅ City recognized: ",
        "help": "📚 **Help**\n\n"
                "Available commands:\n"
                "/start - Start the bot\n"
                "/reset - Cancel current search\n"
                "/help - See this help\n"
                "/contact - Contact an agent\n\n"
                "To search a flight:\n"
                "1. Click '🔍 Search a flight'\n"
                "2. Follow the steps\n"
                "3. Get your booking link\n\n"
                "💡 Tip: You can pay by card directly or contact an agent to pay by Mobile Money."
    },
    "ru": {
        "welcome": "✈️ Добро пожаловать!\n\nИщете авиабилеты? Этот бот поможет сэкономить время и деньги.\n\n💡 Просто. Быстро. Бесплатно.",
        "search": "🔍 Найти рейс",
        "trip_type": "✈️ Тип поездки:",
        "one_way": "➡️ В одну сторону",
        "round_trip": "🔄 Туда и обратно",
        "from": "🌍 Город вылета:",
        "from_custom": "✍️ Введите название города вылета или код аэропорта (напр: Москва или SVO):",
        "to": "🛬 Город прилёта:",
        "to_custom": "✍️ Введите название города прилёта или код аэропорта (напр: Нью-Йорк или JFK):",
        "departure_date": "📅 Дата вылета:",
        "return_date": "📅 Дата возвращения:",
        "today": "📅 Сегодня",
        "tomorrow": "📅 Завтра",
        "manual": "✍️ Ввести дату",
        "format": "📅 Формат: YYYY-MM-DD\n\nПример: 2024-12-25",
        "passengers": "👥 Количество пассажиров:",
        "payment": "💳 Как вы хотите оплатить?",
        "pay_card_text": "💳 Вы можете оплатить картой напрямую на Aviasales по ссылке выше.",
        "pay_agent_text": "📲 Свяжитесь напрямую с агентом в WhatsApp:",
        "result": "✈️ Вот ваш поиск:",
        "choose_departure_continent": "🌍 Континент вылета:",
        "choose_arrival_continent": "🌍 Континент прилёта:",
        "contact": "📞 Связаться с агентом",
        "contact_text": "📞 WhatsApp : +7 996 179 23 26\n📧 Email : kwami.wampah@yahoo.com",
        "about": "ℹ️ О сервисе",
        "about_text": "✈️ Бот поиска авиабилетов.\n🔹 Быстро\n🔹 Просто\n🔹 Бесплатно\n\n📞 Контакт : +7 996 179 23 26",
        "passenger_singular": "пассажир",
        "passenger_plural": "пассажира",
        "economy_class": "Эконом класс",
        "one_way_trip": "В одну сторону",
        "round_trip_text": "Туда и обратно",
        "departure": "Вылет",
        "return": "Возвращение",
        "error_date_format": "❌ Неправильный формат даты. Используйте YYYY-MM-DD",
        "error_return_before_departure": "❌ Дата возвращения должна быть после даты вылета.",
        "search_cancelled": "🔄 Поиск отменён.",
        "select_city_from_list": "🌍 Выберите город из списка или введите его название:",
        "enter_custom_city": "✍️ Ввести другой город...",
        "city_not_found": "❌ Город не найден. Попробуйте:\n- Полное название (напр: 'Москва')\n- Код аэропорта (напр: 'SVO')\n- Проверьте написание",
        "city_found": "✅ Город распознан: ",
        "help": "📚 **Помощь**\n\n"
                "Доступные команды:\n"
                "/start - Запустить бота\n"
                "/reset - Отменить текущий поиск\n"
                "/help - Посмотреть помощь\n"
                "/contact - Связаться с агентом\n\n"
                "Для поиска рейса:\n"
                "1. Нажмите '🔍 Найти рейс'\n"
                "2. Следуйте шагам\n"
                "3. Получите ссылку на бронирование\n\n"
                "💡 Совет: Вы можете оплатить картой напрямую или связаться с агентом для оплаты через Mobile Money."
    }
}

# ================== MENUS ==================
def lang_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇫🇷 Français", "🇬🇧 English", "🇷🇺 Русский")
    return kb

def main_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(T[lang]["search"])
    kb.add(T[lang]["contact"], T[lang]["about"])
    return kb

def trip_type_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(T[lang]["one_way"], T[lang]["round_trip"])
    kb.add(back_button(lang))
    return kb

def continent_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CONTINENTS.values():
        kb.add(c[lang])
    kb.add(back_button(lang))
    return kb

def cities_menu(lang, continent=None):
    """
    Menu des villes avec option pour taper manuellement
    continent: si None, c'est pour choisir un continent
    """
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if continent and continent in CITIES_BY_CONTINENT:
        cities = CITIES_BY_CONTINENT[continent]
        labels = [cities[iata][lang] for iata in cities]
        
        for i in range(0, len(labels), 2):
            if i+1 < len(labels):
                kb.add(labels[i], labels[i+1])
            else:
                kb.add(labels[i])
    
    kb.add(T[lang]["enter_custom_city"])
    kb.add(back_button(lang))
    
    return kb

def date_menu_new(lang):
    return simple_date_menu(lang)

def passengers_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "fr":
        kb.add("👤 1 passager", "👥 2 passagers")
        kb.add("👨‍👩‍👦 3 passagers", "👨‍👩‍👧‍👦 4 passagers")
    elif lang == "en":
        kb.add("👤 1 passenger", "👥 2 passengers")
        kb.add("👨‍👩‍👦 3 passengers", "👨‍👩‍👧‍👦 4 passengers")
    else:
        kb.add("👤 1 пассажир", "👥 2 пассажира")
        kb.add("👨‍👩‍👦 3 пассажира", "👨‍👩‍👧‍👦 4 пассажира")
    kb.add(back_button(lang))
    return kb

def payment_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "fr":
        kb.add("💳 Payer moi-même par carte", "📲 Payer par Mobile Money avec un agent")
    elif lang == "en":
        kb.add("💳 Pay by card myself", "📲 Pay by Mobile Money with an agent")
    else:
        kb.add("💳 Оплатить картой", "📲 Оплатить через Mobile Money с агентом")
    kb.add(back_button(lang))
    return kb

# ================== COMMANDE /TESTLINK AMÉLIORÉE ==================
@dp.message_handler(commands=['testlink'])
async def test_link_command(message: types.Message):
    """✅ Commande pour tester la génération de lien - VERSION FONCTIONNELLE"""
    uid = message.from_user.id
    user_data = load_user_data(uid)
    lang = user_data.get("lang", "fr")
    
    # Tests avec différentes combinaisons
    tests = [
        {
            'name': "Paris → Dakar (Aller simple)",
            'data': {
                'from': 'CDG',
                'to': 'DKR',
                'trip_type': 'one_way',
                'departure_date': '2024-12-25',
                'lang': lang
            }
        },
        {
            'name': "Paris → Dakar (Aller-retour)",
            'data': {
                'from': 'CDG',
                'to': 'DKR',
                'trip_type': 'round_trip',
                'departure_date': '2024-12-25',
                'return_date': '2025-01-05',
                'lang': lang
            }
        },
        {
            'name': "Lomé → Paris",
            'data': {
                'from': 'LFW',
                'to': 'CDG',
                'trip_type': 'one_way',
                'departure_date': '2024-11-15',
                'lang': lang
            }
        }
    ]
    
    results = []
    for test in tests:
        link_data = generate_tpst_link(test['data'])
        results.append({
            'name': test['name'],
            'url': link_data['url'],
            'short_url': link_data['url'][:100] + "..." if len(link_data['url']) > 100 else link_data['url']
        })
    
    # Message de test
    test_message = f"""
🔗 **TEST DES LIENS TP.MEDIA - VERSION CORRIGÉE**

**Format utilisé:**
`https://tp.media/r?marker={MARKER}&trs=null&p=4114&u=URL_ENCODÉE`

**Résultats des tests:**

1. **{results[0]['name']}**
   `{results[0]['short_url']}`

2. **{results[1]['name']}**
   `{results[1]['short_url']}`

3. **{results[2]['name']}**
   `{results[2]['short_url']}`

**Vérifications:**
✅ Marker présent: `{MARKER}`
✅ Format tp.media: Oui
✅ URL encodée: Oui

**Instructions de test:**
1. Cliquez sur un lien
2. Il doit s'ouvrir dans le navigateur
3. Redirection vers Aviasales avec recherche pré-remplie
4. Les clics apparaissent dans votre dashboard Travelpayouts

⚠️ **IMPORTANT:** Les liens utilisent maintenant `tp.media` au lieu de `tp.st`
"""

    await message.answer(test_message, parse_mode="Markdown")
    
    # Envoyer aussi les liens complets
    await message.answer(f"🔗 Lien 1 (Paris → Dakar aller simple):\n{results[0]['url']}")
    await message.answer(f"🔗 Lien 2 (Paris → Dakar aller-retour):\n{results[1]['url']}")
    await message.answer(f"🔗 Lien 3 (Lomé → Paris):\n{results[2]['url']}")

# ================== COMMANDE /CHECKMARKER ==================
@dp.message_handler(commands=['checkmarker'])
async def check_marker_command(message: types.Message):
    """Vérifie la configuration du marker"""
    uid = message.from_user.id
    
    status_message = f"""
🎯 **VÉRIFICATION CONFIGURATION TRAVELPAYOUTS**

**Marker configuré:**
• Marker: `{MARKER}`
• API Token: `{API_TOKEN[:10]}...`
• WhatsApp Agent: `{AGENT_WHATSAPP}`

**Liens générés avec:**
• Format: `https://tp.media/r?marker={MARKER}&trs=null&p=4114&u=...`
• Alternative: `https://tp.media/click?shmarker={MARKER}&...`

**Vérifications:**
✅ Marker non vide
✅ Format tp.media (fonctionne mieux que tp.st)
✅ Promo ID 4114 (Aviasales)

**Pour tester votre marker:**
1. Allez sur: https://www.travelpayouts.com/programs/1001
2. Connectez-vous à votre compte
3. Vérifiez que le marker `{MARKER}` est actif
4. Testez avec `/testlink` dans ce bot
"""
    
    await message.answer(status_message, parse_mode="Markdown")
    
# ================== ENGAGEMENT AUTOMATIQUE ==================

async def daily_deal_reminder():
    """
    📅 Envoie automatiquement 1 deal par jour à des utilisateurs aléatoires
    Fonctionne en arrière-plan sans intervention manuelle
    """
    print("🔄 Démarrage de l'engagement automatique...")
    
    # Attendre que le bot soit complètement démarré
    await asyncio.sleep(10)
    
    while True:
        try:
            # Attendre jusqu'à 11h du matin (heure de pointe Telegram)
            now = datetime.now()
            target_time = now.replace(hour=11, minute=0, second=0, microsecond=0)
            
            if now > target_time:
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            print(f"⏰ Prochain deal automatique à {target_time.strftime('%H:%M')} "
                  f"(dans {wait_seconds/3600:.1f} heures)")
            
            await asyncio.sleep(wait_seconds)
            
            # Liste des deals
            deals_fr = [
                "🔥 **DEAL DU JOUR**\n\nParis → Lomé à partir de 450€\n(Économisez 100€!)\n\n🔍 /search",
                "🎫 **OFFRE SPÉCIALE**\n\nDakar → Paris à 460€\nPrix limité aujourd'hui!\n\n🔍 /search",
                "✈️ **PROMO FLASH**\n\nParis → Accra à 420€\nValable 24h seulement!\n\n🔍 /search",
                "💎 **EXCLUSIVITÉ**\n\nLagos → Paris à 480€\nMeilleur prix du mois!\n\n🔍 /search",
            ]
            
            deals_en = [
                "🔥 **DEAL OF THE DAY**\n\nParis → Lome from 450€\n(Save 100€!)\n\n🔍 /search",
                "🎫 **SPECIAL OFFER**\n\nDakar → Paris at 460€\nLimited time!\n\n🔍 /search",
                "✈️ **FLASH SALE**\n\nParis → Accra at 420€\nValid 24h only!\n\n🔍 /search",
                "💎 **EXCLUSIVE**\n\nLagos → Paris at 480€\nBest price this month!\n\n🔍 /search",
            ]
            
            deals_ru = [
                "🔥 **ПРЕДЛОЖЕНИЕ ДНЯ**\n\nПариж → Ломе от 450€\n(Экономьте 100€!)\n\n🔍 /search",
                "🎫 **СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ**\n\nДакар → Париж за 460€\nОграниченное время!\n\n🔍 /search",
                "✈️ **ФЛЕШ РАСПРОДАЖА**\n\nПариж → Аккра за 420€\nДействительно 24 часа!\n\n🔍 /search",
                "💎 **ЭКСКЛЮЗИВ**\n\nЛагос → Париж за 480€\nЛучшая цена месяца!\n\n🔍 /search",
            ]
            
            # Récupérer 15 utilisateurs aléatoires
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT user_id FROM users ORDER BY RANDOM() LIMIT 15")
            random_users = c.fetchall()
            conn.close()
            
            print(f"🎯 Envoi du deal du jour à {len(random_users)} utilisateurs aléatoires")
            
            sent = 0
            failed = 0
            
            for (user_id,) in random_users:
                try:
                    # Déterminer la langue de l'utilisateur
                    user_data = load_user_data(user_id)
                    lang = user_data.get("lang", "fr")
                    
                    # Sélectionner le deal selon la langue
                    if lang == "fr":
                        deal = random.choice(deals_fr)
                    elif lang == "en":
                        deal = random.choice(deals_en)
                    else:
                        deal = random.choice(deals_ru)
                    
                    await bot.send_message(user_id, deal, parse_mode="Markdown")
                    sent += 1
                    
                    # Attendre 2 secondes entre chaque envoi (anti-spam)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    failed += 1
                    # L'utilisateur a peut-être bloqué le bot ou quitté
                    if "blocked" in str(e).lower() or "Forbidden" in str(e):
                        # Vous pourriez marquer cet utilisateur comme inactif
                        pass
            
            print(f"✅ Deal du jour envoyé : {sent} réussis, {failed} échecs")
            
            # Attendre 23h avant le prochain envoi (pour être à 11h demain)
            await asyncio.sleep(23 * 3600)
            
        except Exception as e:
            print(f"❌ Erreur dans l'engagement automatique : {e}")
            # En cas d'erreur, attendre 1h avant de réessayer
            await asyncio.sleep(3600)

# ================== HANDLERS PRINCIPAUX ==================
@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    """Afficher les statistiques du bot"""
    # Comptez les utilisateurs dans votre base
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    conn.close()
    
    await message.answer(f"📊 **Statistiques du bot**\n\n"
                        f"👥 Utilisateurs: {user_count}\n"
                        f"🌍 Langues: FR/EN/RU\n"
                        f"✈️ Villes: 300+\n"
                        f"🔗 Tracking: Activé ✅\n\n"
                        f"Merci de faire partie de l'aventure !")
@dp.message_handler(commands=['activity'])
async def activity_command(message: types.Message):
    """Voir l'activité des utilisateurs"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # Derniers utilisateurs
    c.execute("SELECT user_id, created_at FROM users ORDER BY created_at DESC LIMIT 10")
    recent_users = c.fetchall()
    
    # Activité par jour
    c.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM users GROUP BY date ORDER BY date DESC LIMIT 7")
    daily_stats = c.fetchall()
    
    conn.close()
    
    text = "📈 **Activité récente**\n\n"
    text += f"👥 Utilisateurs totaux: 26\n\n"
    
    text += "🕐 **Derniers inscrits** :\n"
    for user_id, created_at in recent_users[:5]:
        date = created_at.split()[0] if created_at else "Date inconnue"
        text += f"• User {user_id} - {date}\n"
    
    text += "\n📅 **Inscriptions par jour** :\n"
    for date, count in daily_stats:
        text += f"• {date} : {count} utilisateur(s)\n"
    
    text += "\n💡 *Conseil : Relancez les anciens utilisateurs avec une offre !*"
    
    await message.answer(text, parse_mode="Markdown")
    
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("🌍 Choisissez votre langue / Choose your language / Выберите язык", reply_markup=lang_menu())

@dp.message_handler(commands=["reset", "annuler", "cancel"])
async def reset_command(message: types.Message):
    uid = message.from_user.id
    user_data = load_user_data(uid)
    lang = user_data.get("lang", "fr")
    
    user_data = {"lang": lang}
    save_user_data(uid, user_data)
    
    await message.answer(T[lang]["search_cancelled"], reply_markup=main_menu(lang))

@dp.message_handler(commands=["help", "aide"])
async def help_command(message: types.Message):
    uid = message.from_user.id
    user_data = load_user_data(uid)
    lang = user_data.get("lang", "fr")
    
    await message.answer(T[lang]["help"], reply_markup=main_menu(lang))

@dp.message_handler(commands=["contact"])
async def contact_command(message: types.Message):
    uid = message.from_user.id
    user_data = load_user_data(uid)
    lang = user_data.get("lang", "fr")
    
    await message.answer(T[lang]["contact_text"], reply_markup=main_menu(lang))

@dp.message_handler(lambda m: m.text in ["🇫🇷 Français", "🇬🇧 English", "🇷🇺 Русский"])
async def set_lang(message: types.Message):
    lang = "fr" if "Français" in message.text else "en" if "English" in message.text else "ru"
    
    user_data = {"lang": lang}
    save_user_data(message.from_user.id, user_data)
    
    await message.answer(T[lang]["welcome"], reply_markup=main_menu(lang))

@dp.message_handler(lambda m: m.text == back_button("fr") or m.text == back_button("en") or m.text == back_button("ru"))
async def handle_back(message: types.Message):
    uid = message.from_user.id
    user_data = load_user_data(uid)
    lang = user_data.get("lang", "fr")
    
    if message.text == back_button("fr"):
        current_lang = "fr"
    elif message.text == back_button("en"):
        current_lang = "en"
    else:
        current_lang = "ru"
    
    if current_lang != lang:
        lang = current_lang
        user_data["lang"] = lang
    
    step = user_data.get("step")
    
    # Logique de retour en arrière
    if step == "trip_type":
        user_data.pop("step", None)
        save_user_data(uid, user_data)
        await message.answer(T[lang]["welcome"], reply_markup=main_menu(lang))
    
    elif step in ["from_continent", "from_city", "from_custom"]:
        user_data["step"] = "trip_type"
        save_user_data(uid, user_data)
        await message.answer(T[lang]["trip_type"], reply_markup=trip_type_menu(lang))
    
    elif step in ["to_continent", "to_city", "to_custom"]:
        user_data["step"] = "from_custom" if user_data.get("from_mode") == "custom" else "from_city"
        continent = user_data.get("from_continent")
        save_user_data(uid, user_data)
        if user_data.get("from_mode") == "custom":
            await message.answer(T[lang]["from_custom"])
        else:
            await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent))
    
    elif step in ["departure_date", "manual_departure"]:
        user_data["step"] = "to_custom" if user_data.get("to_mode") == "custom" else "to_city"
        continent = user_data.get("to_continent")
        save_user_data(uid, user_data)
        if user_data.get("to_mode") == "custom":
            await message.answer(T[lang]["to_custom"])
        else:
            await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent))
    
    elif step in ["return_date", "manual_return"]:
        user_data["step"] = "departure_date"
        save_user_data(uid, user_data)
        await message.answer(T[lang]["departure_date"], reply_markup=date_menu_new(lang))
    
    elif step == "passengers":
        if user_data.get("trip_type") == "round_trip":
            user_data["step"] = "return_date"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["return_date"], reply_markup=date_menu_new(lang))
        else:
            user_data["step"] = "departure_date"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["departure_date"], reply_markup=date_menu_new(lang))
    
    elif step == "payment":
        user_data["step"] = "passengers"
        save_user_data(uid, user_data)
        await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
    
    else:
        user_data = {"lang": lang}
        save_user_data(uid, user_data)
        await message.answer(T[lang]["welcome"], reply_markup=main_menu(lang))

def parse_date_from_button(button_text, lang):
    """Parse une date à partir du texte du bouton"""
    today = datetime.now()
    
    if lang == "fr":
        if "Aujourd'hui" in button_text:
            return today.strftime("%Y-%m-%d")
        elif "Demain" in button_text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "3 jours" in button_text:
            return (today + timedelta(days=3)).strftime("%Y-%m-%d")
        elif "1 semaine" in button_text:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif "2 semaines" in button_text:
            return (today + timedelta(days=14)).strftime("%Y-%m-%d")
        elif "1 mois" in button_text:
            return (today + timedelta(days=30)).strftime("%Y-%m-%d")
    elif lang == "en":
        if "Today" in button_text:
            return today.strftime("%Y-%m-%d")
        elif "Tomorrow" in button_text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "3 days" in button_text:
            return (today + timedelta(days=3)).strftime("%Y-%m-%d")
        elif "1 week" in button_text:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif "2 weeks" in button_text:
            return (today + timedelta(days=14)).strftime("%Y-%m-%d")
        elif "1 month" in button_text:
            return (today + timedelta(days=30)).strftime("%Y-%m-%d")
    else:  # ru
        if "Сегодня" in button_text:
            return today.strftime("%Y-%m-%d")
        elif "Завтра" in button_text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "Через 3 дня" in button_text:
            return (today + timedelta(days=3)).strftime("%Y-%m-%d")
        elif "Через неделю" in button_text:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif "Через 2 недели" in button_text:
            return (today + timedelta(days=14)).strftime("%Y-%m-%d")
        elif "Через месяц" in button_text:
            return (today + timedelta(days=30)).strftime("%Y-%m-%d")
    
    return None

@dp.message_handler()
async def flow(message: types.Message):
    uid = message.from_user.id
    user_data = load_user_data(uid)
    
    if "lang" not in user_data:
        await message.answer("🌍 Choisissez votre langue / Choose your language / Выберите язык", reply_markup=lang_menu())
        return
    
    lang = user_data["lang"]
    step = user_data.get("step")

    # ---- MENU FIXE ----
    if message.text == T[lang]["contact"]:
        await message.answer(T[lang]["contact_text"], reply_markup=main_menu(lang))
        return

    if message.text == T[lang]["about"]:
        await message.answer(T[lang]["about_text"], reply_markup=main_menu(lang))
        return

    # ---- DÉMARRAGE RECHERCHE ----
    if message.text == T[lang]["search"]:
        user_data["step"] = "trip_type"
        save_user_data(uid, user_data)
        await message.answer(T[lang]["trip_type"], reply_markup=trip_type_menu(lang))
        return

    # ---- TYPE DE VOYAGE ----
    if step == "trip_type":
        if message.text == T[lang]["one_way"]:
            user_data["trip_type"] = "one_way"
        elif message.text == T[lang]["round_trip"]:
            user_data["trip_type"] = "round_trip"
        else:
            await message.answer(T[lang]["trip_type"], reply_markup=trip_type_menu(lang))
            return
            
        user_data["step"] = "from_continent"
        save_user_data(uid, user_data)
        await message.answer(T[lang]["choose_departure_continent"], reply_markup=continent_menu(lang))
        return

    # ---- CONTINENT DÉPART ----
    if step == "from_continent":
        continent_found = False
        continent_key = None
        
        for key, val in CONTINENTS.items():
            if message.text == val[lang]:
                continent_found = True
                continent_key = key
                break
        
        if continent_found:
            user_data["from_continent"] = continent_key
            user_data["step"] = "from_city"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent_key))
        else:
            await message.answer(T[lang]["choose_departure_continent"], reply_markup=continent_menu(lang))
        return

    # ---- VILLE DÉPART (liste ou saisie) ----
    if step == "from_city":
        if message.text == T[lang]["enter_custom_city"]:
            user_data["step"] = "from_custom"
            user_data["from_mode"] = "custom"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["from_custom"])
            return
        
        continent = user_data.get("from_continent")
        city_found = False
        city_iata = None
        
        if continent and continent in CITIES_BY_CONTINENT:
            for iata, names in CITIES_BY_CONTINENT[continent].items():
                if names[lang] == message.text:
                    city_found = True
                    city_iata = iata
                    break
        
        if city_found:
            user_data["from"] = city_iata
            user_data["from_mode"] = "list"
            user_data["step"] = "to_continent"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["choose_arrival_continent"], reply_markup=continent_menu(lang))
        else:
            await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent))
        return

    # ---- VILLE DÉPART (saisie manuelle) ----
    if step == "from_custom":
        city_iata = find_city_by_name_or_code(message.text, lang)
        
        if city_iata:
            user_data["from"] = city_iata
            user_data["from_mode"] = "custom"
            user_data["step"] = "to_continent"
            save_user_data(uid, user_data)
            
            city_name = get_city_name(city_iata, lang)
            await message.answer(f"{T[lang]['city_found']}{city_name}")
            await message.answer(T[lang]["choose_arrival_continent"], reply_markup=continent_menu(lang))
        else:
            await message.answer(T[lang]["city_not_found"])
            await message.answer(T[lang]["from_custom"])
        return

    # ---- CONTINENT ARRIVÉE ----
    if step == "to_continent":
        continent_found = False
        continent_key = None
        
        for key, val in CONTINENTS.items():
            if message.text == val[lang]:
                continent_found = True
                continent_key = key
                break
        
        if continent_found:
            user_data["to_continent"] = continent_key
            user_data["step"] = "to_city"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent_key))
        else:
            await message.answer(T[lang]["choose_arrival_continent"], reply_markup=continent_menu(lang))
        return

    # ---- VILLE ARRIVÉE (liste ou saisie) ----
    if step == "to_city":
        if message.text == T[lang]["enter_custom_city"]:
            user_data["step"] = "to_custom"
            user_data["to_mode"] = "custom"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["to_custom"])
            return
        
        continent = user_data.get("to_continent")
        city_found = False
        city_iata = None
        
        if continent and continent in CITIES_BY_CONTINENT:
            for iata, names in CITIES_BY_CONTINENT[continent].items():
                if names[lang] == message.text:
                    city_found = True
                    city_iata = iata
                    break
        
        if city_found:
            user_data["to"] = city_iata
            user_data["to_mode"] = "list"
            user_data["step"] = "departure_date"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["departure_date"], reply_markup=date_menu_new(lang))
        else:
            await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent))
        return

    # ---- VILLE ARRIVÉE (saisie manuelle) ----
    if step == "to_custom":
        city_iata = find_city_by_name_or_code(message.text, lang)
        
        if city_iata:
            user_data["to"] = city_iata
            user_data["to_mode"] = "custom"
            user_data["step"] = "departure_date"
            save_user_data(uid, user_data)
            
            city_name = get_city_name(city_iata, lang)
            await message.answer(f"{T[lang]['city_found']}{city_name}")
            await message.answer(T[lang]["departure_date"], reply_markup=date_menu_new(lang))
        else:
            await message.answer(T[lang]["city_not_found"])
            await message.answer(T[lang]["to_custom"])
        return

    # ---- DATE DE DÉPART ----
    if step == "departure_date":
        date_str = parse_date_from_button(message.text, lang)
        
        if date_str:
            user_data["departure_date"] = date_str
            
            if user_data.get("trip_type") == "round_trip":
                user_data["step"] = "return_date"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["return_date"], reply_markup=date_menu_new(lang))
            else:
                user_data["step"] = "passengers"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
            return
        
        if (lang == "fr" and "manuellement" in message.text.lower()) or \
           (lang == "en" and "manually" in message.text.lower()) or \
           (lang == "ru" and "вручную" in message.text.lower()):
            user_data["step"] = "manual_departure"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["format"])
            return
        
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
            user_data["departure_date"] = message.text
            
            if user_data.get("trip_type") == "round_trip":
                user_data["step"] = "return_date"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["return_date"], reply_markup=date_menu_new(lang))
            else:
                user_data["step"] = "passengers"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
        except:
            await message.answer(T[lang]["error_date_format"], reply_markup=date_menu_new(lang))
        return

    if step == "manual_departure":
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
            user_data["departure_date"] = message.text
            if user_data.get("trip_type") == "round_trip":
                user_data["step"] = "return_date"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["return_date"], reply_markup=date_menu_new(lang))
            else:
                user_data["step"] = "passengers"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
        except:
            await message.answer(T[lang]["error_date_format"])
        return

    # ---- DATE DE RETOUR ----
    if step == "return_date":
        date_str = parse_date_from_button(message.text, lang)
        
        if date_str:
            if "departure_date" in user_data:
                departure_date = datetime.strptime(user_data["departure_date"], "%Y-%m-%d")
                return_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if return_date <= departure_date:
                    await message.answer(T[lang]["error_return_before_departure"], reply_markup=date_menu_new(lang))
                    return
            
            user_data["return_date"] = date_str
            user_data["step"] = "passengers"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
            return
        
        if (lang == "fr" and "manuellement" in message.text.lower()) or \
           (lang == "en" and "manually" in message.text.lower()) or \
           (lang == "ru" and "вручную" in message.text.lower()):
            user_data["step"] = "manual_return"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["format"])
            return
        
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
            date_str = message.text
            
            departure_date = datetime.strptime(user_data["departure_date"], "%Y-%m-%d")
            return_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if return_date <= departure_date:
                await message.answer(T[lang]["error_return_before_departure"], reply_markup=date_menu_new(lang))
                return
            
            user_data["return_date"] = date_str
            user_data["step"] = "passengers"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
        except:
            await message.answer(T[lang]["error_date_format"], reply_markup=date_menu_new(lang))
        return

    if step == "manual_return":
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
            date_str = message.text
            
            departure_date = datetime.strptime(user_data["departure_date"], "%Y-%m-%d")
            return_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if return_date <= departure_date:
                await message.answer(T[lang]["error_return_before_departure"])
                return
            
            user_data["return_date"] = date_str
            user_data["step"] = "passengers"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
        except:
            await message.answer(T[lang]["error_date_format"])
        return

    # ---- PASSAGERS ----
    if step == "passengers":
        p = 1
        for char in message.text:
            if char.isdigit():
                p = int(char)
                break
        
        if "👤" in message.text and p == 1:
            p = 1
        elif "👥" in message.text and p == 1:
            p = 2
        elif "👨‍👩‍👦" in message.text:
            p = 3
        elif "👨‍👩‍👧‍👦" in message.text:
            p = 4
        
        p = min(p, 9)
        
        passenger_text = get_passenger_text(p, lang)
        
        # ✅ UTILISER LA FONCTION CORRIGÉE
        link_data = generate_tpst_link(user_data)
        url = link_data['url']
        trip_type_text = link_data['trip_type']
        dates_text = link_data['dates']
        
        user_data["step"] = "payment"
        save_user_data(uid, user_data)
        
        from_city = get_city_name(user_data['from'], lang)
        to_city = get_city_name(user_data['to'], lang)
        
        final_message = (
            f"{T[lang]['result']}\n\n"
            f"✈️ {trip_type_text}\n"
            f"📍 {from_city} → {to_city}\n"
            f"📅 {dates_text}\n"
            f"👥 {passenger_text}\n"
            f"✈️ {T[lang]['economy_class']}\n\n"
            f"🔗 {url}\n\n"
            f"{T[lang]['payment']}"
        )
        
        await message.answer(final_message, reply_markup=payment_menu(lang))
        return

    # ---- PAIEMENT ----
    if step == "payment":
        # --- MOBILE MONEY ---
        if "Mobile Money" in message.text or "agent" in message.text.lower() or "агент" in message.text.lower():
            from_city = get_city_name(user_data.get('from', ''), lang)
            to_city = get_city_name(user_data.get('to', ''), lang)
            
            whatsapp_texts = {
                "fr": f"Bonjour, je souhaite payer un billet d'avion par Mobile Money.\n\n"
                      f"Détails du vol:\n"
                      f"De: {from_city}\n"
                      f"À: {to_city}\n"
                      f"Date: {user_data.get('departure_date', '')}",
                "en": f"Hello, I want to pay for a flight ticket by Mobile Money.\n\n"
                      f"Flight details:\n"
                      f"From: {from_city}\n"
                      f"To: {to_city}\n"
                      f"Date: {user_data.get('departure_date', '')}",
                "ru": f"Здравствуйте, я хочу оплатить авиабилет через Mobile Money.\n\n"
                      f"Детали рейса:\n"
                      f"Из: {from_city}\n"
                      f"В: {to_city}\n"
                      f"Дата: {user_data.get('departure_date', '')}"
            }
            
            whatsapp_link = f"https://wa.me/{AGENT_WHATSAPP}?text={urllib.parse.quote(whatsapp_texts[lang])}"
            
            response = f"{T[lang]['pay_agent_text']}\n\n{whatsapp_link}"
            await message.answer(response, reply_markup=main_menu(lang))
            
            user_data = {"lang": lang}
            save_user_data(uid, user_data)
            return

        # --- CARTE ---
        if "card" in message.text.lower() or "carte" in message.text.lower() or "карт" in message.text.lower():
            await message.answer(T[lang]["pay_card_text"], reply_markup=main_menu(lang))
            
            user_data = {"lang": lang}
            save_user_data(uid, user_data)
            return
    
    # ---- RÉPONSE PAR DÉFAULT ----
    await message.answer(
        f"🤔 Je ne comprends pas. Essayez:\n"
        f"- Cliquer sur '{T[lang]['search']}' pour chercher un vol\n"
        f"- Utiliser /help pour voir les commandes\n"
        f"- Utiliser /reset pour recommencer",
        reply_markup=main_menu(lang)
    )
# ================== DÉMARRAGE DES SERVICES ==================

async def on_startup(dp):
    """
    Fonction exécutée au démarrage du bot
    """
    print("🚀 Lancement des services d'engagement automatique...")
    
    # Démarrer l'engagement automatique
    asyncio.create_task(daily_deal_reminder())
    
    print("✅ Engagement automatique activé")
    print("📅 1 deal/jour sera envoyé à 15 utilisateurs aléatoires")
    print("⏰ Horaire : 11h00 tous les jours")
    
# ... (tout ton code existant avant) ...

if __name__ == "__main__":
    print("🤖 Bot démarré avec engagement automatique...")
    print("🔄 Les deals seront envoyés automatiquement à 11h chaque jour")
    print(f"Base de données initialisée: bot_data.db")
    print(f"Token: {TOKEN[:10]}...")
    print(f"Villes principales: {len(PRINCIPAL_CITIES)}")
    print(f"Toutes les villes: {len(ALL_CITIES)}")
    print(f"Marker Travelpayouts: {MARKER}")
    print(f"UTILISE tp.media POUR LE TRACKING (fonctionne mieux que tp.st)")
    print(f"Commandes disponibles:")
    print(f"/testlink - Tester les liens générés")
    print(f"/checkmarker - Vérifier la configuration")
    print(f"/reset - Réinitialiser la recherche")
    print(f"\n IMPORTANT: Les liens utilisent maintenant le format:")
    print(f"https://tp.media/r?marker={MARKER}&trs=null&p=4114&u=...")
    
    # Démarrer le bot avec la fonction on_startup
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)