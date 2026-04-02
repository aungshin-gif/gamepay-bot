import os
import sqlite3
import logging
from html import escape
from datetime import datetime
from typing import Optional, Dict, Any

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

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

SHOP_NAME = "GAMEPAY HUB"
CONTACT_USERNAME = "@angsthtun"

# Telegram sticker file_id ထည့်ပါ
WELCOME_STICKER_ID = ""   # ဥပမာ: "CAACAgUAAxkBAA..."
SUCCESS_STICKER_ID = ""   # ဥပမာ: "CAACAgUAAxkBAA..."

PAYMENT_ACCOUNTS = {
    "kpay": {
        "label": "💙 KPay",
        "text": "💙 KPay\n📲 09795687480\n👤 Aung Shin Thant Htun",
    },
    "wave": {
        "label": "💛 Wave Pay",
        "text": "💛 Wave Pay\n📲 09795687480\n👤 Aung Shin Thant Htun",
    },
    "uab": {
        "label": "💚 UAB Pay",
        "text": "💚 UAB Pay\n📲 09795687480\n👤 Aung Shin Thant Htun",
    },
    "aya": {
        "label": "❤️ AYA Pay",
        "text": "❤️ AYA Pay\n📲 09795687480\n👤 Aung Shin Thant Htun",
    },
}

# =========================================================
# PRODUCTS
# Coding နဲ့ပဲ stock/product add လုပ်မယ်ဆို ဒီ dict ကိုပဲပြင်
# digital product stock = accounts list ထဲက unused အရေအတွက်
# game product stock = stock field
# =========================================================

PRODUCTS: Dict[str, Dict[str, Any]] = {
    "mlbb_weekly": {
        "category": "game",
        "name": "Weekly Pass",
        "full_name": "MLBB Weekly Pass",
        "description": "⚡ Fast and trusted MLBB Weekly Pass top up service.",
        "photo": "Screenshot_2026-03-31-09-45-06-397_com.mobile.legends.jpg",
        "stock": 10,
        "requires_detail_label": "🆔 <b>Game ID နှင့် Server ID ရေးပေးပါ</b>\n\nဥပမာ:\n<code>123456789 / 1234</code>",
        "plans": {
            "default": {
                "label": "Weekly Pass",
                "price": 6400,
            }
        },
    },
    "genshin_blessing": {
        "category": "game",
        "name": "Blessing",
        "full_name": "Genshin Impact Blessing",
        "description": "✨ Safe and quick Genshin Blessing top up service.",
        "photo": "Buy-Welkin-Moon-In-Game.png",
        "stock": 10,
        "requires_detail_label": "🆔 <b>UID / Server ရေးပေးပါ</b>\n\nဥပမာ:\n<code>812345678 / Asia</code>",
        "plans": {
            "default": {
                "label": "Blessing",
                "price": 14800,
            }
        },
    },
    "capcut_pro": {
        "category": "digital",
        "name": "CapCut Pro",
        "full_name": "CapCut Pro Subscription",
        "description": "📱 CapCut Pro account delivery service.",
        "photo": "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1200&q=80",
        "requires_detail_label": (
    "📝 <b>လိုအပ်ရင် note/message ပို့ပါ</b>\n"
    "မလိုအပ်ရင် <code>No</code> ပို့ပေးပါ။"
),
        "plans": {
            "share_1m": {"label": "Share Plan - 1 Month", "price": 5500},
            "share_3m": {"label": "Share Plan - 3 Months", "price": 15000},
            "private_1m": {"label": "Private Plan - 1 Month", "price": 8000},
            "private_3m": {"label": "Private Plan - 3 Months", "price": 25000},
            "private_6m": {"label": "Private Plan - 6 Months", "price": 45000},
            "private_12m": {"label": "Private Plan - 12 Months", "price": 90000},
            "ownmail_1m": {"label": "Own Mail Plan - 1 Month", "price": 12000},
        },
    },
    "netflix_premium": {
        "category": "digital",
        "name": "Netflix Premium",
        "full_name": "Netflix Premium Subscription",
        "description": "📺 Netflix Premium account delivery service.",
        "photo": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=1200&q=80",
     "requires_detail_label": (
    "📝 <b>လိုအပ်ရင် note/message ပို့ပါ</b>\n"
    "မလိုအပ်ရင် <code>No</code> ပို့ပေးပါ။"
),   
        "plans": {
            "share_1m": {"label": "Share Plan - 1 Month", "price": 8000},
            "share_3m": {"label": "Share Plan - 3 Months", "price": 15000},
            "share_6m": {"label": "Share Plan - 6 Months", "price": 45000},
            "share_1y": {"label": "Share Plan - 1 Year", "price": 90000},
            "private_1m": {"label": "Private Plan - 1 Month", "price": 13000},
            "private_3m": {"label": "Private Plan - 3 Months", "price": 28000},
            "private_6m": {"label": "Private Plan - 6 Months", "price": 50000},
            "private_1y": {"label": "Private Plan - 1 Year", "price": 100000},
            "ownmail_1m": {"label": "Own Mail Plan - 1 Month", "price": 50000},
        },
    },
"canva_pro_edu": {
    "category": "digital",
    "name": "Canva Pro Edu",
    "full_name": "Canva Pro Edu Subscription",
    "description": "Canva Pro Edu account delivery service.",
    "photo": "https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?auto=format&fit=crop&w=1200&q=80",
"requires_detail_label": (
    "📝 <b>လိုအပ်ရင် note/message ပို့ပါ</b>\n"
    "မလိုအပ်ရင် <code>No</code> ပို့ပေးပါ။"
),
    "plans": {
        "edu_1y": {"label": "1 Year Account", "price": 3200},
    },
},
}

# =========================================================
# DIGITAL ACCOUNT INVENTORY
# Coding နဲ့ပဲ stock add လုပ်ချင်ရင် ဒီ accounts list ထဲထည့်
# stock = used=False ဖြစ်တဲ့ account အရေအတွက်
# auto_delivery=True ဆို approve လုပ်တာနဲ့ bot က customer ဆီ auto ပို့မယ်
# auto_delivery=False ဆို admin က /deliver ORDER_ID ... နဲ့ manual ပို့မယ်
# =========================================================

DIGITAL_INVENTORY: Dict[str, Dict[str, Any]] = {
    "capcut_pro": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "share_1m",
                "email": "capcutshare1@example.com",
                "password": "pass1234",
                "extra": "⚠️ Password မပြောင်းပါနဲ့။",
                "used": False,
            },
            {
                "plan_key": "private_1m",
                "email": "capcutprivate1@example.com",
                "password": "pass5678",
                "extra": "✅ Private account",
                "used": False,
            },
        ],
    },
    "netflix_premium": {
        "auto_delivery": False,
        "accounts": [
            {
                "plan_key": "share_1m",
                "email": "netflixshare1@example.com",
                "password": "nf123456",
                "extra": "Profile 1 ကိုပဲသုံးပါ။",
                "used": False,
            },
        ],
    },
"canva_pro_edu": {
    "auto_delivery": True,
    "accounts": [
        {
            "plan_key": "edu_1y",
            "email": "crister272@atomicmail.io",
            "password": "crister272@",
            "extra": "Canva Pro Edu | 1 Year account",
            "used": False,
        },
    ],
},
}

# =========================================================
# STATES
# =========================================================

(
    MENU_STATE,
    CATEGORY_STATE,
    PRODUCT_STATE,
    PLAN_STATE,
    DETAIL_STATE,
    PAYMENT_STATE,
    SCREENSHOT_STATE,
) = range(7)

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================================================
# DATABASE
# =========================================================

DB_PATH = "gamepay_hub.db"


def db_connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        username TEXT,
        full_name TEXT,
        product_key TEXT NOT NULL,
        product_name TEXT NOT NULL,
        plan_key TEXT NOT NULL,
        plan_label TEXT NOT NULL,
        category TEXT NOT NULL,
        price INTEGER NOT NULL,
        detail TEXT,
        payment_key TEXT,
        payment_name TEXT,
        screenshot_file_id TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        admin_note TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS digital_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_key TEXT NOT NULL,
        plan_key TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        extra TEXT,
        used INTEGER NOT NULL DEFAULT 0,
        order_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        actor_id INTEGER,
        action TEXT NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
    sync_inventory_to_db()


def sync_inventory_to_db():
    conn = db_connect()
    cur = conn.cursor()

    for product_key, cfg in DIGITAL_INVENTORY.items():
        for acc in cfg.get("accounts", []):
            cur.execute("""
                SELECT id FROM digital_accounts
                WHERE product_key = ? AND plan_key = ? AND email = ? AND password = ?
            """, (
                product_key,
                acc["plan_key"],
                acc["email"],
                acc["password"],
            ))
            exists = cur.fetchone()
            if not exists:
                cur.execute("""
                    INSERT INTO digital_accounts (
                        product_key, plan_key, email, password, extra, used, order_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_key,
                    acc["plan_key"],
                    acc["email"],
                    acc["password"],
                    acc.get("extra", ""),
                    1 if acc.get("used", False) else 0,
                    None,
                ))

    conn.commit()
    conn.close()


def log_action(order_id: Optional[str], actor_id: int, action: str, note: str = ""):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_logs (order_id, actor_id, action, note, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        order_id,
        actor_id,
        action,
        note,
        now_str(),
    ))
    conn.commit()
    conn.close()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def new_order_id() -> str:
    return "ORD-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")[-20:]


def get_digital_stock(product_key: str, plan_key: Optional[str] = None) -> int:
    conn = db_connect()
    cur = conn.cursor()

    if plan_key:
        cur.execute("""
            SELECT COUNT(*) FROM digital_accounts
            WHERE product_key = ? AND plan_key = ? AND used = 0
        """, (product_key, plan_key))
    else:
        cur.execute("""
            SELECT COUNT(*) FROM digital_accounts
            WHERE product_key = ? AND used = 0
        """, (product_key,))
    count = cur.fetchone()[0]
    conn.close()
    return count


def reserve_account(product_key: str, plan_key: str, order_id: str) -> Optional[dict]:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, email, password, extra
        FROM digital_accounts
        WHERE product_key = ? AND plan_key = ? AND used = 0
        ORDER BY id ASC
        LIMIT 1
    """, (product_key, plan_key))
    row = cur.fetchone()

    if not row:
        conn.close()
        return None

    acc_id, email, password, extra = row

    cur.execute("""
        UPDATE digital_accounts
        SET used = 1, order_id = ?
        WHERE id = ?
    """, (order_id, acc_id))
    conn.commit()
    conn.close()

    return {
        "id": acc_id,
        "email": email,
        "password": password,
        "extra": extra or "",
    }


def order_get(order_id: str) -> Optional[dict]:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def order_update_status(order_id: str, status: str, admin_note: str = ""):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE orders
        SET status = ?, updated_at = ?, admin_note = ?
        WHERE order_id = ?
    """, (status, now_str(), admin_note, order_id))
    conn.commit()
    conn.close()


def order_insert(data: dict):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (
            order_id, user_id, username, full_name, product_key, product_name,
            plan_key, plan_label, category, price, detail,
            payment_key, payment_name, screenshot_file_id,
            status, created_at, updated_at, admin_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["order_id"],
        data["user_id"],
        data["username"],
        data["full_name"],
        data["product_key"],
        data["product_name"],
        data["plan_key"],
        data["plan_label"],
        data["category"],
        data["price"],
        data["detail"],
        data["payment_key"],
        data["payment_name"],
        data["screenshot_file_id"],
        data["status"],
        data["created_at"],
        data["updated_at"],
        data["admin_note"],
    ))
    conn.commit()
    conn.close()


def get_pending_orders(limit: int = 20):
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM orders
        WHERE status IN ('pending_payment_review', 'waiting_manual_delivery')
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# =========================================================
# UI HELPERS
# =========================================================

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛍️ Shop", callback_data="menu_shop")],
            [InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact")],
            [InlineKeyboardButton("🔄 Restart", callback_data="menu_restart")],
        ]
    )


def category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎮 Game Top Up", callback_data="cat:game")],
            [InlineKeyboardButton("💻 Digital Products", callback_data="cat:digital")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
        ]
    )

def products_keyboard(category_key: str) -> InlineKeyboardMarkup:
    rows = []

    for key, product in PRODUCTS.items():
        if product["category"] != category_key:
            continue

        if category_key == "digital":
            cheapest = min(v["price"] for v in product["plans"].values())
            rows.append([
                InlineKeyboardButton(
                    f"✨ {product['name']} • From {cheapest} Ks",
                    callback_data=f"product:{key}"
                )
            ])
        else:
            stock = int(product.get("stock", 0))
            default_plan = next(iter(product["plans"].values()))
            if stock > 0:
                rows.append([
                    InlineKeyboardButton(
                        f"✨ {product['name']} • {default_plan['price']} Ks",
                        callback_data=f"product:{key}"
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"🔴 {product['name']} • Out of Stock",
                        callback_data="out_of_stock"
                    )
                ])

    rows.append([InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_categories")])
    return InlineKeyboardMarkup(rows)


def plans_keyboard(product_key: str) -> InlineKeyboardMarkup:
    rows = []
    product = PRODUCTS[product_key]

    for plan_key, plan in product["plans"].items():
        # Digital products => always available
        if product["category"] == "digital":
            rows.append([
                InlineKeyboardButton(
                    f"{plan['label']} • {plan['price']} Ks",
                    callback_data=f"plan:{plan_key}"
                )
            ])
        else:
            # Game products => real stock check
            stock = int(product.get("stock", 0))
            if stock > 0:
                rows.append([
                    InlineKeyboardButton(
                        f"{plan['label']} • {plan['price']} Ks",
                        callback_data=f"plan:{plan_key}"
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"🔴 {plan['label']} • Out of Stock",
                        callback_data="out_of_stock"
                    )
                ])

    rows.append([InlineKeyboardButton("⬅️ Back to Products", callback_data="back_products")])
    return InlineKeyboardMarkup(rows)

def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(PAYMENT_ACCOUNTS["kpay"]["label"], callback_data="pay:kpay")],
            [InlineKeyboardButton(PAYMENT_ACCOUNTS["wave"]["label"], callback_data="pay:wave")],
            [InlineKeyboardButton(PAYMENT_ACCOUNTS["aya"]["label"], callback_data="pay:aya")],
            [InlineKeyboardButton(PAYMENT_ACCOUNTS["uab"]["label"], callback_data="pay:uab")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_plan")],
        ]
    )


def admin_action_keyboard(order_id: str, category: str) -> InlineKeyboardMarkup:
    if category == "digital":
        return InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("⚡ Auto", callback_data=f"auto:{order_id}"),
                InlineKeyboardButton("✍️ Manual", callback_data=f"manual:{order_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{order_id}"),
            ]]
        )

    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{order_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{order_id}"),
        ]]
    )


def welcome_text() -> str:
    return f"""🌈⚡ <b>{escape(SHOP_NAME)}</b> ⚡🌈

🎮 <b>Welcome from {escape(SHOP_NAME)}</b>
မြန်ဆန် • စိတ်ချရ • ယုံကြည်ရတဲ့ Top Up Service 💎

✨ <b>What would you like to do?</b>
အောက်က menu ကနေရွေးပေးပါ 👇

⚡ Fast Service
🔒 Safe Payment
💖 Trusted Top Up"""


def product_caption(product: dict, product_key: str) -> str:
    if product["category"] == "digital":
        stock = get_digital_stock(product_key)
        price_text = f"From {min(v['price'] for v in product['plans'].values())} Ks"
    else:
        stock = int(product.get("stock", 0))
        price_text = f"{next(iter(product['plans'].values()))['price']} Ks"

    status = "🟢 In Stock" if stock > 0 else "🔴 Out of Stock"

    return f"""✨ <b>{escape(product['full_name'])}</b>
━━━━━━━━━━━━━━━

💰 <b>Price:</b> {escape(price_text)}
📦 <b>Stock:</b> {stock}
📌 <b>Status:</b> {status}

📝 <b>Description</b>
{escape(product['description'])}

━━━━━━━━━━━━━━━
⚡ Fast • 🔒 Safe • 💖 Trusted"""


def payment_text(payment_name: str, account: str, amount: int) -> str:
    return f"""💸 <b>PAYMENT INFO</b>

🏦 <b>Method:</b> {escape(payment_name)}
📲 <b>Account:</b>
{escape(account)}

💰 <b>Amount:</b> {amount} Ks

✅ ငွေလွှဲပြီး <b>payment screenshot</b> ပို့ပေးပါ
📨 ပြီးတာနဲ့ admin ဆီ order တက်သွားပါမယ်"""

# =========================================================
# STICKER HELPERS
# =========================================================

async def send_optional_sticker(message_obj, sticker_id: str):
    if not sticker_id:
        return
    try:
        await message_obj.reply_sticker(sticker=sticker_id)
    except Exception as e:
        logger.warning("Sticker send failed: %s", e)

async def send_optional_bot_sticker(bot, chat_id: int, sticker_id: str):
    if not sticker_id:
        return
    try:
        await bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
    except Exception as e:
        logger.warning("Bot sticker send failed: %s", e)

# =========================================================
# CUSTOMER FLOW
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    if update.message:
        await send_optional_sticker(update.message, WELCOME_STICKER_ID)
        await update.message.reply_text(
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
        context.user_data["category_key"] = category_key

        await query.message.reply_text(
            "📦 <b>Please choose a product</b>",
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
            "📦 <b>Please choose a product</b>",
            reply_markup=products_keyboard(context.user_data.get("category_key", "digital")),
            parse_mode=ParseMode.HTML,
        )
        return PRODUCT_STATE

    if data == "out_of_stock":
        await query.message.reply_text("🔴 This item is out of stock.")
        return PRODUCT_STATE

    if data.startswith("product:"):
        product_key = data.split(":", 1)[1]
        product = PRODUCTS.get(product_key)

        if not product:
            await query.message.reply_text("❌ Invalid product.")
            return PRODUCT_STATE

        context.user_data["product_key"] = product_key
        context.user_data["product_name"] = product["full_name"]
        context.user_data["category"] = product["category"]

        try:
            await query.message.reply_photo(
                photo=product["photo"],
                caption=product_caption(product, product_key),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.exception("Photo error for %s: %s", product_key, e)
            await query.message.reply_text(
                product_caption(product, product_key),
                parse_mode=ParseMode.HTML,
            )

        await query.message.reply_text(
            "📋 <b>Please choose a plan</b>",
            reply_markup=plans_keyboard(product_key),
            parse_mode=ParseMode.HTML,
        )
        return PLAN_STATE

    return PRODUCT_STATE


async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_products":
        category_key = context.user_data.get("category_key", "game")
        await query.message.reply_text(
            "📦 <b>Please choose a product</b>",
            reply_markup=products_keyboard(category_key),
            parse_mode=ParseMode.HTML,
        )
        return PRODUCT_STATE

    if data == "out_of_stock":
        await query.message.reply_text("🔴 This plan is out of stock.")
        return PLAN_STATE

    if data.startswith("plan:"):
        plan_key = data.split(":", 1)[1]
        product_key = context.user_data.get("product_key")
        product = PRODUCTS[product_key]
        plan = product["plans"][plan_key]

        context.user_data["plan_key"] = plan_key
        context.user_data["plan_label"] = plan["label"]
        context.user_data["price"] = plan["price"]

        await query.message.reply_text(
            product["requires_detail_label"],
            parse_mode=ParseMode.HTML,
        )
        return DETAIL_STATE

    return PLAN_STATE


async def detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return DETAIL_STATE

    text = update.message.text.strip()
    if len(text) < 1:
        await update.message.reply_text("❌ Detail ပို့ပေးပါ။")
        return DETAIL_STATE

    context.user_data["detail"] = text

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

    if data == "back_plan":
        product_key = context.user_data.get("product_key")
        await query.message.reply_text(
            "📋 <b>Please choose a plan</b>",
            reply_markup=plans_keyboard(product_key),
            parse_mode=ParseMode.HTML,
        )
        return PLAN_STATE

    if not data.startswith("pay:"):
        return PAYMENT_STATE

    payment_key = data.split(":", 1)[1]
    if payment_key not in PAYMENT_ACCOUNTS:
        await query.message.reply_text("❌ Invalid payment method.")
        return PAYMENT_STATE

    payment_name = PAYMENT_ACCOUNTS[payment_key]["label"]
    payment_account = PAYMENT_ACCOUNTS[payment_key]["text"]
    amount = int(context.user_data["price"])

    context.user_data["payment_key"] = payment_key
    context.user_data["payment_name"] = payment_name

    await query.message.reply_text(
        payment_text(payment_name, payment_account, amount),
        parse_mode=ParseMode.HTML,
    )
    return SCREENSHOT_STATE
    
async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        await update.message.reply_text(
            "📷 Payment screenshot ကို <b>photo</b> နဲ့ပို့ပေးပါ။",
            parse_mode=ParseMode.HTML,
        )
        return SCREENSHOT_STATE

    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id

    order_id = new_order_id()

    data = {
        "order_id": order_id,
        "user_id": user.id,
        "username": f"@{user.username}" if user.username else "",
        "full_name": user.full_name or "",
        "product_key": context.user_data["product_key"],
        "product_name": context.user_data["product_name"],
        "plan_key": context.user_data["plan_key"],
        "plan_label": context.user_data["plan_label"],
        "category": context.user_data["category"],
        "price": int(context.user_data["price"]),
        "detail": context.user_data.get("detail", "-"),
        "payment_key": context.user_data["payment_key"],
        "payment_name": context.user_data["payment_name"],
        "screenshot_file_id": photo_file_id,
        "status": "pending_payment_review",
        "created_at": now_str(),
        "updated_at": now_str(),
        "admin_note": "",
    }
    order_insert(data)
    log_action(order_id, user.id, "order_created", "Customer submitted screenshot")

    admin_caption = (
        "╔══════════════════════╗\n"
        "   📥 <b>NEW ORDER</b>\n"
        "╚══════════════════════╝\n\n"
        f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
        f"🎮 <b>Product:</b> {escape(data['product_name'])}\n"
        f"📋 <b>Plan:</b> {escape(data['plan_label'])}\n"
        f"💰 <b>Price:</b> {data['price']} Ks\n"
        f"📝 <b>Detail:</b> {escape(data['detail'])}\n"
        f"💳 <b>Payment:</b> {escape(data['payment_name'])}\n\n"
        f"👤 <b>Customer:</b> {escape(data['full_name'])}\n"
        f"📎 <b>Username:</b> {escape(data['username'] or '-')}\n"
        f"🪪 <b>User ID:</b> <code>{data['user_id']}</code>\n"
        f"📌 <b>Status:</b> Pending Review"
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=admin_caption,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_action_keyboard(order_id, data["category"]),
        )
    except Exception as e:
        logger.exception("Failed to send order to admin: %s", e)
        await update.message.reply_text("❌ Admin ဆီ order မပို့နိုင်သေးပါ။")
        return SCREENSHOT_STATE

    await update.message.reply_text(
        "✅ <b>Order received successfully!</b>\n\n"
        f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
        "📨 Screenshot + Order info ကို admin ဆီပို့ပြီးပါပြီ\n"
        "⏳ စစ်ဆေးပြီး order ကိုဆက်လုပ်ပေးပါမယ်",
        parse_mode=ParseMode.HTML,
    )

    context.user_data.clear()
    return ConversationHandler.END

# =========================================================
# ADMIN FLOW
# =========================================================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("ဒီ button ကို admin ပဲသုံးလို့ရပါတယ်။", show_alert=True)
        return

    raw = query.data
    action, order_id = raw.split(":", 1)
    order = order_get(order_id)

    if not order:
        await query.answer("Order not found", show_alert=True)
        return

    if action == "reject":
        order_update_status(order_id, "rejected", "Rejected by admin")
        log_action(order_id, query.from_user.id, "rejected")

        try:
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    "❌ <b>Order Rejected!</b>\n\n"
                    f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
                    "📷 Payment screenshot / info ကိုပြန်စစ်ပြီး ပြန်ပို့ပေးပါ။"
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.exception("Failed to notify reject: %s", e)

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ <b>Status: Rejected</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        except Exception as e:
            logger.exception("Failed to edit reject caption: %s", e)
        return

    if action == "approve":
        if order["category"] == "game":
            product = PRODUCTS.get(order["product_key"])
            if not product or int(product.get("stock", 0)) <= 0:
                await query.message.reply_text("❌ Stock မရှိတော့ပါ။")
                return

            product["stock"] -= 1
            order_update_status(order_id, "approved", "Game order approved")
            log_action(order_id, query.from_user.id, "approved_game")

            try:
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=(
                        "✅ <b>Order Approved!</b>\n\n"
                        f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
                        "🎮 Manual top up လုပ်ပေးပြီးပါပြီ\n"
                        "💖 Thanks for using Gamepay Hub"
                    ),
                    parse_mode=ParseMode.HTML,
                )
                await send_optional_bot_sticker(context.bot, order["user_id"], SUCCESS_STICKER_ID)
            except Exception as e:
                logger.exception("Failed to notify game approve: %s", e)

            try:
                await query.edit_message_caption(
                    caption=query.message.caption + "\n\n✅ <b>Status: Approved</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=None,
                )
            except Exception as e:
                logger.exception("Failed to edit approve caption: %s", e)
            return

        # digital
        inventory_cfg = DIGITAL_INVENTORY.get(order["product_key"], {})
        auto_delivery = bool(inventory_cfg.get("auto_delivery", False))

        account = reserve_account(order["product_key"], order["plan_key"], order_id)

        if not account:
            order_update_status(order_id, "waiting_manual_delivery", "No auto account available")
            log_action(order_id, query.from_user.id, "waiting_manual_delivery")

            try:
                await query.edit_message_caption(
                    caption=query.message.caption + "\n\n🟡 <b>Status: Waiting Manual Delivery</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=None,
                )
            except Exception as e:
                logger.exception("Failed to edit manual delivery caption: %s", e)

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📦 <b>Manual delivery required</b>\n\n"
                    f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
                    f"Product: {escape(order['product_name'])}\n"
                    f"Plan: {escape(order['plan_label'])}\n\n"
                    "ပို့ချင်တဲ့ account info ကို ဒီ command နဲ့ပို့ပါ:\n"
                    f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        if auto_delivery:
            order_update_status(order_id, "delivered", "Auto delivered")
            log_action(order_id, query.from_user.id, "auto_delivered")

            delivery_text = (
                f"✅ <b>Your {escape(order['product_name'])} order is ready!</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"📋 <b>Plan:</b> {escape(order['plan_label'])}\n"
                f"📧 <b>Email:</b> <code>{escape(account['email'])}</code>\n"
                f"🔑 <b>Password:</b> <code>{escape(account['password'])}</code>\n"
            )
            if account["extra"]:
                delivery_text += f"\n📝 <b>Note:</b> {escape(account['extra'])}\n"

            delivery_text += (
    "\n🔐 <b>Login ဝင်ရန် Code လိုအပ်ပါက</b>\n"
    "<code>Code</code> လို့ရိုက်ပို့ပေးပါ。\n\n"
    "💖 Thanks for using Gamepay Hub"
            )
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("ဒီ button ကို admin ပဲသုံးလို့ရပါတယ်။", show_alert=True)
        return

    action, order_id = query.data.split(":", 1)
    order = order_get(order_id)

    if not order:
        await query.answer("Order not found", show_alert=True)
        return

    if action == "reject":
        order_update_status(order_id, "rejected", "Rejected by admin")
        log_action(order_id, query.from_user.id, "rejected")

        try:
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    "❌ <b>Order Rejected!</b>\n\n"
                    f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
                    "📷 Payment screenshot / info ကိုပြန်စစ်ပြီး ပြန်ပို့ပေးပါ။"
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.exception("Failed to notify reject: %s", e)

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ <b>Status: Rejected</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        except Exception as e:
            logger.exception("Failed to edit reject caption: %s", e)
        return

    # game product approve
    if action == "approve":
        if order["category"] != "game":
            await query.answer("ဒီ button က game order အတွက်ပဲပါ။", show_alert=True)
            return

        product = PRODUCTS.get(order["product_key"])
        if not product or int(product.get("stock", 0)) <= 0:
            await query.message.reply_text("❌ Stock မရှိတော့ပါ။")
            return

        product["stock"] -= 1
        order_update_status(order_id, "approved", "Game order approved")
        log_action(order_id, query.from_user.id, "approved_game")

        try:
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    "✅ <b>Order Approved!</b>\n\n"
                    f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
                    "🎮 Manual top up လုပ်ပေးပြီးပါပြီ\n"
                    "💖 Thanks for using Gamepay Hub"
                ),
                parse_mode=ParseMode.HTML,
            )
            await send_optional_bot_sticker(context.bot, order["user_id"], SUCCESS_STICKER_ID)
        except Exception as e:
            logger.exception("Failed to notify game approve: %s", e)

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ <b>Status: Approved</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        except Exception as e:
            logger.exception("Failed to edit approve caption: %s", e)
        return

    # digital auto delivery
    if action == "auto":
        if order["category"] != "digital":
            await query.answer("ဒီ button က digital order အတွက်ပဲပါ။", show_alert=True)
            return

        inventory_cfg = DIGITAL_INVENTORY.get(order["product_key"], {})
        account = reserve_account(order["product_key"], order["plan_key"], order_id)

        if not account:
            order_update_status(order_id, "waiting_manual_delivery", "Auto stock not found")
            log_action(order_id, query.from_user.id, "auto_failed_waiting_manual")

            try:
                await query.edit_message_caption(
                    caption=query.message.caption + "\n\n🟡 <b>Status: No Auto Stock / Waiting Manual Delivery</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=None,
                )
            except Exception as e:
                logger.exception("Failed to edit auto-failed caption: %s", e)

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"❌ <b>Auto stock not found</b>\n\n"
                    f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
                    f"🎮 Product: {escape(order['product_name'])}\n"
                    f"📋 Plan: {escape(order['plan_label'])}\n\n"
                    "Manual delivery လုပ်ချင်ရင် ဒီ command သုံးပါ:\n"
                    f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        order_update_status(order_id, "delivered", "Auto delivered")
        log_action(order_id, query.from_user.id, "auto_delivered")

        delivery_text = (
            f"✅ <b>Your {escape(order['product_name'])} order is ready!</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"📋 <b>Plan:</b> {escape(order['plan_label'])}\n"
            f"📧 <b>Email:</b> <code>{escape(account['email'])}</code>\n"
            f"🔑 <b>Password:</b> <code>{escape(account['password'])}</code>\n"
        )

        if account["extra"]:
            delivery_text += f"\n📝 <b>Note:</b> {escape(account['extra'])}\n"

        delivery_text += (
    "\n🔐 <b>Login ဝင်ရန် Code လိုအပ်ပါက</b>\n"
    "<code>Code</code> လို့ရိုက်ပို့ပေးပါ。\n\n"
    "💖 Thanks for using Gamepay Hub"
        )

        try:
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=delivery_text,
                parse_mode=ParseMode.HTML,
            )
            await send_optional_bot_sticker(context.bot, order["user_id"], SUCCESS_STICKER_ID)
        except Exception as e:
            logger.exception("Failed to auto deliver digital: %s", e)

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ <b>Status: Auto Delivered</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        except Exception as e:
            logger.exception("Failed to edit auto delivery caption: %s", e)
        return

    # digital manual delivery
    if action == "manual":
        if order["category"] != "digital":
            await query.answer("ဒီ button က digital order အတွက်ပဲပါ။", show_alert=True)
            return

        order_update_status(order_id, "waiting_manual_delivery", "Waiting admin manual delivery")
        log_action(order_id, query.from_user.id, "manual_delivery_selected")

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n🟡 <b>Status: Waiting Manual Delivery</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        except Exception as e:
            logger.exception("Failed to edit manual caption: %s", e)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"✍️ <b>Manual delivery selected</b>\n\n"
                f"🆔 Order ID: <code>{escape(order_id)}</code>\n"
                f"🎮 Product: {escape(order['product_name'])}\n"
                f"📋 Plan: {escape(order['plan_label'])}\n\n"
                "Customer ဆီပို့ချင်တဲ့ Email / Password ကို ဒီ command နဲ့ပို့ပါ:\n\n"
                f"<code>/deliver {escape(order_id)} Email: yourmail@gmail.com Password: 123456</code>\n\n"
                "ဒါမှမဟုတ် multiline နဲ့လည်းပို့လို့ရတယ်:\n"
                f"<code>/deliver {escape(order_id)}\nEmail: yourmail@gmail.com\nPassword: 123456</code>"
            ),
            parse_mode=ParseMode.HTML,
        )

async def deliver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message or not update.message.text:
        return

    full_text = update.message.text.strip()
    parts = full_text.split(maxsplit=2)

    if len(parts) < 3:
        await update.message.reply_text(
            "Usage:\n"
            "<code>/deliver ORDER_ID Email: xxx Password: yyy</code>\n\n"
            "or\n"
            "<code>/deliver ORDER_ID\nEmail: xxx\nPassword: yyy</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    _, order_id, delivery_text = parts[0], parts[1], parts[2]

    order = order_get(order_id)
    if not order:
        await update.message.reply_text("❌ Order not found.")
        return

    try:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"✅ <b>Your {escape(order['product_name'])} order is ready!</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"<pre>{escape(delivery_text)}</pre>\n\n"
                "💖 Thanks for using Gamepay Hub"
            ),
            parse_mode=ParseMode.HTML,
        )
        await send_optional_bot_sticker(context.bot, order["user_id"], SUCCESS_STICKER_ID)
    except Exception as e:
        logger.exception("Failed to manual deliver: %s", e)
        await update.message.reply_text("❌ Customer ဆီမပို့နိုင်ပါ။")
        return

    order_update_status(order_id, "delivered", "Manually delivered")
    log_action(order_id, update.effective_user.id, "manually_delivered", delivery_text)
    await update.message.reply_text("✅ Delivered successfully.")
async def customer_code_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    text = update.message.text.strip().lower()

    if user.id == ADMIN_ID:
        return

    if text != "code":
        return

    order = None
    rows = get_pending_orders(limit=100)

    # delivered digital orders among recent records
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
          AND category = 'digital'
          AND status IN ('delivered', 'code_requested', 'code_sent')
        ORDER BY created_at DESC
        LIMIT 1
    """, (user.id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("❌ Active digital order မတွေ့ပါ။")
        return

    order = dict(row)
    order_id = order["order_id"]

    order_update_status(order_id, "code_requested", "Customer requested login code")
    log_action(order_id, user.id, "code_requested", "Customer typed Code")

    await update.message.reply_text(
        "⏳ Code request ကို admin ဆီပို့ပြီးပါပြီ။\nCode ရလာတာနဲ့ ပြန်ပို့ပေးပါမယ်။"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🔔 <b>Login Code Requested</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"🎮 <b>Product:</b> {escape(order['product_name'])}\n"
            f"👤 <b>Customer:</b> {escape(order['full_name'])}\n"
            f"📎 <b>Username:</b> {escape(order['username'] or '-')}\n"
            f"🪪 <b>User ID:</b> <code>{order['user_id']}</code>\n\n"
            f"Code ပို့ရန်:\n"
            f"<code>/code {escape(order_id)} 123456</code>"
        ),
        parse_mode=ParseMode.HTML,
    )
    async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n<code>/code ORDER_ID 123456</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    order_id = context.args[0]
    code_value = " ".join(context.args[1:]).strip()

    order = order_get(order_id)
    if not order:
        await update.message.reply_text("❌ Order not found.")
        return

    try:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"🔐 <b>Your login code is ready</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"🔢 <b>Code:</b> <code>{escape(code_value)}</code>\n\n"
                "✅ ကျေးဇူးပြုပြီး ချက်ချင်းအသုံးပြုပေးပါ။"
            ),
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.exception("Failed to send login code: %s", e)
        await update.message.reply_text("❌ Customer ဆီ code မပို့နိုင်ပါ။")
        return

    order_update_status(order_id, "code_sent", "Admin sent login code")
    log_action(order_id, update.effective_user.id, "code_sent", code_value)
    await update.message.reply_text("✅ Login code ပို့ပြီးပါပြီ။")
async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    rows = get_pending_orders(limit=20)
    if not rows:
        await update.message.reply_text("✅ Pending orders မရှိပါ။")
        return

    lines = ["📋 <b>Pending Orders</b>\n"]
    for o in rows:
        lines.append(
            f"🆔 <code>{escape(o['order_id'])}</code>\n"
            f"🎮 {escape(o['product_name'])}\n"
            f"📋 {escape(o['plan_label'])}\n"
            f"👤 {escape(o['full_name'])}\n"
            f"📌 {escape(o['status'])}\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /order ORDER_ID")
        return

    order_id = context.args[0]
    order = order_get(order_id)
    if not order:
        await update.message.reply_text("❌ Order not found.")
        return

    text = (
        f"🆔 <b>Order ID:</b> <code>{escape(order['order_id'])}</code>\n"
        f"🎮 <b>Product:</b> {escape(order['product_name'])}\n"
        f"📋 <b>Plan:</b> {escape(order['plan_label'])}\n"
        f"💰 <b>Price:</b> {order['price']} Ks\n"
        f"📝 <b>Detail:</b> {escape(order['detail'] or '-')}\n"
        f"👤 <b>User:</b> {escape(order['full_name'])}\n"
        f"📎 <b>Username:</b> {escape(order['username'] or '-')}\n"
        f"📌 <b>Status:</b> {escape(order['status'])}\n"
        f"🕒 <b>Created:</b> {escape(order['created_at'])}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    lines = ["📦 <b>Stock List</b>\n"]

    for key, p in PRODUCTS.items():
        if p["category"] == "digital":
            total_stock = get_digital_stock(key)
            lines.append(f"💻 <b>{escape(p['name'])}</b> → {total_stock}")
            for plan_key, plan in p["plans"].items():
                lines.append(f"   • {escape(plan['label'])} = {get_digital_stock(key, plan_key)}")
        else:
            lines.append(f"🎮 <b>{escape(p['name'])}</b> → {int(p.get('stock', 0))}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def addstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "Coding နဲ့ပဲ stock add မယ်ဆို:\n\n"
        "1. game product → PRODUCTS dict ထဲက <code>stock</code> number ပြင်\n"
        "2. digital product → DIGITAL_INVENTORY dict ထဲက <code>accounts</code> list ထဲ account အသစ်ထည့်\n"
        "3. bot restart လုပ်\n\n"
        "ဥပမာ digital account:\n"
        "<code>{\n"
        "  \"plan_key\": \"share_1m\",\n"
        "  \"email\": \"new@example.com\",\n"
        "  \"password\": \"123456\",\n"
        "  \"extra\": \"Profile 1\",\n"
        "  \"used\": False,\n"
        "}</code>",
        parse_mode=ParseMode.HTML,
    )

# =========================================================
# CANCEL
# =========================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Order cancelled.",
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END
             # =========================================================
# MAIN
# =========================================================

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is missing.")
    if not ADMIN_ID:
        raise ValueError("ADMIN_ID environment variable is missing or invalid.")

    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU_STATE: [
                CallbackQueryHandler(menu_handler, pattern=r"^menu_"),
            ],
            CATEGORY_STATE: [
                CallbackQueryHandler(category_handler, pattern=r"^(cat:|back_main$)"),
            ],
            PRODUCT_STATE: [
                CallbackQueryHandler(product_handler, pattern=r"^(product:|back_categories$|out_of_stock$)"),
            ],
            PLAN_STATE: [
                CallbackQueryHandler(plan_handler, pattern=r"^(plan:|back_products$|out_of_stock$)"),
            ],
            DETAIL_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, detail_handler),
            ],
            PAYMENT_STATE: [
                CallbackQueryHandler(payment_handler, pattern=r"^(pay:|back_plan$)"),
            ],
            SCREENSHOT_STATE: [
                MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), screenshot_handler),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    # admin buttons
    application.add_handler(
    CallbackQueryHandler(admin_action, pattern=r"^(approve:|auto:|manual:|reject:)")
    )
    # admin commands
    application.add_handler(CommandHandler("deliver", deliver_command))
    application.add_handler(CommandHandler("orders", orders_command))
    application.add_handler(CommandHandler("order", order_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("addstock", addstock_command))
application.add_handler(CommandHandler("code", code_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, customer_code_request_handler))
    application.run_polling()


if __name__ == "__main__":
    main()           
