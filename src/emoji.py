import requests

# This uses Github's tree API to get the list of all twemoji in twitter/twemoji/assets/72x72.
# It is necessary since the simple API call for git directory contents clamps the resulting list to 1000 entries which is not enough to get all emoji.
# there is probably a better, more explicit way to write this but I do not care right now.

_emojiList = requests.get("https://api.github.com/repos/twitter/twemoji/git/trees/" +
	next(
		(tree for tree in
			requests.get(
				"https://api.github.com/repos/twitter/twemoji/git/trees/" + 
				next(
					(tree for tree in
						requests.get(
							"https://api.github.com/repos/twitter/twemoji/git/trees/" + 
							requests.get("https://api.github.com/repos/twitter/twemoji/branches/master").json()["commit"]["sha"]
						).json()["tree"]
					if tree["path"] == "assets"),
					None
				)["sha"]
			).json()["tree"]
		if tree["path"] == "72x72"),
		None
	)["sha"]
).json()["tree"]

nameList = []
for emoji in _emojiList:
	filename = emoji["path"]
	nameList.append(filename[:filename.index(".")])