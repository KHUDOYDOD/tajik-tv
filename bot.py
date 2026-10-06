"""
Telegram бот — Таджикское ТВ 🇹🇯
Красивые текстовые карточки каналов.
"""
import os
import io
import logging
from datetime import datetime

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

import mediabay

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Иконки и описания каналов
CH_INFO = {
    112: ("📡", "Главный государственный ТВ канал Таджикистана"),
    106: ("🌍", "Информационный канал. Новости на 3 языках"),
    108: ("🌸", "Детский и молодёжный канал"),
    110: ("⛵", "Развлекательные и познавательные программы"),
    397: ("🎬", "Кино и сериалы на таджикском языке"),
    495: ("🎵", "Таджикская музыка и клипы 24/7"),
    544: ("🎥", "Таджикские фильмы и сериалы"),
    583: ("⚽", "Спорт. Футбол в HD качестве"),
    596: ("🏆", "Спортивный канал — все виды спорта"),
    628: ("🏙", "Городской телеканал Душанбе в HD"),
    629: ("🎭", "Культура. Театр, музыка, традиции"),
    630: ("🌿", "Региональный канал Хатлонской области"),
    631: ("🏔", "Региональный канал Бадахшана"),
    632: ("🦁", "Региональный канал Куляба"),
    633: ("🌾", "Региональный канал Согдийской области"),
    673: ("✈️", "Туризм и народные ремёсла"),
    694: ("🔬", "Наука и природа. Документальные программы"),
}


def channels_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    # Кнопка открыть Mini App плеер
    from telebot.types import WebAppInfo
    kb.add(InlineKeyboardButton(
        text="📺 Открыть ТВ плеер",
        web_app=WebAppInfo(url="https://khudoydod.github.io/tajik-tv/")
    ))
    btns = []
    for ch in mediabay.TJ_CHANNELS:
        icon = CH_INFO.get(ch["id"], ("📺", ""))[0]
        btns.append(InlineKeyboardButton(
            text=f"{icon} {ch['name']}",
            callback_data=f"ch:{ch['id']}"
        ))
    for i in range(0, len(btns) - 1, 2):
        kb.row(btns[i], btns[i + 1])
    if len(btns) % 2 != 0:
        kb.add(btns[-1])
    kb.add(InlineKeyboardButton(text="📥 Скачать M3U плейлист", callback_data="m3u"))
    return kb


def channel_keyboard(ch_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.row(
        InlineKeyboardButton(text="▶️ Получить ссылку", callback_data=f"stream:{ch_id}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh:{ch_id}"),
    )
    kb.add(InlineKeyboardButton(text="◀️ Все каналы", callback_data="back"))
    return kb


def stream_keyboard(ch_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text="🔄 Обновить ссылку", callback_data=f"refresh:{ch_id}"),
        InlineKeyboardButton(text="◀️ Все каналы", callback_data="back"),
    )
    return kb


WELCOME = (
    "🇹🇯 *Таджикское ТВ — онлайн*\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "📺 Нажмите *Открыть ТВ плеер* — смотрите прямо в Telegram!\n\n"
    "Или выберите канал ниже и получите ссылку для:\n"
    "• VLC / IPTV Smarters / TiviMate\n"
    "• MX Player на Android\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "👇 Выберите способ:"
)


@bot.message_handler(commands=["start", "channels"])
def cmd_start(message):
    bot.send_message(message.chat.id, WELCOME, parse_mode="Markdown",
                     reply_markup=channels_keyboard())


@bot.message_handler(commands=["m3u"])
def cmd_m3u(message):
    send_m3u_file(message.chat.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ch:"))
def on_channel(call):
    ch_id = int(call.data.split(":")[1])
    ch = mediabay.get_channel_by_id(ch_id)
    if not ch:
        bot.answer_callback_query(call.id, "❌ Канал не найден", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    icon, desc = CH_INFO.get(ch_id, ("📺", "Таджикский телеканал"))
    text = (
        f"{icon} *{ch['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 {desc}\n\n"
        f"Нажмите *▶️ Получить ссылку* для просмотра."
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=channel_keyboard(ch_id))


@bot.callback_query_handler(func=lambda c: c.data.startswith("stream:"))
def on_stream(call):
    ch_id = int(call.data.split(":")[1])
    ch = mediabay.get_channel_by_id(ch_id)
    bot.answer_callback_query(call.id, "⏳ Получаю ссылку...")
    stream = mediabay.get_stream(ch_id)
    if not stream:
        bot.answer_callback_query(call.id, "❌ Не удалось получить стрим", show_alert=True)
        return
    icon, _ = CH_INFO.get(ch_id, ("📺", ""))
    now = datetime.now().strftime("%H:%M")
    text = (
        f"{icon} *{ch['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 *Ссылка для VLC / IPTV плеера:*\n"
        f"`{stream}`\n\n"
        f"📱 *Как открыть:*\n"
        f"1. Скопируй ссылку выше\n"
        f"2. VLC → Медиа → Открыть URL\n"
        f"3. Вставь и нажми Воспроизвести\n\n"
        f"🕐 {now}"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=stream_keyboard(ch_id))


@bot.callback_query_handler(func=lambda c: c.data.startswith("refresh:"))
def on_refresh(call):
    ch_id = int(call.data.split(":")[1])
    ch = mediabay.get_channel_by_id(ch_id)
    bot.answer_callback_query(call.id, "🔄 Обновляю...")
    mediabay._cache.pop(ch_id, None)
    stream = mediabay.get_stream(ch_id)
    if not stream:
        bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
        return
    icon, _ = CH_INFO.get(ch_id, ("📺", ""))
    now = datetime.now().strftime("%H:%M")
    text = (
        f"{icon} *{ch['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 *Ссылка для VLC / IPTV плеера:*\n"
        f"`{stream}`\n\n"
        f"📱 *Как открыть:*\n"
        f"1. Скопируй ссылку выше\n"
        f"2. VLC → Медиа → Открыть URL\n"
        f"3. Вставь и нажми Воспроизвести\n\n"
        f"✅ Обновлено в {now}"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=stream_keyboard(ch_id))


@bot.callback_query_handler(func=lambda c: c.data == "back")
def on_back(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(WELCOME, call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=channels_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == "m3u")
def on_m3u(call):
    bot.answer_callback_query(call.id, "⏳ Генерирую...")
    send_m3u_file(call.message.chat.id)


def send_m3u_file(chat_id):
    msg = bot.send_message(chat_id, "⏳ Генерирую M3U плейлист...")
    channels = mediabay.get_all_streams()
    lines = ["#EXTM3U"]
    count = 0
    for ch in channels:
        if ch.get("stream"):
            lines.append(
                f'#EXTINF:-1 tvg-id="{ch["id"]}" '
                f'tvg-logo="{ch["logo"]}" '
                f'group-title="🇹🇯 Таджикистан",{ch["name"]}'
            )
            lines.append(ch["stream"])
            count += 1
    content = "\n".join(lines).encode("utf-8")
    filename = f"tajikistan_{datetime.now().strftime('%Y%m%d_%H%M')}.m3u"
    bot.delete_message(chat_id, msg.message_id)
    bot.send_document(
        chat_id,
        io.BytesIO(content),
        visible_file_name=filename,
        caption=(
            f"🇹🇯 *M3U плейлист — Таджикское ТВ*\n"
            f"📺 Каналов: {count}\n"
            f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Откройте в VLC, IPTV Smarters или Kodi."
        ),
        parse_mode="Markdown"
    )


if __name__ == "__main__":
    logging.info("🇹🇯 Таджикское ТВ бот запущен")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
