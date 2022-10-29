''' 
Backend API = (definiciones/ métodos/ + documentación y utilidades)
Conectada con Mysql -Bd alojada en Clever Cloud- 
(Para proyecto de encuestas por audio)
Practicas Mr.Houston (Alejandro y Eduardo) (Bejob) 
Escuela de talento del ayuntamiento de Madrid

'''

# importaciones necesarias


from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, ForeignKey
from sqlalchemy import and_, or_, not_
from sqlalchemy_utils import create_database, database_exists
from flask_marshmallow import Marshmallow
import uuid
import json
import os,sys
from werkzeug.utils import secure_filename
from datetime import datetime
import sys



# Configuraciones
app = Flask(__name__, template_folder='src/templates',static_folder='src/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ueqsev5lxkjm8eev:x0EX4LD3oBHjfc6HJK7e@bzkfz4tsdvubijkvi1hd-mysql.services.clever-cloud.com:3306/bzkfz4tsdvubijkvi1hd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']="static/uploads"
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS= set(["xlsx","csv"])
app.config['AUDIO_FOLDER'] = "static/audios"

db = SQLAlchemy(app)
ma = Marshmallow(app)
@app.errorhandler(500)
def handle_500_error(_error):
  return app.render('mensaje.html',"error localizado")


# VARIABLES GLOBALES (SOLO PARA UTILIDADES)
# GLOBAL PARA INPUT BUSCADOR (EN LISTADOS)
busqueda = None
# GLOBAL PARA TIPO PERMISO ACTIVO ("admin" y "Asociado / Cliente")
permisoGlobal = None
# variable GLOBAL ID ENCUESTADOR ACTIVO
idEncuestadorGlobal = None
# variable GLOBAL NOMBRE ENCUESTADOR ACTIVO
nombredeencuestadorGlobal = None
# variable GLOBAL NOMBRE ENCUESTA ACTIVA
nombredeencuestaGlobal = None
# variable GLOBAL ID ENCUESTA ACTIVA
idencuestaGlobal=None

# MODELADO ----------------------------------------------------------------------

# definición y/o creación de tabla tecnologias de spech to text


class Speech_technology(db.Model):
    tech_id = db.Column(db.Integer, primary_key=True)
    tech_active = db.Column(db.Boolean)
    tech_name = db.Column(db.String(100), unique=True, nullable=False)
    tech_apiKey = db.Column(db.String(100), unique=True, nullable=False)
    tech_zona = db.Column(db.String(100))

    def __init__(self, tech_active, tech_name, tech_apiKey, tech_zona=""):
        self.tech_active = tech_active
        self.tech_name = tech_name
        self.tech_apiKey = tech_apiKey
        self.tech_zona = tech_zona
        
# esquema para los datos de tabla tecnologias
class TechSchema(ma.Schema):
    class Meta:
        fields = ('tech_id','tech_active', 'tech_name', 'tech_apiKey', 'tech_zona')

# instancias de esquema tabla tecnologías
tech_schema = TechSchema()
multiples_tech_schema = TechSchema(many=True)


# definicion y/o creación de tabla encuestador
class Encuestador(db.Model):
    encuestador_id = db.Column(db.Integer, primary_key=True)
    encuestador_nombre = db.Column(db.String(100), unique=True, nullable=False)
    encuestador_apikey = db.Column(db.String(100), unique=True, nullable=False)
    encuestador_logo = db.Column(db.String(250))

    def __init__(self, encuestador_nombre, encuestador_apikey, encuestador_logo=""):
        self.encuestador_nombre = encuestador_nombre
        self.encuestador_apikey = encuestador_apikey
        self.encuestador_logo = encuestador_logo

# esquema para los datos de tabla Encuestador
class EncuestadorSchema(ma.Schema):
    class Meta:
        fields = ('encuestador_nombre', 'encuestador_apikey',
                  'encuestador_logo')

# instancias de esquema tabla encuestador
encuestador_schema = EncuestadorSchema()
multiples_encuestadores_schema = EncuestadorSchema(many=True)

# definicion y/o creación de tabla encuestado
class Encuestado(db.Model):
    encuestado_id = db.Column(db.Integer, primary_key=True)
    encuestado_mail = db.Column(db.String(70), unique=True, nullable=False)
    encuestado_wp = db.Column(db.String(20))
    encuestado_departamento = db.Column(db.String(100))
    

    def __init__(self, encuestado_mail, encuestado_wp, encuestado_departamento):
        self.encuestado_mail = encuestado_mail
        self.encuestado_wp = encuestado_wp
        self.encuestado_departamento = encuestado_departamento

# esquema para los datos de tabla Encuestado (destinatario)
class EncuestadoSchema(ma.Schema):
    class Meta:
        fields = ('encuestado_mail',
                  'encuestado_wp','encuestado_departamento')

# instancias de esquema tabla encuestado (destinatario)
encuestado_schema = EncuestadoSchema()
multiples_encuestados_schema = EncuestadoSchema(many=True)

# definicion y/o creación de tabla invitación
class Invitacion(db.Model):
    invitacion_id = db.Column(db.Integer, primary_key=True)
    encuestado_id = db.Column(db.Integer, ForeignKey('encuestado.encuestado_id'), nullable=False)
    encuesta_id = db.Column(db.Integer, ForeignKey('encuesta.encuesta_id'), nullable=False)
    identificador = db.Column(db.String(200))
    fecha_invitacion = db.Column(db.Date)

    def __init__(self, encuestado_id, encuesta_id, identificador, fecha_invitacion):
        self.encuestado_id = encuestado_id
        self.encuesta_id = encuesta_id
        self.identificador = identificador
        self.fecha_invitacion = fecha_invitacion

# esquema para los datos de tabla invitacion
class InvitacionSchema(ma.Schema):
    class Meta:
        fields = ('encuestado_id', 'encuesta_id','identificador','fecha_invitacion')

# instancias de esquema tabla invitación
invitacion_schema = InvitacionSchema()
multiples_invitaciones_schema = InvitacionSchema(many=True)

# definicion y/o creación de tabla Respuesta
class Respuesta(db.Model):
    respuesta_id = db.Column(db.Integer, primary_key=True)
    encuestado_id = db.Column(db.Integer, ForeignKey(
        'encuestado.encuestado_id'), nullable=False)
    encuesta_id = db.Column(db.Integer, ForeignKey(
        'encuesta.encuesta_id'), nullable=False)
    fecha_respuesta = db.Column(db.Date)
    archivoDeAudio = db.Column(db.String(60))
    transcripcion = db.Column(db.String(1024))

    def __init__(self, encuestado_id, encuesta_id, fecha_respuesta, archivoDeAudio,transcripcion):
        self.encuestado_id = encuestado_id
        self.encuesta_id = encuesta_id
        self.fecha_respuesta = fecha_respuesta
        self.archivoDeAudio=archivoDeAudio
        self.transcripcion=transcripcion

# esquema para los datos de tabla Respuesta
class RespuestaSchema(ma.Schema):
    class Meta:
        fields = ('encuestado_id', 'encuesta_id','fecha_respuesta','archivoDeAudio','transcripcion')

# instancias de esquema tabla Respuesta
respuesta_schema = RespuestaSchema()
multiples_invitaciones_schema = RespuestaSchema(many=True)

# definición y/o creación de tabla Encuesta
class Encuesta(db.Model):
    encuesta_id = db.Column(db.Integer, primary_key=True)
    encuestador_id = db.Column(db.Integer, ForeignKey(
        'encuestador.encuestador_id'), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    encuesta_nombre = db.Column(db.String(100), unique=True, nullable=False)
    encuesta_pregunta = db.Column(db.String(200), nullable=False)
    encuesta_observaciones = db.Column(db.String(350))

    def __init__(self, encuestador_id, fecha_inicio, fecha_fin, encuesta_nombre, encuesta_pregunta, encuesta_observaciones):
        self.encuestador_id = encuestador_id
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.encuesta_nombre = encuesta_nombre
        self.encuesta_pregunta = encuesta_pregunta
        self.encuesta_observaciones = encuesta_observaciones


# esquema para los datos de tabla Encuesta
class EncuestaSchema(ma.Schema):
    class Meta:
        fields = ('encuestador_id', 'fecha_inicio', 'fecha_fin',
                  'encuesta_nombre', 'encuesta_pregunta', 'encuesta_observaciones')


# instancias de esquema tabla encuestas
encuestas_schema = EncuestaSchema()
multiples_encuestas_schema = EncuestaSchema(many=True)

# crea base de datos si no existe
urlDb='mysql+pymysql://ueqsev5lxkjm8eev:x0EX4LD3oBHjfc6HJK7e@bzkfz4tsdvubijkvi1hd-mysql.services.clever-cloud.com:3306/bzkfz4tsdvubijkvi1hd'
if not database_exists(urlDb):
    create_database(urlDb)

# ka siguiente sentencia lee todas las clases y crea las tablas
# mysql según el modelo  en el caso de que no existan.
# (si el modelo está terminado, la sentencia es innecesaria)
db.create_all()

# creación del primer Encuestador Admin al crear tablas (necesario para acceder a la app)
# el nombre=admin es necesario en todo el programa para identificar al administrador
primero = Encuestador.query.get(1)
if not primero:
  encuestador_nombre = "admin"
  encuestador_apikey = "adminapikey"
  encuestador_logo = "logo"
  nuevo_registro_encuestador = Encuestador(
      encuestador_nombre, encuestador_apikey, encuestador_logo)
  db.session.add(nuevo_registro_encuestador)
  db.session.commit() 


# FUNCIONES (PROXIMAMENTE EN UN MODULO Y LUEGO SE IMPORTA ESE MODULO AQUI)------------


# GRUPO FUNCIONES PARA USO DESDE URL O PROGRAMACION (RETURN SIN RENDERIZADO HTML)
# funcion permisos por apikey (devuelve id_encuestador)
# En mysql debe haber un encuestador (al menos) con el nombre admin
def permisos(apikey):
    global permisoGlobal
    global idEncuestadorGlobal
    global nombredeencuestadorGlobal
    Encuestadoractivo = Encuestador.query.filter_by(
        encuestador_apikey=apikey).first()
    if Encuestadoractivo:
        # recuerdo de nuevo: en la tabla encuestadores debe haber al menos 
        # uno con el nombre de admin
        if Encuestadoractivo.encuestador_nombre == "admin":
            tipo_de_permiso = "Administrador"
            permisoGlobal = "Administrador"
            idEncuestadorGlobal = Encuestadoractivo.encuestador_id
            nombredeencuestadorGlobal = Encuestadoractivo.encuestador_nombre
            return tipo_de_permiso
        else:
            tipo_de_permiso = "Asociado / Cliente"
            permisoGlobal = "Asociado / Cliente"
            idEncuestadorGlobal = Encuestadoractivo.encuestador_id
            nombredeencuestadorGlobal = Encuestadoractivo.encuestador_nombre
            return tipo_de_permiso
    tipo_de_permiso = None
    permisoGlobal = None
    idEncuestadorGlobal = None
    nombredeencuestadorGlobal = None
    return tipo_de_permiso

# LISTADO DE TECNOLOGIAS PARA USO DESDE URL O PROGRAMACION RETURN SIN RENDERIZADO HTML


@app.route('/<apikey>/tech', methods=['GET'])
def Tecnologias(apikey):
    # COMPRUEBA TIPO PERMISO API-KEY llamando a función PERMISOS
    tipo_de_permiso = permisos(apikey)
    if tipo_de_permiso == "Administrador":
        allTech = Speech_technology.query.all()
        result = multiples_tech_schema.dump(allTech)
        return jsonify(result)
    else:
        return "no es admin"



@app.route('/techActive/<apifront>', methods=['GET'])
def TecnologiaActiva(apifront):
    # poner archivo api.key en gitignore si se sube como (publico) a Github
    file="/api.key"
    path = os.getcwd()+file
    with open(path, 'r') as key:
      apiKey = key.read().replace('\n', '')
    if apifront==apiKey:
         TechActive = Speech_technology.query.filter_by(tech_active=True).first()
         result = tech_schema.dump(TechActive)
         return jsonify(result)
    return "error apikey"  
  

@app.route('/respuesta',  methods=['POST'])
def respuesta():
  encuestado_id = request.json['encuestado']
  encuesta_id = request.json['encuesta']
  fecha_respuesta = request.json['fecha']
  archivoDeAudio = request.json['audio']
  transcripcion = request.json['texto']
  nuevo_registro_respuesta = Respuesta(encuestado_id, encuesta_id, fecha_respuesta, archivoDeAudio, transcripcion)
  try:
        db.session.add(nuevo_registro_respuesta)
        db.session.commit()
        return "ok"

  except:
        return "error"
   
  


@app.route('/comprobarinvitacion/<apifront>/<id>', methods=['GET'])
def ComprobarInvitacion(apifront,id):
    # poner archivo api.key en gitignore si se sube como (publico) a Github
    file = "/api.key"
    path = os.getcwd()+file
    with open(path, 'r') as key:
      apiKey = key.read().replace('\n', '')
    if apifront == apiKey:
        invitacioncomprobada = Invitacion.query.filter_by(identificador=id).first()
        result = invitacion_schema.dump(invitacioncomprobada)
        return jsonify(result)
    return "error apikey"

# comprueba que si ya existe una grabación para una invitación determinada
# esta función se crea para ser llamada desde el front-end
@app.route('/comprobarrespuesta/<apifront>/<audio>', methods=['GET'])
def ComprobarRespuesta(apifront,audio):
    # poner archivo api.key en gitignore si se sube como (publico) a Github
    file = "/api.key"
    path = os.getcwd()+file
    with open(path, 'r') as key:
      apiKey = key.read().replace('\n', '')
    if apifront == apiKey:
        respuestacomprobada = Respuesta.query.filter_by(archivoDeAudio=audio).first()
        result = respuesta_schema.dump(respuestacomprobada)
        return jsonify(result)
    return "error apikey"  
  
@app.route('/datosDeEncuesta/<apifront>/<idencuesta>', methods=['GET'])
def datosDeEncuesta(apifront,idencuesta):
    # poner archivo api.key en gitignore si se sube como (publico) a Github
    file = "/api.key"
    path = os.getcwd()+file
    with open(path, 'r') as key:
      apiKey = key.read().replace('\n', '')
    if apifront == apiKey:
        Encuestaselecionada = Encuesta.query.filter_by(encuesta_id=idencuesta).first()
        result = encuestas_schema.dump(Encuestaselecionada)
        return jsonify(result)
    return "error apikey"


@app.route('/datosDeEncuestador/<apifront>/<idencuestador>', methods=['GET'])
def datosDeEncuestador(apifront, idencuestador):
    # poner archivo api.key en gitignore si se sube como (publico) a Github
    file = "/api.key"
    path = os.getcwd()+file
    with open(path, 'r') as key:
      apiKey = key.read().replace('\n', '')
    if apifront == apiKey:
        Encuestadorselecionado = Encuestador.query.filter_by(
            encuestador_id=idencuestador).first()
        result = encuestador_schema.dump(Encuestadorselecionado)
        return jsonify(result)
    return "error apikey"
  

@app.route('/datosDeEncuestado/<apifront>/<idencuestado>', methods=['GET'])
def datosDeEncuestado(apifront, idencuestado):
    # poner archivo api.key en gitignore si se sube como (publico) a Github
    file = "/api.key"
    path = os.getcwd()+file
    with open(path, 'r') as key:
      apiKey = key.read().replace('\n', '')
    if apifront == apiKey:
        Encuestadoselecionado = Encuestado.query.filter_by(
            encuestado_id=idencuestado).first()
        result = encuestado_schema.dump(Encuestadoselecionado)
        return jsonify(result)
    return "error apikey"

# LISTADO json DE ENCUESTADORES PARA USO DESDE URL O PROGRAMACION RETURN SIN RENDERIZADO HTML


@app.route('/<apikey>/encuestadores', methods=['GET'])
def encuestadores(apikey):
    # COMPRUEBA TIPO PERMISO API-KEY llamando a función PERMISOS
    tipo_de_permiso = permisos(apikey)
    if tipo_de_permiso == "Administrador":
        encuestadores = Encuestador.query.all()
        result = multiples_encuestadores_schema.dump(encuestadores)
        return jsonify(result)
    elif tipo_de_permiso == "Asociado / Cliente":
        encuestador = Encuestador.query.filter_by(
            encuestador_apikey=apikey).first()
        result = encuestador_schema.dump(encuestador)
        return jsonify(result)
    return "no es admin"


# LISTADO json DE ENCUESTAS PARA USO DESDE URL O PROGRAMACION RETURN SIN RENDERIZADO HTML
@app.route('/<apikey>/encuestas', methods=['GET'])
def mostrarEncuestas(apikey):
    # COMPRUEBA IDENTIFICADOR DE TIPO PERMISO API-KEY llamando a función PERMISOS
    tipo_de_permiso = permisos(apikey)
    if tipo_de_permiso == "Administrador":
        allEncuestas = Encuesta.query.all()
        result = multiples_encuestas_schema.dump(allEncuestas)
        return jsonify(result)
    elif tipo_de_permiso == "Asociado / Cliente":
        allEncuestas = Encuesta.query.filter_by(
            encuestador_id=idEncuestadorGlobal)
        result = multiples_encuestas_schema.dump(allEncuestas)
        return jsonify(result)
    return "no es admin. ni se identifica apikey cliente"

# FUNCIONES DECORADAS PARA MOSTRAR UTILIDADES A CLIENTES O ADMIN -------------------------
# SE PASARAN A UN MODULO O SE CREARA UN FRONT-END ESPECIFICO CON ELLAS

# función decorada con renderizado html en (root)
# usada para mostrar documentación y/o utilidades API
# el renderizado condicional puede mostrar un formulario
# login que dolicita el API-KEY si entras por primera vez


@app.route('/', methods=['GET'])
def getapi():
    global nombredeencuestadorGlobal

    if permisoGlobal=="Administrador":
        return render_template('index.html', mensaje=nombredeencuestadorGlobal)
    elif permisoGlobal == "Asociado / Cliente":
        return render_template('clientes.html', mensaje=nombredeencuestadorGlobal)
    else:
        return render_template('loginApi.html')


# función decorada con renderizado html
# para mostrar formulario (login/cambio usuario)
@app.route('/login', methods=['GET'])
def loginapi():
    global permisoGlobal
    permisoGlobal = None
    return render_template('loginApi.html')


# FUNCION QUE RENDERIZA PANEL DE OPCIONES (INDEX.HTML)
# PRIMERO RECIBE Y COMPRUEBA EL APIKEY DESDE FORMULARIO LOGIN (SUBMIT METHOD-POST)
@app.route('/documentacion', methods=['POST'])
def documentacion():
    Encuestadoractivo = Encuestador.query.filter_by(
        encuestador_apikey=request.form['apiKey']).first()

    if Encuestadoractivo:
        global permisoGlobal
        global idEncuestadorGlobal
        global nombredeencuestadorGlobal
        nombredeencuestadorGlobal = Encuestadoractivo.encuestador_nombre
        idEncuestadorGlobal = Encuestadoractivo.encuestador_id
        if Encuestadoractivo.encuestador_nombre == "admin":
            permisoGlobal = "Administrador"
            mensaje = " Id_autorizado= " + nombredeencuestadorGlobal + " " + \
                str(idEncuestadorGlobal) + " con permisos de " + permisoGlobal
            return render_template('index.html', mensaje=mensaje)

        else:
            permisoGlobal = "Asociado / Cliente"
            mensaje = nombredeencuestadorGlobal
            return render_template('clientes.html', mensaje=mensaje)

    return render_template('loginApi.html', error="ERROR: key ")


@app.route('/crear_encuestador', methods=['POST'])
def crear_encuestador():
    encuestador_nombre = (request.form['encuestador_nombre'])
    encuestador_apikey = (request.form['encuestador_apikey'])
    encuestador_logo = (request.form['encuestador_logo'])
    nuevo_registro_encuestador = Encuestador(
        encuestador_nombre, encuestador_apikey, encuestador_logo)
    try:
        db.session.add(nuevo_registro_encuestador)
        db.session.commit()
        return redirect('listado-encuestadores')

    except:
        return render_template('form-encuestador.html', error="ERROR: CAMPO REQUERIDO VACIO O DUPLICADO")


@app.route('/crear_encuesta', methods=['POST'])
def crear_encuesta():
    encuestador_id = idEncuestadorGlobal
    encuesta_nombre = request.form.get('encuesta_nombre')
    encuesta_pregunta = request.form.get('encuesta_pregunta')
    encuesta_observaciones = request.form.get('encuesta_observaciones')
    fecha_inicio = (request.form['fecha_inicio'])
    if fecha_inicio=="":
      datehoy = datetime.now()
      fecha_inicio = datehoy.strftime("%Y/%m/%d")
    fecha_fin = (request.form['fecha_fin'])
    if fecha_fin=="":
        datehoy = datetime.now()
        fecha_fin = datehoy.strftime("%Y/%m/%d")
    nuevo_registro_encuesta = Encuesta(
        encuestador_id, fecha_inicio, fecha_fin, encuesta_nombre, encuesta_pregunta, encuesta_observaciones)
    try:
        db.session.add(nuevo_registro_encuesta)
        db.session.commit()
        return render_template('index.html')

    except Exception as e:
                return render_template('form-nueva-encuesta.html', error=e)


@app.route('/crear_encuestado', methods=['POST'])
def crear_encuestado():
    global idencuestaGlobal
    encuestado_mail = (request.form['encuestado_mail'])
    encuestado_wp = (request.form['encuestado_wp'])
    encuestado_departamento = (request.form['encuestado_departamento'])
    encuesta_id = idencuestaGlobal
    identificador = (request.form['identificador'])
    datehoy = datetime.now()
    dateStr = datehoy.strftime("%Y/%m/%d")
    fecha_invitacion = dateStr
    
    nuevo_registro_encuestado = Encuestado(
        encuestado_mail, encuestado_wp, encuestado_departamento)
    try:
        encuestadoExistente = Encuestado.query.filter_by(
            encuestado_mail=request.form['encuestado_mail']).first()
        if not encuestadoExistente:
          db.session.add(nuevo_registro_encuestado)
          db.session.commit()
          encuestadoExistente = Encuestado.query.filter_by(
              encuestado_mail=request.form['encuestado_mail']).first()
          
        encuestado_id = encuestadoExistente.encuestado_id
        invitacionExistente = Invitacion.query.filter(and_(Invitacion.encuestado_id == encuestado_id,Invitacion.encuesta_id==idencuestaGlobal)).first()
        if not invitacionExistente:
          nuevo_registro_invitacion = Invitacion(
              encuestado_id, encuesta_id, identificador,fecha_invitacion)
          db.session.add(nuevo_registro_invitacion)
          db.session.commit()
          return utilidadesEncuesta(idencuestaGlobal)
        else:
          return render_template('form-nuevo-encuestado.html', error="YA existe esa invitación", idencuesta=idencuestaGlobal, identificador=identificador)

    except Exception as e:
        identificador = str(uuid.uuid4().hex)
        return render_template('form-nuevo-encuestado.html', error="ERROR: CAMPO REQUERIDO VACIO O DUPLICADO "+str(e), idencuesta=idencuestaGlobal, identificador=identificador)


@app.route('/update_encuestador', methods=['POST'])
def update_encuestador():
    duplicado = False
    nameExistente = Encuestador.query.filter(
        Encuestador.encuestador_nombre == request.form['encuestador_nombre']).first()
    if nameExistente and nameExistente.encuestador_id != int(request.form['encuestador_id']):
        duplicado = True
    apikeyExistente = Encuestador.query.filter(
       Encuestador.encuestador_apikey == request.form['encuestador_apikey']).first()
    if apikeyExistente and apikeyExistente.encuestador_id != int(request.form['encuestador_id']):
        duplicado = True
    if not duplicado:    
      id = int((request.form['encuestador_id']))
      seleccion = Encuestador.query.get(id)
      seleccion.encuestador_nombre = (request.form['encuestador_nombre'])
      seleccion.encuestador_apikey = (request.form['encuestador_apikey'])
      seleccion.encuestador_logo = (request.form['encuestador_logo'])
      try:
          db.session.commit()
          return redirect('listado-encuestadores')
      except Exception as e:
          return render_template('update-encuestador.html', dato=seleccion, error=e)
    else:
        return render_template('mensaje.html', error="duplicado no permitido")


@app.route('/update_tecnologia', methods=['POST'])
def update_tecnologia():
  duplicado=False
  nameExistente = Speech_technology.query.filter(
      Speech_technology.tech_name == request.form['tech_name']).first()
  if nameExistente and nameExistente.tech_id != int(request.form['tech_id']):
      duplicado = True
  apikeyExistente = Speech_technology.query.filter(
      Speech_technology.tech_apiKey == request.form['tech_apiKey']).first()
  if apikeyExistente and apikeyExistente.tech_id != int(request.form['tech_id']):
      duplicado = True
 
  if not duplicado:
    if request.form['tech_active'] == "1":
        TechActive = Speech_technology.query.filter_by(
            tech_active=True).first()
        if TechActive:
            TechActive.tech_active = False
            db.session.commit()
    id = int((request.form['tech_id']))
    seleccion = Speech_technology.query.get(id)
    seleccion.tech_name = (request.form['tech_name'])
    seleccion.tech_apiKey = (request.form['tech_apiKey'])
    seleccion.tech_zona = (request.form['tech_zona'])
    seleccion.tech_active = int((request.form['tech_active']))
   
    try:
          db.session.commit()
          if request.form['tech_active'] == "0":
            TechActive = Speech_technology.query.filter_by(tech_active=True).first()
            if not TechActive:
              return render_template('update-tecnologias.html',  error="Ahora no existe tecnología activa")
              
          return redirect('listado-tecnologias')
    except Exception as e:
          return render_template('update-tecnologias.html', dato=seleccion, error=e)
  else:
        return render_template('update-tecnologias.html',  error="duplicado no permitido")


@app.route('/update_encuesta', methods=['POST'])
def update_encuesta():
    global idEncuestadorGlobal
    id = int((request.form['encuesta_id']))
    seleccion = Encuesta.query.get(id)
    seleccion.encuestador_id = idEncuestadorGlobal
    seleccion.encuesta_nombre = request.form['encuesta_nombre']
    seleccion.fecha_inicio = request.form['fecha_inicio']
    seleccion.fecha_fin = request.form['fecha_fin']
    seleccion.encuesta_pregunta = request.form.get('encuesta_pregunta')
    seleccion.encuesta_observaciones = request.form.get('encuesta_observaciones')
    try:
        db.session.commit()
        return redirect('listado-encuestas')
    except Exception as e:
        return render_template('update-encuesta.html', dato=seleccion, error=e)


@app.route('/delete_encuestador', methods=['POST'])
def delete_encuestador():
    id = int((request.form['encuestador_id']))
    seleccion = Encuestador.query.get(id)

    try:
        db.session.delete(seleccion)
        db.session.commit()
        return redirect('listado-encuestadores')

    except:
        return render_template('delete-encuestador.html', dato=seleccion, error="ERROR delete")


@app.route('/delete_encuesta', methods=['POST'])
def delete_encuesta():
    id = int((request.form['encuesta_id']))
    seleccion = Encuesta.query.get(id)

    try:
        db.session.delete(seleccion)
        db.session.commit()
        return redirect('listado-encuestas')

    except:
        return render_template('delete-encuesta.html', dato=seleccion, error="ERROR delete")

@app.route('/delete_tecnologia', methods=['POST'])
def delete_tecnologia():
    id = int((request.form['tech_id']))
    seleccion = Speech_technology.query.get(id)

    try:
        db.session.delete(seleccion)
        db.session.commit()
        TechActive = Speech_technology.query.filter_by(
            tech_active=True).first()
        if not TechActive:
            return render_template('update-tecnologias.html',  error="Ahora no existe tecnología activa")
        return redirect('listado-encuestadores')

    except:
        return render_template('delete-encuestador.html', dato=seleccion, error="ERROR delete")

@app.route('/crear_tecnologia', methods=['POST'])
def crear_tecnologia():
    tech_name = (request.form['tech_name'])
    tech_apiKey = (request.form['tech_apiKey'])
    tech_zona = (request.form['tech_zona'])
    if request.form['tech_active'] == "1":
        tech_active = True
        TechActive = Speech_technology.query.filter_by(
            tech_active=True).first()
        if TechActive:
            TechActive.tech_active = False
            db.session.commit()
    else:
        tech_active = False
    nuevo_registro_tecnologias = Speech_technology(
        tech_active, tech_name, tech_apiKey, tech_zona)
    try:
        db.session.add(nuevo_registro_tecnologias)
        db.session.commit()
        return tech_schema.jsonify(nuevo_registro_tecnologias)
    except:
        return render_template('form-tecnologias.html', error="ERROR: CAMPO REQUERIDO VACIO O DUPLICADO ")

# falta validaciones sobre fechas inicio/fin en crear encuesta
# de momento solo funcionará si rellenan correctamente
@app.route('/encuestas', methods=['POST'])
def create_encuesta():
    global idEncuestadorGlobal
    encuestador_id = idEncuestadorGlobal
    encuesta_nombre = (request.form['encuesta_nombre'])
    fecha_inicio = (request.form['fecha_inicio'])
    fecha_fin = (request.form['fecha_fin'])
    encuesta_pregunta = (request.form['encuesta_pregunta'])
    encuesta_observaciones = (request.form['encuesta_observaciones'])
    nuevo_registro_encuesta = Encuesta(encuestador_id,
                                       fecha_inicio, fecha_fin, encuesta_nombre, encuesta_pregunta, encuesta_observaciones)
    db.session.add(nuevo_registro_encuesta)
    db.session.commit()
    return encuestas_schema.jsonify(nuevo_registro_encuesta)

# modificar salida json por un listado renderizado de tecnologias


@app.route('/tech', methods=['GET'])
def mostrarTecnologias():
    global permisoGlobal
    if permisoGlobal == "Administrador":
        allTech = Speech_technology.query.all()
        result = multiples_tech_schema.dump(allTech)
        return jsonify(result)
    else:
        return render_template('loginApi.html', mensaje="no es admin")


@app.route('/form-encuestador')
def formEncuestador():
    global permisoGlobal
    if permisoGlobal == "Administrador":
        return render_template('form-encuestador.html')
    else:
        return render_template('loginApi.html', mensaje="no es admin")


@app.route('/form-nueva-encuesta')
def formNuevaEncuesta():
    global idEncuestadorGlobal
    seleccion = Encuestador.query.get(idEncuestadorGlobal)
    nombreEncuestador = seleccion.encuestador_nombre
    return render_template('form-nueva-encuesta.html', encuestador="encuestador seleccionado: " + nombreEncuestador)


@app.route('/form-nuevo-escuestado')
def formNuevoEncuestado():
  global idencuestaGlobal
  identificador = str(uuid.uuid4().hex)
 
  
  return render_template('form-nuevo-encuestado.html',idencuesta=idencuestaGlobal,identificador=identificador)


@app.route('/form-tecnologias')
def formTecnologias():
    global permisoGlobal
    if permisoGlobal == "Administrador":
        return render_template('form-tecnologias.html')
    else:
        return render_template('loginApi.html', mensaje="no es admin")


@app.route('/listado-tecnologias', methods=["GET"])
def listadoTecnologias():
    global permisoGlobal
    global nombredeencuestadorGlobal

    if permisoGlobal == "Administrador":
        listatecnologias = Speech_technology.query.all()
        return render_template('listado-tecnologias.html', lista=listatecnologias)
    else:
        return render_template('loginApi.html', mensaje="no es admin")

@app.route('/listado-encuestadores', methods=["GET"])
def listadoEncuestadores():
    global permisoGlobal
    global nombredeencuestadorGlobal

    if permisoGlobal == "Administrador":
        listaencuestadores = Encuestador.query.all()
        return render_template('listado-encuestadores.html', lista=listaencuestadores)
    else:
        return render_template('loginApi.html', mensaje="no es admin")
      
@app.route('/listado-busqueda-encuestadores', methods=["POST"])
def listadoBusquedaEncuestadores():
    global permisoGlobal
    global nombredeencuestadorGlobal

    if permisoGlobal == "Administrador":
        global busqueda
        busqueda = ""
        if request.method == "POST":
            busqueda = (request.form['search'])

        listaencuestadores = Encuestador.query.filter(
            Encuestador.encuestador_nombre.contains(busqueda))
        return render_template('listado-busqueda-encuestadores.html', lista=listaencuestadores, busqueda=busqueda)
    else:
        return render_template('loginApi.html', mensaje="no es admin")
      

# SALIDA CORRESPONDIENTE A JOIN (INVITACION/ENCUESTADO)
@app.route('/listado-invitaciones/<id>', methods=["GET", "POST"])
def listadoInvitaciones(id):
    global permisoGlobal
    global idEncuestadorGlobal
    global nombredeencuestadorGlobal
    global busqueda
    busqueda = ""
    if request.method == "POST":
        busqueda = (request.form['search'])
    listadojoin = db.session.query(Invitacion.identificador, Encuestado.encuestado_mail,Encuestado.encuestado_departamento).join(
            Encuestado, Invitacion.encuesta_id == id).filter(Invitacion.encuestado_id == Encuestado.encuestado_id)
    return render_template('listado-invitaciones.html', lista=listadojoin, busqueda=busqueda, nombre=nombredeencuestadorGlobal, encuestador_id=idEncuestadorGlobal)


# LISTADO DE RESPUESTAS A INVITACIONES 


@app.route('/listado-respuestas/<id>', methods=["GET", "POST"])
def listadoRespuestas(id):
    global permisoGlobal
    global idEncuestadorGlobal
    global nombredeencuestadorGlobal
    global busqueda
    busqueda = ""
    if request.method == "POST":
        busqueda = (request.form['search'])
    if permisoGlobal == "Administrador":
        listarespuestas = Respuesta.query.filter(
            Respuesta.transcripcion.contains(busqueda))
        return render_template('listado-respuestas.html', lista=listarespuestas, busqueda=busqueda)
    else:
        listarespuestas = Respuesta.query.filter(Respuesta.encuesta_id == idencuestaGlobal).filter(
            Respuesta.transcripcion.contains(busqueda))
        return render_template('listado-respuestas.html', lista=listarespuestas, busqueda=busqueda, nombre=nombredeencuestadorGlobal, encuestador_id=idEncuestadorGlobal)
    
    
@app.route('/listado-encuestas', methods=["GET", "POST"])
def listadoEncuestas():
    global permisoGlobal
    global idEncuestadorGlobal
    global nombredeencuestadorGlobal
    global busqueda
    busqueda = ""
    if request.method == "POST":
        busqueda = (request.form['search'])

    if permisoGlobal == "Administrador":
        listaencuestas = Encuesta.query.filter(
            Encuesta.encuesta_nombre.contains(busqueda))
        return render_template('listado-encuestas.html', lista=listaencuestas, busqueda=busqueda, nombre=nombredeencuestadorGlobal, encuestador_id=idEncuestadorGlobal)
    else:
        listaencuestas = Encuesta.query.filter(Encuesta.encuestador_id == idEncuestadorGlobal).filter(
            Encuesta.encuesta_nombre.contains(busqueda))
        return render_template('listado-encuestas.html', lista=listaencuestas, busqueda=busqueda, nombre=nombredeencuestadorGlobal,encuestador_id=idEncuestadorGlobal)


@app.route('/listado-encuestas-especificas/<encuestado>', methods=["GET","POST"])
def listadoEncuestaEspecificas(encuestado):
    global permisoGlobal
    global idEncuestadorGlobal
    global nombredeencuestadorGlobal
    global busqueda
    busqueda = ""
    if request.method == "POST":
        busqueda = (request.form['search'])

    listaencuestas = Encuesta.query.filter(Encuesta.encuestador_id == encuestado).filter(
           Encuesta.encuesta_nombre.contains(busqueda))
    return render_template('listado-encuestas.html', lista=listaencuestas, busqueda=busqueda, nombre=nombredeencuestadorGlobal, encuestador_id=idEncuestadorGlobal)


@app.route('/update_encuestador/<id>')
def updateEncuestador(id):
    id = int(id)
    seleccion = Encuestador.query.get(id)
    return render_template('update-encuestador.html', dato=seleccion)
  

@app.route('/update_tecnologia/<id>')
def updateTecnologia(id):
    id = int(id)
    seleccion = Speech_technology.query.get(id)
    return render_template('update-tecnologias.html', dato=seleccion,active=int(seleccion.tech_active))


@app.route('/update_encuesta/<id>')
def updateEncuesta(id):
    global idencuestaGlobal
    id = int(id)
    idencuestaGlobal=id
    seleccion = Encuesta.query.get(id)
    return render_template('update-encuesta.html', dato=seleccion)


@app.route('/utilidades_encuesta/<id>')
def utilidadesEncuesta(id):
    global idencuestaGlobal
    id = int(id)
    idencuestaGlobal = id
    seleccion = Encuesta.query.get(id)
    return render_template('utilidades-encuesta.html', dato=seleccion)


@app.route('/delete_encuestador/<id>')
def deleteEncuestador(id):
    seleccion = Encuestador.query.get(id)
    return render_template('delete-encuestador.html', dato=seleccion)


@app.route('/delete_encuesta/<id>')
def deleteEncuesta(id):
    seleccion = Encuesta.query.get(id)
    return render_template('delete-encuesta.html', dato=seleccion)


@app.route('/delete_tecnologia/<id>')
def deleteTecnologia(id):
    seleccion = Speech_technology.query.get(id)
    return render_template('delete-tecnologia.html', dato=seleccion)

# en desarrollo


@app.route('/ordenAzEncuestador/<campo>')
def ordenAzEncuestador(campo):
    listaencuestadores = Encuestador.query.order_by(campo).filter(
        Encuestador.encuestador_nombre.contains(busqueda))

    return render_template('listado-encuestadores.html', lista=listaencuestadores, busqueda=busqueda)


@app.route('/ordenZaEncuestador/<campo>')
def ordenZaEncuestador(campo):
    listaencuestadores = Encuestador.query.order_by(desc(campo)).filter(
        Encuestador.encuestador_nombre.contains(busqueda))

    return render_template('listado-encuestadores.html', lista=listaencuestadores, busqueda=busqueda)


@app.route('/ordenAzEncuesta/<campo>')
def ordenAzEncuesta(campo):
    global idEncuestadorGlobal
    global permisoGlobal
    global nombredeencuestadorGlobal
    if permisoGlobal=="Administrador":
        listaencuesta = Encuesta.query.order_by(campo).filter( Encuesta.encuesta_nombre.contains(busqueda))
    else:
        id_encuestador = idEncuestadorGlobal
        listaencuesta = Encuesta.query.order_by(campo).filter(Encuesta.encuestador_id == id_encuestador, Encuesta.encuesta_nombre.contains(busqueda))
   
    return render_template('listado-encuestas.html', lista=listaencuesta, busqueda=busqueda, nombre=nombredeencuestadorGlobal)


@app.route('/ordenZaEncuesta/<campo>')
def ordenZaEncuesta(campo):
    global idEncuestadorGlobal
    global permisoGlobal
    global nombredeencuestadorGlobal
    if permisoGlobal == "Administrador":
        listaencuesta = Encuesta.query.order_by(desc(campo)).filter(
            Encuesta.encuesta_nombre.contains(busqueda))
    else:
        id_encuestador = idEncuestadorGlobal
        listaencuesta = Encuesta.query.order_by(desc(campo)).filter(
            Encuesta.encuestador_id == id_encuestador, Encuesta.encuesta_nombre.contains(busqueda))

    return render_template('listado-encuestas.html', lista=listaencuesta, busqueda=busqueda, nombre=nombredeencuestadorGlobal)

def allowed_file(file):
  file=file.split('.')
  if file[1] in ALLOWED_EXTENSIONS:
    return True
  return False
  

@app.route('/upload', methods=['POST'])
def upload():
  file=request.files['fileupload']
  filename=secure_filename(file.filename)
  if file and allowed_file(filename):
    file.save(os.path.join(basedir,app.config['UPLOAD_FOLDER'],filename))
    return "ok"  
  return"no se ha subido"
    
  
  


if __name__ == "__main__":
    app.run(8000)
