from flask import Flask,session, render_template, request, flash,g,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
import secrets,re,os
import sqlite3
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Engine, delete
from sqlalchemy import Result


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

@app.route('/delete_all', methods=['GET','POST'])    
def delete_all():
    try:
        if request.method == 'GET':
            return render_template('delete_all.html')
        elif request.method=='POST':
           # Get the number of rows before deletion
            rows_before = db.session.query(TextEntry).count()

            # Delete all records from TextEntry table
            db.session.query(TextEntry).delete()

            # Commit the changes to the database
            db.session.commit()

            # Get the number of rows after deletion
            rows_after = db.session.query(TextEntry).count()

            # Calculate the number of rows deleted
            rows_deleted = rows_before - rows_after

            flash(f'{rows_deleted} words deleted successfully!', 'success')
       
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
        print(f'Error: {str(e)}')

    return redirect(url_for('index'))
import requests

@app.route('/themes', methods=['GET','POST'])  
def find_theme_of_word():
    try:
        if request.method == 'GET':
            return render_template('operations.html') 
        elif request.method =='POST':
            # Get the current working directory
            current_dir = os.getcwd()

            file_path_api = 'api_keys.txt'
          
            url = "https://twinword-twinword-bundle-v1.p.rapidapi.com/word_theme/"
            querystring = {"entry":request.form.get('p_word')}
            
            api_key, api_host = read_api_keys(file_path_api)

            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": api_host
            }
  
            response = requests.get(url, headers=headers, params=querystring)
            data =response.json()
            if 'theme' in data:                 
                return render_template('operations.html',themes=data['theme'][:],examples=None)
            else:
                # Handle the case where 'theme' key is not present in the response
                return render_template('operations.html', error_message="Invalid response from the API")

    except requests.exceptions.RequestException as e:
        print(f"Error finding theme of the word: {e}")
        return None

@app.route('/examples', methods=['GET'])  
def find_examples():
    try:            
        if request.method =='GET':

            url = "https://twinword-twinword-bundle-v1.p.rapidapi.com/word_example/"
            querystring = {"entry":request.form.get('p_word')}
            
            file_path_api = 'api_keys.txt'
            api_key, api_host = read_api_keys(file_path_api)

            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": api_host
            }
  
            response = requests.get(url, headers=headers, params=querystring)
            data =response.json()
            if 'example' in data:                 
                return render_template('operations.html',examples=data['example'][:],themes=None)
            else:
                return render_template('operations.html', error_message="Invalid response from the API")

    except requests.exceptions.RequestException as e:
        print(f"Error finding examples: {e}")
        return None

def read_api_keys(file_path_api):
    try:
        # Get the current working directory
        current_dir = os.getcwd()
        print("cUR DIRECTORY: "+current_dir)
        # Construct the full file path
        vocab_training_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        full_file_path = os.path.join(vocab_training_dir, file_path_api)
       
        with open(full_file_path, 'r') as file:
            content = file.read()
            match = re.search(r'"X-RapidAPI-Key":"(.*?)","X-RapidAPI-Host":"(.*?)"', content)
            if match:
                api_key = match.group(1)
                print(api_key)
                api_host = match.group(2)
                print(api_host)
                return api_key, api_host
            else:
                # Handle the case where the pattern is not found in the file
                raise ValueError("API key and host pattern not found in the file")
    except FileNotFoundError:
        # Handle the case where the file is not found
        raise FileNotFoundError(f"File not found: {file_path_api}")
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True,host='0.0.0.0', port=5000)
