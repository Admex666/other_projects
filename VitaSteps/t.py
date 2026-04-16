# read E:\Data\other_projects\VitaSteps\medal\communications.json

import json

with open("medal/communications.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# total messages sent
total_messages = 0
for item in data:
    total_messages += len(item['history'])
print(f"Total messages sent: {total_messages}")

# total words in all messages
total_words = 0
for item in data:
    for message in item['history']:
        total_words += len(message['message'].split())
print(f"Total words in all messages: {total_words}")