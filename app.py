from flask import Flask, jsonify, request
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta
import time
import hmac
import hashlib

app = Flask(__name__)

def format_date_dmy(date_str):
    dt = datetime.strptime(date_str, "%m-%d-%Y")  # input m-d-y
    return dt.strftime("%d-%m-%Y")               # output d-m-y

def get_text(parent, tag):
    el = parent.find(tag)
    return el.text if el is not None else ""

def convert_gmt0_to_gmt7(time_str):
    # ví dụ: "2:00pm"
    dt = datetime.strptime(time_str, "%I:%M%p")
    
    dt = dt + timedelta(hours=7)
    
    return dt.strftime("%H:%M")

# ===== LICENSE CONFIG =====
SECRET = "KyCac_ThachLam_ThachHa_HaTinh_HieuDD"

VALID_ACCOUNTS = [
    "257255068",
    "183819475",
    "159889038",
    "257350472"
]

TIME_WINDOW = 30  # seconds


def verify_signature(account, timestamp, signature):
    msg = f"{account}{timestamp}"
    
    expected = hmac.new(
        SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()

    return expected == signature

@app.route("/check-license", methods=["POST"])
def check_license():
    try:
        data = request.get_json()

        account = data.get("account")
        timestamp = data.get("timestamp")
        signature = data.get("signature")

        # 1. Check thiếu dữ liệu
        if not account or not timestamp or not signature:
            return jsonify({"status": "INVALID_REQUEST"})

        # 2. Check timestamp (chống replay)
        now = int(time.time())
        if abs(now - int(timestamp)) > TIME_WINDOW:
            return jsonify({"status": "EXPIRED"})

        # 3. Verify signature
        if not verify_signature(account, timestamp, signature):
            return jsonify({"status": "INVALID_SIGNATURE"})

        # 4. Check account hợp lệ
        if account not in VALID_ACCOUNTS:
            return jsonify({"status": "INVALID_ACCOUNT"})

        return jsonify({"status": "VALID"})

    except Exception as e:
        return jsonify({"status": "ERROR", "msg": str(e)})

@app.route("/news")
def get_news():
    try:
        input_date = request.args.get("date")
        if not input_date:
            input_date = datetime.now().strftime("%m-%d-%Y")
        
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
        
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/xml",
            "Connection": "keep-alive"
        }, timeout=10)

        if res.status_code != 200:
            return jsonify({"error": "Request failed", "status": res.status_code})

        try:
            root = ET.fromstring(res.content)
        except:
            return jsonify({"error": "Invalid XML", "raw": res.text[:200]})

        result = []

        for event in root.findall("event"):
            country = get_text(event, "country")
            impact   = get_text(event, "impact")
            date    = get_text(event, "date")

            if country == "USD" and impact =="High" and date == input_date:
                result.append({
                    "title": get_text(event, "title"),
                    "time": convert_gmt0_to_gmt7(get_text(event, "time")),
                    "forecast": get_text(event, "forecast"),
                    "previous": get_text(event, "previous")
                })

        msg = f"📅 USD HIGH NEWS ({format_date_dmy(input_date)})\n\n"

        if not result:
            msg += "No news.\n--------------"
        else:
            for item in result:
                msg += f"🕒 {item['time']}\n"
                msg += f"{item['title']}\n"

                if item["forecast"]:
                    msg += f"Forecast: {item['forecast']}\n"

                if item["previous"]:
                    msg += f"Previous: {item['previous']}\n"

                msg += "--------------\n"

        return msg 

    except Exception as e:
        return jsonify({"error": str(e)})
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
