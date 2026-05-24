import telebot
from telebot import types
from telebot import apihelper  # 🌐 IMPORTANTE para PythonAnywhere
import requests
import json
from datetime import datetime
import zoneinfo

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "8867621977:AAEb3DJj0DjicE1_0WUK3cVFsMe3Ok-_YiA"
# ⚠️ Pega aquí la nueva URL exacta que generaste en el paso anterior de Google Sheets
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwnQZ54IA3Jkivr2bMryDVy9qSFUyjCgvqeXnu2-jmcxZOLn7FRoqfIeRfngFojQ1bo/exec"

# 🌐 CONFIGURACIÓN DEL PROXY OBLIGATORIO PARA CUENTAS GRATUITAS DE PYTHONANYWHERE
apihelper.proxy = {'https': 'http://proxy.server:3128'}

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# 🛡️ LISTA DE USUARIOS AUTORIZADOS
USUARIOS_PERMITIDOS = [8375789261, 5615273235]
user_data = {}

def usuario_autorizado(chat_id):
    return chat_id in USUARIOS_PERMITIDOS

def obtener_fecha_caracas():
    return datetime.now(zoneinfo.ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M:%S")

def enviar_menu(message):
    chat_id = message.chat.id
    if not usuario_autorizado(chat_id):
        bot.send_message(chat_id, "❌ **Acceso Denegado:** No estás autorizado.", parse_mode="Markdown")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_admin = types.KeyboardButton('📁 Nuevo Trámite Administrativo')
    btn_tribunal = types.KeyboardButton('🏛️ Nueva Causa Tribunalicia')
    btn_buscar = types.KeyboardButton('🔍 Buscar por ID')
    markup.add(btn_admin, btn_tribunal)
    markup.add(btn_buscar)

    bot.send_message(chat_id, "⚖️ **Escritorio Jurídico - Asistente de Control**\nSelecciona una opción:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['start'])
def comando_start(message):
    enviar_menu(message)

@bot.message_handler(func=lambda message: message.text in ['📁 Nuevo Trámite Administrativo', '🏛️ Nueva Causa Tribunalicia', '🔍 Buscar por ID'])
def manejar_opciones_menu(message):
    chat_id = message.chat.id
    if not usuario_autorizado(chat_id): return

    if message.text == '🔍 Buscar por ID':
        user_data[chat_id] = {"paso": "buscando_id"}
        markup = types.ReplyKeyboardRemove()
        bot.send_message(chat_id, "🔢 Ingrese el **ID asignado** del caso que desea consultar:", parse_mode="Markdown", reply_markup=markup)
        return

    pestana = "administrativos" if message.text == '📁 Nuevo Trámite Administrativo' else "tribunal_causas"
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
    if not usuario_autorizado(chat_id): return

    datos_usuario = user_data[chat_id]
    paso_actual = datos_usuario["paso"]

    # --- FLUJO DE BÚSQUEDA ---
    if paso_actual == "buscando_id":
        id_buscado = message.text.strip()
        bot.send_message(chat_id, f"🔍 Buscando el ID **{id_buscado}** en la base de datos...", parse_mode="Markdown")

        payload = {"accion": "buscar", "id": id_buscado}

        try:
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("status") == "success":
                    info = res_json.get("data")
                    pestana_encontrada = res_json.get("pestana_encontrada", "No especificada")
                    
                    if isinstance(info, list):
                        while len(info) < 8: info.append("")
                        
                        id_caso  = info[0] if info[0] else id_buscado
                        fecha    = info[1] if info[1] else "No registrada"
                        cliente  = info[2] if info[2] else "No definido"
                        tramite  = info[3] if info[3] else "No definido"
                        recaudos = info[4] if info[4] else "Ninguno"
                        acciones = info[5] if info[5] else "Ninguna"
                        estado   = info[6] if info[6] else "Sin estado"
                        operador = info[7] if info[7] else "No especificado"

                        reporte = (
                            f"📄 **Información del Caso [{id_caso}]**\n"
                            f"----------------------------------------\n"
                            f"📂 **Sección:** {str(pestana_encontrada).upper()}\n"
                            f"📅 **Fecha Reg:** {fecha}\n"
                            f"👤 **Cliente:** {cliente}\n"
                            f"📝 **Trámite:** {tramite}\n"
                            f"📥 **Recaudos:** {recaudos}\n"
                            f"🛠️ **Acciones:** {acciones}\n"
                            f"⏳ **Estado:** {estado}\n"
                            f"👤 **Operador:** {operador}"
                        )
                        bot.send_message(chat_id, reporte, parse_mode="Markdown")
                    else:
                        bot.send_message(chat_id, "⚠️ Los datos no tienen un formato válido.")
                else:
                    bot.send_message(chat_id, f"❌ {res_json.get('message', 'Error al buscar el ID.')}")
            else:
                bot.send_message(chat_id, f"❌ Error de comunicación con Google (HTTP {response.status_code}).")
                
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error de conexión: {e}")

        if chat_id in user_data: del user_data[chat_id]
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
        bot.send_message(chat_id, "📂 Ingrese los **Recaudos Recibidos**:", parse_mode="Markdown")

    elif paso_actual == 3:
        datos_usuario["recaudos_recibidos"] = message.text
        datos_usuario["paso"] = 4
        bot.send_message(chat_id, "🛠️ Ingrese los **Trámites Realizados**:", parse_mode="Markdown")

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
            "datos": ["", datos_usuario["fecha"], datos_usuario["cliente"], datos_usuario["tipo_tramite"], datos_usuario["recaudos_recibidos"], datos_usuario["tramites_realizados"], datos_usuario["estado"], datos_usuario["registrado_por"]]
        }

        try:
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("status") == "success":
                    bot.send_message(chat_id, "✅ **¡Caso guardado con éxito!**", parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, f"❌ Error: {res_json.get('message')}")
            else:
                bot.send_message(chat_id, f"❌ Error {response.status_code} en el servidor de Google.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Fallo de conexión: {e}")

        if chat_id in user_data: del user_data[chat_id]
        enviar_menu(message)

if __name__ == "__main__":
    print("🧹 Limpiando webhooks...")
    bot.remove_webhook()
    print("🚀 Bot iniciado correctamente en PythonAnywhere.")
    bot.infinity_polling()
