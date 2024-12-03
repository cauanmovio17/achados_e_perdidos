from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
from Rotas.rota_usuarios import usuarios_bp
from Rotas.rota_item import itens_bp
from Rotas.rota_categoria import categorias_bp


from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)
CORS(app)
app.secret_key = "123456"

app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
app.register_blueprint(itens_bp, url_prefix='/itens')
app.register_blueprint(categorias_bp, url_prefix='/categorias')





@app.route('/')
def home():
    return redirect(url_for('itens.listar_todos_itens'))

if __name__ == "__main__":
    app.run(port=5000, host="192.168.0.120", debug=True)