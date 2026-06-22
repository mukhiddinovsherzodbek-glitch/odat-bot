import os
import json
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "")

START_DATE = date(2026, 6, 22)

HABITS = [
    {"id": "erta_turish",    "label": "🌅 Erta turish",    "note": "3:40 da"},
    {"id": "bomdod",         "label": "🕌 Bomdod",          "note": ""},
    {"id": "otjimaniya",     "label": "💪 Otjimaniya",      "note": "15 ta"},
    {"id": "pres",           "label": "🔥 Pres",            "note": "15 ta"},
    {"id": "otirib_turish",  "label": "🦵 O'tirib turish",  "note": "15 ta"},
    {"id": "peshin",         "label": "🕌 Peshin",          "note": ""},
    {"id": "asr",            "label": "🕌 Asr",             "note": ""},
    {"id": "tarix",          "label": "📚 Tarix o'qish",    "note": "5 ta mavzu"},
    {"id": "shaxmat",        "label": "♟️ Shaxmat",         "note": ""},
    {"id": "shom",           "label": "🕌 Shom",            "note": ""},
    {"id": "vibe_coding",    "label": "💻 Vibe Coding",     "note": "30 min"},
    {"id": "xufton",         "label": "🕌 Xufton",          "note": ""},
    {"id": "vitr",           "label": "🌙 Vitr Vojib",      "note": ""},
    {"id": "erta_uxlash",    "label": "😴 Erta uxlash",     "note": "23:00 gacha"},
]

DATA_FILE = "data.json"

def load():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return {}

def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

def get_state(data, hid, idx):
    return data.get(f"{hid}_{idx}", "")

def get_today_idx():
    delta = (date.today() - START_DATE).days
    if delta < 0: return 1
    if delta >= 30: return 30
    return delta + 1

def day_score(data, idx):
    done = sum(1 for h in HABITS if get_state(data, h["id"], idx) == "done")
    return round(done / len(HABITS) * 100)

def icon(st):
    return "✅" if st == "done" else "❌" if st == "fail" else "⬜"

def next_st(st):
    return "done" if st == "" else "fail" if st == "done" else ""

def build_keyboard(data, idx):
    kb = []
    for h in HABITS:
        st = get_state(data, h["id"], idx)
        note = f" ({h['note']})" if h["note"] else ""
        kb.append([InlineKeyboardButton(
            f"{icon(st)} {h['label']}{note}",
            callback_data=f"t_{h['id']}_{idx}"
        )])
    kb.append([InlineKeyboardButton("🔄 Yangilash", callback_data=f"r_{idx}")])
    return InlineKeyboardMarkup(kb)

def build_text(data, idx):
    today = date.today()
    score = day_score(data, idx)
    done = sum(1 for h in HABITS if get_state(data, h["id"], idx) == "done")
    return (
        f"📅 *{today.day}-{today.strftime('%B')} · {idx}-kun*\n"
        f"Bajarildi: *{score}%* ({done}/{len(HABITS)})\n\n"
        f"⬜ bo'sh → ✅ bajarildi → ❌ bajarilmadi"
    )

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Odat Tracker Botga xush kelibsiz!*\n\n"
        "📅 /bugun — bugungi odatlar\n"
        "📊 /stats — statistika\n"
        "📋 /jadval — 30 kunlik jadval",
        parse_mode="Markdown"
    )

async def bugun(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
    idx = get_today_idx()
    await update.message.reply_text(
        build_text(data, idx),
        reply_markup=build_keyboard(data, idx),
        parse_mode="Markdown"
    )

async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
    idx = get_today_idx()
    text = "📊 *Statistika*\n\n"
    for h in HABITS:
        cnt = sum(1 for d in range(1, 31) if get_state(data, h["id"], d) == "done")
        pct = round(cnt / 30 * 100)
        streak = 0
        for i in range(idx, 0, -1):
            if get_state(data, h["id"], i) == "done": streak += 1
            else: break
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        text += f"{h['label']}\n`{bar}` {cnt}/30"
        if streak: text += f" 🔥{streak}"
        text += "\n\n"
    overall = round(sum(
        1 for h in HABITS for d in range(1, 31)
        if get_state(data, h["id"], d) == "done"
    ) / (len(HABITS) * 30) * 100)
    text += f"*Umumiy: {overall}%*"
    await update.message.reply_text(text, parse_mode="Markdown")

async def jadval(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
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
    data = load()

    if query.data.startswith("t_"):
        _, hid, didx = query.data.split("_", 2)
        didx = int(didx)
        key = f"{hid}_{didx}"
        data[key] = next_st(data.get(key, ""))
        save(data)
        await query.edit_message_text(
            build_text(data, didx),
            reply_markup=build_keyboard(data, didx),
            parse_mode="Markdown"
        )
    elif query.data.startswith("r_"):
        didx = int(query.data.split("_")[1])
        await query.edit_message_text(
            build_text(data, didx),
            reply_markup=build_keyboard(data, didx),
            parse_mode="Markdown"
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bugun", bugun))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("jadval", jadval))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
        
