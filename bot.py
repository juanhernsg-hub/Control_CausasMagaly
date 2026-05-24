import os
import telebot
from telebot import types

# Lee las variables desde Railway
TOKEN_TELEGRAM = os.environ.get("TOKEN_TELEGRAM")
WEBAPP_URL = os.environ.get("WEBAPP_URL")

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "8867621977:AAE_fjmpD9aTnpgjfC5RHNEDSRhUsCwG6Ww"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwnQZ54IA3Jkivr2bMryDVy9qSFUyjCgvqeXnu2-jmcxZOLn7FRoqfIeRfngFojQ1bo/exec"

# 🌐 PARCHE OBLIGATORIO PARA CUENTAS GRATUITAS DE PYTHONANYWHERE
from telebot import apihelper
apihelper.proxy = {'http': 'http://proxy.server:3128', 'https': 'http://proxy.server:3128'}

bot = telebot.TeleBot(TOKEN_TELEGRAM)

fech = datetime.now(zoneinfo.ZoneInfo("America/Caracas")).strftime("%d-%m-%Y %H:%M:%S")

# 🛡️ LISTA DE USUARIOS AUTORIZADOS (Pon aquí los IDs de Telegram permitidos separados por comas)
USUARIOS_PERMITIDOS = [8375789261, 5615273235]  # 👈 REEMPLAZA ESTOS NÚMEROS POR TU ID REAL Y EL DE TU EQUIPO

# Diccionario temporal para guardar el estado del flujo por usuario
user_data = {}

# 🛠️ FUNCIÓN DE SEGURIDAD: Verifica si el usuario tiene permiso
def usuario_autorizado(chat_id):
    return chat_id in USUARIOS_PERMITIDOS

@bot.message_handler(commands=['start', 'menu'])
def enviar_menu(message):
    chat_id = message.chat.id

    # Filtro de seguridad obligatorio
    if not usuario_autorizado(chat_id):
        bot.send_message(chat_id, "❌ **Acceso Denegado:** No estás autorizado para usar este sistema jurídico.", parse_mode="Markdown")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_admin = types.KeyboardButton('📁 Nuevo Trámite Administrativo')
    btn_tribunal = types.KeyboardButton('🏛️ Nueva Causa Tribunalicia')
    markup.add(btn_admin, btn_tribunal)

    bot.send_message(
        chat_id,
        "⚖️ **Escritorio Jurídico - Asistente de Control**\nSelecciona el tipo de caso que deseas registrar:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in ['📁 Nuevo Trámite Administrativo', '🏛️ Nueva Causa Tribunalicia'])
def iniciar_registro(message):
    chat_id = message.chat.id

    # Filtro de seguridad obligatorio
    if not usuario_autorizado(chat_id):
        return

    if message.text == '📁 Nuevo Trámite Administrativo':
        pestana = "administrativos"
    else:
        pestana = "tribunal_causas"

    user_data[chat_id] = {
        "pestana": pestana,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "registrado_por": message.from_user.first_name,
        "paso": 1
    }

    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "👤 Ingrese el **Nombre del Cliente**:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id

    # Filtro de seguridad obligatorio
    if not usuario_autorizado(chat_id):
        return

    datos_usuario = user_data[chat_id]
    paso_actual = datos_usuario["paso"]

    # PASO 1: Cliente
    if paso_actual == 1:
        datos_usuario["cliente"] = message.text
        datos_usuario["paso"] = 2
        bot.send_message(chat_id, "📝 Ingrese el **Tipo de Trámite o Causa**:", parse_mode="Markdown")

    # PASO 2: Tipo de Trámite
    elif paso_actual == 2:
        datos_usuario["tipo_tramite"] = message.text
        datos_usuario["paso"] = 3
        bot.send_message(chat_id, "📂 Ingrese los **Recaudos Recibidos** (Ej: Copia de Cédula, Título, Ninguno):", parse_mode="Markdown")

    # PASO 3: Recaudos
    elif paso_actual == 3:
        datos_usuario["recaudos_recibidos"] = message.text
        datos_usuario["paso"] = 4
        bot.send_message(chat_id, "🛠️ Ingrese los **Trámites Realizados** hasta ahora:", parse_mode="Markdown")

    # PASO 4: Trámites Realizados
    elif paso_actual == 4:
        datos_usuario["tramites_realizados"] = message.text
        datos_usuario["paso"] = 5

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add('En Proceso', 'En Revisión', 'Completado', 'Suspendido')
        bot.send_message(chat_id, "⏳ Seleccione o escriba el **Estado** del caso:", parse_mode="Markdown", reply_markup=markup)

    # PASO 5: Estado y Envío
    elif paso_actual == 5:
        datos_usuario["estado"] = message.text

        markup_remove = types.ReplyKeyboardRemove()
        bot.send_message(chat_id, "🚀 Guardando registro completo en Google Sheets...", reply_markup=markup_remove)

        payload = {
            "pestana": datos_usuario["pestana"],
            "datos": [
                "",
                datos_usuario["fecha"],
                datos_usuario["cliente"],
                datos_usuario["tipo_tramite"],
                datos_usuario["recaudos_recibidos"],
                datos_usuario["tramites_realizados"],
                datos_usuario["estado"],
                datos_usuario["registrado_por"]
            ]
        }

        try:
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            res_json = response.json()

            if res_json.get("status") == "success":
                bot.send_message(chat_id, "✅ **¡Caso guardado con éxito!**", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ Error: {res_json.get('message')}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Fallo de conexión: {e}")

        del user_data[chat_id]
        enviar_menu(message)

if __name__ == "__main__":
    print("Bot corriendo con filtro de seguridad activo...")
    bot.infinity_polling()
