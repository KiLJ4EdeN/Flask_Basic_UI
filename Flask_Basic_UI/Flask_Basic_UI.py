from flask import Flask, render_template, request, redirect, url_for
from mongoengine import *
from flask_wtf import FlaskForm
from flask_mongoengine import MongoEngine, Document
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)

app.config['SECRET_KEY'] = '1234'
app.config['TESTING'] = True
app.config['MONGODB_SETTINGS'] = {
    "db": 'Flask_Basic_UI',
    "alias": 'Project',
}

db = MongoEngine(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
FMT = '%H:%M:%S'
########### MODELS ###########


class User(UserMixin, Document):
    meta = {'db_alias': 'Project', 'collection': 'User'}
    email = db.StringField(max_length=50)
    password = db.StringField(max_length=200)


@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


class RegForm(FlaskForm):
    email = StringField('email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=20)])


class PassForm(FlaskForm):
    old_password = PasswordField('old_password', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=20)])


class MailForm(FlaskForm):
    old_email = StringField('old_email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    email = StringField('email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])


class LogForm(FlaskForm):
    email = StringField('email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=20)])

########### VIEWS ###########


@app.route('/')
@login_required
def app_root():
    return redirect(url_for('login'))


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            existing_user = User.objects(email=form.email.data).first()
            if existing_user is None:
                hashpass = generate_password_hash(form.password.data, method='sha256')
                temp = User()
                temp.email = form.email.data
                temp.password = hashpass
                temp.save()
                login_user(temp)
                return redirect(url_for('dashboard'))
            else:
                return render_template('register.html', form=form, statement='Email Already in use.')
        else:
            return render_template('register.html', form=form, statement='Wrong Entry!')

    return render_template('register.html', form=form, statement='Welcome!')


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LogForm()
    if request.method == 'POST':
        check_user = User.objects(email=form.email.data).first()
        if check_user:
            if check_password_hash(check_user['password'], form.password.data):
                login_user(check_user)
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', form=form, statement='Wrong Email or Password!')
        else:
            return render_template('login.html', form=form, statement='Wrong Email or Password!')
    return render_template('login.html', form=form)


@app.route('/dashboard/')
@login_required
def dashboard():
    return render_template('dashboard.html', email=current_user.email)


@app.route('/changepass/', methods=['POST', 'GET'])
@login_required
def changepass():
    form = PassForm()
    if request.method == 'POST':
        if form.validate():
            existing_user = User.objects(email=current_user.email).first()
            if check_password_hash(existing_user['password'], form.old_password.data):
                hashpass = generate_password_hash(form.password.data, method='sha256')
                existing_user.update(set__password=hashpass)
                existing_user.reload()
                login_user(existing_user)
                return render_template('changepass.html',
                                       statement='Password Successfully Changed.', form=form,
                                       )
            else:
                return render_template('changepass.html', form=form, statement='Wrong Password! Please try again.'
                                       )
        else:
            return render_template('changepass.html', form=form,
                                   statement='Password Must be Longer than 4 and '
                                   'shorter than 30 letters.')

    return render_template('changepass.html', form=form)


@app.route('/changemail/', methods=['POST', 'GET'])
@login_required
def changemail():
    form = MailForm()
    if request.method == 'POST':
        existing_user = User.objects(email=current_user.email).first()
        print(existing_user.email)
        if existing_user.email == form.old_email.data:
            existing_user.update(set__email=form.email.data)
            existing_user.reload()
            login_user(existing_user)
            return render_template('changemail.html', form=form,
                                   statement='Email Successfully Changed to :' + current_user.email)
        else:
            return render_template('changemail.html', form=form,
                                   statement='Wrong Email! Please try again.')
    else:
        return render_template('changemail.html', form=form, statement=''
                               )


@app.route('/logout/', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
