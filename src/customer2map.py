from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack
import json
import csv

# configuration
DATABASE = './db/customer2map.db'
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['csv'])
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('CUSTOMER2MAP_SETTINGS', silent=True)


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(app.config['DATABASE'])
        sqlite_db.row_factory = sqlite3.Row
        top.sqlite_db = sqlite_db

    return top.sqlite_db

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def geocode(address):
    # TODO -- a more open way of doing this.
    # Here we have to sleep 1 second to make sure google doesn't scold us.
    time.sleep(2)
    vals = {'address': address, 'sensor': 'false'}
    qstr = urllib.urlencode(vals)
    reqstr = "http://maps.google.com/maps/api/geocode/json?%s" % qstr
    _json = simplejson.loads(urllib.urlopen(reqstr).read())
    if _json['status'] == "OK":
        lat = _json['results'][0]['geometry']['location']['lat']
        lng = _json['results'][0]['geometry']['location']['lng']
        error = False
    else:
        lat = 0
        lng = 0
        error = True
    return (error,lat,lng)

@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

@app.route('customers.json')
def show_entries():
    db = get_db()
    cur = db.execute('select * from customers')
    rows = cur.fetchall()
    customers = []
    for row in rows:
        customer = []
        customer['id'] = row.id
        customer['name'] = row.name
        customer['address'] = row.address
        customer['lat'] = row.lat
        customer['lng'] = row.lng
        customer['additionaldata'] = row.additionaldata
        customers.append(customer)
    jsonobj = json.dumps(customers)
    return repr(jsonobj)
    #return render_template('show_entries.html', entries=entries)

@app.route('/upload', methods=['GET','POST'])
def addcustomers():
    if request.method == 'POST' and 'file' in request.files:
        db = get_db()
        file = request.files['file']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], "upload.csv"))
        with open('./uploads/upload.csv.csv', 'rb') as csvfile:
            rows = csv.reader(csvfile, delimiter=',', quotechar='"')
                for row in rows:
                    name = row[0]
                    address = row[1]
                    additionaldata = row[2]
                    err,lat,lng = geodecode(address)
                if err == False:
                    db.execute('insert into entries (name,address,lat,lng,additionaldata) values (?,?,?,?,?)',
                    (name,address,lat,lng,additionaldata))
                    db.commit()
        flash('Customers added successfully.')
        return redirect(url_for('/'))
    else:
        return render_template('uploadcsv.html')

@app.route('/upload', methods=['GET','POST'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run()
