import os
import json
import zipfile
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template_string, send_from_directory, request, send_file, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'upload')
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'download')
LANG_FILE = os.path.join(BASE_DIR, 'LANG.json')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Carrega as configurações de idioma do JSON
def carregar_traducoes():
    default_lang = "EN-US"
    if os.path.exists(LANG_FILE):
        try:
            with open(LANG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current = data.get("current_language", default_lang)
                return data["translations"].get(current, data["translations"][default_lang])
        except Exception:
            pass
    # Fallback caso dê erro na leitura do JSON
    return {
        "title": "Local File Sharing", "main_question": "What would you like to do?",
        "box_receive_title": "Receive Files", "box_receive_desc": "Choose and download files from the PC",
        "box_upload_title": "Upload Files", "box_upload_desc": "Send multiple files to the PC",
        "no_files_selected": "No files selected!", "no_files_pc": "No files found!",
        "back": "Back", "available_files": "Available Files", "download_selected": "Download Selected",
        "upload_to_pc": "Upload to PC", "speed": "Speed", "remaining": "Remaining",
        "finishing": "Finishing...", "screen_awake": "Keeping screen awake...",
        "success_upload": "All files uploaded successfully!", "error_upload": "Error during upload.",
        "no_files_uploaded_err": "No files uploaded", "log_download_single": "Device [{ip}] downloaded: '{file}'",
        "log_download_zip": "Device [{ip}] downloaded {count} files in ZIP.",
        "log_upload_success": "Device [{ip}] uploaded {count} file(s): {files}"
    }

lang = carregar_traducoes()

def registrar_log(mensagem):
    horario = datetime.now().strftime('%H:%M:%S')
    print(f"\033[1;32m[LOG {horario}]\033[0m {mensagem}")

@app.route('/')
def index():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ lang['title'] }}</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 80px; background-color: #f4f4f9; color: #333; }
            h1 { color: #2c3e50; }
            .container { display: flex; justify-content: center; gap: 20px; margin-top: 40px; flex-wrap: wrap; }
            .box { padding: 30px; width: 200px; border: 2px solid #bdc3c7; border-radius: 10px; background: white; cursor: pointer; transition: 0.2s; }
            .box:hover { border-color: #3498db; transform: scale(1.05); }
            h2 { margin: 0 0 10px 0; font-size: 1.4em; }
            p { font-size: 0.9em; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <h1>{{ lang['main_question'] }}</h1>
        <div class="container">
            <div class="box" onclick="location.href='/receive'">
                <h2>{{ lang['box_receive_title'] }}</h2>
                <p>{{ lang['box_receive_desc'] }}</p>
            </div>
            <div class="box" onclick="location.href='/upload'">
                <h2>{{ lang['box_upload_title'] }}</h2>
                <p>{{ lang['box_upload_desc'] }}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, lang=lang)

@app.route('/receive', methods=['GET', 'POST'])
def receive():
    if request.method == 'POST':
        selected_files = request.form.getlist('files')
        ip_cliente = request.remote_addr
        
        if not selected_files:
            return render_template_string(f'<script>alert("{lang["no_files_selected"]}"); window.location.href="/receive";</script>')
        
        if len(selected_files) == 1:
            nome_arquivo = selected_files[0]
            registrar_log(lang["log_download_single"].format(ip=ip_cliente, file=nome_arquivo))
            return send_from_directory(app.config['UPLOAD_FOLDER'], nome_arquivo, as_attachment=True)
        
        registrar_log(lang["log_download_zip"].format(ip=ip_cliente, count=len(selected_files)))
        
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in selected_files:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.exists(file_path):
                    zipf.write(file_path, file)
        
        memory_file.seek(0)
        return send_file(memory_file, download_name='shared_files.zip', as_attachment=True)

    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]

    html_receber = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ lang['box_receive_title'] }}</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f9; }
            .card { background: white; padding: 30px; display: inline-block; border-radius: 10px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); text-align: left; min-width: 300px; }
            h2 { text-align: center; color: #2c3e50; }
            .file-item { margin: 12px 0; font-size: 1.1em; display: flex; align-items: center; gap: 10px; }
            input[type="checkbox"] { transform: scale(1.2); cursor: pointer; }
            button { background: #3498db; color: white; border: none; padding: 12px 20px; font-size: 1em; border-radius: 5px; cursor: pointer; width: 100%; margin-top: 20px; }
            button:hover { background: #2980b9; }
            .back { display: block; text-align: center; margin-top: 20px; color: #7f8c8d; text-decoration: none; }
            .empty { text-align: center; color: #e74c3c; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>{{ lang['available_files'] }}</h2>
            {% if files %}
            <form method="post" action="/receive">
                {% for file in files %}
                <div class="file-item">
                    <input type="checkbox" name="files" value="{{ file }}" id="file_{{ loop.index }}">
                    <label for="file_{{ loop.index }}">{{ file }}</label>
                </div>
                {% endfor %}
                <button type="submit">{{ lang['download_selected'] }}</button>
            </form>
            {% else %}
                <p class="empty">{{ lang['no_files_pc'] }}</p>
            {% endif %}
            <a class="back" href="/">&larr; {{ lang['back'] }}</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_receber, files=files, lang=lang)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files')
        ip_cliente = request.remote_addr
        
        if not uploaded_files or uploaded_files[0].filename == '':
            return lang["no_files_uploaded_err"], 400
            
        count = 0
        nomes_arquivos = []
        for file in uploaded_files:
            if file:
                file.save(os.path.join(app.config['DOWNLOAD_FOLDER'], file.filename))
                nomes_arquivos.append(file.filename)
                count += 1
        
        registrar_log(lang["log_upload_success"].format(ip=ip_cliente, count=count, files=nomes_arquivos))
        return "OK", 200

    html_upload = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ lang['box_upload_title'] }}</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 80px; background-color: #f4f4f9; }
            .card { background: white; padding: 30px; display: inline-block; border-radius: 10px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); width: 340px; }
            input[type="file"] { margin: 20px 0; display: block; width: 100%; }
            button { background: #2ec4b6; color: white; border: none; padding: 12px 20px; font-size: 1em; border-radius: 5px; cursor: pointer; width: 100%; }
            button:hover { background: #011627; }
            .back { display: block; margin-top: 20px; color: #7f8c8d; text-decoration: none; }
            
            #progress-container { display: none; margin-top: 20px; text-align: left; }
            .progress-bar-wrapper { background-color: #e0e0e0; border-radius: 10px; height: 22px; width: 100%; overflow: hidden; margin-top: 5px; position: relative;}
            #progress-bar { background-color: #2ec4b6; height: 100%; width: 0%; transition: width 0.1s linear; }
            #status-text { font-size: 0.95em; color: #333; font-weight: bold; text-align: center; margin-top: 8px; }
            .info-box { display: flex; justify-content: space-between; font-size: 0.85em; color: #666; margin-top: 5px; }
            .wakelock-status { font-size: 0.8em; color: #27ae60; margin-top: 10px; font-weight: bold; text-align: center; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>{{ lang['box_upload_title'] }}</h2>
            <form id="upload-form">
                <input type="file" id="file-input" name="files" multiple required>
                <button type="submit" id="submit-btn">{{ lang['upload_to_pc'] }}</button>
            </form>

            <div id="progress-container">
                <div class="progress-bar-wrapper">
                    <div id="progress-bar"></div>
                </div>
                <div id="status-text">0%</div>
                <div class="info-box">
                    <span id="upload-speed">{{ lang['speed'] }}: 0 MB/s</span>
                    <span id="upload-eta">{{ lang['remaining'] }}: --:--</span>
                </div>
                <div id="wakelock-msg" class="wakelock-status">🔒 {{ lang['screen_awake'] }}</div>
            </div>

            <a class="back" href="/">&larr; {{ lang['back'] }}</a>
        </div>

        <script>
            let wakeLock = null;

            async function ativarModoTelaAtiva() {
                try {
                    if ('wakeLock' in navigator) {
                        wakeLock = await navigator.wakeLock.request('screen');
                        document.getElementById('wakelock-msg').style.display = 'block';
                    }
                } catch (err) {
                    document.getElementById('wakelock-msg').style.display = 'none';
                }
            }

            function desativarModoTelaAtiva() {
                if (wakeLock !== null) {
                    wakeLock.release();
                    wakeLock = null;
                }
            }

            document.getElementById('upload-form').addEventListener('submit', function(e) {
                e.preventDefault();
                var fileInput = document.getElementById('file-input');
                if (fileInput.files.length === 0) return;

                var formData = new FormData();
                for (var i = 0; i < fileInput.files.length; i++) {
                    formData.append('files', fileInput.files[i]);
                }

                var xhr = new XMLHttpRequest();
                document.getElementById('progress-container').style.display = 'block';
                document.getElementById('submit-btn').disabled = true;
                ativarModoTelaAtiva();

                let startTime = new Date().getTime();

                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        var percent = Math.round((e.loaded / e.total) * 100);
                        document.getElementById('progress-bar').style.width = percent + '%';
                        document.getElementById('status-text').innerText = percent + '%';

                        let currentTime = new Date().getTime();
                        let duration = (currentTime - startTime) / 1000;
                        if (duration > 0) {
                            let bps = e.loaded / duration;
                            let mbps = (bps / (1024 * 1024)).toFixed(2);
                            document.getElementById('upload-speed').innerText = "{{ lang['speed'] }}: " + mbps + " MB/s";

                            let remainingBytes = e.total - e.loaded;
                            let remainingTime = remainingBytes / bps;

                            if (remainingTime > 0) {
                                let mins = Math.floor(remainingTime / 60);
                                let secs = Math.floor(remainingTime % 60);
                                let formatado = (mins > 0 ? mins + "m " : "") + secs + "s";
                                document.getElementById('upload-eta').innerText = "{{ lang['remaining'] }}: ~ " + formatado;
                            } else {
                                document.getElementById('upload-eta').innerText = "{{ lang['remaining'] }}: {{ lang['finishing'] }}";
                            }
                        }
                    }
                });

                xhr.addEventListener('load', function() {
                    desativarModoTelaAtiva();
                    if (xhr.status === 200) {
                        alert("{{ lang['success_upload'] }}");
                    } else {
                        alert("{{ lang['error_upload'] }}");
                    }
                    window.location.href = "/";
                });

                xhr.open('POST', '/upload', true);
                xhr.send(formData);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_upload, lang=lang)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
