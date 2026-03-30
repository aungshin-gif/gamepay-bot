from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================
BOT_TOKEN = "Yp8414987117:AAG1k4RmLHjnimnen7qEmeJ6Gt9jh353IMQ"
ADMIN_ID =  8458798760 # <- @userinfobot ကရတဲ့ numeric ID ထည့်

SHOP_NAME = "Gamepay Hub"

PAYMENT_ACCOUNTS = {
    "kpay": "KPay - 09xxxxxxxxx",
    "wave": "Wave - 09xxxxxxxxx",
    "uab": "UAB - 09xxxxxxxxx",
}

# =========================================================
# CATEGORY + PRODUCT DATA
# =========================================================
CATEGORIES = {
    "mlbb": {
        "name": "🔥 MLBB",
        "emoji": "🔥",
        "description": "MLBB top up packages",
    },
    "genshin": {
        "name": "✨ Genshin Impact",
        "emoji": "✨",
        "description": "Genshin blessing packages",
    },
    "hsr": {
        "name": "🚄 Honkai: Star Rail",
        "emoji": "🚄",
        "description": "Express Supply Pass packages",
    },
    "wuthering": {
        "name": "🌊 Wuthering Waves",
        "emoji": "🌊",
        "description": "Lunite Subscription packages",
    },
}

PRODUCTS = {
    "mlbb_weekly": {
        "category": "mlbb",
        "name": "Weekly Pass",
        "full_name": "MLBB Weekly Pass",
        "price": 6400,
        "currency_text": "6400 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
        "description": "MLBB Weekly Pass top up service.",
    },
    "genshin_blessing": {
        "category": "genshin",
        "name": "Blessing",
        "full_name": "Genshin Impact Blessing",
        "price": 14800,
        "currency_text": "14800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80",
        "description": "Genshin Blessing of the Welkin Moon service.",
    },
    "hsr_express": {
        "category": "hsr",
        "name": "Express Supply",
        "full_name": "Honkai: Star Rail Express Supply",
        "price": 14800,
        "currency_text": "14800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?auto=format&fit=crop&w=1200&q=80",
        "description": "Honkai: Star Rail Express Supply Pass service.",
    },
    "wuthering_lunite": {
        "category": "wuthering",
        "name": "Lunite Subscription",
        "full_name": "Wuthering Waves Lunite Subscription",
        "price": 18800,
        "currency_text": "18800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1200&q=80",
        "description": "Wuthering Waves Lunite Subscription service.",
    },
}

# =========================================================
# STATES
# =========================================================
(
    MENU_STATE,
    CATEGORY_STATE,
    PRODUCT_STATE,
    ID_SERVER_STATE,
    PAYMENT_STATE,
    SCREENSHOT_STATE,
) = range(6)

# =========================================================
# HELPERS
# =========================================================
def build_main_menu():
    keyboard = [
        [InlineKeyboardButton("🛍 Shop", callback_data="menu_shop")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact")],
        [InlineKeyboardButton("🔄 Restart", callback_data="menu_restart")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_category_menu():
    keyboard = []
    for category_key, category in CATEGORIES.items():
        keyboard.append(
            [InlineKeyboardButton(category["name"], callback_data=f"cat:{category_key}")]
        )
    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


def build_products_menu(category_key: str):
    keyboard = []

    for product_key, product in PRODUCTS.items():
        if product["category"] != category_key:
            continue

        if product["stock"] > 0:
            label = f"🟢 {product['name']} - {product['currency_text']}"
            callback = f"product:{product_key}"
        else:
            label = f"🔴 {product['name']} - Out of Stock"
            callback = "outofstock"

        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    keyboard.append([InlineKeyboardButton("⬅ Back to Categories", callback_data="back_categories")])
    return InlineKeyboardMarkup(keyboard)


def build_payment_menu():
    keyboard = [
        [InlineKeyboardButton("💚 KPay", callback_data="pay:kpay")],
        [InlineKeyboardButton("💙 Wave", callback_data="pay:wave")],
        [InlineKeyboardButton("🩶 UAB", callback_data="pay:uab")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_admin_actions(user_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{user_id}"),
            ]
        ]
    )


def main_welcome_text():
    return (
        "╔════════════════════╗\n"
        f"   🎮 {SHOP_NAME}\n"
        "╚════════════════════╝\n\n"
        "မင်္ဂလာပါ 👋\n"
        "Game top up service မှကြိုဆိုပါတယ်။\n\n"
        "⚡ Fast Service\n"
        "🔒 Safe Payment\n"
        "💎 Trusted Top Up\n\n"
        "အောက်က menu ကနေရွေးပေးပါ။"
    )


def product_caption(product: dict):
    stock_text = "🟢 In Stock" if product["stock"] > 0 else "🔴 Out of Stock"
    category_name = CATEGORIES[product["category"]]["name"]

    return (
        "━━━━━━━━━━━━━━━\n"
        f"🎮 {product['full_name']}\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"📂 Category: {category_name}\n"
        f"💰 Price: {product['currency_text']}\n"
        f"📦 Stock: {product['stock']}\n"
        f"📌 Status: {stock_text}\n\n"
        f"📝 {product['description']}"
    )


# =========================================================
# START / MENU
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        main_welcome_text(),
        reply_markup=build_main_menu(),
    )
    return MENU_STATE


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_shop":
        await query.message.reply_text(
            "🗂 Category တစ်ခုရွေးပေးပါ။",
            reply_markup=build_category_menu(),
        )
        return CATEGORY_STATE

    if data == "menu_contact":
        await query.message.reply_text(
            "📞 Contact Admin\n"
            "Telegram: @yourusername\n"
            "အခက်အခဲရှိရင် admin ကိုတိုက်ရိုက်ဆက်သွယ်နိုင်ပါတယ်။"
        )
        return MENU_STATE

    if data == "menu_restart":
        context.user_data.clear()
        await query.message.reply_text(
            main_welcome_text(),
            reply_markup=build_main_menu(),
        )
        return MENU_STATE

    return MENU_STATE


# =========================================================
# CATEGORY
# =========================================================
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_main":
        await query.message.reply_text(
            main_welcome_text(),
            reply_markup=build_main_menu(),
        )
        return MENU_STATE

    if data.startswith("cat:"):
        category_key = data.split(":", 1)[1]
        context.user_data["category_key"] = category_key

        category = CATEGORIES[category_key]
        await query.message.reply_text(
            f"{category['name']} packages 👇",
            reply_markup=build_products_menu(category_key),
        )
        return PRODUCT_STATE

    return CATEGORY_STATE


# =========================================================
# PRODUCT
# =========================================================
async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_categories":
        await query.message.reply_text(
            "🗂 Category တစ်ခုရွေးပေးပါ။",
            reply_markup=build_category_menu(),
        )
        return CATEGORY_STATE

    if data == "outofstock":
        await query.message.reply_text(
            "🔴 ဒီ package က stock ကုန်နေပါတယ်။\n"
            "နောက်တစ်ခုရွေးပေးပါ။"
        )
        return PRODUCT_STATE

    if data.startswith("product:"):
        product_key = data.split(":", 1)[1]
        product = PRODUCTS[product_key]

        if product["stock"] <= 0:
            await query.message.reply_text("🔴 ဒီ package က stock ကုန်နေပါတယ်။")
            return PRODUCT_STATE

        context.user_data["product_key"] = product_key
        context.user_data["product_name"] = product["full_name"]
        context.user_data["price"] = product["currency_text"]

        await query.message.reply_photo(
            photo=product["photo"],
            caption=product_caption(product),
        )

        await query.message.reply_text(
            "🆔 ကျေးဇူးပြုပြီး Game ID / Server ပို့ပေးပါ။\n"
            "ဥပမာ:\n"
            "123456789 / 1234"
        )
        return ID_SERVER_STATE

    return PRODUCT_STATE


# =========================================================
# ID / SERVER
# =========================================================
async def get_id_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["id_server"] = update.message.text.strip()

    await update.message.reply_text(
        "💳 Payment method တစ်ခုရွေးပေးပါ။",
        reply_markup=build_payment_menu(),
    )
    return PAYMENT_STATE


# =========================================================
# PAYMENT
# =========================================================
async def choose_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("pay:"):
        return PAYMENT_STATE

    payment_key = data.split(":", 1)[1]
    payment_name = payment_key.upper() if payment_key != "kpay" else "KPay"

    context.user_data["payment_method"] = payment_name

    payment_account = PAYMENT_ACCOUNTS[payment_key]

    await query.message.reply_text(
        "━━━━━━━━━━━━━━━\n"
        "💸 PAYMENT INFO\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"Method: {payment_name}\n"
        f"Account: {payment_account}\n\n"
        "ငွေလွှဲပြီး payment screenshot ပို့ပေးပါ။\n"
        "ပြီးတာနဲ့ admin ဘက်ကို order တက်သွားပါမယ်။"
    )
    return SCREENSHOT_STATE


# =========================================================
# SCREENSHOT / ORDER SUBMIT
# =========================================================
async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("📷 Payment screenshot ကို photo နဲ့ပို့ပေးပါ။")
        return SCREENSHOT_STATE

    photo = update.message.photo[-1].file_id
    user = update.effective_user

    product_key = context.user_data.get("product_key")
    product_name = context.user_data.get("product_name", "-")
    price = context.user_data.get("price", "-")
    id_server = context.user_data.get("id_server", "-")
    payment_method = context.user_data.get("payment_method", "-")

    admin_caption = (
        "╔════════════════╗\n"
        "   📥 NEW ORDER\n"
        "╚════════════════╝\n\n"
        f"🎮 Product: {product_name}\n"
        f"💰 Price: {price}\n"
        f"🆔 ID / Server: {id_server}\n"
        f"💳 Payment: {payment_method}\n\n"
        f"👤 Customer: {user.full_name}\n"
        f"📎 Username: @{user.username if user.username else '-'}\n"
        f"🆔 User ID: {user.id}"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=admin_caption,
        reply_markup=build_admin_actions(user.id),
    )

    # keep product key so admin action can reduce stock later
    context.bot_data[str(user.id)] = {
        "product_key": product_key,
        "product_name": product_name,
    }

    await update.message.reply_text(
        "✅ Order လက်ခံပြီးပါပြီ。\n"
        "Admin ဘက်ကို screenshot + order info ပို့ပြီးပါပြီ。\n"
        "စစ်ဆေးပြီး Manual Top Up လုပ်ပေးပါမယ်။"
    )

    context.user_data.clear()
    return ConversationHandler.END


# =========================================================
# ADMIN ACTIONS
# =========================================================
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("ဒီ button ကို admin ပဲသုံးလို့ရပါတယ်။", show_alert=True)
        return

    action, user_id_text = query.data.split(":")
    user_id = int(user_id_text)

    order_data = context.bot_data.get(str(user_id), {})
    product_key = order_data.get("product_key")

    if action == "approve":
        if product_key and product_key in PRODUCTS and PRODUCTS[product_key]["stock"] > 0:
            PRODUCTS[product_key]["stock"] -= 1

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ Order Approved!\n\n"
                "Top up လုပ်ပေးပြီးပါပြီ。\n"
                "Gamepay Hub ကိုအသုံးပြုပေးတာကျေးဇူးတင်ပါတယ် 💖"
            ),
        )

        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ Status: Approved"
        )

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Order Rejected!\n\n"
                "Payment screenshot / info ကိုပြန်စစ်ပြီး ပြန်ပို့ပေးပါ။"
            ),
        )

        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ Status: Rejected"
        )


# =========================================================
# CANCEL
# =========================================================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("လုပ်ငန်းစဉ်ကိုဖျက်လိုက်ပါပြီ။ /start နဲ့ပြန်စနိုင်ပါတယ်။")
    return ConversationHandler.END


# =========================================================
# MAIN
# =========================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU_STATE: [
                CallbackQueryHandler(menu_handler, pattern=r"^(menu_shop|menu_contact|menu_restart)$")
            ],
            CATEGORY_STATE: [
                CallbackQueryHandler(category_handler, pattern=r"^(cat:|back_main)")
            ],
            PRODUCT_STATE: [
                CallbackQueryHandler(product_handler, pattern=r"^(product:|outofstock|back_categories)")
            ],
            ID_SERVER_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_id_server)
            ],
            PAYMENT_STATE: [
                CallbackQueryHandler(choose_payment, pattern=r"^pay:")
            ],
            SCREENSHOT_STATE: [
                MessageHandler(filters.PHOTO, get_screenshot),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_screenshot),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_action, pattern=r"^(approve|reject):"))

    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
