import json
import re
from flask import Flask, jsonify, request, send_from_directory
import requests

app = Flask(__name__, static_folder="static")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9._]{2,24}$")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

@app.get("/")
def home():
    return send_from_directory("static", "index.html")

@app.get("/api/check")
def check_username():
    username = (request.args.get("username") or "").strip().lstrip("@")
    if not USERNAME_RE.fullmatch(username):
        return jsonify({
            "username": username,
            "status": "invalid",
            "message": "صيغة اليوزر غير صحيحة"
        }), 400

    # This is a conservative public-page check, not an official TikTok availability API.
    # Only a positively identified profile is marked as taken. All ambiguous responses
    # remain "unknown" to avoid claiming availability without evidence.
    url = f"https://www.tiktok.com/@{username}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        if response.status_code in (403, 429, 503):
            return jsonify({
                "username": username,
                "status": "unknown",
                "message": "تيك توك منع الطلب أو حدّه؛ تعذّر التحقق"
            })

        if response.status_code >= 500:
            return jsonify({
                "username": username,
                "status": "unknown",
                "message": "خدمة تيك توك غير مستقرة؛ تعذّر التحقق"
            })

        html = response.text
        # Prefer TikTok's structured profile data when present.
        match = re.search(
            r'<script[^>]+id=["\\\']__UNIVERSAL_DATA_FOR_REHYDRATION__["\\\'][^>]*>(.*?)</script>',
            html,
            re.DOTALL
        )
        if match:
            try:
                data = json.loads(match.group(1))
                serialized = json.dumps(data, ensure_ascii=False)
                # Confirm an actual structured user record and matching uniqueId.
                if (
                    f'"uniqueId": "{username}"' in serialized
                    or f'"uniqueId":"{username}"' in serialized
                ):
                    return jsonify({
                        "username": username,
                        "status": "taken",
                        "message": "الحساب موجود في بيانات صفحة تيك توك"
                    })
            except (json.JSONDecodeError, TypeError):
                pass

        # A page response alone, a 404, or missing profile data is not proof of availability.
        return jsonify({
            "username": username,
            "status": "unknown",
            "message": "لم يظهر دليل موثوق كافٍ؛ لا يمكن تأكيد التوفر"
        })

    except requests.RequestException:
        return jsonify({
            "username": username,
            "status": "unknown",
            "message": "تعذّر الاتصال بتيك توك؛ حاول لاحقًا"
        })

@app.get("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
