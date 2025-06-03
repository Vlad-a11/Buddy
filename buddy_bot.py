import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from dotenv import load_dotenv
from datetime import datetime
import asyncio
from flask import Flask, request


load_dotenv()
API_URL = os.getenv("HUGGINGFACE_API_URL")
API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
headers = {"Authorization": f"Bearer {API_TOKEN}"}


# --- Состояния ---
LANGUAGE, CHOOSING, ANXIETY, INSECURITY, PANIC, AI_SUPPORT, JOURNAL_WRITE = range(7)

TEXTS = {
    "ru": {
        "choose_language": "🌍 Выбери язык:",
        "lang_ru_selected": "Вы выбрали Русский. Добро пожаловать!",
        "lang_en_selected": "Вы выбрали Английский. Добро пожаловать!",
        "lang_kk_selected": "Сіз Қазақ тілін таңдадыңыз. Қош келдіңіз!",
        "greeting": (
            "Привет!\n"
            "Я Buddy — твой личный психолог 🌿\n\n"
            "Я помогу тебе, когда:\n"
            "— тревожно\n"
            "— неуверенность мешает\n"
            "— паника накрывает\n"
            "— хочется поддержки\n\n"
            "С чем поработаем сейчас?"
        ),
        "menu_prompt": "Выбери вариант ниже:",
        "anxiety": "Тревожность",
        "insecurity": "Неуверенность",
        "panic": "Паника",
        "support": "Хочу поддержку",
        "ai_prompt": "Напиши, что тебя беспокоит. Я постараюсь помочь.",
        "exit_ai": "Выйти из поддержки",
        "journal_empty": "📭 В журнале пока нет записей.",
        "ready_button": "Готов",
        "menu_button": "В меню",
        "back_menu": "В меню",
        "anxiety_text": "Расскажи, что тебя тревожит. Я помогу разобраться.",
        "insecurity_text": "Поделись своими переживаниями о неуверенности.",
        "panic_text": "Если готов, нажми 'Готов', чтобы начать дыхательную технику.",
        "sos_button": "🆘 SOS",
        "praise_button": "🌟 Похвали",
        "clear_journal": "Очистить дневник",
        "journal_button": "📔 Журнал",
        "reply_keyboard_hint": "Выбери действие внизу 👇",
        "sos_message": (
            "Ты не один. Дыши глубоко.\n"
            "Всё будет хорошо. Я рядом."
        ),
        "write_journal_prompt": "Напиши, что хочешь сохранить в дневник:",
        "journal_saved": "Твоя запись сохранена. Спасибо, что поделился(ась).",
        "praise_response": "Ты молодец! Я тобой горжусь ❤️",
        "sos_response": "Я с тобой. Сделаем глубокий вдох вместе?",
        "panic_ready_response": (
            "Отлично! Давай сделаем 4 круга дыхания «Коробка».\n"
            "Вдох — 4 секунды\n"
            "Задержка — 4 секунды\n"
            "Выдох — 4 секунды\n"
            "Задержка — 4 секунды\n\n"
            "Напиши, когда закончишь."
        ),
        "unknown_command": "Неизвестная команда.",
        "cancel_message": "До встречи! Если понадобится — просто напиши /start.",
        "thank_you_anxiety": "Спасибо, что описал(а) окружение: {}",
        "thank_you_insecurity": "Спасибо, что поделился переживаниями: {}",
        "return_menu_prompt": "Если хочешь вернуться в меню, нажми кнопку ниже.",
        "journal_cleared": "Дневник очищен."
    },
    "en": {
        "choose_language": "🌍 Choose your language:",
        "lang_ru_selected": "You selected Russian. Welcome!",
        "lang_en_selected": "You selected English. Welcome!",
        "lang_kk_selected": "You selected Kazakh. Welcome!",
        "greeting": (
            "Hi!\n"
            "I'm Buddy — your personal mental support bot 🌿\n\n"
            "I can help you when:\n"
            "— you feel anxious\n"
            "— insecurity bothers you\n"
            "— panic hits\n"
            "— you want support\n\n"
            "What shall we work on now?"
        ),
        "menu_prompt": "Choose an option below:",
        "anxiety": "Anxiety",
        "insecurity": "Insecurity",
        "panic": "Panic",
        "support": "Need support",
        "ai_prompt": "Write what worries you. I'll try to help.",
        "exit_ai": "Exit support",
        "ready_button": "Ready",
        "menu_button": "Menu",
        "back_menu": "Menu",
        "anxiety_text": "Tell me what’s making you anxious. I’ll help you work through it.",
        "insecurity_text": "Share your thoughts about what makes you feel insecure.",
        "panic_text": "If you are ready, press 'Ready' to start the breathing exercise.",
        "sos_button": "🆘 SOS",
        "praise_button": "🌟 Praise",
        "clear_journal": "Clear journal",
        "journal_button": "📔 Journal",
        "reply_keyboard_hint": "Choose an action below 👇",
        "journal_empty": "📭 There are no entries in the journal yet.",
        "sos_message": (
            "You are not alone. Breathe deeply.\n"
            "Everything will be okay. I'm here."
        ),
        "write_journal_prompt": "Write what you want to save in the journal:",
        "journal_saved": "Your entry has been saved. Thanks for sharing.",
        "praise_response": "You’re doing great! I’m proud of you ❤️",
        "sos_response": "I’m with you. Let’s take a deep breath together?",
        "panic_ready_response": (
            "Great! Let's do 4 rounds of Box breathing.\n"
            "Inhale — 4 seconds\n"
            "Hold — 4 seconds\n"
            "Exhale — 4 seconds\n"
            "Hold — 4 seconds\n\n"
            "Write to me when you're done."
        ),
        "unknown_command": "Unknown command.",
        "cancel_message": "See you! If you need me, just write /start.",
        "thank_you_anxiety": "Thank you for sharing: {}",
        "thank_you_insecurity": "Thank you for sharing your thoughts: {}",
        "return_menu_prompt": "If you want to return to menu, press the button below.",
        "journal_cleared": "Journal cleared."
    },
    "kk": {
        "choose_language": "🌍 Тілді таңдаңыз:",
        "lang_ru_selected": "Сіз орыс тілін таңдадыңыз. Қош келдіңіз!",
        "lang_en_selected": "Сіз ағылшын тілін таңдадыңыз. Қош келдіңіз!",
        "lang_kk_selected": "Сіз Қазақ тілін таңдадыңыз. Қош келдіңіз!",
        "greeting": (
            "Сәлем!\n"
            "Мен Buddy — сенің жеке психологың 🌿\n\n"
            "Мен саған көмектесемін, егер:\n"
            "— уайымдап жүрсең\n"
            "— сенімсіздік болса\n"
            "— паника болса\n"
            "— қолдау керек болса\n\n"
            "Қазір немен жұмыс істейміз?"
        ),
        "menu_prompt": "Төмендегі опцияны таңдаңыз:",
        "anxiety": "Уайым",
        "insecurity": "Сенімсіздік",
        "panic": "Паника",
        "support": "Қолдау керек",
        "ai_prompt": "Не алаңдатады? Мен көмектесемін.",
        "exit_ai": "Қолдаудан шығу",
        "ready_button": "Дайынмын",
        "menu_button": "Мәзір",
        "back_menu": "Мәзір",
        "anxiety_text": "Сені не нәрсе уайымдатып тұр? Бірге шешім табайық.",
        "insecurity_text": "Өзіңді сенімсіз сезінетін жағдайларыңмен бөліс.",
        "panic_text": "Дайын болсаңыз, «Дайынмын» деп басыңыз, дем алу техникасын бастаймыз.",
        "sos_button": "🆘",
        "praise_button": "🌟",
        "journal_button": "📔",
        "clear_journal": "Дневникті тазарту",
        "reply_keyboard_hint": "Төменнен әрекетті таңдаңыз 👇",
        "journal_empty": "📭 Дневникте әзірге жазбалар жоқ.",
        "sos_message": (
            "Сен жалғыз емессің. Терең тыныс ал.\n"
            "Барлығы жақсы болады. Мен сенімен біргемін."
        ),
        "write_journal_prompt": "Дневникке жазғыңыз келетін нәрсені жазыңыз:",
        "journal_saved": "Жазбаңыз сақталды. Бөліскеніңізге рақмет.",
        "praise_response": "Жарайсың! Мен саған мақтанамын ❤️",
        "sos_response": "Мен сеніменмін. Терең тыныс алайық па?",
        "panic_ready_response": (
            "Тамаша! 4 рет «Қорап» тыныс алу жаттығуын жасаймыз.\n"
            "Тыныс алу — 4 секунд\n"
            "Тыныс ұстап тұру — 4 секунд\n"
            "Шығару — 4 секунд\n"
            "Тыныс ұстап тұру — 4 секунд\n\n"
            "Аяқтағаныңды жазыңыз."
        ),
        "unknown_command": "Белгісіз команда.",
        "cancel_message": "Көріскенше! Қажет болса /start деп жазыңыз.",
        "thank_you_anxiety": "Бөліскеніңізге рахмет: {}",
        "thank_you_insecurity": "Ойларыңызды бөліскеніңізге рахмет: {}",
        "return_menu_prompt": "Мәзірге қайту үшін төмендегі түймені басыңыз.",
        "journal_cleared": "Дневник тазартылды."
    }
}


# --- Клавиатуры ---
def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
         InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
         InlineKeyboardButton("Қазақша 🇰🇿", callback_data="lang_kk")]
    ])

def main_menu_keyboard(lang):
    texts = TEXTS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(texts["anxiety"], callback_data="anxiety"),
         InlineKeyboardButton(texts["insecurity"], callback_data="insecurity")],
        [InlineKeyboardButton(texts["panic"], callback_data="panic")],
        [InlineKeyboardButton(texts["support"], callback_data="support")]
    ])

def bottom_menu_keyboard(lang):
    texts = TEXTS[lang]
    return ReplyKeyboardMarkup([
        [texts["journal_button"], texts["sos_button"], texts["praise_button"]]
    ], resize_keyboard=True)

def panic_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["ready_button"], callback_data="panic_ready")],
        [InlineKeyboardButton(TEXTS[lang]["back_menu"], callback_data="back_menu")]
    ])

def ai_support_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["exit_ai"], callback_data="exit_ai")],
        [InlineKeyboardButton(TEXTS[lang]["back_menu"], callback_data="back_menu")]
    ])

def back_menu_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["back_menu"], callback_data="back_menu")]
    ])

# --- Хендлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TEXTS["ru"]["choose_language"], reply_markup=lang_keyboard())
    return LANGUAGE

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.split("_")[1]
    context.user_data["lang"] = lang_code

    await query.edit_message_text(TEXTS[lang_code]["greeting"], reply_markup=main_menu_keyboard(lang_code))
    return CHOOSING

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "ru")
    data = query.data

    if data == "anxiety":
        await query.edit_message_text(TEXTS[lang]["anxiety_text"], reply_markup=back_menu_keyboard(lang))
        return ANXIETY

    elif data == "insecurity":
        await query.edit_message_text(TEXTS[lang]["insecurity_text"], reply_markup=back_menu_keyboard(lang))
        return INSECURITY

    elif data == "panic":
        await query.edit_message_text(TEXTS[lang]["panic_text"], reply_markup=panic_keyboard(lang))
        return PANIC

    elif data == "support":
        await query.edit_message_text(TEXTS[lang]["ai_prompt"], reply_markup=ai_support_keyboard(lang))
        return AI_SUPPORT

    elif data == "journal":
        await query.edit_message_text(TEXTS[lang]["write_journal_prompt"], reply_markup=back_menu_keyboard(lang))
        return JOURNAL_WRITE

    elif data == "sos":
        await query.edit_message_text(TEXTS[lang]["sos_message"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    elif data == "praise":
        await query.edit_message_text(TEXTS[lang]["praise_response"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    elif data == "back_menu":
        await query.edit_message_text(TEXTS[lang]["greeting"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    elif data == "panic_ready":
        await query.edit_message_text(TEXTS[lang]["panic_ready_response"], reply_markup=back_menu_keyboard(lang))
        return PANIC

    elif data == "exit_ai":
        await query.edit_message_text(TEXTS[lang]["greeting"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    elif data == "clear_journal":
        context.user_data["journal"] = []
        await query.edit_message_text(TEXTS[lang]["journal_cleared"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    else:
        await query.edit_message_text(TEXTS[lang]["unknown_command"])
        return CHOOSING

def reply_keyboard(lang):
    texts = TEXTS[lang]
    return ReplyKeyboardMarkup(
        [
            [texts["sos_button"], texts["praise_button"]],
            [texts["journal_button"]]
        ],
        resize_keyboard=True
    )

async def anxiety_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = update.message.text
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    entry = f"{now} — {TEXTS[lang]['anxiety']}: {text}"
    context.user_data.setdefault("journal", []).append(entry)
    await update.message.reply_text(TEXTS[lang]["thank_you_anxiety"].format(text), reply_markup=bottom_menu_keyboard(lang))
    return CHOOSING

async def insecurity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = update.message.text
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    entry = f"{now} — {TEXTS[lang]['insecurity']}: {text}"
    context.user_data.setdefault("journal", []).append(entry)
    await update.message.reply_text(TEXTS[lang]["thank_you_insecurity"].format(text), reply_markup=bottom_menu_keyboard(lang))
    return CHOOSING

async def panic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = update.message.text.strip().lower()
    if text in ["готов", "done", "finished", "закончено"]:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        context.user_data.setdefault("journal", []).append(f"{now} — {TEXTS[lang]['panic']} завершена")
        await update.message.reply_text(TEXTS[lang]["return_menu_prompt"], reply_markup=bottom_menu_keyboard(lang))
        return CHOOSING
    else:
        await update.message.reply_text(TEXTS[lang]["panic_text"], reply_markup=panic_keyboard(lang))
        return PANIC

async def panic_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("РАБОТАЕТ")
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "ru")
    data = query.data

    if data == "panic_repeat":
        context.user_data["panic_cycles"] = 0
        return await handle_panic_breathing(update, context)

    elif data == "panic_ready":
        chat_id = query.message.chat.id
        await query.edit_message_text("Начинаем дыхательную технику...")
        asyncio.create_task(panic_breathing_task(context.bot, chat_id, context))
        return PANIC

    elif data == "save_panic":
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        journal = context.user_data.get("journal", [])
        journal.append(f"{now} — техника при панике (дыхание квадратом)")
        context.user_data["journal"] = journal

        await query.edit_message_text("✅ Сохранено в журнал.")
        await query.message.reply_text(
            TEXTS[lang]["return_menu_prompt"],
            reply_markup=main_menu_keyboard(lang)
        )
        return CHOOSING

    elif data == "back_menu":
        await query.edit_message_text(TEXTS[lang]["greeting"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    else:
        await query.edit_message_text(TEXTS[lang]["unknown_command"])
        return CHOOSING

def query_hf(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()  # выбросит исключение, если ошибка
    return response.json()

async def ai_support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    user_text = update.message.text

    prompt = (
        "Ты — доброжелательный и поддерживающий собеседник. "
        "Ответь с сочувствием, поддержкой и тёплым отношением на следующее сообщение пользователя:\n\n"
        f"{user_text}"
    )

    payload = {
        "inputs": prompt,
        "parameters": {"temperature": 0.8, "max_new_tokens": 150},
    }

    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, query_hf, payload)
        # response может быть либо список с 'generated_text', либо dict с ошибкой
        if isinstance(response, list) and "generated_text" in response[0]:
            ai_reply = response[0]["generated_text"]
        else:
            ai_reply = "Извините, не удалось получить ответ от модели."
    except Exception as e:
        print(f"HuggingFace API error: {e}")
        ai_reply = "Произошла ошибка при подключении к ИИ. Попробуй позже."

    await update.message.reply_text(ai_reply, reply_markup=ai_support_keyboard(lang))
    return AI_SUPPORT

async def handle_panic_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(
        "Давай попробуем технику дыхания «квадрат»: вдох — задержка — выдох — задержка.\n"
        "Сейчас начнём цикл дыхания...",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data["panic_cycles"] = 0
    return await handle_panic_breathing(update, context)

async def panic_ready_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    # Запускаем задачу дыхания в фоне (не ждём, чтобы не блокировать)
    asyncio.create_task(panic_breathing_task(context.bot, chat_id, context))

    # Можно отредактировать сообщение с кнопкой, чтобы сказать, что техника началась
    await query.edit_message_text("Начинаем дыхательную технику...")

    return PANIC



async def panic_breathing_task(bot, chat_id, context):
    breathing_steps = [
        ("🌬 Вдохни", 4),
        ("⏸ Задержи дыхание", 4),
        ("💨 Выдохни", 4),
        ("⏸ Задержи дыхание", 4),
    ]

    for step, seconds in breathing_steps:
        msg = await bot.send_message(chat_id=chat_id, text=step)
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)

    # После одного полного цикла — показываем финальные кнопки
    lang = context.user_data.get("lang", "ru")
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Готов", callback_data="panic_ready"),
            InlineKeyboardButton("⬅️ Меню", callback_data="back_menu")
        ],
        [
            InlineKeyboardButton("📓 Сохранить в журнал", callback_data="save_panic")
        ]
    ])

    await bot.send_message(chat_id=chat_id, text="Ты молодец! Как себя чувствуешь?", reply_markup=keyboard)


async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    texts = TEXTS[lang]
    text = update.message.text.strip()

    # Прерываем активные техники
    context.user_data["finish"] = True
    context.user_data["state"] = None

    if text == texts["sos_button"]:
        await update.message.reply_text(
            texts["sos_message"] + "\n📞 Телефон доверия: 150 (бесплатно)",
            reply_markup=bottom_menu_keyboard(lang)
        )
        return CHOOSING

    elif text == texts["praise_button"]:
        await update.message.reply_text(
            texts["praise_response"],
            reply_markup=bottom_menu_keyboard(lang)
        )
        return CHOOSING

    elif text == texts["journal_button"]:
        journal = context.user_data.get("journal", [])
        if not journal:
            text_journal = texts["journal_empty"]
        else:
            text_journal = "\n\n".join(journal)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(texts["clear_journal"], callback_data="clear_journal")],
            [InlineKeyboardButton(texts["back_menu"], callback_data="back_menu")]
        ])
        await update.message.reply_text(text_journal, reply_markup=keyboard)
        return CHOOSING

    else:
        await update.message.reply_text(texts["unknown_command"], reply_markup=bottom_menu_keyboard(lang))
        return CHOOSING



async def journal_save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    entry = update.message.text
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    context.user_data.setdefault("journal", []).append(f"{now} — {entry}")
    await update.message.reply_text(TEXTS[lang]["journal_saved"], reply_markup=bottom_menu_keyboard(lang))
    return CHOOSING

async def sos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = TEXTS[lang]["sos_message"] + "\n📞 Телефон доверия: 150 (бесплатно)"
    await update.message.reply_text(text, reply_markup=bottom_menu_keyboard(lang))
    return CHOOSING

async def debug_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print("DEBUG callback data:", query.data)
    await query.answer()
    return  # просто ничего не делать дальше

async def praise_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(TEXTS[lang]["praise_response"], reply_markup=bottom_menu_keyboard(lang))
    return CHOOSING

async def show_journal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    journal = context.user_data.get("journal", [])
    if not journal:
        text = TEXTS[lang]["journal_empty"]
    else:
        text = "\n\n".join(journal)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["clear_journal"], callback_data="clear_journal")],
        [InlineKeyboardButton(TEXTS[lang]["back_menu"], callback_data="back_menu")]
    ])
    await update.message.reply_text(text, reply_markup=keyboard)
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(TEXTS[lang]["cancel_message"])
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [
                CallbackQueryHandler(language_chosen, pattern="^lang_")
            ],
            CHOOSING: [
                CallbackQueryHandler(main_menu_handler, pattern="^(anxiety|insecurity|panic|support|journal|sos|praise|back_menu|ready|exit_ai|clear_journal)$"),
                MessageHandler(filters.TEXT & (~filters.COMMAND), reply_keyboard_handler),  # Общий обработчик для всех текстовых сообщений
            ],
            ANXIETY: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), anxiety_handler),
                CallbackQueryHandler(main_menu_handler, pattern="^back_menu$")
            ],
            INSECURITY: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), insecurity_handler),
                CallbackQueryHandler(main_menu_handler, pattern="^back_menu$")
            ],
            PANIC: [
                CallbackQueryHandler(panic_ready_handler, pattern="^panic_ready$"),
                CallbackQueryHandler(panic_callback_handler, pattern="^(panic_|save_panic)$"),  # тут теперь есть save_panic
                CallbackQueryHandler(main_menu_handler, pattern="^back_menu$"),
                CallbackQueryHandler(debug_callback_handler, pattern=".*"),  # последний, общий
                MessageHandler(filters.TEXT & (~filters.COMMAND), panic_handler),
                CallbackQueryHandler(lambda update, context: update.callback_query.answer("⚠️ Неизвестная кнопка", show_alert=True), pattern=".*"),
            ],            
            AI_SUPPORT: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), ai_support_handler),
                CallbackQueryHandler(main_menu_handler, pattern="^back_menu$")
            ],
            JOURNAL_WRITE: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), journal_save_handler),
                CallbackQueryHandler(main_menu_handler, pattern="^back_menu$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    print("Bot is polling...")
    app.run_polling()

if __name__ == "__main__":
    main()