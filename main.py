import json
import telebot
import os
from keep_alive import keep_alive  # Uptime uchun

TOKEN = "TOKEN"
ADMIN_IDS = [374014720, 301474139]

bot = telebot.TeleBot(TOKEN)
ANIME_FILE = "anime.data.json"

# Fayl mavjud bo'lmasa — yaratamiz
if not os.path.exists(ANIME_FILE):
    with open(ANIME_FILE, "w") as f:
        json.dump([], f)

cancel_state = {}

def load_anime():
    with open(ANIME_FILE, "r") as f:
        return json.load(f)

def save_anime(data):
    with open(ANIME_FILE, "w") as f:
        json.dump(data, f, indent=2)

# 🚫 Noto‘g‘ri kontentni bloklash (sticker, photo, audio)
@bot.message_handler(content_types=['sticker', 'photo', 'audio', 'document'])
def unknown_content(message):
    bot.send_message(message.chat.id, "❌ Bu turdagi kontent qo‘llab-quvvatlanmaydi.")

# 🚀 Start menyusi + kod orqali video yuborish
@bot.message_handler(commands=["start"])
def start_menu(message):
    cancel_state[message.chat.id] = False

    args = message.text.strip().split(" ")
    if len(args) > 1:
        code = args[1].lower()
        data = load_anime()
        for anime in data:
            if anime["code"].lower() == code:
                bot.send_message(message.chat.id, f"📺 {anime['name']}")
                for vid in anime.get("parts", [anime["file_id"]]):
                    bot.send_video(message.chat.id, vid)
                return
        bot.send_message(message.chat.id, "❌ Ushbu kod bo‘yicha anime topilmadi.")
        return

    # Oddiy menyu
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎬 Kod bilan anime izlash", "📩 Adminlarga habar yozish")
    if message.from_user.id in ADMIN_IDS:
        kb.row("🎞️ Anime yuklash", "📂 Anime ro'yxati")
    bot.send_message(message.chat.id, "Quyidagi menyudan birini tanlang:", reply_markup=kb)

# ❌ Bekor qilish
@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    cancel_state[message.chat.id] = True
    bot.send_message(message.chat.id, "❌ Amal bekor qilindi. Bosh menyuga qaytildi.")
    start_menu(message)

# 🔎 Kod bilan izlash
@bot.message_handler(func=lambda msg: msg.text == "🎬 Kod bilan anime izlash")
def search_anime_step1(message):
    msg = bot.send_message(message.chat.id, "Kod yozing (yoki /cancel):")
    bot.register_next_step_handler(msg, search_anime_step2)

def search_anime_step2(message):
    if cancel_state.get(message.chat.id): return
    code = message.text.strip()
    data = load_anime()
    for anime in data:
        if anime["code"].lower() == code.lower():
            bot.send_message(message.chat.id, f"📺 {anime['name']}")
            for vid in anime.get("parts", [anime["file_id"]]):
                bot.send_video(message.chat.id, vid)
            return
    bot.send_message(message.chat.id, "❌ Bunday kod topilmadi.")

# 📩 Adminlarga habar
@bot.message_handler(func=lambda msg: msg.text == "📩 Adminlarga habar yozish")
def to_admin_prompt(message):
    msg = bot.send_message(message.chat.id, "✉️ Adminlarga habar matnini yozing (yoki /cancel):")
    bot.register_next_step_handler(msg, forward_to_admins)

def forward_to_admins(message):
    if cancel_state.get(message.chat.id): return
    text = f"📨 Yangi habar:\n\n{message.text}\n\n👤 @{message.from_user.username or message.from_user.first_name} (ID: {message.from_user.id})"
    for admin in ADMIN_IDS:
        bot.send_message(admin, text)
    bot.send_message(message.chat.id, "✅ Habaringiz adminlarga yuborildi.")

# 🎞️ Anime yuklash
@bot.message_handler(func=lambda msg: msg.text == "🎞️ Anime yuklash")
def upload_anime_step1(message):
    if message.from_user.id not in ADMIN_IDS:
        return bot.send_message(message.chat.id, "❌ Bu buyruq faqat adminlar uchun.")
    msg = bot.send_message(message.chat.id, "Anime nomini yozing (yoki /cancel):")
    bot.register_next_step_handler(msg, upload_anime_step2)

ㅤㅤㅤKirito, [26.07.2025 7:18]
def upload_anime_step2(message):
    if cancel_state.get(message.chat.id): return
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Anime kodi:")
    bot.register_next_step_handler(msg, lambda m: upload_anime_step3(m, name))

def upload_anime_step3(message, name):
    if cancel_state.get(message.chat.id): return
    code = message.text.strip()
    msg = bot.send_message(message.chat.id, "🎬 Endi videoni yuboring:")
    bot.register_next_step_handler(msg, lambda m: save_uploaded_anime(m, name, code))

def save_uploaded_anime(message, name, code):
    if cancel_state.get(message.chat.id): return
    if not message.video:
        return bot.send_message(message.chat.id, "❌ Video yuboring.")
    file_id = message.video.file_id
    data = load_anime()
    data.append({"name": name, "code": code, "file_id": file_id, "parts": [file_id]})
    save_anime(data)
    bot.send_message(message.chat.id, f"✅ '{name}' saqlandi.")

# 📂 Anime ro'yxati va tahrirlash
@bot.message_handler(func=lambda msg: msg.text == "📂 Anime ro'yxati")
def show_anime_list(message):
    if message.from_user.id not in ADMIN_IDS:
        return bot.send_message(message.chat.id, "❌ Bu buyruq faqat adminlar uchun.")
    data = load_anime()
    if not data:
        return bot.send_message(message.chat.id, "⛔ Hech qanday anime topilmadi.")

    msg = "📂 Anime ro'yxati:\n"
    for i, a in enumerate(data, 1):
        msg += f"{i}. {a['name']} ({a['code']})\n"
    bot.send_message(message.chat.id, msg)

    msg2 = bot.send_message(message.chat.id, "🔍 Tahrirlash uchun anime nomi yoki kodini yozing (yoki /cancel):")
    bot.register_next_step_handler(msg2, process_selected_anime)

def process_selected_anime(message):
    if cancel_state.get(message.chat.id): return
    code = message.text.strip()
    data = load_anime()
    for anime in data:
        if anime["code"].lower() == code.lower() or anime["name"].lower() == code.lower():
            bot.send_video(message.chat.id, anime["file_id"], caption=f"📺 {anime['name']} ({anime['code']})")

            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("📝 Nomini o‘zgartirish", "🔢 Kodni o‘zgartirish")
            markup.row("📥 Davomini qo‘shish", "❌ To‘liq o‘chirish")
            bot.send_message(message.chat.id, "🛠 Qanday amal bajaramiz?", reply_markup=markup)

            bot.register_next_step_handler(message, lambda m: handle_anime_edit_action(m, anime))
            return

    bot.send_message(message.chat.id, "❌ Anime topilmadi.")

def handle_anime_edit_action(message, anime):
    if cancel_state.get(message.chat.id): return
    action = message.text.strip()
    if action == "📝 Nomini o‘zgartirish":
        msg = bot.send_message(message.chat.id, "✏️ Yangi nomini yozing:")
        bot.register_next_step_handler(msg, lambda m: update_anime_name(m, anime))
    elif action == "🔢 Kodni o‘zgartirish":
        msg = bot.send_message(message.chat.id, "🔢 Yangi kodni yozing:")
        bot.register_next_step_handler(msg, lambda m: update_anime_code(m, anime))
    elif action == "📥 Davomini qo‘shish":
        msg = bot.send_message(message.chat.id, "📥 Yangi videoni yuboring:")
        bot.register_next_step_handler(msg, lambda m: add_anime_part(m, anime))
    elif action == "❌ To‘liq o‘chirish":
        data = load_anime()
        data = [a for a in data if a != anime]
        save_anime(data)
        bot.send_message(message.chat.id, "🗑️ Anime o‘chirildi.")
    else:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri buyruq.")

def update_anime_name(message, anime):
    if cancel_state.get(message.chat.id): return
    new_name = message.text.strip()
    anime["name"] = new_name
    data = load_anime()
    for i, a in enumerate(data):
        if a["code"] == anime["code"]:
            data[i] = anime
            break
    save_anime(data)
    bot.send_message(message.chat.id, f"✅ Nomi yangilandi: {new_name}")

ㅤㅤㅤKirito, [26.07.2025 7:18]
def update_anime_code(message, anime):
    if cancel_state.get(message.chat.id): return
    new_code = message.text.strip()
    anime["code"] = new_code
    data = load_anime()
    for i, a in enumerate(data):
        if a["name"] == anime["name"]:
            data[i] = anime
            break
    save_anime(data)
    bot.send_message(message.chat.id, f"✅ Kodi yangilandi: {new_code}")

def add_anime_part(message, anime):
    if cancel_state.get(message.chat.id): return
    if not message.video:
        return bot.send_message(message.chat.id, "❌ Iltimos, video yuboring.")
    video_id = message.video.file_id
    anime["parts"].append(video_id)
    data = load_anime()
    for i, a in enumerate(data):
        if a["code"] == anime["code"]:
            data[i] = anime
            break
    save_anime(data)
    bot.send_message(message.chat.id, "✅ Davomi saqlandi.")
# 📢 Post yaratish (rasm + matn + tugma)
@bot.message_handler(commands=["post"])
def start_post(message):
    msg = bot.send_message(message.chat.id, "🖼 Rasm yuboring (yoki /cancel):")
    bot.register_next_step_handler(msg, handle_photo)

def handle_photo(message):
    if cancel_state.get(message.chat.id): return
    if not message.photo:
        return bot.send_message(message.chat.id, "❌ Rasm yuboring.")
    photo_id = message.photo[-1].file_id
    msg = bot.send_message(message.chat.id, "📝 Matn kiriting (yoki /cancel):")
    bot.register_next_step_handler(msg, lambda m: handle_caption(m, photo_id))

def handle_caption(message, photo_id):
    if cancel_state.get(message.chat.id): return
    caption = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔗 'Tomosha qilish' tugmasi uchun havola kiriting (yoki /cancel):")
    bot.register_next_step_handler(msg, lambda m: handle_link(m, photo_id, caption))

def handle_link(message, photo_id, caption):
    if cancel_state.get(message.chat.id): return
    link = message.text.strip()
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("▶️ Tomosha qilish", url=link))
    bot.send_photo(message.chat.id, photo_id, caption=caption, reply_markup=markup)

# 🔁 Ishga tushurish
keep_alive()
print("✅ Bot ishga tushdi!")
bot.infinity_polling()
