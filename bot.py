import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import re

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8740824185:AAFjJA4DKk2jgYS_dCOQePr4UxX0VxqV6aU"  # Client token
REQUIRED_CHANNEL = "@your_channel_username"  # Client ka channel username (@ ke sath)
ADMIN_ID = 8842433415  # Client (DIXIT) Admin ID
UPINUMBER_OR_LINK = "shivamshrivastava98329@okaxis"  # Updated UPI ID
BEP20_ADDRESS = "0xCffF52346B7d75e1E3106310BAB46a71989E63d0"  # Updated BEP20 Address

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------- DATABASE SETUP (SQLite) -----------------
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            name TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id, name="User"):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.execute('INSERT INTO users (user_id, balance, name) VALUES (?, ?, ?)', (user_id, 0.0, name))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    conn.close()
    return balance

def update_balance(user_id, amount):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# ----------------- HELPER FUNCTIONS -----------------
def check_force_join(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"Force join error: {e}")
        return True

def force_join_markup():
    markup = InlineKeyboardMarkup()
    btn_channel = InlineKeyboardButton("📢 Join Channel First", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")
    btn_check = InlineKeyboardButton("✅ Joined / Verify", callback_data="verify_join")
    markup.add(btn_channel)
    markup.add(btn_check)
    return markup

def main_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("🏨 Book Hotel")
    btn2 = KeyboardButton("✈️ Book Flight")
    btn3 = KeyboardButton("💳 Wallet & Buy Balance")
    btn4 = KeyboardButton("💼 Become Reseller")
    btn5 = KeyboardButton("📞 Support")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

# ----------------- HANDLERS -----------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    get_user(user_id, name)

    if not check_force_join(user_id):
        bot.send_message(
            message.chat.id,
            "❌ **Access Denied!**\n\nBot use karne ke liye pehle hamare channel ko join karein:",
            parse_mode="Markdown",
            reply_markup=force_join_markup()
        )
        return

    bot.send_message(
        message.chat.id,
        f"👋 Welcome {name}!\n\nAap Hotel, Flight booking aur Reseller plans ke liye neeche diye gaye buttons ka use karein.",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join_callback(call):
    if check_force_join(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Success! Aap verified ho chuke hain.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            "🎉 Thank you for joining! Aap ab bot use kar sakte hain.",
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    user_id = message.from_user.id

    if not check_force_join(user_id):
        bot.send_message(
            message.chat.id,
            "⚠️ Kripya pehle hamara channel join karein!",
            reply_markup=force_join_markup()
        )
        return

    text = message.text

    if text == "🏨 Book Hotel":
        msg_text = (
            "🏨 **HOTEL BOOKING**\n\n"
            "💡 *Check your booking price on MakeMyTrip and add balance of -35% discount!*\n"
            "Original price me se **35% kam** karke balance add karein.\n\n"
            "👇 *Kripya City name aur Check-in date bhejein:*"
        )
        msg = bot.send_message(message.chat.id, msg_text, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_hotel_booking)

    elif text == "✈️ Book Flight":
        msg_text = (
            "✈️ **FLIGHT BOOKING**\n\n"
            "💡 *Check your booking price on MakeMyTrip and add balance of -35% discount!*\n"
            "Original fare me se **35% kam** karke balance add karein.\n\n"
            "👇 *Kripya From, To aur Flight Date bhejein:*"
        )
        msg = bot.send_message(message.chat.id, msg_text, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_flight_booking)

    elif text == "💳 Wallet & Buy Balance":
        balance = get_user(user_id)
        pay_markup = InlineKeyboardMarkup()
        btn_pay = InlineKeyboardButton("📲 Pay via UPI", url=f"https://upiqr.in/api/qr?name=BookingBot&vpa={UPINUMBER_OR_LINK}")
        btn_submit = InlineKeyboardButton("📤 Submit Screenshot & UTR", callback_data="submit_payment")
        pay_markup.add(btn_pay)
        pay_markup.add(btn_submit)

        bot.send_message(
            message.chat.id,
            f"💳 **Your Wallet:**\n\n"
            f"💰 Current Balance: `₹{balance}`\n\n"
            f"📌 **Payment Details:**\n"
            f"🔹 **UPI ID:** `{UPINUMBER_OR_LINK}`\n"
            f"🔹 **BEP20 Address:** `{BEP20_ADDRESS}`\n\n"
            f"💡 *MakeMyTrip se original fair check karke uspar -35% discount karke paise add karein.*\n\n"
            f"Payment karne ke baad apna **Screenshot aur UTR/TxID** bhejne ke liye neeche wale button par click karein.",
            parse_mode="Markdown",
            reply_markup=pay_markup
        )

    elif text == "💼 Become Reseller":
        reseller_markup = InlineKeyboardMarkup()
        btn_submit = InlineKeyboardButton("📤 Submit Payment Proof", callback_data="submit_payment")
        reseller_markup.add(btn_submit)

        reseller_text = (
            "💼 **BECOME A RESELLER**\n\n"
            "🔥 *Special Reseller Deposit Plans:*\n\n"
            "💎 **Plan 1:** Deposit **10,000 INR / 100 USDT** ➡️ Get **30,000 INR / 300 USDT** Balance\n"
            "💎 **Plan 2:** Deposit **25,000 INR / 250 USDT** ➡️ Get **65,000 INR / 650 USDT** Balance\n\n"
            "📌 **Payment Details:**\n"
            f"🔹 **UPI ID:** `{UPINUMBER_OR_LINK}`\n"
            f"🔹 **BEP20 Address:** `{BEP20_ADDRESS}`\n\n"
            "Payment karne ke baad Screenshot aur UTR/TxID submit karein!"
        )
        bot.send_message(message.chat.id, reseller_text, parse_mode="Markdown", reply_markup=reseller_markup)

    elif text == "📞 Support":
        bot.send_message(message.chat.id, "📞 Kisi bhi help ya query ke liye Admin se contact karein: @ur_dixit")

def process_hotel_booking(message):
    bot.send_message(message.chat.id, f"✅ Hotel Booking Request Received!\nDetails: {message.text}\n\nHamari team jald hi aapse contact karegi.")

def process_flight_booking(message):
    bot.send_message(message.chat.id, f"✅ Flight Booking Request Received!\nDetails: {message.text}\n\nHamari team rates check karke update karegi.")

# Payment Submission Flow
@bot.callback_query_handler(func=lambda call: call.data == "submit_payment")
def payment_submission_prompt(call):
    msg = bot.send_message(call.message.chat.id, "📸 Kripya payment ka **Screenshot** aur uske sath caption me **UTR / TxID Number & Amount** (jaise: `UTR12345678, 10000`) likh kar bhejein:")
    bot.register_next_step_handler(msg, receive_payment_proof)

def receive_payment_proof(message):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Kripya screenshot (photo) ke sath UTR aur Amount bhejein. Dobara menu se try karein.")
        return
    
    file_id = message.photo[-1].file_id
    caption = message.caption if message.caption else "No UTR/Details provided"
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    admin_markup = InlineKeyboardMarkup()
    btn_approve = InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}")
    btn_reject = InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}")
    admin_markup.add(btn_approve, btn_reject)

    admin_text = (
        f"🔔 **New Payment Verification Request!**\n\n"
        f"👤 User: @{username} (ID: `{user_id}`)\n"
        f"📝 Details/UTR/Amount: {caption}\n\n"
        f"Kripya verification ke baad approve ya reject karein:"
    )

    try:
        bot.send_photo(ADMIN_ID, file_id, caption=admin_text, parse_mode="Markdown", reply_markup=admin_markup)
        bot.send_message(message.chat.id, "✅ Aapka payment proof admin ke pas bhej diya gaya hai. Verification ke baad balance update ho jayega!")
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Admin ko message bhejne mein error aaya. Kripya support se contact karein.")

# Admin Action Handler (Approve / Reject)
@bot.callback_query_handler(func=lambda call: call.data.startswith("app_") or call.data.startswith("rej_"))
def admin_action_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Aap admin nahi hain!", show_alert=True)
        return

    data = call.data
    action, user_id_str = data.split("_")
    target_user_id = int(user_id_str)

    if action == "app":
        try:
            caption = call.message.caption or ""
            numbers = re.findall(r'\d+', caption)
            amount = float(numbers[-1]) if numbers else 1000.0
            
            update_balance(target_user_id, amount)
            bot.answer_callback_query(call.id, f"✅ Approved! Amount added.")
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n**STATUS: APPROVED ✅**", parse_mode="Markdown")
            bot.send_message(target_user_id, f"🎉 Congratulations! Aapka payment approve ho gaya hai. Aapke wallet me balance add kar diya gaya hai.")
        except Exception as e:
            bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)

    elif action == "rej":
        bot.answer_callback_query(call.id, "❌ Payment Rejected.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n**STATUS: REJECTED ❌**", parse_mode="Markdown")
        bot.send_message(target_user_id, "❌ Maaf kijiye, aapka payment proof verify nahi ho paya aur reject kar diya gaya hai. Support se contact karein.")

print("Bot is running...")
bot.infinity_polling()
