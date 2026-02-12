from flask import Flask, jsonify
from flask_cors import CORS
import requests
from datetime import datetime
from dateutil.parser import parse
from zoneinfo import ZoneInfo
import garage_storage as storage
from predictor import predict_available

app = Flask(__name__)
CORS(app)

# in memory cache so frontend refresh doesnt spam upstream
PARKING_CACHE_TTL = 30
parking_cache = {"ts": 0, "data": None}
last_good = {"ts": 0, "data": None}

# default
@app.route('/')
def index():
    return 'Hello, World!'

# health
@app.route('/health', methods=['GET'])
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }, 200


# endpoint for testing purposes, returns parking availability
@app.route('/fetch-parking-availability')
def fetch_external_data():

    # parking api url
    url = 'https://www.cityofmadison.com/parking/data/ramp-availability.json'

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Parkify/1.0; +https://example.com)",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.cityofmadison.com/",
        }
        res = requests.get(url, headers=headers, timeout=10)

        if res.ok:
            parking_data = res.json()
            return jsonify(parking_data)
        else:
            return jsonify({"error": f"request failed -- status code: {res.status_code}"}), res.status_code

    except requests.exceptions.RequestException as e:
        # general errors
        return jsonify({"error": f"error occurred: {str(e)}"}), 500


# endpoint for frontend map
@app.route('/parking', methods=['GET'])
def parking():

    # return cached response if still fresh
    now = int(datetime.utcnow().timestamp())
    if parking_cache["data"] is not None and (now - parking_cache["ts"] < PARKING_CACHE_TTL):
        return jsonify(parking_cache["data"])

    url = 'https://www.cityofmadison.com/parking/data/ramp-availability.json'

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Parkify/1.0; +https://example.com)",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.cityofmadison.com/",
        }
        response = requests.get(url, headers=headers, timeout=10)

        if not response.ok:
            # Serve last known good data if we have it, so the UI doesn't die
            if last_good["data"] is not None:
                payload = dict(last_good["data"])
                payload["stale"] = True
                payload["upstream_status"] = response.status_code
                return jsonify(payload), 200

            return jsonify({"error": f"request failed -- status code: {response.status_code}"}), response.status_code

        res = response.json()
        vacancies = res.get("vacancies", {})
        modified = res.get("modified")  # timestamp

        merged = []
        for g_id, available_now in vacancies.items():
            garage_data = storage.GARAGES.get(str(g_id))
            if not garage_data:
                # skip unincluded garages
                continue

            merged.append({
                "garage_id": str(g_id),
                "name": garage_data["name"],
                "lat": garage_data["lat"],
                "lng": garage_data["lng"],
                "capacity": garage_data.get("capacity"),
                "available_now": available_now,
                "occupied_now": (garage_data.get("capacity") - available_now) if garage_data.get("capacity") is not None else None,
                "predicted_30": predict_available(storage.get_history(str(g_id)), garage_data["capacity"], 30),
                "updated_at": modified,
                "generated_at": datetime.utcnow().isoformat()  # server timestamp
            })

        # ordering data
        merged.sort(key=lambda x: x["name"])

        
        payload = {
            "updated_at": modified,
            "count": len(merged),
            "garages": merged
        }

        # store in cache
        parking_cache["ts"] = now
        parking_cache["data"] = payload
        last_good["ts"] = now
        last_good["data"] = payload

        return jsonify(payload)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"error occurred: {str(e)}"}), 500


# sample parking training data
@app.route('/sample-parking', methods=['GET'])
def sample():

    url = 'https://www.cityofmadison.com/parking/data/ramp-availability.json'

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Parkify/1.0; +https://example.com)",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.cityofmadison.com/",
        }
        res = requests.get(url, headers=headers, timeout=10)

        if res.ok:
            parking_data = res.json()

            # get time, account for time zone and convert to unix epoch seconds
            dt = parse(parking_data["modified"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("America/Chicago"))
            else:
                dt = dt.astimezone(ZoneInfo("America/Chicago"))

            t_epoch = int(dt.timestamp())

            # duplicate timestamp (data not yet updated in api)
            if t_epoch == storage.last_ts:
                return jsonify({
                    "timestamp": parking_data["modified"],
                    "count": 0
                })



            vacancies = parking_data.get("vacancies", {})
            sample_count = 0

            for g_id, available in vacancies.items():

                garage_data = storage.GARAGES.get(str(g_id))
                
                if not garage_data:
                    # skip unincluded garages
                    continue

                capacity = garage_data["capacity"]
                occupied = capacity-available

                storage.add_sample( (str(g_id), t_epoch, available, occupied) )

                sample_count += 1
                

            storage.last_ts = t_epoch

            return jsonify({
                "timestamp": parking_data["modified"],
                "count": sample_count
            })
        else:
            return jsonify({"error": f"request failed -- status code: {res.status_code}"}), res.status_code

    except requests.exceptions.RequestException as e:
        # general errors
        return jsonify({"error": f"error occurred: {str(e)}"}), 500


# return { id, current # available, predicted # available, horizon (prediction time mins), timestamp } 
@app.route('/predict/<gid>')
def predict(gid):
    data = storage.get_history(gid)

    if len(data) == 0:
        return jsonify({"error": "no history for this garage"}), 404

    last_gid, last_t, last_avail, last_occ = data[-1]
    curr = int(last_avail)  # current num available
    ts = int(last_t)  # timestamp
    hor = 30  # prediction time (mins)

    garage_data = storage.GARAGES.get(str(gid))
    if not garage_data:
        return jsonify({"error": "unknown garage id"}), 404

    pred = predict_available(storage.get_history(gid), garage_data["capacity"], hor)

    return jsonify({
        "garage_id": str(gid),
        "current_available": curr,
        "predicted_available": pred,
        "horizon_minutes": hor,
        "timestamp": ts
    })

if __name__ == '__main__':
    app.run()
