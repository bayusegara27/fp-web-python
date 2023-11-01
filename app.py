import hashlib
from flask import Flask, render_template, request, redirect, url_for, flash, session, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pokoknya-rahasia'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    snippets = db.relationship('Snippet', backref='author', lazy=True)

class Snippet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    language = db.Column(db.String(50), nullable=False)
    code = db.Column(db.Text, nullable=False)
    documentation = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('email')
        password = request.form.get('password')
        if '@' in identifier:
            user = User.query.filter_by(email=identifier).first()
        else:
            user = User.query.filter_by(username=identifier).first()

        if user and user.password == hashlib.md5(password.encode()).hexdigest():
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        # Cek jika username atau email telah digunakan
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return redirect(url_for('register', message='duplicate'))
        else:
            password = request.form.get('password')
            password_md5 = hashlib.md5(password.encode()).hexdigest()
            new_user = User(username=username, email=email, password=password_md5)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/home')
@login_required
def home():
    username = current_user.username
    return render_template('home.html', username=username)

@app.route('/snippets', methods=['GET', 'POST'])
@login_required
def snippets():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        language = request.form.get('language')
        code = request.form.get('code')
        documentation = request.form.get('documentation')
        new_snippet = Snippet(title=title, description=description, language=language, code=code, documentation=documentation, author=current_user)
        db.session.add(new_snippet)
        db.session.commit()
    snippets = Snippet.query.filter_by(user_id=current_user.id).all()
    return render_template('snippets.html', snippets=snippets)

@app.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        language = request.form.get('language')
        code = request.form.get('code')
        documentation = request.form.get('documentation')
        new_snippet = Snippet(title=title, description=description, language=language, code=code, documentation=documentation, author=current_user)
        db.session.add(new_snippet)
        db.session.commit()
        flash('Snippet added successfully', 'success')
    return render_template('editor.html')

@app.route('/edit/<int:snippet_id>', methods=['GET', 'POST'])
@login_required
def edit_snippet(snippet_id):
    snippet = Snippet.query.get(snippet_id)
    if snippet and snippet.user_id == current_user.id:
        if request.method == 'POST':
            snippet.title = request.form.get('title')
            snippet.description = request.form.get('description')
            snippet.language = request.form.get('language')
            snippet.code = request.form.get('code')
            snippet.documentation = request.form.get('documentation')
            db.session.commit()
            flash('Snippet updated successfully', 'success')
            return redirect(url_for('snippets'))
        return render_template('edit_snippet.html', snippet=snippet)
    else:
        flash('Snippet not found or unauthorized', 'error')
        return redirect(url_for('snippets'))

@app.route('/delete/<int:snippet_id>')
@login_required
def delete_snippet(snippet_id):
    snippet = Snippet.query.get(snippet_id)
    if snippet and snippet.user_id == current_user.id:
        db.session.delete(snippet)
        db.session.commit()
        flash('Snippet deleted successfully', 'success')
    else:
        flash('Snippet not found or unauthorized', 'error')
    return redirect(url_for('snippets'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8081)