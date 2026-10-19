import telebot
from telebot import types

# Bot Token
API_TOKEN = '8740824185:AAFJJA4DKZJgYS_dc0QEPr4UXoVxQv6aU'

bot = telebot.TeleBot(API_TOKEN)

# Admin & Payment Details
ADMIN_ID = 8842433415
ADMIN_USERNAME = "@ur_dixit"
UPI_ID = "shivamshrivastava98329@okaxis"
BEP20_ADDRESS = "0xCffF52346B7d75e1E3106310BAB46a71989E63d0"

# Service Pricing (Original Price)
SERVICES = {
    "hotel": {"name": "🏨 Hotel Booking", "price": 1000},
    "flight": {"name": "✈️ Flight Booking", "price": 2000},
    "package": {"name": "🏖️ Holiday Package", "price": 5000}
}

# User state storage
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🏨 Hotel Booking", callback_data="svc_hotel")
    btn2 = types.InlineKeyboardButton("✈️ Flight Booking", callback_data="svc_flight")
    btn3 = types.InlineKeyboardButton("🏖️ Holiday Package", callback_data="svc_package")
    markup.add(btn1, btn2, btn3)

    welcome_text = (
        "✈️ **Welcome to DIXIT TRAVELS PRO!** 🏨\n\n"
        "🔥 Book Hotels & Flights at **35% OFF**!\n\n"
        "✅ Select your preferred plan.\n"
        "💰 Get a 35% discount on the plan price.\n"
        "💳 Add the remaining balance to your account.\n"
        "🌐 Check booking details on MakeMyTrip and proceed with your booking.\n\n"
        "✈️ **DIXIT TRAVELS PRO — Travel More, Save More!**"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('svc_'))
def handle_service_selection(call):
    svc_key = call.data.split('_')[1]
    svc_info = SERVICES.get(svc_key)
    
    if svc_info:
        orig_price = svc_info["price"]
        discount_price = orig_price * 0.65  # 35% Discount Applied
        
        user_data[call.from_user.id] = {
            "service": svc_info["name"],
            "original_price": orig_price,
            "final_price": discount_price
        }

        markup = types.InlineKeyboardMarkup()
        pay_upi = types.InlineKeyboardButton("💳 Pay via UPI", callback_data="pay_upi")
        pay_crypto = types.InlineKeyboardButton("🪙 Pay via BEP20 (Crypto)", callback_data="pay_crypto")
        markup.add(pay_upi, pay_crypto)

        text = (
            f"📋 **Selected Service:** {svc_info['name']}\n\n"
            f"💵 Original Price: ₹{orig_price}\n"
            f"🎉 **Discounted Price (35% OFF): ₹{discount_price:.2f}**\n\n"
            f"Please select your payment method below:"
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['pay_upi', 'pay_crypto'])
def handle_payment_method(call):
    uid = call.from_user.id
    data = user_data.get(uid)
    
    if not data:
        bot.answer_callback_query(call.id, "Session expired. Please start again with /start.")
        return

    amount = data["final_price"]

    if call.data == 'pay_upi':
        payment_text = (
            f"💳 **UPI Payment Details**\n\n"
            f"💰 **Amount to Pay:** ₹{amount:.2f}\n"
            f"📲 **UPI ID:** `{UPI_ID}`\n\n"
            f"After completing the payment, please upload the screenshot of the payment receipt here."
        )
    else:
        payment_text = (
            f"🪙 **Crypto Payment Details (BEP20)**\n\n"
            f"💰 **Amount:** ₹{amount:.2f} equivalent in USDT/BNB\n"
            f"📫 **BEP20 Address:**\n`{BEP20_ADDRESS}`\n\n"
            f"After sending, please upload the payment screenshot or transaction hash here."
        )

    bot.send_message(call.message.chat.id, payment_text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    uid = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else f"User ID: {uid}"
    
    # Forward screenshot to admin
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    
    # Send notification details to admin
    data = user_data.get(uid, {})
    svc = data.get("service", "N/A")
    amt = data.get("final_price", "N/A")
    
    admin_msg = (
        f"🚨 **NEW PAYMENT SCREENSHOT RECEIVED!**\n\n"
        f"👤 **User:** {username} (`{uid}`)\n"
        f"🏨 **Service:** {svc}\n"
        f"💵 **Amount:** ₹{amt}\n\n"
        f"Please verify the payment in your bank/wallet."
    )
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    
    # Confirm to user
    bot.reply_to(message, "✅ Your payment receipt has been submitted for verification! Admin will confirm your booking shortly.")

# Start Bot Polling
if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
