#####################
#
# Record Store App
# SI364 Final Project
#
##################### 

import os
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, IntegerField, DateField, FloatField, BooleanField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
import random
from flask_migrate import Migrate, MigrateCommand # needs: pip/pip3 install flask-migrate
from flask_mail import Mail, Message
from threading import Thread
from werkzeug import secure_filename
from flask_bootstrap import Bootstrap


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
Bootstrap(app)
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


manager = Manager(app)
db = SQLAlchemy(app) 
migrate = Migrate(app, db) 
manager.add_command('db', MigrateCommand) 
mail = Mail(app) 



class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(255))
    email = db.Column(db.String(255))
    
    def __repr__(self):
        return "User: {} & email: {}".format(self.userName,self.email)

class Sales_Order(db.Model):
    __tablename__ = "sales_orders"
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("records.id"))
    
    def __repr__(self):
        return "Sales Order: {} & URL: {}".format(self.id,self.record_id)

class Record(db.Model):
	__tablename__ = "records"
	id = db.Column(db.Integer, primary_key=True)
	catalog_no = db.Column(db.Integer)
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

class UploadForm(FlaskForm):
    file = FileField()

class AddForm(FlaskForm):
	add = BooleanField("Add to wishlist?")
	submit = SubmitField('Submit')

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



@app.route('/', methods=['GET', 'POST'])
def index():
    records = Record.query.all()
    num_records = len(records)
    print(len(records))
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
    return render_template('index.html', form=form,num_records=num_records)

@app.route('/all_records')
def see_all():
    all_records = []
    records = Record.query.all()
    for r in records:
    	all_records.append((r.title, r.artist))
    
    return render_template('all_records.html',all_records=all_records)

@app.route('/record_view/<catalog_no>', methods=['GET', 'POST'])
def record_view(catalog_no):
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
	return render_template('record_view.html', record_dict=record_dict, form=form)




if __name__ == '__main__':
    db.create_all()
    manager.run() 