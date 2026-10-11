
from flask import Flask, request, jsonify
import requests
import re
import random
import string

app = Flask(__name__)

PAGE = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FX USER SCANNER</title>
<style>
body{background:#080b0a;color:#00ff88;font-family:Arial;text-align:center;padding:20px}
h1{letter-spacing:2px}
button,select{padding:13px;margin:7px;border:0;border-radius:8px;font-weight:bold}
button{background:#00ff88;color:#07100b}
select,textarea{background:#151b18;color:white;border:1px solid #00ff88}
textarea{box-sizing:border-box;width:100%;padding:12px;border-radius:8px}
#result{white-space:pre-wrap;overflow-wrap:anywhere;text-align:left;direction:ltr;color:white}
</style>
</head>
<body>
<h1>FX USER SCANNER</h1>
<p>مولّد يوزرات تيك توك تلقائيًا</p>

<label>طول اليوزر:</label>
<select id="length">
<option value="3">3 أحرف</option>
<option value="4" selected>4 أحرف</option>
</select>

<label>العدد:</label>
<select id="count">
<option value="10">10</option>
<option value="20" selected>20</option>
<option value="30">30</option>
</select>

<br>
<button onclick="generate()">🎲 ولّد يوزرات</button>
<button onclick="checkNames()">🔎 افحص اليوزرات</button>

<p>اليوزرات:</p>
<textarea id="names" rows="9" placeholder="اضغط ولّد يوزرات"></textarea>
<pre id="result"></pre>

<script>
async function generate(){
 const len=Number(document.getElementById('length').value);
 const count=Number(document.getElementById('count').value);
 const chars='abcdefghijklmnopqrstuvwxyz0123456789';
 const names=new Set();

 while(names.size<count){
  let name='';
  for(let i=0;i<len;i++){
   name+=chars[Math.floor(Math.random()*chars.length)];
  }
  names.add(name);
 }

 document.getElementById('names').value=[...names].join('\n');
 document.getElementById('result').textContent=
 'تم توليد '+names.size+' يوزر. اضغط «افحص اليوزرات».';
}

async function checkNames(){
 const names=document.getElementById('names').value
 .split(/[\s,]+/).filter(Boolean);
 const out=document.getElementById('result');

 if(!names.length){
  out.textContent='اضغط «ولّد يوزرات» أولاً';
  return;
 }

 out.textContent='جاري الفحص...';
 try{
  const r=await fetch('/check',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({usernames:names})
  });
  const d=await r.json();
  out.textContent=(d.results||[])
   .map(x=>x.username+' — '+x.status).join('\n');
 }catch(e){
  out.textContent='تعذر الاتصال بالخدمة';
 }
}
</script>
</body>
</html>
"""

@app.get("/")
def home():
    return PAGE

@app.post("/check")
def check():
    data = request.get_json(silent=True) or {}
    names = data.get("usernames", [])

    if not isinstance(names, list):
        return jsonify(results=[]), 400

    results = []

    for raw in names[:30]:
        name = str(raw).strip().lstrip("@").lower()

        if not re.fullmatch(r"[a-z0-9._]{3,4}", name):
            results.append({
                "username": name,
                "status": "اسم غير صالح"
            })
            continue

        try:
            response = requests.get(
                "https://www.tiktok.com/@" + name,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=8
            )

            page = response.text

            if response.status_code == 429:
                status = "تعذر الفحص — حاول لاحقًا"
            elif response.status_code != 200:
                status = "غير مؤكد — تعذر التحقق"
            elif "__UNIVERSAL_DATA_FOR_REHYDRATION__" not in page:
                status = "غير مؤكد — تيك توك لم يعطِ بيانات كافية"
            elif '"userInfo":{"user":' in page or '"userInfo": {"user":' in page:
                status = "قد يكون مأخوذًا — يحتاج تأكيد"
            else:
                status = "غير مؤكد — لا يمكن تأكيد التوفر"

            results.append({
                "username": name,
                "status": status
            })

        except requests.RequestException:
            results.append({
                "username": name,
                "status": "تعذر الاتصال بتيك توك"
            })

    return jsonify(results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
