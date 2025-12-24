from flask import Flask,render_template,request,flash,redirect,url_for,session,logging
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form,StringField,PasswordField,TextAreaField,validators,EmailField
from passlib.hash import sha256_crypt
from functools import wraps
app= Flask(__name__)
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='yAsh@2917'
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'
# init mysql
mysql=MySQL(app)
# article_data=Articles()
app.secret_key="MYSECRETKEY123"
@app.route('/')
def home():
    
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    cur=mysql.connection.cursor()
    
    # get articles
    result=cur.execute('SELECT * FROM articles')
    articles=cur.fetchall()
    if result>0:
        return render_template('articles.html',articles=articles)
    else:
        msg="No articles found"
        return render_template('articles.html',msg=msg)
    cur.close()
@app.route('/article/<int:id>/')
def article(id):
    cur=mysql.connection.cursor()
    
    # get articles
    result=cur.execute('SELECT * FROM articles WHERE id= %s',[id])
    article=cur.fetchone()
            
    return render_template('display_article.html',article=article)
class RegisterForm(Form):
    name=StringField('Name',[validators.length(min=1,max=50)])
    username=StringField('Username',[validators.length(min=4,max=25)])
    email=EmailField('Email',[validators.length(min=6,max=50)])
    password=PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')   
    ])
    confirm=PasswordField('Confirm Password')
    
@app.route('/register',methods=['GET','POST'])
def register():
    form= RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        # create cursor
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
        # commit
        mysql.connection.commit()
        # close connection
        cur.close()
        
        flash("User registered successfully","success")
        return redirect(url_for('home'))
    return render_template('register.html',form=form)
 
def is_logged_in(f):
    @wraps(f)   
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash("Unauthorized, Please Login",'danger')
            return redirect(url_for('home'))
    return wrap
            
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password_candidate=request.form['password']
        # Create cursor
        
        cur=mysql.connection.cursor()
        
        # get user by username
        result= cur.execute("SELECT * FROM users WHERE username= %s",[username])
        if result>0:
            # get stored hash 
            data=cur.fetchone()
            password=data['password']
            
            # Compare password
            if sha256_crypt.verify(password_candidate,password):
                # app.logger.info("PASSWORD MATCHED")
                # Passed
                session['logged_in']=True
                session['username']=username
                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error="Invalid Password"
                return render_template('login.html',error=error)
            cur.close()
        else:
            error="Username not found"
            return render_template('login.html',error=error)
                
        
    return render_template('login.html')

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur=mysql.connection.cursor()
    
    # get articles
    result=cur.execute('SELECT * FROM articles')
    articles=cur.fetchall()
    if result>0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg="No articles found"
        return render_template('dashboard.html',msg=msg)
    cur.close()

class ArticleForm(Form):
    title=StringField('Title',[validators.length(min=1,max=255)])
    body=TextAreaField('Body',[validators.length(min=30)])
    
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data
        # Cursor
        cur= mysql.connection.cursor()
        # Execute 
        cur.execute('INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)',(title,body,session['username']))
        # Commit
        mysql.connection.commit()
        
        # close
        cur.close()
        flash("Article added successfully",'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)
    
@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    # Cursor
    cur= mysql.connection.cursor()
        # Execute 
    result=  cur.execute('SELECT * FROM articles WHERE id=%s',[id])
    article= cur.fetchone()
    
    form=ArticleForm(request.form)
    # Populate form
    form.title.data= article['title']
    form.body.data= article['body']
    
    
    if request.method=='POST' and form.validate():
        title=request.form['title']
        body=request.form['body']
        # Cursor
        cur= mysql.connection.cursor()
        # Execute 
        cur.execute('UPDATE articles SET title=%s, body=%s WHERE id=%s',(title,body,id))
        # Commit
        mysql.connection.commit()
        
        # close
        cur.close()
        flash("Article updated successfully",'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form=form)       
    
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    #    Create cursor
    
    cur= mysql.connection.cursor()
    # execute
    cur.execute("DELETE FROM articles WHERE id=%s",[id])
     # Commit
    mysql.connection.commit()
        
        # close
    cur.close()
    flash("Article deleted successfully",'success')
    return redirect(url_for('dashboard'))
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))   

if __name__=="__main__":
    app.run(debug=True)