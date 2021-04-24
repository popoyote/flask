from flask import Flask, jsonify, render_template, redirect, request, make_response, session, abort

from data import db_session, products_api
from data.users import User
from data.products import Products

from datetime import timedelta

from forms.loginform import LoginForm
from forms.user import RegisterForm
from forms.products import ProductsForm

from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_restful import reqparse, abort, Api, Resource
import products_resources
# Нужные библиотеки

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    days=31
)
api = Api(app)
api.add_resource(products_resources.ProductsListResource, '/api/v2/products')
api.add_resource(products_resources.ProductsResource, '/api/v2/products/<int:products_id>')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/blogs.db")
    app.register_blueprint(products_api.blueprint)
    app.run(debug=True)
# Запуск сервера


@app.route("/")
def index():
    db_sess = db_session.create_session()
    products = db_sess.query(Products)
    return render_template("index.html", products=products)
# Главная страница


@app.route('/create', methods=['GET', 'POST'])
@login_required
def add_products():
    session.expire_on_commit = False
    form = ProductsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = Products()
        products.title = form.title.data
        products.content = form.content.data
        products.price = form.price.data
        current_user.products.append(products)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('create.html', title='Добавление товара',
                           form=form)
# Добавление товара

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            contact_info=form.contact_info.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# Вход (для зарегестрированных) 
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# Выход (для зарегестрированных) 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Тест сессии(кол-во посещений страницы) 
@app.route("/session_test")
def session_test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f"Вы пришли на эту страницу {visits_count + 1} раз")


# Просмотр продукта
@app.route('/products/<int:id>', methods=['GET', 'POST'])
@login_required
def id_products(id):
    form = ProductsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        products = db_sess.query(Products).filter(Products.id == id).first()
        if not products:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = db_sess.query(Products).filter(Products.id == id).first()
    return render_template('cproduct.html', products=products)


# Просмотр профиля
@app.route('/profile/<int:id>', methods=['GET', 'POST'])
@login_required
def profile(id):
    form = RegisterForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id).first()
        if not user:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = db_sess.query(Products).filter(Products.id == id).first()
    return render_template('profile.html', user=user)


# Редактирование продукта
@app.route('/products/re/<int:id>', methods=["GET", 'POST'])
@login_required
def edit_products(id):
    form = ProductsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        products = db_sess.query(Products).filter(Products.id == id,
                                                  Products.user == current_user
                                                  ).first()
        if products:
            form.title.data = products.title
            form.content.data = products.content
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = db_sess.query(Products).filter(Products.id == id,
                                                  Products.user == current_user
                                                  ).first()
        if products:
            products.title = form.title.data
            products.content = form.content.data
            products.price = form.price.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('edit_product.html',
                           title='Редактирование товара',
                           form=form
                           )


# Удаление продукта(для создателя)
@app.route('/products_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def products_delete(id):
    db_sess = db_session.create_session()
    products = db_sess.query(Products).filter(Products.id == id,
                                              Products.user == current_user
                                              ).first()
    if products:
        db_sess.delete(products)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 404)


if __name__ == "__main__":
    main()
