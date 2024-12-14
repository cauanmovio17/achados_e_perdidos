from flask import Blueprint, request, render_template, redirect, url_for, session
from datetime import datetime, date
from conexao import criar_conexao, fechar_conexao
from functools import wraps
from psycopg2.extras import RealDictCursor  # Importa o RealDictCursor
import vercel_blob


itens_bp = Blueprint('itens', __name__)


# Função para verificar se o usuário está logado
def login_required(func):
    @wraps(func)  # Mantém metadados da função decorada
    def wrapper(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('usuarios.login_usuario'))
        return func(*args, **kwargs)
    return wrapper

def uploadFoto(arquivo) :
    try:
        nome_arquivo = arquivo.filename
        url_image = vercel_blob.put(nome_arquivo, arquivo.read(), {})  # Envia o arquivo para o Blob
        return url_image['url']
    except Exception as e:
        return "Erro ao processar a imagem: ", 500
    
def excluirFoto(arquivo):
    try:
        # Usa o método delete da biblioteca vercel_blob para remover a imagem
        vercel_blob.delete(arquivo)  # Remove o arquivo do Blob
        
        print({"message": "Imagem deletada com sucesso", "success": True})
    except Exception as e:
        print({"error": "Erro ao deletar a imagem: " + str(e)})
    

@itens_bp.route('novoitem', methods=['GET', 'POST'])
@login_required
def novo_item():
    if 'usuario' not in session:
        return redirect(url_for('usuarios.login_usuario'))
    
    if request.method == 'POST':
        NOME_ITEM = request.form['nome_item']
        # FOTO = request.form['foto']
        CARACTERISTICA = request.form['caracteristicas_item']
        DATA_PERDA = request.form['data_perdido']
        LOCAL_ENCONTRADO = request.form['local_encontrado']
        ID_CATEGORIA = request.form['id_categoria']
        
        FOTO = uploadFoto(request.files.get('foto') )

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
    nome = request.args.get('nome')  # Obtém o nome da pesquisa
    categoria_id = request.args.get('id_categoria')  # Obtém o ID da categoria da pesquisa
    
    # Cria a conexão com o banco de dados
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Define a consulta SQL inicial com base nos parâmetros
    query = """
        SELECT * FROM ITENS WHERE data_entrega IS NULL
    """
    filters = []
    
    # Adiciona filtro por nome
    if nome:
        query += " AND nome_item ILIKE %s"
        filters.append(f"%{nome}%")
    
    # Adiciona filtro por categoria
    if categoria_id:
        query += " AND id_categoria = %s"
        filters.append(categoria_id)
    
    query += " ORDER BY id_item DESC"
    
    # Executa a consulta com os filtros
    cursor.execute(query, tuple(filters))
    
    itens = cursor.fetchall()
    cursor.close()
    
    # Recupera todas as categorias para o filtro no frontend
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM CATEGORIAS")
    categorias = cursor.fetchall()
    cursor.close()
    
    # Fecha a conexão com o banco
    fechar_conexao(conn)
    
    # Convertendo a data para o formato DD/MM/AAAA
    for item in itens:
        if isinstance(item['data_perda'], date):
            item['data_perda'] = item['data_perda'].strftime('%d/%m/%Y')
    
    return render_template('Telainicial.html', itens=itens, categorias=categorias)

# Exclusão de Item
@itens_bp.route('/excluir/<int:id>', methods=['GET'])
def excluir_item(id):
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT foto FROM ITENS WHERE ID_ITEM = %s", (id,))
    item = cursor.fetchone()
    excluirFoto(item['foto'])
    
    cursor.execute("DELETE FROM ITENS WHERE ID_ITEM = %s", (id,))
    conn.commit()
    cursor.close()
    fechar_conexao(conn)
    return redirect(url_for('.listar_todos_itens'))

# Alteração de Item
@itens_bp.route('/alterar/<int:id>', methods=['GET', 'POST'])
@login_required
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
        
        if request.files.get('file') :
            excluirFoto(FOTO)
            FOTO = uploadFoto(request.files.get('file') )

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
@login_required
def listar_devolucoes():
    # Parâmetros de busca
    nome = request.args.get('nome')  # Obtém o nome da pesquisa
    id_categoria = request.args.get('id_categoria')  # Obtém o ID da categoria da pesquisa

    # Cria a conexão com o banco de dados
    conn = criar_conexao()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Consulta básica com filtros dinâmicos
    query = """
        SELECT nome_item, nome_entregue, data_entrega, foto
        FROM ITENS 
        WHERE data_entrega IS NOT NULL
    """
    filters = []

    # Adiciona filtro por nome, se fornecido
    if nome:
        query += " AND nome_item ILIKE %s"
        filters.append(f"%{nome}%")

    # Adiciona filtro por categoria, se fornecido
    if id_categoria:
        query += " AND id_categoria = %s"
        filters.append(id_categoria)

    query += " ORDER BY data_entrega DESC"

    # Executa a consulta com os filtros
    cursor.execute(query, tuple(filters))
    devolucoes = cursor.fetchall()

    # Consulta de categorias
    cursor.execute("SELECT * FROM CATEGORIAS")
    categorias = cursor.fetchall()

    cursor.close()
    fechar_conexao(conn)

    # Formata as datas para DD/MM/AAAA
    for devolucao in devolucoes:
        if isinstance(devolucao['data_entrega'], date):
            devolucao['data_entrega'] = devolucao['data_entrega'].strftime('%d/%m/%Y')

    return render_template('ListaDevolucao.html', devolucoes=devolucoes, categorias=categorias)




# Devolução de Item
@itens_bp.route('/devolver_item/<int:id>', methods=['GET', 'POST'])
@login_required
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
