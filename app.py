import os
import logging
from html import escape
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

SHOP_NAME = "GAMEPAY HUB"
CONTACT_USERNAME = "@angsthtun"

PAYMENT_ACCOUNTS = {
    "kpay": "💙 KPay\n📲 09795687480\n👤 Aung Shin Thant Htun",
    "wave": "💛 Wave Pay\n📲 09795687480\n👤 Aung Shin Thant Htun",
    "uab": "💚 UAB Pay\n📲 09795687480\n👤 Aung Shin Thant Htun",
    "aya": "❤️ AYA Pay\n📲 09795687480\n👤 Aung Shin Thant Htun",
}
CATEGORIES = {
    "game": {
        "name": "🎮 Game Top Up",
    },
    "digital": {
        "name": "💻 Digital Products",
    },
}


PRODUCTS = {
    "mlbb_weekly": {
        "category": "game",
        "name": "Weekly Pass",
        "full_name": "MLBB Weekly Pass",
        "price_text": "6400 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
        "description": "⚡ Fast and trusted MLBB Weekly Pass top up service.",
    },
    "genshin_blessing": {
        "category": "game",
        "name": "Blessing",
        "full_name": "Genshin Impact Blessing",
        "price_text": "14800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80",
        "description": "✨ Safe and quick Genshin Blessing top up service.",
    },
    "hsr_express": {
        "category": "game",
        "name": "Express Supply",
        "full_name": "Honkai: Star Rail Express Supply",
        "price_text": "14800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?auto=format&fit=crop&w=1200&q=80",
        "description": "🚄 Fast Honkai: Star Rail Express Supply service.",
    },
    "wuthering_lunite": {
        "category": "game",
        "name": "Lunite Subscription",
        "full_name": "Wuthering Waves Lunite Subscription",
        "price_text": "18800 Ks",
        "stock": 10,
        "photo": "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1200&q=80",
        "description": "🌊 Trusted Wuthering Waves Lunite Subscription service.",
    },
"capcut_pro": {
        "category": "digital",
        "name": "CapCut Pro",
        "full_name": "CapCut Pro Subscription",
        "price_text": "From 5500 Ks",
        "stock": 50,
        "photo": "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1200&q=80",
        "description": (
            "📱 CapCut Pro Price\n\n"
            "❤️‍🔥 Share Plan\n"
            "• 1 Month  ➡️  5500 Ks\n"
            "• 3 Months ➡️ 15000 Ks\n\n"
            "❤️‍🔥 Private Plan\n"
            "• 1 Month  ➡️  8000 Ks\n"
            "• 3 Months ➡️ 25000 Ks\n"
            "• 6 Months ➡️ 45000 Ks\n"
            "• 12 Months ➡️ 90000 Ks\n\n"
            "💙 Own Mail Plan\n"
            "• 1 Month  ➡️ 12000 Ks\n\n"
            "‼️ After 1 Month Renewal ➡️ 29000 Ks"
        ),
    }

# =========================
# STATES
# =========================

(
    MENU_STATE,
    CATEGORY_STATE,
    PRODUCT_STATE,
    ID_SERVER_STATE,
    PAYMENT_STATE,
    SCREENSHOT_STATE,
) = range(6)

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# UI HELPERS
# =========================


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛍️ Shop", callback_data="menu_shop")],
            [InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact")],
            [InlineKeyboardButton("🔄 Restart", callback_data="menu_restart")],
        ]
    )


def category_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for key, cat in CATEGORIES.items():
        rows.append([InlineKeyboardButton(cat["name"], callback_data=f"cat:{key}")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def products_keyboard(category_key: str) -> InlineKeyboardMarkup:
    rows = []
    for key, product in PRODUCTS.items():
        if product["category"] != category_key:
            continue

        if product["stock"] > 0:
            text = f"🟢 {product['name']} • {product['price_text']}"
            rows.append([InlineKeyboardButton(text, callback_data=f"product:{key}")])
        else:
            text = f"🔴 {product['name']} • Out of Stock"
            rows.append([InlineKeyboardButton(text, callback_data="out_of_stock")])

    rows.append([InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_categories")])
    return InlineKeyboardMarkup(rows)


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💙 KPay", callback_data="pay:kpay")],
            [InlineKeyboardButton("💛 Wave Pay", callback_data="pay:wave")],
            [InlineKeyboardButton("❤️ AYA Pay", callback_data="pay:aya")],
            [InlineKeyboardButton("💚 UAB Pay", callback_data="pay:uab")],
            [InlineKeyboardButton("⬅️ Back", callback_data="pay_back_products")],
        ]
    )


def admin_action_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{user_id}"),
            ]
        ]
    )


def welcome_text() -> str:
    return """🌈⚡ <b>GAMEPAY HUB</b> ⚡🌈

🎮 <b>Welcome from Gamepay Hub</b>
မြန်ဆန် • စိတ်ချရ • ယုံကြည်ရတဲ့ Top Up Service 💎

✨ <b>What would you like to do?</b>
အောက်က menu ကနေရွေးပေးပါ 👇

⚡ Fast Service
🔒 Safe Payment
💖 Trusted Top Up"""
    


def product_caption(product: dict) -> str:
    status = "🟢 In Stock" if product["stock"] > 0 else "🔴 Out of Stock"
    return f"""🎮 <b>{escape(product['full_name'])}</b>

💰 <b>Price:</b> {escape(product['price_text'])}
📦 <b>Stock:</b> {product['stock']}
📌 <b>Status:</b> {status}

📝 {escape(product['description'])}"""


def payment_text(payment_name: str, account: str) -> str:
    return f"""💸 <b>PAYMENT INFO</b>

🏦 <b>Method:</b> {escape(payment_name)}
📲 <b>Account:</b> {escape(account)}

✅ ငွေလွှဲပြီး <b>payment screenshot</b> ပို့ပေးပါ
📨 ပြီးတာနဲ့ admin ဆီ order တက်သွားပါမယ်"""

# =========================
# HANDLERS
# =========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    if update.message:
        await update.message.reply_text(
            welcome_text(),
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            welcome_text(),
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    return MENU_STATE


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_shop":
        await query.message.reply_text(
            "🗂️ <b>Please choose a category</b>\nရွေးချယ်ပေးပါ 👇",
            reply_markup=category_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return CATEGORY_STATE

    if data == "menu_contact":
        await query.message.reply_text(
            "📞 <b>Contact Admin</b>\n\n"
            f"👤 Telegram: {escape(CONTACT_USERNAME)}\n"
            "အခက်အခဲရှိရင် admin ကိုတိုက်ရိုက်ဆက်သွယ်နိုင်ပါတယ်။",
            parse_mode=ParseMode.HTML,
        )
        return MENU_STATE

    if data == "menu_restart":
        context.user_data.clear()
        await query.message.reply_text(
            welcome_text(),
            reply_markup=main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
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
            parse_mode=ParseMode.HTML,
        )
        return MENU_STATE

    if data.startswith("cat:"):
        category_key = data.split(":", 1)[1]

        if category_key not in CATEGORIES:
            await query.message.reply_text("❌ Invalid category.")
            return CATEGORY_STATE

        context.user_data["category_key"] = category_key

        await query.message.reply_text(
            f"{CATEGORIES[category_key]['name']} <b>list</b> 👇",
            reply_markup=products_keyboard(category_key),
            parse_mode=ParseMode.HTML,
        )
        return PRODUCT_STATE

    return CATEGORY_STATE


async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_categories":
        await query.message.reply_text(
            "🗂️ <b>Please choose a category</b>\nရွေးချယ်ပေးပါ 👇",
            reply_markup=category_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return CATEGORY_STATE

    if data == "out_of_stock":
        await query.message.reply_text(
            "🔴 This item is out of stock.\nကျေးဇူးပြုပြီး နောက်တစ်ခုရွေးပေးပါ။"
        )
        return PRODUCT_STATE

    if data.startswith("product:"):
        product_key = data.split(":", 1)[1]

        if product_key not in PRODUCTS:
            await query.message.reply_text("❌ Invalid product.")
            return PRODUCT_STATE

        product = PRODUCTS[product_key]

        if product["stock"] <= 0:
            await query.message.reply_text("🔴 This item is out of stock.")
            return PRODUCT_STATE

        context.user_data["product_key"] = product_key
        context.user_data["product_name"] = product["full_name"]
        context.user_data["price_text"] = product["price_text"]

        await query.message.reply_photo(
            photo=product["photo"],
            caption=product_caption(product),
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            "🆔 <b>Please send your Game ID / Server</b>\n\n"
            "ဥပမာ:\n"
            "<code>123456789 / 1234</code>",
            parse_mode=ParseMode.HTML,
        )
        return ID_SERVER_STATE

    return PRODUCT_STATE

    if data.startswith("product:"):
        product_key = data.split(":", 1)[1]

        if product_key not in PRODUCTS:
            await query.message.reply_text("❌ Invalid product.")
            return PRODUCT_STATE

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
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            "🆔 <b>Please send your Game ID / Server</b>\n\n"
            "ဥပမာ:\n"
            "<code>123456789 / 1234</code>",
            parse_mode=ParseMode.HTML,
        )
        return ID_SERVER_STATE

    return PRODUCT_STATE


async def id_server_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if len(text) < 3:
        await update.message.reply_text(
            "❌ ID / Server မှန်မှန်ပို့ပေးပါ။\nဥပမာ: 123456789 / 1234"
        )
        return ID_SERVER_STATE

    context.user_data["id_server"] = text

    await update.message.reply_text(
        "💳 <b>Please choose a payment method</b>",
        reply_markup=payment_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    return PAYMENT_STATE


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "pay_back_products":
        category_key = context.user_data.get("category_key")
        if not category_key:
            await query.message.reply_text(
                "🗂️ <b>Please choose a category</b>",
                reply_markup=category_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return CATEGORY_STATE

        await query.message.reply_text(
            f"{CATEGORIES[category_key]['name']} <b>packages</b> 👇",
            reply_markup=products_keyboard(category_key),
            parse_mode=ParseMode.HTML,
        )
        return PRODUCT_STATE

    if not data.startswith("pay:"):
        return PAYMENT_STATE

    payment_key = data.split(":", 1)[1]

    if payment_key not in PAYMENT_ACCOUNTS:
        await query.message.reply_text("❌ Invalid payment method.")
        return PAYMENT_STATE

    payment_name_map = {
        "kpay": "KPay",
        "wave": "Wave Pay",
        "uab": "UAB Pay",
    }

    payment_name = payment_name_map.get(payment_key, payment_key.upper())

    context.user_data["payment_key"] = payment_key
    context.user_data["payment_name"] = payment_name

    await query.message.reply_text(
        payment_text(payment_name, PAYMENT_ACCOUNTS[payment_key]),
        parse_mode=ParseMode.HTML,
    )
    return SCREENSHOT_STATE


async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text(
            "📷 Payment screenshot ကို <b>photo</b> နဲ့ပို့ပေးပါ။",
            parse_mode=ParseMode.HTML,
        )
        return SCREENSHOT_STATE

    photo_file_id = update.message.photo[-1].file_id
    user = update.effective_user

    product_key = context.user_data.get("product_key")
    product_name = context.user_data.get("product_name", "-")
    price_text = context.user_data.get("price_text", "-")
    id_server = context.user_data.get("id_server", "-")
    payment_name = context.user_data.get("payment_name", "-")

    username_text = f"@{user.username}" if user.username else "-"

    admin_caption = (
        "╔══════════════════════╗\n"
        "   📥 <b>NEW ORDER</b>\n"
        "╚══════════════════════╝\n\n"
        f"🎮 <b>Product:</b> {escape(product_name)}\n"
        f"💰 <b>Price:</b> {escape(price_text)}\n"
        f"🆔 <b>ID / Server:</b> {escape(id_server)}\n"
        f"💳 <b>Payment:</b> {escape(payment_name)}\n\n"
        f"👤 <b>Customer:</b> {escape(user.full_name)}\n"
        f"📎 <b>Username:</b> {escape(username_text)}\n"
        f"🪪 <b>User ID:</b> {user.id}"
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=admin_caption,
            reply_markup=admin_action_keyboard(user.id),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.exception("Failed to send order to admin: %s", e)
        await update.message.reply_text(
            "❌ Admin ဆီ order မပို့နိုင်သေးပါ။\nနောက်တစ်ခါပြန်စမ်းပေးပါ။"
        )
        return SCREENSHOT_STATE

    context.bot_data[str(user.id)] = {
        "product_key": product_key,
        "product_name": product_name,
        "price_text": price_text,
        "id_server": id_server,
        "payment_name": payment_name,
    }

    await update.message.reply_text(
        "✅ <b>Order received successfully!</b>\n\n"
        "📨 Screenshot + Order info ကို admin ဆီပို့ပြီးပါပြီ\n"
        "⏳ စစ်ဆေးပြီး Manual Top Up လုပ်ပေးပါမယ်\n"
        "💖 Thanks for using Gamepay Hub",
        parse_mode=ParseMode.HTML,
    )

    context.user_data.clear()
    return ConversationHandler.END


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("ဒီ button ကို admin ပဲသုံးလို့ရပါတယ်။", show_alert=True)
        return

    data = query.data
    action, user_id_text = data.split(":")
    user_id = int(user_id_text)

    order_data = context.bot_data.get(str(user_id), {})
    product_key = order_data.get("product_key")

    if action == "approve":
        if product_key in PRODUCTS and PRODUCTS[product_key]["stock"] > 0:
            PRODUCTS[product_key]["stock"] -= 1

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ <b>Order Approved!</b>\n\n"
                    "🎮 Manual top up လုပ်ပေးပြီးပါပြီ\n"
                    "💖 Gamepay Hub ကိုအသုံးပြုပေးတာ ကျေးဇူးတင်ပါတယ်"
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.exception("Failed to notify user approve: %s", e)

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ <b>Status: Approved</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        except Exception as e:
            logger.exception("Failed to edit admin message approve: %s", e)

        context.bot_data.pop(str(user_id), None)
        return

    if action == "reject":
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ <b>Order Rejected!</b>\n\n"
                    "📷 Payment screenshot / info ကိုပြန်စစ်ပြီး\n"
                    "ကျေးဇူးပြုပြီး ပြန်ပို့ပေးပါ။"
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.exception("Failed to notify user reject: %s", e)

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ <b>Status: Rejected</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        except Exception as e:
            logger.exception("Failed to edit admin message reject: %s", e)

        context.bot_data.pop(str(user_id), None)
        return


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🛑 လုပ်ငန်းစဉ်ကို ဖျက်လိုက်ပါပြီ。\n/start နဲ့ ပြန်စနိုင်ပါတယ်။"
    )
    return ConversationHandler.END


# =========================
# MAIN
# =========================


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found.")
    if not ADMIN_ID:
        raise ValueError("ADMIN_ID not found.")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(False)
        .build()
    )

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU_STATE: [
                CallbackQueryHandler(
                    menu_handler,
                    pattern=r"^(menu_shop|menu_contact|menu_restart)$"
                )
            ],
            CATEGORY_STATE: [
                CallbackQueryHandler(
                    category_handler,
                    pattern=r"^(cat:.*|back_main)$"
                )
            ],
            PRODUCT_STATE: [
                CallbackQueryHandler(
                    product_handler,
                    pattern=r"^(product:.*|out_of_stock|back_categories)$"
                )
            ],
            ID_SERVER_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, id_server_handler)
            ],
            PAYMENT_STATE: [
                CallbackQueryHandler(
                    payment_handler,
                    pattern=r"^(pay:.*|pay_back_products)$"
                )
            ],
            SCREENSHOT_STATE: [
                MessageHandler(filters.PHOTO, screenshot_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, screenshot_handler),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(
        CallbackQueryHandler(admin_action, pattern=r"^(approve|reject):\d+$")
    )

    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
