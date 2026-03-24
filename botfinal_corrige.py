import urllib.parse
import os
import json
import sqlite3
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv
import socket
import aiohttp

# Augmenter le timeout
socket.setdefaulttimeout(60)

# Désactiver les proxies
import os
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

# ================== CONFIGURATION TRAVELPAYOUTS ==================
API_TOKEN = "7cf46628a75a50705c7a6dbdedcc7165"
MARKER = "696220"
AGENT_WHATSAPP = "79961792326"

# Charger les variables d'environnement
load_dotenv()

# Configuration
TOKEN = os.getenv("TELEGRAM_TOKEN", "8443560025:AAEtWwc0vsQt7Dwc2mtiFI-DwybWshBu0IA")

bot = Bot(token=TOKEN, request_timeout=60)
dp = Dispatcher(bot)

# ================== BASE DE DONNÉES ==================
def init_db():
    """Initialiser la base de données SQLite"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  data TEXT, 
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
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

# Initialiser la base de données
init_db()

# ================== VILLES PRINCIPALES ==================
PRINCIPAL_CITIES = {
    # Afrique
    "LFW": {"fr": "Lomé (LFW)", "en": "Lome (LFW)", "ru": "Ломе (LFW)"},
    "COO": {"fr": "Cotonou (COO)", "en": "Cotonou (COO)", "ru": "Котону (COO)"},
    "ACC": {"fr": "Accra (ACC)", "en": "Accra (ACC)", "ru": "Аккра (ACC)"},
    "LOS": {"fr": "Lagos (LOS)", "en": "Lagos (LOS)", "ru": "Лагос (LOS)"},
    "ABJ": {"fr": "Abidjan (ABJ)", "en": "Abidjan (ABJ)", "ru": "Абиджан (ABJ)"},
    "DKR": {"fr": "Dakar (DKR)", "en": "Dakar (DKR)", "ru": "Дакар (DKR)"},
    "CAI": {"fr": "Le Caire (CAI)", "en": "Cairo (CAI)", "ru": "Каир (CAI)"},
    "JNB": {"fr": "Johannesburg (JNB)", "en": "Johannesburg (JNB)", "ru": "Йоханнесбург (JNB)"},
    
    # Europe
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
    
    # Russie
    "SVO": {"fr": "Moscou (SVO)", "en": "Moscow (SVO)", "ru": "Москва (SVO)"},
    "DME": {"fr": "Moscou (SVO)", "en": "Moscow (DME)", "ru": "Москва (DME)"},
    "LED": {"fr": "Saint-Pétersbourg (LED)", "en": "Saint Petersburg (LED)", "ru": "Санкт-Петербург (LED)"},
    "KZN": {"fr": "Kazan (KZN)", "en": "Kazan (KZN)", "ru": "Казань (KZN)"},
    "SVX": {"fr": "Ekaterinbourg (SVX)", "en": "Yekaterinburg (SVX)", "ru": "Екатеринбург (SVX)"},
    "OVB": {"fr": "Novossibirsk (OVB)", "en": "Novosibirsk (OVB)", "ru": "Новосибирск (OVB)"},
    
    # Asie
    "BKK": {"fr": "Bangkok (BKK)", "en": "Bangkok (BKK)", "ru": "Бангкок (BKK)"},
    "NRT": {"fr": "Tokyo (NRT)", "en": "Tokyo (NRT)", "ru": "Токио (NRT)"},
    "DXB": {"fr": "Dubaï (DXB)", "en": "Dubai (DXB)", "ru": "Дубай (DXB)"},
    "ICN": {"fr": "Séoul (ICN)", "en": "Seoul (ICN)", "ru": "Сеул (ICN)"},
    "PEK": {"fr": "Pékin (PEK)", "en": "Beijing (PEK)", "ru": "Пекин (PEK)"},
    "SIN": {"fr": "Singapour (SIN)", "en": "Singapore (SIN)", "ru": "Сингапур (SIN)"},
    "DEL": {"fr": "New Delhi (DEL)", "en": "New Delhi (DEL)", "ru": "Нью-Дели (DEL)"},
    "HKT": {"fr": "Phuket (HKT)", "en": "Phuket (HKT)", "ru": "Пхукет (HKT)"},
    
    # Amérique
    "JFK": {"fr": "New York (JFK)", "en": "New York (JFK)", "ru": "Нью-Йорк (JFK)"},
    "YUL": {"fr": "Montréal (YUL)", "en": "Montreal (YUL)", "ru": "Монреаль (YUL)"},
    "YYZ": {"fr": "Toronto (YYZ)", "en": "Toronto (YYZ)", "ru": "Торонто (YYZ)"},
    "MEX": {"fr": "Mexico (MEX)", "en": "Mexico City (MEX)", "ru": "Мехико (MEX)"},
    "GRU": {"fr": "São Paulo (GRU)", "en": "São Paulo (GRU)", "ru": "Сан-Паулу (GRU)"},
    "EZE": {"fr": "Buenos Aires (EZE)", "en": "Buenos Aires (EZE)", "ru": "Буэнос-Айрес (EZE)"},
    "LAX": {"fr": "Los Angeles (LAX)", "en": "Los Angeles (LAX)", "ru": "Лос-Анджелес (LAX)"},
    "MIA": {"fr": "Miami (MIA)", "en": "Miami (MIA)", "ru": "Майами (MIA)"},
    
    # Océanie
    "SYD": {"fr": "Sydney (SYD)", "en": "Sydney (SYD)", "ru": "Сидней (SYD)"},
    "MEL": {"fr": "Melbourne (MEL)", "en": "Melbourne (MEL)", "ru": "Мельбурн (MEL)"},
    "AKL": {"fr": "Auckland (AKL)", "en": "Auckland (AKL)", "ru": "Окленд (AKL)"},
    "BNE": {"fr": "Brisbane (BNE)", "en": "Brisbane (BNE)", "ru": "Брисбен (BNE)"},
    "PER": {"fr": "Perth (PER)", "en": "Perth (PER)", "ru": "Перт (PER)"},
}

# ================== BASE DE DONNÉES COMPLÈTE ==================
ALL_CITIES = {
    **PRINCIPAL_CITIES,
    # Ajout de villes supplémentaires essentielles
    "BKO": {"fr": "Bamako", "en": "Bamako", "ru": "Бамако"},
    "OUA": {"fr": "Ouagadougou", "en": "Ouagadougou", "ru": "Уагадугу"},
    "NIM": {"fr": "Niamey", "en": "Niamey", "ru": "Ниамей"},
    "NDJ": {"fr": "N'Djamena", "en": "N'Djamena", "ru": "Нджамена"},
    "ORY": {"fr": "Paris Orly", "en": "Paris Orly", "ru": "Париж Орли"},
    "LYS": {"fr": "Lyon", "en": "Lyon", "ru": "Лион"},
    "MRS": {"fr": "Marseille", "en": "Marseille", "ru": "Марсель"},
    "NCE": {"fr": "Nice", "en": "Nice", "ru": "Ницца"},
    "TLS": {"fr": "Toulouse", "en": "Toulouse", "ru": "Тулуза"},
    "BOD": {"fr": "Bordeaux", "en": "Bordeaux", "ru": "Бордо"},
    "MUC": {"fr": "Munich", "en": "Munich", "ru": "Мюнхен"},
    "FRA": {"fr": "Francfort", "en": "Frankfurt", "ru": "Франкфурт"},
    "HAM": {"fr": "Hambourg", "en": "Hamburg", "ru": "Гамбург"},
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
    "africa": {k: PRINCIPAL_CITIES[k] for k in ["LFW", "COO", "ACC", "LOS", "ABJ", "DKR", "CAI", "JNB"]},
    "europe": {k: PRINCIPAL_CITIES[k] for k in ["CDG", "LHR", "BRU", "MAD", "FCO", "BER", "AMS", "IST", "ZRH", "BCN"]},
    "russia": {k: PRINCIPAL_CITIES[k] for k in ["SVO", "LED", "KZN", "SVX", "OVB"]},
    "asia": {k: PRINCIPAL_CITIES[k] for k in ["BKK", "NRT", "DXB", "ICN", "PEK", "SIN", "DEL", "HKT"]},
    "america": {k: PRINCIPAL_CITIES[k] for k in ["JFK", "YUL", "YYZ", "MEX", "GRU", "EZE", "LAX", "MIA"]},
    "oceania": {k: PRINCIPAL_CITIES[k] for k in ["SYD", "MEL", "AKL", "BNE", "PER"]},
}

# ================== FONCTIONS UTILITAIRES ==================
def get_city_name(iata_code, lang):
    """Récupère le nom d'une ville"""
    if iata_code in PRINCIPAL_CITIES:
        name_with_code = PRINCIPAL_CITIES[iata_code].get(lang, iata_code)
        return name_with_code.split('(')[0].strip()
    elif iata_code in ALL_CITIES:
        return ALL_CITIES[iata_code].get(lang, iata_code)
    return iata_code

def find_city_by_name_or_code(input_text, lang):
    """Trouve une ville par son nom ou code IATA"""
    input_text = input_text.upper().strip()
    
    if input_text in ALL_CITIES:
        return input_text
    
    search_text = input_text.lower()
    
    for code, names in PRINCIPAL_CITIES.items():
        city_name = names[lang].lower()
        city_name_only = city_name.split('(')[0].strip().lower()
        if search_text in city_name or search_text in city_name_only:
            return code
    
    for code, names in ALL_CITIES.items():
        city_name = names[lang].lower()
        if search_text in city_name:
            return code
    
    return None

def back_button(lang):
    texts = {"fr": "🔙 Retour", "en": "🔙 Back", "ru": "🔙 Назад"}
    return texts[lang]

def get_passenger_text(p, lang):
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

# ================== FONCTION GÉNÉRATION LIENS ==================
def generate_tpst_link(user_data):
    """Génère un lien d'affiliation Travelpayouts qui fonctionne"""
    trip_type = user_data.get("trip_type", "one_way")
    origin = user_data['from']
    destination = user_data['to']
    
    if trip_type == "one_way":
        base_url = (f"https://www.aviasales.com/search?"
                   f"origin={origin}&destination={destination}&"
                   f"depart_date={user_data['departure_date']}&"
                   f"adults=1&children=0&infants=0")
    else:
        base_url = (f"https://www.aviasales.com/search?"
                   f"origin={origin}&destination={destination}&"
                   f"depart_date={user_data['departure_date']}&"
                   f"return_date={user_data['return_date']}&"
                   f"adults=1&children=0&infants=0")
    
    encoded_url = urllib.parse.quote_plus(base_url)
    tpst_link = f"https://tp.media/r?marker={MARKER}&p=4114&u={encoded_url}"
    
    lang = user_data.get("lang", "fr")
    if lang == "fr":
        trip_type_text = "Aller simple" if trip_type == "one_way" else "Aller-retour"
    elif lang == "en":
        trip_type_text = "One way" if trip_type == "one_way" else "Round trip"
    else:
        trip_type_text = "В одну сторону" if trip_type == "one_way" else "Туда и обратно"
    
    dates_text = user_data['departure_date'] if trip_type == "one_way" else f"{user_data['departure_date']} - {user_data['return_date']}"
    
    return {'url': tpst_link, 'trip_type': trip_type_text, 'dates': dates_text}

# ================== TEXTS ==================
T = {
    "fr": {
        "welcome": "✈️ Bienvenue !\n\nTu cherches un billet d'avion ? Ce bot te fait gagner du temps et de l'argent.\n\n💡 Simple. Rapide. Gratuit.",
        "search": "🔍 Rechercher un vol",
        "trip_type": "✈️ Type de voyage :",
        "one_way": "➡️ Aller simple",
        "round_trip": "🔄 Aller-retour",
        "from_custom": "✍️ Entrez le nom de la ville de départ ou son code aéroport :",
        "to_custom": "✍️ Entrez le nom de la ville d'arrivée ou son code aéroport :",
        "departure_date": "📅 Date de départ :",
        "return_date": "📅 Date de retour :",
        "format": "📅 Format : YYYY-MM-DD\n\nExemple : 2024-12-25",
        "passengers": "👥 Nombre de passagers :",
        "payment": "💳 Comment souhaitez-vous payer ?",
        "pay_card_text": "💳 Payez directement par carte sur Aviasales via le lien ci-dessus.",
        "pay_agent_text": "📲 Contactez un agent sur WhatsApp :",
        "result": "✈️ Voici votre recherche :",
        "choose_departure_continent": "🌍 Continent de départ :",
        "choose_arrival_continent": "🌍 Continent d'arrivée :",
        "contact": "📞 Contacter un agent",
        "contact_text": "📞 WhatsApp : +7 996 179 23 26\n📧 Email : kwami.wampah@yahoo.com",
        "about": "ℹ️ À propos",
        "about_text": "✈️ Bot de recherche de billets d'avion.\n🔹 Rapide\n🔹 Simple\n🔹 Gratuit\n\n📞 Contact : +7 996 179 23 26",
        "economy_class": "Classe Économique",
        "error_date_format": "❌ Format de date incorrect. Utilisez YYYY-MM-DD",
        "error_return_before_departure": "❌ La date de retour doit être après la date d'aller.",
        "search_cancelled": "🔄 Recherche annulée.",
        "select_city_from_list": "🌍 Sélectionnez une ville :",
        "enter_custom_city": "✍️ Taper une autre ville...",
        "city_not_found": "❌ Ville non trouvée.",
        "city_found": "✅ Ville reconnue : ",
        "help": "📚 **Aide**\n\nCommandes: /start, /reset, /help, /contact, /activity, /stats"
    },
    "en": {
        "welcome": "✈️ Welcome!\n\nLooking for a flight? Simple. Fast. Free.",
        "search": "🔍 Search a flight",
        "trip_type": "✈️ Trip type:",
        "one_way": "➡️ One way",
        "round_trip": "🔄 Round trip",
        "from_custom": "✍️ Enter departure city or airport code:",
        "to_custom": "✍️ Enter arrival city or airport code:",
        "departure_date": "📅 Departure date:",
        "return_date": "📅 Return date:",
        "format": "📅 Format: YYYY-MM-DD\n\nExample: 2024-12-25",
        "passengers": "👥 Number of passengers:",
        "payment": "💳 How would you like to pay?",
        "pay_card_text": "💳 Pay by card on Aviasales via the link above.",
        "pay_agent_text": "📲 Contact an agent on WhatsApp:",
        "result": "✈️ Your search:",
        "choose_departure_continent": "🌍 Departure continent:",
        "choose_arrival_continent": "🌍 Arrival continent:",
        "contact": "📞 Contact an agent",
        "contact_text": "📞 WhatsApp: +7 996 179 23 26\n📧 Email: kwami.wampah@yahoo.com",
        "about": "ℹ️ About",
        "about_text": "✈️ Flight search bot.\n🔹 Fast\n🔹 Simple\n🔹 Free",
        "economy_class": "Economy Class",
        "error_date_format": "❌ Wrong date format. Use YYYY-MM-DD",
        "error_return_before_departure": "❌ Return date must be after departure.",
        "search_cancelled": "🔄 Search cancelled.",
        "select_city_from_list": "🌍 Select a city:",
        "enter_custom_city": "✍️ Type another city...",
        "city_not_found": "❌ City not found.",
        "city_found": "✅ City recognized: ",
        "help": "📚 **Help**\n\nCommands: /start, /reset, /help, /contact, /activity, /stats"
    },
    "ru": {
        "welcome": "✈️ Добро пожаловать!\n\nИщете авиабилеты? Просто. Быстро. Бесплатно.",
        "search": "🔍 Найти рейс",
        "trip_type": "✈️ Тип поездки:",
        "one_way": "➡️ В одну сторону",
        "round_trip": "🔄 Туда и обратно",
        "from_custom": "✍️ Введите город вылета или код аэропорта:",
        "to_custom": "✍️ Введите город прилёта или код аэропорта:",
        "departure_date": "📅 Дата вылета:",
        "return_date": "📅 Дата возвращения:",
        "format": "📅 Формат: YYYY-MM-DD\n\nПример: 2024-12-25",
        "passengers": "👥 Количество пассажиров:",
        "payment": "💳 Как оплатить?",
        "pay_card_text": "💳 Оплатите картой на Aviasales по ссылке выше.",
        "pay_agent_text": "📲 Свяжитесь с агентом в WhatsApp:",
        "result": "✈️ Ваш поиск:",
        "choose_departure_continent": "🌍 Континент вылета:",
        "choose_arrival_continent": "🌍 Континент прилёта:",
        "contact": "📞 Связаться с агентом",
        "contact_text": "📞 WhatsApp: +7 996 179 23 26\n📧 Email: kwami.wampah@yahoo.com",
        "about": "ℹ️ О сервисе",
        "about_text": "✈️ Бот поиска авиабилетов.\n🔹 Быстро\n🔹 Просто\n🔹 Бесплатно",
        "economy_class": "Эконом класс",
        "error_date_format": "❌ Неправильный формат даты. Используйте YYYY-MM-DD",
        "error_return_before_departure": "❌ Дата возвращения должна быть после вылета.",
        "search_cancelled": "🔄 Поиск отменён.",
        "select_city_from_list": "🌍 Выберите город:",
        "enter_custom_city": "✍️ Ввести другой город...",
        "city_not_found": "❌ Город не найден.",
        "city_found": "✅ Город распознан: ",
        "help": "📚 **Помощь**\n\nКоманды: /start, /reset, /help, /contact, /activity, /stats"
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

def continent_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CONTINENTS.values():
        kb.add(c[lang])
    kb.add(back_button(lang))
    return kb

def cities_menu(lang, continent=None):
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

def date_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    today = datetime.now()
    kb.add(f"📅 Aujourd'hui ({today.strftime('%d/%m')})")
    kb.add(f"📅 Demain ({(today + timedelta(days=1)).strftime('%d/%m')})")
    kb.add(f"📅 +7 jours ({(today + timedelta(days=7)).strftime('%d/%m')})")
    kb.add(T[lang]["enter_custom_city"])
    kb.add(back_button(lang))
    return kb

def passengers_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "fr":
        kb.add("👤 1", "👥 2")
        kb.add("👨‍👩‍👦 3", "👨‍👩‍👧‍👦 4")
    elif lang == "en":
        kb.add("👤 1", "👥 2")
        kb.add("👨‍👩‍👦 3", "👨‍👩‍👧‍👦 4")
    else:
        kb.add("👤 1", "👥 2")
        kb.add("👨‍👩‍👦 3", "👨‍👩‍👧‍👦 4")
    kb.add(back_button(lang))
    return kb

def payment_menu(lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "fr":
        kb.add("💳 Carte bancaire", "📲 Mobile Money")
    elif lang == "en":
        kb.add("💳 Credit card", "📲 Mobile Money")
    else:
        kb.add("💳 Банковская карта", "📲 Mobile Money")
    kb.add(back_button(lang))
    return kb

# ================== COMMANDES STATS ==================
@dp.message_handler(commands=['activity'])
async def activity_command(message: types.Message):
    """Voir l'activité des utilisateurs"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_id, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    conn.close()
    
    text = "📈 **Activité récente**\n\n"
    text += f"👥 Utilisateurs totaux: {len(users)}\n\n"
    text += "🕐 **Derniers inscrits** :\n"
    for user_id, created_at in users[:5]:
        date = created_at.split()[0] if created_at else "Date inconnue"
        text += f"• ID {user_id} - {date}\n"
    text += "\n💡 *Continuez à partager le bot !*"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    """Statistiques du bot"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    
    await message.answer(
        f"📊 **Statistiques Midzo**\n\n"
        f"👥 Utilisateurs: **{count}**\n"
        f"✈️ Villes disponibles: **{len(ALL_CITIES)}**\n"
        f"🌍 Langues: FR/EN/RU\n"
        f"🔗 Tracking Travelpayouts: ✅\n\n"
        f"💡 *Partagez le bot pour faire grandir la communauté !*",
        parse_mode="Markdown"
    )

# ================== HANDLERS PRINCIPAUX ==================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("🌍 Choisissez votre langue / Choose your language / Выберите язык", reply_markup=lang_menu())

@dp.message_handler(commands=["reset"])
async def reset_command(message: types.Message):
    uid = message.from_user.id
    user_data = load_user_data(uid)
    lang = user_data.get("lang", "fr")
    user_data = {"lang": lang}
    save_user_data(uid, user_data)
    await message.answer(T[lang]["search_cancelled"], reply_markup=main_menu(lang))

@dp.message_handler(commands=["help"])
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

@dp.message_handler()
async def flow(message: types.Message):
    uid = message.from_user.id
    user_data = load_user_data(uid)
    
    if "lang" not in user_data:
        await start(message)
        return
    
    lang = user_data["lang"]
    step = user_data.get("step")
    
    # Menu fixe
    if message.text == T[lang]["contact"]:
        await message.answer(T[lang]["contact_text"], reply_markup=main_menu(lang))
        return
    
    if message.text == T[lang]["about"]:
        await message.answer(T[lang]["about_text"], reply_markup=main_menu(lang))
        return
    
    if message.text == T[lang]["search"]:
        user_data["step"] = "trip_type"
        save_user_data(uid, user_data)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(T[lang]["one_way"], T[lang]["round_trip"])
        kb.add(back_button(lang))
        await message.answer(T[lang]["trip_type"], reply_markup=kb)
        return
    
    # Type de voyage
    if step == "trip_type":
        if message.text == T[lang]["one_way"]:
            user_data["trip_type"] = "one_way"
        elif message.text == T[lang]["round_trip"]:
            user_data["trip_type"] = "round_trip"
        else:
            return
        
        user_data["step"] = "from_continent"
        save_user_data(uid, user_data)
        await message.answer(T[lang]["choose_departure_continent"], reply_markup=continent_menu(lang))
        return
    
    # Continent départ
    if step == "from_continent":
        for key, val in CONTINENTS.items():
            if message.text == val[lang]:
                user_data["from_continent"] = key
                user_data["step"] = "from_city"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, key))
                return
        return
    
    # Ville départ (liste)
    if step == "from_city":
        if message.text == T[lang]["enter_custom_city"]:
            user_data["step"] = "from_custom"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["from_custom"])
            return
        
        continent = user_data.get("from_continent")
        for iata, names in CITIES_BY_CONTINENT.get(continent, {}).items():
            if names[lang] == message.text:
                user_data["from"] = iata
                user_data["step"] = "to_continent"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["choose_arrival_continent"], reply_markup=continent_menu(lang))
                return
        
        await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent))
        return
    
    # Ville départ (custom)
    if step == "from_custom":
        iata = find_city_by_name_or_code(message.text, lang)
        if iata:
            user_data["from"] = iata
            user_data["step"] = "to_continent"
            save_user_data(uid, user_data)
            city_name = get_city_name(iata, lang)
            await message.answer(f"{T[lang]['city_found']}{city_name}")
            await message.answer(T[lang]["choose_arrival_continent"], reply_markup=continent_menu(lang))
        else:
            await message.answer(T[lang]["city_not_found"])
            await message.answer(T[lang]["from_custom"])
        return
    
    # Continent arrivée
    if step == "to_continent":
        for key, val in CONTINENTS.items():
            if message.text == val[lang]:
                user_data["to_continent"] = key
                user_data["step"] = "to_city"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, key))
                return
        return
    
    # Ville arrivée (liste)
    if step == "to_city":
        if message.text == T[lang]["enter_custom_city"]:
            user_data["step"] = "to_custom"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["to_custom"])
            return
        
        continent = user_data.get("to_continent")
        for iata, names in CITIES_BY_CONTINENT.get(continent, {}).items():
            if names[lang] == message.text:
                user_data["to"] = iata
                user_data["step"] = "departure_date"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["departure_date"], reply_markup=date_menu(lang))
                return
        
        await message.answer(T[lang]["select_city_from_list"], reply_markup=cities_menu(lang, continent))
        return
    
    # Ville arrivée (custom)
    if step == "to_custom":
        iata = find_city_by_name_or_code(message.text, lang)
        if iata:
            user_data["to"] = iata
            user_data["step"] = "departure_date"
            save_user_data(uid, user_data)
            city_name = get_city_name(iata, lang)
            await message.answer(f"{T[lang]['city_found']}{city_name}")
            await message.answer(T[lang]["departure_date"], reply_markup=date_menu(lang))
        else:
            await message.answer(T[lang]["city_not_found"])
            await message.answer(T[lang]["to_custom"])
        return
    
    # Date de départ
    if step == "departure_date":
        if message.text == T[lang]["enter_custom_city"]:
            user_data["step"] = "manual_departure"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["format"])
            return
        
        if "Aujourd'hui" in message.text or "Today" in message.text or "Сегодня" in message.text:
            date = datetime.now().strftime("%Y-%m-%d")
        elif "Demain" in message.text or "Tomorrow" in message.text or "Завтра" in message.text:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "+7" in message.text or "7 jours" in message.text:
            date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(message.text, "%Y-%m-%d")
                date = message.text
            except:
                await message.answer(T[lang]["error_date_format"])
                return
        
        user_data["departure_date"] = date
        
        if user_data.get("trip_type") == "round_trip":
            user_data["step"] = "return_date"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["return_date"], reply_markup=date_menu(lang))
        else:
            user_data["step"] = "passengers"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
        return
    
    # Date retour
    if step == "return_date":
        if message.text == T[lang]["enter_custom_city"]:
            user_data["step"] = "manual_return"
            save_user_data(uid, user_data)
            await message.answer(T[lang]["format"])
            return
        
        if "Aujourd'hui" in message.text or "Today" in message.text or "Сегодня" in message.text:
            date = datetime.now().strftime("%Y-%m-%d")
        elif "Demain" in message.text or "Tomorrow" in message.text or "Завтра" in message.text:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "+7" in message.text or "7 jours" in message.text:
            date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(message.text, "%Y-%m-%d")
                date = message.text
            except:
                await message.answer(T[lang]["error_date_format"])
                return
        
        user_data["return_date"] = date
        user_data["step"] = "passengers"
        save_user_data(uid, user_data)
        await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
        return
    
    # Date manuelle
    if step in ["manual_departure", "manual_return"]:
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
            if step == "manual_departure":
                user_data["departure_date"] = message.text
                if user_data.get("trip_type") == "round_trip":
                    user_data["step"] = "return_date"
                    save_user_data(uid, user_data)
                    await message.answer(T[lang]["return_date"], reply_markup=date_menu(lang))
                else:
                    user_data["step"] = "passengers"
                    save_user_data(uid, user_data)
                    await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
            else:
                user_data["return_date"] = message.text
                user_data["step"] = "passengers"
                save_user_data(uid, user_data)
                await message.answer(T[lang]["passengers"], reply_markup=passengers_menu(lang))
        except:
            await message.answer(T[lang]["error_date_format"])
        return
    
    # Passagers
    if step == "passengers":
        p = 1
        for char in message.text:
            if char.isdigit():
                p = int(char)
                break
        
        if p > 4:
            p = 4
        
        passenger_text = get_passenger_text(p, lang)
        
        # Générer le lien
        link_data = generate_tpst_link(user_data)
        
        from_city = get_city_name(user_data['from'], lang)
        to_city = get_city_name(user_data['to'], lang)
        
        final_message = (
            f"{T[lang]['result']}\n\n"
            f"✈️ {link_data['trip_type']}\n"
            f"📍 {from_city} → {to_city}\n"
            f"📅 {link_data['dates']}\n"
            f"👥 {passenger_text}\n"
            f"✈️ {T[lang]['economy_class']}\n\n"
            f"🔗 {link_data['url']}\n\n"
            f"{T[lang]['payment']}"
        )
        
        user_data["step"] = "payment"
        save_user_data(uid, user_data)
        
        await message.answer(final_message, reply_markup=payment_menu(lang))
        return
    
    # Paiement
    if step == "payment":
        if "carte" in message.text.lower() or "card" in message.text.lower() or "карт" in message.text.lower():
            await message.answer(T[lang]["pay_card_text"], reply_markup=main_menu(lang))
            user_data = {"lang": lang}
            save_user_data(uid, user_data)
        
        elif "mobile" in message.text.lower() or "agent" in message.text.lower() or "агент" in message.text.lower():
            whatsapp_link = f"https://wa.me/{AGENT_WHATSAPP}?text=Bonjour, je souhaite réserver un vol."
            await message.answer(f"{T[lang]['pay_agent_text']}\n\n{whatsapp_link}", reply_markup=main_menu(lang))
            user_data = {"lang": lang}
            save_user_data(uid, user_data)
        return
    
    # Bouton retour
    if message.text == back_button(lang):
        if step in ["from_continent", "from_city", "from_custom"]:
            user_data = {"lang": lang}
            save_user_data(uid, user_data)
            await message.answer(T[lang]["welcome"], reply_markup=main_menu(lang))
        else:
            user_data.pop("step", None)
            save_user_data(uid, user_data)
            await message.answer(T[lang]["welcome"], reply_markup=main_menu(lang))
        return

# ================== ENGAGEMENT AUTOMATIQUE ==================
async def daily_deal_reminder():
    """Envoie automatiquement des deals tous les jours à 11h"""
    print("🔄 Démarrage de l'engagement automatique...")
    await asyncio.sleep(10)
    
    deals_fr = [
        "🔥 **DEAL DU JOUR**\n\nParis → Lomé à partir de 450€\n(Économisez 100€!)\n\n🔍 /search",
        "🎫 **OFFRE SPÉCIALE**\n\nDakar → Paris à 460€\nPrix limité!\n\n🔍 /search",
        "✈️ **PROMO FLASH**\n\nParis → Accra à 420€\nValable 24h!\n\n🔍 /search",
    ]
    
    while True:
        try:
            now = datetime.now()
            target = now.replace(hour=11, minute=0, second=0, microsecond=0)
            if now > target:
                target += timedelta(days=1)
            
            wait = (target - now).total_seconds()
            print(f"⏰ Prochain deal à {target.strftime('%H:%M')} (dans {wait/3600:.1f}h)")
            await asyncio.sleep(wait)
            
            conn = sqlite3.connect('bot_data.db')
            c = conn.cursor()
            c.execute("SELECT user_id FROM users ORDER BY RANDOM() LIMIT 10")
            users = c.fetchall()
            conn.close()
            
            print(f"🎯 Envoi à {len(users)} utilisateurs")
            sent = 0
            
            for (uid,) in users:
                try:
                    user_data = load_user_data(uid)
                    lang = user_data.get("lang", "fr")
                    deal = random.choice(deals_fr) if lang == "fr" else random.choice(deals_fr)
                    await bot.send_message(uid, deal, parse_mode="Markdown")
                    sent += 1
                    await asyncio.sleep(2)
                except:
                    pass
            
            print(f"✅ Deal envoyé à {sent} utilisateurs")
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            await asyncio.sleep(3600)

# ================== DÉMARRAGE ==================
async def on_startup(dp):
    print("🚀 Bot Midzo démarré!")
    print(f"👥 Utilisateurs actuels: {len(load_user_data)}")
    print("📅 Engagement automatique activé (11h chaque jour)")
    asyncio.create_task(daily_deal_reminder())

if __name__ == "__main__":
    print("🤖 MIDZO - Bot de recherche de vols")
    print("✅ Liens Travelpayouts: tp.media")
    print("🔧 Commandes: /start, /help, /activity, /stats")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)