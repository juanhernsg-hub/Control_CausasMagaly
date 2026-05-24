@bot.message_handler(func=lambda message: message.chat.id in user_data)
def procesar_flujo(message):
    chat_id = message.chat.id

    if not usuario_autorizado(chat_id):
        return

    datos_usuario = user_data[chat_id]
    paso_actual = datos_usuario["paso"]

    # --- 🔍 FLUJO DE BÚSQUEDA ---
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
                pestana_real = res_json.get("pestana_encontrada", "Desconocida")
                
                if not info or not isinstance(info, list):
                    bot.send_message(chat_id, "⚠️ El ID existe, pero la fila no contiene datos legibles.")
                    del user_data[chat_id]
                    enviar_menu(message)
                    return

                # 🛠️ PARCHE DE SEGURIDAD: Si la fila tiene menos de 8 columnas en Sheets,
                # le agregamos textos vacíos para que info[1], info[2]... info[7] SIEMPRE existan.
                while len(info) < 8:
                    info.append("")

                # Evaluamos cada celda de forma segura antes de armar el reporte
                id_caso = info[0] if info[0] else id_buscado
                fecha = info[1] if info[1] else "No registrada"
                cliente = info[2] if info[2] else "No definido"
                tramite = info[3] if info[3] else "No definido"
                recaudos = info[4] if info[4] else "Ninguno"
                acciones = info[5] if info[5] else "Ninguna"
                estado = info[6] if info[6] else "Sin estado"
                operador = info[7] if info[7] else "No especificado"

                reporte = (
                    f"📄 **Información del Caso [{id_caso}]**\n"
                    f"----------------------------------------\n"
                    f"📂 **Sección:** {str(pestana_real).upper()}\n"
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
                # Si el error viene de Google Sheets, te dirá exactamente qué pasó
                bot.send_message(chat_id, f"❌ {res_json.get('message', 'Error al buscar el ID.')}")
                
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error al procesar la respuesta de la base de datos: {e}")

        del user_data[chat_id]
        enviar_menu(message)
        return

    # --- 📁 FLUJO DE REGISTRO ORIGINAL ---
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
                "",  # Columna A (ID automático en Sheets)
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
