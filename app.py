
from flask import Flask, request, jsonify
import requests
import re
import os

app = Flask(__name__)

@app.get("/")
def home():
    return """
<!doctype html>
<html lang="ar" dir="rtl">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FX USER SCANNER</title>
<body style="background:#080b0a;color:#00ff88;font-family:Arial;text-align:center;padding:24px">
<h1>FX USER SCANNER</h1>
<p>فحص أسماء مستخدمي تيك توك</p>
<textarea id="names" placeholder="اكتب كل يوزر في سطر"
style="width:95%;height:130px;box-sizing:border-box;padding:12px"></textarea>
<br><br>
<button onclick="check()" style="padding:12px 30px">افحص اليوزرات</button>
<pre id="result" style="white-space:pre-wrap;text-align:right"></pre>
<script>
async function check(){
 const out=document.getElementById('result');
 const names=document.getElementById('names').value.split(/[\\s,]+/).filter(Boolean);
 out.textContent='جاري الفحص...';
 try{
  const r=await fetch('/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usernames:names})});
  const d=await r.json();
  out.textContent=(d.results||[]).map(x=>x.username+' — '+x.status).join('\\n');
 }catch(e){out.textContent='تعذر الاتصال بالخدمة';}
}
</script>
</body></html>
"""

@app.post("/check")
def check():
    data = request.get_json(silent=True) or {}
    names = data.get("usernames", [])
    if not isinstance(names, list):
        return jsonify(results=[]), 400

    results = []
    for raw in names[:20]:
        name = str(raw).strip().lstrip("@")
        if not re.fullmatch(r"[A-Za-z0-9._]{2,24}", name):
            results.append({"username": name, "status": "اسم غير صالح"})
            continue

        try:
            response = requests.get(
                "https://www.tiktok.com/@" + name,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            page = response.text
            if "__UNIVERSAL_DATA_FOR_REHYDRATION__" not in page:
                status = "غير مؤكد — تيك توك لم يعطِ بيانات كافية"
            elif '"userInfo":{"user":' in page or '"userInfo": {"user":' in page:
                status = "قد يكون مأخوذًا — يحتاج تأكيد"
            else:
                status = "غير مؤكد — لا تعتمد على النتيجة وحدها"

            results.append({"username": name, "status": status})
        except requests.RequestException:
            results.append({"username": name, "status": "تعذر الاتصال"})

    return jsonify(results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
