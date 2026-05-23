var TOKEN = "8867621977:AAFIOV7R4ou1nNcThJBCGgkayshTaV5rDoo";
var MI_CHAT_ID = "8375789261";

function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  var chatId = data.message.chat.id;
  var text = data.message.text.trim();
  
  // Seguridad: Solo tú o tu equipo autorizado
  if (chatId.toString() !== MI_CHAT_ID.toString()) return;
  
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetEstados = ss.getSheetByName("estados_bot");
  
  // Buscar si este usuario ya inició un flujo de preguntas
  var rangoEstados = sheetEstados.getDataRange().getValues();
  var filaUsuario = -1;
  var estadoActual = "";
  var datosGuardados = "";
  
  for (var i = 1; i < rangoEstados.length; i++) {
    if (rangoEstados[i][0].toString() === chatId.toString()) {
      filaUsuario = i + 1;
      estadoActual = rangoEstados[i][1];
      datosGuardados = rangoEstados[i][2];
      break;
    }
  }
  
  // --- MENÚ PRINCIPAL O REINICIO ---
  if (text === "/start" || text === "/cancelar") {
    limpiarEstado(sheetEstados, filaUsuario, chatId);
    var saludo = "⚖️ *Asistente Virtual de Control de Causas*\n\n" +
                 "¿Qué tipo de caso deseas registrar hoy?\n\n" +
                 "👉 Escribe *1* para Trámite Administrativo\n" +
                 "👉 Escribe *2* para Causa Tribunalicia\n\n" +
                 "_(Puedes cancelar el proceso en cualquier momento escribiendo /cancelar)_";
    sendText(chatId, saludo);
    return;
  }
  
  // --- MÁQUINA DE ESTADOS (Conversación) ---
  if (estadoActual === "") {
    if (text === "1") {
      actualizarEstado(sheetEstados, filaUsuario, chatId, "ADMIN_CLIENTE", "administrativos");
      sendText(chatId, "👤 *Trámite Administrativo*\n\n¿Cuál es el nombre del **Cliente**?");
    } else if (text === "2") {
      actualizarEstado(sheetEstados, filaUsuario, chatId, "TRIBUNAL_EXPEDIENTE", "tribunal_causas");
      sendText(chatId, "🏛️ *Causa Tribunalicia*\n\n¿Cuál es el número de **Expediente**?");
    } else {
      sendText(chatId, "⚠️ Opción no válida. Por favor, escribe *1* o *2*, o /start para reiniciar.");
    }
  } 
  
  // --- FLUJO ADMINISTRATIVOS ---
  else if (estadoActual === "ADMIN_CLIENTE") {
    actualizarEstado(sheetEstados, filaUsuario, chatId, "ADMIN_ASUNTO", datosGuardados + "||" + text);
    sendText(chatId, "📝 ¿Cuál es el **Asunto o Trámite**? (Ej: Redacción de Contrato)");
  } 
  else if (estadoActual === "ADMIN_ASUNTO") {
    actualizarEstado(sheetEstados, filaUsuario, chatId, "ADMIN_ESTADO", datosGuardados + "||" + text);
    sendText(chatId, "⏳ ¿Cuál es el **Estado** actual? (Ej: En Revisión, Completado)");
  } 
  else if (estadoActual === "ADMIN_ESTADO") {
    var partes = datosGuardados.split("||");
    var tabla = ss.getSheetByName(partes[0]); // administrativos
    
    // Insertar en la tabla: Fecha, Cliente, Asunto, Estado
    tabla.appendRow([new Date(), partes[1], partes[2], text]);
    
    sendText(chatId, "✅ *¡Guardado con éxito!*\nEl trámite administrativo ya está reflejado en tu sistema y en la Web App.");
    limpiarEstado(sheetEstados, filaUsuario, chatId);
  }
  
  // --- FLUJO TRIBUNALES ---
  else if (estadoActual === "TRIBUNAL_EXPEDIENTE") {
    actualizarEstado(sheetEstados, filaUsuario, chatId, "TRIBUNAL_JUZGADO", datosGuardados + "||" + text);
    sendText(chatId, "🏢 ¿En qué **Tribunal o Juzgado** se encuentra la causa?");
  } 
  else if (estadoActual === "TRIBUNAL_JUZGADO") {
    actualizarEstado(sheetEstados, filaUsuario, chatId, "TRIBUNAL_ESTADO", datosGuardados + "||" + text);
    sendText(chatId, "⏳ ¿Cuál es el **Estado** actual del expediente? (Ej: Fase de Alegatos, Sentencia)");
  } 
  else if (estadoActual === "TRIBUNAL_ESTADO") {
    var partes = datosGuardados.split("||");
    var tabla = ss.getSheetByName(partes[0]); // tribunal_causas
    
    // Insertar en la tabla: Fecha, Expediente, Tribunal, Estado
    tabla.appendRow([new Date(), partes[1], partes[2], text]);
    
    sendText(chatId, "🏛️ *¡Causa Tribunalicia registrada!*\nEl expediente se ha actualizado correctamente.");
    limpiarEstado(sheetEstados, filaUsuario, chatId);
  }
}

// --- FUNCIONES DE APOYO PARA LA MEMORIA DEL BOT ---
function actualizarEstado(sheet, fila, chatId, nuevoEstado, datos) {
  if (fila === -1) {
    sheet.appendRow([chatId, nuevoEstado, datos]);
  } else {
    sheet.getRange(fila, 2).setValue(nuevoEstado);
    sheet.getRange(fila, 3).setValue(datos);
  }
}

function limpiarEstado(sheet, fila, chatId) {
  if (fila !== -1) {
    sheet.deleteRow(fila);
  }
}

function sendText(chatId, text) {
  var url = "https://api.telegram.org/bot" + TOKEN + "/sendMessage";
  var payload = {
    "method": "post",
    "payload": {
      "chat_id": chatId,
      "text": text,
      "parse_mode": "Markdown"
    }
  };
  UrlFetchApp.fetch(url, payload);
}
