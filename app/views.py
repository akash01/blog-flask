from app import app, db, login_manager, models
import datetime
import os

from flask import Flask, render_template, request, flash, session, url_for, redirect, g
from flask.ext.login import login_user, logout_user, current_user, login_required

from forms import SignupForm, PostForm, LoginForm
from models import  User, Post, Tag,ROLE_USER, ROLE_ADMIN

from config import POSTS_PER_PAGE
from config import MAX_SEARCH_RESULTS

def remove_unused_tags():
    session.query(models.Tag).\
        filter(~models.Post.posts.any()).\
        delete(synchronize_session=False)

@login_manager.user_loader
def load_user(uid):
    return User.query.filter_by(uid = session['uid']).first()

@app.before_request
def before_request():
    g.user = current_user

#index, home page
@app.route('/')
@app.route('/index')
@app.route('/index/<int:page>')
def index(page=1):
    recent_post = Post.query.order_by(Post.pub_date.desc()).limit(5).all()
    posts = Post.query.order_by(Post.pub_date.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html', posts=posts, recent_post = recent_post, cur_page = 'index')

#contact
@app.route('/contact')
def contact():
  return render_template('contact.html')

#post detail view
@app.route('/post/<id>',)
def post(id):
    user = User.query.filter_by(email = session['email']).first()
    post = Post.query.filter(Post.id == id ).first()
    recent_post = Post.query.order_by(Post.pub_date.desc()).limit(5).all()
    return render_template('post_detail.html',post=post,recent_post=recent_post,user=user )

#recent posts
@app.route('/recent/<id>',)
def recent_post(id):
    user = User.query.filter_by(email = session['email']).first()
    post = Post.query.filter_by(id=id).first()
    recent_post = Post.query.order_by(Post.pub_date.desc()).limit(5).all()
    return render_template('post_detail.html', post=post, recent_post =recent_post,user=user)

@app.route('/tag/<tag>', defaults={'page': 1})
@app.route('/tag/<tag>/<int:page>/')
def show_tag(tag, page):
    tagres = Tag.query.filter_by(name=tag).first()
    posts = tagres.posts.order_by(Post.pub_date.desc()).paginate(page, POSTS_PER_PAGE, False)
    recent_post = Post.query.order_by(Post.pub_date.desc()).limit(5).all()
    flash("Search result for tag: "+ tag)
    return render_template('index.html', posts=posts, recent_post = recent_post, cur_page = 'tag/'+tag )

@app.route('/search', methods = ['POST'])
def search():
    query = request.form["search"]
    if query == "":
        flash('Search query empty.')
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query = request.form["search"]))

# search 
@app.route('/search_results/<query>')
def search_results(query):
    recent_post = Post.query.order_by(Post.pub_date.desc()).limit(5).all()
    results = db.session.execute("SELECT * FROM post WHERE title_tsv @@ plainto_tsquery('"+query+"') OR body_tsv @@ plainto_tsquery('"+query+"')")
    
    if not results:
        return redirect(url_for('index'))
    ## if result not found
    if results.rowcount == 0:
        flash('Sorry no result found, Try again.')
        results = ""
        #return redirect(url_for('index'))
    return render_template('search.html',
        query = query,
        recent_post = recent_post,
        results = results)     

#login
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if 'email' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template('login.html', form=form)
        else:
            session['email'] = form.email.data
            flash('Login successful !')
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template('login.html', form=form)

#sign-up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if 'email' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        if form.validate() == False:
            return render_template('signup.html', form=form)
        else:
            newuser = User(form.firstname.data, form.lastname.data, form.email.data, form.password.data )
            db.session.add(newuser)
            db.session.commit()
            session['email'] = newuser.email
            flash('Registraction successful')
            return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template('signup.html', form=form)

#signout
@app.route('/signout')
def signout():

    if 'email' not in session:
        return redirect(url_for('login'))

    session.pop('email', None)
    flash('Logout successful')
    return redirect(url_for('index'))

#profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = PostForm()

    if 'email' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(email = session['email']).first()

    if request.method == 'POST':

        if form.validate() == False:
            return render_template('profile.html', form=form, user=user)
        else:
            post = Post(form.title.data,form.body.data, datetime.datetime.now(), user.id)
            db.session.add(post)
            db.session.commit()
            for tag in form.tags.data.split(','):
                tag = Tag.get_or_create(tag)
                tag.posts.append(post)
                db.session.commit()
            flash("Your post in live now!")
            return redirect(url_for('index'))

    elif request.method == 'GET':
        if user.role == ROLE_ADMIN:
            return redirect(url_for('admin'))
        if user.role == ROLE_USER:
            return render_template('profile.html', form=form, user=user)

# admin page
@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/<int:page>', methods=['GET', 'POST'])
def admin(page=1):
    form = PostForm()
    if 'email' not in session:
        return redirect(url_for('login'))
    posts = Post.query.paginate(page, POSTS_PER_PAGE, False)
    return render_template('admin.html', posts=posts,form = form, cur_page = 'admin')

@app.route('/delete/<int:id>',)
def delete_post(id):
    post_delete = Post.query.filter_by( id=id).first()
    db.session.delete(post_delete )
    db.session.commit()
    flash(post_delete.title + " has been deleted" )
    return redirect(url_for('admin'))

@app.route('/edit', methods=['GET', 'POST'])
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    print id
    post_edit = Post.query.filter_by(id=id).first()
    form = PostForm(request.form, post_edit)

    if request.method == 'GET':
        tagname = []
        form.title.data = post_edit.title
        form.body.data = post_edit.body
        for tag in post_edit.tags:
            tagname.append(tag.name)
        tags = ', '.join(tagname)
        form.tags.data = tags
        #form.populate_obj(post_edit)

    if request.method == 'POST':
        if form.validate() == False:
            return render_template('admin.html', form=form)
        else:
            tags = list(post_edit.tags)
            for tag in tags:
                post_edit.tags.remove(tag)

            # Parse new tags
            tags = map(lambda x: x.strip(), form.tags.data.split(","))
            # Remove empty tags
            tags = [tag for tag in tags if not tag == ""]

            for tag in tags:
                tag = Tag.get_or_create(tag)
                tag.posts.append(post_edit)
                db.session.commit()

            post_edit.title = form.title.data
            post_edit.body = form.body.data
            post_edit.pub_date = datetime.datetime.now()
            db.session.merge(post_edit)
            db.session.commit()
            
            flash('Successfully updated post')
            return redirect(url_for('admin'))
    return render_template('admin.html', form=form,posts="",admin=admin,id=id)

@app.route('/add/', methods=['GET', 'POST'])
def add_post_admin():
    form = PostForm()
    user = User.query.filter_by(email = session['email']).first()
    
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('admin.html', form=form, user=user)
        else:
            post = Post(form.title.data,form.body.data, datetime.datetime.now(), user.id)
            db.session.add(post)
            db.session.commit()
            # Parse new tags
            tags = map(lambda x: x.strip(), form.tags.data.split(","))
            tags = [tag for tag in tags if not tag == ""]

            for tag in tags:
                tag = Tag.get_or_create(tag)
                tag.posts.append(post)
                db.session.commit()
            flash("Admin Your post in live now!")
            return redirect(url_for('admin'))

    elif request.method == 'GET':
        return render_template('admin.html', form=form, user=user, posts="")

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
