import urllib.parse
import requests
import json
import datetime


HEADERS = {"X-API-KEY": "076a4b7f8a8746d88f480a0c994b8b54"}

raceType = {0: "인간", 1: "각성자", 2: "엑소"}
classType = {0: "타이탄", 1: "헌터", 2: "워록"}
activityModeType = {37: "생존", 38: "카운트다운", 72: "격돌", 74: "점령"}


def period2datetime(period):
    return datetime.datetime.strptime(period, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=9)


def split_season(date):
    # 귀찮으니 미구현
    return "7"


def change_data(data, glory):
    activity_time = period2datetime(data["period"])
    info = {
        "instanceId": data['activityDetails']['instanceId'],
        "time": activity_time.__str__(),
        "mode": activityModeType.get(data["activityDetails"]["mode"], data["activityDetails"]["mode"]),
        "kda": f"{data['values']['kills']['basic']['displayValue']}/{data['values']['deaths']['basic']['displayValue']}/{data['values']['assists']['basic']['displayValue']}",
        "efficiency": data['values']['efficiency']['basic']['displayValue'],
        "glory": glory
    }
    return info


def find(data: list, instanceId):
    for info in data:
        if info["instanceId"] == instanceId:
            return True
        else:
            continue
    return False


def save(data, glory, path):
    with open(path, "r", encoding="utf-8") as f:
        ori = json.load(f)
    info = change_data(data, glory)
    activity_time = datetime.datetime.strptime(info["time"], "%Y-%m-%d %H:%M:%S")
    if not ori.get(f"{activity_time.year}/{activity_time.month}/{activity_time.day}"):
        ori[f"{activity_time.year}/{activity_time.month}/{activity_time.day}"] = [info]
    else:
        if find(ori[f"{activity_time.year}/{activity_time.month}/{activity_time.day}"], info["instanceId"]):
            # override recent data
            ori[f"{activity_time.year}/{activity_time.month}/{activity_time.day}"][-1] = info
        else:
            ori[f"{activity_time.year}/{activity_time.month}/{activity_time.day}"].append(info)
    # print("{instanceId}, {time}, {mode}, {kda}, {efficiency}".format(**info))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ori, f, indent=2, ensure_ascii=False)
    return


def save_many(data, path, reset=True):
    if reset:
        ori = {}
    else:
        with open(path, "r", encoding="utf-8") as f:
            ori = json.load(f)
    for info in data:
        activity_time = datetime.datetime.strptime(info["time"], "%Y-%m-%d %H:%M:%S")
        if not ori.get(f"{activity_time.year}/{activity_time.month}/{activity_time.day}"):
            ori[f"{activity_time.year}/{activity_time.month}/{activity_time.day}"] = [info]
        else:
            ori[f"{activity_time.year}/{activity_time.month}/{activity_time.day}"].append(info)
        # print("{instanceId}, {time}, {mode}, {kda}, {efficiency}".format(**info))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ori, f, indent=2, ensure_ascii=False)
    return


def make_info_object(data, glory):
    activity_time = period2datetime(data["period"])
    info = {
        "instanceId": data['activityDetails']['instanceId'],
        "time": activity_time.__str__(),
        "mode": activityModeType.get(data["activityDetails"]["mode"], data["activityDetails"]["mode"]),
        "kda": f"{data['values']['kills']['basic']['displayValue']}/{data['values']['deaths']['basic']['displayValue']}/{data['values']['assists']['basic']['displayValue']}",
        "efficiency": data['values']['efficiency']['basic']['displayValue'],
        "glory": glory if glory else None
    }
    return info


def bungie_response_wrapper(original_func):
    def wrapper_func(*args, **kwargs):
        resp = original_func(*args, **kwargs).json()
        if not resp.get("Response"):
            raise Exception(f"ErrorCode: {resp.get('ErrorCode')}, ErrorStatus: {resp.get('ErrorStatus')}, Message: {resp.get('Message')}")
        return resp.get("Response")
    return wrapper_func


@bungie_response_wrapper
def search_destiny_player(displayName):
    return requests.get(f"https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayer/-1/{urllib.parse.quote(displayName)}", headers=HEADERS)


@bungie_response_wrapper
def get_profile(membershipType, membershipId, components):
    return requests.get(f"https://www.bungie.net/Platform/Destiny2/{membershipType}/Profile/{membershipId}/?components={','.join(components)}", headers=HEADERS)


@bungie_response_wrapper
def get_activity_history(membershipType, membershipId, characterId, count=3, mode=0, page=0):
    data = {"count": count, "mode": mode, "page": page}
    return requests.get(f"https://www.bungie.net/Platform/Destiny2/{membershipType}/Account/{membershipId}/Character/{characterId}/Stats/Activities/", headers=HEADERS, params=data)


def update(displayName):
    _player_info = search_destiny_player(displayName)[0]
    membershipId = _player_info["membershipId"]
    membershipType = _player_info["membershipType"]
    _characters_data = get_profile(membershipType, membershipId, ['200', '202'])
    _characters_id_list = list(_characters_data["characters"]["data"].keys())
    _glory = _characters_data["characterProgressions"]["data"][_characters_id_list[0]]["progressions"]["2679551909"]["currentProgress"]
    for characterId in _characters_id_list:
        try:
            _recent_activity = get_activity_history(membershipType, membershipId, characterId, count=1, mode=69)
        except:
            continue
        _activity_time = period2datetime(_recent_activity.get("activities")[0].get("period")) + datetime.timedelta(hours=9)
        _last_activity_time = datetime.datetime(2019, 7, 1)
        if _activity_time < _last_activity_time:
            continue
        else:
            _last_activity_time = _activity_time
            recent_activity = _recent_activity
    save(recent_activity.get("activities")[0], _glory, "crucible_data.json")
    return


def initializing_all(displayName):
    _player_info = search_destiny_player(displayName)[0]
    membershipId = _player_info["membershipId"]
    membershipType = _player_info["membershipType"]
    _characters_data = get_profile(membershipType, membershipId, ['200', '202'])
    _characters_id_list = list(_characters_data["characters"]["data"].keys())
    _info_list = []
    # 캐릭터별로 최근 100개의 정보 받아오기
    for characterId in _characters_id_list:
        # 경쟁 플레이리스트 기록 (최대 100개) -> list
        try:
            _recent_activities = get_activity_history(membershipType, membershipId, characterId, count=100, mode=69).get("activities")
        except:
            continue
        for _recent_activity in _recent_activities:
            _activity_time = period2datetime(_recent_activity.get("period")) + datetime.timedelta(hours=9)
            # 특정 날짜 이전 기록은 스킵
            if _activity_time < datetime.datetime(2019, 6, 5):
                # print(f"- 7시즌 이전 기록은 건너뜁니다. {_activity_time}")
                continue
            _info_list.append(change_data(_recent_activity, ""))
    _info_list.sort(key=lambda x: x["time"])
    save_many(_info_list, "crucible_data.json", True)
    return


def main():
    with open("player_name", "r", encoding="utf-8") as f:
        player_name = f.read()
    initializing_all(player_name)
    return


if __name__ == "__main__":
    main()
