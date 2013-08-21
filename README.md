sdmb
====

SMDB as "Sweet Dreams Made By" (xxx).

Basic dream-blog using Flask.

A minimalist blog-like platform to post your dreams.

## Requirements ##

Python, Flask & sqlite3. And that's all.

## Installation ##

I use Apache and modwsgi, but frankly, there are better ways of doing it.
DB link had to be absolute path, and you have to make sure the process running
the app has writing rules on the database.

Following Flask tutorial, I added a method to create the db for you. A simple :

    python
    from dreams import init_db
    init_db()

Should do the trick.

Make sure you've set the DB path in the config.py file, though !

You should also make sure the config.py file has a proper username and password. You'll 
use them to access the admin back-office ("/admin"). You'll also need a secret key to be
able to log-in.

Finally, you'll need a USER_PAGE_SIZE config parameter to set up the number of dreams
displayed to the user.

## Disqus integration ##

If you want to enable comments, add a DISQUS_SHORTNAME in the config file.
Of course, you will need a disqus account.

## Todo list ##

- I have to implement tags. There is some code to display them in the templates, but no table or so.
- Need pagination for admin back-office. And a nicer presentation.
- Need auto-tweeting when a dream is added.

