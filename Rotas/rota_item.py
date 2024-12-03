from flask import Blueprint, request, render_template, redirect, url_for, session
from datetime import datetime, date
from conexao import criar_conexao, fechar_conexao

from psycopg2.extras import RealDictCursor  # Importa o RealDictCursor


itens_bp = Blueprint('itens', __name__)

@itens_bp.route('novoitem', methods=['GET', 'POST'])
def novo_item():
    if 'usuario' not in session:
        return redirect(url_for('usuarios.login_usuario'))
    
    if request.method == 'POST':
        NOME_ITEM = request.form['nome_item']
        FOTO = request.form['foto']
        CARACTERISTICA = request.form['caracteristicas_item']
        DATA_PERDA = request.form['data_perdido']
        LOCAL_ENCONTRADO = request.form['local_encontrado']
        ID_CATEGORIA = request.form['id_categoria']

        try:
            # Inserção no banco de dados
            conn = criar_conexao()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO ITENS (nome_item, foto, caracteristicas, data_perda, local_encontrado, id_categoria)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (NOME_ITEM, FOTO, CARACTERISTICA, DATA_PERDA, LOCAL_ENCONTRADO, ID_CATEGORIA))
            
            conn.commit()
            cursor.close()
            fechar_conexao(conn)
            return redirect(url_for('itens.listar_todos_itens'))

        except Exception as erro:
            print(f"Erro ao cadastrar item: {erro}")
            return "Erro interno no servidor", 500

    # Listagem de categorias
    usuario_nome = session.get('usuario')['login']
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM CATEGORIAS")
    categorias = cursor.fetchall()
    cursor.close()
    fechar_conexao(conn)
   
    return render_template('cadastroItens.html', usuario_nome=usuario_nome, categorias=categorias)

# Listagem de Todos os Itens
@itens_bp.route('/listar_itens', methods=['GET'])
def listar_todos_itens():
    conn = criar_conexao()
    # cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT * FROM ITENS WHERE data_entrega IS NULL ORDER BY id_item DESC;
    """)
    
    itens = cursor.fetchall()
    cursor.close()
    fechar_conexao(conn)
    # Convertendo a data para o formato DD/MM/AAAA
    for item in itens:
        if isinstance(item['data_perda'], date):  # Certifique-se de usar a classe correta aqui
            item['data_perda'] = item['data_perda'].strftime('%d/%m/%Y')

    return render_template('telainicial.html', itens=itens)

# Exclusão de Item
@itens_bp.route('/excluir/<int:id>', methods=['GET'])
def excluir_item(id):
    conn = criar_conexao()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ITENS WHERE ID_ITEM = %s", (id,))
    conn.commit()
    cursor.close()
    fechar_conexao(conn)
    return redirect(url_for('.listar_todos_itens'))

# Alteração de Item
@itens_bp.route('/alterar/<int:id>', methods=['GET', 'POST'])
def alterar_item(id):
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        NOME_ITEM = request.form['nome_item']
        FOTO = request.form['foto']
        CARACTERISTICA = request.form['caracteristicas_item']
        DATA_PERDA = request.form['data_perdido']
        LOCAL_ENCONTRADO = request.form['local_encontrado']
        ID_CATEGORIA = request.form['id_categoria']

        cursor.execute("""
            UPDATE ITENS
            SET nome_item = %s, foto = %s, caracteristicas = %s, data_perda = %s, local_encontrado = %s, id_categoria = %s
            WHERE id_item = %s
        """, (NOME_ITEM, FOTO, CARACTERISTICA, DATA_PERDA, LOCAL_ENCONTRADO, ID_CATEGORIA, id))
        
        conn.commit()
        cursor.close() 
        fechar_conexao(conn)
        return redirect(url_for('itens.listar_todos_itens'))

    cursor.execute("SELECT * FROM ITENS WHERE ID_ITEM = %s", (id,))
    item = cursor.fetchone()

    cursor.execute("SELECT * FROM CATEGORIAS")
    categorias = cursor.fetchall()

    cursor.close()
    fechar_conexao(conn)
    
    return render_template("alterarItem.html", item=item, categorias=categorias)

# Listagem de Devoluções
@itens_bp.route('/listar_devolucoes', methods=['GET'])
def listar_devolucoes():
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT nome_item, nome_entregue, data_entrega, foto
        FROM ITENS 
        WHERE data_entrega IS NOT NULL
        ORDER BY data_entrega DESC
    """)

    devolucoes = cursor.fetchall()
    cursor.close()
    fechar_conexao(conn)
      # Convertendo a data para o formato DD/MM/AAAA
    for devolucao in devolucoes:
        if isinstance(devolucao['data_entrega'], date):  # Certifique-se de usar a classe correta aqui
            devolucao['data_entrega'] = devolucao['data_entrega'].strftime('%d/%m/%Y')

    return render_template('ListaDevolucao.html', devolucoes=devolucoes)

# Devolução de Item
@itens_bp.route('/devolver_item/<int:id>', methods=['GET', 'POST'])
def devolver_item(id):
    if 'usuario' not in session:
        return redirect(url_for('usuarios.login_usuario'))
    
    if request.method == 'POST':
        nome_entregue = request.form['nome_entregue']
        data_entrega = datetime.now().strftime('%Y-%m-%d')  # Data atual
        
        conn = criar_conexao()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            UPDATE ITENS 
            SET nome_entregue = %s, data_entrega = %s 
            WHERE id_item = %s
        """, (nome_entregue, data_entrega, id))
        
        conn.commit()
        cursor.close()
        fechar_conexao(conn)
        return redirect(url_for('itens.listar_todos_itens'))
    
    usuario_nome = session.get('usuario')['login']
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM ITENS WHERE ID_ITEM = %s", (id,))
    item = cursor.fetchone()
    cursor.close()
    fechar_conexao(conn)
   
    return render_template('devolucao.html', item=item)
