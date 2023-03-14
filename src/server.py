import asyncio
import websockets
import base64
import aiohttp
import os
import json
import database as db
import time
import emoji

# websocket function
async def takeClient(websocket, path):
	print("Client connected.")
	isVerified = False
	localUser = ""
	
	# ask client to verify themselves with a new verification key
	verificationCode = base64.b64encode(os.urandom(32)).decode("utf-8")
	print("Sending verify:" + verificationCode)
	await websocket.send("verify:" + verificationCode)
	emojiPageSize = 41
	for page in range(0, len(emoji.nameList), emojiPageSize):
		await websocket.send("emoji:" + str(page / emojiPageSize) + "|" + "/".join(emoji.nameList[page:page + emojiPageSize]))
	
	async for message in websocket:
		print("Received " + message)
		if message.startswith("login:"):
			localUser = message[6:]
			async with aiohttp.ClientSession() as session:
				# ask Neos API for their cloud var
				time.sleep(5)
				attempts = 0
				while attempts < 3: # in case the 5 second delay wasn't enough, we are allowed to retry twice more, hoping that the cloud variable will have updated.
					attempts += 1
					async with session.post("https://api.neos.com/api/readvars", json = [{"ownerId": localUser, "path": "U-Psychpsyo.worldReviewVerification"}]) as response:
						jsonData = await response.json()
						print("Read CloudVar: " + jsonData[0].get("variable", {}).get("value", None))
						if jsonData[0].get("variable", {}).get("value", None) == verificationCode:
							isVerified = True
							print("Sending loginOk:")
							await websocket.send("loginOk:")
							break
						else:
							if attempts == 3:
								print("Sending loginFail:")
								await websocket.send("loginFail:")
								break
							else:
								time.sleep(2.5)
		elif message.startswith("getReviews:"):
			worldURL = message[11:]
			for review in db.getReviews(worldURL, localUser):
				print("Sending showReview:" + review["author"] + "|0|" + str(review["score"]) + "|2|" + review["emoji"] + "|" + review["content"])
				await websocket.send("showReview:" + review["author"] + "|0|" + str(review["score"]) + "|" + ["0","2","1"][review["localVote"] + 1] + "|" + review["emoji"] + "|" + review["content"])
		
		if isVerified:
			if message.startswith("writeReview:"):
				reviewData = json.loads(message[12:])
				db.writeReview(localUser, reviewData["world"], reviewData["emoji"], reviewData["content"])
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