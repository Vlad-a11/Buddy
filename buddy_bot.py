import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import openai

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- States ---
LANGUAGE, CHOOSING, ANXIETY, INSECURITY, PANIC, AI_SUPPORT, JOURNAL_WRITE = range(7)

TEXTS = {
    "ru": {
        "choose_language": (
            "🌍 Выбери язык:\n"
            "🌍 Choose your language:\n"
            "🌍 Тілді таңдаңыз:"
        ),
        "lang_ru_selected": "Вы выбрали Русский. Добро пожаловать!",
        "lang_en_selected": "Вы выбрали Английский. Добро пожаловать!",
        "lang_kk_selected": "Сіз Қазақ тілін таңдадыңыз. Қош келдіңіз!",
        "greeting": (
            "Привет!\n"
            "Я твой личный цифровой психолог 🌿\n\n"
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
        "sos_button": "🚨 SOS",
        "sos_message": "Ты не один. Всё будет хорошо. Если нужно, свяжись с нашим психологом.",
        "call_support": "Связаться с поддержку",
        "close_message": "❌ Закрыть",
        "praise_button": "🌟 Похвали",
        "clear_journal": "Очистить дневник",
        "journal_button": "📔 Журнал",
        "reply_keyboard_hint": "Выбери действие внизу 👇",
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
            "Hi! I'm your personal mental support bot 🌿\n\n"
            "I can help when you feel:\n"
            "- Anxious\n- Insecure\n"
            "- Panicked\n- Need support\n\n"
            "What would you like to work on?"
        ),
        "menu_prompt": "Choose an option below:",
        "anxiety": "Anxiety",
        "insecurity": "Insecurity",
        "panic": "Panic",
        "support": "Need support",
        "ai_prompt": "What's bothering you? I'll try to help.",
        "exit_ai": "Exit support",
        "journal_empty": "📭 Journal is empty.",
        "ready_button": "Ready",
        "menu_button": "Menu",
        "back_menu": "Menu",
        "anxiety_text": "What's making you anxious? Let's work through it.",
        "insecurity_text": "Share what makes you feel insecure.",
        "panic_text": "Press 'Ready' to start breathing exercise.",
        "sos_button": "🚨 SOS",
        "sos_message": "You are not alone. It's going to be okay. Text us if you need help.",
        "call_support": "Support",
        "close_message": "❌ Close",
        "praise_button": "🌟 Praise",
        "clear_journal": "Clear journal",
        "journal_button": "📔 Journal",
        "reply_keyboard_hint": "Choose action below 👇",
        "write_journal_prompt": "What would you like to journal?",
        "journal_saved": "Entry saved. Thank you for sharing.",
        "praise_response": "You're doing great! I'm proud of you ❤️",
        "panic_ready_response": (
            "Great! Let's do 4 rounds of Box breathing:\n"
            "Inhale — 4s\nHold — 4s\n"
            "Exhale — 4s\nHold — 4s\n\n"
            "Message when done."
        ),
        "unknown_command": "Unknown command.",
        "cancel_message": "Goodbye! Type /start if you need me.",
        "thank_you_anxiety": "Thank you for sharing: {}",
        "thank_you_insecurity": "I appreciate your trust: {}",
        "return_menu_prompt": "Press button below to return to menu.",
        "journal_cleared": "Journal cleared.",
        "ai_error": "AI connection error. Please try later.",
        "breathing_complete": "Great job! How do you feel now?"
    },
    "zh": {
        "choose_language": "🌍 请选择你的语言：",
        "lang_ru_selected": "你选择了俄语。欢迎！",
        "lang_en_selected": "你选择了英语。欢迎！",
        "lang_kk_selected": "你选择了哈萨克语。欢迎！",
        "lang_zh_selected": "你选择了中文。欢迎！",
        "greeting": (
            "你好！我是你的心理支持助手 🌿\n\n"
            "我可以在你感到以下情况时提供帮助：\n"
            "- 焦虑\n- 缺乏信心\n"
            "- 恐慌\n- 需要支持\n\n"
            "我们现在要处理哪个问题？"
        ),
        "menu_prompt": "请选择以下选项：",
        "anxiety": "焦虑",
        "insecurity": "缺乏信心",
        "panic": "恐慌",
        "support": "需要支持",
        "ai_prompt": "告诉我你的烦恼，我会尽力帮你。",
        "exit_ai": "退出支持",
        "journal_empty": "📭 日志目前是空的。",
        "ready_button": "准备好了",
        "menu_button": "菜单",
        "back_menu": "菜单",
        "anxiety_text": "告诉我你为什么感到焦虑，我们一起来解决。",
        "insecurity_text": "分享你感到不安的原因。",
        "panic_text": "准备好就点击『准备好了』开始呼吸练习。",
        "sos_button": "🚨 紧急求助",
        "sos_message": "你并不孤单，一切都会好起来。如果需要，请拨打电话。",
        "call_support": "📞 呼叫支持热线",
        "close_message": "❌ 关闭",
        "praise_button": "🌟 夸奖我",
        "clear_journal": "清空日志",
        "journal_button": "📔 日志",
        "reply_keyboard_hint": "请在下方选择操作 👇",
        "write_journal_prompt": "你想写入日志的内容是？",
        "journal_saved": "已保存。感谢你的分享。",
        "praise_response": "你做得很好！我为你感到骄傲 ❤️",
        "panic_ready_response": (
            "太棒了！我们来做四轮『盒式呼吸』：\n"
            "吸气 — 4秒\n屏息 — 4秒\n"
            "呼气 — 4秒\n屏息 — 4秒\n\n"
            "完成后告诉我。"
        ),
        "unknown_command": "未知指令。",
        "cancel_message": "再见！如需帮助请输入 /start。",
        "thank_you_anxiety": "谢谢你的分享：{}",
        "thank_you_insecurity": "谢谢你的信任：{}",
        "return_menu_prompt": "点击下方按钮返回菜单。",
        "journal_cleared": "日志已清空。",
        "ai_error": "AI连接错误，请稍后再试。",
        "breathing_complete": "干得好！现在感觉怎么样？"
    },
    "kk": {
        "choose_language": "🌍 Тілді таңдаңыз:",
        "lang_ru_selected": "Сіз орыс тілін таңдадыңыз. Қош келдіңіз!",
        "lang_en_selected": "Сіз ағылшын тілін таңдадыңыз. Қош келдіңіз!",
        "lang_kk_selected": "Сіз қазақ тілін таңдадыңыз. Қош келдіңіз!",
        "greeting": (
            "Сәлем! Мен сіздің жеке психологиялық көмекшісіңіз 🌿\n\n"
            "Мен көмектесе аламын:\n"
            "- Қобалжу кезінде\n- Сенімсіздікте\n"
            "- Дереу көмек қажет болса\n- Қолдау керек болса\n\n"
            "Қазір неге көмектесеін?"
        ),
        "menu_prompt": "Төмендегі опцияны таңдаңыз:",
        "anxiety": "Қобалжу",
        "insecurity": "Сенімсіздік",
        "panic": "Паника",
        "support": "Қолдау керек",
        "ai_prompt": "Сізді не мазалайды? Көмектесуге тырысамын.",
        "exit_ai": "Қолдаудан шығу",
        "journal_empty": "📭 Күнделік бос.",
        "ready_button": "Дайын",
        "menu_button": "Мәзір",
        "back_menu": "Мәзір",
        "anxiety_text": "Сізді не мазалайды? Бірге шешейік.",
        "insecurity_text": "Өзіңізді сенімсіз сезінетін нәрселеріңізбен бөлісіңіз.",
        "panic_text": "Демалыс жаттығуын бастау үшін 'Дайын' басыңыз.",
        "sos_button": "🚨 SOS",
        "sos_message": "Сіз жалғыз емессіз. Бәрі жақсы болады. Қажет болса, қоңырау шалыңыз.",
        "call_support": "📞 Қолдау қызметіне қоңырау шалу",
        "close_message": "❌ Жабу",        "praise_button": "🌟 Мақтау",
        "clear_journal": "Күнделікті тазалау",
        "journal_button": "📔 Күнделік",
        "reply_keyboard_hint": "Төмендегі әрекетті таңдаңыз 👇",
        "write_journal_prompt": "Күнделікке не жазуды қалайсыз?",
        "journal_saved": "Жазылым сақталды. Бөліскеніңізге рахмет.",
        "praise_response": "Сіз кереметсіз! Сізге мақтанамын ❤️",
        "panic_ready_response": (
            "Керемет! 4 рет 'Қорап' демалысын жасайық:\n"
            "Тыныс алу — 4с\nҰстау — 4с\n"
            "Шығару — 4с\nҰстау — 4с\n\n"
            "Аяқтаған соң хабарлаңыз."
        ),
        "unknown_command": "Белгісіз команда.",
        "cancel_message": "Сау болыңыз! Қажет болса /start теруіңіз.",
        "thank_you_anxiety": "Бөліскеніңізге рахмет: {}",
        "thank_you_insecurity": "Сеніміңіз үшін рахмет: {}",
        "return_menu_prompt": "Мәзірге оралу үшін төмендегі батырманы басыңыз.",
        "journal_cleared": "Күнделік тазаланды.",
        "ai_error": "AI қосылу қатесі. Кейінірек көріңіз.",
        "breathing_complete": "Керемет! Қазір қалай сезінесіз?"
    }
}

# --- Клавиатуры ---
def lang_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("Қазақша 🇰🇿", callback_data="lang_kk"),
            InlineKeyboardButton("中文 🇨🇳", callback_data="lang_zh")
        ]
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
    await context.bot.send_message(
           chat_id=query.message.chat_id,
           text=TEXTS[lang_code]["reply_keyboard_hint"],
           reply_markup=bottom_menu_keyboard(lang_code)
       )
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
        await query.edit_message_text(TEXTS[lang]["panic_text"], reply_markup=back_menu_keyboard(lang))
        return PANIC

    elif data == "support":
        await query.edit_message_text(TEXTS[lang]["ai_prompt"], reply_markup=ai_support_keyboard(lang))
        return AI_SUPPORT

    elif data == "journal":
        await query.edit_message_text(TEXTS[lang]["write_journal_prompt"], reply_markup=back_menu_keyboard(lang))
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            reply_markup=ReplyKeyboardRemove()  # удаляет нижнюю клавиатуру
        )
        return JOURNAL_WRITE

    elif data == "sos":
        await query.edit_message_text(TEXTS[lang]["sos_message"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    elif data == "praise":
        await query.edit_message_text(TEXTS[lang]["praise_response"], reply_markup=main_menu_keyboard(lang))
        return CHOOSING

    elif data == "back_menu":
        await query.edit_message_text(TEXTS[lang]["greeting"], reply_markup=main_menu_keyboard(lang))
    # Добавляем нижнюю клавиатуру
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=TEXTS[lang]["reply_keyboard_hint"],
            reply_markup=bottom_menu_keyboard(lang)
        )
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
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=TEXTS[lang]["reply_keyboard_hint"],
            reply_markup=bottom_menu_keyboard(lang)
        )
        return CHOOSING

    else:
        await query.edit_message_text(TEXTS[lang]["unknown_command"])
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=TEXTS[lang]["reply_keyboard_hint"],
            reply_markup=bottom_menu_keyboard(lang)
        )
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
    lang = context.user_data.get("lang", "en")
    
    # Инициализация состояния для техники 5-4-3-2-1
    if 'anxiety_step' not in context.user_data:
        context.user_data['anxiety_step'] = 5
        context.user_data['anxiety_items'] = {}
        
        # Первое сообщение с инструкцией
        step_prompts = {
            "ru": "Назовите 5 вещей, которые вы ВИДЕТЕ вокруг себя:",
            "en": "Name 5 things you can SEE around you:",
            "zh": "说出你能看到的5样东西:",
            "kk": "Қоршаған ортадан 5 КӨРІНЕТІН нәрсені атаңыз:"
        }
        await update.message.reply_text(step_prompts.get(lang, step_prompts["en"]),
                                      reply_markup=ReplyKeyboardRemove())
        return ANXIETY
    
    # Получаем текущий шаг
    current_step = context.user_data['anxiety_step']
    user_text = update.message.text
    
    # Сохраняем ответ пользователя
    context.user_data['anxiety_items'][current_step] = user_text
    
    # Переходим к следующему шагу
    next_step = current_step - 1
    
    if next_step >= 1:
        context.user_data['anxiety_step'] = next_step
        
        step_prompts = {
            4: {
                "ru": "Теперь назовите 4 вещи, которые вы можете ПОТРОГАТЬ:",
                "en": "Now name 4 things you can TOUCH:",
                "zh": "现在说出你能触摸的4样东西:",
                "kk": "Енді 4 ҰСТАЙ АЛАТЫН нәрсені атаңыз:"
            },
            3: {
                "ru": "Назовите 3 вещи, которые вы СЛЫШИТЕ прямо сейчас:",
                "en": "Name 3 things you can HEAR right now:",
                "zh": "说出你现在能听到的3种声音:",
                "kk": "Қазір 3 ЕСТІЛЕТІН нәрсені атаңыз:"
            },
            2: {
                "ru": "Назовите 2 вещи, которые вы можете ПОЧУВСТВОВАТЬ (запах или вкус):",
                "en": "Name 2 things you can SMELL or TASTE:",
                "zh": "说出你能闻到或尝到的2样东西:",
                "kk": "2 ИІСЕ АЛАСЫЗ немесе ДӘМІН ТАТАСЫЗ нәрсені атаңыз:"
            },
            1: {
                "ru": "Назовите 1 вещь, за которую вы БЛАГОДАРНЫ:",
                "en": "Name 1 thing you're GRATEFUL for:",
                "zh": "说出1件你感激的事情:",
                "kk": "1 РАХМЕТ БІЛДІРЕТІН нәрсені атаңыз:"
            }
        }
        
        await update.message.reply_text(step_prompts[next_step].get(lang, step_prompts[next_step]["en"]))
        return ANXIETY
    else:
        # Все шаги завершены, сохраняем в дневник
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        items = context.user_data['anxiety_items']
        
        journal_entry = {
            "ru": f"{now} — Техника 5-4-3-2-1:\n"
                 f"👁 Вижу: {items.get(5, '-')}\n"
                 f"✋ Осязаю: {items.get(4, '-')}\n"
                 f"👂 Слышу: {items.get(3, '-')}\n"
                 f"👃 Чувствую: {items.get(2, '-')}\n"
                 f"❤ Благодарен за: {items.get(1, '-')}",
                 
            "en": f"{now} — 5-4-3-2-1 Technique:\n"
                 f"👁 See: {items.get(5, '-')}\n"
                 f"✋ Touch: {items.get(4, '-')}\n"
                 f"👂 Hear: {items.get(3, '-')}\n"
                 f"👃 Smell/Taste: {items.get(2, '-')}\n"
                 f"❤ Grateful for: {items.get(1, '-')}",
                 
            "zh": f"{now} — 5-4-3-2-1 技巧:\n"
                 f"👁 看到: {items.get(5, '-')}\n"
                 f"✋ 触摸: {items.get(4, '-')}\n"
                 f"👂 听到: {items.get(3, '-')}\n"
                 f"👃 闻到/尝到: {items.get(2, '-')}\n"
                 f"❤ 感激: {items.get(1, '-')}",
                 
            "kk": f"{now} — 5-4-3-2-1 Әдісі:\n"
                 f"👁 Көремін: {items.get(5, '-')}\n"
                 f"✋ Ұстаймын: {items.get(4, '-')}\n"
                 f"👂 Естимін: {items.get(3, '-')}\n"
                 f"👃 Иіс/Дәм: {items.get(2, '-')}\n"
                 f"❤ Рахмет: {items.get(1, '-')}"
        }
        
        # Сохраняем в дневник
        context.user_data.setdefault('journal', []).append(journal_entry.get(lang, journal_entry["en"]))
        
        # Создаем клавиатуру с кнопкой "Мне лучше"
        feeling_better_button = {
            "ru": "😊 Мне лучше",
            "en": "😊 I feel better", 
            "zh": "😊 我感觉好些了",
            "kk": "😊 Жақсырап кеттім"
        }
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(feeling_better_button.get(lang, "😊 I feel better"), 
             callback_data="back_menu")]
        ])
        
        # Отправляем итоговое сообщение
        summary_text = {
            "ru": "Отлично! Техника завершена и сохранена в дневник.\n"
                 "Если чувствуете себя лучше, вернитесь в меню:",
            "en": "Great! Technique completed and saved to journal.\n"
                 "If you feel better, return to menu:",
            "zh": "太好了！技巧已完成并保存到日记中。\n"
                 "如果感觉好些了，返回菜单:",
            "kk": "Керемет! Әдіс аяқталды және күнделікке сақталды.\n"
                 "Егер өзіңізді жақсырақ сезінетін болсаңыз, мәзірге оралыңыз:"
        }
        
        await update.message.reply_text(
            summary_text.get(lang, summary_text["en"]),
            reply_markup=keyboard
        )
        
        # Очищаем временные данные
        del context.user_data['anxiety_step']
        del context.user_data['anxiety_items']
        
        return ANXIETY

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
        # Локализованное сообщение
        start_breathing_text = {
            "ru": "Начинаем дыхательную технику...",
            "en": "Starting the breathing exercise...",
            "kk": "Тыныс алу техникасын бастаймыз...",
            "zh": "我们开始呼吸练习..."
        }.get(lang, "Starting the breathing exercise...")

        await query.edit_message_text(start_breathing_text)
        asyncio.create_task(panic_breathing_task(context.bot, chat_id, context))
        return PANIC

    elif data == "save_panic":
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        journal = context.user_data.get("journal", [])

        panic_journal_entry = {
            "ru": "техника при панике (дыхание квадратом)",
            "en": "panic technique (box breathing)",
            "kk": "паникаға арналған техника (квадрат тыныс алу)",
            "zh": "恐慌时的技术（方形呼吸）"
        }.get(lang, "panic technique (box breathing)")

        journal.append(f"{now} — {panic_journal_entry}")
        context.user_data["journal"] = journal

        saved_text = {
            "ru": "✅ Сохранено в журнал.",
            "en": "✅ Saved to journal.",
            "kk": "✅ Журналға сақталды.",
            "zh": "✅ 已保存到日记。"
        }.get(lang, "✅ Saved to journal.")

        await query.edit_message_text(saved_text)
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
    lang = context.user_data.get("lang", "en")
    user_text = update.message.text

    # Локализованный system prompt
    system_prompts = {
        "ru": "Ты — личный психолог пользователя. Отвечай тепло, с сочувствием и поддержкой на русском языке.",
        "en": "You are the user's personal psychologist. Respond warmly, with empathy and support in English.",
        "kk": "Сіз пайдаланушының жеке психологысыз. Жылы, жанашыр және қолдаушы түрде қазақ тілінде жауап беріңіз.",
        "zh": "您是用户的个人心理学家。 用中文热烈、同情、支持地回应。",
    }

    system_prompt = system_prompts.get(lang, system_prompts["en"])

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=1,
            max_tokens=500
        )
        ai_reply = response["choices"][0]["message"]["content"]

        # Разбиваем длинные сообщения, если нужно
        for chunk in [ai_reply[i:i+4096] for i in range(0, len(ai_reply), 4096)]:
            await update.message.reply_text(chunk, reply_markup=ai_support_keyboard(lang) if chunk == ai_reply[-4096:] else None)

    except Exception as e:
        print(f"OpenAI error: {e}")
        ai_reply = TEXTS[lang]["ai_error"]
        await update.message.reply_text(ai_reply, reply_markup=ai_support_keyboard(lang))

    return AI_SUPPORT



async def handle_panic_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    breathing_intro = {
        "ru": "Давай попробуем технику дыхания «квадрат»: вдох — задержка — выдох — задержка.\nСейчас начнём цикл дыхания...",
        "en": "Let's try the box breathing technique: inhale — hold — exhale — hold.\nWe'll start a breathing cycle now...",
        "kk": "«Шаршы тыныс алу» техникасын қолданып көрейік: тыныс алу — кідіріс — тыныс шығару — кідіріс.\nҚазір тыныс алу циклі басталады...",
        "zh": "让我们试试“方形呼吸”技巧：吸气 — 停顿 — 呼气 — 停顿。\n现在开始呼吸循环..."
    }.get(lang, "Let's try the box breathing technique...")

    await update.message.reply_text(breathing_intro, reply_markup=ReplyKeyboardRemove())
    context.user_data["panic_cycles"] = 0
    return await handle_panic_breathing(update, context)



async def panic_ready_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    lang = context.user_data.get("lang", "ru")
    start_msg = {
        "ru": "Начинаем дыхательную технику...",
        "en": "Starting the breathing technique...",
        "kk": "Тыныс алу техникасын бастаймыз...",
        "zh": "我们开始呼吸练习..."
    }.get(lang, "Starting breathing...")

    asyncio.create_task(panic_breathing_task(context.bot, chat_id, context))
    await query.edit_message_text(start_msg)

    return PANIC



async def panic_breathing_task(bot, chat_id, context):
    lang = context.user_data.get("lang", "ru")

    breathing_steps_localized = {
        "ru": [("🌬 Вдохни", 4), ("⏸ Задержи дыхание", 4), ("💨 Выдохни", 4), ("⏸ Задержи дыхание", 4)],
        "en": [("🌬 Inhale", 4), ("⏸ Hold your breath", 4), ("💨 Exhale", 4), ("⏸ Hold your breath", 4)],
        "kk": [("🌬 Дем ал", 4), ("⏸ Тыныс ұста", 4), ("💨 Дем шығар", 4), ("⏸ Тыныс ұста", 4)],
        "zh": [("🌬 吸气", 4), ("⏸ 屏住呼吸", 4), ("💨 呼气", 4), ("⏸ 再次屏住呼吸", 4)]
    }

    breathing_steps = breathing_steps_localized.get(lang, breathing_steps_localized["en"])

    for step, seconds in breathing_steps:
        msg = await bot.send_message(chat_id=chat_id, text=step)
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)

    final_msg = {
        "ru": "Ты молодец! Как себя чувствуешь?",
        "en": "Well done! How are you feeling?",
        "kk": "Жарайсың! Өзіңді қалай сезініп тұрсың?",
        "zh": "干得好！你现在感觉如何？"
    }.get(lang, "Well done! How are you feeling?")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                {"ru": "✅ повторить", "en": "✅ Repeat", "kk": "✅ Қайталау", "zh": "✅  重复"}.get(lang),
                callback_data="panic_ready"
            ),
            InlineKeyboardButton(
                {"ru": "⬅️ Мне лучше", "en": "⬅️ I feel better", "kk": "⬅️ Жағдайым жақсарып қалды", "zh": "⬅️ 我感觉好多了"}.get(lang),
                callback_data="back_menu"
            )
        ],
        [
            InlineKeyboardButton(
                {"ru": "📓 Сохранить в дневник", "en": "📓 Save to journal", "kk": "📓 Журналға сақтау", "zh": "📓 保存到日记"}.get(lang),
                callback_data="save_panic"
            )
        ]
    ])

    await bot.send_message(chat_id=chat_id, text=final_msg, reply_markup=keyboard)


async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    texts = TEXTS[lang]
    text = update.message.text.strip()

    # Прерываем активные техники
    context.user_data["finish"] = True
    context.user_data["state"] = None

    if text == texts["sos_button"]:
        support_number = "77058661243"  # Без + и пробелов
        
        await update.message.reply_text(
            texts["sos_message"],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    texts["call_support"],
                    url=f"tg://resolve?phone={support_number}"  # Специальная схема Telegram
                )],
                [InlineKeyboardButton(texts["back_menu"], callback_data="back_menu")]
            ])
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

async def close_sos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.delete()



async def journal_save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    entry = update.message.text
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    context.user_data.setdefault("journal", []).append(f"{now} — {entry}")
    await update.message.reply_text(TEXTS[lang]["journal_saved"], reply_markup=bottom_menu_keyboard(lang))
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