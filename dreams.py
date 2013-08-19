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

# Basic
@app.route('/')
def main_page():
    return show_dreams(0)

@app.route('/dreams/<int:from_nb>')
def show_dreams(from_nb):
    cur = g.db.execute('select dr_title, dr_text, dr_date from dreams order by dr_date desc LIMIT ?, ?', [from_nb, app.config['USER_PAGE_SIZE']])
    dreams = [dict(title=row[0], text=row[1], date=row[2]) for row in cur.fetchall()]

    pagination = paginate(from_nb, app.config['USER_PAGE_SIZE'], get_max_dreams())
    return render_template('dreams.html', 
            dreams=dreams, 
            previous_page = pagination[0],
            next_page = pagination[1])

###############
# Admin stuff #
###############

# Login
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if session['logged_in']:
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
        abort(401)
    else:
        return render_template('admin.html', dreams=get_admin_dreams())

# Add dream
@app.route('/new', methods=['POST', 'GET'])
def add_dream():
    if not session.get('logged_in'):
        abort(401)
    elif request.method == 'GET':
        today = time.strftime( "%d/%m/%Y" )
        return render_template('new.html', today=today, title="", content="")
    else:
        g.db.execute('insert into dreams (dr_title, dr_text, dr_date) values (?,?,?)', [request.form['title'], request.form['content'], request.form['date']])
        g.db.commit()
        return redirect(url_for('admin'))

# Interceptors

@app.context_processor
def inject_globals():
    return dict ( author = app.config['DREAMS_MADE_BY'] )

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


# DB shortcuts

def get_admin_dreams():
    cur = g.db.execute('select dr_title, dr_id from dreams order by dr_date desc');
    return [dict(title=row[0], date=row[1]) for row in cur.fetchall()]

def get_single_dream(dream_id):
    return g.db.execute('select dr_title, dr_date, dr_text from dreams where dr_id = ?', dream_id)

def update_dream(dream_id, title, date, text):
    g.db.execute('update dreams set dr_title = ?, dr_date = ?, dr_text = ? where dr_id=?', title, date, text, dream_id)

def delete_dream(dream_id):
    g.db.execute('delete from dreams where dr_id = ?', dream_id)

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
