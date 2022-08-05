import requests
import datetime
import statistics

WRITE = False

def main() -> None:
    try:
        print("Enter a username: ", end="")
        name = input()
        process(fetch(name))
    except ValueError as e:
        print(e)

def fetch(name: str) -> tuple:
    """Fetch data using official Reddit APIs"""
     # 0: posts; 1: comments; the tuple contains lists because above 100 elements we have to
     # request the data in multiple parts
    fetched_data = ([], [])
     # The credentials of your app on the Reddit dev site and your Reddit account
    auth = requests.auth.HTTPBasicAuth("<YOUR APP ID>", "<YOUR APP PASSWORD>")
    data = {
        "grant_type": "password",
        "username": "<YOUR ACCOUNT NAME>",
        "password": "<YOUR ACCOUNT PASSWORD>"
    }
    headers = {
        "User-Agent": "Python"
    }
     # We get an access token
    res = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers)
    if not res.status_code == 200:
        raise ValueError(f"{res.status_code}\n{res.reason}")
    token = res.json()["access_token"]
    headers = {
        **headers,
        **{
            "Authorization" : f"bearer {token}"
          }
        }

    params = {
        "limit" : "100"
    }
    while True:
         # Requesting data until we get 0 elements, after the request we start another, requesting data after
         # the last element of the last request
        server_response = requests.get(url=f"https://oauth.reddit.com/user/{name}/submitted", headers=headers, params=params)
        if not server_response.status_code == 200:
            raise ValueError(f"{server_response.status_code}\n{server_response.reason}")
        if len(server_response.json()["data"]["children"]) == 0:
            break
        params["after"] = server_response.json()["data"]["children"][len(server_response.json()["data"]["children"]) - 1]["data"]["name"]
        fetched_data[0].append(server_response.json())
     # If we don't remove "after" from the dictionary, the following will fail
    params.pop("after")
    while True:
         # Like before, just this time we request comments
        server_response = requests.get(url=f"https://oauth.reddit.com/user/{name}/comments", headers=headers, params=params)
        if not server_response.status_code == 200:
            raise ValueError(f"{server_response.status_code}\n{server_response.reason}")
        if len(server_response.json()["data"]["children"]) == 0:
            break
        params["after"] = server_response.json()["data"]["children"][len(server_response.json()["data"]["children"]) - 1]["data"]["name"]
        fetched_data[1].append(server_response.json())
    return fetched_data

def process(data: tuple) -> None:
    """Processing data, printing statistics, writing the days between 2 activities to file on demand in order"""
     # We put the return values from the fetch() function to a set
    activity = set()
    for j in range(len(data[0])):
        for i in data[0][j]["data"]["children"]:
            date_reddit = datetime.datetime.utcfromtimestamp(int(i["data"]["created"])).strftime("%Y-%m-%d")
            if not date_reddit in activity:
                activity.add(date_reddit)
    for j in range(len(data[1])):
        for i in data[1][j]["data"]["children"]:
            date_reddit = datetime.datetime.utcfromtimestamp(int(i["data"]["created"])).strftime("%Y-%m-%d")
            if not date_reddit in activity:
                activity.add(date_reddit)
     # We make a sorted list from the set to make the calculations easier
    list_act = list(activity)
    list_act.sort()
    diffs = []
    with open("diffs.txt", "wt", encoding="UTF-8") as f:
        for i in range(1, len(list_act)):
            delta = datetime.datetime.strptime(list_act[i], "%Y-%m-%d") - datetime.datetime.strptime(list_act[i - 1], "%Y-%m-%d")
            diffs.append(delta.days)
            if WRITE:
                f.write(f"{delta.days}\n")
    print(f"The average number of days between two active days: {statistics.mean(diffs):.2f}; median: {statistics.median(diffs)}; minimum: {min(diffs)}; maximum: {max(diffs)}; last activity on this day: {str(list_act[len(list_act) - 1])[0:10]}")

main()