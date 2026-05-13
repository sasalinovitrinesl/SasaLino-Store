import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sasalino_secret_2026'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_FILE = 'database.json'
CONFIG_FILE = 'config.json'
STATS_FILE = 'stats.json'

if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"senha": "158815", "whatsapp": "16892336326", "instagram": "", "facebook": ""}, f)
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'w') as f: json.dump({"visitas": 0, "cliques": 0}, f)

def get_stats():
    try:
        with open(STATS_FILE, 'r') as f: return json.load(f)
    except: return {"visitas": 0, "cliques": 0}

def save_stats(st):
    with open(STATS_FILE, 'w') as f: json.dump(st, f)

def load_db():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except: return []

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    if 'ja_visitou' not in session:
        st = get_stats()
        st['visitas'] += 1
        save_stats(st)
        session['ja_visitou'] = True
    
    with open(CONFIG_FILE, 'r') as f: config = json.load(f)
    
    produtos_brutos = load_db()
    # Garante que campos opcionais existam para não quebrar o template
    for p in produtos_brutos:
        if 'descricao' not in p: p['descricao'] = "Sem descrição."
        if 'categoria' not in p: p['categoria'] = "todos"
        
    produtos = produtos_brutos[::-1] # Inverte para mostrar os novos primeiro
    return render_template('index.html', produtos=produtos, config=config)

@app.route('/registrar_clique', methods=['POST'])
def registrar_clique():
    st = get_stats()
    st['cliques'] += 1
    save_stats(st)
    return {"status": "ok"}

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    with open(CONFIG_FILE, 'r') as f: config = json.load(f)
    
    # Lógica de Login corrigida
    if request.method == 'POST' and 'senha_login' in request.form:
        if request.form.get('senha_login') == config['senha']:
            session['admin_logado'] = True
            return redirect(url_for('admin'))
    
    if not session.get('admin_logado'):
        return render_template('login.html')

    if request.method == 'POST':
        # Logout
        if 'logout' in request.form:
            session.pop('admin_logado', None)
            return redirect(url_for('index'))

        # Atualizar Redes Sociais
        if 'update_config' in request.form:
            config['whatsapp'] = request.form.get('whatsapp')
            config['instagram'] = request.form.get('instagram')
            config['facebook'] = request.form.get('facebook')
            with open(CONFIG_FILE, 'w') as f: json.dump(config, f)
            return redirect(url_for('admin'))

        # Zerar Stats
        if 'zerar_stats' in request.form:
            save_stats({"visitas": 0, "cliques": 0})
            return redirect(url_for('admin'))

        # Deletar Produto
        if 'apagar_idx' in request.form:
            db = load_db()
            idx = int(request.form.get('apagar_idx'))
            if 0 <= idx < len(db):
                db.pop(idx)
                save_db(db)
            return redirect(url_for('admin'))

        # ADICIONAR NOVO PRODUTO
        if 'nome' in request.form:
            nome = request.form.get('nome')
            preco = request.form.get('preco')
            categoria = request.form.get('categoria', 'todos')
            tag = request.form.get('tag', '')
            descricao = request.form.get('descricao', '')

            fotos = request.files.getlist('fotos')
            video = request.files.get('video')

            filenames = []
            for f in fotos:
                if f and f.filename:
                    fn = secure_filename(f.filename)
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                    filenames.append(fn)

            vid_name = None
            if video and video.filename:
                vid_name = secure_filename(video.filename)
                video.save(os.path.join(app.config['UPLOAD_FOLDER'], vid_name))

            if filenames: # Só salva se tiver pelo menos uma foto
                db = load_db()
                db.append({
                    "nome": nome,
                    "preco": preco,
                    "categoria": categoria,
                    "tag": tag,
                    "imgs": filenames,
                    "video": vid_name,
                    "descricao": descricao
                })
                save_db(db)
            return redirect(url_for('admin'))

    produtos = load_db()
    stats = get_stats()
    return render_template('admin.html', produtos=produtos, stats=stats, config=config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
