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


The index page uses a interesting query to get data from both the ads table and the seat_offerings table.

  SELECT a.text, so.library_name, so.seat_id
  FROM ads a, seat_offerings so
  WHERE so.seat_offering_id = a.seat_offering_id"

The index page uses this to display a list of advertisements and the seats they are advertising for on the home page.

We think it's interesting because it demonstrates gathering the exact data we need 
from multiple tables in an elegant way.



