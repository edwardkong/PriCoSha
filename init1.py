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
	password = hashlib.sha256(request.form['password']).hexdigest()

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
	password = hashlib.sha256(request.form['password']).hexdigest()
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
	query = '''SELECT content.ID, content.content_name FROM content NATURAL JOIN person NATURAL JOIN member NATURAL JOIN share
    WHERE person.username = %s
	ORDER BY content.ID DESC
    '''
	cursor.execute(query, (username))
	data = cursor.fetchall()
	print data
	query = '''SELECT group_name FROM person Natural Join friendgroup
	WHERE person.username = %s'''
	cursor.execute(query, (username))
	ownedFG = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data, ownFG=ownedFG)


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
        query = '''SELECT DISTINCT username FROM person Natural Join member
                WHERE member.group_name = group_name
                AND member.username_creator = username_creator
                AND username != %s'''
        cursor.execute(query, username)
        yourFriends = cursor.fetchall()
        print yourFriends
        return render_template('friends.html', urFriends = yourFriends)

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
	print memberFG
	cursor.close()
	print ownedFG
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
	query = '''SELECT DISTINCT username FROM person Natural Join member
			WHERE member.group_name = group_name
			AND member.username_creator = username_creator
			AND username != %s'''
	cursor.execute(query, username)
	yourFriends = cursor.fetchall()
	print yourFriends
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
	print message
	conn.commit()
	cursor.close()
	return redirect(url_for('messages'))

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
