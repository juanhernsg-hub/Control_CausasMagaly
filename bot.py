import telebot
from telebot import types
import requests
import json
from datetime import datetime
import zoneinfo
import base64

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "8867621977:AAGVh7ZqNj27QZeIptBGftQv0jnFMJDbt0k"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxvkfqb-2OoyoQgpHw2G6xNWoKDxokKXKRIPer-RCO2Or9tI3L9zj1jdnWMbeFyPZAg/exec"

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# 🛡️ LISTA DE USUARIOS AUTORIZADOS
USUARIOS_PERMITIDOS = [8375789261, 5615273235]

# Diccionario temporal para guardar el estado del flujo por usuario
user_data = {}

# 🛠️ FUNCIÓN DE SEGURIDAD: Verifica si el usuario tiene permiso
def usuario_autorizado(chat_id):
    return chat_id in USUARIOS_PERMITIDOS

# ⚙️ FUNCIÓN AUXILIAR: Obtiene la fecha actual con la zona horaria de Caracas
def obtener_fecha_caracas():
    return datetime.now(zoneinfo.ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M:%S")

def enviar_menu(message):
    chat_id = message.chat.id

    # Filtro de seguridad obligatorio
    if not usuario_autorizado(chat_id):
        bot.send_message(chat_id, "❌ **Acceso Denegado:** No estás autorizado para usar este sistema jurídico.", parse_mode="Markdown")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_admin = types.KeyboardButton('📁 Nuevo Trámite Administrativo')
    btn_tribunal = types.KeyboardButton('🏛️ Nueva Causa Tribunalicia')
    btn_buscar = types.KeyboardButton('🔍 Buscar por ID')
    markup.add(btn_admin, btn_tribunal)
    markup.add(btn_buscar)

    bot.send_message(
        chat_id,
        "⚖️ **Escritorio Jurídico - Asistente de Control**\nSelecciona una opción:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Manejador para iniciar el registro, la búsqueda o el comando /start
@bot.message_handler(commands=['start'])
def comando_start(message):
    enviar_menu(message)

@bot.message_handler(func=lambda message: message.text in ['📁 Nuevo Trámite Administrativo', '🏛️ Nueva Causa Tribunalicia', '🔍 Buscar por ID'])
def manejar_opciones_menu(message):
    chat_id = message.chat.id

    if not usuario_autorizado(chat_id):
        return

    # CASO: BÚSQUEDA POR ID
    if message.text == '🔍 Buscar por ID':
        user_data[chat_id] = {
            "paso": "buscando_id"
        }
        markup = types.ReplyKeyboardRemove()
        bot.send_message(chat_id, "🔢 Ingrese el **ID asignado** del caso que desea consultar:", parse_mode="Markdown", reply_markup=markup)
        return

    # CASO: NUEVO REGISTRO
    if message.text == '📁 Nuevo Trámite Administrativo':
        pestana = "administrativos"
    else:
        pestana = "tribunal_causas"

    user_data[chat_id] = {
        "pestana": pestana,
        "fecha": obtener_fecha_caracas(),
        "registrado_por": message.from_user.first_name,
        "paso": 1
    }

    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "👤 Ingrese o dicte el **Nombre del Cliente**:", parse_mode="Markdown", reply_markup=markup)


# 🎤 MANEJADOR DE DICTADO POR VOZ (NOTAS DE VOZ Y AUDIO)
@bot.message_handler(content_types=['voice', 'audio'])
def manejar_dictado_voz(message):
    chat_id = message.chat.id

    if not usuario_autorizado(chat_id):
        return

    # Si el usuario no ha iniciado ningún flujo operativo, ignoramos el audio
    if chat_id not in user_data:
        bot.send_message(chat_id, "⚠️ Por favor, selecciona una opción del menú antes de enviar una nota de voz.")
        return

    bot.send_message(chat_id, "🎤 Procesando nota de voz, por favor espera...", parse_mode="Markdown")

    try:
        # 1. Obtener identificador único del archivo de audio enviado
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file_info = bot.get_file(file_id)
        
        # 2. Descargar los bytes crudos del archivo desde los servidores de Telegram
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 3. Convertir a Base64 plano para empaquetarlo sin conflictos dentro del JSON
        audio_base64 = base64.b64encode(downloaded_file).decode('utf-8')

        # 4. Enviar carga útil a Google Apps Script para transcribir
        payload = {
            "tipo": "transcribir",
            "audio": audio_base64
        }
        
        response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        res_json = response.json()

        if res_json.get("status") == "success":
            texto_transcrito = res_json.get("texto", "").strip()
            
            if not texto_transcrito:
                bot.send_message(chat_id, "⚠️ El audio fue procesado pero no se detectó ningún texto hablado.")
                return
            
            bot.send_message(chat_id, f"📝 **Texto interpretado:** {texto_transcrito}", parse_mode="Markdown")
            
            # Reinyectamos artificialmente el texto dictado al flujo interactivo de preguntas
            message.text = texto_transcrito
            procesar_flujo(message)
        else:
            bot.send_message(chat_id, f"❌ Error del transcriptor en la hoja: {res_json.get('message')}")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Fallo crítico al procesar tu dictado de voz: {e}")


@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id

    if not usuario_autorizado(chat_id):
        return

    datos_usuario = user_data[chat_id]
    paso_actual = datos
