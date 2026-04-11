from flask import Flask, jsonify
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route("/news")
def get_news():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    
    res = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0"
    })

    root = ET.fromstring(res.content)

    result = []

    for event in root.findall("event"):
        currency = event.find("currency").text
        impact   = event.find("impact").text

        if currency == "USD" and impact == "High":
            result.append({
                "title": event.find("title").text,
                "time": event.find("time").text,
                "forecast": event.find("forecast").text,
                "previous": event.find("previous").text
            })

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
