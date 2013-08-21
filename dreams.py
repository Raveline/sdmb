from flask import Flask, g, request, session, redirect, url_for, abort, render_template
import sqlite3
import time
from contextlib import closing
import config
from paginate import paginate
import re
from jinja2 import evalcontextfilter, Markup, escape


# App generation
app = Flask(__name__)
app.config.from_object(config)

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

### PAGES ###

# Basic
@app.route('/')
def main_page():
    return show_dreams()

# Main page with pagination
@app.route('/<int:from_nb>')
def show_dreams(from_nb=0):
    dreams = [dict(iddream = row[0], date=row[1], title=row[2], text=row[3]) for row in get_dream_page(from_nb)]
    pagination = paginate(from_nb, app.config['USER_PAGE_SIZE'], get_max_dreams())
    return render_template('dreams.html', 
            dreams=dreams, 
            previous_page = pagination[0],
            next_page = pagination[1])

# Single dream page
@app.route('/dream/<int:dream_id>')
def show_dream(dream_id):
    dream = get_dream_dict(dream_id)
    if dream == None:
        abort(404)
    else:
        return render_template('single_dream.html', dream=dream)

### ADMIN PAGES ###

# Login
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin'))
    # Check if user is connected
    login = request.form['login']
    password = request.form['password']
    if login != app.config['USERNAME'] and password != app.config['PASSWORD']:
        return render_template('login.html', error="Wrong login or password.")
    else:
        session['logged_in'] = True
        return redirect(url_for('admin'))

# Logout
@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('main_page'))

# Main menu
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('admin.html', dreams=get_admin_dreams())

# Add dream
@app.route('/new', methods=['GET'])
def new_dream():
    if not session.get('logged_in'):
        abort(401)
    return render_template('new.html', dream = get_empty_dream_dict)

@app.route('/new', methods=['POST'])
def add_dream():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into dreams (dr_title, dr_text, dr_date) values (?,?,?)', [request.form['title'], request.form['content'], request.form['date']])
    g.db.commit()
    return redirect(url_for('admin'))

@app.route('/remove/<int:dream_id>')
def remove_dream(dream_id):
    if not session.get('logged_in'):
        abort(401)
    delete_dream(dream_id)
    return redirect(url_for('admin'))

@app.route('/modifiy/<int:dream_id>', methods=['GET'])
def modify_dream(dream_id):
    if not session.get('logged_in'):
        abort(401)
    dream = get_dream_dict(dream_id)
    if dream == None:
        abort(404)
    return render_template('new.html', dream = dream)

@app.route('/modify/<int:dream_id>', methods=['POST'])
def act_modify_dream(dream_id):
    if not session.get('logged_in'):
        abort(401)
    update_dream(dream_id, request.form['title'],
            request.form['date'], request.form['content'])
    return redirect(url_for('admin'))

### INTERCEPTORS ###

@app.context_processor
def inject_globals():
    return dict ( author = app.config['DREAMS_MADE_BY'],
            disqus = app.config['DISQUS_SHORTNAME'])

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception=None):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# JINJA2 filters
@app.template_filter('dateformat')
def dateformat(d):
    return d.strftime('%d-%m-%Y')

@app.template_filter('nl2br')
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
            for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

def get_empty_dream_dict():
    return dict(dreamid = None, title="", 
            date=time.strftime("%d/%m/%Y"), content="")

def get_dream_dict(dream_id):
    dream = get_single_dream(dream_id)
    if dream is None:
        return None
    row = dream.fetchall()[0]
    return dict(dreamid = row[0], title=row[1], date=row[2], content=row[3])

# DB shortcuts

def get_admin_dreams():
    cur = g.db.execute('select dr_date, dr_title, dr_id from dreams order by dr_date desc');
    return [dict(date=row[0], title=row[1], iddream=row[2]) for row in cur.fetchall()]

def get_single_dream(dream_id):
    return g.db.execute('select dr_id, dr_title, dr_date, dr_text from dreams where dr_id = ?', [dream_id])

def get_dream_page(from_nb):
    return g.db.execute('select dr_id, dr_date, dr_title, dr_text from dreams order by dr_date desc LIMIT ?, ?', [from_nb, app.config['USER_PAGE_SIZE']])

def update_dream(dream_id, title, date, text):
    g.db.execute('update dreams set dr_title = ?, dr_date = ?, dr_text = ? where dr_id=?', [title, date, text, dream_id])
    g.db.commit()

def delete_dream(dream_id):
    g.db.execute('delete from dreams where dr_id = ?', [dream_id])
    g.db.commit()

def get_max_dreams():
    return g.db.execute('select count(*) from dreams').fetchall()[0][0]

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


# DB init method for deployment

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

if __name__ == '__main__':
    app.run()
