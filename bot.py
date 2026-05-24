import os
import telebot
from telebot import types
from datetime import datetime
import json
import requests
import zoneinfo

# Configuración: Asegúrate de que TOKEN_TELEGRAM y WEBAPP_URL 
# estén configurados como variables de entorno en Railway.
TOKEN_TELEGRAM = os.environ.get("TOKEN_TELEGRAM")
WEBAPP_URL = os.environ.get("WEBAPP_URL")

bot = telebot.TeleBot(TOKEN_TELEGRAM)
user_data = {}
USUARIOS_PERMITIDOS = [8375789261, 5615273235]

def usuario_autorizado(chat_id):
    return chat_id in USUARIOS_PERMITIDOS

@bot.message_handler(commands=['start', 'menu'])
def enviar_menu(message):
    chat_id = message.chat.id
    if not usuario_autorizado(chat_id):
        bot.send_message(chat_id, "❌ Acceso denegado.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('📁 Nuevo Trámite Administrativo', '🏛️ Nueva Causa Tribunalicia')
    bot.send_message(chat_id, "⚖️ **Escritorio Jurídico**\nSelecciona el tipo de caso:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['📁 Nuevo Trámite Administrativo', '🏛️ Nueva Causa Tribunalicia'])
def iniciar_registro(message):
    chat_id = message.chat.id
    if not usuario_autorizado(chat_id): return

    pestana = "administrativos" if message.text == '📁 Nuevo Trámite Administrativo' else "tribunal_causas"

    user_data[chat_id] = {
        "pestana": pestana,
        "fecha": datetime.now(zoneinfo.ZoneInfo("America/Caracas")).strftime("%Y-%m-%d %H:%M:%S"),
        "registrado_por": message.from_user.first_name,
        "paso": 1
    }

    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "👤 Ingrese el **Nombre del Cliente**:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id
    datos = user_data[chat_id]
    
    if datos["paso"] == 1:
        datos["cliente"] = message.text
        datos["paso"] = 2
        bot.send_message(chat_id, "📝 Ingrese el **Tipo de Trámite o Causa**:")
    elif datos["paso"] == 2:
        datos["tipo_tramite"] = message.text
        datos["paso"] = 3
        bot.send_message(chat_id, "📂 Ingrese los **Recaudos Recibidos**:")
    elif datos["paso"] == 3:
        datos["recaudos"] = message.text
        datos["paso"] = 4
        bot.send_message(chat_id, "🛠️ Ingrese los **Trámites Realizados**:")
    elif datos["paso"] == 4:
        datos["tramites"] = message.text
        datos["paso"] = 5
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('En Proceso', 'En Revisión', 'Completado', 'Suspendido')
        bot.send_message(chat_id, "⏳ Seleccione el **Estado** del caso:", reply_markup=markup)
    elif datos["paso"] == 5:
        datos["estado"] = message.text
        
        # Enviar a Google Sheets
        payload = {
            "pestana": datos["pestana"],
            "datos": ["", datos["fecha"], datos["cliente"], datos["tipo_tramite"], datos["recaudos"], datos["tramites"], datos["estado"], datos["registrado_por"]]
        }
        
        try:
            requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            bot.send_message(chat_id, "✅ ¡Caso guardado con éxito!", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error al conectar con Sheets: {e}")
            
        del user_data[chat_id]
        enviar_menu(message)

if __name__ == "__main__":
    print("Bot activo y escuchando...")
    bot.infinity_polling()
