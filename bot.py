import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
import requests
import threading
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "[SECRET]"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "experto-linux"
TU_CHAT_ID = "[SECRET]" 

SERVIDORES = {
    "FoxEngine": "local",
    "Plant": "foxadmin@192.168.1.12",
    "MotherBase": "foxadmin@192.168.1.10",
    "Tanker": "foxadmin@192.168.1.11"
}

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app_flask = Flask(__name__)
CORS(app_flask)

# --- VARIABLES DE ESTADO ---
comando_pendiente = ""
servidor_seleccionado = "FoxEngine"
CONTEXTO_GRAL = "Eres un administrador de sistemas jefe. Respuestas breves y técnicas."

# --- FUNCIONES DE APOYO ---

def query_ollama(prompt, system_prompt=""):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=40)
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Error de conexión con Ollama: {e}"

def clean_command(text):
    # CORRECCIÓN AQUÍ: Aseguramos que todas las comillas estén cerradas
    text = text.replace("```bash", "").replace("```sh", "").replace("```", "")
    return text.strip().split('\n')[0]

def es_usuario_autorizado(message):
    id_usuario = str(message.chat.id)
    if id_usuario != TU_CHAT_ID:
        print(f"⚠️ Acceso denegado: {id_usuario}")
        bot.reply_to(message, "❌ No autorizado.")
        return False
    return True

# --- RUTAS DE FLASK (API PARA APP Y ALERTAS) ---

@app_flask.route('/alerta', methods=['POST'])
def recibir_alerta():
    data = request.json
    alertas = data.get('alerts', [])
    for alerta in alertas:
        nombre = alerta['labels'].get('alertname', 'desconocida')
        instancia = alerta['labels'].get('instance', '?')
        prompt_auto = f"Alerta: {nombre} en {instancia}. Comando Linux para arreglarlo:"
        comando_sugerido = clean_command(query_ollama(prompt_auto, "Solo comando Linux."))
        
        mensaje = (f"🚨 **ALERTA**\nEvento: `{nombre}`\nInstancia: `{instancia}`\n\n"
                   f"🛠️ **Sugerencia:** `/haz {comando_sugerido}`")
        bot.send_message(TU_CHAT_ID, mensaje, parse_mode="Markdown")
    return "OK", 200

@app_flask.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    mensaje = data.get("mensaje", "")
    if not mensaje:
        return jsonify({"status": "error", "message": "Mensaje vacío"}), 400
    respuesta = query_ollama(mensaje, CONTEXTO_GRAL)
    return jsonify({"status": "success", "respuesta": respuesta, "servidor": servidor_seleccionado})

@app_flask.route('/api/estado', methods=['GET'])
def api_estado():
    target = SERVIDORES.get(servidor_seleccionado)
    try:
        if target == "local":
            salida = subprocess.check_output(['uptime'], text=True)
        else:
            salida = subprocess.check_output(f"ssh -o ConnectTimeout=5 {target} 'uptime'", shell=True, text=True)
        return jsonify({"status": "success", "data": salida, "servidor": servidor_seleccionado})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/api/haz', methods=['POST'])
def api_haz():
    global comando_pendiente
    data = request.json
    peticion = data.get("peticion", "")
    raw_response = query_ollama(peticion, "Responde solo con el comando Bash.")
    comando_pendiente = clean_command(raw_response)
    return jsonify({
        "status": "success", 
        "comando": comando_pendiente, 
        "servidor": servidor_seleccionado
    })

@app_flask.route('/api/ejecutar', methods=['POST'])
def api_ejecutar():
    global comando_pendiente
    target = SERVIDORES.get(servidor_seleccionado)
    try:
        comando_final = f"sudo {comando_pendiente}" if target == "local" else f"ssh -o ConnectTimeout=10 {target} 'sudo {comando_pendiente}'"
        resultado = subprocess.run(comando_final, shell=True, capture_output=True, text=True, timeout=40)
        salida, error = resultado.stdout.strip(), resultado.stderr.strip()
        comando_pendiente = "" 
        return jsonify({"status": "success", "salida": salida, "error": error})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/api/servidores', methods=['GET', 'POST'])
def api_servidores():
    global servidor_seleccionado
    if request.method == 'POST':
        data = request.json
        nuevo_servidor = data.get("servidor")
        if nuevo_servidor in SERVIDORES:
            servidor_seleccionado = nuevo_servidor
            return jsonify({"status": "success", "servidor": servidor_seleccionado})
        return jsonify({"status": "error", "message": "No encontrado"}), 404
    return jsonify({"servidores": list(SERVIDORES.keys()), "actual": servidor_seleccionado})

# --- RUTAS DE GESTIÓN DE ARCHIVOS ---

@app_flask.route('/api/files/list', methods=['POST'])
def list_files():
    data = request.json
    path = data.get("path", ".")
    try:
        abs_path = os.path.abspath(path)
        items = []
        if abs_path != "/":
            items.append({"name": "..", "type": "folder", "size": "-", "path": os.path.dirname(abs_path)})
        for entry in os.scandir(abs_path):
            items.append({
                "name": entry.name,
                "type": "folder" if entry.is_dir() else "file",
                "size": f"{os.path.getsize(entry.path) // 1024}KB" if entry.is_file() else "-",
                "path": entry.path
            })
        return jsonify({"status": "success", "files": items, "currentPath": abs_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/api/files/read', methods=['POST'])
def read_file():
    path = request.json.get("path")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"status": "success", "content": content})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/api/files/write', methods=['POST'])
def write_file():
    data = request.json
    path, content = data.get("path"), data.get("content")
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"status": "success", "message": "Archivo guardado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- MANEJADORES DE TELEGRAM ---

@bot.message_handler(commands=['start', 'server'])
def menu_servidores(message):
    if not es_usuario_autorizado(message): return
    markup = InlineKeyboardMarkup()
    for nombre in SERVIDORES.keys():
        markup.add(InlineKeyboardButton(f"🖥️ {nombre}", callback_data=f"set_srv_{nombre}"))
    bot.send_message(message.chat.id, f"📍 **Actual:** `{servidor_seleccionado}`\nSelecciona objetivo:", 
                     parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['estado'])
def ver_estado(message):
    if not es_usuario_autorizado(message): return
    target = SERVIDORES.get(servidor_seleccionado)
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        salida = subprocess.check_output(['uptime'], text=True) if target == "local" else subprocess.check_output(f"ssh -o ConnectTimeout=5 {target} 'uptime'", shell=True, text=True)
        bot.reply_to(message, f"📊 **Estado {servidor_seleccionado}:**\n`{salida}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: `{e}`")

@bot.message_handler(commands=['haz'])
def solicitar_confirmacion(message):
    if not es_usuario_autorizado(message): return
    global comando_pendiente
    peticion = message.text.replace("/haz ", "")
    if not peticion or peticion == "/haz":
        bot.reply_to(message, "⚠️ Uso: `/haz <accion>`")
        return
    raw_response = query_ollama(peticion, "Responde solo con el comando Bash.")
    comando_pendiente = clean_command(raw_response)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ EJECUTAR", callback_data="run_confirmed"),
               InlineKeyboardButton("❌ CANCELAR", callback_data="run_cancel"))
    bot.reply_to(message, f"🛡️ **CONFIRMACIÓN ({servidor_seleccionado})**\n`{comando_pendiente}`", 
                 parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global comando_pendiente, servidor_seleccionado
    if call.data.startswith("set_srv_"):
        servidor_seleccionado = call.data.replace("set_srv_", "")
        bot.edit_message_text(f"✅ Objetivo: **{servidor_seleccionado}**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    elif call.data == "run_confirmed":
        target = SERVIDORES.get(servidor_seleccionado)
        try:
            # Comando final con sudo o SSH
            if target == "local":
                comando_final = f"sudo {comando_pendiente}"
            else:
                comando_final = f"ssh -o ConnectTimeout=10 {target} 'sudo {comando_pendiente}'"
            
            resultado = subprocess.run(comando_final, shell=True, capture_output=True, text=True, timeout=40)
            res_msg = f"🖥️ **Nodo:** `{servidor_seleccionado}`\n```\n{resultado.stdout.strip()}\n```"
            if resultado.stderr: res_msg += f"\n⚠️ **Error:** `{resultado.stderr.strip()}`"
            bot.send_message(call.message.chat.id, res_msg, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Fallo: {e}")
    elif call.data == "run_cancel":
        bot.edit_message_text("🚫 Cancelado.", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: True)
def responder_chat(message):
    if not es_usuario_autorizado(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    respuesta = query_ollama(message.text, CONTEXTO_GRAL)
    bot.reply_to(message, f"🤖 **[{servidor_seleccionado}]**:\n{respuesta}", parse_mode="Markdown")

if __name__ == "__main__":
    # Flask en hilo separado
    threading.Thread(target=lambda: app_flask.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()
    print(f"🚀 FoxEngine Listo | ID: {TU_CHAT_ID}")
    bot.polling(none_stop=True)
