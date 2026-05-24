import telebot  
from telebot import types
import requests
import json
from datetime import datetime
import zoneinfo

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "8867621977:AAE_fjmpD9aTnpgjfC5RHNEDSRhUsCwG6Ww"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxvkfqb-2OoyoQgpHw2G6xNWoKDxokKXKRIPer-RCO2Or9tI3L9zj1jdnWMbeFyPZAg/exec"

# 🌐 PARCHE REMOVIDO: Como estás en local, ya no necesitas 'apihelper.proxy'
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
    bot.send_message(chat_id, "👤 Ingrese el **Nombre del Cliente**:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id

    if not usuario_autorizado(chat_id):
        return

    datos_usuario = user_data[chat_id]
    paso_actual = datos_usuario["paso"]

    # --- FLUJO DE BÚSQUEDA ---
    if paso_actual == "buscando_id":
        id_buscado = message.text.strip()
        bot.send_message(chat_id, f"🔍 Buscando el ID **{id_buscado}** en la base de datos...", parse_mode="Markdown")

        payload = {
            "accion": "buscar",
            "id": id_buscado
        }

        try:
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            res_json = response.json()

            if res_json.get("status") == "success":
                info = res_json.get("data")
                
                reporte = (
                    f"📄 **Información del Caso [{id_buscado}]**\n"
                    f"----------------------------------------\n"
                    f"📂 **Sección:** {res_json.get('pestana_encontrada')}\n"
                    f"📅 **Fecha Reg:** {info[1]}\n"
                    f"👤 **Cliente:** {info[2]}\n"
                    f"📝 **Trámite:** {info[3]}\n"
                    f"📥 **Recaudos:** {info[4]}\n"
                    f"🛠️ **Acciones:** {info[5]}\n"
                    f"⏳ **Estado:** {info[6]}\n"
                    f"👤 **Operador:** {info[7]}"
                )
                bot.send_message(chat_id, reporte, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ {res_json.get('message')}")
                
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error al conectar con la base de datos: {e}")

        del user_data[chat_id]
        enviar_menu(message)
        return

    # --- FLUJO DE REGISTRO ORIGINAL ---
    if paso_actual == 1:
        datos_usuario["cliente"] = message.text
        datos_usuario["paso"] = 2
        bot.send_message(chat_id, "📝 Ingrese el **Tipo de Trámite o Causa**:", parse_mode="Markdown")

    elif paso_actual == 2:
        datos_usuario["tipo_tramite"] = message.text
        datos_usuario["paso"] = 3
        bot.send_message(chat_id, "📂 Ingrese los **Recaudos Recibidos** (Ej: Copia de Cédula, Título, Ninguno):", parse_mode="Markdown")

    elif paso_actual == 3:
        datos_usuario["recaudos_recibidos"] = message.text
        datos_usuario["paso"] = 4
        bot.send_message(chat_id, "🛠️ Ingrese los **Trámites Realizados** hasta ahora:", parse_mode="Markdown")

    elif paso_actual == 4:
        datos_usuario["tramites_realizados"] = message.text
        datos_usuario["paso"] = 5

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add('En Proceso', 'En Revisión', 'Completado', 'Suspendido')
        bot.send_message(chat_id, "⏳ Seleccione o escriba el **Estado** del caso:", parse_mode="Markdown", reply_markup=markup)

    elif paso_actual == 5:
        datos_usuario["estado"] = message.text

        markup_remove = types.ReplyKeyboardRemove()
        bot.send_message(chat_id, "🚀 Guardando registro completo en Google Sheets...", reply_markup=markup_remove)

        payload = {
            "accion": "guardar",
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
    print("Bot corriendo de forma local con éxito...")
    bot.infinity_polling()
