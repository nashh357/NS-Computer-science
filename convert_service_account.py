import json

with open("serviceAccountKey.json") as f:
    json_data = json.load(f)

json_string = json.dumps(json_data)
print(json_string)  # Copy this output so that the credentials can run on render
