from flask import Flask, jsonify,session, render_template, request, flash,g,redirect,url_for
from flask_sqlalchemy import SQLAlchemy,pagination
import secrets,re,os
import sqlite3
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, func,or_,and_
from sqlalchemy import Result
from sqlalchemy import Column, Integer, String
# from db_model import Idioms

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask import current_app
import random

app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_hex(16) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['DATABASE'] = 'instance\data.db'

db = SQLAlchemy(app)

# Create the SQLAlchemy instance

class LanguageData(db.Model):
    __tablename__ = 'language_data'
    id = db.Column(db.Integer, primary_key=True, index=True)
    level = db.Column(db.String, index=True)
    german_word = db.Column(db.String, unique=True, index=True)
    english_word = db.Column(db.String)
    german_example = db.Column(db.String)
    english_example = db.Column(db.String)
    in_dictionary = db.Column(db.Boolean)
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    play_date = db.Column(db.DateTime, nullable=False)
# bio table
class BioGuess(db.Model):
    __tablename__ = 'bio_guess'
    id = db.Column(db.Integer, primary_key=True, index=True)
    person_name = db.Column(db.String, unique=True)
    nationality = db.Column(db.String)
    short_bio_en = db.Column(db.String)
    short_bio_de = db.Column(db.String)
class Idioms(db.Model):
    __tablename__ = 'idioms'
    id = db.Column(db.Integer, primary_key=True, index=True)
    idiom_de = db.Column(db.String, unique=True)
    idiom_en = db.Column(db.String)
    explanation_en = db.Column(db.String)


# Function to create the application context
def create_app_context():
    return app.app_context()

# Route to handle button click and fetch a random word based on selected level
@app.route('/get_random_word', methods=['POST'])
def get_random_word():
    if 'vocab_level' in request.form:
        selected_level = request.form['vocab_level']
        print('** SELECTED LEVEL ',selected_level)
        if selected_level:
            # Query the database to get a random word with the selected level
            print('***** ',LanguageData.query.filter_by(level=selected_level).order_by(func.random()).first())
            random_word = LanguageData.query.filter_by(level=selected_level).order_by(func.random()).first()
            print('$$$$ ',random_word)
            if random_word:
                return render_template('index.html',random_word=random_word)
    else:
        flash('vocab_level could not be found on page.', 'error')        
        
    return render_template('index.html', random_word=None)

@app.route('/exercise')
def exercise():
    # Get a random word where in_dictionary = 1
    words = LanguageData.query.filter_by(in_dictionary=1).all()
    random_word = random.choice(words) if words else None
    return render_template('exercise.html', word=random_word)
@app.route('/exercise_flip')
def exercise_flip():
    words = LanguageData.query.filter_by(in_dictionary=True).all()
    return render_template('exercise2.html', words=words)

@app.route('/exercise_bio')
def exercise_bio():
    people = BioGuess.query.filter_by().all()
    return render_template('exercise_biography.html', people=people)

@app.route('/idioms')
def idioms():
    idioms_all = Idioms.query.filter_by().all()
    return render_template('idioms.html', idioms_all=idioms_all)

@app.route('/check_word',methods=['POST'])
def check_word():
    data = request.json
    german_word = data['german_word']
    user_guess = data['user_guess']
    current_score = data['current_score']
    step_count = data['step_count']

    # Find the matching word in the database
    word_entry = LanguageData.query.filter_by(german_word=german_word, in_dictionary=1).first()

    if word_entry and user_guess.lower() == word_entry.english_word.lower():
        # Update score based on level
        score_map = {'A1': 2, 'A2': 4, 'B1': 8, 'B2': 10, 'C1': 15, 'C2': 20}
        current_score += score_map.get(word_entry.level, 0)
        correct = True
    else:
        correct = False

    # Increment step count and check if game is over
    step_count += 1
    game_over = step_count >= 5

    # Fetch a new word if the game is not over
    new_word = None
    if not game_over:
        new_word = LanguageData.query.filter_by(in_dictionary=1).order_by(db.func.random()).first()

    # Save the score if the game is over
    if game_over:
        new_score_entry = Score(score=current_score, play_date=datetime.now())
        db.session.add(new_score_entry)
        db.session.commit()

    return jsonify({
        'correct': correct,
        'new_word': new_word.german_word if new_word else None,
        'current_score': current_score,
        'game_over': game_over
    })

    

@app.route('/get_word', methods=['GET'])
def get_word():
    # Fetch a random word
    word = LanguageData.query.filter_by(in_dictionary=1).order_by(func.random()).first()
    return jsonify(german_word=word.german_word, level=word.level)

# Function to populate the database from the text file
def populate_database(file_path):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)
    with app.app_context():
        session = SessionLocal()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                data = line.strip().split(";")
                level, german_word, english_word, german_example, english_example = data

                # existing_record = session.query(LanguageData).filter_by(german_word=german_word).first()
                # existing_record = session.query(LanguageData).filter(LanguageData.german_word == german_word).first()
                try:

                    existing_entry = LanguageData.query.filter_by(german_word=german_word).first()
                    if existing_entry:
                        existing_entry.level = level
                        existing_entry.english_word = english_word
                        existing_entry.german_example = german_example
                        existing_entry.english_example = english_example

                    else:
                        # Create an instance of the LanguageData model
                        language_data = LanguageData(
                            level=level,
                            german_word=german_word,
                            english_word=english_word,
                            german_example=german_example,
                            english_example=english_example,
                            in_dictionary=0
                        )

                        # Add the instance to the session
                        db.session.add(language_data)
                    # Commit the changes
                    db.session.commit()
                except IntegrityError  as e:
                    db.session.rollback()
                    print(f"Record with german_word '{german_word}' already exists. Skipping...")
                    # flash(f'Error: {str(e)}', 'error')
        
def populate_db_with_bio(file_path):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)
   
    with app.app_context():
        session = SessionLocal()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip()=="":
                    continue
                data = line.strip().split(";")
                person, nationality, short_bio_en, short_bio_de = data

                # existing_record = session.query(LanguageData).filter_by(german_word=german_word).first()
                # existing_record = session.query(LanguageData).filter(LanguageData.german_word == german_word).first()
                try:

                    existing_entry = BioGuess.query.filter_by(person_name=person).first()
                    if existing_entry:
                        existing_entry.person_name = person
                        existing_entry.nationality = nationality
                        existing_entry.short_bio_en = short_bio_en
                        existing_entry.short_bio_de = short_bio_de
                    else:                        
                        bio_guess = BioGuess(
                            person_name=person,
                            nationality=nationality,
                            short_bio_en=short_bio_en,
                            short_bio_de=short_bio_de,
                        )

                        # Add the instance to the session
                        db.session.add(bio_guess)
                    # Commit the changes
                    db.session.commit()
                except IntegrityError  as e:
                    db.session.rollback()
                    print(f"Record with person '{person}' already exists. Skipping...")
                    # flash(f'Error: {str(e)}', 'error')
        
def populate_db_with_idioms_de(file_path):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)

    with app.app_context():
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip()=="":
                    continue
                data = line.strip().split(";")
                idiom_german, idiom_english, explanation = data
                try:
                    print('idiom german: '+ idiom_german)
                    # existing_entry = Idioms.query.filter_by(idiom_de=idiom_german).first()
                    # if existing_entry:
                    #     existing_entry.idiom_de = idiom_german
                    #     existing_entry.idiom_en = idiom_english
                    #     existing_entry.explanation_en = explanation
                    # else:                        
                    new_idiom = Idioms(
                        idiom_de=idiom_german,
                        idiom_en=idiom_english,
                        explanation_en=explanation,
                    )

                    # Add the instance to the session
                    db.session.add(new_idiom)
                    # Commit the changes
                    db.session.commit()
                except IntegrityError  as e:
                    db.session.rollback()
                    print(f"The idiom '{idiom_german}' already exists. Skipping...")
                    # flash(f'Error: {str(e)}', 'error')
  

# Helper function to close the database connection
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
# Register functions to be called before and after each request
app.teardown_appcontext(close_db)



# Helper function to get a database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db



# db = SQLAlchemy(app)

class TextEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    german_text = db.Column(db.String(255), nullable=False, unique=True)
    turkish_text = db.Column(db.String(255), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        per_page = 30
        paginated_results = LanguageData.query.paginate(page=page, per_page=per_page)

    return render_template('index.html',results=None)

def get_results_for_page(page, per_page):
    # Query your database here, considering pagination
    db = get_db()
    cursor = db.cursor()
    
    query = """
    SELECT * FROM language_data
    WHERE in_dictionary = 1 
    """
    search_term = f"%{request.form['search']}%"
    cursor.execute(query, (search_term, search_term))
    results = cursor.fetchall()
    # Example: results = YourModel.query.paginate(page=page, per_page=per_page)
    results = LanguageData.query.paginate(page=page,per_page=per_page)

    return results
@app.route('/delete_all', methods=['GET','POST'])
def delete_all():
    # if request.method == 'POST':
    db = get_db()
    cursor = db.cursor()

    query = """
    UPDATE language_data
    SET in_dictionary = 0 
    """
    cursor.execute(query)
    db.commit()
    flash('All words removed from dictionary.', 'success')    
    return redirect(url_for('index'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # search_term = request.form.get('search','').strip()
       
        page = request.args.get('page', 1, type=int)
        per_page = 5
        paginated_results = LanguageData.query.filter(           
                LanguageData.in_dictionary==1                 
        ).paginate(page=page, per_page=per_page)
        return render_template('index.html', results=paginated_results)
        
      # Handle GET request or invalid search term
    elif request.method == 'GET':
        # Process the search term from the URL parameters
        # search_term = request.args.get('search', '').strip()
        # search_term = request.form.get('search', '').strip()

        # if search_term and search_term != '%%':
            # If the search term is valid, perform the search
        print('     --- This is GET ---')
        page = request.args.get('page', 1, type=int)
        per_page = 5

        paginated_results = LanguageData.query.filter(
            LanguageData.in_dictionary == 1 
        ).paginate(page=page, per_page=per_page)

        return render_template('index.html', results=paginated_results)

    # Handle invalid search term or other cases
    return redirect(url_for('index'))

@app.route('/delete_row/<int:row_id>', methods=['POST'])    
def delete_row(row_id):
    try:
        if request.method == 'POST':
         entry_to_update = LanguageData.query.get(row_id)
         if entry_to_update:
             entry_to_update.in_dictionary = 0
             db.session.commit()
             flash(f'The word: \'{entry_to_update.german_word}\' removed from dictionary.', 'success')
             return redirect(url_for('index'))
            #  print ("U:"+entry_to_update.german_word)
            #  message = f'\'{entry_to_update.german_word}\' removed from dictionary!', 'success'
        
            # flash('No entry found.', 'error')
            #  return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'error')
    return redirect(url_for('index'))
    

    return jsonify({'success': False, 'message': 'No entry found'}), 404

import requests

    
@app.route('/add2dict/<int:row_id>', methods=['POST'])
def add2dict(row_id):
    # Find the row with the given ID
    word_to_update = LanguageData.query.get(row_id)
    
    # Check if the word exists
    if word_to_update:
        # Update the in_dictionary column
        word_to_update.in_dictionary = 1
        db.session.commit()

        # Redirect to a desired page after updating
        flash(f'The word: \'{word_to_update.german_word}\' added to dictionary.', 'success')
        return redirect(url_for('index'))        
    else:
        # Handle the case where the word doesn't exist
        flash(f'The word could not be found.', 'error')
        return redirect(url_for('index'))
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Get the current working directory
        current_dir = os.getcwd()
        # print("cUR DIRECTORY: "+current_dir)
        # Construct the full file path
        # file_path2words = "words.txt"

        # vocab_training_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        # full_file_path2words = os.path.join(vocab_training_dir, file_path2words)

        # populate_database(full_file_path2words)

        
        importPeople=False
        importWords=False
        importIdioms=False

        if importPeople:
            file_path2people = "people.txt"
            people_file_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            full_file_path2people = os.path.join(people_file_dir, file_path2people)
            print('Path: '+full_file_path2people)
            populate_db_with_bio(full_file_path2people)
        
        if importIdioms:
            file_path2idioms = "idioms.txt"
            idioms_file_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            full_file_path2idioms = os.path.join(idioms_file_dir, file_path2idioms)
            print('Path: '+full_file_path2idioms)
            populate_db_with_idioms_de(full_file_path2idioms)

    app.run(debug=True,host='0.0.0.0', port=5000)
