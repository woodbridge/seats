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

import os
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

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = libraries, user = g.user)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
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
  return render_template("another.html", name=name)


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')


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
