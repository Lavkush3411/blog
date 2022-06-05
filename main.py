from flask import Flask, render_template, redirect, url_for,request,flash,abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Column, ForeignKey, Integer
from wtforms import StringField, SubmitField,PasswordField,EmailField
from wtforms.validators import DataRequired, URL,InputRequired,Email
from flask_ckeditor import CKEditor, CKEditorField
import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin, LoginManager, current_user,login_required, login_user,logout_user
from functools import wraps
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CONFIGURE TABLE
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = relationship("Users",back_populates="posts")
    img_url = db.Column(db.String(250), nullable=False)
    userid=Column(Integer(),ForeignKey('users.id'))
    coments=relationship("Comments",back_populates='comment_obj')
class Users(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(30),nullable=False)
    password=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(30),nullable=False,unique=True)
    posts=relationship('BlogPost',back_populates='author')
    coments=relationship("Comments",back_populates='author_id')
class Comments(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    text=db.Column(db.String(100))
    userid=db.Column(Integer(),ForeignKey('users.id'))
    author_id=relationship("Users",back_populates="coments")
    postid=db.Column(Integer(),ForeignKey('blog_post.id'))
    comment_obj=relationship("BlogPost",back_populates='coments')


db.create_all()
# db.drop_all()

def admin_only(f):
    @wraps(f)
    def wrapper_function(*args,**kwargs):
        if current_user.is_authenticated and current_user.id==1:
            return f(*args,**kwargs)
        else:
            flash("Admin Privillages are needed !")
            return redirect(url_for('get_all_posts'))
    return wrapper_function
def login_required2(f):
    @wraps(f)
    def wrapper_function2(*args,**kwargs):
        if current_user.is_authenticated:
            return f(*args,**kwargs)
        else:
            flash("Login Is needed for this action !")
            return redirect(url_for('login'))
            
    return wrapper_function2

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired('fill')])
    subtitle = StringField("Subtitle", validators=[DataRequired('fill')])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class Register(FlaskForm):
    name=StringField('Name',validators=[DataRequired()])
    email=EmailField('Email',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[InputRequired()])
    register=SubmitField("Register")

class LoginForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    login=SubmitField("Login")

class ComentForm(FlaskForm):
    text=CKEditorField("Comment",validators=[InputRequired()])
    comment=SubmitField("Comment")

#LOGIN MANAGER

login_manager=LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route('/register',methods=["GET","POST"])
def register():
    reg_form=Register()
    if reg_form.validate_on_submit():
        email=reg_form.email.data
        hashed_password=generate_password_hash(reg_form.password.data,method="pbkdf2:sha256",salt_length=8)
        user=Users.query.filter_by(email=email).first()
        if not user: # if we found user=True then it will become notTrue=False condition will be False
            entry=Users(name=reg_form.name.data,
            email=email,
            password=hashed_password)
            db.session.add(entry)
            db.session.commit()
        else:
            flash("User Already exists Please login !!")
        return redirect(url_for('login'))
    return render_template('register.html',reg_form=reg_form)

@app.route('/login',methods=["GET","POST"])
def login():
    login_form=LoginForm()
    if login_form.validate_on_submit():
        email=login_form.email.data
        user=Users.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,login_form.password.data):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        elif user:
            flash("Wrong ID/Password. Try Again")
        else:
            flash("Register First")
            return redirect(url_for('register'))
    return render_template('login.html',login_form=login_form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/')
def get_all_posts():
    posts=BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:index>",methods=["GET","POST"])
def show_post(index):
    
    requested_post=BlogPost.query.get(index)
    coment_form=ComentForm()
    if request.method=="POST":
        entry=Comments(text=coment_form.text.data,
        author_id=current_user,
        comment_obj=requested_post
        )
        db.session.add(entry)
        db.session.commit()
    return render_template("post.html", post=requested_post,coment_form=coment_form)

@app.route("/new_post",methods=["GET","POST"])
@admin_only
def new_post():
    form=CreatePostForm()
    date=datetime.datetime.now().date()
    date=date.strftime('%B %d, %Y')
    if form.validate_on_submit():
        entry=BlogPost(
            title =request.form.get('title') ,
            subtitle =request.form.get('subtitle') ,
            body = form.body.data,
            author = current_user,
            date=date,
            img_url = request.form.get('img_url')
        )
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template('make-post.html',form=form,type="New Post")

@app.route("/edit/<post_id>",methods=["GET","POST"])
@admin_only
def edit_post(post_id):
    
    post=BlogPost.query.get(post_id)
    form=CreatePostForm(title=post.title,
    subtitle=post.subtitle,
    author=post.author,
    img_url=post.img_url,
    body=post.body,
    )
    if form.validate_on_submit():
        post.title=request.form.get('title')
        post.subtitle =request.form.get('subtitle') 
        post.body = form.body.data
        post.author = form.author.data
        post.img_url = request.form.get('img_url')
        db.session.commit()
        return redirect(url_for('get_all_posts'))
        
    return render_template('make-post.html',form=form,type="Edit Post",title=post.title)

@app.route('/delete/<id>')
@admin_only
def delete(id):
    data=BlogPost.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/about")
@login_required2
def about():
    return render_template("about.html")

@app.route("/contact")
@login_required2
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)