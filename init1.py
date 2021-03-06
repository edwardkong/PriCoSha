#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import datetime

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
					   user='root',
					   password='',
					   db='pricosha',
					   charset='utf8mb4',
					   cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
	return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
	return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	username = request.form['username']
	password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM person WHERE username = %s and password = %s'
	cursor.execute(query, (username, password))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	username = request.form['username']
	password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()
	f_name = request.form['first_name']
	l_name = request.form['last_name']
	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, (username))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	if(data):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (username, password, f_name, l_name))
		conn.commit()
		cursor.close()
		return render_template('index.html')

@app.route('/home')
def home():
	username = session['username']
	cursor = conn.cursor();
	query = '''SELECT content.ID, content.content_name, share.username, timest, member.group_name
	FROM member JOIN share
	ON member.group_name = share.group_name
	JOIN content ON
	share.id = content.id
	WHERE  member.username = %s
	ORDER BY content.ID DESC
    '''
	cursor.execute(query, (username))
	data = cursor.fetchall()
	print(data)

	query = '''SELECT group_name FROM person Natural Join friendgroup
	WHERE person.username = %s'''
	cursor.execute(query, (username))
	ownedFG = cursor.fetchall()

	query = '''SELECT content.ID, content.content_name, username, timest FROM content
	WHERE  content.public
	ORDER BY content.ID DESC'''
	cursor.execute(query)
	public = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data, ownFG=ownedFG, public = public)

@app.route('/posts/<int:post_id>')
def showPost(post_id):
	cursor = conn.cursor();
	query = '''SELECT *
	FROM content
	WHERE id = %s'''
	cursor.execute(query, post_id)
	content = cursor.fetchall()

	query = '''SELECT first_name, last_name
	FROM content JOIN tag ON
	content.id = tag.id JOIN person ON
	tag.username_taggee = person.username
	WHERE content.id = %s and status=1
	'''
	cursor.execute(query, post_id)
	tags = cursor.fetchall()

	query = '''SELECT comment.username, comment.timest, comment_text
	FROM comment JOIN content ON
	comment.id = content.id
	WHERE content.id = %s '''
	cursor.execute(query, post_id)
	comments = cursor.fetchall()

	return render_template('post.html', content = content, tags = tags, comments = comments)

@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor();
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	path = request.form['path']
	content_name = request.form['title']
	public = request.form['is_pub']
	query = '''INSERT into Content(username, timest, file_path, content_name, public)
	values (%s , %s, %s, %s, %s)'''
	cursor.execute(query, (username, timestamp, path, content_name, public))

	if (public == "0"):
		group_name = request.form['friendgroup']
		query = "SELECT Max(id) AS max FROM Content"
		cursor.execute(query)
		id = cursor.fetchone()['max']
		query = '''INSERT into share VALUES( %s, %s, %s)'''
		cursor.execute(query, (id, group_name, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))

@app.route('/logout')
def logout():
	session.pop('username')
	return redirect('/')

@app.route('/friends')
def friends():
        username = session['username']
        cursor = conn.cursor();
        query = '''SELECT DISTINCT username FROM member
                WHERE username != %s
                AND username_creator IN (SELECT username_creator FROM member WHERE username = %s)
                AND group_name IN (SELECT group_name FROM member WHERE username = %s)'''
        cursor.execute(query, (username, username, username))
        yourFriends = cursor.fetchall()
        print(yourFriends)
        return render_template('friends.html', urFriends = yourFriends)

@app.route('/myposts')
def myposts():
        username = session['username']
        cursor = conn.cursor();
        query = '''SELECT * FROM Content
                WHERE username = %s'''
        cursor.execute(query, username)
        yourPosts = cursor.fetchall()
        print(yourPosts)
        return render_template('myposts.html', posts = yourPosts)

@app.route('/friendgroups')
def friendgroups():
	username = session['username']
	cursor = conn.cursor();
	query = '''SELECT group_name FROM person Natural Join friendgroup
	WHERE person.username = %s'''
	cursor.execute(query,username)
	ownedFG = cursor.fetchall()
	query = '''SELECT group_name, username_creator FROM member WHERE username = %s'''
	cursor.execute(query,username)
	memberFG = cursor.fetchall()
	print(memberFG)
	cursor.close()
	print(ownedFG)
	return render_template('friendgroups.html', ownFG = ownedFG, memFG = memberFG)

@app.route('/createFG', methods=['GET', 'POST'])
def createFG():
	username = session['username']
	cursor = conn.cursor();
	gname = request.form["gname"]
	gname = gname.replace(" ", "")
	description = request.form["description"]
	query = '''INSERT into friendgroup values (%s, %s, %s)'''
	cursor.execute(query,(gname,username,description))
	query2 = '''INSERT into member values (%s, %s, %s)'''
	cursor.execute(query2,(username,gname,username))
	conn.commit()
	cursor.close()
	return redirect(url_for('friendgroups'))

@app.route('/messages', methods=['GET', 'POST'])
def messages():
	username = session['username']
	cursor = conn.cursor();
	query = '''SELECT DISTINCT username FROM member
			WHERE username != %s
			AND username_creator IN (SELECT username_creator FROM member WHERE username = %s)
			AND group_name IN (SELECT group_name FROM member WHERE username = %s)'''
	cursor.execute(query, (username, username, username))
	yourFriends = cursor.fetchall()
	print(yourFriends)
	query = '''SELECT sender, timest, message FROM message WHERE recipient = %s ORDER BY timest DESC'''
	cursor.execute(query, username)
	messages = cursor.fetchall()
	query = '''SELECT recipient, timest, message FROM message WHERE sender = %s ORDER BY timest DESC'''
	cursor.execute(query, username)
	sentMessages = cursor.fetchall()
	conn.commit()
	cursor.close()
	return render_template('messages.html', urFriends = yourFriends, messages = messages ,sent = sentMessages)

@app.route('/sendMessage', methods=['GET', 'POST'])
def sendMessage():
	username = session['username']
	cursor = conn.cursor();
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	recipient = request.form['recipient']
	message = request.form['message']
	query = '''INSERT into message(sender, recipient, timest, message) values
	(%s, %s, %s, %s) '''
	cursor.execute(query, (username, recipient, timestamp, message))
	print(message)
	conn.commit()
	cursor.close()
	return redirect(url_for('messages'))

@app.route('/add_friend', methods=['GET', 'POST'])
def addFriend():
	username = session['username']
	cursor = conn.cursor()
	f_name = request.form['first_name']
	l_name = request.form['last_name']
	friendgroup = request.form['friendgroup']
	query = '''SELECT group_name FROM friendgroup WHERE group_name = %s'''
	cursor.execute(query, (friendgroup))
	data = cursor.fetchone()
	if(data):
		query2 = '''SELECT member.username FROM member WHERE member.username IN
		(SELECT person.username FROM person WHERE first_name = %s AND last_name = %s) AND
		 group_name = %s '''
		cursor.execute(query2, (f_name, l_name, friendgroup))
		data2 = cursor.fetchone()
		if(data2):
			error = "This person is already in this friendgroup!"
			print("This person is already in this friendgroup!")
			return render_template('friends.html', error = error)
		else:
			query3 = '''SELECT username FROM person WHERE first_name = %s AND
			last_name = %s
			'''
			cursor.execute(query3, (f_name, l_name))
			data3 = cursor.fetchall();
			if(len(data3) > 1):
				error = "There are multiple people with that name!"
				return render_template('friends.html', error = error)
			elif(len(data3) == 0):
				error = "This person does not exist!"
				return render_template('friends.html', error = error)
			else:
				ins = '''INSERT into member values (%s, %s, %s)'''
				cursor.execute(ins, (data3[0]["username"], friendgroup, username))
				conn.commit()
				cursor.close()
				print(data3[0]["username"])
				return redirect(url_for('friends'))
	else:
		error = "This friendgroup does not exist!"
		print("That didn't work!")
		return render_template('friends.html', error = error)

# <<<<<<< HEAD
@app.route('/tagContent', methods=['GET', 'POST'])
def tagContent():
		username = session['username']
		cursor = conn.cursor()
		username_taggee = request.form['tag']
		content_id = request.form['id']
		timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		query = '''SELECT username FROM person WHERE username = %s'''
		cursor.execute(query, (username_taggee))
		data = cursor.fetchone()
		if(data):
			query = '''SELECT id, username_tagger, username_taggee FROM tag WHERE 
			id = %s AND username_tagger = %s AND username_taggee = %s'''
			cursor.execute(query, (content_id, username, username_taggee))
			data = cursor.fetchone()
			if(data):
				error = "This person has already been tagged!"
				return render_template('home.html', error = error)
			if(username_taggee == username):
				ins = '''INSERT into tag values (%s, %s, %s, %s, %s)'''
				cursor.execute(ins, (content_id, username, username_taggee, timestamp, 1))
				conn.commit()
				cursor.close()
				print("Data has been commited")
				return redirect(url_for('home'))
			else:
				#query to see if content item is visible(public or shared in friendgroup)
				query = '''SELECT id FROM content WHERE public = %s AND id = %s'''
				cursor.execute(query, (1, content_id))
				data = cursor.fetchone()
				if(data):
					ins = '''INSERT into tag values (%s, %s, %s, %s, %s)'''
					cursor.execute(ins, (content_id, username, username_taggee, timestamp, 0))
					conn.commit()
					cursor.close()
					print("Content item was public, so tag was added")
					return redirect(url_for('home'))
				else:
					query = '''SELECT member.username FROM share, member WHERE id = %s AND
					share.group_name = member.group_name AND member.username = %s'''
					cursor.execute(query, (content_id, username_taggee))
					data = cursor.fetchall()
					if(data):
						ins = '''INSERT into tag values (%s, %s, %s, %s, %s)'''
						cursor.execute(ins, (content_id, username, username_taggee, timestamp, 0))
						conn.commit()
						cursor.close()
						print(data)
						print("This content is private, but is shared with the friendgroup of the taggee")
						return redirect(url_for('home'))
					else:
						error = "Can not propose tag, content item not visible to that user"
						return render_template('home.html', error = error )
		else:
			error = "This user does not exist!"
			return render_template('home.html', error = error)



# =======
@app.route('/users')
def users():
	cursor = conn.cursor()
	query = '''SELECT username, first_name, last_name
	FROM person'''
	cursor.execute(query)
	users = cursor.fetchall()
	cursor.close()
	return render_template('users.html', users = users)

@app.route('/managetags')
def managetags():
	username = session['username']
	cursor = conn.cursor()
	query = '''SELECT username_tagger, content.content_name, content.id
	FROM tag JOIN content ON
	tag.id = content.id
	WHERE username_taggee = %s AND status = 0 '''
	cursor.execute(query, username)
	pendingTags = cursor.fetchall()
	cursor.close()
	return render_template('managetags.html', pendingTags = pendingTags)

@app.route('/approve/<post_id>')
def approve(post_id):
	username = session['username']
	query = '''UPDATE tag SET status = 1
	WHERE username_taggee = %s AND id = %s'''
	cursor = conn.cursor()
	cursor.execute(query, (username, post_id))
	conn.commit()
	cursor.close()
	return redirect(url_for('managetags'))

@app.route('/reject/<post_id>')
def reject(post_id):
	username = session['username']
	query = '''DELETE FROM tag WHERE username_taggee = %s AND id = %s'''
	cursor = conn.cursor()
	cursor.execute(query, (username, post_id))
	conn.commit()
	cursor.close()
	return redirect(url_for('managetags'))
# >>>>>>> 0f0d188631d065ca432b3fe22fe52794816e3d17

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
