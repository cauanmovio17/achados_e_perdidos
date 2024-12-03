from flask import Blueprint, request, render_template, redirect, url_for, session
from conexao import criar_conexao, fechar_conexao
from hashlib import sha256

from psycopg2.extras import RealDictCursor  # Importa o RealDictCursor

usuarios_bp = Blueprint('usuarios', __name__)

# Função para criptografar e checar senha
def checar_senha(senhaBanco, senha):
    senha = sha256(senha.encode('utf-8')).hexdigest()
    return senha == senhaBanco

# Rota para criar usuário
@usuarios_bp.route('/novousuario', methods=['GET', 'POST'])
def criar_usuario():
    if request.method == 'POST':
        NOME = request.form.get('nome')
        LOGIN = request.form['LOGIN']
        SENHA = request.form.get('SENHA')

        if not NOME or not LOGIN or not SENHA:
            return render_template('cadastroUsuario.html', mensagem='Todos os campos são obrigatórios!')

        senhaCripto = sha256(SENHA.encode('utf-8')).hexdigest()

        try:
            conn = criar_conexao()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO USUARIOS (nome, login, senha) VALUES (%s, %s, %s)", 
                (NOME, LOGIN, senhaCripto)
            )
            conn.commit()
            mensagem = 'Usuário criado com sucesso!'
        except Exception as e:
            conn.rollback()
            mensagem = f'Erro ao criar usuário: {e}'
        finally:
            cursor.close()
            fechar_conexao(conn)

        return render_template('login.html', mensagem=mensagem)

    return render_template('cadastroUsuario.html')

# Rota para login
@usuarios_bp.route('/login', methods=['GET', 'POST'])
def login_usuario():
    if request.method == 'POST':
        LOGIN = request.form.get('LOGIN')
        SENHA = request.form.get('SENHA')

        if not LOGIN or not SENHA:
            return render_template('login.html', mensagem='Preencha todos os campos!')

        try:
            conn = criar_conexao()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT SENHA, LOGIN, ID_USUARIO FROM USUARIOS WHERE LOGIN = %s", 
                (LOGIN,)
            )
            usuarioEncontrado = cursor.fetchone()
        finally:
            cursor.close()
            fechar_conexao(conn)

        if usuarioEncontrado and checar_senha(usuarioEncontrado['senha'], SENHA):
            # Sessão bem definida
            session['usuario'] = {
                'id_usuario': usuarioEncontrado.get('id_usuario'),
                'login': usuarioEncontrado.get('login')
            }
            return redirect(url_for('itens.listar_todos_itens'))

        return render_template('login.html', mensagem='Login ou senha incorretos.')

    return render_template('login.html')

# Rota para listar todos os usuários
@usuarios_bp.route('/listar_usuarios', methods=['GET'])
def listar_todos_usuarios():
    if 'usuario' not in session:
        return redirect(url_for('usuarios.login_usuario'))

    try:
        conn = criar_conexao()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM USUARIOS ORDER BY login;")
        usuarios = cursor.fetchall()
    finally:
        cursor.close()
        fechar_conexao(conn)

    return render_template('ListaUsuarios.html', usuarios=usuarios)

# Rota para excluir usuário
@usuarios_bp.route('/excluir_usuario/<int:id_usuario>', methods=['POST'])
def excluir_usuario(id_usuario):
    if 'usuario' not in session or 'id_usuario' not in session['usuario']:
        return redirect(url_for('usuarios.login_usuario'))

    try:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM USUARIOS WHERE ID_USUARIO = %s", (id_usuario,))
        conn.commit()

        if session['usuario']['id_usuario'] == id_usuario:
            session.pop('usuario', None)

        return redirect(url_for('usuarios.listar_todos_usuarios'))
    except Exception as e:
        conn.rollback()
        return render_template('ListaUsuarios.html', mensagem=f"Erro ao excluir usuário: {e}")
    finally:
        cursor.close()
        fechar_conexao(conn)

# Rota para alterar usuário
@usuarios_bp.route('/alterar/<int:id>', methods=['GET', 'POST'])
def alterar_usuario(id):
    if 'usuario' not in session or 'id_usuario' not in session['usuario']:
        return redirect(url_for('usuarios.login_usuario'))

    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        NOME = request.form.get('NOME')
        LOGIN = request.form.get('LOGIN')
        SENHA = request.form.get('SENHA')
        
        # Se não passar NOME ou LOGIN, exibe erro
        if not NOME or not LOGIN:
            return render_template('alterarUsuario.html', mensagem='Nome e Login são obrigatórios!', usuario={'ID_USUARIO': id, 'NOME': NOME, 'LOGIN': LOGIN})

        senhaCripto = None
        if SENHA:
            senhaCripto = sha256(SENHA.encode('utf-8')).hexdigest()

        try:
            if senhaCripto:
                cursor.execute(
                    "UPDATE USUARIOS SET nome = %s, login = %s, senha = %s WHERE ID_USUARIO = %s",
                    (NOME, LOGIN, senhaCripto, id)
                )
            else:
                cursor.execute(
                    "UPDATE USUARIOS SET nome = %s, login = %s WHERE ID_USUARIO = %s",
                    (NOME, LOGIN, id)
                )
            conn.commit()
            return redirect(url_for('usuarios.listar_todos_usuarios'))
        except Exception as e:
            conn.rollback()
            return render_template('alterarUsuario.html', mensagem=f'Erro ao alterar usuário: {e}', usuario={'ID_USUARIO': id, 'NOME': NOME, 'LOGIN': LOGIN})

        finally:
            cursor.close()
            fechar_conexao(conn)

    cursor.execute("SELECT ID_USUARIO as id_usuario, nome, login FROM USUARIOS WHERE ID_USUARIO = %s", (id,))
    usuario = cursor.fetchone()
    cursor.close()
    fechar_conexao(conn)

    return render_template("alterarUsuario.html", usuario=usuario)

# Rota para logout
@usuarios_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('home'))
