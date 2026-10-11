
from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.get("/")
def home():
    return """
    <!doctype html>
    <html lang="ar" dir="rtl">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FX USER SCANNER</title>
    <body style="background:#080b0a;color:#00ff88;font-family:Arial;text-align:center;padding:25px">
      <h1>FX USER SCANNER</h1>
      <p>فحص أسماء مستخدمي تيك توك</p>
      <input id="names" placeholder="اكتب اليوزرات وافصل بينها بفواصل"
        style="width:90%;padding:12px;box-sizing:border-box">
      <br><br>
      <button onclick="check()" style="padding:12px 25px">افحص</button>
      <pre id="result" style="white-space:pre-wrap;text-align:left"></pre>
      <script>
      async function check(){
        const result=document.getElementById('result');
        result.textContent='جاري الفحص...';
        try {
          const r=await fetch('/check',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({usernames:document.getElementById('names').value.split(',').map(x=>x.trim()).filter(Boolean)})
          });
          const d=await r.json();
          result.textContent=d.results.map(x=>x.username+' : '+x.status).join('\\n');
        } catch(e) { result.textContent='تعذر الاتصال. حاول مرة أخرى.'; }
      }
      </script>
    </body></html>
    """

@app.post("/check")
def check():
    data = request.get_json(silent=True) or {}
    names = data.get("usernames", [])
    if not isinstance(names, list):
        return jsonify(error="Invalid input"), 400

    results = []
    for name in names[:20]:
        name = str(name).strip().lstrip("@")
        if not re.fullmatch(r"[A-Za-z0-9._]{2,24}", name):
            results.append({"username": name, "status": "اسم غير صالح"})
            continue
        try:
            r = requests.get(
                "https://www.tiktok.com/@" + name,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            match = re.search(r'"userInfo"\s*:\s*\{', r.text)
            status = "غير مؤكد — يحتاج تحقق" if r.status_code == 200 else "تعذر الفحص"
            results.append({"username": name, "status": status})
        except requests.RequestException:
            results.append({"username": name, "status": "تعذر الاتصال"})
    return jsonify(results=results)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
