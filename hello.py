from datetime import datetime
from flask import Flask, render_template,session,redirect,url_for,flash
from flask_script import Manager,Server,Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField,SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate,MigrateCommand
from flask_mail import Mail,Message
from threading import Thread 
import os

#get current file path
basedir = os.path.abspath(os.path.dirname(__file__)) 

app = Flask(__name__) #building a entity 
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
	'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#config mail 
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'  #subject(主题)
app.config['FLASKY_MAIL_SENDER'] = '35223644@qq.com'  #send mail 
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')#recipient mail

db = SQLAlchemy(app)

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
mail = Mail(app)
#open debug moddle!
manager.add_command("runserver", Server(use_debugger=True))
#config db migration
migrate = Migrate(app,db)
manager.add_command('db',MigrateCommand)
#let shell auto load db/app/modul ......
def make_shell_context():
	return dict(app=app,db=db,User=User,Role=Role)
manager.add_command('shell',Shell(make_context=make_shell_context))
##def mail 
def send_async_email(app,msg):
	with app.app_context():  #manul create app's context
		mail.send(msg)

def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email,args=[app,msg])
    thr.start()
    return thr

class NameForm(Form):## Inherit flask.ext.wtf class
	name = StringField('what is your name?',validators = [Required()])
	submit = SubmitField('Submit')

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer,primary_key = True)
	name = db.Column(db.String(64),unique = True)

	def __repr__(self):
		return '<Role %r>' % self.name

class User(db.Model):
	__tablename__ = 'Users'
	id = db.Column(db.Integer,primary_key = True)
	username = db.Column(db.String(64),unique = True, index = True)
	role = db.Column(db.String(64),nullable = True)

	def __repr__(self): 
		return '<User %r>' % self.username


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    # # name = None
    # form = NameForm()
    # #get argument values
    # flash(app.config['MAIL_USERNAME'])
    # if form.validate_on_submit():
    # 	user = User.query.filter_by(username=form.name.data).first()
    # 	if user is None:
    # 		user = User(username = form.name.data)
    # 		db.session.add(user)
    # 		session['known'] = False
    # 	else:
    # 		session['known'] = True
    # 	session['name'] = form.name.data
    # 	form.name.data = ''
    # 	return redirect(url_for('index'))
    # # return render_template		
    # # 	old_name  = session.get('name')
    # # 	if old_name is not None and old_name != form.name.data:
    # # 		flash('您似乎用了一个新名字！！')
    # # 	session['name'] = form.name.data
    # #     # form.name.data = ''
    # # 	return redirect(url_for('index'))##keep the value on sesson ,redirct resolve refresh problem
    # return render_template('index.html', current_time = datetime.utcnow(),form=form, name=session.get('name'),known = session.get('known',False))


    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], '有新用户注册！',
                           'mail/new_user', user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html', current_time = datetime.utcnow(),form=form, name=session.get('name'),
                           known=session.get('known', False))

    
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


if __name__ == '__main__':
    manager.run()
