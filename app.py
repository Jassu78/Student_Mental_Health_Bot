from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'Random'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    quiz_score = db.Column(db.Integer, default=0)  # To store quiz score

# Configure Gemini AI model
genai.configure(api_key=os.getenv("API_KEY"))  # Replace with your actual API key
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('main'))
        flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        score = sum(int(request.form[q]) for q in request.form)
        user = User.query.get(session['user_id'])
        user.quiz_score = score
        db.session.commit()
        return redirect(url_for('main'))
    return render_template('quiz.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        flash('Profile updated successfully!')
        return redirect(url_for('main'))
    return render_template('profile.html', user=user)

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = User.query.get(session['user_id'])
    chat_history = session.get('chat_history', [])
    
    if request.method == 'POST':
        user_input = request.form['message']
        prompt = f"Your role is that of  AI assistant for only Students mental health of age between 5 to 25 years.The student will ask a question for help regarding mental health or as an answer to a question based on chat history. Your goal is to help users by giving an understanding, empathetic, engaging, and discursive response. Keep the responses minimum (3 lines maximum) and just plain text. If you feel like the student is asking for anything unrelated to mental health or studies, get them back on track wisely. Respond to: {user_input}"
        response = model.generate_content(prompt)

        # Store chat messages in the history
        chat_history.append({'user': user_input, 'bot': response.text})
        session['chat_history'] = chat_history
        
        return redirect(url_for('chat'))

    return render_template('chat.html', chat_history=chat_history)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
