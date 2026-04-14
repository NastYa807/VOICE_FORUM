from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Список категорий для главной страницы
CATEGORIES = [
    {"id": 1, "name": "Спорт и Волочкова"},
    {"id": 2, "name": "Музыка и Макан"},
    {"id": 3, "name": "Стримеры и Полковник"},
    {"id": 4, "name": "Мужская логика и Маркарян"},
    {"id": 5, "name": "Женская логика и Кисова"},
    {"id": 6, "name": "Бизнес и Эпштейн"},
]

# Простая модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# МАРШРУТЫ!!!

@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Упрощенная логика: создаем или входим
        user = User.query.filter_by(username=request.form['username']).first()
        if not user:
            user = User(username=request.form['username'], password='123')
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/category/<int:cat_id>')
@login_required
def category(cat_id):
    cat_name = next(c['name'] for c in CATEGORIES if c['id'] == cat_id)
    # Здесь в реальном проекте будет запрос к БД за темами этой категории
    return render_template('category.html', name=cat_name)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)