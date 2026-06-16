from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'glubinka-secret-key-2024'
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_YpcAkVbCh7G4@ep-hidden-haze-aq65rdqu.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# НАСТРОЙКИ ДЛЯ ПОЧТЫ АДМИНА
MY_EMAIL = "golos.glubinki@mail.ru"
MY_PASSWORD = "yKbRoR6Kl3gfaDn0JLdN"


# АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ СЕРВЕРА НА ПОЧТЕ
def get_mail_server(email):
    email_lower = email.lower()
    if '@gmail.com' in email_lower:
        return {
            'server': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'use_ssl': False
        }
    elif '@yandex.ru' in email_lower or '@yandex.com' in email_lower:
        return {
            'server': 'smtp.yandex.ru',
            'port': 465,
            'use_tls': False,
            'use_ssl': True
        }
    elif '@mail.ru' in email_lower or '@inbox.ru' in email_lower or '@list.ru' in email_lower or '@bk.ru' in email_lower:
        return {
            'server': 'smtp.mail.ru',
            'port': 465,
            'use_tls': False,
            'use_ssl': True
        }
    else:
        return None


# НАСТРОЙКА ПОЧТЫ НА ОСНОВЕ ПОЧТЫ АДМИНА
mail_config = get_mail_server(MY_EMAIL)
if mail_config:
    app.config['MAIL_SERVER'] = mail_config['server']
    app.config['MAIL_PORT'] = mail_config['port']
    app.config['MAIL_USE_TLS'] = mail_config['use_tls']
    app.config['MAIL_USE_SSL'] = mail_config['use_ssl']
    app.config['MAIL_USERNAME'] = MY_EMAIL
    app.config['MAIL_PASSWORD'] = MY_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = MY_EMAIL
    print(f"Почта настроена: {MY_EMAIL} через {mail_config['server']}")
else:
    print(f"Ошибка: Почтовый сервис для {MY_EMAIL} не поддерживается")

# ОБЪЕКТЫ УПРАВЛЕНИЯ
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# КАТЕГОРИИ ТЕМ
CATEGORIES = [
    {"id": 1, "name": "Политика и Милонов", "color": "red"},
    {"id": 2, "name": "Нефоры и ЧВК Редан", "color": "gray"},
    {"id": 3, "name": "Блогеры и Литвин", "color": "yellow"},
    {"id": 4, "name": "35 и Сухой закон", "color": "blue"},
    {"id": 5, "name": "Учёба и Прокрастинация", "color": "green"},
    {"id": 6, "name": "Пестик и Тычинка", "color": "pink"},
    {"id": 7, "name": "Спорт и Волочкова", "color": "orange"},
    {"id": 8, "name": "Музыка и Макан", "color": "purple"},
    {"id": 9, "name": "Стримеры и Полковник", "color": "indigo"},
    {"id": 10, "name": "Мужская логика и Маркарян", "color": "cyan"},
    {"id": 11, "name": "Женская логика и Кисова", "color": "pink"},
    {"id": 12, "name": "Бизнес и Эпштейн", "color": "emerald"},
]


# МОДЕЛИ БД
# ПОЛЬЗОВАТЕЛИ(ЛОГИН, ПОЧТА, ПАРОЛЬ, ПРАВА АДМИНА)
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ХРАНЕНИЕ ТОКЕНОВ ДЛЯ СБРОСА ПАРОЛЯ
class PasswordReset(db.Model):
    __tablename__ = 'password_reset'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)


# ТЕМЫ ОБСУЖДЕНИЙ
class Topic(db.Model):
    __tablename__ = 'topic'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    author = db.Column(db.String(100))


# КОММЕНТАРИИ К ТЕМАМ
class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    author = db.Column(db.String(100))


# ЗАГРУЗЧИК ПОЛЬЗОВАТЕЛЯ
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# МАРШРУТЫ
#  ГЛАВНАЯ СТРАНИЦА СО СПИСКОМ КАТЕГОРИЙ
@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES)


# ВХОД И РЕГИСТРАЦИЯ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_type = request.form.get('form_type', 'login')

        if form_type == 'login':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash(f'Добро пожаловать, {username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Неверный логин или пароль!', 'error')

        elif form_type == 'register':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if password != confirm_password:
                flash('Пароли не совпадают!', 'error')
                return redirect(url_for('login'))

            if len(password) < 3:
                flash('Пароль должен быть минимум 3 символа!', 'error')
                return redirect(url_for('login'))

            if User.query.filter_by(username=username).first():
                flash('Пользователь с таким логином уже существует!', 'error')
                return redirect(url_for('login'))

            if email and User.query.filter_by(email=email).first():
                flash('Пользователь с таким email уже существует!', 'error')
                return redirect(url_for('login'))

            if not email or '@' not in email:
                flash('Введите корректный email!', 'error')
                return redirect(url_for('login'))

            new_user = User(username=username, email=email, is_admin=False)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash('Регистрация успешна! Теперь войдите в аккаунт.', 'success')
            return redirect(url_for('login'))

    return render_template('login.html')


# ВОССТАНОВЛЕНИЕ ПАРОЛЯ ЧЕРЕЗ ПОЧТУ
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Пользователь с таким email не найден! Проверьте правильность ввода.', 'error')
            return redirect(url_for('forgot_password'))

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)

        reset = PasswordReset(email=email, token=token, expires_at=expires_at)
        db.session.add(reset)
        db.session.commit()

        reset_url = url_for('reset_password', token=token, _external=True)

        try:
            msg = Message(
                subject='Восстановление пароля - Форум "Глубинка"',
                recipients=[email]
            )

            msg.body = f'''Здравствуйте, {user.username}!

Вы запросили сброс пароля для аккаунта на форуме "Глубинка".

Чтобы создать новый пароль, перейдите по ссылке:
{reset_url}

Ссылка действительна в течение 1 часа.

Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.

---
С уважением,
Команда форума "Глубинка"
'''
            mail.send(msg)
            flash(f'Ссылка для сброса пароля отправлена на {email}! Проверьте папку "Спам".', 'success')
            print(f"Письмо отправлено на {email}")

        except Exception as e:
            print(f"Ошибка отправки: {e}")
            flash(f'Не удалось отправить email. Ошибка: {str(e)}', 'error')

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


# ВОССТАНОВЛЕНИЕ ПАРОЛЯ ЧЕРЕЗ ПОЧТУ
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordReset.query.filter_by(token=token, used=False).first()

    if not reset or reset.expires_at < datetime.now():
        flash('Неверная или просроченная ссылка для сброса пароля.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return redirect(url_for('reset_password', token=token))

        if len(password) < 3:
            flash('Пароль должен быть минимум 3 символа!', 'error')
            return redirect(url_for('reset_password', token=token))

        user = User.query.filter_by(email=reset.email).first()
        if user:
            user.set_password(password)
            reset.used = True
            db.session.commit()
            flash('Пароль успешно изменён! Теперь войдите с новым паролем.', 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


# СТРАНИЦА КОНКРЕТНОЙ КАТЕГОРИИ С ТЕМАМИ(СОЗДАЮТСЯ НОВЫЕ ТЕМЫ)
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


# СТРАНИЦА ТЕМЫ(СТАВИТЬ ЛАЙКИ, ПИСАТЬ КОММЫ)
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


# УДАЛЕНИЕ(ДЛЯ АДМИНА)
@app.route('/delete_topic/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    if current_user.is_admin:
        Comment.query.filter_by(topic_id=topic_id).delete()
        db.session.delete(topic)
        db.session.commit()
        flash('Тема удалена', 'success')
    else:
        flash('У вас нет прав на удаление темы', 'error')
    return redirect(url_for('category', cat_id=topic.category_id))


# УДАЛЕНИЕ(ДЛЯ АДМИНА)
@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user.is_admin or comment.author == current_user.username:
        db.session.delete(comment)
        db.session.commit()
        flash('Комментарий удалён', 'success')
    else:
        flash('У вас нет прав на удаление этого комментария', 'error')
    return redirect(url_for('topic_detail', topic_id=comment.topic_id))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# ЗАПУСК(СОЗДАНИЕ АДМИНА)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@forum.com', is_admin=True)
            admin.set_password('123')
            db.session.add(admin)
            db.session.commit()
            print("Администратор создан: admin / 123")
    app.run(debug=True, port=5000)
