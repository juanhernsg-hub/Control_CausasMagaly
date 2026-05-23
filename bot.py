import telebot
from telebot import types
import requests
import json
from datetime import datetime

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "TU_TOKEN_DE_TELEGRAM_BOT_AQUI"
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
    pestana = "administrativos" if "Administrativo" in message.text else "tribunalicios"
    
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
    
    # PASO 1: Capturar Cliente y pedir tipo de trámite o delito/causa
    if datos_usuario["paso"] == 1:
        datos_usuario["cliente"] = message.text
        datos_usuario["paso"] = 2
        bot.send_message(chat_id, "📝 Ingrese el **Detalle o Tipo de Trámite/Causa**:", parse_mode="Markdown")
        
    # PASO 2: Capturar detalle y enviar directamente a Google Sheets
    elif datos_usuario["paso"] == 2:
        datos_usuario["detalle"] = message.text
        
        bot.send_message(chat_id, "⏳ Guardando registro en Google Sheets...")
        
        # Estructuramos los datos en el orden exacto de tus columnas del Sheets
        # Fila: [ID/Auto, Fecha, Cliente, Detalle/Tipo]
        # Nota: Dejamos el ID en blanco para que lo llenes en Sheets, o puedes usar el chat_id
        payload = {
            "pestana": datos_usuario["pestana"],
            "datos": [
                "", # Columna A: id (puedes dejarlo vacío o generar un correlativo)
                datos_usuario["fecha"], # Columna B: fecha_registro
                datos_usuario["cliente"], # Columna C: cliente
                datos_usuario["detalle"]   # Columna D: tipo_tramite
            ]
        }
        
        try:
            # Enviamos los datos al conector de Google
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            res_json = response.json()
            
            if res_json.get("status") == "success":
                bot.send_message(chat_id, "✅ **¡Registro guardado con éxito!**\nYa está visible en el Escritorio Jurídico web.", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ Error al guardar en Sheets: {res_json.get('message')}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Fallo de conexión con la nube: {e}")
            
        # Limpiar el estado de este usuario
        del user_data[chat_id]
        enviar_menu(message)

# Iniciar el bot en modo escucha local
if __name__ == "__main__":
    print("Bot corriendo...")
    bot.infinity_polling()
