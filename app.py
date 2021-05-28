from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_mysqldb import MySQL
import base64
import PyPDF2
import fitz
import os
from os import remove
from base64 import b64decode


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
app.config['UPLOAD_FOLDER'] = './'

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
    cur.execute('SELECT * FROM cv inner join usuario on cv.IdUsuario = usuario.IdUsuario  WHERE dni = %s', [session['dni']])
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

# -----CV--------------------------- #
# pantalla carga cv
@app.route('/cv')
def Index():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    cur.execute('SELECT * FROM cv where IdUsuario = %s', [session['id']])
    tienecv = cur.fetchone()
    if tienecv:
        return render_template('home.html', session = session)
    else:
        cur.execute('SELECT direccion.IdDireccion,direccion.nombre FROM direccion group by direccion.IdDireccion order by direccion.IdDireccion')
        direc = cur.fetchall()
        cur.execute('SELECT *,DATE_ADD(fechaNacimiento,INTERVAL 18 YEAR) as mayoredad,CURRENT_DATE as hoy FROM usuario join direccion on usuario.IdUsuario=direccion.IdDireccion WHERE dni = %s', [session['dni']])
        data = cur.fetchone()
        cur.execute('SELECT * FROM atributo group by atributo order by atributo')
        atrib = cur.fetchall()
        cur.execute('SELECT * FROM nivel order by IdNivel')
        level = cur.fetchall()
        if data:
            return render_template('index.html', cv = data, direcccio = direc, atrib = atrib, level = level) 
        else:
            return render_template('home.html', cv = data, session = session)

# pantalla grilla cvs cargados
@app.route('/gridcv')
def gridcv():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    cur.execute('SELECT * FROM cv join usuario on cv.IdUsuario = usuario.IdUsuario')
    data = cur.fetchall()
    #cv del usuario
    cur.execute('SELECT * FROM cv join usuario on cv.IdUsuario = usuario.IdUsuario WHERE dni = %s', [session['dni']])
    datacv = cur.fetchall()
    return render_template('gridcv.html', cv = data, cvuser = datacv)

        
# pantalla edicion cv
@app.route('/edit/<string:id>')
def get_cv(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    ###datos ingresados por el usuario en tabla cv
    cur.execute('SELECT * FROM cv join usuario on cv.IdUsuario = usuario.IdUsuario WHERE cv.IdCV = {0}'.format(id))
    cvuser = cur.fetchone()
    b64 = cvuser[5]
    bytes = b64decode(b64, validate=True)

# Perform a basic validation to make sure that the result is a valid PDF file
# Be aware! The magic number (file signature) is not 100% reliable solution to validate PDF files
# Moreover, if you get Base64 from an untrusted source, you must sanitize the PDF contents
    # Write the PDF contents to a local file
    f = open('./templates/file.pdf', 'wb')
    f.write(bytes)
    f.close()


    cur.execute('SELECT * FROM cvatributo join nivel on cvatributo.IdNivel = nivel.IdNivel WHERE cvatributo.IdCV = {0}'.format(id))
    atribuser = cur.fetchall()
    cur.execute('SELECT direccion.IdDireccion,direccion.nombre FROM direccion group by direccion.IdDireccion order by direccion.IdDireccion')
    direc = cur.fetchall()
    cur.execute('SELECT *,DATE_ADD(fechaNacimiento,INTERVAL 18 YEAR) as mayoredad,CURRENT_DATE as hoy FROM usuario join direccion on usuario.IdUsuario=direccion.IdDireccion WHERE dni = %s', [session['dni']])
    data = cur.fetchone()
    cur.execute('SELECT * FROM atributo group by atributo order by atributo')
    atrib = cur.fetchall()
    cur.execute('SELECT * FROM nivel order by IdNivel')
    level = cur.fetchall()
    return render_template('edit-cv.html', cv = data[0], direcccio = direc, atrib = atrib, level = level)


# pantalla vista de un puesto cargado
@app.route('/viewjob/<string:id>')
def viewjob(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    cur.execute('SELECT *,datediff(CURRENT_DATE, fechaPublicacion) as dias FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion join usuario on busqueda.IdUsuario = usuario.IdUsuario WHERE busqueda.IdBusqueda = {0}'.format(id))
    data = cur.fetchall()
    cur.execute('SELECT * FROM postulacion where IdUsuario = %s and IdBusqueda = %s',[session['id'],id])
    UserPostulacion = cur.fetchall()
    print(UserPostulacion)
    cur.execute('SELECT telefono FROM cv where IdUsuario = %s', [session['id']])
    tele = cur.fetchone()
    cur.execute('SELECT IdPerfil FROM busqueda WHERE IdBusqueda = %s', [id])
    idperfilbusqueda = cur.fetchone()
    cur.execute('SELECT descripcion from perfil where IdPerfil = %s', [idperfilbusqueda])
    nombreperfil = cur.fetchone()
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "I" ', [idperfilbusqueda])
    dataI = cur.fetchall()
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "E" ', [idperfilbusqueda])
    dataE = cur.fetchall()
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo FROM atributo left join perfil_atributo on perfil_atributo.IdAtributo = atributo.IdAtributo and perfil_atributo.IdPerfil = %s WHERE atributo.tipoAtributo = "A" ', [idperfilbusqueda])
    dataA = cur.fetchall()
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "T" ', [idperfilbusqueda])
    dataT = cur.fetchall()
    return render_template('viewjob.html', UserPostulacion = UserPostulacion, busqueda = data[0], tele = tele, nombreperfil = nombreperfil, dataI = dataI ,dataE = dataE, dataT = dataT ,dataA = dataA)

# pantalla puestos cargados
@app.route('/gridjobs', methods= ['GET','POST'])
def gridjobs():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.form:
        if request.form['iddireccion'] == '1':
            cur.execute('SELECT *,datediff(CURRENT_DATE, fechaPublicacion) as dias,CURRENT_DATE FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion order by dias')
            data = cur.fetchall()
        else:
            filtrodireccion = str(request.form['iddireccion'][:2])
            cur.execute('SELECT *,datediff(CURRENT_DATE, fechaPublicacion) as dias,CURRENT_DATE FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion where busqueda.IdDireccion = %s order by dias', [filtrodireccion])
            data = cur.fetchall()
    else:
        cur.execute('SELECT *,datediff(CURRENT_DATE, fechaPublicacion) as dias,CURRENT_DATE FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion order by dias')
        data = cur.fetchall()
    cur.execute('SELECT * FROM postulacion where IdUsuario = %s',[session['id']])
    UserPostulacion = cur.fetchall()
    cur.execute('SELECT direccion.IdDireccion, direccion.nombre as dia FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion where busqueda.fechaPublicacion <= CURRENT_DATE group by direccion.IdDireccion order by direccion.IdDireccion')
    direc = cur.fetchall()
    print(data)
    print(UserPostulacion)
    return render_template('gridjobs.html', UserPostulacion = UserPostulacion, busqueda = data, direcccio = direc)
# post nuevo puesto
@app.route('/mostrargrilla', methods= ['POST'])
def mostrargrilla():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.form['iddireccion'] == '1':
        cur.execute('SELECT *,datediff(CURRENT_DATE, fechaPublicacion) as dias,CURRENT_DATE FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion order by dias')
        data = cur.fetchall()
    else:
        filtrodireccion = str(request.form['iddireccion'][:2])
        cur.execute('SELECT *,datediff(CURRENT_DATE, fechaPublicacion) as dias,CURRENT_DATE FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion where busqueda.IdDireccion = %s order by dias', [filtrodireccion])
        data = cur.fetchall()
    cur.execute('SELECT direccion.IdDireccion,direccion.nombre as dia FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion where busqueda.fechaPublicacion <= CURRENT_DATE group by direccion.IdDireccion order by direccion.IdDireccion')
    direc = cur.fetchall()
    return render_template('gridjobs.html', busqueda = data, direcccio = direc)

# pantalla alta nuevo puestos
@app.route('/nuevopuesto')
def nuevopuesto():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if session['rol'] == 1:
        cur.execute('SELECT direccion.IdDireccion, direccion.nombre ,CURRENT_DATE as dia, DATE_ADD(CURRENT_DATE,INTERVAL 30 DAY) as mastreinta FROM direccion join usuario on direccion.IdDireccion = usuario.IdDireccion WHERE IdUsuario = %s',[session['id']])
        direc = cur.fetchone()
        cur.execute('SELECT IdPerfil, descripcion FROM perfil')
        dataperfil = cur.fetchall()
        print(dataperfil)
        return render_template('nuevopuesto.html', direccio = direc, dataperfil = dataperfil )
    else:
        return render_template('home.html')  

# pantalla edicion puesto
@app.route('/editjobs/<string:id>')
def editjobs(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    if session['rol'] == 1:
        cur.execute('SELECT *,CURRENT_DATE as dia FROM direccion')
        direc = cur.fetchall()
        cur.execute('SELECT *,CURRENT_DATE as dia, DATE_ADD(CURRENT_DATE,INTERVAL 30 DAY) as mastreinta FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion WHERE busqueda.IdBusqueda = {0}'.format(id))
        data = cur.fetchall()
        return render_template('editjobs.html', busqueda = data[0], direcccio = direc)
    else:
        return render_template('home.html')  

# post actualizacion puesto
@app.route('/updatejobs/<string:id>', methods = ['GET', 'POST'])
def updatejobs(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.method == 'POST':
        IdDireccion = str(request.form['iddireccion'][:2])
        puesto = request.form['puesto']
        fechaPublicacion = request.form['fecha']
        vacantes = request.form['vacantes']
        alcance = request.form['alcance']
        tareas = request.form['tareas']
        contacto = request.form['contacto']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE busqueda
            SET IdDireccion = %s,
                puesto = %s,
                fechaPublicacion = %s,
                vacantes = %s,
                alcance = %s,
                tareas = %s,
                contacto = %s
            WHERE id = %s
        """, (IdDireccion, puesto, fechaPublicacion, vacantes, alcance, tareas, contacto, id))
        mysql.connection.commit()
        flash('Puesto actualizado correctamente')
        return redirect(url_for('mygridjobs'))

# post nuevo puesto
@app.route('/addnuevopuesto', methods= ['POST'])
def addnuevopuesto():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if session['rol'] == 1:
        if request.method == 'POST':
            IdDireccion = str(request.form['iddireccion'][:2])
            puesto = request.form['puesto']
            fechaPublicacion = request.form['fecha']
            vacantes = request.form['vacantes']
            alcance = request.form['alcance']
            tareas = request.form['tareas']
            IdUser = session['id']
            IdEstado = 1
            IdPerfil = str(request.form['perfil'][:2])
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO busqueda (IdDireccion, puesto, fechaPublicacion, vacantes, alcance, tarea, IdUsuario , IdEstado, IdPerfil) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (IdDireccion, puesto, fechaPublicacion, vacantes, alcance, tareas, IdUser, IdEstado, IdPerfil))
            mysql.connection.commit()
            flash('Puesto agregado correctamente')
            return redirect(url_for('mygridjobs'))
    else:
        return render_template('home.html')   


# post nuevo cv
@app.route('/add_cv', methods= ['POST'])
def add_cv():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.method == 'POST':
        f = request.files['archivo']
        # Guardamos el archivo en el directorio "Archivos PDF"
        
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        
        ### pdf a texto
        pdf_doc = f.filename
        documento = fitz.open(pdf_doc)
        
        for pagina in documento:
            texto = pagina.getText().encode("utf8")

        ### pdf a base 64
        with open((os.path.join(app.config['UPLOAD_FOLDER'], f.filename)), "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        
        telefono = request.form['telefono']

        IdUsuario = session['id']
        IdPerfil = 1
        fechaCreacion  = datetime.now()
        CvRead = texto
        CvBase64 = encoded_string


        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO cv (telefono, IdUsuario, fechaCreacion , CvRead, CvBase64) VALUES (%s, %s, %s, %s, %s)',
        (telefono, IdUsuario, fechaCreacion , CvRead, CvBase64))
        mysql.connection.commit()
        cur.execute('SELECT IdCV FROM cv where cv.IdUsuario = %s order by IdCV desc', [session['id']])
        idCVs = cur.fetchone()

        if ((request.form['iddireccion']) or (request.form['iddireccion1']) or (request.form['iddireccion2'])):
            if request.form['iddireccion']:
                IdDireccion = request.form['iddireccion']
                FechaDesde = request.form['fechaIngreso']
                FechaHasta = request.form['fechaEgreso']
                Puesto = request.form['puesto']
                Tarea = request.form['tareas']
                IdCV = idCVs
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO cvdireccion (IdDireccion, FechaDesde, FechaHasta, Puesto, Tarea,IdCV) VALUES (%s, %s, %s, %s, %s, %s)',
                (IdDireccion, FechaDesde, FechaHasta, Puesto, Tarea, IdCV))
                mysql.connection.commit()

                if request.form['iddireccion1']:
                    IdDireccion = request.form['iddireccion1']
                    FechaDesde = request.form['fechaIngreso1']
                    FechaHasta = request.form['fechaEgreso1']
                    Puesto = request.form['puesto1']
                    Tarea = request.form['tareas1']
                    IdCV = idCVs
                    cur = mysql.connection.cursor()
                    cur.execute('INSERT INTO cvdireccion (IdDireccion, FechaDesde, FechaHasta, Puesto, Tarea, IdCV) VALUES (%s, %s, %s, %s, %s, %s)',
                    (IdDireccion, FechaDesde, FechaHasta, Puesto, Tarea, IdCV))
                    mysql.connection.commit()

                    if request.form['iddireccion2']:
                        IdDireccion = request.form['iddireccion2']
                        FechaDesde = request.form['fechaIngreso2']
                        FechaHasta = request.form['fechaEgreso2']
                        Puesto = request.form['puesto2']
                        Tarea = request.form['tareas2']
                        IdCV = idCVs
                        cur = mysql.connection.cursor()
                        cur.execute('INSERT INTO cvdireccion (IdDireccion, FechaDesde, FechaHasta, Puesto, Tarea, IdCV) VALUES (%s, %s, %s, %s, %s, %s)',
                        (IdDireccion, FechaDesde, FechaHasta, Puesto, Tarea, IdCV))
                        mysql.connection.commit()

        if ('formcheck' in request.form):   
            for f in request.form.getlist('formcheck'):
                IdCV = idCVs
                IdAtributo = f
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo) VALUES (%s, %s)',
                (IdCV, IdAtributo))
                mysql.connection.commit()

        if ((request.form['estudios']) or (request.form['estudios1']) or (request.form['estudios2'])):
            IdCV = idCVs
            IdAtributo = request.form['estudios']
            IdNivel = request.form['estado']
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
            (IdCV, IdAtributo, IdNivel))
            mysql.connection.commit()

            if request.form['estudios1']:
                IdCV = idCVs
                IdAtributo = request.form['estudios1']
                IdNivel = request.form['estado1']
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
                (IdCV, IdAtributo, IdNivel))
                mysql.connection.commit()

                if request.form['estudios2']:
                    IdCV = idCVs
                    IdAtributo = request.form['estudios2']
                    IdNivel = request.form['estado2']
                    cur = mysql.connection.cursor()
                    cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
                    (IdCV, IdAtributo, IdNivel))
                    mysql.connection.commit()


        if ((request.form['idioma']) or (request.form['idioma1']) or (request.form['idioma2'])):
            IdCV = idCVs
            IdAtributo = request.form['idioma']
            IdNivel = request.form['nivel']
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
            (IdCV, IdAtributo, IdNivel))
            mysql.connection.commit()

            if request.form['idioma1']:
                IdCV = idCVs
                IdAtributo = request.form['idioma1']
                IdNivel = request.form['nivel1']
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
                (IdCV, IdAtributo, IdNivel))
                mysql.connection.commit()

                if request.form['idioma2']:
                    IdCV = idCVs
                    IdAtributo = request.form['idioma2']
                    IdNivel = request.form['nivel2']
                    cur = mysql.connection.cursor()
                    cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
                    (IdCV, IdAtributo, IdNivel))
                    mysql.connection.commit()
            
        if ((request.form['Herramientas']) or (request.form['Herramientas1']) or (request.form['Herramientas2'])):
            IdCV = idCVs
            IdAtributo = request.form['Herramientas']
            IdNivel = request.form['niveltecnico']
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
            (IdCV, IdAtributo, IdNivel))
            mysql.connection.commit()

            if request.form['Herramientas1']:
                IdCV = idCVs
                IdAtributo = request.form['Herramientas1']
                IdNivel = request.form['niveltecnico1']
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
                (IdCV, IdAtributo, IdNivel))
                mysql.connection.commit()

                if request.form['Herramientas2']:
                    IdCV = idCVs
                    IdAtributo = request.form['Herramientas2']
                    IdNivel = request.form['niveltecnico2']
                    cur = mysql.connection.cursor()
                    cur.execute('INSERT INTO cvatributo (IdCV, IdAtributo, IdNivel) VALUES (%s, %s, %s)',
                    (IdCV, IdAtributo, IdNivel))
                    mysql.connection.commit()

            
        flash('Curriculum agregado correctamente')
        return redirect(url_for('Index'))


# post actualizacion cv
@app.route('/updatecv/<string:id>', methods = ['POST'])
def updatecv(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        telefono = request.form['telefono']
        email = request.form['email']
        birthdate = request.form['birthdate']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE cv
            SET nombre = %s,
                apellido = %s,
                dni = %s,
                telefono = %s,
                email = %s,
                birthdate = %s
            WHERE id = %s
        """, (nombre, apellido, dni, telefono, email, birthdate, id))
        mysql.connection.commit()
        flash('Contacto actualizado correctamente')
        return redirect(url_for('gridcv'))

# borrado de cv        
@app.route('/delete/<string:id>')
def delete_cv(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    cur.execute('DELETE FROM cv WHERE idCV = {0}'.format(id))
    mysql.connection.commit()
    flash('Contact Removed Successfully')
    return redirect(url_for('gridcv'))

# borrado de puesto           
@app.route('/deletejobs/<string:id>')
def deletejobs(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if session['rol'] == 1:
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM busqueda WHERE id = {0}'.format(id))
        mysql.connection.commit()
        flash('Puesto Removed Successfully')
        return redirect(url_for('gridjobs'))
    else:
        return render_template('home.html')

# post nueva postulacion
@app.route('/postular/<string:id>', methods= ['POST'])
def postular(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.method == 'POST':
        IdUsuario = session['id']
        IdBusqueda = id
        fechapostulacion = datetime.now()
        IdEstado = 1
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO postulacion (IdUsuario, IdBusqueda, fechapostulacion, IdEstado) VALUES (%s, %s, %s, %s)',
        (IdUsuario, IdBusqueda, fechapostulacion, IdEstado))
        mysql.connection.commit()
        flash('Postulacion correcta')
        return redirect(url_for('gridjobs'))

# pantalla puestos cargados
@app.route('/mygridjobs')
def mygridjobs():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    cur.execute('SELECT *,datediff(CURRENT_DATE, fechaPublicacion) as dias,CURRENT_DATE FROM busqueda join direccion on busqueda.IdDireccion = direccion.IdDireccion where busqueda.IdUsuario = %s order by dias', [session['id']] )
    data = cur.fetchall()
    a = len(data)
    print(data)
    if data:
        return render_template('mygridjobs.html', busqueda = data, cantregistros = a)
    else:
        return render_template('home.html')
   
#abm atributos
@app.route('/atributo/<string:id>')
def atributo(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    cur.execute('SELECT *,ROW_NUMBER() OVER (ORDER BY atributo) AS Nro FROM atributo WHERE tipoAtributo = %s group by atributo', [id])
    data = cur.fetchall()
    if id == 'I':
        dato = 'Idioma'
    if id == 'T':
        dato = 'Conocimientos Técnicos'
    if id == 'A':
        dato = 'Caracteristica Personales'
    if id == 'E':
        dato = 'Estudios Academicos'
    if data:
        return render_template('atributo.html', cv = data, dato = dato)
    else:
        return render_template('home.html')

#abm atributos
@app.route('/veratributos/<string:id>')
def veratributos(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    print(request.form)
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "I" ', [id])
    dataI = cur.fetchall()
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "E" ', [id])
    dataE = cur.fetchall()
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo FROM atributo left join perfil_atributo on perfil_atributo.IdAtributo = atributo.IdAtributo and perfil_atributo.IdPerfil = %s WHERE atributo.tipoAtributo = "A" ', [id])
    dataA = cur.fetchall()
    cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "T" ', [id])
    dataT = cur.fetchall()
    cur.execute('SELECT descripcion FROM perfil where IdPerfil != %s',[id])
    descript = cur.fetchall()
    return render_template('veratributos.html', descript = descript, dataI = dataI, dataE = dataE, dataA = dataA, dataT = dataT)


@app.route('/add_atributo/<string:id>', methods= ['POST'])
def add_atributo(id):
    print(id)
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    if request.method == 'POST':
        atributo = request.form['idioma']
        tipoAtributo = id
        fechaCreacion = datetime.now()
        IdUsuarioCreacion = session['id']
        cur.execute('SELECT * FROM atributo WHERE atributo = %s', [atributo])
        data = cur.fetchone()
        if data:
            flash('Idioma ya existente')
            return redirect(url_for('atributo', id = id))
        cur.execute('INSERT INTO atributo (atributo, tipoAtributo, fechaCreacion, IdUsuarioCreacion) VALUES (%s, %s, %s, %s)',
        (atributo, tipoAtributo, fechaCreacion, IdUsuarioCreacion))
        mysql.connection.commit()
        flash('Operacion realizada correctamente')
        return redirect(url_for('atributo', id = id))

@app.route('/edit_atributo/<string:id>', methods= ['POST'])
def edit_atributo(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    print(id)
    print(request.form)
    if request.method == 'POST':
        atributo = request.form['atribNew']
        fechaCreacion = datetime.now()
        IdUsuarioCreacion = session['id']
        atribOld = request.form['atribOld']
        cur.execute("""
            UPDATE atributo 
            SET atributo = %s,
                fechaCreacion = %s,
                IdUsuarioCreacion = %s
            WHERE atributo = %s
        """, (atributo, fechaCreacion, IdUsuarioCreacion, atribOld))
        mysql.connection.commit()
        flash('Operacion realizada correctamente')
        return redirect(url_for('atributo', id = id))

# borrado de atributo           
@app.route('/deleteatributo/<string:id>', methods = ['POST'])
def deleteatributo(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    print(request.form)
    if session['rol'] == 1:
        cur = mysql.connection.cursor()
        idatrib = request.form['idatrib']
        cur.execute('SELECT * FROM perfil_atributo WHERE IdAtributo = %s', [idatrib])
        data = cur.fetchall()
        print(data)
        if data:
            flash('Atributo asignado a uno o mas usuarios, no se puede eliminar')
            return redirect(url_for('atributo', id = id))
        cur.execute('DELETE FROM atributo WHERE IdAtributo = %s', [idatrib])
        mysql.connection.commit()
        flash('Atributo eliminado exitosamente')
        return redirect(url_for('atributo', id = id))
    else:
        return render_template('home.html')

# pantalla perfiles cargados
@app.route('/perfil')
def perfil():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    cur.execute('SELECT * FROM perfil')
    data = cur.fetchall()
    print(data)
    if data:
        return render_template('perfil.html', perfil = data)
    else:
        flash('No se han creado perfiles')
        return render_template('perfil.html')

@app.route('/editperfil/<string:id>')
def editperfil(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    if session['rol'] == 1:
        cur.execute('SELECT IdPerfil, descripcion FROM perfil WHERE IdPerfil = %s', [id])
        data = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "I" ', [id])
        dataI = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "E" ', [id])
        dataE = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo FROM atributo left join perfil_atributo on perfil_atributo.IdAtributo = atributo.IdAtributo and perfil_atributo.IdPerfil = %s WHERE atributo.tipoAtributo = "A" ', [id])
        dataA = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "T" ', [id])
        dataT = cur.fetchall()
        cur.execute('SELECT descripcion FROM perfil where IdPerfil != %s',[id])
        descript = cur.fetchall()
        print(descript)
        cur.execute('SELECT * FROM atributo group by atributo order by atributo')
        atrib = cur.fetchall()
        cur.execute('SELECT * FROM nivel order by IdNivel')
        level = cur.fetchall()
        print(data)
        return render_template('editperfil.html', descript = descript, perfil = data, dataI = dataI ,dataE = dataE, dataT = dataT ,dataA = dataA,  level = level, atrib = atrib)
    else:
        return render_template('home.html')

@app.route('/nuevoperfil')
def nuevoperfil():
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html')
    if session['rol'] == 1:
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel, idPerfilatributo, perfil_atributo.IdPerfil FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s', [id])
        data = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "I" ', [id])
        dataI = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "E" ', [id])
        dataE = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo FROM atributo left join perfil_atributo on perfil_atributo.IdAtributo = atributo.IdAtributo WHERE (perfil_atributo.IdPerfil = %s or perfil_atributo.IdPerfil is NULL) and atributo.tipoAtributo = "A" ', [id])
        dataA = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo FROM atributo left join perfil_atributo on perfil_atributo.IdAtributo = atributo.IdAtributo WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "A" ', [id])
        dataAsi = cur.fetchall()
        cur.execute('SELECT atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo FROM atributo WHERE atributo.tipoAtributo = "A" ')
        dataTODO = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil.descripcion, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel, nivel.nivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo join nivel on perfil_atributo.IdNivel = nivel.IdNivel join perfil on perfil_atributo.IdPerfil = perfil.IdPerfil WHERE perfil_atributo.IdPerfil = %s and atributo.tipoAtributo = "T" ', [id])
        dataT = cur.fetchall()
        cur.execute('SELECT perfil_atributo.IdPerfilatributo, perfil_atributo.IdPerfil, perfil_atributo.IdAtributo, atributo.atributo, atributo.tipoAtributo, perfil_atributo.IdNivel FROM perfil_atributo join atributo on perfil_atributo.IdAtributo = atributo.IdAtributo WHERE perfil_atributo.IdPerfil = %s', [id])
        dato = cur.fetchall()
        cur.execute('SELECT * FROM atributo group by atributo order by atributo')
        atrib = cur.fetchall()
        cur.execute('SELECT * FROM nivel order by IdNivel')
        level = cur.fetchall()
        cur.execute('SELECT descripcion FROM perfil')
        descript = cur.fetchall()
        return render_template('nuevoperfil.html', perfil = data, descript = descript, dataAsi= dataAsi, dataTODO= dataTODO , dato = dato, dataI = dataI ,dataE = dataE, dataT = dataT ,dataA = dataA,  level = level, atrib = atrib)
    else:
        return render_template('home.html')

@app.route('/updatePerfil/<string:id>', methods = ['POST'])
def updatePerfil(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        olddescripcion = request.form['olddescripcion']
        if olddescripcion != descripcion:
            cur = mysql.connection.cursor()
            IdUsuarioCreacion = session['id']
            fechaCreacion = datetime.now()
            cur.execute("""
                UPDATE perfil
                SET descripcion = %s,
                    IdUsuarioCreacion = %s,
                    fechaCreacion = %s
                WHERE IdPerfil = %s
            """,  (descripcion, IdUsuarioCreacion, fechaCreacion, id))
            mysql.connection.commit()

        print(request.form)

        c = 0
        for c in range(3):
            if c == 0:
                IdAtributo = request.form['estudios'][:2]
                IdEstado = request.form['estado']
                atribOld = request.form['atribOld']
            else:
                IdAtributo = request.form['estudios' + str(c)][:2]
                IdEstado = request.form['estado'+ str(c)]
                atribOld = request.form['atribOld'+ str(c)]
            IdUsuarioCreacion = session['id']
            fechaCreacion = datetime.now()
            cur = mysql.connection.cursor() 
            if atribOld == '0':  ### sino tiene nada cargado previo
                if IdAtributo == "":   ### sino cargo atributo
                    pass   ### sin atrib anterior y  idatrib = "" no hacer nada
                else:
                    ### sin previo y con un atrib ingresado - nuevo atributo
                    cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdNivel, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s, %s)',
                (id, IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion))
                    mysql.connection.commit()
            else:   ### tiene algo cargado previamente
                if IdAtributo == "":   ### sino cargo atributo
                    ### con atrib anterior y idatributo == "" el usuario eliminimo ese atributo
                    cur.execute('DELETE FROM perfil_atributo WHERE IdPerfil = %s and IdAtributo = %s', [id,atribOld])
                    mysql.connection.commit()
                else:  ### con anterior y atributo cargado update 
                    print(id)
                    print(IdAtributo)  
                    cur.execute("""
                        UPDATE perfil_atributo
                        SET IdAtributo = %s,
                            IdNivel = %s,
                            IdUsuarioCreacion = %s,
                            fechaCreacion = %s
                        WHERE IdPerfil = %s and IdAtributo = %s
                    """,  (IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion, id, atribOld))
                    mysql.connection.commit()
            IdAtributo == ""
            c = c + 1
                    
        c = 0
        for c in range(3):
            if c == 0:
                IdAtributo = request.form['idioma'][:2]
                IdEstado = request.form['nivel']
                atribOld = request.form['atribOldI']
            else:
                IdAtributo = request.form['idioma' + str(c)][:2]
                IdEstado = request.form['nivel'+ str(c)]
                atribOld = request.form['atribOldI'+ str(c)]
            IdUsuarioCreacion = session['id']
            fechaCreacion = datetime.now()
            cur = mysql.connection.cursor() 
            if atribOld == '0':  ### sino tiene nada cargado previo
                if IdAtributo == "":   ### sino cargo atributo
                    pass   ### sin atrib anterior y  idatrib = "" no hacer nada
                else:
                    ### sin previo y con un atrib ingresado - nuevo atributo
                    cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdNivel, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s, %s)',
                (id, IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion))
                    mysql.connection.commit()
            else:   ### tiene algo cargado previamente
                if IdAtributo == "":   ### sino cargo atributo
                    ### con atrib anterior y idatributo == "" el usuario eliminimo ese atributo
                    cur.execute('DELETE FROM perfil_atributo WHERE IdPerfil = %s and IdAtributo = %s', [id,atribOld])
                    mysql.connection.commit()
                else:  ### con anterior y atributo cargado update   
                    cur.execute("""
                        UPDATE perfil_atributo
                        SET IdAtributo = %s,
                            IdNivel = %s,
                            IdUsuarioCreacion = %s,
                            fechaCreacion = %s
                        WHERE IdPerfil = %s and IdAtributo = %s
                    """,  (IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion, id, atribOld))
                    mysql.connection.commit()
            IdAtributo == ""
            c = c + 1

        c = 0
        for c in range(3):
            if c == 0:
                IdAtributo = request.form['Herramientas'][:2]
                IdEstado = request.form['niveltecnico']
                atribOld = request.form['atribOldT']
            else:
                IdAtributo = request.form['Herramientas' + str(c)][:2]
                IdEstado = request.form['niveltecnico'+ str(c)]
                atribOld = request.form['atribOldT'+ str(c)]
            IdUsuarioCreacion = session['id']
            fechaCreacion = datetime.now()
            cur = mysql.connection.cursor() 
            if atribOld == '0':  ### sino tiene nada cargado previo
                if IdAtributo == "":   ### sino cargo atributo
                    pass   ### sin atrib anterior y  idatrib = "" no hacer nada
                else:
                    ### sin previo y con un atrib ingresado - nuevo atributo
                    cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdNivel, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s, %s)',
                (id, IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion))
                    mysql.connection.commit()
            else:   ### tiene algo cargado previamente
                if IdAtributo == "":   ### sino cargo atributo
                    ### con atrib anterior y idatributo == "" el usuario eliminimo ese atributo
                    cur.execute('DELETE FROM perfil_atributo WHERE IdPerfil = %s and IdAtributo = %s', [id,atribOld])
                    mysql.connection.commit()
                else:  ### con anterior y atributo cargado update   
                    cur.execute("""
                        UPDATE perfil_atributo
                        SET IdAtributo = %s,
                            IdNivel = %s,
                            IdUsuarioCreacion = %s,
                            fechaCreacion = %s
                        WHERE IdPerfil = %s and IdAtributo = %s
                    """,  (IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion, id, atribOld))
                    mysql.connection.commit()
            IdAtributo == ""
            c = c + 1
            
        if ('formcheck' in request.form):
            dataOld = request.form.getlist('data')
            dataNew = request.form.getlist('formcheck')
            if dataOld == dataNew:
                pass
            else:
                for dOld in dataOld:
                    if dOld in dataNew:
                        pass
                    else:   ### delelete atributo esta en la vieja y no en la nueva
                        IdAtributo = dOld
                        cur = mysql.connection.cursor() 
                        cur.execute('DELETE FROM perfil_atributo WHERE IdPerfil = %s and IdAtributo = %s', [id,IdAtributo])
                        mysql.connection.commit()

                for dNew in dataNew:
                    if dNew in dataOld:
                        pass
                    else:  ### insert, nuevo atributo
                        IdAtributo = dNew
                        IdUsuarioCreacion = session['id']
                        fechaCreacion = datetime.now()
                        cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s)',
                    (id, IdAtributo, IdUsuarioCreacion, fechaCreacion))
                    mysql.connection.commit()
                    
        else:
            cur.execute('SELECT perfil_atributo.IdAtributo from perfil_atributo join atributo on perfil_atributo.IdAtributo=atributo.IdAtributo WHERE IdPerfil = %s and tipoAtributo="A" ', [id])
            datacheckA = cur.fetchall()
            if datacheckA:
                for dtc in datacheckA:
                    IdAtributo = dtc
                    cur = mysql.connection.cursor() 
                    cur.execute('DELETE FROM perfil_atributo WHERE IdPerfil = %s and IdAtributo = %s', [id,IdAtributo])
                    mysql.connection.commit()
            
    flash('Perfil actualizado correctamente')
    return redirect(url_for('perfil'))

@app.route('/saveNewPerfil', methods = ['POST'])
def saveNewPerfil():

    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    if request.method == 'POST':

        descripcion = request.form['descripcion']
        IdUsuarioCreacion = session['id']
        fechaCreacion = datetime.now()
        cur.execute('INSERT INTO perfil (descripcion, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s)',
        (descripcion, IdUsuarioCreacion, fechaCreacion))  
        mysql.connection.commit()
        cur.execute('SELECT MAX(IdPerfil) FROM PERFIL WHERE IdUsuarioCreacion = %s', [session['id']])
        IdPerfilNew = cur.fetchone()


        if ((request.form['estudios']) or (request.form['estudios1']) or (request.form['estudios2'])):
            c = 0
            for c in range(3):
                if c == 0:
                    if request.form['estudios']:
                        IdAtributo = request.form['estudios'][:2]
                        IdEstado = request.form['estado']
                else:
                    if request.form['estudios'+ str(c)]:
                        IdAtributo = request.form['estudios' + str(c)][:2]
                        IdEstado = request.form['estado'+ str(c)]
                
                if IdAtributo:
                    IdUsuarioCreacion = session['id']
                    fechaCreacion = datetime.now()
                    cur = mysql.connection.cursor() 
                    cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdNivel, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s, %s)',
                    (IdPerfilNew, IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion))
                    mysql.connection.commit()
                IdAtributo = ""
                c = c + 1

        if ((request.form['idioma']) or (request.form['idioma1']) or (request.form['idioma2'])):            
            c = 0
            for c in range(3):
                if c == 0:
                    if request.form['idioma']:
                        IdAtributo = request.form['idioma'][:2]
                        IdEstado = request.form['nivel']
                else:
                    if request.form['idioma'+ str(c)]:
                        IdAtributo = request.form['idioma' + str(c)][:2]
                        IdEstado = request.form['nivel'+ str(c)]
                if IdAtributo:                        
                    IdUsuarioCreacion = session['id']
                    fechaCreacion = datetime.now()
                    cur = mysql.connection.cursor() 
                    cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdNivel, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s, %s)',
                    (IdPerfilNew, IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion))
                    mysql.connection.commit()
                IdAtributo = ""
                c = c + 1

        if ((request.form['Herramientas']) or (request.form['Herramientas1']) or (request.form['Herramientas2'])): 
            c = 0
            for c in range(3):
                if c == 0:
                    if request.form['Herramientas']:
                        IdAtributo = request.form['Herramientas'][:2]
                        IdEstado = request.form['niveltecnico']
                else:
                    if request.form['Herramientas'+ str(c)]:
                        IdAtributo = request.form['Herramientas' + str(c)][:2]
                        IdEstado = request.form['niveltecnico'+ str(c)]
                if IdAtributo:
                    IdUsuarioCreacion = session['id']
                    fechaCreacion = datetime.now()
                    cur = mysql.connection.cursor() 
                    cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdNivel, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s, %s)',
                    (IdPerfilNew, IdAtributo, IdEstado, IdUsuarioCreacion, fechaCreacion))
                    mysql.connection.commit()
                IdAtributo = ""
                c = c + 1
        
        if ('formcheck' in request.form):
            for f in request.form.getlist('formcheck'):
                IdAtributo = f
                IdUsuarioCreacion = session['id']
                fechaCreacion = datetime.now()
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO perfil_atributo (IdPerfil, IdAtributo, IdUsuarioCreacion, fechaCreacion) VALUES (%s, %s, %s, %s)',
                (IdPerfilNew, IdAtributo, IdUsuarioCreacion, fechaCreacion))
                mysql.connection.commit()
            
    flash('Perfil creado correctamente')
    return redirect(url_for('perfil'))

# borrado de perfil           
@app.route('/deleteperfil/<string:id>', methods = ['POST', 'GET'])
def deleteperfil(id):
    cur = mysql.connection.cursor()
    if 'loggedin' in session:
        pass
    else:        
        flash('Sesion vencida o cerrada')
        return render_template('login.html') 
    print(request.form)
    if session['rol'] == 1:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM perfil join perfil_atributo on perfil.IdPerfil = perfil_atributo.IdPerfil WHERE perfil.IdPerfil = %s', [id])
        data = cur.fetchall()
        print(data)
        if data:
            flash('El perfil tiene asignado uno o mas atributo, no se puede eliminar')
            return redirect(url_for('perfil', id = id))
        cur.execute('DELETE FROM perfil WHERE IdPerfil = %s', [id])
        mysql.connection.commit()
        flash('Perfil eliminado exitosamente')
        return redirect(url_for('perfil', id = id))
    else:
        return render_template('home.html')


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
    app.run(port = 3000, debug = True)




