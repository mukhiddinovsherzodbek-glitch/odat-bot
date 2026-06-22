import os
import json
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")

START_DATE = date(2026, 6, 22)

HABITS = [
    {"id": "erta_turish",   "label": "🌅 Erta turish",    "note": "3:40 da"},
    {"id": "bomdod",        "label": "🕌 Bomdod",          "note": ""},
    {"id": "otjimaniya",    "label": "💪 Otjimaniya",      "note": "15 ta"},
    {"id": "pres",          "label": "🔥 Pres",            "note": "15 ta"},
    {"id": "otirib_turish", "label": "🦵 O'tirib turish",  "note": "15 ta"},
    {"id": "peshin",        "label": "🕌 Peshin",          "note": ""},
    {"id": "asr",           "label": "🕌 Asr",             "note": ""},
    {"id": "tarix",         "label": "📚 Tarix o'qish",    "note": "5 ta mavzu"},
    {"id": "shaxmat",       "label": "♟️ Shaxmat",         "note": ""},
    {"id": "shom",          "label": "🕌 Shom",            "note": ""},
    {"id": "vibe_coding",   "label": "💻 Vibe Coding",     "note": "30 min"},
    {"id": "xufton",        "label": "🕌 Xufton",          "note": ""},
    {"id": "vitr",          "label": "🌙 Vitr Vojib",      "note": ""},
    {"id": "erta_uxlash",   "label": "😴 Erta uxlash",     "note": "23:00 gacha"},
]

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_state(data, hid, day_idx):
    return data.get(f"{hid}_{day_idx}", "")

def get_today_idx():
    today = date.today()
    delta = (today - START_DATE).days
    if delta < 0:
        return 1
    if delta >= 30:
        return 30
    return delta + 1

def day_score(data, idx):
    done = sum(1 for h in HABITS if get_state(data, h["id"], idx) == "done")
    return round(done / len(HABITS) * 100)

def state_icon(st):
    return "✅" if st == "done" else "❌" if st == "fail" else "⬜"

def next_state(st):
    return "done" if st == "" else "fail" if st == "done" else ""

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Odat Tracker Botga xush kelibsiz!*\n\n"
        "📅 /bugun — bugungi odatlar\n"
        "📊 /stats — statistika\n"
        "📋 /jadval — 30 kunlik jadval\n"
        "ℹ️ /help — yordam"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def bugun(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    idx = get_today_idx()
    today = date.today()
    score = day_score(data, idx)

    text = f"📅 *{today.day}-{today.strftime('%B')} · {idx}-kun*\n"
    text += f"Bajarildi: *{score}%*\n\n"
    text += "Bosib holatini o'zgartir:\n⬜ bo'sh → ✅ bajarildi → ❌ bajarilmadi"

    keyboard = []
    for h in HABITS:
        st = get_state(data, h["id"], idx)
        icon = state_icon(st)
        note = f" ({h['note']})" if h["note"] else ""
        label = f"{icon} {h['label']}{note}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"toggle_{h['id']}_{idx}")])

    keyboard.append([InlineKeyboardButton("🔄 Yangilash", callback_data=f"refresh_{idx}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    idx = get_today_idx()
    text = "📊 *Statistika*\n\n"

    for h in HABITS:
        cnt = sum(1 for d in range(1, 31) if get_state(data, h["id"], d) == "done")
        pct = round(cnt / 30 * 100)
        streak = 0
        for i in range(idx, 0, -1):
            if get_state(data, h["id"], i) == "done":
                streak += 1
            else:
                break
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        text += f"{h['label']}\n`{bar}` {cnt}/30"
        if streak > 0:
            text += f" 🔥{streak}"
        text += "\n\n"

    overall = round(sum(
        1 for h in HABITS for d in range(1, 31)
        if get_state(data, h["id"], d) == "done"
    ) / (len(HABITS) * 30) * 100)
    text += f"*Umumiy: {overall}%*"

    await update.message.reply_text(text, parse_mode="Markdown")

async def jadval(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    idx = get_today_idx()
    text = "📋 *30 Kunlik Jadval*\n\n"

    for h in HABITS:
        row = h["label"] + "\n"
        for d in range(1, 31):
            st = get_state(data, h["id"], d)
            if d == idx:
                row += "👆" if st == "" else ("✅" if st == "done" else "❌")
            else:
                row += "✅" if st == "done" else ("❌" if st == "fail" else "⬜")
        text += row + "\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    if query.data.startswith("toggle_"):
        parts = query.data.split("_", 2)
        hid = parts[1]
        didx = int(parts[2])
        key = f"{hid}_{didx}"
        cur = data.get(key, "")
        data[key] = next_state(cur)
        save_data(data)

        # Refresh the message
        score = day_score(data, didx)
        today = date.today()
        text = f"📅 *{today.day}-{today.strftime('%B')} · {didx}-kun*\n"
        text += f"Bajarildi: *{score}%*\n\n"
        text += "Bosib holatini o'zgartir:\n⬜ bo'sh → ✅ bajarildi → ❌ bajarilmadi"

        keyboard = []
        for h in HABITS:
            st = get_state(data, h["id"], didx)
            icon = state_icon(st)
            note = f" ({h['note']})" if h["note"] else ""
            label = f"{icon} {h['label']}{note}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"toggle_{h['id']}_{didx}")])
        keyboard.append([InlineKeyboardButton("🔄 Yangilash", callback_data=f"refresh_{didx}")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data.startswith("refresh_"):
        didx = int(query.data.split("_")[1])
        score = day_score(data, didx)
        today = date.today()
        text = f"📅 *{today.day}-{today.strftime('%B')} · {didx}-kun*\n"
        text += f"Bajarildi: *{score}%*\n\n"
        text += "Bosib holatini o'zgartir:\n⬜ bo'sh → ✅ bajarildi → ❌ bajarilmadi"

        keyboard = []
        for h in HABITS:
            st = get_state(data, h["id"], didx)
            icon = state_icon(st)
            note = f" ({h['note']})" if h["note"] else ""
            label = f"{icon} {h['label']}{note}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"toggle_{h['id']}_{didx}")])
        keyboard.append([InlineKeyboardButton("🔄 Yangilash", callback_data=f"refresh_{didx}")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *Yordam*\n\n"
        "/bugun — bugungi odatlarni ko'rish va belgilash\n"
        "/stats — har bir odat statistikasi\n"
        "/jadval — 30 kunlik to'liq jadval\n\n"
        "Har bir tugmaga bosing: ⬜→✅→❌→⬜"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bugun", bugun))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("jadval", jadval))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
