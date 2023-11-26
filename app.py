from flask import Flask,session, render_template, request, flash,g,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
import secrets
import sqlite3
from sqlalchemy.exc import IntegrityError


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
    german_text = db.Column(db.String(255), nullable=False, unique=True)
    turkish_text = db.Column(db.String(255), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        german_text = request.form['txtGerman']
        turkish_text = request.form['txtTurkish']

        # Check if a record with the same german_text already exists
        existing_entry = TextEntry.query.filter_by(german_text=german_text).first()

        if existing_entry:
            flash('This word has already been created.', 'warning')
        else:
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
        cursor = db.cursor()
        
        query = """
        SELECT * FROM text_entry
        WHERE german_text LIKE ? OR turkish_text LIKE ?
        """

        search_term = f"%{request.form['search']}%"
        cursor.execute(query, (search_term, search_term))
        results = cursor.fetchall()

    return render_template('index.html',results=results)

@app.route('/delete_row/<int:row_id>', methods=['POST'])    
def delete_row(row_id):
    try:
        if request.method == 'POST':
         entry_to_delete = TextEntry.query.get(row_id)
        db.session.delete(entry_to_delete)
        db.session.commit()
        flash('Row deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/delete_all', methods=['POST'])    
def delete_all():
    try:
        if request.method == 'POST':
            TextEntry.query.delete()
            db.session.commit()
            flash('All records deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,host='0.0.0.0', port=5000)
