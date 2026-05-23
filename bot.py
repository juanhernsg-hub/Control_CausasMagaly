import telebot
from telebot import types
import requests
import json
from datetime import datetime

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "8867621977:AAE_fjmpD9aTnpgjfC5RHNEDSRhUsCwG6Ww"
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxvkfqb-2OoyoQgpHw2G6xNWoKDxokKXKRIPer-RCO2Or9tI3L9zj1jdnWMbeFyPZAg/exec"

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
    
    # SOLUCIÓN: Identificar explícitamente el botón presionado
    if message.text == '📁 Nuevo Trámite Administrativo':
        pestana = "administrativos"
    else:
        pestana = "tribunal_causas"
    
    user_data[chat_id] = {
        "pestana": pestana,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "paso": 1
    }
    
    # Quitar teclados anteriores para escribir libre
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
        
    # PASO 2: Capturar detalle y enviar directamente a Google Sheets
    elif datos_usuario["paso"] == 2:
        datos_usuario["detalle"] = message.text
        
        bot.send_message(chat_id, "⏳ Guardando registro en Google Sheets...")
        
        payload = {
            "pestana": datos_usuario["pestana"],
            "datos": [
                "", 
                datos_usuario["fecha"], 
                datos_usuario["cliente"], 
                datos_usuario["detalle"]  
            ]
        }
        
        try:
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            res_json = response.json()
            
            if res_json.get("status") == "success":
                bot.send_message(chat_id, "✅ **¡Registro guardado con éxito!**\nYa está visible en el Escritorio Jurídico web.", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ Error al guardar en Sheets: {res_json.get('message')}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Fallo de conexión con la nube: {e}")
            
        # Limpiar el estado de este usuario y volver a mostrar el menú
        del user_data[chat_id]
        enviar_menu(message)

if __name__ == "__main__":
    print("Bot corriendo...")
    bot.infinity_polling()
