from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import bcrypt
from config import Config
from utils.ai_summary import generate_summary

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ------------------ MODELS ------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(200))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ ROUTES ------------------

@app.route('/')
def index():
    posts = Post.query.all()
    return render_template("index.html", posts=posts)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        hashed = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        user = User(username=request.form['username'], email=request.form['email'], password=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Account created!")
        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.checkpw(request.form['password'].encode('utf-8'), user.password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route('/dashboard')
@login_required
def dashboard():
    posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", posts=posts)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == "POST":
        post = Post(
            title=request.form['title'],
            content=request.form['content'],
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template("create_post.html")

@app.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template("post.html", post=post)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if request.method == "POST":
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template("edit_post.html", post=post)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/summarize/<int:id>')
@login_required
def summarize(id):
    post = Post.query.get_or_404(id)
    post.summary = generate_summary(post.content)
    db.session.commit()
    return redirect(url_for('post', id=id))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)