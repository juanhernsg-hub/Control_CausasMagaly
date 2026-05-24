import telebot
from telebot import types
from telebot import apihelper  # 🌐 Obligatorio para PythonAnywhere
import requests
import json
from datetime import datetime
import zoneinfo

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "8867621977:AAEb3DJj0DjicE1_0WUK3cVFsMe3Ok-_YiA"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwnQZ54IA3Jkivr2bMryDVy9qSFUyjCgvqeXnu2-jmcxZOLn7FRoqfIeRfngFojQ1bo/exec"

# 🌐 SOLUCIÓN PROXY 503: Configuración explícita de HTTP y HTTPS para PythonAnywhere
apihelper.proxy = {
    'http': 'http://proxy.server:3128',
    'https': 'http://proxy.server:3128'
}

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# 🛡️ LISTA DE USUARIOS AUTORIZADOS
USUARIOS_PERMITIDOS = [8375789261, 5615273235]
user_data = {}

def usuario_autorizado(chat_id):
    return chat_id in USUARIOS_PERMITIDOS

def obtener_fecha_caracas():
    return datetime.now(zoneinfo.ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M:%S")

# 🧼 FUNCIÓN ANTI-CRASHEO: Evita errores de parseo si la celda tiene caracteres especiales
def limpiar_html(texto):
    return str(texto).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def enviar_menu(message):
    chat_id = message.chat.id
    if not usuario_autorizado(chat_id):
        bot.send_message(chat_id, "❌ <b>Acceso Denegado:</b> No estás autorizado para usar este sistema jurídico.", parse_mode="HTML")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_admin = types.KeyboardButton('📁 Nuevo Trámite Administrativo')
    btn_tribunal = types.KeyboardButton('🏛️ Nueva Causa Tribunalicia')
    btn_buscar = types.KeyboardButton('🔍 Buscar por ID')
    markup.add(btn_admin, btn_tribunal)
    markup.add(btn_buscar)

    bot.send_message(
        chat_id, 
        "⚖️ <b>Escritorio Jurídico - Asistente de Control</b>\nSelecciona una opción:", 
        parse_mode="HTML", 
        reply_markup=markup
    )

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
        bot.send_message(chat_id, "🔢 Ingrese el <b>ID asignado</b> del caso que desea consultar:", parse_mode="HTML", reply_markup=markup)
        return

    pestana = "administrativos" if message.text == '📁 Nuevo Trámite Administrativo' else "tribunal_causas"
    user_data[chat_id] = {
        "pestana": pestana,
        "fecha": obtener_fecha_caracas(),
        "registrado_por": message.from_user.first_name,
        "paso": 1
    }
    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "👤 Ingrese el <b>Nombre del Cliente</b>:", parse_mode="HTML", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id
    if not usuario_autorizado(chat_id): return

    datos_usuario = user_data[chat_id]
    paso_actual = datos_usuario["paso"]

    # --- FLUJO DE BÚSQUEDA ---
    if paso_actual == "buscando_id":
        id_buscado = message.text.strip()
        bot.send_message(chat_id, f"🔍 Buscando el ID <b>{id_buscado}</b> en la base de datos...", parse_mode="HTML")

        payload = {"accion": "buscar", "id": id_buscado}

        try:
            response = requests.post(
                WEBAPP_URL, 
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), 
                headers={"Content-Type": "application/json"}, 
                timeout=15
            )
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("status") == "success":
                    info = res_json.get("data")
                    pestana_encontrada = res_json.get("pestana_encontrada", "No especificada")
                    
                    if isinstance(info, list):
                        while len(info) < 8: info.append("")
                        
                        # Limpieza estricta de variables devueltas
                        id_caso  = limpiar_html(info[0] if info[0] else id_buscado)
                        fecha    = limpiar_html(info[1] if info[1] else "No registrada")
                        cliente  = limpiar_html(info[2] if info[2] else "No definido")
                        tramite  = limpiar_html(info[3] if info[3] else "No definido")
                        recaudos = limpiar_html(info[4] if info[4] else "Ninguno")
                        acciones = limpiar_html(info[5] if info[5] else "Ninguna")
                        estado   = limpiar_html(info[6] if info[6] else "Sin estado")
                        operador = limpiar_html(info[7] if info[7] else "No especificado")

                        reporte = (
                            f"📄 <b>Información del Caso [{id_caso}]</b>\n"
                            f"----------------------------------------\n"
                            f"📂 <b>Sección:</b> {str(pestana_encontrada).upper()}\n"
                            f"📅 <b>Fecha Reg:</b> {fecha}\n"
                            f"👤 <b>Cliente:</b> {cliente}\n"
                            f"📝 <b>Trámite:</b> {tramite}\n"
                            f"📥 <b>Recaudos:</b> {recaudos}\n"
                            f"🛠️ <b>Acciones:</b> {acciones}\n"
                            f"⏳ <b>Estado:</b> {estado}\n"
                            f"👤 <b>Operador:</b> {operador}"
                        )
                        bot.send_message(chat_id, reporte, parse_mode="HTML")
                    else:
                        bot.send_message(chat_id, "⚠️ Los datos devueltos no tienen un formato de lista válido.")
                else:
                    bot.send_message(chat_id, f"❌ {res_json.get('message', 'Error al procesar la búsqueda.')}")
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
        bot.send_message(chat_id, "📝 Ingrese el <b>Tipo de Trámite o Causa</b>:", parse_mode="HTML")

    elif paso_actual == 2:
        datos_usuario["tipo_tramite"] = message.text
        datos_usuario["paso"] = 3
        bot.send_message(chat_id, "📂 Ingrese los <b>Recaudos Recibidos</b>:", parse_mode="HTML")

    elif paso_actual == 3:
        datos_usuario["recaudos_recibidos"] = message.text
        datos_usuario["paso"] = 4
        bot.send_message(chat_id, "🛠️ Ingrese los <b>Trámites Realizados</b>:", parse_mode="HTML")

    elif paso_actual == 4:
        datos_usuario["tramites_realizados"] = message.text
        datos_usuario["paso"] = 5
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add('En Proceso', 'En Revisión', 'Completado', 'Suspendido')
        bot.send_message(chat_id, "⏳ Seleccione o escriba el <b>Estado</b> del caso:", parse_mode="HTML", reply_markup=markup)

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
            response = requests.post(
                WEBAPP_URL, 
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), 
                headers={"Content-Type": "application/json"}, 
                timeout=15
            )
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("status") == "success":
                    bot.send_message(chat_id, "✅ <b>¡Caso guardado con éxito!</b>", parse_mode="HTML")
                else:
                    bot.send_message(chat_id, f"❌ Error: {res_json.get('message')}")
            else:
                bot.send_message(chat_id, f"❌ Error {response.status_code} en el servidor de Google.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Fallo de conexión: {e}")

        if chat_id in user_data: del user_data[chat_id]
        enviar_menu(message)

if __name__ == "__main__":
    print("Base limpia de webhooks...")
    bot.remove_webhook()
    print("🚀 Bot iniciado correctamente en PythonAnywhere con blindaje HTML y Proxy Corregido.")
    bot.infinity_polling()
