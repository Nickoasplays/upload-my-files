import os
import zipfile
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template_string, send_from_directory, request, redirect, send_file, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'upload')
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'download')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def registrar_log(mensagem):
    horario = datetime.now().strftime('%H:%M:%S')
    print(f"\033[1;32m[LOG {horario}]\033[0m {mensagem}")

# --- PÁGINA INICIAL ---
@app.route('/')
def index():
    html_template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Compartilhamento Local v5</title>
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
        <h1>O que você deseja fazer?</h1>
        <div class="container">
            <div class="box" onclick="location.href='/receber'">
                <h2>Receber Arquivos</h2>
                <p>Escolher e baixar arquivos do PC</p>
            </div>
            <div class="box" onclick="location.href='/enviar'">
                <h2>Enviar Arquivos</h2>
                <p>Mandar múltiplos arquivos pesados para o PC</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)


# --- FLUXO DE RECEBER (PC -> Celular) ---
@app.route('/receber', methods=['GET', 'POST'])
def receber():
    if request.method == 'POST':
        selected_files = request.form.getlist('files')
        ip_cliente = request.remote_addr

        if not selected_files:
            return render_template_string('<script>alert("Nenhum arquivo semifinal selecionado!"); window.location.href="/receber";</script>')

        if len(selected_files) == 1:
            nome_arquivo = selected_files[0]
            registrar_log(f"O dispositivo [{ip_cliente}] iniciou o download de: '{nome_arquivo}'")
            return send_from_directory(app.config['UPLOAD_FOLDER'], nome_arquivo, as_attachment=True)

        registrar_log(f"O dispositivo [{ip_cliente}] iniciou o download de {len(selected_files)} arquivos em ZIP.")

        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in selected_files:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.exists(file_path):
                    zipf.write(file_path, file)

        memory_file.seek(0)
        return send_file(memory_file, download_name='arquivos_compartilhados.zip', as_attachment=True)

    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]

    html_receber = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Selecionar Arquivos</title>
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
            <h2>Arquivos Disponíveis</h2>
            {% if files %}
            <form method="post" action="/receber">
                {% for file in files %}
                <div class="file-item">
                    <input type="checkbox" name="files" value="{{ file }}" id="file_{{ loop.index }}">
                    <label for="file_{{ loop.index }}">{{ file }}</label>
                </div>
                {% endfor %}
                <button type="submit">Baixar Selecionados</button>
            </form>
            {% else %}
                <p class="empty">Nenhum arquivo na pasta 'upload' do PC!</p>
            {% endif %}
            <a class="back" href="/">&larr; Voltar</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_receber, files=files)


# --- FLUXO DE ENVIAR (Com Velocidade, Tempo Restante e WakeLock) ---
@app.route('/enviar', methods=['GET', 'POST'])
def enviar():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files')
        ip_cliente = request.remote_addr

        if not uploaded_files or uploaded_files[0].filename == '':
            return "Nenhum arquivo enviado", 400

        count = 0
        nomes_arquivos = []
        for file in uploaded_files:
            if file:
                file.save(os.path.join(app.config['DOWNLOAD_FOLDER'], file.filename))
                nomes_arquivos.append(file.filename)
                count += 1

        registrar_log(f"O dispositivo [{ip_cliente}] enviou {count} arquivo(s) com sucesso: {nomes_arquivos}")
        return "OK", 200

    html_upload = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enviar Arquivos Extras</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 60px; background-color: #f4f4f9; }
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
            <h2>Enviar Vídeos Pesados</h2>
            <form id="upload-form">
                <input type="file" id="file-input" name="files" multiple required>
                <button type="submit" id="submit-btn">Enviar tudo para o PC</button>
            </form>

            <div id="progress-container">
                <div class="progress-bar-wrapper">
                    <div id="progress-bar"></div>
                </div>
                <div id="status-text">0%</div>
                <div class="info-box">
                    <span id="upload-speed">Velocidade: 0 MB/s</span>
                    <span id="upload-eta">Restante: --:--</span>
                </div>
                <div id="wakelock-msg" class="wakelock-status">🔒 Mantendo a tela ligada...</div>
            </div>

            <a class="back" href="/">&larr; Voltar</a>
        </div>

        <script>
            let wakeLock = null;

            // Função para forçar a tela a ficar ligada
            async function ativarModoTelaAtiva() {
                try {
                    if ('wakeLock' in navigator) {
                        wakeLock = await navigator.wakeLock.request('screen');
                        document.getElementById('wakelock-msg').style.display = 'block';
                    }
                } catch (err) {
                    console.log("WakeLock não suportado ou negado: ", err.message);
                    document.getElementById('wakelock-msg').style.display = 'none';
                }
            }

            // Função para liberar a tela quando o upload acabar
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

                // Ativa o bloqueio de descanso de tela antes do upload começar
                ativarModoTelaAtiva();

                let startTime = new Date().getTime();

                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        var percent = Math.round((e.loaded / e.total) * 100);
                        document.getElementById('progress-bar').style.width = percent + '%';
                        document.getElementById('status-text').innerText = percent + '%';

                        // Cálculo de Velocidade e Tempo Restante (ETA)
                        let currentTime = new Date().getTime();
                        let duration = (currentTime - startTime) / 1000; // em segundos
                        if (duration > 0) {
                            let bps = e.loaded / duration; // bytes por segundo
                            let mbps = (bps / (1024 * 1024)).toFixed(2); // megabytes por segundo
                            document.getElementById('upload-speed').innerText = "Velocidade: " + mbps + " MB/s";

                            let remainingBytes = e.total - e.loaded;
                            let remainingTime = remainingBytes / bps; // segundos restantes

                            if (remainingTime > 0) {
                                let mins = Math.floor(remainingTime / 60);
                                let secs = Math.floor(remainingTime % 60);
                                // Formata pra ficar bonito (ex: 02m 05s)
                                let formatado = (mins > 0 ? mins + "m " : "") + secs + "s";
                                document.getElementById('upload-eta').innerText = "Restante: ~ " + formatado;
                            } else {
                                document.getElementById('upload-eta').innerText = "Restante: Finalizando...";
                            }
                        }
                    }
                });

                xhr.addEventListener('load', function() {
                    desativarModoTelaAtiva(); // Devolve o controle da tela ao sistema

                    if (xhr.status === 200) {
                        alert("Todos os arquivos pesados foram enviados com sucesso!");
                    } else {
                        alert("Ocorreu um erro no envio do arquivo.");
                    }

                    document.getElementById('progress-container').style.display = 'none';
                    document.getElementById('submit-btn').disabled = false;
                    document.getElementById('file-input').value = '';
                    window.location.href = "/";
                });

                xhr.open('POST', '/enviar', true);
                xhr.send(formData);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_upload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
