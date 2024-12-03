from flask import Blueprint, request, render_template, redirect, url_for, session
from conexao import criar_conexao, fechar_conexao

from psycopg2.extras import RealDictCursor  # Importa o RealDictCursor

categorias_bp = Blueprint('categorias', __name__)

# Função para listar categorias
@categorias_bp.route('/listar_categorias', methods=['GET'])
def listar_categorias():
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM CATEGORIAS")
    categorias = cursor.fetchall()
    cursor.close()
    fechar_conexao(conn)
    return render_template('ListaCategoria.html', categorias=categorias)  # Passa as categorias para o template

@categorias_bp.route('/novaCategoria', methods=['GET', 'POST'])
def nova_categoria():
    if request.method == 'POST':
        nome_categoria = request.form['CATEGORIA']

        try:
            conn = criar_conexao()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('INSERT INTO CATEGORIAS(nome_categoria) VALUES (%s)', (nome_categoria,))
            conn.commit()
            cursor.close()
            fechar_conexao(conn)
            return redirect(url_for('categorias.listar_categorias'))  # Redireciona para a listagem de categorias

        except Exception as e:
            print(f"Erro ao inserir categoria: {e}")
            return render_template('erro.html', mensagem="Erro ao adicionar categoria")

    return render_template('AdcionarCategoria.html')  # Apenas exibe a tela de adicionar categoria

@categorias_bp.route('/excluir/<int:id>', methods=['GET'])
def excluir_categoria(id):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM CATEGORIAS WHERE ID_CATEGORIA = %s", (id,))
    conn.commit()
    cursor.close()
    fechar_conexao(conn)
    return redirect(url_for('.listar_categorias'))  # Redireciona para a listagem após exclusão

@categorias_bp.route('/alterar/<int:id>', methods=['GET', 'POST'])
def alterar_categoria(id):
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        nome_categoria = request.form['CATEGORIA']
        cursor.execute("UPDATE CATEGORIAS SET nome_categoria = %s WHERE ID_CATEGORIA = %s", (nome_categoria, id))
        conn.commit()
        cursor.close()
        fechar_conexao(conn)
        return redirect(url_for('categorias.listar_categorias'))  # Redireciona para a listagem após alteração

    # Para GET, buscar a categoria existente
    cursor.execute("SELECT * FROM CATEGORIAS WHERE ID_CATEGORIA = %s", (id,))
    categoria = cursor.fetchone()
    cursor.close()
    fechar_conexao(conn)
    return render_template('alterar_categoria.html', categoria=categoria)  # Passa a categoria para o template
