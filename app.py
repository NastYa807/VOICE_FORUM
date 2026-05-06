from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

# Инициализация приложения и настройки базы данных
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Объекты управления базой данных и авторизацией
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Список категорий форума
CATEGORIES = [
    {"id": 1, "name": "Спорт и Волочкова", "color": "orange"},
    {"id": 2, "name": "Музыка и Макан", "color": "blue"},
    {"id": 3, "name": "Стримеры и Полковник", "color": "purple"},
    {"id": 4, "name": "Мужская логика и Маркарян", "color": "indigo"},
    {"id": 5, "name": "Женская логика и Кисова", "color": "pink"},
    {"id": 6, "name": "Бизнес и Эпштейн", "color": "green"},
]


# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


# Модель темы форума
class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    author = db.Column(db.String(100))


# Модель комментария к теме
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    author = db.Column(db.String(100))


# Загрузка пользователя по его ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ОБРАБОТКА МАРШРУТА

# Главная страница со списком категорий
@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES)


# Страница авторизации и регистрация новых пользователей
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, password='123')
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html')


# Страница категории и создание новой темы
@app.route('/category/<int:cat_id>', methods=['GET', 'POST'])
@login_required
def category(cat_id):
    cat = next((c for c in CATEGORIES if c['id'] == cat_id), None)
    if request.method == 'POST':
        new_topic = Topic(
            title=request.form['title'],
            content=request.form['content'],
            category_id=cat_id,
            author=current_user.username
        )
        db.session.add(new_topic)
        db.session.commit()
        return redirect(url_for('category', cat_id=cat_id))

    topics = Topic.query.filter_by(category_id=cat_id).all()
    return render_template('category_topics.html', cat=cat, topics=topics)


# Страница темы, счетчик лайков и добавление комментариев
@app.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def topic_detail(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    if request.method == 'POST':
        if 'like' in request.form:
            topic.likes += 1
        elif 'comment' in request.form:
            new_comment = Comment(text=request.form['comment'], topic_id=topic.id, author=current_user.username)
            db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('topic_detail', topic_id=topic_id))

    comments = Comment.query.filter_by(topic_id=topic_id).all()
    return render_template('topic_detail.html', topic=topic, comments=comments)


# УДАЛЕНИЕ ТЕМЫ (Только администратор)
@app.route('/delete_topic/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    # Проверка на права администратора
    if current_user.is_admin:
        Comment.query.filter_by(topic_id=topic_id).delete()
        db.session.delete(topic)
        db.session.commit()
    return redirect(url_for('category', cat_id=topic.category_id))


# УДАЛЕНИЕ КОММЕНТАРИЯ (Только администратор)
@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user.is_admin:
        topic_id = comment.topic_id
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('topic_detail', topic_id=topic_id))
    return "Доступ запрещен", 403


# Выход из системы
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# Создание базы данных и запуск сервера
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # БД
        # Автоматическое создание учетной записи администратора
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='123', is_admin=True)
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)