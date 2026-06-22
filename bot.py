import os
import json
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "")
START_DATE = date(2026, 6, 22)

HABITS = [
    {"id": "h01", "label": "🌅 Erta turish",   "note": "3:40 da"},
    {"id": "h02", "label": "🕌 Bomdod",         "note": ""},
    {"id": "h03", "label": "💪 Otjimaniya",     "note": "15 ta"},
    {"id": "h04", "label": "🔥 Pres",           "note": "15 ta"},
    {"id": "h05", "label": "🦵 Otirib turish",  "note": "15 ta"},
    {"id": "h06", "label": "🕌 Peshin",         "note": ""},
    {"id": "h07", "label": "🕌 Asr",            "note": ""},
    {"id": "h08", "label": "📚 Tarix oqish",    "note": "5 mavzu"},
    {"id": "h09", "label": "♟ Shaxmat",         "note": ""},
    {"id": "h10", "label": "🕌 Shom",           "note": ""},
    {"id": "h11", "label": "💻 Vibe Coding",    "note": "30 min"},
    {"id": "h12", "label": "🕌 Xufton",         "note": ""},
    {"id": "h13", "label": "🌙 Vitr Vojib",     "note": ""},
    {"id": "h14", "label": "😴 Erta uxlash",    "note": "23:00 gacha"},
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

def gst(data, hid, idx):
    return data.get(hid + str(idx), "")

def today_idx():
    delta = (date.today() - START_DATE).days
    return max(1, min(30, delta + 1))

def score(data, idx):
    n = sum(1 for h in HABITS if gst(data, h["id"], idx) == "done")
    return round(n / len(HABITS) * 100)

def ico(st):
    if st == "done": return "✅"
    if st == "fail": return "❌"
    return "⬜"

def nxt(st):
    if st == "": return "done"
    if st == "done": return "fail"
    return ""

def make_kb(data, idx):
    rows = []
    for h in HABITS:
        st = gst(data, h["id"], idx)
        note = "(" + h["note"] + ") " if h["note"] else ""
        rows.append([InlineKeyboardButton(
            ico(st) + " " + note + h["label"],
            callback_data="t" + h["id"] + str(idx)
        )])
    rows.append([InlineKeyboardButton("🔄 Yangilash", callback_data="r" + str(idx))])
    return InlineKeyboardMarkup(rows)

def make_txt(data, idx):
    sc = score(data, idx)
    dn = sum(1 for h in HABITS if gst(data, h["id"], idx) == "done")
    return (
        "*" + str(idx) + "-kun — " + date.today().strftime("%d %B %Y") + "*\n"
        "Bajarildi: *" + str(sc) + "%* (" + str(dn) + "/" + str(len(HABITS)) + ")\n\n"
        "⬜ bos → ✅ → ❌ → ⬜"
    )

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Odat Tracker*\n\n"
        "/bugun — bugungi odatlar\n"
        "/stats — statistika\n"
        "/jadval — 30 kunlik jadval",
        parse_mode="Markdown"
    )

async def cmd_bugun(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
    idx = today_idx()
    await update.message.reply_text(
        make_txt(data, idx),
        reply_markup=make_kb(data, idx),
        parse_mode="Markdown"
    )

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
    idx = today_idx()
    lines = ["📊 *Statistika*\n"]
    for h in HABITS:
        cnt = sum(1 for d in range(1, 31) if gst(data, h["id"], d) == "done")
        pct = round(cnt / 30 * 100)
        streak = 0
        for i in range(idx, 0, -1):
            if gst(data, h["id"], i) == "done":
                streak += 1
            else:
                break
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        line = h["label"] + "\n`" + bar + "` " + str(cnt) + "/30"
        if streak:
            line += " 🔥" + str(streak)
        lines.append(line)
    total = round(sum(
        1 for h in HABITS for d in range(1, 31)
        if gst(data, h["id"], d) == "done"
    ) / (len(HABITS) * 30) * 100)
    lines.append("\n*Umumiy: " + str(total) + "%*")
    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

async def cmd_jadval(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load()
    idx = today_idx()
    lines = ["📋 *30 Kunlik Jadval*\n"]
    for h in HABITS:
        row = h["label"] + "\n"
        for d in range(1, 31):
            st = gst(data, h["id"], d)
            if d == idx:
                row += "👆" if st == "" else ("✅" if st == "done" else "❌")
            else:
                row += ico(st)
        lines.append(row)
    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load()
    cb = q.data
    if cb.startswith("t"):
        hid = cb[1:4]
        idx = int(cb[4:])
        key = hid + str(idx)
        data[key] = nxt(data.get(key, ""))
        save(data)
        await q.edit_message_text(
            make_txt(data, idx),
            reply_markup=make_kb(data, idx),
            parse_mode="Markdown"
        )
    elif cb.startswith("r"):
        idx = int(cb[1:])
        await q.edit_message_text(
            make_txt(data, idx),
            reply_markup=make_kb(data, idx),
            parse_mode="Markdown"
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("bugun", cmd_bugun))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("jadval", cmd_jadval))
    app.add_handler(CallbackQueryHandler(on_button))
    print("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
