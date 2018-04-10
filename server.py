#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os, datetime
from functools import wraps
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, flash, session
from psycopg2 import IntegrityError
import bcrypt

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = 'secret'

app.config['TEMPLATES_AUTO_RELOAD'] = True

DATABASEURI = "postgresql://jrw2190:2233@35.227.79.146/proj1part2"

LIBRARY_NAMES = {
    'butler': 'Butler',
    'lehman': 'Lehman',
    'avery': 'Avery',
    'noco': 'NOCO',
    'law': 'Law',
    'math': 'Math',
    'dodge': 'Dodge',
    'kent': 'Kent'

  }

engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

  user_id = session.get('user_id')

  if user_id:
    r = g.conn.execute('SELECT * FROM users WHERE user_id = (%s)', user_id)
    user = r.fetchone()

    if user:
      g.user = user
  else:
      g.user = None



@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

def login_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    if g.user is None:
      flash('login required')
      return redirect('/login')
    else:
      return fn(*args, **kwargs)

  return wrapper


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  cursor = g.conn.execute("SELECT name FROM library")
  libraries = []

  for result in cursor:
    libraries.append(result['name'].lower())  # can also be accessed using result[0]

  cursor.close()

  r = g.conn.execute("SELECT a.text, so.library_name, so.seat_id FROM ads a, seat_offerings so WHERE so.seat_offering_id = a.seat_offering_id")  

  ads = []
  for row in r:
    # TODO: We could parse these from tuples into dicts with named attribute keys but fuck it.
    ads.append(r.fetchone())  

  r.close()

  context = dict(data = libraries, user = g.user, ads=ads)

  return render_template("index.html", **context)


## User Flow

@app.route('/signup')
def signup_form():
  return render_template("signup.html")

@app.route('/signup', methods=['POST'])
def create_account():
  print("---> making an account")

  pass_bytes = bytes(request.form['password'])
  pass_hash = bcrypt.hashpw(pass_bytes, bcrypt.gensalt(14))

  query = "INSERT into users(name, email, password_hash) VALUES (%s, %s, %s) RETURNING user_id"

  trans = g.conn.begin()

  try:
    r = g.conn.execute(query, request.form['name'], request.form['email'], pass_hash)

    user_id = r.fetchone()[0]

    print('---> created new user with id ' + str(user_id))

    session['user_id'] = user_id
    trans.commit()
    return redirect('/')
  except Exception as e:
    print(e)
    trans.rollback()
    flash('Failed to create account, please make sure your email is unique.')
    return redirect('/signup')


@app.route('/library/<name>')
def view_library(name):
  library_name = LIBRARY_NAMES[name]

  r = g.conn.execute('SELECT * FROM seats where library_name = (%s)', library_name)

  seats = []
  for row in r:
    seats.append(r.fetchone())

  r.close()

  r = g.conn.execute("SELECT a.text, so.library_name, so.seat_id FROM ads a, seat_offerings so WHERE so.seat_offering_id = a.seat_offering_id AND so.library_name = (%s)", library_name)

  ads = r.fetchall()

  return render_template("another.html", name=name, seats=seats, ads=ads)

@app.route('/library/<library_name>/<seat_id>')
def view_seat(library_name, seat_id):
  library_name = LIBRARY_NAMES[library_name]

  r = g.conn.execute("SELECT * from seats WHERE library_name = (%s) AND seat_id = (%s)", library_name, seat_id)

  seat_attrs = r.fetchone()

  if not seat_attrs: return "fuck"

  seat = {
    'id': seat_attrs[0],
    'library': seat_attrs[1]
  }

  r = g.conn.execute("SELECT * from seat_offerings WHERE library_name = (%s) AND seat_id = (%s)", library_name, seat_id)
  offering_attrs = r.fetchone()
  if offering_attrs:
    offering = {
      'offering_id': offering_attrs[0],
      'price': offering_attrs[1],
      'date': offering_attrs[2],
      'seat_id': offering_attrs[3],
      'user_id': offering_attrs[4],
      'library_name': offering_attrs[5]
    }
  else:
    offering = None

  if offering:
    r = g.conn.execute("SELECT * from users WHERE user_id = (%s)", offering['user_id'])
    owner_attrs = r.fetchone()

    owner = {
      'user_id': owner_attrs[0],
      'email': owner_attrs[1],
      'name': owner_attrs[2]
    }
  else:
    owner = None


  r = g.conn.execute("SELECT c.text, u.email FROM comments c, users u WHERE c.user_id = u.user_id AND library_name = (%s) AND seat_id = (%s)", library_name, seat_id)

  comments = []

  for row in r:

    c = {
      'text': row[0],
      'email': row[1]
    }

    comments.append(c)

  if g.user:
    session_id = g.user[0]
  else:
    session_id = None

  return render_template('view_seat.html', seat=seat, offering=offering, owner=owner, comments=comments, login_user=session_id)

@app.route('/post_comment', methods=['POST'])
@login_required
def post_comment():
  seat_id = request.form['seat_id']
  library_name = request.form['library_name']
  comment_text = request.form['text']
  user_id = g.user[0]


  if not comment_text or len(comment_text) == 0:
    flash('need to write a comment')
    return redirect("/library/{0}/{1}".format(library_name.lower(), seat_id))

  query = "INSERT INTO comments(library_name, user_id, seat_id, text) VALUES (%s, %s, %s, %s) RETURNING comment_id"

  trans = g.conn.begin()

  try:
    r = g.conn.execute(query, library_name, user_id, seat_id, comment_text)

    comment_id = r.fetchone()[0]

    trans.commit()
    return redirect("/library/{0}/{1}".format(library_name.lower(), seat_id))
  except Exception as e:
    print(e)
    trans.rollback()
    return 'error'

@app.route('/leave', methods=['POST'])
def leave():
    offering  = request.form['offering']
    print offering['offering_id']
    query = "DELETE FROM seat_offerings WHERE offering_id = (%s) RETURNING offering_id"
    trans = g.conn.begin()

    try:
        r = g.conn.execute(query, offering['offering_id'])

        id = r.fetchone()[0]

        print('---> removed seat offering' + str(id))

        trans.commit()
        return redirect('/library/{0}/{1}'.format(library_name.lower(), seat_id))
    except Exception as e:
        print(e)
        trans.rollback()
        return 'failure'


@app.route('/claim', methods=['POST'])
@login_required
def claim_seat():
  seat_id = request.form['seat_id']
  library_name = request.form['library_name']
  price = request.form['price']
  date = datetime.datetime.utcnow()
  user_id = g.user[0] # TODO: convert to dictionary

  query = "INSERT INTO seat_offerings(price, offering_date, seat_id, user_id, library_name) VALUES (%s, %s, %s, %s, %s) RETURNING seat_offering_id"

  trans = g.conn.begin()

  try:
    r = g.conn.execute(query, price, date, seat_id, user_id, library_name)

    id = r.fetchone()[0]

    print('---> created new seat_offering with id ' + str(id))

    trans.commit()
    return redirect("/library/{0}/{1}".format(library_name.lower(), seat_id))
  except Exception as e:
    print(e)
    trans.rollback()
    return 'failure'



  return str(seat_id) + ' ' + library_name

@app.route('/login')
def login():
  return render_template('login.html')

@app.route('/login', methods=['POST'])
def check_login():
  r = g.conn.execute('SELECT * FROM users WHERE email = %s', request.form['email'])
  user = r.fetchone()

  if not user:
    flash('bad email')
    return redirect('/login')
  else:
    if bcrypt.checkpw(bytes(request.form['password']), bytes(user[2])):
      session['user_id'] = user[0]
      flash('logged in!')
      return redirect('/')
    else:
      flash('bad password')
      return redirect('/login')


@app.route('/logout')
def logout():
  session['user_id'] = None
  return redirect('/')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)

  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=True, threaded=threaded)


  run()
