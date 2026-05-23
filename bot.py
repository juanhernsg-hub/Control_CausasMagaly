import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import sqlite3

TOKEN = "8867621977:AAFIOV7R4ou1nNcThJBCGgkayshTaV5rDoo" # <-- Tu Token de Telegram
bot = telebot.TeleBot(TOKEN)
DB_NAME = "C:/Users/Usuario/Documents/DASBOARD_MAGALY/datos.db"

datos_usuario = {}

def conectar_db():
    return sqlite3.connect(DB_NAME)

def mostrar_menu_auxiliar(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_admin = KeyboardButton("🏢 Nuevo Trámite Administrativo")
    btn_tribunal = KeyboardButton("🏛️ Nuevo Trámite Tribunalicio")
    markup.add(btn_admin, btn_tribunal)
    
    uid = message.chat.id
    bot.send_message(
        uid, 
        "⚖️ **Asistente Jurídico Virtual**\nSelecciona el módulo correspondiente para iniciar el registro dirigido, o escribe /cancelar para salir:", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['start', 'help', 'menu'])
def menu_principal(message):
    mostrar_menu_auxiliar(message)

# --- FLUJO: REGISTRO ADMINISTRATIVO ---
@bot.message_handler(func=lambda msg: msg.text == "🏢 Nuevo Trámite Administrativo")
def iniciar_admin(message):
    uid = message.chat.id
    datos_usuario[uid] = {'tipo': 'admin', 'paso': 1}
    bot.send_message(uid, "🏢 **Nuevo Trámite Administrativo**\n\n✍️ Escribe el Nombre del **Cliente**:", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

# --- FLUJO: REGISTRO TRIBUNALICIO ---
@bot.message_handler(func=lambda msg: msg.text == "🏛️ Nuevo Trámite Tribunalicio")
def iniciar_tribunal(message):
    uid = message.chat.id
    datos_usuario[uid] = {'tipo': 'tribunal', 'paso': 1}
    bot.send_message(uid, "🏛️ **Nueva Causa Tribunalicia**\n\n✍️ Escribe el **Circuito Judicial** (Ej: CIVIL, LABORAL, NNA, CONTENCIOSO):", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

# --- PROCESADOR CENTRAL DE RESPUESTAS (MÁQUINA DE ESTADOS) ---
@bot.message_handler(func=lambda msg: msg.chat.id in datos_usuario)
def procesar_pasos(message):
    uid = message.chat.id
    usuario = datos_usuario[uid]
    texto = message.text.strip()
    
    if texto.lower() == '/cancelar':
        del datos_usuario[uid]
        bot.send_message(uid, "❌ Operación cancelada por el usuario.", reply_markup=ReplyKeyboardRemove())
        mostrar_menu_auxiliar(message)
        return

    # --- LÓGICA DE CAPTURA ADMINISTRATIVA ---
    if usuario['tipo'] == 'admin':
        if usuario['paso'] == 1:
            usuario['cliente'] = texto
            usuario['paso'] = 2
            bot.send_message(uid, "✍️ Escribe el **Tipo de Trámite** (Ej: Título Supletorio, Solicitud ante Sarem, Reenganche):")
        elif usuario['paso'] == 2:
            usuario['tipo_tramite'] = texto
            usuario['paso'] = 3
            bot.send_message(uid, "✍️ Detalla los **Recaudos Recibidos** (Ej: Copias de cédula, Título anterior, Documento de propiedad):")
        elif usuario['paso'] == 3:
            usuario['recaudos'] = texto
            usuario['paso'] = 4
            bot.send_message(uid, "✍️ Detalla los **Trámites Realizados / Actuaciones** hasta la fecha:")
        elif usuario['paso'] == 4:
            usuario['tramites'] = texto
            usuario['paso'] = 5
            markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            markup.add("Activo", "Pendiente", "Terminado", "Cerrado")
            bot.send_message(uid, "📍 Selecciona el **Estado actual** del caso administrativo:", reply_markup=markup)
        elif usuario['paso'] == 5:
            usuario['estatus'] = texto
            
            # Guardado final estructurado
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO administrativos (cliente, tipo_tramite, recaudos_recibidos, tramites_realizados, estatus, registrado_por)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (usuario['cliente'], usuario['tipo_tramite'], usuario['recaudos'], usuario['tramites'], usuario['estatus'], message.from_user.first_name))
            conn.commit()
            conn.close()
            
            bot.send_message(uid, "✅ **¡Caso Administrativo registrado exitosamente e indexado al Excel!**")
            del datos_usuario[uid]
            mostrar_menu_auxiliar(message)

    # --- LÓGICA DE CAPTURA TRIBUNALICIA ---
    elif usuario['tipo'] == 'tribunal':
        if usuario['paso'] == 1:
            usuario['circuito'] = texto
            usuario['paso'] = 2
            bot.send_message(uid, "✍️ Escribe el **Número de Expediente / Causa**:")
        elif usuario['paso'] == 2:
            usuario['expediente'] = texto
            usuario['paso'] = 3
            bot.send_message(uid, "✍️ Escribe el **Tribunal** a cargo de la causa:")
        elif usuario['paso'] == 3:
            usuario['tribunal'] = texto
            usuario['paso'] = 4
            bot.send_message(uid, "✍️ Escribe las **Partes involucradas** (Ej: Demandante vs Demandado):")
        elif usuario['paso'] == 4:
            usuario['partes'] = texto
            usuario['paso'] = 5
            bot.send_message(uid, "✍️ Escribe el **Recurso / Objeto del Juicio** (Ej: Divorcio, Unión Estable, Tercería):")
        elif usuario['paso'] == 5:
            usuario['recurso'] = texto
            usuario['paso'] = 6
            bot.send_message(uid, "✍️ Detalla las últimas **Actuaciones** procesales:")
        elif usuario['paso'] == 6:
            usuario['actuaciones'] = texto
            usuario['paso'] = 7
            bot.send_message(uid, "✍️ Agrega las **Observaciones** generales de control:")
        elif usuario['paso'] == 7:
            usuario['observaciones'] = texto
            usuario['paso'] = 8
            markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            markup.add("Activo", "Sentenciado", "Pendiente", "En Espera", "Terminado")
            bot.send_message(uid, "📍 Selecciona el **Estado procesal** de la causa:", reply_markup=markup)
        elif usuario['paso'] == 8:
            usuario['estatus'] = texto
            
            # Guardado completo indexado
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tribunalicios (circuito, numero_expediente, tribunal, partes, recurso, actuaciones, observaciones, estatus, registrado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (usuario['circuito'], usuario['expediente'], usuario['tribunal'], usuario['partes'], usuario['recurso'], usuario['actuaciones'], usuario['observaciones'], usuario['estatus'], message.from_user.first_name))
            conn.commit()
            conn.close()
            
            bot.send_message(uid, "✅ **¡Expediente Judicial sincronizado con éxito e indexado al Excel!**")
            del datos_usuario[uid]
            mostrar_menu_auxiliar(message)

print("🤖 Bot UX Adaptativo corriendo de forma limpia...")
bot.infinity_polling()