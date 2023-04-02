import requests

# This uses Github's tree API to get the list of all twemoji in jdecked/twemoji/assets/72x72.
# It is necessary since the simple API call for git directory contents clamps the resulting list to 1000 entries which is not enough to get all emoji.
# there is probably a better, more explicit way to write this but I do not care right now.

_emojiList = requests.get("https://api.github.com/repos/jdecked/twemoji/git/trees/" +
	next(
		(tree for tree in
			requests.get(
				"https://api.github.com/repos/jdecked/twemoji/git/trees/" + 
				next(
					(tree for tree in
						requests.get(
							"https://api.github.com/repos/jdecked/twemoji/git/trees/" + 
							requests.get("https://api.github.com/repos/jdecked/twemoji/branches/master").json()["commit"]["sha"]
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
fullNameList = []
for emoji in _emojiList:
	filename = emoji["path"]
	filename = filename[:filename.index(".")]
	fullNameList.append(filename)
	# exclude skin tone / gender sequences from the basic list of emoji to be shown in the picker.
	# TODO: refine this to whitelist things like flags
	if not "-" in filename:
		nameList.append(filename)