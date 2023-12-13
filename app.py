import hashlib
import random
import string
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pokoknya-rahasia'

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="final_project"
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    return User(user['id'], user['username'], user['email'], user['password']) if user else None

class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('email')
        password = request.form.get('password')
        
        cursor = mydb.cursor(dictionary=True)
        if '@' in identifier:
            cursor.execute("SELECT * FROM user WHERE email = %s", (identifier,))
        else:
            cursor.execute("SELECT * FROM user WHERE username = %s", (identifier,))

        user = cursor.fetchone()

        if user and user['password'] == hashlib.md5(password.encode()).hexdigest():
            login_user(User(user['id'], user['username'], user['email'], user['password']))
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')

        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            return redirect(url_for('register', message='duplicate'))
        else:
            password = request.form.get('password')
            password_md5 = hashlib.md5(password.encode()).hexdigest()

            cursor.execute("INSERT INTO user (username, email, password) VALUES (%s, %s, %s)", (username, email, password_md5))
            mydb.commit()

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

        cursor = mydb.cursor(dictionary=True)
        cursor.execute("INSERT INTO snippet (title, description, language, code, documentation, user_id) VALUES (%s, %s, %s, %s, %s, %s)", (title, description, language, code, documentation, current_user.id))
        mydb.commit()

    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM snippet WHERE user_id = %s", (current_user.id,))
    snippets = cursor.fetchall()
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

        cursor = mydb.cursor(dictionary=True)
        cursor.execute("INSERT INTO snippet (title, description, language, code, documentation, user_id) VALUES (%s, %s, %s, %s, %s, %s)", (title, description, language, code, documentation, current_user.id))
        mydb.commit()

        flash('Snippet added successfully', 'success')

    return render_template('editor.html')

@app.route('/edit/<int:snippet_id>', methods=['GET', 'POST'])
@login_required
def edit_snippet(snippet_id):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM snippet WHERE id = %s AND user_id = %s", (snippet_id, current_user.id))
    snippet = cursor.fetchone()

    if snippet:
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            language = request.form.get('language')
            code = request.form.get('code')
            documentation = request.form.get('documentation')

            cursor.execute("UPDATE snippet SET title = %s, description = %s, language = %s, code = %s, documentation = %s WHERE id = %s", (title, description, language, code, documentation, snippet_id))
            mydb.commit()

            flash('Snippet updated successfully', 'success')
            return redirect(url_for('snippets'))

        return render_template('edit_snippet.html', snippet=snippet)
    else:
        flash('Snippet not found or unauthorized', 'error')
        return redirect(url_for('snippets'))

@app.route('/delete/<int:snippet_id>')
@login_required
def delete_snippet(snippet_id):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("DELETE FROM snippet WHERE id = %s AND user_id = %s", (snippet_id, current_user.id))
    mydb.commit()

    flash('Snippet deleted successfully', 'success')
    return redirect(url_for('snippets'))

@app.route('/generate_share_link/<int:snippet_id>')
@login_required
def generate_share_link(snippet_id):
    share_code = ''.join(random.choices(string.ascii_lowercase, k=6))

    cursor = mydb.cursor(dictionary=True)
    cursor.execute("UPDATE snippet SET share_code = %s WHERE id = %s AND user_id = %s", (share_code, snippet_id, current_user.id))
    mydb.commit()

    share_link = f"http://localhost:8081/share/{share_code}"
    return share_link

@app.route('/share/<share_code>')
def shared_snippet(share_code):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM snippet WHERE share_code = %s", (share_code,))
    snippet = cursor.fetchone()

    if snippet:
        return render_template('shared_snippet.html', snippet=snippet)
    else:
        flash('Snippet not found or unauthorized', 'error')
        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8081)