import sqlite3

# database connection
con = sqlite3.connect("database.db", check_same_thread = False)
cur = con.cursor()

# Initializes the Database
def createDatabase():
	cur.execute("""CREATE TABLE reviews(
		id INTEGER PRIMARY KEY,
		author TEXT NOT NULL,
		world TEXT NOT NULL,
		emoji TEXT NOT NULL,
		content TEXT NOT NULL,
		UNIQUE (author, world)
	)""")
	
	cur.execute("""CREATE TABLE votes(
		id INTEGER PRIMARY KEY,
		user TEXT NOT NULL,
		review INTEGER NOT NULL,
		value INTEGER NOT NULL,
		FOREIGN KEY (review) REFERENCES reviews (id) ON DELETE CASCADE,
		UNIQUE (user, review)
	)""")
	
	con.commit()

def getReviews(world, localUser):
	for review in cur.execute("""SELECT
		r.author,
		r.world,
		r.emoji,
		r.content,
		(SELECT SUM(value) FROM votes v WHERE v.review = r.id) AS score,
		(SELECT value FROM votes v WHERE v.user = ? and v.review = r.id) AS localVote
		FROM reviews r WHERE r.world = ?""", (localUser, world)):
		yield {
			"author": review[0],
			"world": review[1],
			"emoji": review[2],
			"content": review[3],
			"score": review[4] or 0,
			"localVote": review[5] or 0
		}

def writeReview(user, world, emoji, content):
	cur.execute("INSERT OR IGNORE INTO reviews (author, world, emoji, content) VALUES (?, ?, ?, ?)", (user, world, emoji, content))
	if cur.lastrowid == 0:
		return False
	cur.execute("INSERT OR IGNORE INTO votes (user, review, value) VALUES (?, ?, 1)", (user, cur.lastrowid))
	con.commit()
	return True

def deleteReview(user, world):
	# in theory the ON DELETE CASCADE would make this unnecessary but it turned out to not work so we need to manually delete the review votes.
	cur.execute("DELETE FROM votes WHERE review = (SELECT id FROM reviews WHERE author = ? AND world = ?)", (user, world))
	cur.execute("DELETE FROM reviews WHERE author = ? AND world = ?", (user, world))
	con.commit()

def upvoteReview(user, reviewAuthor, reviewWorld):
	cur.execute("INSERT OR REPLACE INTO votes (review, user, value) SELECT id, ?, 1 FROM reviews WHERE author = ? and world = ?", (user, reviewAuthor, reviewWorld))
	con.commit()

def downvoteReview(user, reviewAuthor, reviewWorld):
	cur.execute("INSERT OR REPLACE INTO votes (review, user, value) SELECT id, ?, -1 FROM reviews WHERE author = ? and world = ?", (user, reviewAuthor, reviewWorld))
	con.commit()

def removeVote(user, reviewAuthor, reviewWorld):
	cur.execute("DELETE FROM votes WHERE user = ? AND review IN (SELECT id FROM reviews WHERE author = ? and world = ?)", (user, reviewAuthor, reviewWorld))
	con.commit()