Running

`pip install -r requirements.txt`
`python server.py`


Postgres Database Account: jrw2190
URL of Web app: http://35.196.112.49:8111


A description of the parts of your original proposal in Part 1 that you implemented, the parts you did not (which hopefully is nothing or something very small), and possibly new features that were not included in the proposal and that you implemented anyway. If you did not implement some part of the proposal in Part 1, explain why.

We implemented all parts of the proposal:

* Browsing libraries
* Buying a seat
* Claiming a seat
* Advertising a seat
* Display advertisements
* Posting a comment
* Making an account / authentication flow

Briefly describe two of the web pages that require (what you consider) the most interesting database operations in terms of what the pages are used for, how the page is related to the database operations (e.g., inputs on the page are used in such and such way to produce database operations that do such and such), and why you think they are interesting.

***Interesting Queries***
The index page uses a interesting query to get data from both the ads table and the seat_offerings table.

  SELECT a.text, so.library_name, so.seat_id
  FROM ads a, seat_offerings so
  WHERE so.seat_offering_id = a.seat_offering_id"

The index page uses this to display a list of advertisements and the seats they are advertising for on the home page. This feature is interesting because it demonstrates gathering the exact data we need from multiple tables in an elegant way.

The view_seat page uses a query to get comments regarding a specific seat in a library.

  SELECT c.text, u.email FROM comments c, users u WHERE c.user_id = u.user_id AND library_name = (%s) AND seat_id = (%s)", library_name, seat_id

This query is used to display all comments about a seat as well as who wrote the comments. This is a fun/interesting feature that we wanted to add because it allows people to share there experiences and feeling for a particular seat without having to own it. It is one of the few feature that connects a user to a specific seat without ever occupying or owning the seat. 
