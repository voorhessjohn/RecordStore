#####################
#
# Record Store App
# SI364 Final Project
#
##################### 

import os
import requests
import json
from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, IntegerField, DateField, FloatField, BooleanField, PasswordField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms.fields.html5 import EmailField
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand # needs: pip/pip3 install flask-migrate
from flask_mail import Mail, Message
from threading import Thread
from werkzeug import secure_filename
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash


# Get some data from another source (an API, BeautifulSoup)
# At least 4 view functions (not counting error handling) [DONE]
# 	index
# 	wishlist_view
# 	record_view
# 	upload
# At least 2 error handling view functions (404 and whatever other real error you want) [DONE]
# At least 3 models (database tables) [DONE]
# At least 1 one-to-many relationship [DONE]
# At least 1 many-to-many relationship with association table [DONE]
# At least 2 get_or_create functions to deal with entering data into a database [DONE]
# At least 1 form using WTForms [DONE]
# At least 2 dynamic links, which can be covered by:
# 	a href tags that send data that is processed by the end URL [DONE]
# 	using url_for
# 	using redirect
# (200 points of the 2500) Use at least one flask extension so that it works:
# 	Could be Flask email
# 	user authentication
# 	file upload


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.debug = True
app.static_folder = 'static'
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364thisisnotsupersecurebutitsok'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/record_store" 
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587 #default
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') 
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_SUBJECT_PREFIX'] = '[Songs App]'
app.config['MAIL_SENDER'] = 'Admin <>' 
app.config['ADMIN'] = os.environ.get('ADMIN')

#YOUTUBE_API_KEY = AIzaSyCaViVTsN35aH0PWZxVHFUzrcDLV5SMVcs


manager = Manager(app)
db = SQLAlchemy(app) 
migrate = Migrate(app, db) 
manager.add_command('db', MigrateCommand) 
mail = Mail(app) 

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

sales_order_record = db.Table('sales_order_record',db.Column('sales_order_id',db.Integer, db.ForeignKey('sales_orders.id')),db.Column('record_id',db.Integer, db.ForeignKey('records.id')))

class User(UserMixin, db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	userName = db.Column(db.String(255))
	email = db.Column(db.String(255))
	password_hash = db.Column(db.String(128))

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return "User: {} & email: {}".format(self.userName,self.email)

## DB load function
## Necessary for behind the scenes login manager that comes with flask_login capabilities! Won't run without this.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # returns User object or None

class Sales_Order(db.Model):
    __tablename__ = "sales_orders"
    id = db.Column(db.Integer, primary_key=True)
    catalog_no = db.Column(db.Integer, db.ForeignKey("records.catalog_no"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    def __repr__(self):
        return "Sales Order Line: id-{} catalog_no-{} user_id-{}".format(self.id,self.catalog_no,self.user_id)

class Record(db.Model):
	__tablename__ = "records"
	id = db.Column(db.Integer, primary_key=True)
	catalog_no = db.Column(db.Integer, unique=True)
	artist = db.Column(db.String(255))
	title = db.Column(db.String(255))
	label = db.Column(db.String(255))
	record_format = db.Column(db.String(255))
	rating = db.Column(db.String(255))
	released = db.Column(db.Date)
	release_id = db.Column(db.String(255))
	collection_folder = db.Column(db.String(255))
	date_added = db.Column(db.Date)
	collection_media_condition = db.Column(db.String(255))
	collection_sleeve_condition = db.Column(db.String(255))
	collection_notes = db.Column(db.String(255))
	price = db.Column(db.Float)

	def __repr__(self):
		return "Record: Item Number:{} {} by {} {}".format(self.id,self.title,self.artist,self.price)

class RecordForm(FlaskForm):
	catalog_no = IntegerField("Catalog Number")
	artist = StringField("Artist")
	title = StringField("Title")
	label = StringField("Label")
	record_format = StringField("Format")
	rating = StringField("Rating")
	released = DateField("Date")
	release_id = IntegerField("Release ID")
	collection_folder = StringField("Collection Folder")
	date_added = DateField("Date Added")
	collection_media_condition = StringField("Media Condition")
	collection_sleeve_condition = StringField("Sleeve Condition")
	collection_notes = StringField("Notes")
	price = FloatField("Price")
	submit = SubmitField('Submit')

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    userName = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class UploadForm(FlaskForm):
    file = FileField()

class AddForm(FlaskForm):
	user_id = IntegerField("User ID")
	submit = SubmitField('Add to wishlist')

def getItunesDataByArtistId(artistId):
	resp = requests.get('https://itunes.apple.com/lookup?id='+str(artistId))
	data = json.loads(resp.text)
	return data

def getItunesData(artist):
	params = {}
	params['term'] = artist
	resp = requests.get('https://itunes.apple.com/search?', params = params)
	data = json.loads(resp.text)
	return data

def get_or_create_record(
	db_session, 
	catalog_no, 
	artist, 
	title, 
	label, 
	record_format, 
	rating, 
	released, 
	release_id, 
	collection_folder, 
	date_added, 
	collection_media_condition, 
	collection_sleeve_condition, 
	collection_notes,
	price
	):
    record = db_session.query(Record).filter_by(catalog_no=catalog_no).first()
    if record:
        return record
    else:
        record = Record(
        	catalog_no=catalog_no, 
        	artist=artist, 
        	title=title, 
        	label=label, 
        	record_format=record_format, 
        	rating=rating, 
        	released=released, 
        	release_id=release_id,
        	collection_folder=collection_folder, 
        	date_added=date_added, 
        	collection_media_condition=collection_media_condition, 
        	collection_sleeve_condition=collection_sleeve_condition,
        	collection_notes=collection_notes,
        	price=price
        	)
        db_session.add(record)
        db_session.commit()
        return record

def get_or_create_sales_order_line(
	db_session, 
	catalog_no, 
	user_id
	):
    sales_order_line = db_session.query(Sales_Order).filter_by(catalog_no=catalog_no).filter_by(user_id=user_id).first()
    user = db_session.query(User).filter_by(id=user_id).first()
    if sales_order_line:
        return sales_order_line
    else:
        sales_order_line = Sales_Order(
        	catalog_no=catalog_no,
        	user_id=user_id
        	)
        db_session.add(sales_order_line)
        db_session.commit()
        flash("item added.")
        return sales_order_line

def get_or_create_user(
				db_session,
				userName,
            	email 
            	):
	user = db.session.query(User).filter_by(email=email).first()
	if user:
		return user
	else:
		user = User(
			userName=userName,
			email=email
			)
		db_session.add(user)
		db_session.commit()
		flash("user added.")
		return user
	

def get_number_of_records():
	records = Record.query.all()
	num_records = len(records)
	return num_records

## Error handlers
@app.errorhandler(404)
def four_oh_four(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
	num_records = get_number_of_records()
	all_records = []
	records = Record.query.all()
	for r in records:
		all_records.append((r.title, r.artist, r.catalog_no))
	return render_template('index.html',all_records=all_records,num_records=num_records)

@app.route('/add_records_to_db', methods=['GET','POST'])
def add_records_to_db():
    num_records = get_number_of_records()
    form = RecordForm()
    if form.validate_on_submit():
        if db.session.query(Record).filter_by(catalog_no=form.catalog_no.data).first(): 
            flash("You've already saved a record with that catalog number!")
        else:
            get_or_create_record(
            	db.session,
            	form.catalog_no.data, 
            	form.artist.data, 
            	form.title.data, 
            	form.label.data, 
            	form.record_format.data,
            	form.rating.data,
            	form.released.data,
            	form.release_id.data, 
            	form.collection_folder.data,
            	form.date_added.data, 
            	form.collection_media_condition.data, 
            	form.collection_sleeve_condition.data, 
            	form.collection_notes.data,
            	form.price.data
            	)
    return render_template('add_records_to_db.html', form=form,num_records=num_records)

@app.route('/record_view/<catalog_no>', methods=['GET', 'POST'])
def record_view(catalog_no):
	num_records = get_number_of_records()
	form=AddForm()
	record_dict = {}
	record = Record.query.filter_by(catalog_no=catalog_no).first()
	record_dict['catalog_no']=record.catalog_no, 
	record_dict['artist']=record.artist, 
	record_dict['title']=record.title,
	record_dict['label']=record.label, 
	record_dict['collection_sleeve_condition']=record.collection_sleeve_condition, 
	record_dict['collection_media_condition']=record.collection_media_condition,
	record_dict['collection_notes']=record.collection_notes
	record_dict['price']=record.price
	itunesdata = getItunesData(record_dict['artist'][0])
	artistId = itunesdata['results'][0]['artistId']
	bio_data = getItunesDataByArtistId(artistId)
	artist_url = bio_data['results'][0]['artistLinkUrl']
	artist_genre = bio_data['results'][0]['primaryGenreName']
	if form.validate_on_submit():
		user_id = form.user_id.data
		user = db.session.query(User).filter_by(id=user_id).first()
		if db.session.query(Sales_Order).filter_by(catalog_no=catalog_no).filter_by(user_id=user_id).first(): 
			flash("You've already saved a record with that catalog number!")
		elif not user:
			flash("User is not registered")
		else:
			new_sales_order_line = get_or_create_sales_order_line(
				db.session,
				catalog_no,
            	user_id 
            	)
			user_id = new_sales_order_line.user_id
	return render_template(
		'record_view.html', 
		record_dict=record_dict, 
		form=form, 
		num_records=num_records, 
		artist_url=artist_url, 
		artist_genre=artist_genre
		)

@app.route('/wishlist_view/<user_id>', methods=['GET','POST'])
def wishlist_view(user_id):
	num_records=get_number_of_records()
	list_of_sales_order_lines = []
	
	sales_order_lines = Sales_Order.query.filter_by(user_id=user_id).all()
	if not sales_order_lines:
		flash("No wishlist items for that user")
		return url_for(index)
		
	for line in sales_order_lines:
		list_of_sales_order_lines.append(line)
	return render_template(
		'wishlist_view.html', 
		user_id=user_id, 
		list_of_sales_order_lines=list_of_sales_order_lines,
		num_records=num_records
		)

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,userName=form.userName.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))




if __name__ == '__main__':
    db.create_all()
    manager.run() 