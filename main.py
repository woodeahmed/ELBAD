import flet as ft
import threading
import requests
import re, os, urllib.parse, random, binascii, uuid, time, secrets, string

# نفس الاستيراد المستخدم عندك
try:
    from MedoSigner import Argus, Gorgon, Ladon, md5
except ImportError:
    # لو بتجرب محلي
    os.system('pip install MedoSigner pycryptodome cffi')
    from MedoSigner import Argus, Gorgon, Ladon, md5


# ====== دوال جلب البيانات ======
def sign(params, payload: str = None, sec_device_id: str = "", cookie: str | None = None,
         aid: int = 1233, license_id: int = 1611921764,
         sdk_version_str: str = "2.3.1.i18n", sdk_version: int = 2,
         platform: int = 19, unix: int | None = None):
    x_ss_stub = md5(payload.encode('utf-8')).hexdigest() if payload is not None else None
    if not unix:
        unix = int(time.time())
    return Gorgon(params, unix, payload, cookie).get_value() | {
        "x-ladon": Ladon.encrypt(unix, license_id, aid),
        "x-argus": Argus.get_sign(
            params, x_ss_stub, unix, platform=platform, aid=aid,
            license_id=license_id, sec_device_id=sec_device_id,
            sdk_version=sdk_version_str, sdk_version_int=sdk_version
        )
    }

def get_level_by_uid(uid: str) -> str:
    """
    جلب الليفل باستخدام نفس الفكرة والـ headers تبعك
    (نستخدم uid القادم من أداة login بدل ما نعمل scrape أول)
    """
    url = (
        "https://webcast16-normal-no1a.tiktokv.eu/webcast/user/"
        f"?request_from=profile_card_v2&request_from_scene=1&target_uid={uid}"
        f"&iid={random.randint(1, 10**19)}&device_id={random.randint(1, 10**19)}"
        "&ac=wifi&channel=googleplay&aid=1233&app_name=musical_ly&version_code=300102"
        "&version_name=30.1.2&device_platform=android&os=android&ab_version=30.1.2&ssmix=a"
        "&device_type=RMX3511&device_brand=realme&language=ar&os_api=33&os_version=13"
        f"&openudid={binascii.hexlify(os.urandom(8)).decode()}"
        "&manifest_version_code=2023001020&resolution=1080*2236&dpi=360"
        "&update_version_code=2023001020"
        f"&_rticket={round(random.uniform(1.2, 1.6) * 100000000) * -1}4632"
        "&current_region=IQ&app_type=normal&sys_region=IQ&mcc_mnc=41805"
        "&timezone_name=Asia%2FBaghdad&carrier_region_v2=418&residence=IQ&app_language=ar"
        "&carrier_region=IQ&ac2=wifi&uoo=0&op_region=IQ&timezone_offset=10800"
        "&build_number=30.1.2&host_abi=arm64-v8a&locale=ar&region=IQ&content_language=gu%2C"
        f"&ts={round(random.uniform(1.2, 1.6) * 100000000) * -1}"
        f"&cdid={uuid.uuid4()}&webcast_sdk_version=2920&webcast_language=ar&webcast_locale=ar_IQ"
    )

    headers = {
        'User-Agent': "com.zhiliaoapp.musically/2023001020 (Linux; U; Android 13; ar; RMX3511; "
                      "Build/TP1A.220624.014; Cronet/TTNetVersion:06d6a583 2023-04-17 "
                      "QuicVersion:d298137e 2023-02-13)"
    }

    # نفس توليد توقيع Argus/Gorgon/Ladon
    headers.update(
        sign(
            url.split('?')[1], '', "AadCFwpTyztA5j9L" +
            ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(9)),
            None, 1233
        )
    )
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        m = re.search(r'"default_pattern":"(.*?)"', resp.text)
        if not m:
            return "غير معروف"
        pat = m.group(1)
        # مثال: "المستوى رقم 5"
        if 'المستوى رقم ' in pat:
            return pat.split('المستوى رقم ')[1]
        return pat
    except Exception:
        return "غير معروف"


def get_user_info_via_login(unique_id: str) -> dict | None:
    """
    نفس استدعاء login الذي أرسلته، مع الاحتفاظ بالـ headers والداتا كما هي.
    نستخدم json=data لأن Content-Type application/json.
    """
    url = 'http://tik.report.ilebo.cc/users/login'
    headers = {
        'X-IG-Capabilities': '3brTvw==',
        'User-Agent': 'TikTok 85.0.0.21.100 Android (33/13; 480dpidpi; 1080x2298; HONOR; ANY-LX2; ANY-LX2;)',
        'Accept-Language': 'en-US',
        'Content-Type': 'application/json; charset=utf-8',
        # ملاحظة: عدم ضبط Content-Length يدويًا أفضل مع requests
        'Host': 'tik.report.ilebo.cc',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
    }
    data = {"unique_id": unique_id, "purchaseTokens": []}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        js = r.json()
        return js
    except Exception:
        return None


# ====== واجهة Flet ======
def app_main(page: ft.Page):
    page.title = "ELBAD_OFF"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.window_width = 400
    page.window_height = 700
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "adaptive"

    # ==== الصفحة الأولى (المقدمة) ====
    splash_image = ft.Image(
        src="https://i.postimg.cc/hPH3KXrp/IMG-20250825-000216-706.jpg",
        width=380, height=300, fit=ft.ImageFit.CONTAIN, border_radius=10
    )
    dev_info = ft.Text(
        "𝐓𝐢𝐤𝐭𝐨𝐤      ► elbad_off\n𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐦 ► elbad_off",
        size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF", text_align=ft.TextAlign.CENTER
    )
    btn_contact = ft.ElevatedButton(
        "مراسلة المبرمج", on_click=lambda e: page.launch_url("https://t.me/elbad_off"),
        width=300, height=50,
        style=ft.ButtonStyle(bgcolor="#303F9F", color="#FFFFFF",
                             shape=ft.RoundedRectangleBorder(radius=10))
    )
    def go_next(_):
        # امسح واذهب للواجهة الأساسية
        build_main_ui()
    btn_skip = ft.ElevatedButton(
        "تخطي", on_click=go_next, width=300, height=50,
        style=ft.ButtonStyle(bgcolor="#D32F2F", color="#FFFFFF",
                             shape=ft.RoundedRectangleBorder(radius=10))
    )
    page.add(
        ft.Container(
            content=ft.Column([ft.Container(height=30), splash_image, ft.Container(height=20),
                               dev_info, ft.Container(height=30), btn_contact,
                               ft.Container(height=15), btn_skip, ft.Container(height=30)],
                              alignment="center", horizontal_alignment="center", spacing=10),
            padding=20, expand=True
        )
    )

    # ==== الواجهة الأساسية ====
    def build_main_ui():
        page.controls.clear()

        top_image = ft.Image(
            src="https://i.postimg.cc/2SBvfwjX/image.jpg",
            width=220, height=220, fit=ft.ImageFit.CONTAIN
        )
        username_tf = ft.TextField(
            hint_text="ادخل اليوزر", width=320, text_align=ft.TextAlign.CENTER
        )

        # صندوق النتيجة
        result_text = ft.Text("", color="#FFFFFF", size=14, selectable=True)
        result_box = ft.Container(
            content=result_text, width=350, height=260,
            bgcolor="#111111", border_radius=10, padding=10
        )

        # تشغيل الجلب في ثريد عشان ما يعلق الواجهة
        def fetch_data():
            user = (username_tf.value or "").strip().replace("@", "")
            if not user:
                result_text.value = "⚠️ الرجاء إدخال اليوزر"
                page.update()
                return

            result_text.value = "⏳ جاري جلب البيانات ..."
            page.update()

            # 1) معلومات المستخدم من أداة login (كما أرسلتها)
            js = get_user_info_via_login(user)
            if not js:
                result_text.value = "❌ فشل في جلب بيانات المستخدم"
                page.update()
                return

            try:
                user_data = js['data']['user']['user']
                stats = js['data']['user']['stats']

                uid = user_data['id']
                fm = user_data['uniqueId']
                name = user_data['nickname']
                bio = user_data.get('signature', '') or ''
                sec_uid = user_data.get('secUid', '')
                priv = user_data.get('privateAccount', False)

                folon = stats.get('followingCount', 0)
                folos = stats.get('followerCount', 0)
                lik = stats.get('heartCount', 0)
                vid = stats.get('videoCount', 0)

                # 2) جلب الليفل بنفس طريقتك
                lvl = get_level_by_uid(uid)

                # 3) تنسيق النتيجة كما طلبت (تحت بعض بشكل جميل)
                result_text.value = (
                    "═════════𝚃𝙸𝙺𝚃𝙾𝙺═══════════\n"
                    f"𝐍𝐀𝐌𝐄 ⇾ {name}\n"
                    f"𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 ⇾ {fm}\n"
                    f"𝐅𝐎𝐋𝐋𝐎𝐖𝐄𝐑𝐒 ⇾ {folos}\n"
                    f"𝐅𝐎𝐋𝐋𝐎𝐖𝐈𝐍𝐆 ⇾ {folon}\n"
                    f"𝐋𝐈𝐊𝐄𝐒 ⇾ {lik}\n"
                    f"𝐕𝐈𝐃𝐄𝐎 ⇾ {vid}\n"
                    f"𝐋𝐄𝐕𝐄𝐋 ⇾ {lvl}\n"
                    f"𝐏𝐑𝐈𝐕𝐀𝐓𝐄 ⇾ {priv}\n"
                    f"𝐒𝐄𝐂𝐔𝐈𝐃 ⇾ {sec_uid}\n"
                    f"𝐁𝐈𝐎 ⇾ {bio}\n"
                    f"𝐔𝐑𝐋 ⇾ https://www.tiktok.com/@{fm}\n"
                    "═════════𝚃𝙸𝙺𝚃𝙾𝙺═══════════"
                )
                page.update()
            except Exception:
                result_text.value = "❌ خطأ في تحليل استجابة السيرفر"
                page.update()

        def on_start_click(_):
            threading.Thread(target=fetch_data, daemon=True).start()

        start_btn = ft.ElevatedButton(
            "Start", on_click=on_start_click, width=220, height=48,
            style=ft.ButtonStyle(
                bgcolor="#4CAF50", color="#FFFFFF",
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )

        page.add(
            ft.Column(
                [top_image, ft.Container(height=10), username_tf, ft.Container(height=8),
                 start_btn, ft.Container(height=14), result_box],
                alignment="center", horizontal_alignment="center", spacing=10
            )
        )
        page.update()

    # انتهى

# تشغيل كتطبيق ويب (مفيد للتجربة والـ Replit) وأيضًا الباكر يبني APK
ft.app(target=app_main, view=ft.WEB_BROWSER, port=5000)
