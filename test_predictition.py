import json

import requests

url = "http://localhost:9000/invocations"
headers = {"Content-Type": "application/json",
           "format": "pandas-split"}
with open("input.json") as data_set:
    data = json.load(data_set)
# print(data)
response_cost = requests.post(url, data=json.dumps(data), headers=headers)
print(response_cost.content)
