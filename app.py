ဍimport re
import os
import json
import base64
import requests
from PIL import Image, ImageOps, ImageFilter
try:
    import pytesseract
except ImportError:
    pytesseract = None
import sqlite3
import logging
import asyncio
from html import escape
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    Defaults,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 0

CUSTOM_EMOJI = {
    # Product title icons
    "mlbb": os.getenv("EMOJI_MLBB", "").strip(),
    "genshin": os.getenv("EMOJI_GENSHIN", "").strip(),
    "hsr": os.getenv("EMOJI_HSR", "").strip(),
    "arena": "6129869323050687063",
    "capcut": os.getenv("EMOJI_CAPCUT", "").strip(),
    "expressvpn": os.getenv("EMOJI_EXPRESSVPN", "").strip(),
    "spotify": os.getenv("EMOJI_SPOTIFY", "").strip(),
    "youtube": "5334681713316479679",
    "netflix": "5318911503938634641",
    "primevideo": "5346056560537779652",
    "canva": "5796214303329620386",
    "picsart": os.getenv("EMOJI_PICSART", "").strip(),
    "grammarly": os.getenv("EMOJI_GRAMMARLY", "").strip(),
    "gmail": "6242548417126469488",
    "alight": "6239810925231084514",
    "hma": "5796595022115639741",
    "gemini": "6244416981303303108",
    "hiddify": "5940644462832127906",
    "happ": "6114074490625334807",
    "v2raytun": "6050646916109179497",
    "v2box": "5866266486942733691",
    "skip": "5416117059207572332",
"back": "6319056439096644016",
"cancel": "5210952531676504517",
    "zoom": "5334932883003949665",
    "hbomax": "5346319945112240722",
    "outofstock": "5210952531676504517",
"detail": "5395444784611480792",
    "payment": "5472250091332993630",
    "phone": "5348125953090403204",
    "user": "5409109841538994759",
    "price": "5409048419211682843",
    "camera": "5231012545799666522",
    "success": "5206607081334906820",
    "time": "5440621591387980068",
"pending": "5386367538735104399",
"reject": "5240241223632954241",
"reason": "5440660757194744323",
    "new_order": "5424818078833715060",
"contact": "5271604874419647061",
    "key": "5307843983102204243",
"world": "5447410659077661506",
"note": "5395444784611480792",
    "payment_method": "6179409279729012467",    
"kpay": "6172325371124389041",
"wave": "6172676549125346152",
"aya": "6145467330009767114",
"uab": "6145670035286268472",
    "wink": "6244687263595239404",
"meitu": "6244383016701925583",
"vip": "5438496463044752972",
"svip": "5217822164362739968",
    "box": "5334544901428229844",
"lock": "5296369303661067030",
"mail": "5253742260054409879",

    # Text/card icons
    "stock": os.getenv("EMOJI_STOCK", "").strip(),
    "status": os.getenv("EMOJI_STATUS", "").strip(),
    "loading": "5386367538735104399",
    "description": os.getenv("EMOJI_DESCRIPTION", "").strip(),
    "fast": os.getenv("EMOJI_FAST", "").strip(),
    "secure": os.getenv("EMOJI_SECURE", "").strip(),
    "trusted": os.getenv("EMOJI_TRUSTED", "").strip(),
    "cart": os.getenv("EMOJI_CART", "").strip(),
    "refresh": os.getenv("EMOJI_REFRESH", "").strip(),
"orders": os.getenv("EMOJI_ORDERS", "").strip(),
    "id": "5841276284155467413",

    # General icons
    "shop": os.getenv("EMOJI_SHOP", "").strip(),
    "game": os.getenv("EMOJI_GAME", "").strip(),
    "digital": os.getenv("EMOJI_DIGITAL", "").strip(),
"default": os.getenv("EMOJI_DEFAULT", "").strip(),
    "join": os.getenv("EMOJI_JOIN", "").strip(),
    "category": os.getenv("EMOJI_CATEGORY", "").strip(),
    "shop_now": os.getenv("EMOJI_SHOP_NOW", "").strip(),
    "choose": os.getenv("EMOJI_CHOOSE", "").strip(),
    "bulb": "5395444784611480792",
    "warning": "5240241223632954241",
    "globe": "5447410659077661506",
    "heart": "5337080053119336309",
    "tv": "5318911503938634641",
    "video": "5334932883003949665",
    "brush": "5348125953090403204",
    "robot": "6244416981303303108",
    "star": "6244687263595239404",
    "camera_icon": "5231012545799666522",
    "blue_box": "6244275874447760070",
    "computer": "5841276284155467413",
    "mac": "5841276284155467413",
    "music": "5334681713316479679",
}
def tg_emoji(key: str, fallback: str = "✨") -> str:
    emoji_id = CUSTOM_EMOJI.get(key, "").strip()

    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

    return fallback


def button_kwargs(key: str) -> dict:
    emoji_id = CUSTOM_EMOJI.get(key, "").strip()

    if not emoji_id:
        return {}

    return {
        "api_kwargs": {
            "icon_custom_emoji_id": emoji_id
        }
    }
def start_now_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Start Now")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )    

SHOP_NAME = "GAMEPAY HUB"
CONTACT_USERNAME = "@angsthtun"
CHANNEL_URL = "https://t.me/gamepaydyet"

WELCOME_STICKER_ID = ""
SUCCESS_STICKER_ID = ""

LOW_STOCK_THRESHOLD = 2
DB_PATH = "gamepay_hub.db"
DUPLICATE_ORDER_WINDOW_MINUTES = 5
AUTO_PAYMENT_TIMEOUT_MINUTES = 5
AUTO_ORDER_REMINDER_SECONDS = 240  # customer reminder before 5-minute KPay auto-plan timeout
AUTO_VERIFY_AMOUNT_TOLERANCE = 100

KPAY_EXPECTED_RECEIVER_NAMES = [
    "aung shin thant htun",
    "aung shin thant",
    "thant htun",
    "aung shin",
]
KPAY_EXPECTED_RECEIVER_PHONE = "09795687480"

PAYMENT_ACCOUNTS = {
    "kpay": {
        "label": "KPay",
        "text": f'KPay\n{tg_emoji("phone", "📱")} 09795687480\n{tg_emoji("user", "👤")} Aung Shin Thant Htun',
    },

    "wave": {
        "label": "Wave Pay",
        "text": f'Wave Pay\n{tg_emoji("phone", "📱")} 09795687480\n{tg_emoji("user", "👤")} Aung Shin Thant Htun',
    },

    "uab": {
        "label": "UAB Pay",
        "text": f'UAB Pay\n{tg_emoji("phone", "📱")} 09795687480\n{tg_emoji("user", "👤")} Aung Shin Thant Htun',
    },

    "aya": {
        "label": "AYA Pay",
        "text": f'AYA Pay\n{tg_emoji("phone", "📱")} 09795687480\n{tg_emoji("user", "👤")} Aung Shin Thant Htun',
    },
}


REJECT_REASONS = {
    "wrong_amount": f"{tg_emoji('price', '💰')} ငွေပမာဏမမှန်ပါ",
    "unclear_ss": f"{tg_emoji('camera', '📷')} Screenshot မရှင်းပါ",
    "fake_payment": f"{tg_emoji('reject', '❌')} Payment မအောင်မြင်သေးပါ",
    "duplicate_order": f"{tg_emoji('warning', '⚠️')} Duplicate order ဖြစ်နေပါတယ်",
    "other": f"{tg_emoji('reason', '📝')} Order info ပြန်စစ်ပြီး ပြန်တင်ပါ",
}

PRODUCTS: Dict[str, Dict[str, Any]] = {
    "mlbb_weekly": {
        "category": "game",
        "emoji_key": "mlbb",
        "name": "Weekly Pass",
        "full_name": "MLBB Weekly Pass",
        "description": "Fast and trusted MLBB Weekly Pass top up service.", 
        "photo": "Screenshot_2026-03-31-09-45-06-397_com.mobile.legends.jpg",
        "stock": 10,
        "enabled": True,
    "requires_detail_label": (
    f'{tg_emoji("id", "🆔")} <b>MLBB ID, Server ID နဲ့ Account Name ကို ပို့ပေးပါ။</b>\n\n'
    "ဥပမာ:\n<code>123456789 / 1234 / Mg</code>\n\n"
    f'{tg_emoji("bulb", "💡")} Note မရှိရင် <b>Skip / No Note</b> ကိုနှိပ်လို့ရပါတယ်။'
),
     "plans": {
            "default": {"label": "Weekly Pass", "price": 6500},
        },
    },
"genshin_blessing": {
    "category": "game",
    "emoji_key": "genshin",
    "name": "Blessing",
    "full_name": "Genshin Impact Blessing",
    "description": "Fast and trusted MLBB Weekly Pass top up service.",
    "photo": "Buy-Welkin-Moon-In-Game.png",
    "stock": 10,
    "enabled": True,
    "requires_detail_label": (
    f'{tg_emoji("id", "🆔")} <b>Genshin ID နဲ့ Region ကို ပို့ပေးပါ။</b>\n\n'
    "ဥပမာ:\n<code>800123456 / Asia</code>\n\n"
    f'{tg_emoji("bulb", "💡")} Note မရှိရင် <b>Skip / No Note</b> ကိုနှိပ်လို့ရပါတယ်။'
),
    "plans": {
        "default": {"label": "Blessing", "price": 19300},
    },
},

"honkai_starrail_supply": {
    "category": "game",
    "emoji_key": "hsr",
    "name": "Express Supply",
    "full_name": "Honkai Star Rail Express Supply",
    "description": "Fast and trusted Honkai Star Rail Express Supply top up service.",
    "photo": "hsr.jpg",
    "stock": 10,
    "enabled": True,
    "requires_detail_label": (
    f'{tg_emoji("id", "🆔")} <b>Honkai Star Rail ID နဲ့ Region ကို ပို့ပေးပါ။</b>\n\n'
    "ဥပမာ:\n<code>800123456 / Asia</code>\n\n"
    f'{tg_emoji("bulb", "💡")} Note မရှိရင် <b>Skip / No Note</b> ကိုနှိပ်လို့ရပါတယ်။'
),
    "plans": {
        "default": {"label": "Express Supply", "price": 19600},
    },
},
    "arena_breakout": {
    "category": "game",
    "emoji_key": "arena",
    "name": "Arena Breakout",
    "full_name": "Arena Breakout Infinite",
    "description": "Fast and trusted Arena Breakout top up service.",
    "photo": "arena.jpg",
    "stock": 10,
    "enabled": True,
    "requires_detail_label": (
    f'{tg_emoji("id", "🆔")} <b>Arena Breakout ID နဲ့ Account Name ကို ပို့ပေးပါ။</b>\n\n'
    "ဥပမာ:\n<code>123456789 / Mg Mg</code>\n\n"
    f'{tg_emoji("bulb", "💡")} Note မရှိရင် <b>Skip / No Note</b> ကိုနှိပ်လို့ရပါတယ်။'
),
    "plans": {
        "beginner_select": {
            "label": "Beginner Select",
            "price": 3500
        },

        "bulletproof_case": {
            "label": "Bulletproof Case (30d)",
            "price": 9900
        },

        "composition_case": {
            "label": "Composition Case (30d)",
            "price": 29300
        },

        "monthly_abp": {
            "label": "Monthly Advanced Battle Pass",
            "price": 4400
        },

        "monthly_pbp": {
            "label": "Monthly Premium Battle Pass",
            "price": 16800
        },

        "quarterly_pbp": {
            "label": "Quarterly Premium Battle Pass",
            "price": 49300
        },
    },
},  
    "capcut_pro": {
    "category": "digital",
    "emoji_key": "capcut",
    "name": "CapCut Pro",
    "full_name": "CapCut Pro Subscription",
        "description": (
    f'{tg_emoji("capcut", "📱")} CapCut Pro\n'
    f'{tg_emoji("reject", "⚠️")} Share Plan One Device'
),    
    "photo": "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1200&q=80",
    "enabled": True,
    "requires_detail_label": (
    f'{tg_emoji("detail", "📝")} <b>CapCut Pro Plan Information</b>\n\n'
    f'{tg_emoji("reject", "⚠️")} <b>Share Plan</b>\n'
    "1 Device ပဲဝင်ရပါတယ်။\n"
    "ပိုဝင်လို့အကောင့်ပျက်ရင် ပြန်မလဲပေးပါ။\n\n"
    f'{tg_emoji("success", "✅")} <b>Private Plan</b>\n'
    "4 Devices ဝင်ရပါတယ်။\n\n"
    f'{tg_emoji("success", "👉")} <b>Skip button ကိုပဲနှိပ်ပေးပါဗျ။</b>'
),
    "plans": {
        "private_1m": {"label": "Private Plan - 1 Month", "price": 20000},
    },
},  
    "hma_vpn": {
    "category": "digital",
    "emoji_key": "hma",
    "name": "HMA VPN",
    "full_name": "HMA VPN Subscription",
    "description": (
        f'{tg_emoji("hma", "🛡️")} HMA VPN\n'
        f'{tg_emoji("success", "✅")} Private Plan သည် Device 9 လုံးအထိ ဝင်ဆံ့ပါသည်။'
    ),
    "photo": "hma.jpg",
    "enabled": True,

    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>HMA VPN Plan Information</b>\n\n'

        f'{tg_emoji("reject", "⚠️")} <b>Share Plan</b>\n'
        "• One Device Only\n\n"

        f'{tg_emoji("success", "✅")} <b>Private Plan</b>\n'
        "• Device 9 လုံးအထိ ဝင်ဆံ့ပါသည်\n"
        "• All Devices Support\n\n"

        f'{tg_emoji("skip", "⏭")} <b>Skip button ကိုပဲနှိပ်ပေးပါဗျ။</b>'
    ),

    "plans": {
        "share_1m": {
            "label": "1 Month Share",
            "price": 1800
        },

        "private_1m": {
            "label": "1 Month Private",
            "price": 5000
        },
    },
},

    "express_vpn": {
    "category": "digital",
    "emoji_key": "expressvpn",
    "name": "Express VPN",
    "full_name": "Express VPN Subscription",
    "description": f'{tg_emoji("expressvpn", "🌐")} Share‌ Plan inly One deviceပါ။ပို၀င်ရင်လိူင်းကျပါတယ်။စည်းစနစ်ရှိ‌‌ေပးပါ။',  
    "photo": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?auto=format&fit=crop&w=1200&q=80",
    "enabled": True,
    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Express VPN Plan Information</b>\n\n'

        f'{tg_emoji("reject", "⚠️")} <b>Share Plan</b>\n'
        "• One Device ပဲဝင်ပါဗျ\n"
        "• Devices အများကြီးဝင်ရင် လိုင်းမကောင်းတာမျိုး ခဏခဏဖြစ်နိုင်ပါတယ်\n\n"

        f'{tg_emoji("success", "✅")} <b>3M / 6M Plan</b>\n'
        "• All Devices Support\n"
        "• Devices အများကြီးသုံးချင်ရင် ဒီ Plan တွေက ပိုသင့်တော်ပါတယ်\n\n"

        f'{tg_emoji("skip", "⏭")} <b>Skip button ကိုပဲနှိပ်ပေးပါဗျ။</b>'
    ),

    "plans": {
        "mobile_share_1m": {
            "label": "1 Month (Share) - Mobile",
            "price": 1400
        },

        "pc_share_1m": {
            "label": "1 Month (Share) - PC/Windows",
            "price": 2500
        },

        "mac_linux_share_1m": {
            "label": "1 Month (Share) - Mac/Linux",
            "price": 2500
        },

        "private_1m": {
            "label": "1 Month Private - All Devices Support",
            "price": 6500
        },

        "private_3m": {
            "label": "3 Month Share - All Devices Support",
            "price": 9000
        },

        "private_6m": {
            "label": "6 Month Share - All Devices Support",
            "price": 11500
        },
    },
},   
"v2raytun_v2box_vpn": {
"category": "digital",
"emoji_key": "v2raytun",
"name": "V2RayTun & V2Box VPN",
"full_name": "V2RayTun & V2Box VPN Key",

"description": (
    f'{tg_emoji("v2raytun", "🔹")} / '
    f'{tg_emoji("v2box", "🔹")} '
    f'{tg_emoji("success", "✅")} Unlimited Devices Support'
),

"photo": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?auto=format&fit=crop&w=1200&q=80",

"enabled": True,

"requires_detail_label": (
    f'{tg_emoji("detail", "📝")} <b>V2RayTun & V2Box VPN Information</b>\n\n'

    f'{tg_emoji("key", "🔑")} Key ပေးမှာပါဗျ\n'
    'ရရှိတဲ့ Key ကို Paste လုပ်ရုံနဲ့ အသုံးပြုနိုင်ပါတယ်\n\n'

    f'{tg_emoji("success", "✅")} Unlimited Devices Support\n\n'

    f'{tg_emoji("world", "🌍")} <b>Available Regions</b>\n'
    '• Singapore (SG)\n'
    '• Thailand (TH)\n\n'

    f'{tg_emoji("note", "✍️")} <b>လိုချင်တဲ့ Region ကို Note မှာရေးပို့ပါ</b>\n'
    'ဥပမာ - SG / TH\n\n'

    f'{tg_emoji("skip", "⏭")} <b>မရေးချင်ရင် Skip button ပဲနှိပ်ပါဗျ။</b>'
),

"plans": {
    "50gb_1m": {
        "label": "50GB Plan - 1 Month",
        "price": 3000
    },

    "100gb_1m": {
        "label": "100GB Plan - 1 Month",
        "price": 4000
    },

    "150gb_1m": {
        "label": "150GB Plan - 1 Month",
        "price": 5500
    },

    "200gb_1m": {
        "label": "200GB Plan - 1 Month",
        "price": 7000
    }
}

},
    "hiddify_vpn": {
    "category": "digital",
    "emoji_key": "hiddify",
    "name": "Hiddify VPN",
    "full_name": "Hiddify VPN Key",
    "description": f'{tg_emoji("hiddify", "🔐")} Hiddify VPN key delivery service.', 
    "photo": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?auto=format&fit=crop&w=1200&q=80",
    "enabled": True,

    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Hiddify VPN Information</b>\n\n'

        f'{tg_emoji("key", "🔑")} Key ပေးမှာပါဗျ\n'
        "ရရှိတဲ့ Key ကို Paste လုပ်ရုံနဲ့ အသုံးပြုနိုင်ပါတယ်\n\n"

        f'{tg_emoji("world", "🌍")} <b>Available Region</b>\n'
        "• Singapore (SG)\n\n"
        "• Thailand (TH)\n\n"

        f'{tg_emoji("note", "✍️")} <b>လိုအပ်ရင် Note ရေးပို့နိုင်ပါတယ်</b>\n\n'

        f'{tg_emoji("skip", "⏭")} <b>မရေးချင်ရင် Skip button ပဲနှိပ်ပါဗျ။</b>'
    ),

    "plans": {
        "50gb_1m": {
            "label": "50GB Plan - 1 Month",
            "price": 3000
        },

        "100gb_1m": {
            "label": "100GB Plan - 1 Month",
            "price": 4000
        },

        "150gb_1m": {
            "label": "150GB Plan - 1 Month",
            "price": 5500
        },

        "200gb_1m": {
            "label": "200GB Plan - 1 Month",
            "price": 7000
        },
    },
},
    
 "happ_vpn": {
    "category": "digital",
    "emoji_key": "happ",
    "name": "Happ Key",
    "full_name": "Happ VPN Key",
     "description": f'{tg_emoji("happ", "🔑")} Unlimitedလိုချင်Dmကြွပါ။',
    "photo": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?auto=format&fit=crop&w=1200&q=80",
    "enabled": True,

    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Outline VPN Information</b>\n\n'

        f'{tg_emoji("key", "🔑")} Key ပေးမှာပါဗျ\n'
        "ရရှိတဲ့ Key ကို Paste လုပ်ရုံနဲ့ အသုံးပြုနိုင်ပါတယ်\n\n"

        f'{tg_emoji("world", "🌍")} <b>Available Regions</b>\n'
        "• Singapore (SG)\n"
        "• Thailand (TH)\n\n"
        
        f'{tg_emoji("note", "✍️")} <b>လိုချင်တဲ့ Region ကို Note မှာရေးပို့ပါ</b>\n'
        "ဥပမာ - SG / US / Thailand\n\n"

        f'{tg_emoji("skip", "⏭")} <b>မရေးချင်ရင် Skip button ပဲနှိပ်ပါဗျ။</b>'
    ),

    "plans": {
        "50gb_1m": {
            "label": "50GB Plan - 1 Month",
            "price": 3000
        },

        "100gb_1m": {
            "label": "100GB Plan - 1 Month",
            "price": 4000
        },

        "150gb_1m": {
            "label": "150GB Plan - 1 Month",
            "price": 5500
        },

        "200gb_1m": {
            "label": "200GB Plan - 1 Month",
            "price": 7000
        },
    },
}, 
        "spotify_premium": {
        "category": "digital",
        "emoji_key": "spotify",
        "name": "Spotify Premium",
        "full_name": "Spotify Premium Subscription",
        "description": f'{tg_emoji("spotify", "🎵")} 2M/3M individualက‌ စောင့်ရပါတယ်။',
        "photo": "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?auto=format&fit=crop&w=1000&q=80",
        "enabled": True,
        "requires_detail_label": (
            f'{tg_emoji("detail", "📝")} <b>Spotify Plan Information</b>\n\n'
            f'{tg_emoji("reject", "⚠️")} <b>Individual 2M/3M Plan က စောင့်ရပါတယ်ဗျ။</b>\n'
            "At least 30 min ပါဗျ။\n\n"
            f'{tg_emoji("success", "👉")} <b>Skip button ကိုပဲနှိပ်ပေးပါဗျ။</b>'
        ),
        "plans": {
            "individual_3m": {"label": "Individual Plan - 3 Months", "price":14000},
        },
    },
       
    "youtube_premium": {
    "category": "digital",
    "emoji_key": "youtube",
    "name": "YouTube Premium",
    "full_name": "YouTube Premium Subscription",
    "description": f'{tg_emoji("youtube", "🎬")} Individual Plan Private accountပါ။',  
    "photo": "youtube.jpg",
    "enabled": True,

    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Private account ဖြစ်တဲ့အတွက် detail မလိုပါ။</b>\n\n'
        f'{tg_emoji("success", "👉")} <b>Skip button ကိုပဲနှိပ်ပေးပါဗျ။</b>'
    ),

    "plans": {
        "individual_1m": {
            "label": "Individual Private 1 Month",
            "price": 8000
        },
    },
},   
    "hbo_max": {
    "category": "digital",
    "emoji_key": "hbomax",
    "name": "HBO Max",
    "full_name": "HBO Max Premium Subscription",
    "description": (
        f'{tg_emoji("hbomax", "🎬")} HBO Max Premium\n'
        f'{tg_emoji("success", "✅")} Premium Streaming Service'
    ),
    "photo": "YOUR_HBO_IMAGE_URL",
    "enabled": True,
    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Profile 3ခူယူရင် ၁ခုစာကို6000 ks ပဲကျသင့်ပါတယ်။</b>\n\n'

        f'{tg_emoji("success", "✅")} <b>1 Profile</b>\n'
        "• Private Profile Access\n"
        "• Premium Quality Support\n\n"

        f'{tg_emoji("success", "✅")} <b>HBO Head</b>\n'
        "• Full HBO Max Account Access\n"
        "• Change Password & Manage Profiles\n\n"

        f'{tg_emoji("success", "👉")} <b>Skip button ကိုနှိပ်ပေးပါ</b>'
    ),
    "plans": {
        "profile_1": {
            "label": "1 Profile",
            "price": 8500
        },

        "hbo_head": {
            "label": "HBO Head",
            "price": 25000
        },
    },
},
    "netflix_premium": {
    "category": "digital",
    "emoji_key": "netflix",
    "name": "Netflix Premium",
    "full_name": "Netflix Premium Subscription",
    "description": f'{tg_emoji("netflix", "📺")} Netflix Premium account delivery service.',   
    "photo": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=1200&q=80",
    "enabled": True,

    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Netflix Information</b>\n\n'

        f'{tg_emoji("success", "✅")} Login With Password account ပါ\n\n'

        f'{tg_emoji("user", "👥")} <b>Profile များများဝယ်ချင်ရင် DM လာပေးပါဗျ</b>\n'
        "ဈေးပိုသက်သာပါတယ်\n\n"

        f'{tg_emoji("skip", "⏭")} <b>Skip button ပဲနှိပ်ပေးပါဗျ။</b>'
    ),

    "plans": {
        "private_1m": {
            "label": "Private Plan - 1 Month",
            "price": 15000
        },
    },
},
    "zoom_pro": {
    "category": "digital",
    "emoji_key": "zoom",
    "name": "Zoom Pro",
    "full_name": "Zoom Pro Subscription",
    "description": (
        f'{tg_emoji("zoom", "🎥")} Zoom Pro\n'
        f'{tg_emoji("success", "✅")} Premium Meeting Features'
    ),
    "photo": "YOUR_ZOOM_IMAGE_URL",
    "enabled": True,
    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Zoom Pro Plan Information</b>\n\n'

        f'{tg_emoji("success", "✅")} <b>Private Plan</b>\n'
        "• Full Premium Features\n"
        "• Private Account Access\n"
        "• Meeting Host Support\n\n"

        f'{tg_emoji("success", "👉")} <b>Skip button ကိုနှိပ်ပေးပါ</b>'
    ),
    "plans": {
        "private_14days": {
            "label": "1 Month Private",
            "price": 5000
        },
    },
},
    "prime_video": {
    "category": "digital",
    "emoji_key": "primevideo",
    "name": "Prime Video",
    "full_name": "Prime Video Premium",
    "description": "Prime Video premium account service.",
    "photo": "prime.jpg",
    "enabled": True,
    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} Note လိုအပ်ရင်ရေးပေးပါ\n'
        "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ"
    ),
    "plans": {
        "private_1m": {
            "label": "Private 1 Month",
            "price": 10500,
            "emoji_key": "primevideo",
        },
    },
},
    "canva_pro_edu": {
        "category": "digital",
         "emoji_key": "canva",
        "name": "Canva Pro Edu",
        "full_name": "Canva Pro Edu Subscription",
        "description": f'{tg_emoji("canva", "🎨")} Canva plans၃ခူရှိလို့ သေချာဖတ်‌ပေးပါဗျ။',
        "photo": "https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
        "requires_detail_label": (
    f'{tg_emoji("detail", "📝")} <b>Canva Plan Information</b>\n\n'
    f'{tg_emoji("mail", "📧")} Invite Plan တွေဆိုရင် မိမိရဲ့ Canva Mail ပို့ပေးပါ။\n\n'
    "Account ဆိုရင် ဒီဘက်ကပို့ပေးပါမယ်။\n\n"
    f'{tg_emoji("success", "👉")} <b>Mail မလိုတဲ့ plan ဆိုရင် Skip button ကိုနှိပ်ပေးပါဗျ။</b>'
),
        "plans": {
    "edu_1y": {"label": "Edu Invite 2.5 Year", "price": 3500},
    "pro_1m": {"label": "Canva Pro Account 1 Month", "price": 6500},
    "business_1m": {"label": "Business Invite 1 Month", "price": 8000},
},
    },
    "gemini_ai_pro": {
        "category": "digital",
           "emoji_key": "gemini",
        "name": "Gemini Ai Pro",
        "full_name": "Gemini Ai Pro Subscription",
        "description": f'{tg_emoji("gemini", "🤖")} 3M/4M ပိုတန်ပါတယ်။',
        "photo": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
       "requires_detail_label": (
    f'{tg_emoji("detail", "📝")} <b>Gemini Plan Information</b>\n\n'
    f'{tg_emoji("mail", "📧")} Invite Plan တွေဆိုရင် မိမိရဲ့ Mail ပို့ပေးပါ။\n\n'
    "Account ဆိုရင် ဒီဘက်ကပို့ပေးပါမယ်။\n\n"
    f'{tg_emoji("success", "👉")} <b>Mail မလိုတဲ့ plan ဆိုရင် Skip button ကိုနှိပ်ပေးပါဗျ။</b>'
),
        "plans": {
            "invite_1m": {"label": "1 Month - Ownmail Invite", "price": 4000},
        },
    },

"wink_app": {
    "category": "digital",
    "emoji_key": "wink",
    "name": "Wink App",
    "full_name": "Wink Premium Subscription",
    "description": f'{tg_emoji("wink", "✨")} China Versionပါ။',
    "photo": "wink.jpg",
    "enabled": True,
    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Wink App Information</b>\n\n'
        f'{tg_emoji("success", "✅")} China Version မို့ <b>China Wink</b> နဲ့သုံးရပါမယ်\n\n'
        f'{tg_emoji("phone", "📱")} China Phone တွေဆို <b>GetApps</b> ကနေ Download ရပါတယ်\n'
        f'{tg_emoji("phone", "📱")} iOS ဆို <b>App Store</b> ကနေ Download ရပါတယ်\n\n'
        f'{tg_emoji("contact", "📩")} Global Phone တွေအတွက် ကျနော့်ဆီ File လာတောင်းပေးပါ\n\n'
        f'{tg_emoji("skip", "⏭")} <b>Skip button ပဲနှိပ်ပေးပါဗျ။</b>'
    ),
    "plans": {
        "share_1m": {"label": "Share 1 Month", "price": 6500},
        "private_1m": {"label": "Private 1 Month", "price": 17000},
    },
},
    "meitu_vip": {
    "category": "digital",
    "emoji_key": "meitu",
    "name": "Meitu VIP",
    "full_name": "Meitu Premium Subscription",
    "description": f'{tg_emoji("meitu", "📸")} China Version',
    "photo": "meitu.jpg",
    "enabled": True,
    "requires_detail_label": (
        f'{tg_emoji("detail", "📝")} <b>Meitu VIP Information</b>\n\n'
        f'{tg_emoji("success", "✅")} China Ver မို့ <b>China Meitu</b> နဲ့သုံးရပါမယ်\n\n'
        f'{tg_emoji("phone", "📱")} China Phone တွေဆို <b>GetApps</b> ကနေ Download ရပါတယ်\n'
        f'{tg_emoji("phone", "📱")} iOS ဆို <b>App Store</b> ကနေ Download ရပါတယ်\n\n'
        f'{tg_emoji("contact", "📩")} Global Phone တွေအတွက် ကျနော့်ဆီ File လာတောင်းပေးပါ\n\n'
        f'{tg_emoji("skip", "⏭")} <b>Skip button ပဲနှိပ်ပေးပါဗျ။</b>'
    ),
    "plans": {
        "vip_1m": {"label": "VIP Plan (1 Month)", "price": 12500, "emoji_key": "vip"},
        "vip_1y": {"label": "VIP Plan (1 Year)", "price": 95000, "emoji_key": "vip"},
        "svip_1m": {"label": "SVIP Plan (1 Month)", "price": 22000, "emoji_key": "svip"},
        "svip_3m": {"label": "SVIP Plan (3 Months)", "price": 53000, "emoji_key": "svip"},
        "svip_1y": {"label": "SVIP Plan (1 Year)", "price": 160000, "emoji_key": "svip"},
    },
},
        "alight_motion": {
        "category": "digital",
           "emoji_key": "alight",
        "name": "Alight Motion",
        "full_name": "Alight Motion Premium",
        "description": f'{tg_emoji("alight", "🟦")} Alight Motion premium account service.',
        "photo": "https://images.unsplash.com/photo-1558655146-9f40138edfeb?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
        "requires_detail_label": (
            f'{tg_emoji("detail", "📝")} Note လိုအပ်ရင်ရေးပေးပါ\n'
            "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ"
        ),
        "plans": {
            "private_1y_pro": {"label": "1 Year (Private) Premium", "price": 2000},
        },
    },
    
    "gmail": {
    "category": "digital",
    "emoji_key": "gmail",
    "name": "Gmail",
    "full_name": "Gmail Account",
     "description": (
    f'{tg_emoji("gmail", "📧")} Gmail Account\n'
    f'{tg_emoji("reject", "⚠️")} Disable 2FA'
),  
     "requires_detail_label": (
    f'{tg_emoji("detail", "📝")} <b>Gmail Account Information</b>\n\n'
    f'{tg_emoji("reject", "⚠️")} 2FA ပိတ်ထားပြီးသား Gmail ပါ\n'
    "Login ဝင်ပြီးတာနဲ့ Password / Recovery Info ပြောင်းထားပေးပါ\n\n"
    f'{tg_emoji("skip", "⏭")} <b>Skip button ကိုပဲနှိပ်ပေးပါဗျ။</b>'
),
    "photo": "https://images.unsplash.com/photo-1611162617474-5b21e879e113?auto=format&fit=crop&w=1200&q=80",
    "enabled": True,
    "plans": {
        "one_mail": {
            "label": "One Mail",
            "price": 7300,
            "emoji_key": "gmail",
        },
    },
},
    
    "grammarly_ai": {
        "category": "digital",
           "emoji_key": "grammarly",
        "name": "Grammarly Ai",
        "full_name": "Grammarly Ai Subscription",
        "description": f"{tg_emoji('payment', '💳')} Grammarly Ai account delivery service.",
        "photo": "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=1200&q=80",
        "enabled": True,
        "requires_detail_label": (
            f"{tg_emoji('detail', '📝')} <b>လိုအပ်ရင် note / message ပို့ပါ</b>\n"
            "မလိုအပ်ရင် <code>No</code> ရိုက်ပို့ပါ သို့မဟုတ် <b>Skip / No Note</b> ကိုနှိပ်ပါ။"
        ),
        "plans": {
            "gram_1m": {"label": "1 Month", "price": 13000},
            "gram_2m": {"label": "2 Months", "price": 23500},
        },
    },
}

DIGITAL_INVENTORY: Dict[str, Dict[str, Any]] = {
    "capcut_pro": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "private_1m",
                "email": "capcutprivate1@example.com",
                "password": "pass5678",
                "extra": f"{tg_emoji('success', '✅')} Private account",
                "used": False,
            },
            {
                "plan_key": "private_1m",
                "email": "capcutprivate2@example.com",
                "password": "pass5678",
                "extra": f"{tg_emoji('success', '✅')} Private account",
                "used": False,
            },
        ],
    },
    "hma_vpn": {
    "auto_delivery": True,
    "accounts": [
        {
            "plan_key": "share_1m",
            "email": "hma_share_email_here",
            "password": "hma_share_password_here",
            "extra": f"{tg_emoji('hma', '🛡️')} HMA VPN 1 Month Share",
            "used": False,
        },
        {
            "plan_key": "private_1m",
            "email": "hma_private_email_here",
            "password": "hma_private_password_here",
            "extra": (
                f"{tg_emoji('hma', '🛡️')} HMA VPN 1 Month Private\n"
                f"{tg_emoji('success', '✅')} Device 9 လုံးအထိ ဝင်ဆံ့ပါသည်"
            ),
            "used": False,
        },
    ],
},

    "express_vpn": {
        "auto_delivery": True,
        "accounts": [
            {
    "plan_key": "mobile_share_1m",
    "email": "npulaep@gokublue.me",
    "password": "879235749",
    "extra": "[AUTO] Express VPN 1M Mobile Share | Slot 1",
    "used": False,
},
{
    "plan_key": "mobile_share_1m",
    "email": "npulaep@gokublue.me",
    "password": "879235749",
    "extra": "[AUTO] Express VPN 1M Mobile Share | Slot 1",
    "used": False,
},
            {
                "plan_key": "pc_share_1m",
                "email": "expresspc1@example.com",
                "password": "pass1234",
                "extra": f"{tg_emoji('computer', '💻')} PC / Windows Only",
                "used": False,
            },
            {
                "plan_key": "mac_linux_share_1m",
                "email": "expressmac1@example.com",
                "password": "pass1234",
                "extra": f"{tg_emoji('mac', '🖥️')} Mac / Linux Only",
                "used": False,
            },
            {
                "plan_key": "private_1m",
                "email": "expressprivate1@example.com",
                "password": "pass1234",
                "extra": f"{tg_emoji('success', '✅')} Private Account\n{tg_emoji('success', '✅')} All Devices Support",
                "used": False,
            },
            {
                "plan_key": "private_3m",
                "email": "expressprivate1@example.com",
                "password": "pass1234",
                "extra": f"{tg_emoji('success', '✅')} Private Account\n{tg_emoji('success', '✅')} All Devices Support",
                "used": False,
            },
            {
                "plan_key": "private_3m",
                "email": "expressprivate2@example.com",
                "password": "pass1234",
                "extra": f"{tg_emoji('success', '✅')} Share Account\n{tg_emoji('success', '✅')} All Devices Support",
                "used": False,
            },
            {
                "plan_key": "private_6m",
                "email": "expressprivate2@example.com",
                "password": "pass1234",
                "extra": f"{tg_emoji('success', '✅')} Share Account\n{tg_emoji('success', '✅')} All Devices Support",
                "used": False,
            },
        ],
    },
    "v2raytun_v2box_vpn": {
    "auto_delivery": False,
    "accounts": [],
},
    "hiddify_vpn": {
    "auto_delivery": False,
    "accounts": [],
},
    "happ_vpn": {
    "auto_delivery": False,
    "accounts": [],
},
    "spotify_premium": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "individual_3m",
                "email": "spotifyindividua2@example.com",
                "password": "12345",
                "extra": f"{tg_emoji('music', '🎵')} Individual 3 Month",
                "used": False,
            },
        ],
    },
   "youtube_premium": {
    "auto_delivery": False,
    "accounts": [],
}, 
    "hbo_max": {
    "auto_delivery": True,
    "accounts": [

        {
            "plan_key": "profile_1",
            "email": "hbomaxprofile1@example.com",
            "password": "pass1234",
            "extra": f"{tg_emoji('hbomax', '🎬')} HBO Max Profile",
            "used": False,
        },

        {
            "plan_key": "profile_1",
            "email": "hbomaxprofile2@example.com",
            "password": "pass1234",
            "extra": f"{tg_emoji('hbomax', '🎬')} HBO Max Profile",
            "used": False,
        },

        {
            "plan_key": "hbo_head",
            "email": "hbomaxhead1@example.com",
            "password": "pass5678",
            "extra": f"{tg_emoji('vip', '👑')} HBO Head Account",
            "used": False,
        },

    ],
},
    "netflix_premium": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "share_1m",
                "email": "netflixshare1@example.com",
                "password": "nf123456",
                "extra": f"{tg_emoji('bulb', '📌')} Profile 1 ကိုပဲသုံးပါ။",
                "used": False,
            },
            {
                "plan_key": "private_1m",
                "email": "netflixshare2@example.com",
                "password": "nf223456",
                "extra": f"{tg_emoji('bulb', '📌')} Profile 1 ကိုပဲသုံးပါ။",
                "used": False,
            },
        ],
    },
    "zoom_pro": {
    "auto_delivery": True,
    "accounts": [

        {
            "plan_key": "private_1m",
            "email": "zoomprivate1@example.com",
            "password": "pass5678",
            "extra": f"{tg_emoji('zoom', '🎥')} Zoom Pro Private Account",
            "used": False,
        },

        {
            "plan_key": "private_1m",
            "email": "zoomprivate2@example.com",
            "password": "pass5678",
            "extra": f"{tg_emoji('zoom', '🎥')} Zoom Pro Private Account",
            "used": False,
        },

    ],
},
    "prime_video": {
    "auto_delivery": True,
    "accounts": [
        {
            "plan_key": "private_1m",
            "email": "prime1@example.com",
            "password": "pass1234",
            "extra": "✅ Private Account",
            "used": False,
        },
        {
            "plan_key": "private_1m",
            "email": "prime2@example.com",
            "password": "pass5678",
            "extra": "✅ Private Account",
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
    "wink_app": {
    "auto_delivery": False,
    "accounts": [],
},

"meitu_vip": {
    "auto_delivery": False,
    "accounts": [],
},
    "picsart_pro": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "share_1m",
                "email": "picsart1@example.com",
                "password": "pass1234",
                "extra": "⚠️ Password မပြောင်းပါနဲ့",
                "used": False,
            },
            {
                "plan_key": "private_1m",
                "email": "picsartprivate@example.com",
                "password": "pass5678",
                "extra": "✅ Private Account",
                "used": False,
            },
        ],
    },
    "alight_motion": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "private_1y_pro",
                "email": "alight1@example.com",
                "password": "pass1111",
                "extra": "🟦 Basic Share",
                "used": False,
            },
            {
                "plan_key": "private_1y_pro",
                "email": "alight2@example.com",
                "password": "pass2222",
                "extra": "🟦 Premium Share",
                "used": False,
            },
        ],
    },
     "gmail": {
    "auto_delivery": True,
    "accounts": [
        {
            "plan_key": "one_mail",
            "email": "gmail1@example.com",
            "password": "gmail12345",
            "extra": f"{tg_emoji('warning', '⚠️')} 2FA Disabled\n{tg_emoji('success', '✅')} Login ဝင်ပြီး Password / Recovery Info ပြောင်းပါ\n{tg_emoji('success', '✅')} Full Warranty",
            "used": False,
        },
        {
            "plan_key": "one_mail",
            "email": "gmail2@example.com",
            "password": "gmail67890",
            "extra": f"{tg_emoji('warning', '⚠️')} 2FA Disabled\n{tg_emoji('success', '✅')} Login ဝင်ပြီး Password / Recovery Info ပြောင်းပါ\n{tg_emoji('success', '✅')} Full Warranty",
            "used": False,
        },
    ],
},
    "grammarly_ai": {
        "auto_delivery": True,
        "accounts": [
            {
                "plan_key": "gram_1m",
                "email": "grammarly1@example.com",
                "password": "gram12345",
                "extra": f"{tg_emoji('success', '✅')} 2 devices\n{tg_emoji('success', '✅')} Full Warranty\n{tg_emoji('success', '✅')} Projects/Notes are private",
                "used": True,
            },
            {
                "plan_key": "gram_2m",
                "email": "grammarly2@example.com",
                "password": "gram67890",
                "extra": f"{tg_emoji('success', '✅')} 2 devices\n{tg_emoji('success', '✅')} Full Warranty\n{tg_emoji('success', '✅')} Projects/Notes are private",
                "used": True,
            },
        ],
    },
}
INVITE_ONLY_PRODUCTS = {"gemini_ai_pro"}
INVITE_ONLY_PLANS = {
    ("canva_pro_edu", "edu_1y"),
    ("canva_pro_edu", "business_1m"),
    ("gemini_ai_pro", "invite_1m"),
}
MANUAL_DELIVERY_PLANS = {
    ("canva_pro_edu", "pro_1m"),
}
MANUAL_UNLIMITED_PRODUCTS = {
    "v2raytun_v2box_vpn",
    "hiddify_vpn",
    "happ_vpn",
    "wink_app",
    "meitu_vip",
    "youtube_premium",
}
AUTO_VERIFY_PLANS = {
    ("express_vpn", "mobile_share_1m"),
    ("capcut_pro", "share_1m"),
    ("capcut_pro", "share_3m"),
    ("hiddify_vpn", "50gb_1m"),
    ("hiddify_vpn", "100gb_1m"),
    ("outline_vpn", "50gb_1m"),
    ("outline_vpn", "100gb_1m"),
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
# PERFORMANCE CACHE
# =========================================================

CACHE = {
    "digital_stock": {},
    "game_stock": {},
}

def clear_cache():
    CACHE["digital_stock"].clear()
    CACHE["game_stock"].clear()

# =========================================================
# DATABASE
# =========================================================

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


MM_TZ = ZoneInfo("Asia/Yangon")

def now_dt() -> datetime:
    return datetime.now(MM_TZ)


def now_str() -> str:
    return now_dt().strftime("%Y-%m-%d %H:%M:%S")


def new_order_id() -> str:
    return "ORD-" + now_dt().strftime("%Y%m%d-%H%M%S-%f")[-20:]


ORDER_ID_RE = re.compile(r"ORD\s*[-‐‑‒–—−]\s*\d{6}\s*[-‐‑‒–—−]\s*\d{6}\s*[-‐‑‒–—−]\s*\d{6}", re.IGNORECASE)


def normalize_order_id(value: str) -> str:
    """Normalize copied/pasted Telegram order IDs to the database format."""
    if not value:
        return ""

    text = str(value).strip()
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"[‐‑‒–—−]", "-", text)
    text = re.sub(r"\s+", "", text)
    text = text.upper()

    match = re.search(r"ORD-?([0-9]{6})-?([0-9]{6})-?([0-9]{6})", text)
    if match:
        return f"ORD-{match.group(1)}-{match.group(2)}-{match.group(3)}"

    return text


def extract_order_id_from_text(text: str) -> str:
    """Extract and normalize the first order ID from a command or pasted admin message."""
    if not text:
        return ""

    match = ORDER_ID_RE.search(text)
    if match:
        return normalize_order_id(match.group(0))

    fallback = re.search(r"ORD[-\s‐‑‒–—−]*[0-9\s\-‐‑‒–—−]{18,}", text, re.IGNORECASE)
    if fallback:
        return normalize_order_id(fallback.group(0))

    return normalize_order_id(text.split()[0] if text.split() else text)

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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            joined_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS broadcast_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broadcast_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
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
                WHERE product_key = ?
                AND plan_key = ?
                AND email = ?
                AND password = ?
                AND extra = ?
                """,
                (
               product_key,
               acc["plan_key"],
               acc["email"],
               acc["password"],
               acc.get("extra", ""),
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
    clear_cache()


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
    clear_cache()


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
    normalized_order_id = normalize_order_id(order_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE order_id = ?", (normalized_order_id,))
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
    if product_key in INVITE_ONLY_PRODUCTS or product_key in MANUAL_UNLIMITED_PRODUCTS:
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


def get_cached_digital_stock(product_key: str, plan_key: Optional[str] = None) -> int:
    if product_key in INVITE_ONLY_PRODUCTS or product_key in MANUAL_UNLIMITED_PRODUCTS:
        return 999

    cache_key = f"{product_key}:{plan_key or 'all'}"
    if cache_key in CACHE["digital_stock"]:
        return CACHE["digital_stock"][cache_key]
    value = get_digital_stock(product_key, plan_key)
    CACHE["digital_stock"][cache_key] = value
    return value


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
        clear_cache()
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

def reserve_auto_account(product_key: str, plan_key: str, order_id: str):

    conn = db_connect()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN IMMEDIATE")

        cur.execute(
            """
            SELECT id, email, password, extra
            FROM digital_accounts
            WHERE product_key = ?
              AND plan_key = ?
              AND used = 0
              -- AND extra LIKE '[AUTO]%'
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
        clear_cache()

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
def normalize_ocr_text(text: str) -> str:
    """Normalize OCR text so KPay receiver name / phone matching becomes more reliable."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9:/, .\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_amount_from_text(text: str) -> Optional[int]:
    """Return the most likely payment amount from OCR text.

    KBZPay/KPay receipts commonly show paid amounts as values such as
    "-1,400.00 Ks". The old parser split that into 1, 400, and 00, so a
    valid 1,400 Ks receipt could be detected as 400 Ks and auto-cancelled.
    This parser keeps comma/decimal/signed money tokens together, converts
    them to absolute Kyat amounts, and ignores long transaction IDs.
    """
    raw_text = text or ""
    normalized = normalize_ocr_text(raw_text)
    amounts = []

    money_patterns = [
        # Strong matches near amount labels, e.g. "Amount -1,400.00 Ks".
        r"(?:amount|amt|total|paid)\s*[:\-]?\s*([\-−]?\s*\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)\s*(?:ks|kyat|mmk)?",
        r"(?:amount|amt|total|paid)\s*[:\-]?\s*([\-−]?\s*\d+(?:\.\d{1,2})?)\s*(?:ks|kyat|mmk)",
        # General money values, e.g. "-1,400.00 Ks" or "1400 Ks".
        r"([\-−]?\s*\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)\s*(?:ks|kyat|mmk)?",
        r"([\-−]?\s*\d+(?:\.\d{1,2})?)\s*(?:ks|kyat|mmk)",
    ]

    def add_amount(token: str):
        token = (token or "").replace("−", "-").replace(" ", "").replace(",", "")
        if not token or token in {"-", "."}:
            return
        try:
            value = abs(float(token))
        except ValueError:
            return
        # Reject decimal fragments and long IDs; accept realistic plan prices.
        if value.is_integer():
            clean = int(value)
        else:
            clean = int(round(value))
        if 500 <= clean <= 500000:
            amounts.append(clean)

    for pattern in money_patterns:
        for match in re.findall(pattern, normalized):
            add_amount(match)

    # Fallback for OCR text without Ks/MMK labels, still preserving comma decimals.
    for match in re.findall(r"[\-−]?\s*\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?", normalized):
        add_amount(match)

    if not amounts:
        return None

    # Prefer the largest parsed money value. This avoids decimal/comma fragments
    # such as 900 from "-2,900.00 Ks" overriding the real 2,900 Ks amount.
    return max(amounts)


def verify_kpay_receiver_text(text: str) -> bool:
    normalized = normalize_ocr_text(text)
    compact = normalized.replace(" ", "").replace("-", "")
    expected_phone_variants = {
        KPAY_EXPECTED_RECEIVER_PHONE,
        KPAY_EXPECTED_RECEIVER_PHONE.replace("09", "959", 1),
        KPAY_EXPECTED_RECEIVER_PHONE.replace("09", "+959", 1).replace("+", ""),
    }
    phone_ok = any(phone.replace(" ", "").replace("-", "").replace("+", "") in compact for phone in expected_phone_variants)
    exact_name_ok = any(name in normalized for name in KPAY_EXPECTED_RECEIVER_NAMES)
    # OCR can split or slightly distort names; require at least 3 meaningful receiver-name tokens.
    receiver_tokens = {"aung", "shin", "thant", "htun"}
    token_hits = sum(1 for token in receiver_tokens if token in normalized)
    partial_name_ok = token_hits >= 3
    return bool(phone_ok or exact_name_ok or partial_name_ok)


def auto_reject_text(order_id: str, reason_title: str, reason_detail: str) -> str:
    return (
        f"{tg_emoji('reject', '❌')} <b>Order Auto Cancelled</b>\n\n"
        f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
        f"{tg_emoji('reason', '📝')} <b>Reason:</b> {escape(reason_title)}\n\n"
        f"{escape(reason_detail)}\n\n"
        "ငွေပမာဏ / KPay name / screenshot ကိုစစ်ပြီး order အသစ် ပြန်တင်ပေးပါ။"
    )


async def auto_reject_order(context, user_id: int, order_id: str, reason_title: str, reason_detail: str, log_note: str):
    order_update_status(order_id, "rejected", log_note)
    log_action(order_id, 0, "auto_rejected", log_note)
    await context.bot.send_message(
        chat_id=user_id,
        text=auto_reject_text(order_id, reason_title, reason_detail),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"{tg_emoji('reject', '❌')} <b>KPay Auto Rejected</b>\n\n"
            f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"{tg_emoji('reason', '📝')} <b>Reason:</b> {escape(log_note)}"
        ),
        parse_mode=ParseMode.HTML,
    )


def _prepare_ocr_images(file_path: str) -> list:
    """Create OCR-friendly image variants for clean KBZPay/KPay receipts."""
    image = Image.open(file_path).convert("RGB")
    # Telegram screenshots are often scaled down; upscale and boost contrast before OCR.
    scale = 2 if max(image.size) < 1800 else 1
    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale))

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    sharp = gray.filter(ImageFilter.SHARPEN)
    binary = sharp.point(lambda p: 255 if p > 165 else 0)
    return [image, gray, sharp, binary]


def _local_tesseract_ocr(file_path: str) -> str:
    """Run Tesseract on multiple preprocessed variants and return combined text."""
    if pytesseract is None:
        raise RuntimeError("pytesseract Python package is not installed")

    texts = []
    last_error = None
    for image in _prepare_ocr_images(file_path):
        try:
            text = pytesseract.image_to_string(
                image,
                config="--psm 6 -c preserve_interword_spaces=1",
            )
            if text and text.strip():
                texts.append(text.strip())
        except Exception as exc:
            last_error = exc
    combined = "\n".join(dict.fromkeys(texts))
    if combined.strip():
        return combined
    if last_error:
        raise last_error
    return ""


def _openai_vision_receipt_ocr(file_path: str) -> str:
    """Optional fallback OCR using OpenAI-compatible vision when OPENAI_API_KEY is configured."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ""

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")
    with open(file_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Read this KBZPay/KPay payment receipt. Return only plain text lines for "
                            "Amount, Transfer To/Receiver name, Receiver phone last digits if visible, "
                            "Transaction Time, and Transaction No. Do not add explanation."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": 300,
    }
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.exception("OpenAI vision OCR fallback failed: %s", exc)
        return ""


async def extract_kpay_screenshot_info(context, file_id: str) -> dict:
    """Download one screenshot once, run robust OCR, and return amount/name verification data."""
    tg_file = await context.bot.get_file(file_id)
    safe_file_id = re.sub(r"[^A-Za-z0-9_-]", "_", file_id)
    file_path = f"/tmp/kpay_{safe_file_id}.jpg"

    await tg_file.download_to_drive(file_path)
    try:
        local_text = ""
        local_error = ""
        try:
            local_text = _local_tesseract_ocr(file_path)
        except Exception as exc:
            local_error = str(exc)
            logger.exception("Local Tesseract OCR failed: %s", exc)

        vision_text = ""
        # Use vision if local OCR failed or did not contain enough usable receipt data.
        if not local_text or extract_amount_from_text(local_text) is None or not verify_kpay_receiver_text(local_text):
            vision_text = _openai_vision_receipt_ocr(file_path)

        text = "\n".join(part for part in [local_text, vision_text] if part and part.strip())
        amount = extract_amount_from_text(text)
        receiver_ok = verify_kpay_receiver_text(text)

        logger.info("KPay OCR text: %s", text)
        return {
            "text": text,
            "amount": amount,
            "receiver_ok": receiver_ok,
            "ocr_error": local_error if not text else "",
        }
    finally:
        try:
            os.remove(file_path)
        except Exception:
            pass


async def extract_amount_from_screenshot(context, file_id):
    # Backward compatible wrapper for older admin/debug usage.
    return (await extract_kpay_screenshot_info(context, file_id))["amount"]


async def verify_kpay_receiver_name(context, file_id):
    # Backward compatible wrapper for older admin/debug usage.
    return (await extract_kpay_screenshot_info(context, file_id))["receiver_ok"]


def is_auto_verify_plan(product_key: str, plan_key: str, payment_key: str) -> bool:
    return payment_key == "kpay" and (product_key, plan_key) in AUTO_VERIFY_PLANS


def kpay_auto_plan_notice_text(product_name: str, plan_label: str, price: int) -> str:
    return (
        f"{tg_emoji('time', '⏰')} <b>Quick Delivery Plan Notice</b>\n\n"
        f"{tg_emoji('box', '📦')} <b>Product:</b> {escape(product_name)}\n"
        f"{tg_emoji('stock', '📦')} <b>Plan:</b> {escape(plan_label)}\n"
        f"{tg_emoji('price', '💰')} <b>Amount:</b> {price} Ks\n\n"
        f"{tg_emoji('success', '✅')} KPay payment screenshot ကို "
        f"<b>{AUTO_PAYMENT_TIMEOUT_MINUTES} မိနစ်အတွင်း</b> photo အနေနဲ့ပို့ပေးပါ။\n"
        f"{tg_emoji('camera', '📷')} Screenshot ထဲမှာ <b>Name / Amount / Time</b> မြင်ရအောင် ပို့ပေးပါ။\n"
        f"{tg_emoji('delivery', '🚚')} Payment စစ်ဆေးအောင်မြင်ပြီး stock ရှိပါက product ကိုချက်ချင်းပို့ပါမယ်။ "
        "Screenshot မဖတ်နိုင်ပါက admin က manual စစ်ဆေးပေးပါမယ်။"
    )


async def _auto_order_alarm_task(context: ContextTypes.DEFAULT_TYPE, user_id: int, session_id: str):
    await asyncio.sleep(AUTO_ORDER_REMINDER_SECONDS)
    if context.user_data.get("auto_alarm_session_id") != session_id:
        return
    if not is_auto_verify_plan(
        context.user_data.get("product_key", ""),
        context.user_data.get("plan_key", ""),
        context.user_data.get("payment_key", ""),
    ):
        return

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            f"{tg_emoji('time', '⏰')} <b>Payment Screenshot Reminder</b>\n\n"
            f"{tg_emoji('success', '✅')} ကျေးဇူးပြု၍ <b>{AUTO_PAYMENT_TIMEOUT_MINUTES} မိနစ်အတွင်း</b> "
            "KPay screenshot ကို photo အနေနဲ့ပို့ပေးပါ။\n"
            f"{tg_emoji('camera', '📷')} <b>Name / Amount / Time</b> မြင်ရအောင်ပို့ပါ။ "
            "Payment စစ်ဆေးအောင်မြင်ပြီး stock ရှိပါက product ကိုချက်ချင်းပို့ပါမယ်။"
        ),
        parse_mode=ParseMode.HTML,
    )


def schedule_auto_order_alarm(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    session_id = f"{user_id}:{now_dt().timestamp()}"
    context.user_data["auto_alarm_session_id"] = session_id
    context.application.create_task(_auto_order_alarm_task(context, user_id, session_id))


def build_auto_delivery_text(order: dict, account: dict, heading: str = "Products ပို့ပြီးပါပြီ") -> str:
    text = (
        f"{tg_emoji('success', '✅')} <b>{escape(heading)}</b>\n\n"
        f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order['order_id'])}</code>\n"
        f"{tg_emoji('box', '📦')} <b>Product:</b> {escape(order.get('product_name', '-'))}\n"
        f"{tg_emoji('stock', '📦')} <b>Plan:</b> {escape(order.get('plan_label', '-'))}\n\n"
        f"{tg_emoji('mail', '📧')} <b>Email:</b> <code>{escape(account['email'])}</code>\n"
        f"{tg_emoji('key', '🔑')} <b>Password:</b> <code>{escape(account['password'])}</code>\n"
    )
    if account.get("extra"):
        text += f"\n{tg_emoji('note', '📝')} <b>Note:</b> {escape(account['extra'])}\n"
    text += f"\n{tg_emoji('lock', '🔐')} Login code လိုရင် <code>Code</code> လို့ရိုက်ပို့နိုင်ပါတယ်။"
    return text

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
    clear_cache()


def get_game_stock(product_key: str) -> int:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT stock FROM game_products WHERE product_key = ?", (product_key,))
    row = cur.fetchone()
    conn.close()
    return int(row["stock"]) if row else 0


def get_cached_game_stock(product_key: str) -> int:
    if product_key in CACHE["game_stock"]:
        return CACHE["game_stock"][product_key]
    value = get_game_stock(product_key)
    CACHE["game_stock"][product_key] = value
    return value


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
    clear_cache()


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
    clear_cache()
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
    clear_cache()


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
def save_user(user):
    if not user:
        return

    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO users (
            user_id, username, full_name, joined_at
        )
        VALUES (?, ?, ?, COALESCE(
            (SELECT joined_at FROM users WHERE user_id = ?),
            ?
        ))
        """,
        (
            user.id,
            f"@{user.username}" if user.username else "",
            user.full_name or "",
            user.id,
            now_str(),
        ),
    )

    conn.commit()
    conn.close()


def get_all_users() -> List[int]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [int(r["user_id"]) for r in rows]


def save_broadcast_message(broadcast_id: str, user_id: int, message_id: int):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO broadcast_messages (
            broadcast_id, user_id, message_id, created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (broadcast_id, user_id, message_id, now_str()),
    )

    conn.commit()
    conn.close()


def get_broadcast_messages(broadcast_id: str) -> List[dict]:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM broadcast_messages
        WHERE broadcast_id = ?
        """,
        (broadcast_id,),
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_broadcast_records(broadcast_id: str):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM broadcast_messages WHERE broadcast_id = ?",
        (broadcast_id,),
    )

    conn.commit()
    conn.close()
# =========================================================
# UI HELPERS
# =========================================================

async def fake_loading(query, text: str = None):

    if text is None:
        text = f"{tg_emoji('pending', '⏳')} <b>Loading...</b>"

    try:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
        )

        await asyncio.sleep(0.18)

    except Exception:
        pass



def glam_title(title: str) -> str:
    return f"<b>{escape(title)}</b>"


def glam_footer() -> str:
    return ""

def human_status(status: str) -> str:
    mapping = {
        "pending_payment_review":
            f"{tg_emoji('pending', '⏳')} Pending Review",

        "waiting_manual_delivery":
            f"{tg_emoji('box', '📦')} Waiting Delivery",

        "approved":
            f"{tg_emoji('success', '✅')} Approved",

        "delivered":
            f"{tg_emoji('success', '✅')} Delivered",

        "code_requested":
            f"{tg_emoji('lock', '🔐')} Code Requested",

        "code_sent":
            f"{tg_emoji('key', '🔑')} Code Sent",

        "rejected":
            f"{tg_emoji('reject', '❌')} Rejected",
    }

    return mapping.get(status, status)

def order_summary_text(order: dict) -> str:
    summary_icon = tg_emoji("detail", "📋")
    id_icon = tg_emoji("id", "🆔")
    product_icon = tg_emoji("cart", "🛍️")
    plan_icon = tg_emoji("stock", "📦")
    price_icon = tg_emoji("price", "💰")
    detail_icon = tg_emoji("detail", "📝")
    payment_icon = tg_emoji("payment", "🏦")
    status_icon = tg_emoji("status", "📌")
    time_icon = tg_emoji("time", "🕒")

    return (
        f"{summary_icon} <b>Order Summary</b>\n\n"
        f"{id_icon} <b>Order ID:</b> <code>{escape(order['order_id'])}</code>\n"
        f"{product_icon} <b>Product:</b> {escape(order['product_name'])}\n"
        f"{plan_icon} <b>Plan:</b> {escape(order['plan_label'])}\n"
        f"{price_icon} <b>Price:</b> {order['price']} Ks\n"
        f"{detail_icon} <b>Detail / Note:</b> {escape(order.get('detail') or '-')}\n"
        f"{payment_icon} <b>Payment:</b> {escape(order.get('payment_name') or '-')}\n"
        f"{status_icon} <b>Status:</b> {human_status(order['status'])}\n"
        f"{time_icon} <b>Created:</b> {escape(order['created_at'])}"
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
            stock = get_cached_digital_stock(product_key)
            cheapest = min(v["price"] for v in product["plans"].values())
            price_text = f"From {cheapest} Ks"
            enabled = product.get("enabled", True)
            is_in_stock = stock > 0 and enabled
    else:
        stock = get_cached_game_stock(product_key)
        first_price = next(iter(product["plans"].values()))["price"]
        price_text = f"{first_price} Ks"
        enabled = is_game_enabled(product_key)
        is_in_stock = stock > 0 and enabled

    product_icon = tg_emoji(product.get("emoji_key", "default"), "🔥")
    price_icon = tg_emoji("price", "💰")
    stock_icon = tg_emoji("stock", "📦")
    status_icon = tg_emoji("status", "📌")
    description_icon = tg_emoji("description", "📝")
    fast_icon = tg_emoji("fast", "⚡")
    secure_icon = tg_emoji("secure", "🔐")
    trusted_icon = tg_emoji("trusted", "💎")
    status_green = tg_emoji("success", "🟢")
    status_red = tg_emoji("outofstock", "🔴")
    status = f"{status_green} Available" if is_in_stock else f"{status_red} Out of Stock"


    return (
        f"{product_icon} <b>{escape(product['full_name'])}</b>\n\n"
        f"{price_icon} <b>Price:</b> {escape(price_text)}\n"
        f"{stock_icon} <b>Stock:</b> {stock}\n"
        f"{status_icon} <b>Status:</b> {status}\n\n"
        f"{description_icon} <b>Description</b>\n"
        f"{product['description']}\n\n"
        f"{fast_icon} Fast Service\n"
        f"{secure_icon} Secure Payment\n"
        f"{trusted_icon} Trusted Seller"
    )

    
def payment_text(payment_name: str, pay_text: str, amount: int, payment_key: str) -> str:

    payment_icon = tg_emoji("payment", "💳")
    pay_emoji = tg_emoji(payment_key, "💰")

    price_icon = tg_emoji("price", "💰")
    camera_emoji = tg_emoji("camera", "📷")
    success_emoji = tg_emoji("success", "✅")

    return (
        f"{payment_icon} <b>Payment Info</b>\n\n"

        f"{pay_emoji} <b>Method:</b> {escape(payment_name)}\n\n"

        f"{pay_text}\n\n"

        f"{price_icon} <b>Amount:</b> {amount} Ks\n\n"

        f"{camera_emoji} ငွေလွှဲပြီး payment screenshot ကို <b>photo</b> နဲ့ပို့ပေးပါ\n"

        f"{success_emoji} Screenshot ပို့ပြီးတာနဲ့ payment ကိုစစ်ပေးပါမယ်"
    )
def welcome_text() -> str:
    shop_icon = tg_emoji("shop", "🎉")
    game_icon = tg_emoji("game", "🎮")
    digital_icon = tg_emoji("digital", "💻")
    fast_icon = tg_emoji("fast", "⚡")
    secure_icon = tg_emoji("secure", "🔐")
    trusted_icon = tg_emoji("trusted", "💎")
    choose_icon = tg_emoji("choose", "👇")
    

    return (
        f'{tg_emoji("success","✅")} <b>June Promotion Is Live!</b>\n\n'
        f"{shop_icon} <b>Welcome to {escape(SHOP_NAME)}</b>\n\n"
        f"{game_icon} Game Top Up\n"
        f"{digital_icon} Digital Products\n"
        f"{fast_icon} Fast Delivery\n"
        f"{secure_icon} Safe Payment\n"
        f"{trusted_icon} Premium Service\n"
        f"{choose_icon} <b>Please choose from the menu below</b>"
    )



def category_text() -> str:
    category_icon = tg_emoji("category", "📂")
    choose_icon = tg_emoji("choose", "👇")

    return (
        f"{category_icon} <b>Shop Categories</b>\n\n"
        f"စိတ်ကြိုက် category ကိုရွေးပေးပါ {choose_icon}"
    )

def products_text(category_key: str) -> str:
    choose_icon = tg_emoji("choose", "👇")

    if category_key == "game":
        game_icon = tg_emoji("game", "🎮")
        return (
            f"{game_icon} <b>Game Products</b>\n\n"
            f"ဝယ်ယူချင်တဲ့ game item ကိုရွေးပေးပါ {choose_icon}"
        )

    digital_icon = tg_emoji("digital", "💻")
    return (
        f"{digital_icon} <b>Digital Products</b>\n\n"
        f"ဝယ်ယူချင်တဲ့ product ကိုရွေးပေးပါ {choose_icon}"
    )


def plan_text(product_key: str) -> str:
    cart_icon = tg_emoji("cart", "🛒")
    return product_caption(PRODUCTS[product_key], product_key) + f"\n\n{cart_icon} <b>Please choose a plan</b>"


def detail_text(product_key: str) -> str:
    detail_icon = tg_emoji("detail", "📝")

    product = PRODUCTS[product_key]

    return (
        f"{detail_icon} <b>Detail / Note</b>\n\n"
        f"{product['requires_detail_label']}\n\n"
        f"စာရိုက်ပို့လို့ရပါတယ်\n"
        f"မလိုရင် button ကိုနှိပ်လို့ရပါတယ် {tg_emoji('choose', '👇')}"
    )


async def safe_edit_message(query, text: str, reply_markup=None):
    """Edit callback message, and fall back to sending a new message if Telegram rejects the edit.

    This prevents the UI from being left on temporary screens such as
    "Preparing payment..." when an edit fails because of Telegram-side
    limitations, deleted messages, stale callback messages, or formatting
    issues. Existing callers may ignore the boolean return value.
    """
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return True
    except Exception as edit_error:
        logger.warning("safe_edit_message edit failed, trying reply fallback: %s", edit_error)

    try:
        if getattr(query, "message", None):
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            return True
    except Exception as reply_error:
        logger.error("safe_edit_message reply fallback failed: %s", reply_error)

    return False


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
            [
                
                InlineKeyboardButton(
                    "Shop Now",
                    callback_data="menu_shop",
                    **button_kwargs("shop_now"),
                    
                )
            ],
            [
                InlineKeyboardButton(
                    "Join Channel",
                    url=CHANNEL_URL,
                    **button_kwargs("join"),
                )
            ],
            [
                InlineKeyboardButton(
                    "My Orders",
                    callback_data="menu_myorders",
                    **button_kwargs("orders"),
                ),
                InlineKeyboardButton(
                    "Contact Admin",
                    callback_data="menu_contact",
                    **button_kwargs("contact"),
                ),
            ],
            [
                InlineKeyboardButton(
                    "Refresh",
                    callback_data="menu_restart",
                    **button_kwargs("refresh"),
                )
            ],
        ]
    )
def category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Game Top Up",
                    callback_data="cat:game",
                    **button_kwargs("game"),
                )
            ],
            [
                InlineKeyboardButton(
                    "Digital Products",
                    callback_data="cat:digital",
                    **button_kwargs("digital"),
                )
            ],
            [
                InlineKeyboardButton(
                    "Back",
                    callback_data="back_main",
                    **button_kwargs("back"),
                )
            ],
        ]
    )
DIGITAL_PRODUCTS_PER_PAGE = 8

def products_keyboard(category_key: str, page: int = 0) -> InlineKeyboardMarkup:
    rows = []

    products = [
        (key, product)
        for key, product in PRODUCTS.items()
        if product["category"] == category_key
    ]

    if category_key == "digital":
        products = [
            (key, product)
            for key, product in products
            if product.get("enabled", True)
        ]

        total_pages = max(1, (len(products) + DIGITAL_PRODUCTS_PER_PAGE - 1) // DIGITAL_PRODUCTS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        start = page * DIGITAL_PRODUCTS_PER_PAGE
        end = start + DIGITAL_PRODUCTS_PER_PAGE
        visible_products = products[start:end]
    else:
        visible_products = products
        total_pages = 1
        page = 0

    for key, product in visible_products:
        emoji_key = product.get("emoji_key", "default")

        if category_key == "digital":
            cheapest = min(v["price"] for v in product["plans"].values())
            total_stock = 999 if key in INVITE_ONLY_PRODUCTS or key in MANUAL_UNLIMITED_PRODUCTS or any(k == key for k, _ in INVITE_ONLY_PLANS | MANUAL_DELIVERY_PLANS) else get_cached_digital_stock(key)
            
            if total_stock > 0:
                price_text = f"{cheapest} Ks" if key in INVITE_ONLY_PRODUCTS else f"From {cheapest} Ks"
                rows.append([
                    InlineKeyboardButton(
                        f"{product['name']} • {price_text}",
                        callback_data=f"product:{key}",
                        **button_kwargs(emoji_key),
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"{product['name']} • Out of Stock",
                        callback_data="out_of_stock",
                        **button_kwargs("reject"),
                    )
                ])

        else:
            if not is_game_enabled(key):
                continue

            stock = get_cached_game_stock(key)
            default_price = next(iter(product["plans"].values()))["price"]

            if stock > 0:
                rows.append([
                    InlineKeyboardButton(
                        f"{product['name']} • {default_price} Ks",
                        callback_data=f"product:{key}",
                        **button_kwargs(emoji_key),
                    )
                ])
            else:
                rows.append([
                    InlineKeyboardButton(
                        f"{product['name']} • Out of Stock",
                        callback_data="out_of_stock",
                        **button_kwargs("reject"),
                    )
                ])

    if category_key == "digital" and total_pages > 1:
        nav_row = []

        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    "Previous",
                    callback_data=f"digital_page:{page - 1}",
                    **button_kwargs("back"),
                )
            )

        if page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton(
                    "Next",
                    callback_data=f"digital_page:{page + 1}",
                    **button_kwargs("skip"),
                )
            )

        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton(
            "Back to Categories",
            callback_data="back_categories",
            **button_kwargs("back"),
        )
    ])

    return InlineKeyboardMarkup(rows)
  

def plans_keyboard(product_key: str) -> InlineKeyboardMarkup:
    rows = []
    product = PRODUCTS[product_key]
    emoji_key = product.get("emoji_key", "default")

    for plan_key, plan in product["plans"].items():
        plan_emoji_key = plan.get("emoji_key", emoji_key)

        # Plan-level out of stock check (must be first)
        if plan.get("out_of_stock", False):
            rows.append([
                InlineKeyboardButton(
                    f"{plan['label']} • {plan['price']} Ks • Out of Stock",
                    callback_data=f"plan:{plan_key}",
                    **button_kwargs("reject"),
                )
            ])
            continue

        if product["category"] == "digital":
            if not product.get("enabled", True):
                rows.append([
                    InlineKeyboardButton(
                        f"{plan['label']} • Disabled",
                        callback_data="out_of_stock",
                        **button_kwargs("reject"),
                    )
                ])
                continue
            if product_key not in INVITE_ONLY_PRODUCTS and product_key not in MANUAL_UNLIMITED_PRODUCTS and (product_key, plan_key) not in MANUAL_DELIVERY_PLANS and (product_key, plan_key) not in INVITE_ONLY_PLANS:
                stock = get_cached_digital_stock(product_key, plan_key)
                if stock <= 0:
                    rows.append([
                        InlineKeyboardButton(
                            f"{plan['label']} • {plan['price']} Ks • Out of Stock",
                            callback_data="out_of_stock",
                            **button_kwargs("reject"),
                        )
                    ])
                    continue

        else:
            if not is_game_enabled(product_key) or get_cached_game_stock(product_key) <= 0:
                rows.append([
                    InlineKeyboardButton(
                        f"{plan['label']} • {plan['price']} Ks • Out of Stock",
                        callback_data="out_of_stock",
                        **button_kwargs("reject"),
                    )
                ])
                continue

        rows.append([
            InlineKeyboardButton(
                f"{plan['label']} • {plan['price']} Ks",
                callback_data=f"plan:{plan_key}",
                **button_kwargs(plan_emoji_key),
            )
        ])

    rows.append([
        InlineKeyboardButton(
            "Back to Products",
            callback_data="back_products",
            **button_kwargs("back"),
        )
    ])

    return InlineKeyboardMarkup(rows)


def detail_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Skip / No Note",
                    callback_data="detail_skip",
                    **button_kwargs("skip"),
                )
            ],
            [
                InlineKeyboardButton(
                    "Back to Plans",
                    callback_data="detail_back_plan",
                    **button_kwargs("back"),
                ),
                InlineKeyboardButton(
                    "Cancel",
                    callback_data="detail_cancel",
                    **button_kwargs("cancel"),
                ),
            ],
        ]
    )

def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "KPay",
                    callback_data="pay:kpay",
                    **button_kwargs("kpay"),
                )
            ],
            [
                InlineKeyboardButton(
                    "Wave Pay",
                    callback_data="pay:wave",
                    **button_kwargs("wave"),
                )
            ],
            [
                InlineKeyboardButton(
                    "AYA Pay",
                    callback_data="pay:aya",
                    **button_kwargs("aya"),
                )
            ],
            [
                InlineKeyboardButton(
                    "UAB Pay",
                    callback_data="pay:uab",
                    **button_kwargs("uab"),
                )
            ],
            [
                InlineKeyboardButton(
                    "Back",
                    callback_data="back_plan",
                    **button_kwargs("back"),
                )
            ],
        ]
    )


def payment_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Back to Payment",
                    callback_data="back_payment_methods",
                    **button_kwargs("payment_method"),
                )
            ],
            [
                InlineKeyboardButton(
                    "Back to Plans",
                    callback_data="back_plan",
                    **button_kwargs("back"),
                )
            ],
        ]
    )


def simple_back_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Back",
                    callback_data="back_main",
                    **button_kwargs("back"),
                )
            ]
        ]
    )


def my_orders_keyboard(rows: List[dict]) -> InlineKeyboardMarkup:
    buttons = []

    for o in rows:
        buttons.append([
            InlineKeyboardButton(
                f"{o['plan_label']} • {human_status(o['status'])}",
                callback_data=f"track:{o['order_id']}",
                **button_kwargs("orders"),
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "Refresh",
            callback_data="menu_myorders",
            **button_kwargs("refresh"),
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "Back",
            callback_data="back_main",
            **button_kwargs("back"),
        )
    ])

    return InlineKeyboardMarkup(buttons)

def admin_action_keyboard(order_id: str, category: str, product_key: str = "") -> InlineKeyboardMarkup:
    if category == "digital":
        if product_key == "gemini_ai_pro" or product_key == "canva_pro_edu":
            return InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Invite Check",
                            callback_data=f"auto:{order_id}",
                            **button_kwargs("contact"),
                        ),

                        InlineKeyboardButton(
                            "Approve",
                            callback_data=f"approve:{order_id}",
                            **button_kwargs("success"),
                        ),
                    ],

                    [
                        InlineKeyboardButton(
                            "Reject",
                            callback_data=f"rejectmenu:{order_id}",
                            **button_kwargs("reject"),
                        )
                    ],
                ]
            )

        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Auto Deliver",
                        callback_data=f"auto:{order_id}",
                        **button_kwargs("fast"),
                    ),

                    InlineKeyboardButton(
                        "Manual Deliver",
                        callback_data=f"manual:{order_id}",
                        **button_kwargs("detail"),
                    ),
                ],

                [
                    InlineKeyboardButton(
                        "Reject",
                        callback_data=f"rejectmenu:{order_id}",
                        **button_kwargs("reject"),
                    )
                ],
            ]
        )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Approve",
                    callback_data=f"approve:{order_id}",
                    **button_kwargs("success"),
                ),

                InlineKeyboardButton(
                    "Reject",
                    callback_data=f"rejectmenu:{order_id}",
                    **button_kwargs("reject"),
                ),
            ]
        ]
    )

def reject_reason_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💸 ငွေပမာဏမမှန်", callback_data=f"reject:{order_id}:wrong_amount", **button_kwargs("price"))],
            [InlineKeyboardButton("🖼 Screenshot မရှင်း", callback_data=f"reject:{order_id}:unclear_ss", **button_kwargs("camera"))],
            [InlineKeyboardButton("🚫 Payment မအောင်မြင်", callback_data=f"reject:{order_id}:fake_payment", **button_kwargs("reject"))],
            [InlineKeyboardButton("♻️ Duplicate Order", callback_data=f"reject:{order_id}:duplicate_order", **button_kwargs("refresh"))],
            [InlineKeyboardButton("📝 Other", callback_data=f"reject:{order_id}:other", **button_kwargs("detail"))],
        ]
    )
    
def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Stats",
                    callback_data="admin_gui:stats",
                    **button_kwargs("status"),
                ),
                InlineKeyboardButton(
                    "Stock",
                    callback_data="admin_gui:stock",
                    **button_kwargs("stock"),
                ),
            ],
            [
                InlineKeyboardButton(
                    "Pending",
                    callback_data="admin_gui:pending",
                    **button_kwargs("pending"),
                ),
                InlineKeyboardButton(
                    "Low Stock",
                    callback_data="admin_gui:lowstock",
                    **button_kwargs("outofstock"),
                ),
            ],
            [
                InlineKeyboardButton(
                    "Close",
                    callback_data="admin_gui:close",
                    **button_kwargs("back"),
                )
            ],
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

            current_stock = get_cached_digital_stock(product_key, plan_key)
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
            current_stock = get_cached_game_stock(product_key)
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
    save_user(update.effective_user)
    context.user_data.clear()
    if update.message:
        await send_optional_sticker(update.message, WELCOME_STICKER_ID)
        await update.message.reply_text(
    welcome_text(),
    reply_markup=start_now_keyboard(),
    parse_mode=ParseMode.HTML,
    disable_web_page_preview=True,
        )
    return MENU_STATE
async def start_now_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)
    context.user_data.clear()

    await update.message.reply_text(
        welcome_text(),
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    return MENU_STATE
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(cache_time=1)
    data = query.data

    if data == "menu_shop":
        await safe_edit_message(query, category_text(), reply_markup=category_keyboard())
        return CATEGORY_STATE

    if data == "menu_myorders":
        rows = get_user_orders(query.from_user.id, limit=10)

        if not rows:
            await safe_edit_message(
                query,
                f"{tg_emoji('orders', '📦')} <b>Your Orders</b>\n\n"
                "သင့် order history မရှိသေးပါ။",
                reply_markup=simple_back_main_keyboard(),
            )
            return MENU_STATE

        await safe_edit_message(
            query,
            f"{tg_emoji('orders', '📦')} <b>Your Orders</b>\n\n"
            "ကိုယ်ဝယ်ထားတဲ့ order တွေကိုအောက်မှာပြန်ကြည့်နိုင်ပါတယ် 👇",
            reply_markup=my_orders_keyboard(rows),
        )
        return MENU_STATE

    if data == "menu_contact":
        contact_icon = tg_emoji("contact", "📞")
        await safe_edit_message(
            query,
            f"{contact_icon} <b>Contact Admin</b>\n\n"
            f"{tg_emoji('user', '👤')} Telegram: {escape(CONTACT_USERNAME)}",
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
    await query.answer(cache_time=1)

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
    await query.answer(cache_time=1)
    data = query.data

    if data == "back_main":
        context.user_data.clear()
        await safe_edit_message(query, welcome_text(), reply_markup=main_menu_keyboard())
        return MENU_STATE

    if data.startswith("cat:"):
        category_key = data.split(":", 1)[1]
        context.user_data["category_key"] = category_key
        context.user_data["product_page"] = 0
        await safe_edit_message(
            query,
            products_text(category_key),
            reply_markup=products_keyboard(category_key, page=0),
        )
        return PRODUCT_STATE

    return CATEGORY_STATE


async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(cache_time=1)
    data = query.data

    if data == "back_categories":
        await safe_edit_message(query, category_text(), reply_markup=category_keyboard())
        return CATEGORY_STATE

    if data.startswith("digital_page:"):
        page = int(data.split(":", 1)[1])
        context.user_data["category_key"] = "digital"
        context.user_data["product_page"] = page
        await safe_edit_message(
            query,
            products_text("digital"),
            reply_markup=products_keyboard("digital", page=page),
        )
        return PRODUCT_STATE

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

        await fake_loading(
            query,
            f"{tg_emoji('loading', '⏳')} <b>Opening product...</b>"
        )
        await send_or_edit_product_card(query, product_key, reply_markup=plans_keyboard(product_key))
        return PLAN_STATE

    return PRODUCT_STATE



async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(cache_time=1)
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

        if plan.get("out_of_stock", False):
            await query.answer(
                "ဒီ plan က လက်ရှိ Out of Stock ဖြစ်နေပါတယ်ဗျ။",
                show_alert=True
            )
            return PLAN_STATE

        if product["category"] == "digital":
            if not product.get("enabled", True):
                await query.answer("🔴 ဒီ plan က မရနိုင်သေးပါ။", show_alert=True)
                return PLAN_STATE

        if product["category"] == "digital":
            if not product.get("enabled", True):
                await query.answer("🔴 ဒီ plan က မရနိုင်သေးပါ။", show_alert=True)
                return PLAN_STATE

            if product_key not in INVITE_ONLY_PRODUCTS and product_key not in MANUAL_UNLIMITED_PRODUCTS and (product_key, plan_key) not in MANUAL_DELIVERY_PLANS and get_cached_digital_stock(product_key, plan_key) <= 0:
                await query.answer("🔴 ဒီ plan က stock မရှိတော့ပါ။", show_alert=True)
                return PLAN_STATE
        else:
            if not is_game_enabled(product_key) or get_cached_game_stock(product_key) <= 0:
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
    plan_key = context.user_data.get("plan_key")

    if (product_key, plan_key) in INVITE_ONLY_PLANS and text.lower() == "no":
        await update.message.reply_text("❌ ဒီ plan အတွက် mail မဖြစ်မနေလိုပါတယ်။")
        return DETAIL_STATE

    context.user_data["detail"] = text

    payment_method_icon = tg_emoji("payment_method", "💳")

    await update.message.reply_text(
        f"{payment_method_icon} <b>Payment Method</b>\n\nငွေပေးချေမယ့် method ကိုရွေးပေးပါ 👇",
        reply_markup=payment_keyboard(),
        parse_mode=ParseMode.HTML,
    )

    return PAYMENT_STATE


async def detail_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(cache_time=1)
    data = query.data

    if data == "detail_skip":
        product_key = context.user_data.get("product_key")
        plan_key = context.user_data.get("plan_key")

        if (product_key, plan_key) in INVITE_ONLY_PLANS:
            await query.answer("ဒီ plan အတွက် mail မဖြစ်မနေလိုပါတယ်။", show_alert=True)
            return DETAIL_STATE

        context.user_data["detail"] = "No"
        payment_method_icon = tg_emoji("payment_method", "💳")

        await safe_edit_message(
            query,
            f"{payment_method_icon} <b>Payment Method</b>\n\nငွေပေးချေမယ့် method ကိုရွေးပေးပါ 👇",
            reply_markup=payment_keyboard(),
        )
        return PAYMENT_STATE

    if data == "detail_back_plan":
        product_key = context.user_data.get("product_key")
        if not product_key:
            context.user_data.clear()
            await safe_edit_message(query, welcome_text(), reply_markup=main_menu_keyboard())
            return MENU_STATE

        await safe_edit_message(query, plan_text(product_key), reply_markup=plans_keyboard(product_key))
        return PLAN_STATE

    if data == "detail_cancel":
        context.user_data.clear()
        await safe_edit_message(
            query,
            f"{tg_emoji('cancel', '❌')} <b>Order Cancelled</b>\n\nYour current order has been cancelled.",
            reply_markup=main_menu_keyboard(),
        )
        return MENU_STATE

    return DETAIL_STATE

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(cache_time=1)
    data = query.data

    if data == "back_plan":
        product_key = context.user_data.get("product_key")
        if not product_key:
            await query.message.reply_text("❌ Session error. /start နဲ့ပြန်စပါ။")
            return ConversationHandler.END

        await safe_edit_message(query, plan_text(product_key), reply_markup=plans_keyboard(product_key))
        return PLAN_STATE

    if data == "back_payment_methods":
        payment_method_icon = tg_emoji("payment_method", "💳")

        await safe_edit_message(
            query,
            f"{payment_method_icon} <b>Payment Method</b>\n\nငွေပေးချေမယ့် method ကိုရွေးပေးပါ 👇",
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

    # Build and show the payment screen in a single Telegram edit.
    # The previous fake-loading edit could leave customers stuck on
    # "Preparing payment..." if the final edit failed or Telegram was slow.
    pay_msg = payment_text(
        PAYMENT_ACCOUNTS[payment_key]["label"],
        PAYMENT_ACCOUNTS[payment_key]["text"],
        int(context.user_data["price"]),
        payment_key,
    )

    if is_auto_verify_plan(
        context.user_data.get("product_key", ""),
        context.user_data.get("plan_key", ""),
        payment_key,
    ):
        pay_msg += "\n\n" + kpay_auto_plan_notice_text(
            context.user_data.get("product_name", "-"),
            context.user_data.get("plan_label", "-"),
            int(context.user_data["price"]),
        )
        schedule_auto_order_alarm(context, query.from_user.id)

    payment_message_sent = await safe_edit_message(
        query,
        pay_msg,
        reply_markup=payment_back_keyboard(),
    )

    if not payment_message_sent:
        await query.answer(
            "Payment info မပြနိုင်သေးပါ။ နောက်တစ်ကြိမ်နှိပ်ပေးပါ။",
            show_alert=True,
        )
        return PAYMENT_STATE

    context.user_data["payment_started_at"] = now_str()

    return SCREENSHOT_STATE


async def screenshot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        if update.message:
            await update.message.reply_text(
                f"{tg_emoji('camera', '📷')} <b>Upload Screenshot</b>\n\nPayment screenshot ကို <b>photo</b> နဲ့ပို့ပေးပါ။",
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
        f"{tg_emoji('reject','❌')} <b>Duplicate Order Detected</b>\n\n"
        f"{tg_emoji('id','🆔')} Existing Order: <code>{escape(duplicate['order_id'])}</code>\n"
        f"{tg_emoji('status','📌')} Status: {human_status(duplicate['status'])}",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )

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
    started_at = context.user_data.get("payment_started_at")

    if started_at:
        started_time = datetime.strptime(
            started_at,
            "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=MM_TZ)

        if now_dt() - started_time > timedelta(minutes=5):
            await update.message.reply_text(
                f"{tg_emoji('cancel', '❌')} <b>Payment Time Expired</b>\n\n"
                "ငွေပေးချေမှု ကြာမြင့်ချိန် ၅ မိနစ် ကျော်သွားပါပြီ။ ကျေးဇူးပြု၍ order အသစ် ပြန်တင်ပေးပါ။",
                reply_markup=main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )

            context.user_data.clear()
            return MENU_STATE

    order_insert(data)
    log_action(order_id, user.id, "order_created", "Customer submitted screenshot")

    # Stop any pending auto-order reminder after a screenshot is received.
    context.user_data.pop("auto_alarm_session_id", None)

    is_auto_plan = is_auto_verify_plan(
        data["product_key"],
        data["plan_key"],
        data["payment_key"],
    )

    if is_auto_plan:
        try:
            kpay_info = await extract_kpay_screenshot_info(context, photo_file_id)
            detected_amount = kpay_info.get("amount")
            expected_amount = int(data["price"])
            amount_ok = (
                detected_amount is not None
                and abs(int(detected_amount) - expected_amount) <= AUTO_VERIFY_AMOUNT_TOLERANCE
            )
            name_ok = bool(kpay_info.get("receiver_ok"))

            if not amount_ok:
                if detected_amount is None:
                    # Do not auto-cancel when OCR cannot read the amount at all; this is an OCR failure, not proof of wrong payment.
                    order_update_status(order_id, "waiting_manual_delivery", "OCR could not read amount; not auto-cancelled")
                    log_action(order_id, 0, "auto_verify_amount_unreadable", kpay_info.get("ocr_error", "amount not found"))
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=(
                            f"{tg_emoji('pending', '⏳')} <b>Payment Screenshot Received</b>\n\n"
                            f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                            "Screenshot ထဲက amount ကို OCR မဖတ်နိုင်လို့ auto cancel မလုပ်တော့ပါ။ Admin ကစစ်ပြီး product ပို့ပေးပါမယ်။"
                        ),
                        parse_mode=ParseMode.HTML,
                        reply_markup=main_menu_keyboard(),
                    )
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=(
                            f"{tg_emoji('warning', '⚠️')} <b>KPay Amount OCR Unreadable</b>\n\n"
                            f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                            f"{tg_emoji('price', '💰')} <b>Expected:</b> {expected_amount} Ks\n"
                            "Auto cancel မလုပ်ထားပါ။ စစ်ပြီး deliver လုပ်ပါ။\n\n"
                            f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                    context.user_data.clear()
                    return MENU_STATE

                await auto_reject_order(
                    context,
                    user.id,
                    order_id,
                    "ငွေပမာဏ မကိုက်ပါ",
                    f"လိုအပ်တဲ့ amount က {expected_amount} Ks ဖြစ်ပြီး screenshot ထဲက amount ကို {detected_amount} Ks လို့တွေ့ပါတယ်။",
                    f"amount mismatch detected={detected_amount} expected={expected_amount}",
                )
                context.user_data.clear()
                return MENU_STATE

            if not name_ok:
                await auto_reject_order(
                    context,
                    user.id,
                    order_id,
                    "KPay receiver name / phone မကိုက်ပါ",
                    "Screenshot ထဲမှာ bot ရဲ့ KPay receiver name သို့မဟုတ် phone number ကိုရှင်းရှင်းလင်းလင်း မတွေ့ပါ။",
                    f"receiver mismatch amount={detected_amount} expected={expected_amount}",
                )
                context.user_data.clear()
                return MENU_STATE

            if amount_ok and name_ok:
                account = reserve_auto_account(
                    data["product_key"],
                    data["plan_key"],
                    order_id,
                )

                if account:
                    order_update_status(order_id, "delivered", "KPay Auto Delivered")
                    log_action(
                        order_id,
                        0,
                        "auto_delivered",
                        f"KPay auto verify success | amount={detected_amount} | name_ok={name_ok}",
                    )

                    await send_optional_bot_sticker(
                        context.bot,
                        user.id,
                        SUCCESS_STICKER_ID,
                    )

                    await context.bot.send_message(
                        chat_id=user.id,
                        text=build_auto_delivery_text(data, account, "Products ပို့ပြီးပါပြီ"),
                        parse_mode=ParseMode.HTML,
                        reply_markup=main_menu_keyboard(),
                    )

                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=(
                            f"{tg_emoji('success', '✅')} <b>KPay Auto Verify Success</b>\n\n"
                            f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                            f"{tg_emoji('user', '👤')} <b>Customer:</b> {escape(data['full_name'])}\n"
                            f"{tg_emoji('box', '📦')} <b>Product:</b> {escape(data['product_name'])}\n"
                            f"{tg_emoji('stock', '📦')} <b>Plan:</b> {escape(data['plan_label'])}\n"
                            f"{tg_emoji('price', '💰')} <b>Expected:</b> {expected_amount} Ks\n"
                            f"{tg_emoji('price', '💰')} <b>Detected:</b> {detected_amount} Ks\n"
                            f"{tg_emoji('user', '👤')} <b>KPay Name:</b> OK\n\n"
                            f"{tg_emoji('success', '✅')} <b>Auto delivered to customer.</b>"
                        ),
                        parse_mode=ParseMode.HTML,
                    )

                    await maybe_send_low_stock_alert(context.bot, data["product_key"], data["plan_key"])
                    context.user_data.clear()
                    return MENU_STATE

                order_update_status(order_id, "waiting_manual_delivery", "Auto verify OK but auto stock not found")
                log_action(order_id, 0, "auto_stock_not_found", "KPay verified but stock missing")
                await context.bot.send_message(
                    chat_id=user.id,
                    text=(
                        f"{tg_emoji('pending', '⏳')} <b>Payment Verified</b>\n\n"
                        f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                        "Payment က မှန်ပါတယ်။ ဒါပေမယ့် auto stock မရှိလို့ admin က product ကို manual ပို့ပေးပါမယ်။"
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=main_menu_keyboard(),
                )
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"{tg_emoji('pending', '⚠️')} <b>KPay Verified But Auto Stock Not Found</b>\n\n"
                        f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                        f"{tg_emoji('box', '📦')} <b>Product:</b> {escape(data['product_name'])}\n"
                        f"{tg_emoji('stock', '📦')} <b>Plan:</b> {escape(data['plan_label'])}\n\n"
                        f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                    ),
                    parse_mode=ParseMode.HTML,
                )
                context.user_data.clear()
                return MENU_STATE

        except Exception as e:
            logger.exception("Auto verify failed: %s", e)
            order_update_status(order_id, "waiting_manual_delivery", f"OCR unavailable; do not auto-cancel: {e}")
            log_action(order_id, 0, "auto_verify_ocr_unavailable", str(e))
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    f"{tg_emoji('pending', '⏳')} <b>Payment Screenshot Received</b>\n\n"
                    f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                    "Bot OCR က screenshot ကိုမဖတ်နိုင်သေးတာကြောင့် auto cancel မလုပ်တော့ပါ။ Admin က payment စစ်ပြီး product ကိုပို့ပေးပါမယ်။"
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard(),
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"{tg_emoji('warning', '⚠️')} <b>KPay OCR Unavailable</b>\n\n"
                    f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                    "Payment screenshot ကို bot က မဖတ်နိုင်ပါ။ Auto cancel မလုပ်ထားပါ။\n\n"
                    f"<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>"
                ),
                parse_mode=ParseMode.HTML,
            )
            context.user_data.clear()
            return MENU_STATE

    admin_caption = (
        f"{tg_emoji('success')} <b>New Order Received</b>\n\n"
        f"{order_summary_text(data)}\n\n"
        f"{tg_emoji('user')} <b>Customer:</b> {escape(data['full_name'])}\n"
        f"{tg_emoji('contact')} <b>Username:</b> {escape(data['username'] or '-')}\n"
        f"{tg_emoji('id')} <b>User ID:</b> <code>{data['user_id']}</code>"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=admin_caption,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_action_keyboard(
            order_id,
            data["category"],
            data["product_key"]
        ),
    )

    await send_optional_bot_sticker(
        context.bot,
        user.id,
        SUCCESS_STICKER_ID
    )

    await update.message.reply_text(
        (
            f"{tg_emoji('success')} <b>Order Success</b>\n\n"
            f"{order_summary_text(data)}\n\n"
            f"{tg_emoji('pending')} Admin review ပြီးတာနဲ့ result ပြန်ပို့ပေးပါမယ်"
        ),
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
    await query.answer(cache_time=1)

    if query.from_user.id != ADMIN_ID:
        await query.answer("ဒီ button ကို admin ပဲသုံးလို့ရပါတယ်။", show_alert=True)
        return

    raw = query.data

    if raw.startswith("rejectmenu:"):
        order_id = raw.split(":", 1)[1]
        await query.message.reply_text(
            f"{tg_emoji('reject', '❌')} <b>Reject Reason</b>\n\n{tg_emoji('id', '🆔')} <code>{escape(order_id)}</code>\nReason ရွေးပေးပါ",
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
                f"{tg_emoji('reject', '❌')} <b>Order Rejected</b>\n\n"
f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
f"{tg_emoji('reason', '📌')} <b>Reason:</b> {reason_text}"
            ),
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"{tg_emoji('reject', '❌')} <b>Order Rejected</b>\n\n"
f"{tg_emoji('id', '🆔')} <code>{escape(order_id)}</code>\n"
f"{tg_emoji('reason', '📌')} {reason_text}",
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

        if (order["product_key"], order.get("plan_key", "")) in INVITE_ONLY_PLANS:
            if order["product_key"] == "canva_pro_edu":
                plan_label = order.get("plan_label", "")
                product_label = f"Canva {plan_label}"
            else:
                product_label = "Gemini Ai Pro"

            order_update_status(order_id, "approved", "Invite completed")
            log_action(order_id, query.from_user.id, "invite_approved")
            await disable_query_buttons(query)

            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    f"{tg_emoji('success', '✅')} <b>Invite Ready</b>\n\n"
                    f"Your {escape(product_label)} access is ready.\n"
                    f"{tg_emoji('mail', '📧')} Invite already sent to your email"
                ),
                parse_mode=ParseMode.HTML,
            )

            await query.message.reply_text(
                f"{tg_emoji('success', '✅')} <b>Invite Approved</b>\n\n{tg_emoji('id', '🆔')} <code>{escape(order_id)}</code>\nInvite completed",
                parse_mode=ParseMode.HTML,
            )
            return


        product = PRODUCTS.get(order["product_key"])
        if not product or order["category"] != "game":
            return

        current_stock = get_cached_game_stock(order["product_key"])
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
                f"{tg_emoji('success', '✅')} <b>Order Approved</b>\n\n"
                f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
                f"{tg_emoji('cart', '🛍️')} <b>Product:</b> {escape(order.get('product_name', '-'))}\n"
                f"{tg_emoji('heart', '💖')} Thanks for using Gamepay Hub"
            ),
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"{tg_emoji('success', '✅')} <b>Approved</b>\n\n{tg_emoji('id', '🆔')} <code>{escape(order_id)}</code>\n{tg_emoji('stock', '📦')} Remaining Stock: {new_stock}",
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
        if (order["product_key"], order.get("plan_key", "")) in INVITE_ONLY_PLANS:
            user_mail = (order.get("detail") or "").strip()

            if not user_mail or user_mail.lower() == "no":
                await query.message.reply_text("❌ User mail မရှိသေးပါ။ Customer ဆီက mail တောင်းပေးပါ။")
                return

            await disable_query_buttons(query)

            product_label = "Canva Pro Edu" if order["product_key"] == "canva_pro_edu" else "Gemini Ai Pro"

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"{tg_emoji('mail', '📧')} <b>Invite Required</b>\n\n"
                    f"{tg_emoji('id', '🆔')} <code>{escape(order_id)}</code>\n"
                    f"{tg_emoji('cart', '🛍️')} <b>Product:</b> {escape(product_label)}\n"
                    f"{tg_emoji('mail', '📧')} <b>User Mail:</b> <code>{escape(user_mail)}</code>\n\n"
                    f"Invite ပို့ပြီးရင် original order message က Approve ကိုနှိပ်ပါ"
                ),
                parse_mode=ParseMode.HTML,
            )

            await query.message.reply_text(
                f"{tg_emoji('mail', '📧')} <b>Invite Required</b>\n\n"
                f"{tg_emoji('id', '🆔')} <code>{escape(order_id)}</code>\n"
                f"Invite ပို့ပြီးမှ Approve နှိပ်ပါ",
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
                text=f"{tg_emoji('detail', '✍️')} <b>Manual Delivery Required</b>\n\n<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>",
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
                text=f"{tg_emoji('pending', '⚠️')} <b>Auto Stock Not Found</b>\n\n<code>/deliver {escape(order_id)} Email: xxx Password: yyy</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        order_update_status(order_id, "delivered", "Auto delivered")
        log_action(order_id, query.from_user.id, "auto_delivered")
        await disable_query_buttons(query)

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=build_auto_delivery_text(order, account, "Products ပို့ပြီးပါပြီ"),
            parse_mode=ParseMode.HTML,
        )

        await query.message.reply_text(
            f"{tg_emoji('success', '✅')} <b>Auto Delivered</b>\n\n{tg_emoji('id', '🆔')} <code>{escape(order_id)}</code>",
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
            text=f"{tg_emoji('detail', '✍️')} <b>Manual Delivery Selected</b>\n\n<code>/deliver {escape(order_id)} Email: yourmail@gmail.com Password: 123456</code>",
            parse_mode=ParseMode.HTML,
        )
        return

# =========================================================
# ADMIN GUI PANEL
# =========================================================

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"{tg_emoji('status', '🛠')} <b>Admin Panel</b>\n\nQuick control buttons", 
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_keyboard(),
    )
async def admin_gui_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(cache_time=1)

    if query.from_user.id != ADMIN_ID:
        return

    data = query.data

    if data == "admin_gui:close":
        await safe_edit_message(
            query,
            f"{tg_emoji('success', '✅')} <b>Admin Panel Closed</b>",
            reply_markup=None,
        )
        return

    if data == "admin_gui:stats":
        await fake_loading(query)
        stats = get_stats_summary()

        stats_icon = tg_emoji("status", "📊")
        orders_icon = tg_emoji("orders", "📦")
        success_icon = tg_emoji("success", "✅")
        pending_icon = tg_emoji("pending", "⏳")
        reject_icon = tg_emoji("reject", "❌")
        price_icon = tg_emoji("price", "💰")

        await safe_edit_message(
            query,
            (
                f"{stats_icon} <b>Bot Statistics</b>\n\n"
                f"{orders_icon} <b>Total Orders:</b> {stats['total_orders']}\n"
                f"{success_icon} <b>Delivered / Approved:</b> {stats['delivered_orders']}\n"
                f"{pending_icon} <b>Pending:</b> {stats['pending_orders']}\n"
                f"{reject_icon} <b>Rejected:</b> {stats['rejected_orders']}\n"
                f"{price_icon} <b>Total Sales:</b> {stats['total_sales']} Ks"
            ),
            reply_markup=admin_panel_keyboard(),
        )
        return

    if data == "admin_gui:stock":
        await fake_loading(query)

        lines = [f"{tg_emoji('stock', '📦')} <b>Stock List</b>"]

        for key, p in PRODUCTS.items():
            icon = tg_emoji(p.get("emoji_key", "default"), "✨")

            if p["category"] == "digital":
                if key in INVITE_ONLY_PRODUCTS:
                    lines.append(f"{icon} <b>{escape(p['name'])}</b> → Invite Flow")
                else:
                    lines.append(f"{icon} <b>{escape(p['name'])}</b> → {get_cached_digital_stock(key)}")
            else:
                lines.append(f"{icon} <b>{escape(p['name'])}</b> → {get_cached_game_stock(key)}")

        await safe_edit_message(
            query,
            "\n".join(lines),
            reply_markup=admin_panel_keyboard(),
        )
        return

    if data == "admin_gui:pending":
        await fake_loading(query)
        rows = get_pending_orders(limit=20)

        if not rows:
            await safe_edit_message(
                query,
                f"{tg_emoji('success', '✅')} <b>Pending orders မရှိပါ။</b>",
                reply_markup=admin_panel_keyboard(),
            )
            return

        lines = [f"{tg_emoji('pending', '📋')} <b>Pending Orders</b>"]

        for o in rows:
            lines.append(
                f"\n{tg_emoji('id', '🆔')} <code>{escape(o['order_id'])}</code>\n"
                f"{tg_emoji('cart', '🛍️')} {escape(o['product_name'])}\n"
                f"{tg_emoji('stock', '📦')} {escape(o['plan_label'])}\n"
                f"{tg_emoji('user', '👤')} {escape(o['full_name'])}\n"
                f"{tg_emoji('status', '📌')} {human_status(o['status'])}"
            )

        await safe_edit_message(
            query,
            "\n".join(lines),
            reply_markup=admin_panel_keyboard(),
        )
        return

    if data == "admin_gui:lowstock":
        await fake_loading(query)

        lines = [f"{tg_emoji('pending', '⚠️')} <b>Low Stock Items</b>"]
        found = False

        for key, p in PRODUCTS.items():
            icon = tg_emoji(p.get("emoji_key", "default"), "✨")

            if p["category"] == "digital":
                if key in INVITE_ONLY_PRODUCTS:
                    continue

                total = get_cached_digital_stock(key)
                if total <= LOW_STOCK_THRESHOLD:
                    found = True
                    lines.append(f"{icon} <b>{escape(p['name'])}</b> → {total}")
            else:
                total = get_cached_game_stock(key)
                if total <= LOW_STOCK_THRESHOLD:
                    found = True
                    lines.append(f"{icon} <b>{escape(p['name'])}</b> → {total}")

        if not found:
            lines.append(f"{tg_emoji('success', '✅')} Low stock item မရှိပါ။")

        await safe_edit_message(
            query,
            "\n".join(lines),
            reply_markup=admin_panel_keyboard(),
        )
        return

# =========================================================
# COMMANDS
# =========================================================
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.replace("/broadcast", "", 1).strip()

    if not text:
        await update.message.reply_text("Usage:\n/broadcast Your message")
        return

    broadcast_id = "BC-" + now_dt().strftime("%Y%m%d-%H%M%S")
    users = get_all_users()

    if not users:
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Broadcast ပို့မယ့် user မရှိသေးပါ။\n\n"
        f"{tg_emoji('user','👥')} User တွေ bot ကို /start လုပ်ထားမှ ပို့လို့ရပါတယ်။",
        parse_mode=ParseMode.HTML
    )
    return

    sent = 0
    failed = 0

    for user_id in users:
        try:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text=text,
                disable_web_page_preview=True,
            )

            save_broadcast_message(
                broadcast_id=broadcast_id,
                user_id=user_id,
                message_id=msg.message_id,
            )

            sent += 1
            await asyncio.sleep(0.05)

        except Exception as e:
            failed += 1
            logger.warning("Broadcast failed to %s: %s", user_id, e)

    await update.message.reply_text(
    f"{tg_emoji('success','✅')} <b>Broadcast sent</b>\n\n"
    f"{tg_emoji('id','🆔')} Broadcast ID: <code>{broadcast_id}</code>\n"
    f"{tg_emoji('user','👥')} Users: {len(users)}\n"
    f"{tg_emoji('contact','📤')} Sent: {sent}\n"
    f"{tg_emoji('reject','❌')} Failed: {failed}\n\n"
    f"ပြန်ဖျက်ချင်ရင်:\n"
    f"<code>/delete_broadcast {broadcast_id}</code>",
    parse_mode=ParseMode.HTML,
    )
    
async def delete_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/delete_broadcast BC-YYYYMMDD-HHMMSS"
        )
        return

    broadcast_id = context.args[0].strip()
    rows = get_broadcast_messages(broadcast_id)

    if not rows:
        await update.message.reply_text("❌ Broadcast ID မတွေ့ပါ။")
        return

    deleted = 0
    failed = 0

    for row in rows:
        try:
            await context.bot.delete_message(
                chat_id=row["user_id"],
                message_id=row["message_id"],
            )

            deleted += 1
            await asyncio.sleep(0.05)

        except Exception:
            failed += 1

    delete_broadcast_records(broadcast_id)

    await update.message.reply_text(
        f"🗑 Broadcast delete finished\n\n"
        f"🆔 Broadcast ID: <code>{broadcast_id}</code>\n"
        f"✅ Deleted: {deleted}\n"
        f"❌ Failed: {failed}",
        parse_mode=ParseMode.HTML,
    )

def extract_custom_emoji_ids_from_message(message) -> List[str]:
    entities = message.entities or []
    caption_entities = message.caption_entities or []
    found = []

    for ent in list(entities) + list(caption_entities):
        if ent.type == "custom_emoji" and ent.custom_emoji_id:
            found.append(ent.custom_emoji_id)

    return found


async def emoji_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["waiting_emoji_id"] = True

    await update.message.reply_text(
        "✅ Premium emoji ID ဖမ်းဖို့ အသင့်ဖြစ်ပါပြီ။\n\n"
        "အခု သုံးချင်တဲ့ Premium custom emoji တစ်လုံးကို ဒီ bot ဆီပို့ပါ။\n\n"
        "ဥပမာ CapCut icon သုံးချင်ရင် CapCut အတွက်ထားချင်တဲ့ Premium emoji ကိုပို့ပါ။"
    )


async def emoji_id_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message:
        return

    found = extract_custom_emoji_ids_from_message(update.message)

    if not found:
        if context.user_data.get("waiting_emoji_id"):
            await update.message.reply_text(
                "Premium custom emoji မတွေ့ပါ။\n\n"
                "Normal emoji မဟုတ်ဘဲ Telegram Premium custom emoji ကိုပို့ပါ။"
            )
        return

    context.user_data["waiting_emoji_id"] = False

    await update.message.reply_text(
        "✅ Custom Emoji ID တွေ့ပါပြီ:\n\n"
        + "\n".join([f"<code>{escape(x)}</code>" for x in found])
        + "\n\nRailway Variables ထဲမှာ ဒီ ID ကိုထည့်ပါ။\n\n"
        "ဥပမာ:\n"
        "<code>EMOJI_CAPCUT=ဒီ_ID</code>",
        parse_mode=ParseMode.HTML,
    )

async def deliver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not update.message or not update.message.text:
        return

    command_text = update.message.text.strip()
    order_id = extract_order_id_from_text(command_text)
    order_match = ORDER_ID_RE.search(command_text)

    if not order_id or not order_match:
        await update.message.reply_text("Usage: /deliver ORDER_ID Email: xxx Password: yyy")
        return

    delivery_text = command_text[order_match.end():].strip()
    if not delivery_text:
        await update.message.reply_text("Usage: /deliver ORDER_ID Email: xxx Password: yyy")
        return

    order = order_get(order_id)

    if not order:
        await update.message.reply_text(
            f"❌ Order not found.\n\nစစ်ထားတဲ့ Order ID: <code>{escape(order_id)}</code>\n"
            "Admin message ထဲက Order ID ကို copy နှိပ်ပြီးပြန်သုံးပါ။",
            parse_mode=ParseMode.HTML,
        )
        return

    if order["status"] not in ["pending_payment_review", "waiting_manual_delivery", "code_requested"]:
        await update.message.reply_text("❌ Already processed.")
        return

    canonical_order_id = order["order_id"]
    await context.bot.send_message(
        chat_id=order["user_id"],
        text=(
            f"{tg_emoji('success', '✅')} <b>Account Ready</b>\n\n"
            f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(canonical_order_id)}</code>\n"
            f"<pre>{escape(delivery_text)}</pre>"
        ),
        parse_mode=ParseMode.HTML,
    )

    order_update_status(canonical_order_id, "delivered", "Manually delivered")
    log_action(canonical_order_id, update.effective_user.id, "manually_delivered", delivery_text)
    await update.message.reply_text(
    f"{tg_emoji('success', '✅')} <b>Delivered successfully.</b>",
    parse_mode=ParseMode.HTML,
)

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
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Order not found.",
        parse_mode=ParseMode.HTML
    )
    return

    await context.bot.send_message(
        chat_id=order["user_id"],
        text=(
                 f"{tg_emoji('lock', '🔐')} <b>Login Code Ready</b>\n\n"
            f"{tg_emoji('id', '🆔')} <b>Order ID:</b> <code>{escape(order_id)}</code>\n"
            f"{tg_emoji('key', '🔢')} <b>Code:</b> <code>{escape(code_value)}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )

    order_update_status(order_id, "code_sent", "Admin sent login code")
    log_action(order_id, update.effective_user.id, "code_sent", code_value)
    await update.message.reply_text(f"{tg_emoji('success', '✅')} Login code ပို့ပြီးပါပြီ။")


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
    clear_cache()

    if deleted:
        await update.message.reply_text(f"✅ Deleted: {email}")
    else:
        await update.message.reply_text("❌ Email not found or already used")

async def clear_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /clear_stock PRODUCT_KEY PLAN_KEY")
        return

    product_key, plan_key = context.args[0], context.args[1]
    
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM digital_accounts WHERE product_key = ? AND plan_key = ? AND used = 0", (product_key, plan_key))
        count = cur.rowcount
        conn.commit()
        conn.close()
        clear_cache()
        await update.message.reply_text(f"✅ Cleared {count} unused accounts for {product_key} ({plan_key}).")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def remove_game_stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage:\n/remove_game_stock PRODUCT_KEY QTY")
        return

    product_key = context.args[0].strip()
    qty_text = context.args[1].strip()

    if product_key not in PRODUCTS:
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Invalid product key.",
        parse_mode=ParseMode.HTML
    )
    return

if PRODUCTS[product_key]["category"] != "game":
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} ဒီ command က game product အတွက်ပဲပါ။",
        parse_mode=ParseMode.HTML
    )
    return

try:
    qty = int(qty_text)
except ValueError:
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} QTY must be a number.",
        parse_mode=ParseMode.HTML
    )
    return

if qty <= 0:
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} QTY must be greater than 0.",
        parse_mode=ParseMode.HTML
    )
    return

current_stock = get_cached_game_stock(product_key)
if qty > current_stock:
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Current stock = {current_stock} only.",
        parse_mode=ParseMode.HTML
    )
    return

    new_stock = adjust_game_stock(product_key, -qty)
    log_action(None, update.effective_user.id, "remove_game_stock", f"{product_key} -{qty}")

    await update.message.reply_text(
    f"{tg_emoji('box','📦')} <b>Game Stock Reduced</b>\n\n"
    f"{tg_emoji('shop','🛍️')} <b>Product:</b> {escape(PRODUCTS[product_key]['full_name'])}\n"
    f"{tg_emoji('reject','➖')} <b>Removed:</b> {qty}\n"
    f"{tg_emoji('box','📦')} <b>Remaining:</b> {new_stock}",
    parse_mode=ParseMode.HTML,
    )

async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    rows = get_pending_orders(limit=20)
    if not rows:
        await update.message.reply_text("✅ Pending orders မရှိပါ။")
        return

    lines = [f"{tg_emoji('detail', '📋')} <b>Pending Orders</b>"]

    for o in rows:
        lines.append(
            f"\n{tg_emoji('id', '🆔')} <code>{escape(o['order_id'])}</code>\n"
            f"{tg_emoji('cart', '🛍️')} {escape(o['product_name'])}\n"
            f"{tg_emoji('stock', '📦')} {escape(o['plan_label'])}\n"
            f"{tg_emoji('user', '👤')} {escape(o['full_name'])}\n"
            f"{tg_emoji('status', '📌')} {human_status(o['status'])}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

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

    stats_icon = tg_emoji("status", "📊")
    orders_icon = tg_emoji("orders", "📦")
    success_icon = tg_emoji("success", "✅")
    pending_icon = tg_emoji("pending", "⏳")
    reject_icon = tg_emoji("reject", "❌")
    price_icon = tg_emoji("price", "💰")

    await update.message.reply_text(
        f"{stats_icon} <b>Bot Statistics</b>\n\n"
        f"{orders_icon} <b>Total Orders:</b> {stats['total_orders']}\n"
        f"{success_icon} <b>Delivered / Approved:</b> {stats['delivered_orders']}\n"
        f"{pending_icon} <b>Pending:</b> {stats['pending_orders']}\n"
        f"{reject_icon} <b>Rejected:</b> {stats['rejected_orders']}\n"
        f"{price_icon} <b>Total Sales:</b> {stats['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )

async def sales_today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    start = now_dt().replace(hour=0, minute=0, second=0, microsecond=0)
    end = now_dt().replace(hour=23, minute=59, second=59, microsecond=0)
    result = get_sales_between(start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))

    time_icon = tg_emoji("time", "📅")
    orders_icon = tg_emoji("orders", "📦")
    price_icon = tg_emoji("price", "💰")

    await update.message.reply_text(
        f"{time_icon} <b>Sales Today</b>\n\n"
        f"{orders_icon} <b>Orders:</b> {result['total_orders']}\n"
        f"{price_icon} <b>Total Sales:</b> {result['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )


async def sales_week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    start = now_dt() - timedelta(days=7)
    end = now_dt()
    result = get_sales_between(start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))

    time_icon = tg_emoji("time", "📆")
    orders_icon = tg_emoji("orders", "📦")
    price_icon = tg_emoji("price", "💰")

    await update.message.reply_text(
        f"{time_icon} <b>Sales Last 7 Days</b>\n\n"
        f"{orders_icon} <b>Orders:</b> {result['total_orders']}\n"
        f"{price_icon} <b>Total Sales:</b> {result['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )


async def sales_month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    start = now_dt() - timedelta(days=30)
    end = now_dt()
    result = get_sales_between(start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))

    time_icon = tg_emoji("time", "🗓")
    orders_icon = tg_emoji("orders", "📦")
    price_icon = tg_emoji("price", "💰")

    await update.message.reply_text(
        f"{time_icon} <b>Sales Last 30 Days</b>\n\n"
        f"{orders_icon} <b>Orders:</b> {result['total_orders']}\n"
        f"{price_icon} <b>Total Sales:</b> {result['total_sales']} Ks",
        parse_mode=ParseMode.HTML,
    )
async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    lines = [f"{tg_emoji('stock', '📦')} <b>Stock List</b>"]

    for key, p in PRODUCTS.items():
        icon = tg_emoji(p.get("emoji_key", "default"), "✨")

        if p["category"] == "digital":
            if key in INVITE_ONLY_PRODUCTS:
                lines.append(f"{icon} <b>{escape(p['name'])}</b> → Invite Flow")
            else:
                lines.append(f"{icon} <b>{escape(p['name'])}</b> → {get_cached_digital_stock(key)}")
        else:
            lines.append(f"{icon} <b>{escape(p['name'])}</b> → {get_cached_game_stock(key)}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )

async def lowstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    lowstock_icon = tg_emoji("pending", "⚠️")
    digital_icon = tg_emoji("digital", "💻")
    game_icon = tg_emoji("game", "🎮")
    success_icon = tg_emoji("success", "✅")

    lines = [f"{lowstock_icon} <b>Low Stock Items</b>"]
    found = False

    for key, p in PRODUCTS.items():
        if p["category"] == "digital":
            if key in INVITE_ONLY_PRODUCTS:
                continue

            total = get_cached_digital_stock(key)
            if total <= LOW_STOCK_THRESHOLD:
                found = True
                icon = tg_emoji(p.get("emoji_key", "digital"), "💻")
                lines.append(f"{icon} <b>{escape(p['name'])}</b> → {total}")
        else:
            total = get_cached_game_stock(key)
            if total <= LOW_STOCK_THRESHOLD:
                found = True
                icon = tg_emoji(p.get("emoji_key", "game"), "🎮")
                lines.append(f"{icon} <b>{escape(p['name'])}</b> → {total}")

    if not found:
        lines.append(f"{success_icon} Low stock item မရှိပါ။")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )


async def outofstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    reject_icon = tg_emoji("reject", "❌")
    success_icon = tg_emoji("success", "✅")

    lines = [f"{reject_icon} <b>Out of Stock Items</b>"]
    found = False

    for key, p in PRODUCTS.items():
        if p["category"] == "digital":
            if key in INVITE_ONLY_PRODUCTS:
                continue

            total = get_cached_digital_stock(key)
            if total <= 0:
                found = True
                icon = tg_emoji(p.get("emoji_key", "digital"), "💻")
                lines.append(f"{icon} <b>{escape(p['name'])}</b> → 0")
        else:
            total = get_cached_game_stock(key)
            if total <= 0:
                found = True
                icon = tg_emoji(p.get("emoji_key", "game"), "🎮")
                lines.append(f"{icon} <b>{escape(p['name'])}</b> → 0")

    if not found:
        lines.append(f"{success_icon} Out of stock item မရှိပါ။")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        )


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
    f"{tg_emoji('box','📦')} <b>Game Stock Updated</b>\n\n"
    f"{tg_emoji('shop','🛍️')} <b>Product:</b> {escape(PRODUCTS[product_key]['full_name'])}\n"
    f"{tg_emoji('success','➕')} <b>Added:</b> {qty}\n"
    f"{tg_emoji('box','📦')} <b>Current Stock:</b> {new_stock}",
    parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
    f"{tg_emoji('reject','❌')} Invalid game product.",
    parse_mode=ParseMode.HTML
        )

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
        await update.message.reply_text(
    f"{tg_emoji('reject','❌')} Format မမှန်ပါ။",
    parse_mode=ParseMode.HTML
        )
        return

    product_key, plan_key, email = parts[0], parts[1], parts[2]
    password = " ".join(parts[3:])

    add_digital_account(product_key, plan_key, email, password, extra)
    log_action(None, update.effective_user.id, "add_account", f"{product_key}/{plan_key}/{email}")
    await update.message.reply_text(
    f"{tg_emoji('success','✅')} Digital account added.",
    parse_mode=ParseMode.HTML
    )


async def disable_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/disable_game PRODUCT_KEY")
        return

    product_key = context.args[0].strip()
if product_key not in PRODUCTS or PRODUCTS[product_key]["category"] != "game":
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Invalid game product.",
        parse_mode=ParseMode.HTML
    )
    return

set_game_enabled(product_key, False)
log_action(None, update.effective_user.id, "disable_game", product_key)
await update.message.reply_text(
    f"{tg_emoji('success','✅')} Game product disabled.",
    parse_mode=ParseMode.HTML
)

async def enable_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/enable_game PRODUCT_KEY")
        return

    product_key = context.args[0].strip()
if product_key not in PRODUCTS or PRODUCTS[product_key]["category"] != "game":
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Invalid game product.",
        parse_mode=ParseMode.HTML
    )
    return

set_game_enabled(product_key, True)
log_action(None, update.effective_user.id, "enable_game", product_key)
await update.message.reply_text(
    f"{tg_emoji('success','✅')} Game product enabled.",
    parse_mode=ParseMode.HTML
)

async def addstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(
            "/add_game_stock PRODUCT_KEY QTY\n"
            "/remove_game_stock PRODUCT_KEY QTY\n"
            "/add_account PRODUCT_KEY PLAN_KEY EMAIL PASSWORD | EXTRA\n"
            "/disable_game PRODUCT_KEY\n"
            "/enable_game PRODUCT_KEY\n"
            "/admin"
        )


async def myorders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_user_orders(update.effective_user.id, limit=10)

    if not rows:
    await update.message.reply_text(
        f"{tg_emoji('box','📦')} သင့် order history မရှိသေးပါ။",
        parse_mode=ParseMode.HTML
    )
    return

    lines = [f"{tg_emoji('orders', '📦')} <b>Your Recent Orders</b>"]

    for o in rows:
        lines.append(
            f"\n{tg_emoji('id', '🆔')} <code>{escape(o['order_id'])}</code>\n"
            f"{tg_emoji('cart', '🛍️')} {escape(o['product_name'])}\n"
            f"{tg_emoji('stock', '📦')} {escape(o['plan_label'])}\n"
            f"{tg_emoji('status', '📌')} {human_status(o['status'])}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /track ORDER_ID")
        return

    order = order_get(context.args[0])
    if not order:
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Order not found.",
        parse_mode=ParseMode.HTML
    )
    return

if update.effective_user.id != ADMIN_ID and order["user_id"] != update.effective_user.id:
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} ဒီ order ကိုကြည့်ခွင့်မရှိပါ။",
        parse_mode=ParseMode.HTML
    )
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
    await update.message.reply_text(
        f"{tg_emoji('reject','❌')} Active digital order မတွေ့ပါ။",
        parse_mode=ParseMode.HTML
    )
    return

    order = dict(row)
    order_update_status(order["order_id"], "code_requested", "Customer requested login code")
    log_action(order["order_id"], update.effective_user.id, "customer_code_request")

    await update.message.reply_text(f"{tg_emoji('pending', '⏳')} Code request ကို admin ဆီပို့ပြီးပါပြီ။")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"{tg_emoji('lock', '🔐')} <b>Code Requested</b>\n\n<code>/code {escape(order['order_id'])} 123456</code>",
        parse_mode=ParseMode.HTML,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.message:
        await update.message.reply_text(
            f"{tg_emoji('cancel', '❌')} <b>Order Cancelled</b>\n\nCurrent order cancelled.",
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
    application = (
    Application.builder()
    .token(BOT_TOKEN)
    .defaults(Defaults(parse_mode=ParseMode.HTML))
    .build()
)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU_STATE: [
                MessageHandler(filters.Regex(r"^Start Now$"), start_now_handler),
                CallbackQueryHandler(menu_handler, pattern=r"^menu_"),
                CallbackQueryHandler(track_callback_handler, pattern=r"^track:"),
                CallbackQueryHandler(category_handler, pattern=r"^back_main$"),
            ],
            CATEGORY_STATE: [
                CallbackQueryHandler(category_handler, pattern=r"^(cat:|back_main$)")
            ],
                      PRODUCT_STATE: [
                CallbackQueryHandler(product_handler, pattern=r"^(product:|back_categories$|out_of_stock$|digital_page:)")
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
        fallbacks=[
    CommandHandler("cancel", cancel),
    MessageHandler(filters.Regex("^Start Now$"), start),
],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    application.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern=r"^(approve:|auto:|manual:|rejectmenu:|reject:)",
        )
    )

    application.add_handler(
        CallbackQueryHandler(admin_gui_handler, pattern=r"^admin_gui:")
    )

    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("myorders", myorders_command))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("deliver", deliver_command))
    application.add_handler(CommandHandler("orders", orders_command))
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
    application.add_handler(CommandHandler("clear_stock", clear_stock_command))
    application.add_handler(CommandHandler("disable_game", disable_game_command))
    application.add_handler(CommandHandler("enable_game", enable_game_command))
    application.add_handler(CommandHandler("code", code_command))
    application.add_handler(CommandHandler("admin", admin_panel_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("delete_broadcast", delete_broadcast_command))
    application.add_handler(CommandHandler("emojiid", emoji_id_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, emoji_id_message_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, customer_code_request_handler)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
