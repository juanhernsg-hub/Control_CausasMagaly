import telebot
from telebot import types
import requests
import json
from datetime import datetime

# 🔑 CONFIGURACIÓN PRINCIPAL
TOKEN_TELEGRAM = "8867621977:AAE_fjmpD9aTnpgjfC5RHNEDSRhUsCwG6Ww"  # 👈 Pon aquí tu nuevo token de BotFather
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
    
    if message.text == '📁 Nuevo Trámite Administrativo':
        pestana = "administrativos"
    else:
        pestana = "tribunal_causas"
    
    # Iniciamos el diccionario con el orden de las nuevas preguntas
    user_data[chat_id] = {
        "pestana": pestana,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "registrado_por": message.from_user.first_name, # Captura el nombre de quien escribe en Telegram
        "paso": 1
    }
    
    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "👤 Ingrese el **Nombre del Cliente**:", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id
    datos_usuario = user_data[chat_id]
    paso_actual = datos_usuario["paso"]
    
    # PASO 1: Capturar Cliente -> Pedir Tipo de Trámite
    if paso_actual == 1:
        datos_usuario["cliente"] = message.text
        datos_usuario["paso"] = 2
        bot.send_message(chat_id, "📝 Ingrese el **Tipo de Trámite o Causa**:", parse_mode="Markdown")
        
    # PASO 2: Capturar Tipo Trámite -> Pedir Recaudos Recibidos
    elif paso_actual == 2:
        datos_usuario["tipo_tramite"] = message.text
        datos_usuario["paso"] = 3
        bot.send_message(chat_id, "📂 Ingrese los **Recaudos Recibidos** (Ej: Copia de Cédula, Título, Ninguno):", parse_mode="Markdown")
        
    # PASO 3: Capturar Recaudos -> Pedir Trámites Realizados
    elif paso_actual == 3:
        datos_usuario["recaudos_recibidos"] = message.text
        datos_usuario["paso"] = 4
        bot.send_message(chat_id, "🛠️ Ingrese los **Trámites Realizados** hasta ahora:", parse_mode="Markdown")
        
    # PASO 4: Capturar Trámites Realizados -> Pedir Estado del Caso
    elif paso_actual == 4:
        datos_usuario["tramites_realizados"] = message.text
        datos_usuario["paso"] = 5
        
        # Ofrecer botones rápidos para el Estado
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add('En Proceso', 'En Revisión', 'Completado', 'Suspendido')
        bot.send_message(chat_id, "⏳ Seleccione o escriba el **Estado** del caso:", parse_mode="Markdown", reply_markup=markup)
        
    # PASO 5: Capturar Estado -> Enviar todo al Google Sheet
    elif paso_actual == 5:
        datos_usuario["estado"] = message.text
        
        markup_remove = types.ReplyKeyboardRemove()
        bot.send_message(chat_id, "🚀 Guardando registro completo en Google Sheets...", reply_markup=markup_remove)
        
        # Estructura exacta solicitada para tus columnas
        payload = {
            "pestana": datos_usuario["pestana"],
            "datos": [
                "",                                   # Columna A: id (vacío para manejo interno o fórmulas)
                datos_usuario["fecha"],              # Columna B: fecha_registro
                datos_usuario["cliente"],            # Columna C: cliente
                datos_usuario["tipo_tramite"],        # Columna D: tipo_tramite
                datos_usuario["recaudos_recibidos"],  # Columna E: recaudos_recibidos
                datos_usuario["tramites_realizados"], # Columna F: tramites_realizados
                datos_usuario["estado"],             # Columna G: Estado
                datos_usuario["registrado_por"]       # Columna H: registrado_por
            ]
        }
        
        try:
            response = requests.post(WEBAPP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            res_json = response.json()
            
            if res_json.get("status") == "success":
                bot.send_message(chat_id, "✅ **¡Caso guardado con éxito!**\nToda la información ya está publicada en el Escritorio Jurídico web.", parse_mode="Markdown")
            else:
                bot.send_message(chat_id, f"❌ Error al guardar en Sheets: {res_json.get('message')}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Fallo de conexión con la nube: {e}")
            
        # Limpiar la memoria del usuario y restablecer el menú principal
        del user_data[chat_id]
        enviar_menu(message)

if __name__ == "__main__":
    print("Bot corriendo con los nuevos campos...")
    bot.infinity_polling()
