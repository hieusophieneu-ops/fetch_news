from flask import Flask, jsonify
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)

def get_text(parent, tag):
    el = parent.find(tag)
    return el.text if el is not None else ""

@app.route("/news")
def get_news():
    try:
        print("CALL API START")
        
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
        
        res = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/xml",
            "Connection": "keep-alive"
        }, timeout=10)

        print("STATUS:", res.status_code)
        print("DATA:", res.text[:200])

        if res.status_code != 200:
            return jsonify({"error": "Request failed", "status": res.status_code})

        try:
            root = ET.fromstring(res.content)
        except:
            return jsonify({"error": "Invalid XML", "raw": res.text[:200]})

        result = []

        for event in root.findall("event"):
            currency = get_text(event, "currency")
            impact   = get_text(event, "impact")

            if currency == "USD" and impact == "High":
                result.append({
                    "title": get_text(event, "title"),
                    "time": get_text(event, "time"),
                    "forecast": get_text(event, "forecast"),
                    "previous": get_text(event, "previous")
                })

        return jsonify(res if len(result) == 0 else result)

    except Exception as e:
        return jsonify({"error": str(e)})
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
