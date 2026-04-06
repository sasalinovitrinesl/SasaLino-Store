import os
import json
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_FILE = 'database.json'
CONFIG_FILE = 'config.json'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"senha": "158815"}, f)

def get_senha():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)['senha']

def set_senha(nova_senha):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"senha": nova_senha}, f)

def load_db():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, 'r') as f:
        try: return json.load(f)
        except: return []

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    produtos = load_db()
    whatsapp_number = "5511999999999" # Ajuste o número aqui
    return render_template('index.html', produtos=produtos, whatsapp=whatsapp_number)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    erro = None
    sucesso = None
    senha_mestra = get_senha()
    produtos = load_db()

    if request.method == 'POST':
        senha_digitada = request.form.get('senha_acesso')
        
        if senha_digitada == senha_mestra:
            # AÇÃO: Apagar Produto
            apagar_idx = request.form.get('apagar_idx')
            if apagar_idx is not None:
                idx = int(apagar_idx)
                # Remove o arquivo da imagem para não encher o celular
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], produtos[idx]['img'])
                if os.path.exists(img_path): os.remove(img_path)
                
                produtos.pop(idx)
                save_db(produtos)
                sucesso = "Produto removido!"
                return render_template('admin.html', produtos=produtos, sucesso=sucesso, senha_valida=senha_mestra)

            # AÇÃO: Alterar Senha
            nova_senha = request.form.get('nova_senha')
            if nova_senha:
                set_senha(nova_senha)
                sucesso = "Senha alterada com sucesso!"
                return render_template('admin.html', produtos=produtos, sucesso=sucesso, senha_valida=nova_senha)

            # AÇÃO: Postar Produto
            nome = request.form.get('nome')
            preco = request.form.get('preco')
            foto = request.files.get('foto')
            if foto and nome and preco:
                filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                produtos.append({"nome": nome, "preco": preco, "img": filename})
                save_db(produtos)
                return redirect(url_for('index'))
            
            return render_template('admin.html', produtos=produtos, senha_valida=senha_mestra)
        else:
            erro = "Senha Incorreta!"

    return render_template('login.html', erro=erro)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
