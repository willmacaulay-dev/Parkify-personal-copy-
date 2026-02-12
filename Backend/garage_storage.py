from collections import deque

# last timestamp
last_ts = None

# garage metadata
GARAGES = {
    "1": {
        "name": "Overture Center Garage",
        "lat": 43.0735,
        "lng": -89.3898,
        "capacity": 607
    },
    "2": {
        "name": "State Street Capitol Garage",
        "lat": 43.0750,
        "lng": -89.3880,
        "capacity": 811
    },
    "5": {
        "name": "State Street Campus Garage",
        "lat": 43.0737,
        "lng": -89.3966,
        "capacity": 545
    },
    "6": {
        "name": "Capitol Square North Garage",
        "lat": 43.0776,
        "lng": -89.3825,
        "capacity": 601
    },
    "9": {
        "name": "Government East Garage",
        "lat": 43.0740,
        "lng": -89.3808,
        "capacity": 486
    },
    "18": {
        "name": "South Livingston Street Garage",
        "lat": 43.0802,
        "lng": -89.3737,
        "capacity": 637
    },
    "19": {
        "name": "Wilson Street Garage",
        "lat": 43.0736,
        "lng": -89.3814,
        "capacity": 504
    }
}

CAP = 180
# ring buffers for each garage, max 180 data points
garage_store = {
    g_id: deque(maxlen=CAP)
    for g_id in GARAGES.keys()
}

# garage data tuple: ( garage id, time (unix epoch seconds), # available, # occupied )
def add_sample(tup):

    gid = str(tup[0])

    # ignore unknown garage
    if gid not in garage_store:
        return

    # ignore duplicate (if api data isnt updated yet)
    if (len(garage_store[gid]) == 0) or (garage_store[gid][-1][1] != tup[1]):
        garage_store[gid].append(tup)

# fetch data for one garage (by id)
def get_history(gid):
    return garage_store.get(str(gid), deque())
