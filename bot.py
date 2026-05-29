import telebot
from telebot import types
import json
import os
import time

TOKEN = "8915420556:AAE5uZzb4riRJ8g6uPZMuKbTqUOzaV2FADQ"

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "players.json"

SWORDS = [
    ("🪵 Деревянный", 0),
    ("⛓ Железный", 500),
    ("⚫ Угольный", 1600),
    ("💧 Водный", 2800),
    ("💎 Алмазный", 3700),
    ("🔥 Огненный", 5000),
    ("🌑 Теневой", 7000),
    ("⚡ Электро", 10000),
    ("☢️ Ядерный", 15000),
    ("👑 Легендарный", 25000)
]

cooldowns = {}

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_player(user_id):
    data = load_data()

    if str(user_id) not in data:
        data[str(user_id)] = {
            "clicks": 0,
            "power": 1,
            "swords": 0,
            "lang": "ru"
        }
        save_data(data)

    return data[str(user_id)]

def save_player(user_id, player):
    data = load_data()
    data[str(user_id)] = player
    save_data(data)

def get_sword(clicks):
    current = SWORDS[0][0]

    for sword, need in SWORDS:
        if clicks >= need:
            current = sword

    return current

def texts(lang):
    if lang == "en":
        return {
            "click": "⚔ Click",
            "shop": "🛒 Shop",
            "profile": "👤 Profile",
            "top": "🏆 Top",
            "upgrade": "Upgrade +0.1 click for 1 sword coin",
            "not_enough": "Not enough sword coins!",
            "bought": "Upgrade purchased!",
            "welcome": "Welcome to Sword Clicker!"
        }

    return {
        "click": "⚔ Клик",
        "shop": "🛒 Магазин",
        "profile": "👤 Профиль",
        "top": "🏆 Топ",
        "upgrade": "Улучшить +0.1 клик за 1 sword монету",
        "not_enough": "Недостаточно sword монет!",
        "bought": "Улучшение куплено!",
        "welcome": "Добро пожаловать в Sword Clicker!"
    }

def main_menu(lang):
    t = texts(lang)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(t["click"])
    markup.add(t["shop"], t["profile"])
    markup.add(t["top"])

    return markup

@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()

    ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    en = types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")

    markup.add(ru, en)

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в Sword Clicker!\n\nWelcome to Sword Clicker!\n\nВыберите язык / Choose language",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def choose_lang(call):
    lang = call.data.split("_")[1]

    player = get_player(call.from_user.id)
    player["lang"] = lang
    save_player(call.from_user.id, player)

    t = texts(lang)

    bot.send_message(
        call.message.chat.id,
        t["welcome"],
        reply_markup=main_menu(lang)
    )

@bot.message_handler(func=lambda message: True)
def messages(message):
    player = get_player(message.from_user.id)

    lang = player["lang"]
    t = texts(lang)

    text = message.text

    if text == t["click"]:
        now = time.time()

        if message.from_user.id in cooldowns:
            if now - cooldowns[message.from_user.id] < 1:
                return

        cooldowns[message.from_user.id] = now

        player["clicks"] += player["power"]

        if int(player["clicks"]) % 100 == 0:
            player["swords"] += 1

        save_player(message.from_user.id, player)

        sword = get_sword(player["clicks"])

        bot.send_message(
            message.chat.id,
            f"{sword}\n\n⚔ Клики: {round(player['clicks'],1)}\n🪙 Sword: {player['swords']}\n💥 Сила клика: {round(player['power'],1)}"
        )

    elif text == t["shop"]:
        markup = types.InlineKeyboardMarkup()

        btn = types.InlineKeyboardButton(
            t["upgrade"],
            callback_data="upgrade"
        )

        markup.add(btn)

        bot.send_message(
            message.chat.id,
            f"🪙 Sword монет: {player['swords']}",
            reply_markup=markup
        )

    elif text == t["profile"]:
        sword = get_sword(player["clicks"])

        bot.send_message(
            message.chat.id,
            f"""
👤 Профиль

🗡 Меч: {sword}
⚔ Клики: {round(player['clicks'],1)}
🪙 Sword монет: {player['swords']}
💥 Сила клика: {round(player['power'],1)}
"""
        )

    elif text == t["top"]:
        data = load_data()

        top = sorted(
            data.items(),
            key=lambda x: x[1]["clicks"],
            reverse=True
        )

        text_top = "🏆 ТОП ИГРОКОВ\n\n"

        place = 1

        for user_id, info in top[:10]:
        username = info.get("username", "player")
text_top += f"{place}. @{username} — {round(info['clicks'])} кликов\n"
            place += 1

        bot.send_message(message.chat.id, text_top)

@bot.callback_query_handler(func=lambda call: call.data == "upgrade")
def upgrade(call):
    player = get_player(call.from_user.id)

    lang = player["lang"]
    t = texts(lang)

    if player["swords"] >= 1:
        player["swords"] -= 1
        player["power"] += 0.1

        save_player(call.from_user.id, player)

        bot.answer_callback_query(call.id, t["bought"])
    else:
        bot.answer_callback_query(call.id, t["not_enough"])

print("Bot started...")
bot.infinity_polling()
