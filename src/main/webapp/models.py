# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LanguageData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(10))
    german_word = db.Column(db.String(100), unique=True)
    english_word = db.Column(db.String(100))
    german_example = db.Column(db.String(255))
    english_example = db.Column(db.String(255))
