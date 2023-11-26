from flask import Flask,session, render_template, request, flash,g
from flask_sqlalchemy import SQLAlchemy
import secrets
import sqlite3


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['DATABASE']='instance/data.db'
# Helper function to get a database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db
# Helper function to close the database connection
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
# Register functions to be called before and after each request
app.teardown_appcontext(close_db)

db = SQLAlchemy(app)

class TextEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    german_text = db.Column(db.String(255), nullable=False)
    turkish_text = db.Column(db.String(255), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        german_text = request.form['txtGerman']
        turkish_text = request.form['txtTurkish']

        entry = TextEntry(german_text=german_text, turkish_text=turkish_text)

        try:
            db.session.add(entry)
            db.session.commit()
            flash('Operation successful!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('index.html')
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        db = get_db()
        print('db connected')
        cursor = db.cursor()
        print('cursor reached')
        
        query = """
        SELECT * FROM text_entry
        WHERE german_text LIKE ? OR turkish_text LIKE ?
        """

        # Use '%' to perform a partial match
        search_term = f"%{request.form['search']}%"
        print('search term: '+search_term)
        cursor.execute(query, (search_term, search_term))
        results = cursor.fetchall()

    return render_template('index.html',results=results)

    
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
