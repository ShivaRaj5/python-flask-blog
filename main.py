from flask import Flask, render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import os
import math
# from werkzeug import secure_filename
with open('config.json','r') as c:
    params=json.load(c)['params']
local_server=True
app = Flask(__name__)
app.secret_key="super-secret-key"
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME= params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)
class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_post']]
    last=math.ceil(len(posts)/int(params["no_of_post"]))
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params["no_of_post"]):(page-1)*int(params["no_of_post"])+int(params["no_of_post"])]
    if(page==1):
        prev="#"
        next="/?page="+str(page+1)
    elif(page==last):
        prev="/?page="+str(page-1)
        next = "#"
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)
    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)
@app.route("/about")
def about():
    return render_template('about.html',params=params)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone = phone, message = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('new message from '+name,sender=email,recipients=[params['gmail-user']],body=email+'\n'+message+'\n'+phone)
    return render_template('contact.html',params=params)
@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)
@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    if "user" in session and session['user']==params['user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)
    if request.method=="POST":
        username = request.form.get("uname")
        userpass = request.form.get("upass")
        if username==params['user'] and userpass==params['password']:
            # set the session variable
            session['uname']=username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)
    return render_template("login.html", params=params)
@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if "user" in session and session['user'] == params['user']:
        if request.method=='POST':
            box_title=request.form.get('title')
            tagline=request.form.get('tagline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            date=datetime.now()
            if sno=='0':# we will add new post
                post=Posts(title=box_title,tagline=tagline,slug=slug,content=content,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.tagline=tagline
                post.slug=slug
                post.content=content
                post.date=date
                db.session.commit()
                return redirect('/edit'+sno)
    post=Posts.query.filter_by(sno=sno).first()
    return render_template("edit.html", params=params,sno=sno,post=post)
@app.route("/uploader",methods=['GET','POST'])
def uploader():
    if "user" in session and session['user'] == params['user']:
        if request.method=='POST':
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],f))
    return "Uploaded Successfully"
@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect('/dashboard')
@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if "user" in session and session['user'] == params['user']:
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')
app.run(debug=True)


