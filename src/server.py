import asyncio
import websockets
import base64
import aiohttp
import os
import json
import database as db
import time
import emoji

validVersions = ["1", "1.0.1", "1.1.0"]

# websocket function
async def takeClient(websocket, path):
	isVerified = False
	localUser = ""
	version = ""
	
	async for message in websocket:
		if version == "":
			if message.startswith("version:"):
				sentVersion = message[8:]
				# ignore other versions for now
				if sentVersion in validVersions:
					version = sentVersion
					verificationCode = base64.b64encode(os.urandom(32)).decode("utf-8")
					await websocket.send("verify:" + verificationCode)
					emojiPageSize = 41
					for page in range(0, len(emoji.nameList), emojiPageSize):
						await websocket.send("emoji:" + "/".join(emoji.nameList[page:page + emojiPageSize]) + "/")
					
					# check for newest version
					if version != validVersions[-1]:
						await websocket.send("error:4")
		else:
			if message.startswith("login:"):
				localUser = message[6:]
				async with aiohttp.ClientSession() as session:
					# ask Neos API for their cloud var
					time.sleep(5)
					attempts = 0
					while attempts < 3: # in case the 5 second delay wasn't enough, we are allowed to retry twice more, hoping that the cloud variable will have updated.
						attempts += 1
						async with session.get("https://api.neos.com/api/users/" + localUser + "/vars/U-Psychpsyo.worldReviewVerification") as response:
							jsonData = await response.json()
							if jsonData.get("value", None) == verificationCode:
								isVerified = True
								await websocket.send("loginOk:")
								break
							else:
								if attempts == 3:
									await websocket.send("loginFail:")
									await websocket.send("error:5")
									break
								else:
									time.sleep(2.5)
			elif message.startswith("getReviews:"):
				worldURL = message[11:]
				for review in db.getReviews(worldURL, localUser):
					await websocket.send("showReview:" + review["author"] + "|0|" + str(review["score"]) + "|" + ["0","2","1"][review["localVote"] + 1] + "|" + review["emoji"] + "|" + review["content"])
			
			if isVerified:
				if message.startswith("writeReview:"):
					reviewData = json.loads(message[12:])
					if reviewData["emoji"] not in emoji.fullNameList:
						await websocket.send("error:1")
						break
					if len(reviewData["content"]) > 10000:
						await websocket.send("error:2")
						break
					if not db.writeReview(localUser, reviewData["world"], reviewData["emoji"], reviewData["content"]):
						await websocket.send("error:3")
				elif message.startswith("deleteReview:"):
					db.deleteReview(localUser, message[13:])
				elif message.startswith("voteUp:"):
					voteData = json.loads(message[7:])
					db.upvoteReview(localUser, voteData["author"], voteData["world"])
				elif message.startswith("voteDown:"):
					voteData = json.loads(message[9:])
					db.downvoteReview(localUser, voteData["author"], voteData["world"])
				elif message.startswith("unvote:"):
					voteData = json.loads(message[7:])
					db.removeVote(localUser, voteData["author"], voteData["world"])


loop = asyncio.get_event_loop()

# start websocket and listen
print("Starting websocket.")
start_server = websockets.serve(takeClient, "localhost", 15158)

loop.run_until_complete(start_server)
loop.run_forever()