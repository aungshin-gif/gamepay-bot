import os
import sqlite3
import logging
from html import escape
from datetime import datetime
from typing import Optional, Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 0

SHOP_NAME = "GAMEPAY HUB"
CONTACT_USERNAME = "@angsthtun"

WELCOME_STICKER_ID = ""
SUCCESS_STICKER_ID = ""

LOW_STOCK_THRESHOLD = 2
DB_PATH = "gamepay_hub.db"

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

REJECT_REASONS = {
    "wrong_amount": "ငွေပမာဏမမှန်ပါ",
    "unclear_ss": "screenshot မရှင်းပါ",
    "fake_payment": "payment မအောင်မြင်သေးပါ",
    "duplicate_order": "duplicate order ဖြစ်နေပါတယ်",
    "other": "order info ပြန်စစ်ပြီးပြန်တင်ပါ",
}

PRODUCTS: Dict[str, Dict[str, Any]] = {
    "mlbb_weekly": {
        "category": "game",
        "name": "Weekly Pass",
        "full_name": "MLBB Weekly Pass",
        "description": "⚡ Fast and trusted MLBB Weekly Pass top up service.",
        "photo": "Screenshot_2026-03-31-09-45-06-397_com.mobile.legends.jpg",
        "stock": 10,
        "requires_detail_label": (
            "🆔 <b>Game ID နှင့် Server ID ရေးပေးပါ</b>\n\n"
            "ဥပမာ:\n<code>123456789 / 1234</code>"
        ),
        "plans": {
            "default": {"label": "Weekly Pass", "price": 6400},
        },
    },
    "genshin_blessing": {
        "category": "game",
        "name": "Blessing",
        "full_name": "Genshin Impact Blessing",
        "description": "✨ Safe and quick Genshin Blessing top up service.",
        "photo": "Buy-Welkin-Moon-In-Game.png",
        "stock": 10,
        "requires_detail_label": (
            "🆔 <b>UID / Server ရေးပေးပါ</b>\n\n"
            "ဥပမာ:\n<code>812345678 / Asia</code>"
        ),
        "plans": {
            "default": {"label": "Blessing", "price": 14800},
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
            "spotify_premium": {
            "category": "digital",
            "name": "Spotify Premium",
            "full_name": "Spotify Premium Subscription",
            "description": "🎵 Spotify Premium account delivery service.",
            "photo": "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?auto=format&fit=crop&w=1000&q=80",
            "requires_detail_label": (
                "📝 <b>လိုအပ်ရင် note/message ပို့ပါ</b>\n"
                "မလိုအပ်ရင် <code>No</code> လို့ပေးပါ။"
            ),
            "plans": {
                "family_1m": {"label": "Family Plan - 1 Month", "price": 8000},
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
                "plan_key": "share_3m",
                "email": "capcutshare2@example.com",
                "password": "pass2234",
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
            "spotify_premium": {
            "auto_delivery": True,
            "accounts": [
                {
                    "plan_key": "family_1m",
                    "email": "2iws8@24hournons.top",
                    "password": "masuk12345",
                    "extra": "😀 Family 1 Month",
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
            {
                "plan_key": "private_1m",
                "email": "netflixshare2@example.com",
                "password": "nf223456",
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
            "extra": "Canva Pro Edu | 1 Year account | access via atomicmail.io",
            "used": False,
        },
        {
            "plan_key": "edu_1y",
            "email": "alam0404@atomicmail.io",
            "password": "alam0404@",
            "extra": "Canva Pro Edu | 1 Year account | access via atomicmail.io",
            "used": False,
        },
        {
            "plan_key": "edu_1y",
            "email": "basta205@atomicmail.io",
            "password": "basta205@",
            "extra": "Canva Pro Edu | 1 Year account | access via atomicmail.io",
            "used": False,
        },
        {
            "plan_key": "edu_1y",
            "email": "fatfs575@atomicmail.io",
            "password": "fatfs575@",
            "extra": "Canva Pro Edu | 1 Year account | access via atomicmail.io",
            "used": False,
        },
    ],
}, 
}

(
    MENU_STATE,
    CATEGORY_STATE,
    PRODUCT_STATE,
    PLAN_STATE,
    DETAIL_STATE,
    PAYMENT_STATE,
    SCREENSHOT_STATE,
) = range(7)

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================================================
# DATABASE
# =========================================================

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def new_order_id() -> str:
    return "ORD-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")[-20:]


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
        admin_note TEXT DEFAULT ''
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
    """, (order_id, actor_id, action, note, now_str()))
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


def order_get(order_id: str) -> Optional[dict]:
    conn = db_connect()
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


def get_user_orders(user_id: int, limit: int = 10) -> List[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_orders(limit: int = 20) -> List[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM orders
        WHERE status IN ('pending_payment_review', 'waiting_manual_delivery', 'code_requested')
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_digital_stock(product_key: str, plan_key: Optional[str] = None) -> int:
    conn = db_connect()
    cur = conn.cursor()

    if plan_key:
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM digital_accounts
            WHERE product_key = ? AND plan_key = ? AND used = 0
        """, (product_key, plan_key))
    else:
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM digital_accounts
            WHERE product_key = ? AND used = 0
        """, (product_key,))

    count = cur.fetchone()["cnt"]
    conn.close()
    return int(count)


def reserve_account(product_key: str, plan_key: str, order_id: str) -> Optional[dict]:
    conn = db_connect()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("""
            SELECT id, email, password, extra
            FROM digital_accounts
            WHERE product_key = ? AND plan_key = ? AND used = 0
            ORDER BY id ASC
            LIMIT 1
        """, (product_key, plan_key))
        row = cur.fetchone()

        if not row:
            conn.rollback()
            return None

        cur.execute("""
            UPDATE digital_accounts
            SET used = 1, order_id = ?
            WHERE id = ? AND used = 0
        """, (order_id, row["id"]))

        if cur.rowcount != 1:
            conn.rollback()
            return None

        conn.commit()
        return {
            "id": row["id"],
            "email": row["email"],
            "password": row["password"],
            "extra": row["extra"] or "",
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_digital_account(product_key: str, plan_key: str, email: str, password: str, extra: str = ""):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO digital_accounts (product_key, plan_key, email, password, extra, used, order_id)
        VALUES (?, ?, ?, ?, ?, 0, NULL)
    """, (product_key, plan_key, email, password, extra))
    conn.commit()
    conn.close()


def get_stats_summary() -> dict:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cur.fetchone()["total_orders"]

    cur.execute("""
        SELECT COUNT(*) AS delivered_orders
        FROM orders
        WHERE status IN ('approved', 'delivered', 'code_sent')
    """)
    delivered_orders = cur.fetchone()["delivered_orders"]

    cur.execute("""
        SELECT COUNT(*) AS pending_orders
        FROM orders
        WHERE status IN ('pending_payment_review', 'waiting_manual_delivery', 'code_requested')
    """)
    pending_orders = cur.fetchone()["pending_orders"]

    cur.execute("""
        SELECT COUNT(*) AS rejected_orders
        FROM orders
        WHERE status = 'rejected'
    """)
    rejected_orders = cur.fetchone()["rejected_orders"]

    cur.execute("""
        SELECT COALESCE(SUM(price), 0) AS total_sales
        FROM orders
        WHERE status IN ('approved', 'delivered', 'code_sent')
    """)
    total_sales = cur.fetchone()["total_sales"]

    conn.close()

    return {
        "total_orders": int(total_orders),
        "delivered_orders": int(delivered_orders),
        "pending_orders": int(pending_orders),
        "rejected_orders": int(rejected_orders),
        "total_sales": int(total_sales),
    }

# =========================================================
# HELPERS
# =========================================================

def human_status(status: str) -> str:
    mapping = {
        "pending_payment_review": "⏳ Pending Review",
        "waiting_manual_delivery": "🟡 Waiting Manual Delivery",
        "approved": "✅ Approved",
        "delivered": "✅ Delivered",
        "code_requested": "🔐 Code Requested",
        "code_sent": "🔐 Code Sent",
        "rejected": "❌ Rejected",
    }
    return mapping.get(status, status)


def order_summary_text(order: dict) -> str:
    return (
        f"🆔 <b>Order ID:</b> <code>{escape(order['order_id'])}</code>\n"
        f"🎮 <b>Product:</b> {escape(order['product_name'])}\n"
        f"📋 <b>Plan:</b> {escape(order['plan_label'])}\n"
        f"💰 <b>Price:</b> {order['price']} Ks\n"
        f"📝 <b>Detail:</b> {escape(order.get('detail') or '-')}\n"
        f"💳 <b>Payment:</b> {escape(order.get('payment_name') or '-')}\n"
        f"📌 <b>Status:</b> {human_status(order['status'])}\n"
        f"🕒 <b>Created:</b> {escape(order['created_at'])}"
    )


def product_caption(product: dict, product_key: str) -> str:
    if product["category"] == "digital":
        stock = get_digital_stock(product_key)
        cheapest = min(v["price"] for v in product["plans"].values())
        price_text = f"From {cheapest} Ks"
    else:
        stock = int(product.get("stock", 0))
        first_price = next(iter(product["plans"].values()))["price"]
        price_text = f"{first_price} Ks"

    status = "🟢 In Stock" if stock > 0 else "🔴 Out of Stock"

    return (
        f"✨ <b>{escape(product['full_name'])}</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Price:</b> {escape(price_text)}\n"
        f"📦 <b>Stock:</b> {stock}\n"
        f"📌 <b>Status:</b> {status}\n\n"
        f"📝 <b>Description</b>\n"
        f"{escape(product['description'])}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⚡ Fast • 🔒 Safe • 💖 Trusted"
    )


def payment_text(payment_name: str, account: str, amount: int) -> str:
    return (
        f"💸 <b>PAYMENT INFO</b>\n\n"
        f"🏦 <b>Method:</b> {escape(payment_name)}\n"
        f"📲 <b>Account:</b>\n{escape(account)}\n\n"
        f"💰 <b>Amount:</b> {amount} Ks\n\n"
        f"✅ ငွေလွှဲပြီး <b>payment screenshot</b> ပို့ပေးပါ\n"
        f"📨 ပြီးတာနဲ့ admin ဆီ order တက်သွားပါမယ်"
    )


def welcome_text() -> str:
    return (
        f"🌈⚡ <b>{escape(SHOP_NAME)}</b> ⚡🌈\n\n"
        f"🎮 <b>Welcome from {escape(SHOP_NAME)}</b>\n"
        f"မြန်ဆန် • စိတ်ချရ • ယုံကြည်ရတဲ့ Top Up Service 💎\n\n"
        f"✨ <b>What would you like to do?</b>\n"
        f"အောက်က menu ကနေရွေးပေးပါ 👇\n\n"
        f"⚡ Fast Service\n"
        f"🔒 Safe Payment\n"
        f"💖 Trusted Top Up"
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ Shop", callback_data="menu_shop")],
        [InlineKeyboardButton("📦 My Orders", callback_data="menu_myorders")],
        [InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact")],
        [InlineKeyboardButton("🔄 Restart", callback_data="menu_restart")],
    ])


def category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Game Top Up", callback_data="cat:game")],
        [InlineKeyboardButton("💻 Digital Products", callback_data="cat:digital")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")],
    ])


def products_keyboard(category_key: str) -> InlineKeyboardMarkup:
    rows = []

    for key, product in PRODUCTS.items():
        if product["category"] != category_key:
            continue

        if category_key == "digital":
            total_stock = get_digital_stock(key)
            cheapest = min(v["price"] for v in product["plans"].values())
            if total_stock > 0:
                rows.append([
                    InlineKeyboardButton(
                        f"✨ {product['name']} • From {cheapest} Ks",
                        callback_data=f"product:{key}",
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"🔴 {product['name']} • Out of Stock",
                        callback_data="out_of_stock",
                    )
                ])
        else:
            stock = int(product.get("stock", 0))
            default_price = next(iter(product["plans"].values()))["price"]
            if stock > 0:
                rows.append([
                    InlineKeyboardButton(
                        f"✨ {product['name']} • {default_price} Ks",
                        callback_data=f"product:{key}",
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"🔴 {product['name']} • Out of Stock",
                        callback_data="out_of_stock",
                    )
                ])

    rows.append([InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_categories")])
    return InlineKeyboardMarkup(rows)


def plans_keyboard(product_key: str) -> InlineKeyboardMarkup:
    rows = []
    product = PRODUCTS[product_key]

    for plan_key, plan in product["plans"].items():
        if product["category"] == "digital":
            stock = get_digital_stock(product_key, plan_key)
            if stock > 0:
                rows.append([
                    InlineKeyboardButton(
                        f"{plan['label']} • {plan['price']} Ks",
                        callback_data=f"plan:{plan_key}",
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"🔴 {plan['label']} • Out of Stock",
                        callback_data="out_of_stock",
                    )
                ])
        else:
            stock = int(product.get("stock", 0))
            if stock > 0:
                rows.append([
                    InlineKeyboardButton(
                        f"{plan['label']} • {plan['price']} Ks",
                        callback_data=f"plan:{plan_key}",
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"🔴 {plan['label']} • Out of Stock",
                        callback_data="out_of_stock",
                    )
                ])

    rows.append([InlineKeyboardButton("⬅️ Back to Products", callback_data="back_products")])
    return InlineKeyboardMarkup(rows)


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(PAYMENT_ACCOUNTS["kpay"]["label"], callback_data="pay:kpay")],
        [InlineKeyboardButton(PAYMENT_ACCOUNTS["wave"]["label"], callback_data="pay:wave")],
        [InlineKeyboardButton(PAYMENT_ACCOUNTS["aya"]["label"], callback_data="pay:aya")],
        [InlineKeyboardButton(PAYMENT_ACCOUNTS["uab"]["label"], callback_data="pay:uab")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_plan")],
    ])


def admin_action_keyboard(order_id: str, category: str) -> InlineKeyboardMarkup:
    if category == "digital":
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚡ Auto", callback_data=f"auto:{order_id}"),
                InlineKeyboardButton("✍️ Manual", callback_data=f"manual:{order_id}"),
            ],
            [InlineKeyboardButton("❌ Reject", callback_data=f"rejectmenu:{order_id}")],
        ])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{order_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rejectmenu:{order_id}"),
        ]
    ])


def reject_reason_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ငွေပမာဏမမှန်", callback_data=f"reject:{order_id}:wrong_amount")],
        [InlineKeyboardButton("Screenshot မရှင်း", callback_data=f"reject:{order_id}:unclear_ss")],
        [InlineKeyboardButton("Payment မအောင်မြင်", callback_data=f"reject:{order_id}:fake_payment")],
        [InlineKeyboardButton("Duplicate Order", callback_data=f"reject:{order_id}:duplicate_order")],
        [InlineKeyboardButton("Other", callback_data=f"reject:{order_id}:other")],
    ])


async def send_optional_sticker(message_obj, sticker_id: str):
    if sticker_id:
        try:
            await message_obj.reply_sticker(sticker=sticker_id)
        except Exception as e:
            logger.warning("Sticker send failed: %s", e)


async def send_optional_bot_sticker(bot, chat_id: int, sticker_id: str):
    if sticker_id:
        try:
            await bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
        except Exception as e:
            logger.warning("Bot sticker send failed: %s", e)


async def send_product_preview(message_obj, product_key: str):
    product = PRODUCTS[product_key]
    caption = product_caption(product, product_key)

    try:
        await message_obj.reply_photo(
            photo=product["photo"],
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.warning("Photo preview failed for %s: %s", product_key, e)
        await message_obj.reply_text(caption, parse_mode=ParseMode.HTML)


async def maybe_send_low_stock_alert(bot, product_key: str, plan_key: Optional[str] = None):
    try:
        product = PRODUCTS.get(product_key)
        if not product:
            return

        if product["category"] == "digital":
            current_stock = get_digital_stock(product_key, plan_key)
            if current_stock <= LOW_STOCK_THRESHOLD:
                plan_label = "All Plans"
                if plan_key and plan_key in product["plans"]:
                    plan_label = product["plans"][plan_key]["label"]

                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"⚠️ <b>Low Stock Alert</b>\n\n"
                        f"🎮 <b>Product:</b> {escape(product['full_name'])}\n"
                        f"📋 <b>Plan:</b> {escape(plan_label)}\n"
                        f"📦 <b>Remaining:</b> {current_stock}"
                    ),
                    parse_mode=ParseMode.HTML,
                )
        else:
            current_stock = int(product.get("stock", 0))
            if current_stock <= LOW_STOCK_THRESHOLD:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"⚠️ <b>Low Stock Alert</b>\n\n"
                        f"🎮 <b>Product:</b> {escape(product['full_name'])}\n"
                        f"📦 <b>Remaining:</b> {current_stock}"
                    ),
                    parse_mode=ParseMode.HTML,
                )
    except Exception as e:
        logger.warning("Low stock alert failed: %s", e)

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

    if data == "menu_myorders":
        rows = get_user_orders(query.from_user.id, limit=5)
        if not rows:
            await query.message.reply_text("📦 သင့် order history မရှိသေးပါ။")
            return MENU_STATE

        lines = ["📦 <b>Your Recent Orders</b>\n"]
        for o in rows:
            lines.append(
                f"🆔 <code>{escape(o['order_id'])}</code>\n"
                f"🎮 {escape(o['product_name'])}\n"
                f"📋 {escape(o['plan_label'])}\n"
                f"📌 {human_status(o['status'])}\n"
                f"🕒 {escape(o['created_at'])}\n"
            )
        lines.append("အသေးစိတ်ကြည့်ရန်: <code>/track ORDER_ID</code>")
        await query.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        return MENU_STATE

    if data == "menu_contact":
        await query.message.reply_text(
            "📞 <b>Contact Admin</b>\n\n"
            f"👤 Telegram: {escape(CONTACT_USERNAME)}",
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
            "🗂️ <b>Please choose a category</b>",
            reply_markup=category_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return CATEGORY_STATE

    if data == "out_of_stock":
        await query.message.reply_text("🔴 This item is out of stock.")
        return PRODUCT_STATE

    if data.startswith("product:"):
        product_key = data.split(":", 1)[1]
        if product_key not in PRODUCTS:
            await query.message.reply_text("❌ Invalid product.")
            return PRODUCT_STATE

        product = PRODUCTS[product_key]
        context.user_data["product_key"] = product_key
        context.user_data["product_name"] = product["full_name"]
        context.user_data["category"] = product["category"]

        await send_product_preview(query.message, product_key)
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

        if not product_key or product_key not in PRODUCTS:
            await query.message.reply_text("❌ Session error. /start နဲ့ပြန်စပါ။")
            context.user_data.clear()
            return ConversationHandler.END

        product = PRODUCTS[product_key]
        if plan_key not in product["plans"]:
            await query.message.reply_text("❌ Invalid plan.")
            return PLAN_STATE

        plan = product["plans"][plan_key]

        if product["category"] == "digital":
            if get_digital_stock(product_key, plan_key) <= 0:
                await query.message.reply_text("🔴 ဒီ plan က stock မရှိတော့ပါ။")
                return PLAN_STATE
        else:
            if int(product.get("stock", 0)) <= 0:
                await query.message.reply_text("🔴 ဒီ item က stock မရှိတော့ပါ။")
                return PLAN_STATE

        context.user_data["plan_key"] = plan_key
        context.user_data["plan_label"] = plan["label"]
        context.user_data["price"] = int(plan["price"])

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
    if not text:
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
        if not product_key:
            await query.message.reply_text("❌ Session error. /start နဲ့ပြန်စပါ။")
            return ConversationHandler.END

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

    context.user_data["payment_key"] = payment_key
    context.user_data["payment_name"] = PAYMENT_ACCOUNTS[payment_key]["label"]

    await query.message.reply_text(
        payment_text(
            PAYMENT_ACCOUNTS[payment_key]["label"],
            PAYMENT_ACCOUNTS[payment_key]["text"],
            int(context.user_data["price"]),
        ),
        parse_mode=ParseMode.HTML,
    )
    return SCREENSHOT_STATE


async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        if update.message:
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
        "📥 <b>NEW ORDER</b>\n\n"
        f"{order_summary_text(data)}\n\n"
        f"👤 <b>Customer:</b> {escape(data['full_name'])}\n"
        f"📎 <b>Username:</b> {escape(data['username'] or '-')}\n"
        f"🪪 <b>User ID:</b> <code>{data['user_id']}</code>"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=admin_caption,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_action_keyboard(order_id, data["category"]),
    )

    await update.message.reply_text(
        "✅ <b>Order received successfully!</b>\n\n"
        f"{order_summary_text(data)}",
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

    # reject menu
    if raw.startswith("rejectmenu:"):
        order_id = raw.split(":", 1)[1]
        await query.message.reply_text(
            f"❌ <b>Reject Reason ရွေးပါ</b>\n🆔 <code>{escape(order_id)}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=reject_reason_keyboard(order_id),
        )
        return

    # reject action
    if raw.startswith("reject:"):
        try:
            _, order_id, reason_key = raw.split(":", 2)
        except ValueError:
            return

        order = order_get(order_id)
        if not order:
            return

        reason_text = REJECT_REASONS.get(reason_key, "Order rejected")
        order_update_status(order_id, "rejected", reason_text)
        log_action(order_id, query.from_user.id, "rejected", reason_text)

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                "❌ <b>Order Rejected</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"📌 <b>Reason:</b> {escape(reason_text)}"
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    # approve / auto / manual
    try:
        action, order_id = raw.split(":", 1)
    except ValueError:
        return

    order = order_get(order_id)
    if not order:
        return

    # GAME APPROVE
    if action == "approve":
        product = PRODUCTS.get(order["product_key"])
        if not product or order["category"] != "game":
            return

        if int(product.get("stock", 0)) <= 0:
            await query.message.reply_text("❌ Stock မရှိတော့ပါ။")
            return

        product["stock"] -= 1
        order_update_status(order_id, "approved", "Game order approved")
        log_action(order_id, query.from_user.id, "approved_game")

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                "✅ <b>Order Approved!</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"🎮 <b>Product:</b> {escape(order.get('product_name', '-'))}\n"
                "💖 Thanks for using Gamepay Hub"
            ),
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"✅ <b>Approved</b>\n\n"
            f"🆔 <code>{escape(order_id)}</code>\n"
            f"🎮 {escape(order.get('product_name', '-'))}\n"
            f"📦 Remaining Stock: {product['stock']}",
            parse_mode=ParseMode.HTML,
        )

        await maybe_send_low_stock_alert(context.bot, order["product_key"])
        return

    # DIGITAL AUTO
    if action == "auto":
        if order["category"] != "digital":
            return

        product_cfg = DIGITAL_INVENTORY.get(order["product_key"], {})

        if not bool(product_cfg.get("auto_delivery", False)):
            order_update_status(order_id, "waiting_manual_delivery", "Manual only product")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"✍️ <b>Manual delivery required</b>\n\n"
                    f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        account = reserve_account(order["product_key"], order["plan_key"], order_id)
        if not account:
            order_update_status(order_id, "waiting_manual_delivery", "Auto stock not found")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"❌ <b>Auto stock not found</b>\n\n"
                    f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        order_update_status(order_id, "delivered", "Auto delivered")
        log_action(order_id, query.from_user.id, "auto_delivered")

        delivery_text = (
            f"✅ <b>Your {escape(order.get('product_name', '-'))} order is ready!</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"📧 <b>Email:</b> <code>{escape(account['email'])}</code>\n"
            f"🔑 <b>Password:</b> <code>{escape(account['password'])}</code>\n"
        )

        if account["extra"]:
            delivery_text += f"\n📝 <b>Note:</b> {escape(account['extra'])}\n"

        delivery_text += "\n<code>Code</code> လို့ရိုက်ပို့ပြီး login code တောင်းနိုင်ပါတယ်။"

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=delivery_text,
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"✅ <b>Auto Delivered</b>\n\n"
            f"🆔 <code>{escape(order_id)}</code>\n"
            f"🎮 {escape(order.get('product_name', '-'))}",
            parse_mode=ParseMode.HTML,
        )

        await maybe_send_low_stock_alert(context.bot, order["product_key"], order["plan_key"])
        return

    # DIGITAL MANUAL
    if action == "manual":
        if order["category"] != "digital":
            return

        order_update_status(order_id, "waiting_manual_delivery", "Waiting admin manual delivery")

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"✍️ <b>Manual delivery selected</b>\n\n"
                f"<code>/deliver {escape(order_id)} Email: yourmail@gmail.com Password: 123456</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
        return
                
    


    # =====================================================
    # GAME APPROVE
    # =====================================================
    if action == "approve":
        product = PRODUCTS.get(order["product_key"])
        if not product or order["category"] != "game":
            return

        if int(product.get("stock", 0)) <= 0:
            await query.message.reply_text("❌ Stock မရှိတော့ပါ။")
            return

        product["stock"] -= 1
        order_update_status(order_id, "approved", "Game order approved")
        log_action(order_id, query.from_user.id, "approved_game")

        # customer notify
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                "✅ <b>Order Approved!</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"🎮 <b>Product:</b> {escape(order.get('product_name', '-'))}\n"
                "💖 Thanks for using Gamepay Hub"
            ),
            parse_mode=ParseMode.HTML,
        )

        # admin feedback
        await query.message.reply_text(
            f"✅ <b>Approved</b>\n\n"
            f"🆔 <code>{escape(order_id)}</code>\n"
            f"🎮 {escape(order.get('product_name', '-'))}\n"
            f"📦 Remaining Stock: {product['stock']}",
            parse_mode=ParseMode.HTML,
        )

        await maybe_send_low_stock_alert(context.bot, order["product_key"])
        return

    # =====================================================
    # DIGITAL AUTO
    # =====================================================
    if action == "auto":
        if order["category"] != "digital":
            return

        product_cfg = DIGITAL_INVENTORY.get(order["product_key"], {})

        if not bool(product_cfg.get("auto_delivery", False)):
            order_update_status(order_id, "waiting_manual_delivery", "Manual only product")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"✍️ <b>Manual delivery required</b>\n\n"
                    f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        account = reserve_account(order["product_key"], order["plan_key"], order_id)
        if not account:
            order_update_status(order_id, "waiting_manual_delivery", "Auto stock not found")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"❌ <b>Auto stock not found</b>\n\n"
                    f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        order_update_status(order_id, "delivered", "Auto delivered")
        log_action(order_id, query.from_user.id, "auto_delivered")

        delivery_text = (
            f"✅ <b>Your {escape(order.get('product_name', '-'))} order is ready!</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"📧 <b>Email:</b> <code>{escape(account['email'])}</code>\n"
            f"🔑 <b>Password:</b> <code>{escape(account['password'])}</code>\n"
        )

        if account["extra"]:
            delivery_text += f"\n📝 <b>Note:</b> {escape(account['extra'])}\n"

        delivery_text += "\n<code>Code</code> လို့ရိုက်ပို့ပြီး login code တောင်းနိုင်ပါတယ်။"

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=delivery_text,
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"✅ <b>Auto Delivered</b>\n\n"
            f"🆔 <code>{escape(order_id)}</code>\n"
            f"🎮 {escape(order.get('product_name', '-'))}",
            parse_mode=ParseMode.HTML,
        )

        await maybe_send_low_stock_alert(context.bot, order["product_key"], order["plan_key"])
        return

    # =====================================================
    # DIGITAL MANUAL
    # =====================================================
    if action == "manual":
        if order["category"] != "digital":
            return

        order_update_status(order_id, "waiting_manual_delivery", "Waiting admin manual delivery")

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"✍️ <b>Manual delivery selected</b>\n\n"
                f"<code>/deliver {escape(order_id)} Email: yourmail@gmail.com Password: 123456</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
        return

# =========================================================
# COMMANDS
# =========================================================

async def deliver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not update.message or not update.message.text:
        return

    parts = update.message.text.strip().split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Usage: /deliver ORDER_ID Email: xxx Password: yyy")
        return

    _, order_id, delivery_text = parts
    order = order_get(order_id)
    if not order:
        await update.message.reply_text("❌ Order not found.")
        return

    await context.bot.send_message(
        chat_id=order["user_id"],
        text=(
            f"✅ <b>Your {escape(order['product_name'])} order is ready!</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"<pre>{escape(delivery_text)}</pre>"
        ),
        parse_mode=ParseMode.HTML,
    )
    order_update_status(order_id, "delivered", "Manually delivered")
    log_action(order_id, update.effective_user.id, "manually_delivered", delivery_text)
    await update.message.reply_text("✅ Delivered successfully.")


async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /code ORDER_ID 123456")
        return

    order_id = context.args[0]
    code_value = " ".join(context.args[1:])
    order = order_get(order_id)
    if not order:
        await update.message.reply_text("❌ Order not found.")
        return

    await context.bot.send_message(
        chat_id=order["user_id"],
        text=(
            f"🔐 <b>Your login code is ready</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"🔢 <b>Code:</b> <code>{escape(code_value)}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )
    order_update_status(order_id, "code_sent", "Admin sent login code")
    await update.message.reply_text("✅ Login code ပို့ပြီးပါပြီ။")
async def delete_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/delete_account email@example.com",
            parse_mode=ParseMode.HTML,
        )
        return

    email = context.args[0].strip()

    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM digital_accounts WHERE email = ? AND used = 0",
        (email,),
    )
    deleted = cur.rowcount

    conn.commit()
    conn.close()

    if deleted:
        await update.message.reply_text(f"✅ Deleted: {email}")
    else:
        await update.message.reply_text("❌ Email not found or already used")


async def remove_game_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage:\n/remove_game_stock PRODUCT_KEY QTY",
            parse_mode=ParseMode.HTML,
        )
        return

    product_key = context.args[0].strip()
    qty_text = context.args[1].strip()

    if product_key not in PRODUCTS:
        await update.message.reply_text("❌ Invalid product key.")
        return

    if PRODUCTS[product_key]["category"] != "game":
        await update.message.reply_text("❌ ဒီ command က game product အတွက်ပဲပါ။")
        return

    try:
        qty = int(qty_text)
    except ValueError:
        await update.message.reply_text("❌ QTY must be a number.")
        return

    if qty <= 0:
        await update.message.reply_text("❌ QTY must be greater than 0.")
        return

    current_stock = int(PRODUCTS[product_key].get("stock", 0))

    if qty > current_stock:
        await update.message.reply_text(
            f"❌ Current stock = {current_stock} only.",
            parse_mode=ParseMode.HTML,
        )
        return

    PRODUCTS[product_key]["stock"] = current_stock - qty
    log_action(None, update.effective_user.id, "remove_game_stock", f"{product_key} -{qty}")

    await update.message.reply_text(
        f"✅ <b>Game stock reduced</b>\n\n"
        f"🎮 <b>Product:</b> {escape(PRODUCTS[product_key]['full_name'])}\n"
        f"➖ <b>Removed:</b> {qty}\n"
        f"📦 <b>Remaining Stock:</b> {PRODUCTS[product_key]['stock']}",
        parse_mode=ParseMode.HTML,
    )

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
            f"📌 {human_status(o['status'])}\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /order ORDER_ID")
        return

    order = order_get(context.args[0])
    if not order:
        await update.message.reply_text("❌ Order not found.")
        return
    await update.message.reply_text(order_summary_text(order), parse_mode=ParseMode.HTML)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    stats = get_stats_summary()
    await update.message.reply_text(
        "📊 <b>Bot Statistics</b>\n\n"
        f"📦 <b>Total Orders:</b> {stats['total_orders']}\n"
        f"✅ <b>Delivered / Approved:</b> {stats['delivered_orders']}\n"
        f"⏳ <b>Pending:</b> {stats['pending_orders']}\n"
        f"❌ <b>Rejected:</b> {stats['rejected_orders']}\n"
        f"💰 <b>Total Sales:</b> {stats['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lines = ["📦 <b>Stock List</b>\n"]
    for key, p in PRODUCTS.items():
        if p["category"] == "digital":
            lines.append(f"💻 <b>{escape(p['name'])}</b> → {get_digital_stock(key)}")
        else:
            lines.append(f"🎮 <b>{escape(p['name'])}</b> → {int(p.get('stock', 0))}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def add_game_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or len(context.args) != 2:
        return
    product_key = context.args[0]
    qty = int(context.args[1])
    if product_key in PRODUCTS and PRODUCTS[product_key]["category"] == "game":
        PRODUCTS[product_key]["stock"] = int(PRODUCTS[product_key].get("stock", 0)) + qty
        await update.message.reply_text("✅ Game stock updated.")


async def add_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not update.message or not update.message.text:
        return
    payload = update.message.text[len("/add_account"):].strip()
    extra = ""
    if "|" in payload:
        main_part, extra = payload.split("|", 1)
        extra = extra.strip()
    else:
        main_part = payload
    parts = main_part.split()
    if len(parts) < 4:
        await update.message.reply_text("❌ Format မမှန်ပါ။")
        return
    product_key, plan_key, email = parts[0], parts[1], parts[2]
    password = " ".join(parts[3:])
    add_digital_account(product_key, plan_key, email, password, extra)
    await update.message.reply_text("✅ Digital account added.")


async def addstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(
            "/add_game_stock PRODUCT_KEY QTY\n/add_account PRODUCT_KEY PLAN_KEY EMAIL PASSWORD | EXTRA"
        )


async def myorders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_user_orders(update.effective_user.id, limit=10)
    if not rows:
        await update.message.reply_text("📦 သင့် order history မရှိသေးပါ။")
        return
    lines = ["📦 <b>Your Recent Orders</b>\n"]
    for o in rows:
        lines.append(
            f"🆔 <code>{escape(o['order_id'])}</code>\n"
            f"🎮 {escape(o['product_name'])}\n"
            f"📋 {escape(o['plan_label'])}\n"
            f"📌 {human_status(o['status'])}\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /track ORDER_ID")
        return
    order = order_get(context.args[0])
    if not order:
        await update.message.reply_text("❌ Order not found.")
        return
    if update.effective_user.id != ADMIN_ID and order["user_id"] != update.effective_user.id:
        await update.message.reply_text("❌ ဒီ order ကိုကြည့်ခွင့်မရှိပါ။")
        return
    await update.message.reply_text(order_summary_text(order), parse_mode=ParseMode.HTML)


async def customer_code_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if update.effective_user.id == ADMIN_ID:
        return
    if update.message.text.strip().lower() != "code":
        return

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
          AND category = 'digital'
          AND status IN ('delivered', 'code_requested', 'code_sent')
        ORDER BY created_at DESC
        LIMIT 1
    """, (update.effective_user.id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("❌ Active digital order မတွေ့ပါ။")
        return

    order = dict(row)
    order_update_status(order["order_id"], "code_requested", "Customer requested login code")
    await update.message.reply_text("⏳ Code request ကို admin ဆီပို့ပြီးပါပြီ။")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"<code>/code {escape(order['order_id'])} 123456</code>",
        parse_mode=ParseMode.HTML,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.message:
        await update.message.reply_text("❌ Order cancelled.", reply_markup=main_menu_keyboard())
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
            MENU_STATE: [CallbackQueryHandler(menu_handler, pattern=r"^menu_")],
            CATEGORY_STATE: [CallbackQueryHandler(category_handler, pattern=r"^(cat:|back_main$)")],
            PRODUCT_STATE: [CallbackQueryHandler(product_handler, pattern=r"^(product:|back_categories$|out_of_stock$)")],
            PLAN_STATE: [CallbackQueryHandler(plan_handler, pattern=r"^(plan:|back_products$|out_of_stock$)")],
            DETAIL_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, detail_handler)],
            PAYMENT_STATE: [CallbackQueryHandler(payment_handler, pattern=r"^(pay:|back_plan$)")],
            SCREENSHOT_STATE: [MessageHandler(filters.PHOTO, screenshot_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    application.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern=r"^(approve:|auto:|manual:|rejectmenu:|reject:)"
        )
    )

    application.add_handler(CommandHandler("myorders", myorders_command))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("deliver", deliver_command))
    application.add_handler(CommandHandler("orders", orders_command))
    application.add_handler(CommandHandler("order", order_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("addstock", addstock_command))
    application.add_handler(CommandHandler("add_game_stock", add_game_stock_command))
    application.add_handler(CommandHandler("remove_game_stock", remove_game_stock_command))
    application.add_handler(CommandHandler("add_account", add_account_command))
    application.add_handler(CommandHandler("delete_account", delete_account_command))
    application.add_handler(CommandHandler("code", code_command))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, customer_code_request_handler)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
