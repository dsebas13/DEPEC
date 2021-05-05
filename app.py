from flask import Flask, render_template, request, redirect, url_for, flash, session

from flask_mysqldb import MySQL

#mySql conection
app = Flask(__name__)
app.config["DEBUG"] = True
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'depec' 
mysql = MySQL(app)


# settings
app.config['SECRET_KEY'] = 'mysecretkey'


# HOME
#revisar
@app.route('/home')
def home():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:     
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    if session['rol'] == 1:
        cur.execute('SELECT * FROM cv')
    else:
        cur.execute('SELECT * FROM cv join usuario on cv.IdUsuario = usuario.IdUsuario WHERE dni = %s', [session['dni']])
        data = cur.fetchall()
        return render_template('home.html', cv = data, session = session)
    cur.execute('SELECT * FROM cv join usuario on cv.IdUsuario = usuario.IdUsuario  WHERE dni = %s', [session['dni']])
    conta = cur.fetchall()
    return render_template('home.html', session = session, cv = conta)

@app.route('/')
def my_form():
    if 'loggedin' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM cv')
        data = cur.fetchall()
        return render_template('home.html', cv = data)
    else:
        return render_template('login.html')

# LOGIN
@app.route('/', methods= ['POST'])
def login():
    username = request.form['u']
    password = request.form['p']
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuario where email = %s and password = %s', (username, password))
    account = cur.fetchone()
    if account:
        session['loggedin'] = True
        session['id'] = account[0]
        session['username'] = account[3]
        session['name'] = account[1]
        session['surname'] = account[2]
        session['rol'] = account[6]
        session['dni'] = account[7]
        return redirect(url_for('home'))
    else:
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html') 

# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile')
def profile(): 
 # Check if account exists using MySQL
    cur = mysql.connection.cursor()
  
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cur.execute('SELECT * FROM accounts WHERE id = %s', [session['id']])
        account = cur.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
       
# logoaut
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port = 5000, debug = True)




