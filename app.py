import os
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

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

SHOP_NAME = "Gamepay Hub"

PAYMENT_ACCOUNTS = {
    "kpay": "KPay - 09xxxxxxxxx",
    "wave": "Wave - 09xxxxxxxxx",
    "uab": "UAB - 09xxxxxxxxx",
}

CATEGORIES = {
    "mlbb": {
        "name": "🔥 MLBB",
        "description": "MLBB top up packages",
    },
    "genshin": {
        "name": "✨ Genshin Impact",
        "description": "Genshin packages",
    },
    "hsr": {
        "name": "🚄 Honkai: Star Rail",
        "description": "Honkai Star Rail packages",
    },
    "wuthering": {
        "name": "🌊 Wuthering Waves",
        "description": "Wuthering Waves packages",
    },
}

PRODUCTS = {
    "mlbb_weekly": {
        "category": "mlbb",
        "name": "Weekly Pass",
        "full_name": "MLBB Weekly Pass",
        "price_text": "6400 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
        "description": "Fast and trusted MLBB Weekly Pass top up.",
    },
    "genshin_blessing": {
        "category": "genshin",
        "name": "Blessing",
        "full_name": "Genshin Impact Blessing",
        "price_text": "14800 Ks",
        "stock": 10,
        "photo": "genshin-impact-codes-redeem-1-550x309.jpg",
        "description": "Genshin Blessing top up service.",
    },
    "hsr_express": {
        "category": "hsr",
        "name": "Express Supply",
        "full_name": "Honkai: Star Rail Express Supply",
        "price_text": "14800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?auto=format&fit=crop&w=1200&q=80",
        "description": "Honkai Star Rail Express Supply service.",
    },
    "wuthering_lunite": {
        "category": "wuthering",
        "name": "Lunite Subscription",
        "full_name": "Wuthering Waves Lunite Subscription",
        "price_text": "18800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1200&q=80",
        "description": "Wuthering Waves Lunite Subscription service.",
    },
}

(
    MENU_STATE,
    CATEGORY_STATE,
    PRODUCT_STATE,
    ID_SERVER_STATE,
    PAYMENT_STATE,
    SCREENSHOT_STATE,
) = range(6)


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛍 Shop", callback_data="menu_shop")],
            [InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact")],
            [InlineKeyboardButton("🔄 Restart", callback_data="menu_restart")],
        ]
    )


def category_keyboard():
    rows = []
    for key, cat in CATEGORIES.items():
        rows.append([InlineKeyboardButton(cat["name"], callback_data=f"cat:{key}")])
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def products_keyboard(category_key: str):
    rows = []
    for key, product in PRODUCTS.items():
        if product["category"] != category_key:
            continue

        if product["stock"] > 0:
            text = f"🟢 {product['name']} - {product['price_text']}"
            rows.append([InlineKeyboardButton(text, callback_data=f"product:{key}")])
        else:
            text = f"🔴 {product['name']} - Out of Stock"
            rows.append([InlineKeyboardButton(text, callback_data="out_of_stock")])

    rows.append([InlineKeyboardButton("⬅ Back to Categories", callback_data="back_categories")])
    return InlineKeyboardMarkup(rows)


def payment_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💚 KPay", callback_data="pay:kpay")],
            [InlineKeyboardButton("💙 Wave", callback_data="pay:wave")],
            [InlineKeyboardButton("🩶 UAB", callback_data="pay:uab")],
        ]
    )


def admin_action_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{user_id}"),
            ]
        ]
    )


def welcome_text():
    return (
        "╔════════════════════╗\n"
        f"   🎮 {SHOP_NAME}\n"
        "╚════════════════════╝\n\n"
        "Hello Gamepay Hub မှကြိုဆိုပါတယ် 👋\n"
        "ဘာများအလိုရှိပါသလဲ?\n\n"
        "⚡ Fast Service\n"
        "🔒 Safe Payment\n"
        "💎 Trusted Top Up\n\n"
        "အောက်က menu ကနေရွေးပေးပါ။"
    )


def product_caption(product: dict):
    status = "🟢 In Stock" if product["stock"] > 0 else "🔴 Out of Stock"
    return (
        "━━━━━━━━━━━━━━━\n"
        f"🎮 {product['full_name']}\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"💰 Price: {product['price_text']}\n"
        f"📦 Stock: {product['stock']}\n"
        f"📌 Status: {status}\n\n"
        f"📝 {product['description']}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        welcome_text(),
        reply_markup=main_menu_keyboard(),
    )
    return MENU_STATE


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_shop":
        await query.message.reply_text(
            "🗂 Category တစ်ခုရွေးပေးပါ။",
            reply_markup=category_keyboard(),
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
            welcome_text(),
            reply_markup=main_menu_keyboard(),
        )
        return MENU_STATE

    return MENU_STATE


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_main":
        await query.message.reply_text(
            welcome_text(),
            reply_markup=main_menu_keyboard(),
        )
        return MENU_STATE

    if data.startswith("cat:"):
        category_key = data.split(":", 1)[1]
        context.user_data["category_key"] = category_key
        await query.message.reply_text(
            f"{CATEGORIES[category_key]['name']} packages 👇",
            reply_markup=products_keyboard(category_key),
        )
        return PRODUCT_STATE

    return CATEGORY_STATE


async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_categories":
        await query.message.reply_text(
            "🗂 Category တစ်ခုရွေးပေးပါ။",
            reply_markup=category_keyboard(),
        )
        return CATEGORY_STATE

    if data == "out_of_stock":
        await query.message.reply_text(
            "🔴 ဒီ package က stock ကုန်နေပါတယ်။\nနောက်တစ်ခုရွေးပေးပါ။"
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
        context.user_data["price_text"] = product["price_text"]

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


async def id_server_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["id_server"] = update.message.text.strip()
    await update.message.reply_text(
        "💳 Payment method တစ်ခုရွေးပေးပါ။",
        reply_markup=payment_keyboard(),
    )
    return PAYMENT_STATE


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    payment_key = query.data.split(":", 1)[1]
    payment_name = "KPay" if payment_key == "kpay" else payment_key.upper()

    context.user_data["payment_key"] = payment_key
    context.user_data["payment_name"] = payment_name

    await query.message.reply_text(
        "━━━━━━━━━━━━━━━\n"
        "💸 PAYMENT INFO\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"Method: {payment_name}\n"
        f"Account: {PAYMENT_ACCOUNTS[payment_key]}\n\n"
        "ငွေလွှဲပြီး payment screenshot ပို့ပေးပါ။\n"
        "ပြီးတာနဲ့ admin ဘက်ကို order တက်သွားပါမယ်။"
    )
    return SCREENSHOT_STATE


async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("📷 Payment screenshot ကို photo နဲ့ပို့ပေးပါ။")
        return SCREENSHOT_STATE

    photo_file_id = update.message.photo[-1].file_id
    user = update.effective_user

    product_key = context.user_data.get("product_key")
    product_name = context.user_data.get("product_name", "-")
    price_text = context.user_data.get("price_text", "-")
    id_server = context.user_data.get("id_server", "-")
    payment_name = context.user_data.get("payment_name", "-")

    admin_caption = (
        "╔════════════════╗\n"
        "   📥 NEW ORDER\n"
        "╚════════════════╝\n\n"
        f"🎮 Product: {product_name}\n"
        f"💰 Price: {price_text}\n"
        f"🆔 ID / Server: {id_server}\n"
        f"💳 Payment: {payment_name}\n\n"
        f"👤 Customer: {user.full_name}\n"
        f"📎 Username: @{user.username if user.username else '-'}\n"
        f"🆔 User ID: {user.id}"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=admin_caption,
        reply_markup=admin_action_keyboard(user.id),
    )

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
                "Manual top up လုပ်ပေးပြီးပါပြီ。\n"
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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("လုပ်ငန်းစဉ်ကိုဖျက်လိုက်ပါပြီ။ /start နဲ့ပြန်စနိုင်ပါတယ်။")
    return ConversationHandler.END


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found.")
    if not ADMIN_ID:
        raise ValueError("ADMIN_ID not found.")

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
                CallbackQueryHandler(product_handler, pattern=r"^(product:|out_of_stock|back_categories)")
            ],
            ID_SERVER_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, id_server_handler)
            ],
            PAYMENT_STATE: [
                CallbackQueryHandler(payment_handler, pattern=r"^pay:")
            ],
            SCREENSHOT_STATE: [
                MessageHandler(filters.PHOTO, screenshot_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, screenshot_handler),
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
