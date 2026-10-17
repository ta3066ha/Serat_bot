
import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from balethon import Client
from balethon.objects import (
    ReplyKeyboard,
    ReplyKeyboardButton,
    InlineKeyboard,
    InlineKeyboardButton,
)

from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen

print("BOT_TOKEN found:", bool(os.getenv("BOT_TOKEN")))

# ---------- Configuration ----------

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_COMMAND = os.getenv("ADMIN_COMMAND", "")
if not BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("BOT_TOKEN or GROQ_API_KEY is missing!")

BASE_DIR = Path(__file__).resolve().parent
MODEL_FILE = BASE_DIR / "Model_h.txt"

MODEL = "openrouter/free"
MAX_HISTORY = 10

MODEL = "openai/gpt-oss-20b"

BASE_URL = "https://api.groq.com/openai/v1"

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=BASE_URL,
    timeout=45.0,
    max_retries=1
)


bot = Client(BOT_TOKEN)

# ---------- User data ----------

user_data = {}
user_states = {}
user_messages = {}
user_locks = {}

from openai import OpenAI
from balethon import Client
from balethon.objects import (
    ReplyKeyboard,
    ReplyKeyboardButton,
    InlineKeyboard,
    InlineKeyboardButton,
)

import asyncio
import os
from dotenv import load_dotenv


# =========================================================
# تنظیمات اولیه
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_COMMAND = os.getenv("ADMIN_COMMAND", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN در متغیرهای محیطی تنظیم نشده است.")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY در متغیرهای محیطی تنظیم نشده است.")

if not ADMIN_COMMAND:
    print("هشدار: ADMIN_COMMAND تنظیم نشده؛ مدیریت حافظه غیرفعال است.")


# =========================================================
# تنظیمات Groq
# =========================================================

MODEL = "openai/gpt-oss-20b"
BASE_URL = "https://api.groq.com/openai/v1"

MAX_HISTORY = 10

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=BASE_URL,
    timeout=45.0,
    max_retries=1,
)


# =========================================================
# اتصال به Bale
# =========================================================

bot = Client(BOT_TOKEN)


# =========================================================
# اطلاعات کاربران
# =========================================================

user_data = {}
user_states = {}
user_messages = {}


# =========================================================
# فایل System Prompt
# =========================================================

MODEL_FILE = os.path.join(BASE_DIR, "Model_h.txt")


def load_system_prompt():
    with open(MODEL_FILE, "r", encoding="utf-8") as file:
        return file.read()


Txt_Model = load_system_prompt()
system_prompt = Txt_Model


# =========================================================
# بارگذاری دوباره System Prompt
# =========================================================

def reload_system_prompt():
    global Txt_Model, system_prompt

    Txt_Model = load_system_prompt()
    system_prompt = Txt_Model

    for chat_id in user_messages:
        if user_messages[chat_id]:
            user_messages[chat_id][0] = {
                "role": "system",
                "content": system_prompt,
            }


# =========================================================
# ساخت حافظه اولیه برای کاربر
# =========================================================

def get_user_messages(chat_id):
    if chat_id not in user_messages:
        user_messages[chat_id] = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

    return user_messages[chat_id]


# =========================================================
# ارسال درخواست به Groq
# =========================================================

async def ask_ai(chat_id, user_message):
    messages = get_user_messages(chat_id)

    messages.append({
        "role": "user",
        "content": user_message,
    })

    # System Prompt + حداکثر 10 پیام اخیر
    history = [messages[0]] + messages[-MAX_HISTORY:]

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=MODEL,
            messages=history,
            temperature=0.7,
            max_completion_tokens=1024,
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "متأسفانه پاسخی دریافت نکردم."

        messages.append({
            "role": "assistant",
            "content": answer,
        })

        # اطلاعات مصرف در گزارش‌های Render
        if response.usage:
            print("Input Tokens:", response.usage.prompt_tokens)
            print("Output Tokens:", response.usage.completion_tokens)
            print("Total Tokens:", response.usage.total_tokens)

        # حفظ تاریخچه در حافظه، بدون حذف System Prompt
        recent = messages[-MAX_HISTORY:]
        user_messages[chat_id] = [messages[0]] + recent

        return answer

    except Exception as e:
        print("GROQ ERROR:", repr(e))

        # خطاهای محدودیت سهمیه یا نرخ درخواست
        status_code = getattr(e, "status_code", None)

        if status_code == 429:
            return (
                "تعداد درخواست‌های مجاز هوش مصنوعی فعلاً تمام شده "
                "یا سرعت درخواست‌ها بیش از حد مجاز است. "
                "لطفاً کمی بعد دوباره امتحان کنید."
            )

        if status_code in (401, 403):
            return (
                "کلید API یا دسترسی مدل مشکل دارد. "
                "تنظیمات Groq را بررسی کنید."
            )

        if status_code == 400:
            return (
                "درخواست توسط مدل پذیرفته نشد. "
                "نام مدل و تنظیمات درخواست را بررسی کنید."
            )

        return (
            "متأسفانه در ارتباط با هوش مصنوعی مشکلی پیش آمد. "
            "لطفاً بعداً دوباره امتحان کنید."
        )


# =========================================================
# مدیریت پیام‌ها
# =========================================================

@bot.on_message()
async def all_messages(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    # =====================================================
    # حالت اضافه کردن به حافظه
    # =====================================================

    if user_states.get(chat_id) == "ap":
        if text == "E":
            user_states.pop(chat_id, None)
            await message.reply(
                "از حالت اضافه کردن حافظه بیرون آمدید."
            )
            return

        with open(MODEL_FILE, "a", encoding="utf-8") as file:
            file.write(f"\n\n{text}")

        reload_system_prompt()

        user_states.pop(chat_id, None)

        await message.reply(
            "متن شما با موفقیت به حافظه اضافه شد! ✅"
        )
        return

    # =====================================================
    # حالت تغییر کامل حافظه
    # =====================================================

    if user_states.get(chat_id) == "wr":
        if text == "E":
            user_states.pop(chat_id, None)
            await message.reply(
                "از حالت تغییر حافظه بیرون آمدید."
            )
            return

        with open(MODEL_FILE, "w", encoding="utf-8") as file:
            file.write(text)

        reload_system_prompt()

        user_states.pop(chat_id, None)

        await message.reply(
            "حافظه با موفقیت تغییر کرد! ✅"
        )
        return

    # =====================================================
    # /start
    # =====================================================

    if text == "/start":
        user_states.pop(chat_id, None)
        user_data.pop(chat_id, None)
        user_messages.pop(chat_id, None)

        keyboard = ReplyKeyboard(
            ["کانال بله", "راهنما"],
            ["شروع چت با هوش مصنوعی"],
            resize=True,
        )

        await message.reply(
            "سلام! 👋\n"
            "به چت‌بات کانون صراط خوش آمدید.\n\n"
            "از دکمه‌های زیر استفاده کنید.",
            reply_markup=keyboard,
        )
        return

    # =====================================================
    # راهنما
    # =====================================================

    if text == "راهنما":
        await message.reply(
            "راهنما:\n\n"
            "🤖 برای صحبت با هوش مصنوعی، گزینه "
            "«شروع چت با هوش مصنوعی» را انتخاب کنید.\n\n"
            "🚪 برای خروج از حالت چت، کلمه «خروج» را بفرستید."
        )
        return

    # =====================================================
    # کانال بله
    # =====================================================

    if text == "کانال بله":
        keyboard = InlineKeyboard(
            [
                InlineKeyboardButton(
                    text="کانال بله ما",
                    url="https://ble.ir/knserat",
                )
            ]
        )

        await message.reply(
            "لینک کانال کانون صراط نظرآباد/هشتگرد:",
            reply_markup=keyboard,
        )
        return

    # =====================================================
    # شروع چت
    # =====================================================

    if text == "شروع چت با هوش مصنوعی":
        user_states[chat_id] = "ai_chat"
        get_user_messages(chat_id)

        await message.reply(
            "😊 سلام!\n"
            "من چت‌بات کانون صراط هستم.\n\n"
            "سؤالتان را بپرسید.\n"
            "برای خروج، کلمه «خروج» را بفرستید."
        )
        return

    # =====================================================
    # خروج از چت
    # =====================================================

    if text == "خروج":
        user_states.pop(chat_id, None)

        await message.reply(
            "از حالت چت با هوش مصنوعی خارج شدید. 👋"
        )
        return

    # =====================================================
    # فعال‌سازی مدیریت حافظه
    # =====================================================

    if ADMIN_COMMAND and text == ADMIN_COMMAND:
        keyboard = InlineKeyboard(
            [
                InlineKeyboardButton(
                    text="اضافه کردن",
                    callback_data="append",
                ),
                InlineKeyboardButton(
                    text="تغییر دادن",
                    callback_data="write",
                ),
            ]
        )

        await message.reply(
            "حالت تغییر حافظه چت‌بات فعال شد!"
        )

        await asyncio.sleep(1)

        await message.reply("حافظه فعلی چت‌بات 👇")

        await asyncio.sleep(1)

        await message.reply_document(MODEL_FILE)

        await asyncio.sleep(1)

        await message.reply(
            "اگر می‌خواهید متنی به حافظه اضافه کنید، "
            "«اضافه کردن» را بزنید.\n\n"
            "اگر می‌خواهید کل حافظه را جایگزین کنید، "
            "«تغییر دادن» را بزنید.",
            reply_markup=keyboard,
        )
        return

    # =====================================================
    # پیام‌های مربوط به هوش مصنوعی
    # =====================================================

    if user_states.get(chat_id) == "ai_chat":
        if not text:
            await message.reply("لطفاً پیام متنی ارسال کنید.")
            return

        answer = await ask_ai(chat_id, text)

        await message.reply(answer)
        return


# =========================================================
# Callback دکمه‌های مدیریت حافظه
# =========================================================

@bot.on_callback_query()
async def callback_handler(callback_query):
    chat_id = callback_query.message.chat.id

    if callback_query.data == "append":
        user_states[chat_id] = "ap"

        await callback_query.message.reply(
            "متن جدیدی که می‌خواهید به System Prompt اضافه شود "
            "را بفرستید.\n\nبرای لغو، E را ارسال کنید."
        )

    elif callback_query.data == "write":
        user_states[chat_id] = "wr"

        await callback_query.message.reply(
            "متن جدید System Prompt را کامل ارسال کنید.\n\n"
            "برای لغو، E را ارسال کنید."
        )


# =========================================================
# اجرای بات
# =========================================================

# ---------- HTTP Server + Mutual Pinging ----------

PORT = int(os.environ.get("PORT", "10000"))
PING_URL = os.environ.get("PING_URL", "").strip()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b'{"status":"ok","service":"bale-bot"}'

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def run_http_server():
    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )
    print(f"HTTP health server started on port {PORT}")
    server.serve_forever()


def ping_second_service():
    while True:
        if PING_URL:
            try:
                with urlopen(PING_URL, timeout=20) as response:
                    print("Second service ping:", response.status)
            except Exception as exc:
                print("Second service ping failed:", repr(exc))

        time.sleep(60)
if __name__ == "__main__":
    threading.Thread(
        target=run_http_server,
        daemon=True
    ).start()

    threading.Thread(
        target=ping_second_service,
        daemon=True
    ).start()

    print("Bot is running...")
    bot.run()