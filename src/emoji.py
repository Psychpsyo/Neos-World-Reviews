import requests

_emojiList = requests.get("https://api.github.com/repos/twitter/twemoji/contents/assets/72x72").json()
nameList = []

for emoji in _emojiList:
	filename = emoji["name"]
	nameList.append(filename[:filename.index(".")])