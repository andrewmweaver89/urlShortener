import sqlite3
import uuid
from flask import Flask, render_template, request, g, redirect

# configuration
DATABASE = 'url.db'
BASEPATH = 'localhost:5000/'

app = Flask(__name__)

@app.route("/", methods=['GET'])
def serveform():
    return render_template('form.html')

@app.route("/<path:shortUrl>", methods=['GET'])
def serveLongUrl(shortUrl):
    existingUrl = query_db('select long from url where short = ?', [shortUrl], one=True)

    if existingUrl is None:
        return render_template('404.html')
    else:
        #TODO: need to handle protocols being absent or present
        # for now we just assume they are left off and hardcode the protocol
        longUrl = existingUrl[0]
        return redirect(f'https://{longUrl}')

@app.route("/shorten", methods=['POST'])
def shorten():
    longUrl = request.form['longUrl']

    # TODO: should have redis cache here that looks for longUrl in cache prior to tapping db
    existingUrl = query_db('select short from url where long = ?', [longUrl], one=True)

    shortUrl = shortenAndInsert(longUrl) if existingUrl is None else existingUrl[0]

    # TODO: should be configurable by environment
    basePath = BASEPATH

    # TODO: make template return link not just text
    # in general templates need work :sigh:
    return render_template('shortened.html', shortUrl=f'{basePath}{shortUrl}')

def shortenAndInsert(longUrl):
    shortUrl = uuid.uuid4().hex[0:6]
    uniqueShort = None
    while uniqueShort is None:
        uniqueShort = query_db('select short from url where short = ?', [shortUrl], one=True)
        if uniqueShort is None:
            record = (longUrl, shortUrl)
            create_url(record)
            break
        shortUrl = uuid.uuid4().hex[0:6]

    return shortUrl

def create_url(record):
    db = get_db()
    curr = db.cursor()
    query = 'insert into url(long,short) values (?,?)'
    curr.execute(query, record)
    db.commit()
    curr.close()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run(debug=False)
