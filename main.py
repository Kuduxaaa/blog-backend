#!/usr/bin/python3
# -*- encoding: utf-8 -*-
# Coded by Kuduxaaa

import os

from datetime import datetime

from flask import Flask, render_template, url_for, flash, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed

from werkzeug.utils import secure_filename

from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField, PasswordField, TextField
from wtforms.widgets import TextArea\

from hashlib import md5

basedir = os.path.abspath(os.path.dirname(__file__))

root = Flask(__name__)
root.config['SECRET_KEY'] = 'fl4$k'
root.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
root.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(root)


class AdminLoginForm(FlaskForm):
	email = StringField('ელ. ფოსტა', [DataRequired()])
	password = PasswordField('პაროლი', [DataRequired()])
	submit = SubmitField('შესვლა')


class NewPost(FlaskForm):
	title = StringField('სათაური', [DataRequired()], render_kw={"placeholder": "სათაური"})
	content = TextField('სტატია', validators=[DataRequired()], render_kw={"placeholder": "სტატია"}, widget=TextArea())
	tags = StringField('თეგები', render_kw={"placeholder": "თეგები (Keywords)"})
	image = FileField(validators=[FileAllowed(['png', 'jpg', 'jpeg'])])
	submit = SubmitField('დაემატება')


def is_logedin():
	try:
		return session['is_logedin']
	except KeyError:
		return False


class PostsModel(db.Model):
    __tablename__ = 'posts'

    post_id = db.Column(db.Integer, primary_key=True)
    post_title = db.Column(db.String)
    post_tags = db.Column(db.String)
    post_content = db.Column(db.Text)
    posted_at = db.Column(db.Date)
    image = db.Column(db.String)

    def __init__(self, title, tags, content, date, image):
        self.post_title = title
        self.post_tags = tags
        self.post_content = content
        self.posted_at = date
        self.image = image

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()



class UserModel(db.Model):
    __tablename__ = 'users'

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    created_at = db.Column(db.Date)

    def __init__(self, username, email, password, created_at):
        self.username = username
        self.email = email
        self.password = password
        self.created_at = created_at

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()




@root.route('/')
def index():
	posts = PostsModel.query.all()
	return render_template('index.html', posts=posts)


@root.route('/about')
def about():
	return render_template('about.html')


@root.route('/post/<int:post_id>')
def post(post_id):
	data = PostsModel.query.get(post_id)
	if data is not None:
		data_to_send = {'id': data.post_id,  'tags': data.post_tags, 'title': data.post_title, 'content': data.post_content, 'posted_at': data.posted_at}
		return render_template('post.html', data=data_to_send)
	else:
		return 'not found'



@root.route('/admin', methods=['GET', 'POST'])
def admin_index():
	if is_logedin():
		posts = PostsModel.query.all()
		return render_template('admin/index.html', posts=posts)
	else:
		return redirect(url_for('admin_login'))



@root.route('/admin/delete_post/<int:post_id>')
def admin_delete_post(post_id):
	if is_logedin():
		post = PostsModel.query.filter_by(post_id = post_id).one()
		db.session.delete(post)
		db.session.commit()
		return redirect(url_for('admin_index'))
	else:
		return redirect(url_for('index'))



@root.route('/admin/new', methods=['GET', 'POST'])
def admin_new_post():
	if is_logedin():
		new_post_form = NewPost()

		if new_post_form.validate_on_submit() and request.method == 'POST':
			date = datetime.now().date()
			image_file_name = 'no_image.png'
			post_title = new_post_form.title.data
			post_tags = new_post_form.tags.data
			post_content = new_post_form.content.data
			image_file = new_post_form.image.data
			if image_file:
				image_file_name = secure_filename(image_file.filename)
				new_post_form.image.data.save('uploads/' + image_file_name)


			saver = PostsModel(post_title, post_tags, post_content, date, image_file_name)
			saver.save_to_db()

			return redirect(url_for('admin_index'))
		return render_template('admin/new_post.html', form=new_post_form)
	else:
		return redirect(url_for('admin_login'))



@root.route('/admin/edit_post/<int:post_id>', methods=['GET', 'POST'])
def admin_edit_post(post_id):
	if is_logedin():
		data = PostsModel.query.get(post_id)
		edit_post_form = NewPost()

		if request.method == 'POST':
			image_file_name = 'no_image.png'
			data.post_title = edit_post_form.title.data
			data.post_tags = edit_post_form.tags.data
			data.post_content = edit_post_form.content.data
			image_file = edit_post_form.image.data
			if image_file:
				image_file_name = secure_filename(image_file.filename)
				edit_post_form.image.data.save('uploads/' + image_file_name)

			data.image = image_file_name
			data.post_content = edit_post_form.content.data
			db.session.commit()

			return redirect(url_for('admin_index'))
		return render_template('admin/new_post.html', form=edit_post_form, data=data)
	else:
		return redirect(url_for('admin_login'))




@root.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
	if not is_logedin():	
		login_form = AdminLoginForm()

		if login_form.validate_on_submit():
			email = login_form.email.data
			password = md5(str(login_form.password.data).encode()).hexdigest()

			data = UserModel.query.filter_by(email=email, password=password).first()
			if data is not None:
				session['is_logedin'] = True
				session['email'] = email
				session['username'] = data.username
				session['password'] = data.password

				return redirect(url_for('admin_index'))
			else:
				return render_template('admin/login.html',login_form = login_form, alert='ელ. ფოსტა ან პაროლი არასწორია')

		return render_template('admin/login.html', login_form = login_form)
	else:
		return redirect(url_for('admin_index'))





@root.route('/admin/logout')
def adimn_logout():
	if is_logedin():
		session.clear()
	return redirect(url_for('index'))




if __name__ == '__main__':
	root.run()