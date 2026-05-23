import telebot
from telebot import types
import requests
import json
from datetime import datetime

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "TU_TOKEN_DE_TELEGRAM_BOT_AQUI"
# Pega aquí la URL que te dio Google (la misma que abriste en el navegador)
WEBAPP_URL = "TU_URL_DE_APPS_SCRIPT_DE_GOOGLE_AQUI"

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# Diccionario temporal para guardar el estado del flujo por usuario
user_data = {}

@bot.message_handler(commands=['start', 'menu'])
def enviar_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_admin = types.KeyboardButton('📁 Nuevo Trámite Administrativo')
    btn_tribunal = types.KeyboardButton('🏛️ Nueva Causa Tribunalicia')
    markup.add(btn_admin, btn_tribunal)
    
    bot.send_message(
        message.chat.id, 
        "⚖️ **Escritorio Jurídico - Asistente de Control**\nSelecciona el tipo de caso que deseas registrar:", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in ['📁 Nuevo Trámite Administrativo', '🏛️ Nueva Causa Tribunalicia'])
def iniciar_registro(message):
    chat_id = message.chat.id
    # Corregido para que use 'tribunal_causas' tal como se ve en tu Google Sheets
    pestana = "administrativos" if "Administrativo" in message.text else "tribunal_causas"
    
    user_data[chat_id] = {
        "pestana": pestana,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "paso": 1
    }
    
    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "✍️ Ingrese el **Nombre del Cliente**:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id
    datos_usuario = user_data[chat_id]
    
    # PASO 1: Capturar Cliente y pedir detalle
    if datos_usuario["paso"] == 1:
        datos_usuario["cliente"] = message.text
        datos_usuario["paso"] = 2
        bot.send_message(chat_id, "📝 Ingrese el **Detalle o Tipo de Trámite/Causa**:", parse_mode="Markdown")
        
    # PASO 2: Capturar detalle y enviar a la nube
    elif datos_usuario["paso"] == 2:
        datos_usuario["detalle"] = message.text
        
        bot.send_message(chat_id, "⏳ Guardando registro en Google Sheets...")
        
        # Estructura alineada a tus columnas: id, fecha_registro, cliente, tipo_tramite
        payload = {
            "pestana": datos_usuario["pestana"],
            "datos": [
                "",                         # Columna A: id (vacío)
                datos_usuario["fecha"],     # Columna B: fecha_registro
                datos_usuario["cliente"],   # Columna C: cliente
                datos_usuario["detalle"]    # Columna D: tipo_tramite
            ]
        }
        
        try:
            # Enviamos los datos mediante POST (el método que procesa el Apps Script)
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            res_json = response.json()
            
            if res_json.get("status") == "success":
                bot.send_message(chat_id, "✅ **¡Registro guardado con éxito!**\nYa está enviado a Google Sheets.", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ Error en el script de Google: {res_json.get('message')}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Fallo de comunicación: {e}")
            
        # Limpiar flujo
        del user_data[chat_id]
        enviar_menu(message)

if __name__ == "__main__":
    print("Bot activo y escuchando...")
    bot.infinity_polling()
