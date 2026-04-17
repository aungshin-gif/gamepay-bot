import os
import sqlite3
import logging
from html import escape
from datetime import datetime, timedelta
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
CHANNEL_URL = "https://t.me/gamepaydyet"

WELCOME_STICKER_ID = ""
SUCCESS_STICKER_ID = ""

LOW_STOCK_THRESHOLD = 2
DB_PATH = "gamepay_hub.db"
DUPLICATE_ORDER_WINDOW_MINUTES = 5

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
    "unclear_ss": "Screenshot မရှင်းပါ",
    "fake_payment": "Payment မအောင်မြင်သေးပါ",
    "duplicate_order": "Duplicate order ဖြစ်နေပါတယ်",
    "other": "Order info ပြန်စစ်ပြီး ပြန်တင်ပါ",
}

PRODUCTS: Dict[str, Dict[str, Any]] = {
    "mlbb_weekly": {
        "category": "game",
        "name": "Weekly Pass",
        "full_name": "MLBB Weekly Pass",
        "description": "⚡ Fast and trusted MLBB Weekly Pass top up service.",
        "photo": "Screenshot_2026-03-31-09-45-06-397_com.mobile.legends.jpg",
        "stock": 10,
        "enabled": True,
        "requires_detail_label": (
            "🆔 <b>Game ID + Server ID ပို့ပေးပါ</b>\n\n"
            "ဥပမာ:\n<code>123456789 / 1234</code>\n\n"
            "💡 Note မရှိရင် <b>Skip / No Note</b> ကိုနှိပ်လို့ရပါတယ်။"
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
        "enabled": True,
        "requires_detail_label": (
            "🆔 <b>UID / Server ပို့ပေးပါ</b>\n\n"
            "ဥပမာ:\n<code>812345678 / Asia</code>\n\n"
            "💡 Note မရှိရင် <b>Skip / No Note</b> ကိုနှိပ်လို့ရပါတယ်။"
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
        "enabled": True,
        "requires_detail_label": (
            "📝 <b>လိုအပ်ရင် note / message ပို့ပါ</b>\n"
            "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ သို့မဟုတ် <b>Skip / No Note</b> ကိုနှိပ်ပါ။"
        ),
        "plans": {
            "share_1m": {"label": "Share Plan - 1 Month", "price": 5500},
            "share_3m": {"label": "Share Plan - 3 Months", "price": 15000},
            "private_1m": {"label": "Private Plan - 1 Month", "price": 8000},
            "private_3m": {"label": "Private Plan - 3 Months", "price": 25000},
            "ownmail_1m": {"label": "Own Mail Plan - 1 Month", "price": 12000},
        },
    },
    "express_vpn": {
        "category": "digital",
        "name": "Express VPN",
        "full_name": "Express VPN Subscription",
        "description": "🌐 Express VPN email & password delivery service.",
        "photo": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
        "requires_detail_label": (
            "📝 <b>လိုအပ်ရင် note / message ပို့ပါ</b>\n"
            "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ သို့မဟုတ် <b>Skip / No Note</b> ကိုနှိပ်ပါ။"
        ),
        "plans": {
            "mobile_share_1m": {"label": "1 Month (Share) - Mobile", "price": 1200},
            "pc_share_1m": {"label": "1 Month (Share) - PC/Windows", "price": 2500},
            "mac_linux_share_1m": {"label": "1 Month (Share) - Mac/Linux", "price": 2500},
            "private_1m": {"label": "1 Month Private - All Devices Support", "price": 6500},
        },
    },
    "spotify_premium": {
        "category": "digital",
        "name": "Spotify Premium",
        "full_name": "Spotify Premium Subscription",
        "description": "🎵 Spotify Premium account delivery service.",
        "photo": "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?auto=format&fit=crop&w=1000&q=80",
        "enabled": True,
        "requires_detail_label": (
            "📝 <b>လိုအပ်ရင် note / message ပို့ပါ</b>\n"
            "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ သို့မဟုတ် <b>Skip / No Note</b> ကိုနှိပ်ပါ။"
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
        "enabled": True,
        "requires_detail_label": (
            "📝 <b>လိုအပ်ရင် note / message ပို့ပါ</b>\n"
            "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ သို့မဟုတ် <b>Skip / No Note</b> ကိုနှိပ်ပါ။"
        ),
        "plans": {
            "share_1m": {"label": "Share Plan - 1 Month", "price": 8000},
            "private_1m": {"label": "Private Plan - 1 Month", "price": 13000},
        },
    },
    "canva_pro_edu": {
        "category": "digital",
        "name": "Canva Pro Edu",
        "full_name": "Canva Pro Edu Subscription",
        "description": "🎨 Canva Pro Edu invite delivery service.",
        "photo": "https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
        "requires_detail_label": (
            "📧 <b>Canva Mail ပို့ပေးပါ</b>\n\n"
            "👉 Invite ပို့ဖို့ mail လိုပါတယ်\n"
            "ဥပမာ:\n<code>example@gmail.com</code>"
        ),
        "plans": {
            "edu_1y": {"label": "1 Year Invite Access", "price": 3200},
        },
    },
    "gemini_ai_pro": {
        "category": "digital",
        "name": "Gemini Ai Pro",
        "full_name": "Gemini Ai Pro Subscription",
        "description": "🤖 Gemini Ai Pro own-mail invite service.",
        "photo": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
        "requires_detail_label": (
            "📧 <b>Gemini Mail ပို့ပေးပါ</b>\n\n"
            "👉 Invite ပို့ဖို့ mail လိုပါတယ်\n"
            "ဥပမာ:\n<code>example@gmail.com</code>\n\n"
            "⚠️ Mail မဖြစ်မနေလိုပါတယ်"
        ),
        "plans": {
            "invite_1m": {"label": "1 Month - Ownmail Invite", "price": 5000},
        },
    },
    "grammarly_ai": {
        "category": "digital",
        "name": "Grammarly Ai",
        "full_name": "Grammarly Ai Subscription",
        "description": "💳 Grammarly Ai account delivery service.",
        "photo": "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
        "requires_detail_label": (
            "📝 <b>လိုအပ်ရင် note / message ပို့ပါ</b>\n"
            "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ သို့မဟုတ် <b>Skip / No Note</b> ကိုနှိပ်ပါ။"
        ),
        "plans": {
            "gram_1m": {"label": "1 Month", "price": 9000},
            "gram_2m": {"label": "2 Months", "price": 13500},
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
    "express_vpn": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "mobile_share_1m",
                "email": "expressmobile1@example.com",
                "password": "pass1234",
                "extra": "📱 Mobile Only",
                "used": False,
            },
            {
                "plan_key": "pc_share_1m",
                "email": "expresspc1@example.com",
                "password": "pass1234",
                "extra": "💻 PC / Windows Only",
                "used": False,
            },
            {
                "plan_key": "mac_linux_share_1m",
                "email": "expressmac1@example.com",
                "password": "pass1234",
                "extra": "🖥️ Mac / Linux Only",
                "used": False,
            },
            {
                "plan_key": "private_1m",
                "email": "expressprivate1@example.com",
                "password": "pass1234",
                "extra": "✅ Private Account\n✅ All Devices Support",
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
                "extra": "🎵 Family 1 Month",
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
                "extra": "📌 Profile 1 ကိုပဲသုံးပါ။",
                "used": False,
            },
            {
                "plan_key": "private_1m",
                "email": "netflixshare2@example.com",
                "password": "nf223456",
                "extra": "📌 Profile 1 ကိုပဲသုံးပါ။",
                "used": False,
            },
        ],
    },
    "canva_pro_edu": {
        "auto_delivery": False,
        "accounts": [],
    },
    "gemini_ai_pro": {
        "auto_delivery": False,
        "accounts": [],
    },
    "grammarly_ai": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "gram_1m",
                "email": "grammarly1@example.com",
                "password": "gram12345",
                "extra": "✅ 2 devices\n✅ Full Warranty\n✅ Projects/Notes are private",
                "used": False,
            },
            {
                "plan_key": "gram_2m",
                "email": "grammarly2@example.com",
                "password": "gram67890",
                "extra": "✅ 2 devices\n✅ Full Warranty\n✅ Projects/Notes are private",
                "used": False,
            },
        ],
    },
}

INVITE_ONLY_PRODUCTS = {"canva_pro_edu", "gemini_ai_pro"}

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


def now_dt() -> datetime:
    return datetime.now()


def now_str() -> str:
    return now_dt().strftime("%Y-%m-%d %H:%M:%S")


def new_order_id() -> str:
    return "ORD-" + now_dt().strftime("%Y%m%d-%H%M%S-%f")[-20:]


def init_db():
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        """
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
        """
    )

    cur.execute(
        """
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
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            actor_id INTEGER,
            action TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS game_products (
            product_key TEXT PRIMARY KEY,
            stock INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()

    sync_inventory_to_db()
    sync_game_products_to_db()


def sync_inventory_to_db():
    conn = db_connect()
    cur = conn.cursor()

    for product_key, cfg in DIGITAL_INVENTORY.items():
        for acc in cfg.get("accounts", []):
            cur.execute(
                """
                SELECT id FROM digital_accounts
                WHERE product_key = ? AND plan_key = ? AND email = ? AND password = ?
                """,
                (
                    product_key,
                    acc["plan_key"],
                    acc["email"],
                    acc["password"],
                ),
            )
            exists = cur.fetchone()

            if not exists:
                cur.execute(
                    """
                    INSERT INTO digital_accounts (
                        product_key, plan_key, email, password, extra, used, order_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_key,
                        acc["plan_key"],
                        acc["email"],
                        acc["password"],
                        acc.get("extra", ""),
                        1 if acc.get("used", False) else 0,
                        None,
                    ),
                )

    conn.commit()
    conn.close()


def sync_game_products_to_db():
    conn = db_connect()
    cur = conn.cursor()

    for product_key, product in PRODUCTS.items():
        if product["category"] != "game":
            continue

        cur.execute("SELECT product_key FROM game_products WHERE product_key = ?", (product_key,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(
                """
                INSERT INTO game_products (product_key, stock, enabled, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    product_key,
                    int(product.get("stock", 0)),
                    1 if product.get("enabled", True) else 0,
                    now_str(),
                ),
            )

    conn.commit()
    conn.close()


def log_action(order_id: Optional[str], actor_id: int, action: str, note: str = ""):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO audit_logs (order_id, actor_id, action, note, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (order_id, actor_id, action, note, now_str()),
    )
    conn.commit()
    conn.close()


def order_insert(data: dict):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO orders (
            order_id, user_id, username, full_name,
            product_key, product_name, plan_key, plan_label,
            category, price, detail, payment_key, payment_name,
            screenshot_file_id, status, created_at, updated_at, admin_note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
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
        ),
    )
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
    cur.execute(
        """
        UPDATE orders
        SET status = ?, updated_at = ?, admin_note = ?
        WHERE order_id = ?
        """,
        (status, now_str(), admin_note, order_id),
    )
    conn.commit()
    conn.close()


def get_user_orders(user_id: int, limit: int = 10) -> List[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_orders(limit: int = 20) -> List[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM orders
        WHERE status IN ('pending_payment_review', 'waiting_manual_delivery', 'code_requested')
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_digital_stock(product_key: str, plan_key: Optional[str] = None) -> int:
    if product_key in INVITE_ONLY_PRODUCTS:
        return 999

    conn = db_connect()
    cur = conn.cursor()

    if plan_key:
        cur.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM digital_accounts
            WHERE product_key = ? AND plan_key = ? AND used = 0
            """,
            (product_key, plan_key),
        )
    else:
        cur.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM digital_accounts
            WHERE product_key = ? AND used = 0
            """,
            (product_key,),
        )

    count = cur.fetchone()["cnt"]
    conn.close()
    return int(count)


def reserve_account(product_key: str, plan_key: str, order_id: str) -> Optional[dict]:
    conn = db_connect()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            """
            SELECT id, email, password, extra
            FROM digital_accounts
            WHERE product_key = ? AND plan_key = ? AND used = 0
            ORDER BY id ASC
            LIMIT 1
            """,
            (product_key, plan_key),
        )
        row = cur.fetchone()

        if not row:
            conn.rollback()
            return None

        cur.execute(
            """
            UPDATE digital_accounts
            SET used = 1, order_id = ?
            WHERE id = ? AND used = 0
            """,
            (order_id, row["id"]),
        )

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
    cur.execute(
        """
        INSERT INTO digital_accounts (product_key, plan_key, email, password, extra, used, order_id)
        VALUES (?, ?, ?, ?, ?, 0, NULL)
        """,
        (product_key, plan_key, email, password, extra),
    )
    conn.commit()
    conn.close()


def get_game_stock(product_key: str) -> int:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT stock FROM game_products WHERE product_key = ?", (product_key,))
    row = cur.fetchone()
    conn.close()
    return int(row["stock"]) if row else 0


def set_game_stock(product_key: str, stock: int):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE game_products
        SET stock = ?, updated_at = ?
        WHERE product_key = ?
        """,
        (stock, now_str(), product_key),
    )
    conn.commit()
    conn.close()


def adjust_game_stock(product_key: str, delta: int) -> int:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT stock FROM game_products WHERE product_key = ?", (product_key,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return 0

    new_stock = max(0, int(row["stock"]) + delta)
    cur.execute(
        """
        UPDATE game_products
        SET stock = ?, updated_at = ?
        WHERE product_key = ?
        """,
        (new_stock, now_str(), product_key),
    )
    conn.commit()
    conn.close()
    return new_stock


def is_game_enabled(product_key: str) -> bool:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT enabled FROM game_products WHERE product_key = ?", (product_key,))
    row = cur.fetchone()
    conn.close()
    return bool(row["enabled"]) if row else False


def set_game_enabled(product_key: str, enabled: bool):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE game_products
        SET enabled = ?, updated_at = ?
        WHERE product_key = ?
        """,
        (1 if enabled else 0, now_str(), product_key),
    )
    conn.commit()
    conn.close()


def find_recent_duplicate_order(
    user_id: int,
    product_key: str,
    plan_key: str,
    price: int,
    screenshot_file_id: str,
) -> Optional[dict]:
    conn = db_connect()
    cur = conn.cursor()
    since = (now_dt() - timedelta(minutes=DUPLICATE_ORDER_WINDOW_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        SELECT * FROM orders
        WHERE user_id = ?
          AND created_at >= ?
          AND (
                screenshot_file_id = ?
                OR (
                    product_key = ?
                    AND plan_key = ?
                    AND price = ?
                    AND status IN (
                        'pending_payment_review',
                        'waiting_manual_delivery',
                        'approved',
                        'delivered',
                        'code_requested',
                        'code_sent'
                    )
                )
          )
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, since, screenshot_file_id, product_key, plan_key, price),
    )

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_stats_summary() -> dict:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cur.fetchone()["total_orders"]

    cur.execute(
        """
        SELECT COUNT(*) AS delivered_orders
        FROM orders
        WHERE status IN ('approved', 'delivered', 'code_sent')
        """
    )
    delivered_orders = cur.fetchone()["delivered_orders"]

    cur.execute(
        """
        SELECT COUNT(*) AS pending_orders
        FROM orders
        WHERE status IN ('pending_payment_review', 'waiting_manual_delivery', 'code_requested')
        """
    )
    pending_orders = cur.fetchone()["pending_orders"]

    cur.execute(
        """
        SELECT COUNT(*) AS rejected_orders
        FROM orders
        WHERE status = 'rejected'
        """
    )
    rejected_orders = cur.fetchone()["rejected_orders"]

    cur.execute(
        """
        SELECT COALESCE(SUM(price), 0) AS total_sales
        FROM orders
        WHERE status IN ('approved', 'delivered', 'code_sent')
        """
    )
    total_sales = cur.fetchone()["total_sales"]

    conn.close()

    return {
        "total_orders": int(total_orders),
        "delivered_orders": int(delivered_orders),
        "pending_orders": int(pending_orders),
        "rejected_orders": int(rejected_orders),
        "total_sales": int(total_sales),
    }


def get_sales_between(start_str: str, end_str: str) -> dict:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) AS total_orders, COALESCE(SUM(price), 0) AS total_sales
        FROM orders
        WHERE status IN ('approved', 'delivered', 'code_sent')
          AND created_at >= ?
          AND created_at <= ?
        """,
        (start_str, end_str),
    )
    row = cur.fetchone()
    conn.close()
    return {
        "total_orders": int(row["total_orders"]),
        "total_sales": int(row["total_sales"]),
    }


def get_order_logs(order_id: str, limit: int = 20) -> List[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM audit_logs
        WHERE order_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (order_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =========================================================
# UI HELPERS
# =========================================================

def glam_title(title: str) -> str:
    return f"<b>{escape(title)}</b>"


def glam_footer() -> str:
    return ""


def human_status(status: str) -> str:
    mapping = {
        "pending_payment_review": "⏳ Pending Review",
        "waiting_manual_delivery": "📦 Waiting Delivery",
        "approved": "✅ Approved",
        "delivered": "✅ Delivered",
        "code_requested": "🔐 Code Requested",
        "code_sent": "🔑 Code Sent",
        "rejected": "❌ Rejected",
    }
    return mapping.get(status, status)


def order_summary_text(order: dict) -> str:
    return (
        f"📋 <b>Order Summary</b>\n\n"
        f"🆔 <b>Order ID:</b> <code>{escape(order['order_id'])}</code>\n"
        f"🛍️ <b>Product:</b> {escape(order['product_name'])}\n"
        f"📦 <b>Plan:</b> {escape(order['plan_label'])}\n"
        f"💸 <b>Price:</b> {order['price']} Ks\n"
        f"📝 <b>Detail / Note:</b> {escape(order.get('detail') or '-')}\n"
        f"🏦 <b>Payment:</b> {escape(order.get('payment_name') or '-')}\n"
        f"📌 <b>Status:</b> {human_status(order['status'])}\n"
        f"🕒 <b>Created:</b> {escape(order['created_at'])}"
    )


def product_caption(product: dict, product_key: str) -> str:
    if product["category"] == "digital":
        if product_key in INVITE_ONLY_PRODUCTS:
            stock = "Unlimited"
            cheapest = min(v["price"] for v in product["plans"].values())
            price_text = f"From {cheapest} Ks"
            enabled = product.get("enabled", True)
            is_in_stock = enabled
        else:
            stock = get_digital_stock(product_key)
            cheapest = min(v["price"] for v in product["plans"].values())
            price_text = f"From {cheapest} Ks"
            enabled = product.get("enabled", True)
            is_in_stock = stock > 0 and enabled
    else:
        stock = get_game_stock(product_key)
        first_price = next(iter(product["plans"].values()))["price"]
        price_text = f"{first_price} Ks"
        enabled = is_game_enabled(product_key)
        is_in_stock = stock > 0 and enabled

    status = "🟢 Available" if is_in_stock else "🔴 Out of Stock"

    return (
        f"🔥 <b>{escape(product['full_name'])}</b>\n\n"
        f"💰 <b>Price:</b> {escape(price_text)}\n"
        f"📦 <b>Stock:</b> {stock}\n"
        f"📌 <b>Status:</b> {status}\n\n"
        f"📝 <b>Description</b>\n"
        f"{escape(product['description'])}\n\n"
        f"⚡ Fast Service\n"
        f"🔐 Secure Payment\n"
        f"💎 Trusted Seller"
    )


def payment_text(payment_name: str, account: str, amount: int) -> str:
    return (
        f"💳 <b>Payment Info</b>\n\n"
        f"🏦 <b>Method:</b> {escape(payment_name)}\n\n"
        f"<pre>{escape(account)}</pre>\n"
        f"💸 <b>Amount:</b> {amount} Ks\n\n"
        f"📷 ငွေလွှဲပြီး payment screenshot ကို <b>photo</b> နဲ့ပို့ပေးပါ\n"
        f"✅ ပြီးတာနဲ့ admin review တင်ပေးပါမယ်"
    )


def welcome_text() -> str:
    return (
        f"🎉 <b>Welcome to {escape(SHOP_NAME)}</b>\n\n"
        f"🎮 Game Top Up\n"
        f"💻 Digital Products\n"
        f"⚡ Fast Delivery\n"
        f"🔐 Safe Payment\n"
        f"💎 Premium Service\n\n"
        f"👇 <b>Please choose from the menu below</b>"
    )


def category_text() -> str:
    return (
        f"🗂 <b>Shop Categories</b>\n\n"
        f"စိတ်ကြိုက် category ကိုရွေးပေးပါ 👇"
    )


def products_text(category_key: str) -> str:
    if category_key == "game":
        return (
            f"🎮 <b>Game Products</b>\n\n"
            f"ဝယ်ယူချင်တဲ့ game item ကိုရွေးပေးပါ 👇"
        )
    return (
        f"💻 <b>Digital Products</b>\n\n"
        f"ဝယ်ယူချင်တဲ့ product ကိုရွေးပေးပါ 👇"
    )


def plan_text(product_key: str) -> str:
    return product_caption(PRODUCTS[product_key], product_key) + "\n\n🛒 <b>Please choose a plan</b>"


def detail_text(product_key: str) -> str:
    product = PRODUCTS[product_key]
    return (
        f"📝 <b>Detail / Note</b>\n\n"
        f"{product['requires_detail_label']}\n\n"
        f"စာရိုက်ပို့လို့ရပါတယ်\n"
        f"မလိုရင် button ကိုနှိပ်လို့ရပါတယ် 👇"
    )


async def safe_edit_message(query, text: str, reply_markup=None):
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception:
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning("safe_edit_message failed: %s", e)


async def disable_query_buttons(query):
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass


async def send_or_edit_product_card(query, product_key: str, reply_markup=None):
    caption = plan_text(product_key)
    await safe_edit_message(query, caption, reply_markup=reply_markup)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛍 Shop Now", callback_data="menu_shop")],
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
            [
                InlineKeyboardButton("📦 My Orders", callback_data="menu_myorders"),
                InlineKeyboardButton("📞 Contact Admin", callback_data="menu_contact"),
            ],
            [InlineKeyboardButton("🔄 Refresh", callback_data="menu_restart")],
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
            if not product.get("enabled", True):
                continue

            cheapest = min(v["price"] for v in product["plans"].values())

            if key in INVITE_ONLY_PRODUCTS:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"✨ {product['name']} • {cheapest} Ks",
                            callback_data=f"product:{key}",
                        )
                    ]
                )
                continue

            total_stock = get_digital_stock(key)

            if total_stock > 0:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🟢 {product['name']} • From {cheapest} Ks",
                            callback_data=f"product:{key}",
                        )
                    ]
                )
            else:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🔴 {product['name']} • Out of Stock",
                            callback_data="out_of_stock",
                        )
                    ]
                )
        else:
            if not is_game_enabled(key):
                continue

            stock = get_game_stock(key)
            default_price = next(iter(product["plans"].values()))["price"]

            if stock > 0:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🟢 {product['name']} • {default_price} Ks",
                            callback_data=f"product:{key}",
                        )
                    ]
                )
            else:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🔴 {product['name']} • Out of Stock",
                            callback_data="out_of_stock",
                        )
                    ]
                )

    rows.append([InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_categories")])
    return InlineKeyboardMarkup(rows)


def plans_keyboard(product_key: str) -> InlineKeyboardMarkup:
    rows = []
    product = PRODUCTS[product_key]

    for plan_key, plan in product["plans"].items():
        if product["category"] == "digital":
            if not product.get("enabled", True):
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🔴 {plan['label']} • Disabled",
                            callback_data="out_of_stock",
                        )
                    ]
                )
                continue

            if product_key in INVITE_ONLY_PRODUCTS:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"✨ {plan['label']} • {plan['price']} Ks",
                            callback_data=f"plan:{plan_key}",
                        )
                    ]
                )
                continue

            stock = get_digital_stock(product_key, plan_key)
            if stock > 0:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"💠 {plan['label']} • {plan['price']} Ks",
                            callback_data=f"plan:{plan_key}",
                        )
                    ]
                )
            else:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🔴 {plan['label']} • Out of Stock",
                            callback_data="out_of_stock",
                        )
                    ]
                )
        else:
            if not is_game_enabled(product_key):
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🔴 {plan['label']} • Disabled",
                            callback_data="out_of_stock",
                        )
                    ]
                )
                continue

            stock = get_game_stock(product_key)
            if stock > 0:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"💠 {plan['label']} • {plan['price']} Ks",
                            callback_data=f"plan:{plan_key}",
                        )
                    ]
                )
            else:
                rows.append(
                    [
                        InlineKeyboardButton(
                            f"🔴 {plan['label']} • Out of Stock",
                            callback_data="out_of_stock",
                        )
                    ]
                )

    rows.append([InlineKeyboardButton("⬅️ Back to Products", callback_data="back_products")])
    return InlineKeyboardMarkup(rows)


def detail_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏭ Skip / No Note", callback_data="detail_skip")],
            [
                InlineKeyboardButton("⬅️ Back to Plans", callback_data="detail_back_plan"),
                InlineKeyboardButton("❌ Cancel", callback_data="detail_cancel"),
            ],
        ]
    )


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💙 KPay", callback_data="pay:kpay")],
            [InlineKeyboardButton("💛 Wave Pay", callback_data="pay:wave")],
            [InlineKeyboardButton("❤️ AYA Pay", callback_data="pay:aya")],
            [InlineKeyboardButton("💚 UAB Pay", callback_data="pay:uab")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_plan")],
        ]
    )


def payment_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬅️ Back to Payment", callback_data="back_payment_methods")],
            [InlineKeyboardButton("⬅️ Back to Plans", callback_data="back_plan")],
        ]
    )


def simple_back_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data="back_main")]]
    )


def my_orders_keyboard(rows: List[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for o in rows:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"📦 {o['plan_label']} • {human_status(o['status'])}",
                    callback_data=f"track:{o['order_id']}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="menu_myorders")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def admin_action_keyboard(order_id: str, category: str, product_key: str = "") -> InlineKeyboardMarkup:
    if category == "digital":
        if product_key in INVITE_ONLY_PRODUCTS:
            return InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("📧 Invite Check", callback_data=f"auto:{order_id}"),
                        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{order_id}"),
                    ],
                    [InlineKeyboardButton("❌ Reject Order", callback_data=f"rejectmenu:{order_id}")],
                ]
            )

        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⚡ Auto Deliver", callback_data=f"auto:{order_id}"),
                    InlineKeyboardButton("✍️ Manual Deliver", callback_data=f"manual:{order_id}"),
                ],
                [InlineKeyboardButton("❌ Reject Order", callback_data=f"rejectmenu:{order_id}")],
            ]
        )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{order_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"rejectmenu:{order_id}"),
            ]
        ]
    )


def reject_reason_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💸 ငွေပမာဏမမှန်", callback_data=f"reject:{order_id}:wrong_amount")],
            [InlineKeyboardButton("🖼 Screenshot မရှင်း", callback_data=f"reject:{order_id}:unclear_ss")],
            [InlineKeyboardButton("🚫 Payment မအောင်မြင်", callback_data=f"reject:{order_id}:fake_payment")],
            [InlineKeyboardButton("♻️ Duplicate Order", callback_data=f"reject:{order_id}:duplicate_order")],
            [InlineKeyboardButton("📝 Other", callback_data=f"reject:{order_id}:other")],
        ]
    )


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


async def maybe_send_low_stock_alert(bot, product_key: str, plan_key: Optional[str] = None):
    try:
        product = PRODUCTS.get(product_key)
        if not product:
            return

        if product["category"] == "digital":
            if product_key in INVITE_ONLY_PRODUCTS:
                return

            current_stock = get_digital_stock(product_key, plan_key)
            if current_stock <= LOW_STOCK_THRESHOLD:
                plan_label = "All Plans"
                if plan_key and plan_key in product["plans"]:
                    plan_label = product["plans"][plan_key]["label"]

                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"⚠️ <b>Low Stock Alert</b>\n\n"
                        f"🛍️ <b>Product:</b> {escape(product['full_name'])}\n"
                        f"📦 <b>Plan:</b> {escape(plan_label)}\n"
                        f"📉 <b>Remaining:</b> {current_stock}"
                    ),
                    parse_mode=ParseMode.HTML,
                )
        else:
            current_stock = get_game_stock(product_key)
            if current_stock <= LOW_STOCK_THRESHOLD:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"⚠️ <b>Low Stock Alert</b>\n\n"
                        f"🛍️ <b>Product:</b> {escape(product['full_name'])}\n"
                        f"📉 <b>Remaining:</b> {current_stock}"
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
            disable_web_page_preview=True,
        )
    return MENU_STATE


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_shop":
        await safe_edit_message(query, category_text(), reply_markup=category_keyboard())
        return CATEGORY_STATE

    if data == "menu_myorders":
        rows = get_user_orders(query.from_user.id, limit=10)
        if not rows:
            await safe_edit_message(
                query,
                "📦 <b>Your Orders</b>\n\nသင့် order history မရှိသေးပါ။",
                reply_markup=simple_back_main_keyboard(),
            )
            return MENU_STATE

        await safe_edit_message(
            query,
            "📦 <b>Your Orders</b>\n\nကိုယ်ဝယ်ထားတဲ့ order တွေကိုအောက်မှာပြန်ကြည့်နိုင်ပါတယ် 👇",
            reply_markup=my_orders_keyboard(rows),
        )
        return MENU_STATE

    if data == "menu_contact":
        await safe_edit_message(
            query,
            f"📞 <b>Contact Admin</b>\n\n👤 Telegram: {escape(CONTACT_USERNAME)}",
            reply_markup=simple_back_main_keyboard(),
        )
        return MENU_STATE

    if data == "menu_restart":
        context.user_data.clear()
        await safe_edit_message(query, welcome_text(), reply_markup=main_menu_keyboard())
        return MENU_STATE

    return MENU_STATE


async def track_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":", 1)[1]
    order = order_get(order_id)

    if not order:
        await query.answer("Order not found", show_alert=True)
        return MENU_STATE

    if query.from_user.id != ADMIN_ID and order["user_id"] != query.from_user.id:
        await query.answer("Not allowed", show_alert=True)
        return MENU_STATE

    await safe_edit_message(query, order_summary_text(order), reply_markup=simple_back_main_keyboard())
    return MENU_STATE


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        context.user_data.clear()
        await safe_edit_message(query, welcome_text(), reply_markup=main_menu_keyboard())
        return MENU_STATE

    if data.startswith("cat:"):
        category_key = data.split(":", 1)[1]
        context.user_data["category_key"] = category_key
        await safe_edit_message(
            query,
            products_text(category_key),
            reply_markup=products_keyboard(category_key),
        )
        return PRODUCT_STATE

    return CATEGORY_STATE


async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_categories":
        await safe_edit_message(query, category_text(), reply_markup=category_keyboard())
        return CATEGORY_STATE

    if data == "out_of_stock":
        await query.answer("🔴 This item is out of stock.", show_alert=True)
        return PRODUCT_STATE

    if data.startswith("product:"):
        product_key = data.split(":", 1)[1]
        if product_key not in PRODUCTS:
            await query.answer("❌ Invalid product.", show_alert=True)
            return PRODUCT_STATE

        product = PRODUCTS[product_key]
        context.user_data["product_key"] = product_key
        context.user_data["product_name"] = product["full_name"]
        context.user_data["category"] = product["category"]

        await send_or_edit_product_card(query, product_key, reply_markup=plans_keyboard(product_key))
        return PLAN_STATE

    return PRODUCT_STATE


async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_products":
        category_key = context.user_data.get("category_key", "game")
        await safe_edit_message(
            query,
            products_text(category_key),
            reply_markup=products_keyboard(category_key),
        )
        return PRODUCT_STATE

    if data == "out_of_stock":
        await query.answer("🔴 This plan is out of stock.", show_alert=True)
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
            await query.answer("❌ Invalid plan.", show_alert=True)
            return PLAN_STATE

        plan = product["plans"][plan_key]

        if product["category"] == "digital":
            if not product.get("enabled", True):
                await query.answer("🔴 ဒီ plan က မရနိုင်သေးပါ။", show_alert=True)
                return PLAN_STATE

            if product_key not in INVITE_ONLY_PRODUCTS and get_digital_stock(product_key, plan_key) <= 0:
                await query.answer("🔴 ဒီ plan က stock မရှိတော့ပါ။", show_alert=True)
                return PLAN_STATE
        else:
            if not is_game_enabled(product_key) or get_game_stock(product_key) <= 0:
                await query.answer("🔴 ဒီ item က stock မရှိတော့ပါ။", show_alert=True)
                return PLAN_STATE

        context.user_data["plan_key"] = plan_key
        context.user_data["plan_label"] = plan["label"]
        context.user_data["price"] = int(plan["price"])

        await query.message.reply_text(
            detail_text(product_key),
            parse_mode=ParseMode.HTML,
            reply_markup=detail_keyboard(),
            disable_web_page_preview=True,
        )
        return DETAIL_STATE

    return PLAN_STATE


async def detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return DETAIL_STATE

    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Detail / note ပို့ပေးပါ။", reply_markup=detail_keyboard())
        return DETAIL_STATE

    product_key = context.user_data.get("product_key")

    if product_key in {"gemini_ai_pro", "canva_pro_edu"} and text.lower() == "no":
        await update.message.reply_text("❌ ဒီ product အတွက် mail မဖြစ်မနေလိုပါတယ်။")
        return DETAIL_STATE

    context.user_data["detail"] = text

    await update.message.reply_text(
        "💳 <b>Payment Method</b>\n\nငွေပေးချေမယ့် method ကိုရွေးပေးပါ 👇",
        reply_markup=payment_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    return PAYMENT_STATE


async def detail_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "detail_skip":
        product_key = context.user_data.get("product_key")

        if product_key == "gemini_ai_pro":
            await query.answer("Gemini အတွက် mail မဖြစ်မနေလိုပါတယ်။", show_alert=True)
            return DETAIL_STATE

        if product_key == "canva_pro_edu":
            await query.answer("Canva အတွက် mail ပို့ပေးပါ။", show_alert=True)
            return DETAIL_STATE

        context.user_data["detail"] = "No"
        await safe_edit_message(
            query,
            "💳 <b>Payment Method</b>\n\nငွေပေးချေမယ့် method ကိုရွေးပေးပါ 👇",
            reply_markup=payment_keyboard(),
        )
        return PAYMENT_STATE

    if data == "detail_back_plan":
        product_key = context.user_data.get("product_key")
        if not product_key:
            context.user_data.clear()
            await safe_edit_message(query, welcome_text(), reply_markup=main_menu_keyboard())
            return MENU_STATE

        await send_or_edit_product_card(query, product_key, reply_markup=plans_keyboard(product_key))
        return PLAN_STATE

    if data == "detail_cancel":
        context.user_data.clear()
        await safe_edit_message(
            query,
            "❌ <b>Order Cancelled</b>\n\nYour current order has been cancelled.",
            reply_markup=main_menu_keyboard(),
        )
        return MENU_STATE

    return DETAIL_STATE


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_plan":
        product_key = context.user_data.get("product_key")
        if not product_key:
            await query.message.reply_text("❌ Session error. /start နဲ့ပြန်စပါ။")
            return ConversationHandler.END

        await send_or_edit_product_card(query, product_key, reply_markup=plans_keyboard(product_key))
        return PLAN_STATE

    if data == "back_payment_methods":
        await safe_edit_message(
            query,
            "💳 <b>Payment Method</b>\n\nငွေပေးချေမယ့် method ကိုရွေးပေးပါ 👇",
            reply_markup=payment_keyboard(),
        )
        return PAYMENT_STATE

    if not data.startswith("pay:"):
        return PAYMENT_STATE

    payment_key = data.split(":", 1)[1]
    if payment_key not in PAYMENT_ACCOUNTS:
        await query.answer("❌ Invalid payment method.", show_alert=True)
        return PAYMENT_STATE

    context.user_data["payment_key"] = payment_key
    context.user_data["payment_name"] = PAYMENT_ACCOUNTS[payment_key]["label"]

    await safe_edit_message(
        query,
        payment_text(
            PAYMENT_ACCOUNTS[payment_key]["label"],
            PAYMENT_ACCOUNTS[payment_key]["text"],
            int(context.user_data["price"]),
        ),
        reply_markup=payment_back_keyboard(),
    )
    return SCREENSHOT_STATE


async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        if update.message:
            await update.message.reply_text(
                "📷 <b>Upload Screenshot</b>\n\nPayment screenshot ကို <b>photo</b> နဲ့ပို့ပေးပါ။",
                parse_mode=ParseMode.HTML,
            )
        return SCREENSHOT_STATE

    required_keys = [
        "product_key",
        "product_name",
        "plan_key",
        "plan_label",
        "category",
        "price",
        "payment_key",
        "payment_name",
    ]

    if any(k not in context.user_data for k in required_keys):
        await update.message.reply_text("❌ Session expired. /start နဲ့ပြန်စပါ။")
        context.user_data.clear()
        return ConversationHandler.END

    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id

    duplicate = find_recent_duplicate_order(
        user_id=user.id,
        product_key=context.user_data["product_key"],
        plan_key=context.user_data["plan_key"],
        price=int(context.user_data["price"]),
        screenshot_file_id=photo_file_id,
    )

    if duplicate:
        await update.message.reply_text(
            f"❌ <b>Duplicate Order Detected</b>\n\n"
            f"🆔 Existing Order: <code>{escape(duplicate['order_id'])}</code>\n"
            f"📌 Status: {human_status(duplicate['status'])}",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
        )
        context.user_data.clear()
        return MENU_STATE

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
        f"🆕 <b>New Order Received</b>\n\n"
        f"{order_summary_text(data)}\n\n"
        f"👤 <b>Customer:</b> {escape(data['full_name'])}\n"
        f"🔗 <b>Username:</b> {escape(data['username'] or '-')}\n"
        f"🪪 <b>User ID:</b> <code>{data['user_id']}</code>"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=admin_caption,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_action_keyboard(order_id, data["category"], data["product_key"]),
    )

    await send_optional_bot_sticker(context.bot, user.id, SUCCESS_STICKER_ID)

    await update.message.reply_text(
        f"✅ <b>Order Received Successfully</b>\n\n"
        f"{order_summary_text(data)}\n\n"
        f"⏳ Admin review ပြီးတာနဲ့ result ပြန်ပို့ပေးပါမယ်",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )

    context.user_data.clear()
    return MENU_STATE


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

    if raw.startswith("rejectmenu:"):
        order_id = raw.split(":", 1)[1]
        await query.message.reply_text(
            f"❌ <b>Reject Reason</b>\n\n🆔 <code>{escape(order_id)}</code>\nReason ရွေးပေးပါ",
            parse_mode=ParseMode.HTML,
            reply_markup=reject_reason_keyboard(order_id),
        )
        return

    if raw.startswith("reject:"):
        try:
            _, order_id, reason_key = raw.split(":", 2)
        except ValueError:
            return

        order = order_get(order_id)
        if not order:
            return

        if order["status"] not in ["pending_payment_review", "waiting_manual_delivery", "code_requested"]:
            await query.answer("Already processed!", show_alert=True)
            return

        reason_text = REJECT_REASONS.get(reason_key, "Order rejected")
        order_update_status(order_id, "rejected", reason_text)
        log_action(order_id, query.from_user.id, "rejected", reason_text)
        await disable_query_buttons(query)

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"❌ <b>Order Rejected</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"📌 <b>Reason:</b> {escape(reason_text)}"
            ),
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"❌ <b>Order Rejected</b>\n\n🆔 <code>{escape(order_id)}</code>\n📌 {escape(reason_text)}",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        action, order_id = raw.split(":", 1)
    except ValueError:
        return

    order = order_get(order_id)
    if not order:
        return

    if action == "approve":
        if order["status"] not in ["pending_payment_review", "waiting_manual_delivery", "code_requested"]:
            await query.answer("Already processed!", show_alert=True)
            return

        if order["product_key"] in INVITE_ONLY_PRODUCTS:
            product_label = "Canva Pro Edu" if order["product_key"] == "canva_pro_edu" else "Gemini Ai Pro"

            order_update_status(order_id, "approved", "Invite completed")
            log_action(order_id, query.from_user.id, "invite_approved")
            await disable_query_buttons(query)

            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    f"✅ <b>Invite Ready</b>\n\n"
                    f"Your {escape(product_label)} access is ready.\n"
                    f"📧 Invite already sent to your email"
                ),
                parse_mode=ParseMode.HTML,
            )

            await query.message.reply_text(
                f"✅ <b>Invite Approved</b>\n\n🆔 <code>{escape(order_id)}</code>\nInvite completed",
                parse_mode=ParseMode.HTML,
            )
            return

        product = PRODUCTS.get(order["product_key"])
        if not product or order["category"] != "game":
            return

        current_stock = get_game_stock(order["product_key"])
        if current_stock <= 0:
            await query.message.reply_text("❌ Stock မရှိတော့ပါ။")
            return

        new_stock = adjust_game_stock(order["product_key"], -1)
        order_update_status(order_id, "approved", "Game order approved")
        log_action(order_id, query.from_user.id, "approved_game")
        await disable_query_buttons(query)

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"✅ <b>Order Approved</b>\n\n"
                f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"🛍️ <b>Product:</b> {escape(order.get('product_name', '-'))}\n"
                f"💖 Thanks for using Gamepay Hub"
            ),
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"✅ <b>Approved</b>\n\n🆔 <code>{escape(order_id)}</code>\n📦 Remaining Stock: {new_stock}",
            parse_mode=ParseMode.HTML,
        )

        await maybe_send_low_stock_alert(context.bot, order["product_key"])
        return

    if action == "auto":
        if order["status"] != "pending_payment_review":
            await query.answer("Already processed!", show_alert=True)
            return

        if order["category"] != "digital":
            return

        if order["product_key"] in INVITE_ONLY_PRODUCTS:
            user_mail = (order.get("detail") or "").strip()

            if not user_mail or user_mail.lower() == "no":
                await query.message.reply_text("❌ User mail မရှိသေးပါ။ Customer ဆီက mail တောင်းပေးပါ။")
                return

            await disable_query_buttons(query)

            product_label = "Canva Pro Edu" if order["product_key"] == "canva_pro_edu" else "Gemini Ai Pro"

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📧 <b>Invite Required</b>\n\n"
                    f"🆔 <code>{escape(order_id)}</code>\n"
                    f"🛍️ <b>Product:</b> {escape(product_label)}\n"
                    f"📧 <b>User Mail:</b> <code>{escape(user_mail)}</code>\n\n"
                    f"Invite ပို့ပြီးရင် original order message က Approve ကိုနှိပ်ပါ"
                ),
                parse_mode=ParseMode.HTML,
            )

            await query.message.reply_text(
                f"📧 <b>Invite Required</b>\n\n🆔 <code>{escape(order_id)}</code>\nInvite ပို့ပြီးမှ Approve နှိပ်ပါ",
                parse_mode=ParseMode.HTML,
            )
            return

        product_cfg = DIGITAL_INVENTORY.get(order["product_key"], {})

        if not bool(product_cfg.get("auto_delivery", False)):
            order_update_status(order_id, "waiting_manual_delivery", "Manual only product")
            log_action(order_id, query.from_user.id, "manual_required", "Manual only product")
            await disable_query_buttons(query)

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"✍️ <b>Manual Delivery Required</b>\n\n<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        account = reserve_account(order["product_key"], order["plan_key"], order_id)
        if not account:
            order_update_status(order_id, "waiting_manual_delivery", "Auto stock not found")
            log_action(order_id, query.from_user.id, "auto_stock_not_found")
            await disable_query_buttons(query)

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ <b>Auto Stock Not Found</b>\n\n<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        order_update_status(order_id, "delivered", "Auto delivered")
        log_action(order_id, query.from_user.id, "auto_delivered")
        await disable_query_buttons(query)

        delivery_text = (
            f"✅ <b>Account Ready</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"📧 <b>Email:</b> <code>{escape(account['email'])}</code>\n"
            f"🔑 <b>Password:</b> <code>{escape(account['password'])}</code>\n"
        )

        if account["extra"]:
            delivery_text += f"\n📝 <b>Note:</b> {escape(account['extra'])}\n"

        delivery_text += "\n🔐 Login code လိုရင် <code>Code</code> လို့ရိုက်ပို့နိုင်ပါတယ်။"

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=delivery_text,
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"✅ <b>Auto Delivered</b>\n\n🆔 <code>{escape(order_id)}</code>",
            parse_mode=ParseMode.HTML,
        )

        await maybe_send_low_stock_alert(context.bot, order["product_key"], order["plan_key"])
        return

    if action == "manual":
        if order["status"] != "pending_payment_review":
            await query.answer("Already processed!", show_alert=True)
            return

        if order["category"] != "digital":
            return

        order_update_status(order_id, "waiting_manual_delivery", "Waiting admin manual delivery")
        log_action(order_id, query.from_user.id, "manual_selected")
        await disable_query_buttons(query)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✍️ <b>Manual Delivery Selected</b>\n\n<code>/deliver {escape(order_id)} Email: yourmail@gmail.com Password: 123456</code>",
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

    if order["status"] not in ["pending_payment_review", "waiting_manual_delivery", "code_requested"]:
        await update.message.reply_text("❌ Already processed.")
        return

    await context.bot.send_message(
        chat_id=order["user_id"],
        text=(
            f"✅ <b>Account Ready</b>\n\n"
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
            f"🔐 <b>Login Code Ready</b>\n\n"
            f"🆔 <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"🔢 <b>Code:</b> <code>{escape(code_value)}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )

    order_update_status(order_id, "code_sent", "Admin sent login code")
    log_action(order_id, update.effective_user.id, "code_sent", code_value)
    await update.message.reply_text("✅ Login code ပို့ပြီးပါပြီ။")


async def delete_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/delete_account email@example.com")
        return

    email = context.args[0].strip()

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM digital_accounts WHERE email = ? AND used = 0", (email,))
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
        await update.message.reply_text("Usage:\n/remove_game_stock PRODUCT_KEY QTY")
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

    current_stock = get_game_stock(product_key)
    if qty > current_stock:
        await update.message.reply_text(f"❌ Current stock = {current_stock} only.")
        return

    new_stock = adjust_game_stock(product_key, -qty)
    log_action(None, update.effective_user.id, "remove_game_stock", f"{product_key} -{qty}")

    await update.message.reply_text(
        f"📦 <b>Game Stock Reduced</b>\n\n"
        f"🛍️ <b>Product:</b> {escape(PRODUCTS[product_key]['full_name'])}\n"
        f"➖ <b>Removed:</b> {qty}\n"
        f"📦 <b>Remaining:</b> {new_stock}",
        parse_mode=ParseMode.HTML,
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    rows = get_pending_orders(limit=20)
    if not rows:
        await update.message.reply_text("✅ Pending orders မရှိပါ။")
        return

    lines = ["📋 <b>Pending Orders</b>"]
    for o in rows:
        lines.append(
            f"\n🆔 <code>{escape(o['order_id'])}</code>\n"
            f"🛍️ {escape(o['product_name'])}\n"
            f"📦 {escape(o['plan_label'])}\n"
            f"👤 {escape(o['full_name'])}\n"
            f"📌 {human_status(o['status'])}"
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


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /logs ORDER_ID")
        return

    order_id = context.args[0]
    logs = get_order_logs(order_id)

    if not logs:
        await update.message.reply_text("❌ No logs found.")
        return

    lines = [f"🧾 <b>Order Logs</b>\n🆔 <code>{escape(order_id)}</code>\n"]
    for item in logs:
        lines.append(
            f"\n🕒 <b>{escape(item['created_at'])}</b>\n"
            f"👤 Actor ID: <code>{item['actor_id']}</code>\n"
            f"⚙️ Action: {escape(item['action'])}\n"
            f"📝 Note: {escape(item.get('note') or '-')}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    stats = get_stats_summary()
    await update.message.reply_text(
        f"📊 <b>Bot Statistics</b>\n\n"
        f"📦 <b>Total Orders:</b> {stats['total_orders']}\n"
        f"✅ <b>Delivered / Approved:</b> {stats['delivered_orders']}\n"
        f"⏳ <b>Pending:</b> {stats['pending_orders']}\n"
        f"❌ <b>Rejected:</b> {stats['rejected_orders']}\n"
        f"💰 <b>Total Sales:</b> {stats['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )


async def sales_today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    start = now_dt().replace(hour=0, minute=0, second=0, microsecond=0)
    end = now_dt().replace(hour=23, minute=59, second=59, microsecond=0)
    result = get_sales_between(start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))

    await update.message.reply_text(
        f"📅 <b>Sales Today</b>\n\n"
        f"📦 <b>Orders:</b> {result['total_orders']}\n"
        f"💰 <b>Total Sales:</b> {result['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )


async def sales_week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    start = now_dt() - timedelta(days=7)
    end = now_dt()
    result = get_sales_between(start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))

    await update.message.reply_text(
        f"📆 <b>Sales Last 7 Days</b>\n\n"
        f"📦 <b>Orders:</b> {result['total_orders']}\n"
        f"💰 <b>Total Sales:</b> {result['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )


async def sales_month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    start = now_dt() - timedelta(days=30)
    end = now_dt()
    result = get_sales_between(start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))

    await update.message.reply_text(
        f"🗓 <b>Sales Last 30 Days</b>\n\n"
        f"📦 <b>Orders:</b> {result['total_orders']}\n"
        f"💰 <b>Total Sales:</b> {result['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    lines = ["📦 <b>Stock List</b>"]
    for key, p in PRODUCTS.items():
        if p["category"] == "digital":
            if key in INVITE_ONLY_PRODUCTS:
                lines.append(f"💻 <b>{escape(p['name'])}</b> → Invite Flow")
            else:
                lines.append(f"💻 <b>{escape(p['name'])}</b> → {get_digital_stock(key)}")
        else:
            lines.append(f"🎮 <b>{escape(p['name'])}</b> → {get_game_stock(key)}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def lowstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    lines = ["⚠️ <b>Low Stock Items</b>"]
    found = False

    for key, p in PRODUCTS.items():
        if p["category"] == "digital":
            if key in INVITE_ONLY_PRODUCTS:
                continue
            total = get_digital_stock(key)
            if total <= LOW_STOCK_THRESHOLD:
                found = True
                lines.append(f"💻 <b>{escape(p['name'])}</b> → {total}")
        else:
            total = get_game_stock(key)
            if total <= LOW_STOCK_THRESHOLD:
                found = True
                lines.append(f"🎮 <b>{escape(p['name'])}</b> → {total}")

    if not found:
        lines.append("✅ Low stock item မရှိပါ။")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def outofstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    lines = ["❌ <b>Out of Stock Items</b>"]
    found = False

    for key, p in PRODUCTS.items():
        if p["category"] == "digital":
            if key in INVITE_ONLY_PRODUCTS:
                continue
            total = get_digital_stock(key)
            if total <= 0:
                found = True
                lines.append(f"💻 <b>{escape(p['name'])}</b> → 0")
        else:
            total = get_game_stock(key)
            if total <= 0:
                found = True
                lines.append(f"🎮 <b>{escape(p['name'])}</b> → 0")

    if not found:
        lines.append("✅ Out of stock item မရှိပါ။")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def add_game_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage:\n/add_game_stock PRODUCT_KEY QTY")
        return

    product_key = context.args[0]

    try:
        qty = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ QTY must be a number.")
        return

    if product_key in PRODUCTS and PRODUCTS[product_key]["category"] == "game":
        new_stock = adjust_game_stock(product_key, qty)
        log_action(None, update.effective_user.id, "add_game_stock", f"{product_key} +{qty}")
        await update.message.reply_text(
            f"📦 <b>Game Stock Updated</b>\n\n"
            f"🛍️ <b>Product:</b> {escape(PRODUCTS[product_key]['full_name'])}\n"
            f"➕ <b>Added:</b> {qty}\n"
            f"📦 <b>Current Stock:</b> {new_stock}",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text("❌ Invalid game product.")


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
    log_action(None, update.effective_user.id, "add_account", f"{product_key}/{plan_key}/{email}")
    await update.message.reply_text("✅ Digital account added.")


async def disable_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/disable_game PRODUCT_KEY")
        return

    product_key = context.args[0].strip()
    if product_key not in PRODUCTS or PRODUCTS[product_key]["category"] != "game":
        await update.message.reply_text("❌ Invalid game product.")
        return

    set_game_enabled(product_key, False)
    log_action(None, update.effective_user.id, "disable_game", product_key)
    await update.message.reply_text("✅ Game product disabled.")


async def enable_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/enable_game PRODUCT_KEY")
        return

    product_key = context.args[0].strip()
    if product_key not in PRODUCTS or PRODUCTS[product_key]["category"] != "game":
        await update.message.reply_text("❌ Invalid game product.")
        return

    set_game_enabled(product_key, True)
    log_action(None, update.effective_user.id, "enable_game", product_key)
    await update.message.reply_text("✅ Game product enabled.")


async def addstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(
            "/add_game_stock PRODUCT_KEY QTY\n"
            "/remove_game_stock PRODUCT_KEY QTY\n"
            "/add_account PRODUCT_KEY PLAN_KEY EMAIL PASSWORD | EXTRA\n"
            "/disable_game PRODUCT_KEY\n"
            "/enable_game PRODUCT_KEY"
        )


async def myorders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_user_orders(update.effective_user.id, limit=10)
    if not rows:
        await update.message.reply_text("📦 သင့် order history မရှိသေးပါ။")
        return

    lines = ["📦 <b>Your Recent Orders</b>"]
    for o in rows:
        lines.append(
            f"\n🆔 <code>{escape(o['order_id'])}</code>\n"
            f"🛍️ {escape(o['product_name'])}\n"
            f"📦 {escape(o['plan_label'])}\n"
            f"📌 {human_status(o['status'])}"
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
    cur.execute(
        """
        SELECT * FROM orders
        WHERE user_id = ?
          AND category = 'digital'
          AND status IN ('delivered', 'code_requested', 'code_sent')
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (update.effective_user.id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("❌ Active digital order မတွေ့ပါ။")
        return

    order = dict(row)
    order_update_status(order["order_id"], "code_requested", "Customer requested login code")
    log_action(order["order_id"], update.effective_user.id, "customer_code_request")

    await update.message.reply_text("⏳ Code request ကို admin ဆီပို့ပြီးပါပြီ။")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔐 <b>Code Requested</b>\n\n<code>/code {escape(order['order_id'])} 123456</code>",
        parse_mode=ParseMode.HTML,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.message:
        await update.message.reply_text(
            "❌ <b>Order Cancelled</b>\n\nCurrent order cancelled.",
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
                CallbackQueryHandler(track_callback_handler, pattern=r"^track:"),
                CallbackQueryHandler(category_handler, pattern=r"^back_main$"),
            ],
            CATEGORY_STATE: [
                CallbackQueryHandler(category_handler, pattern=r"^(cat:|back_main$)")
            ],
            PRODUCT_STATE: [
                CallbackQueryHandler(product_handler, pattern=r"^(product:|back_categories$|out_of_stock$)")
            ],
            PLAN_STATE: [
                CallbackQueryHandler(plan_handler, pattern=r"^(plan:|back_products$|out_of_stock$)")
            ],
            DETAIL_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, detail_handler),
                CallbackQueryHandler(detail_callback_handler, pattern=r"^(detail_skip$|detail_back_plan$|detail_cancel$)"),
            ],
            PAYMENT_STATE: [
                CallbackQueryHandler(payment_handler, pattern=r"^(pay:|back_plan$|back_payment_methods$)")
            ],
            SCREENSHOT_STATE: [
                MessageHandler(filters.PHOTO, screenshot_handler),
                CallbackQueryHandler(payment_handler, pattern=r"^(back_plan$|back_payment_methods$)"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    application.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern=r"^(approve:|auto:|manual:|rejectmenu:|reject:)",
        )
    )

    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("myorders", myorders_command))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("deliver", deliver_command))
    application.add_handler(CommandHandler("orders", orders_command))
    application.add_handler(CommandHandler("order", order_command))
    application.add_handler(CommandHandler("logs", logs_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("lowstock", lowstock_command))
    application.add_handler(CommandHandler("outofstock", outofstock_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("sales_today", sales_today_command))
    application.add_handler(CommandHandler("sales_week", sales_week_command))
    application.add_handler(CommandHandler("sales_month", sales_month_command))
    application.add_handler(CommandHandler("addstock", addstock_command))
    application.add_handler(CommandHandler("add_game_stock", add_game_stock_command))
    application.add_handler(CommandHandler("remove_game_stock", remove_game_stock_command))
    application.add_handler(CommandHandler("add_account", add_account_command))
    application.add_handler(CommandHandler("delete_account", delete_account_command))
    application.add_handler(CommandHandler("disable_game", disable_game_command))
    application.add_handler(CommandHandler("enable_game", enable_game_command))
    application.add_handler(CommandHandler("code", code_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, customer_code_request_handler)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
