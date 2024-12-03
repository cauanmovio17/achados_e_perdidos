# import mysql.connector
import os
import psycopg2

DATABASE_URL = os.getenv("POSTGRES_URL")

def criar_conexao():
    # return mysql.connector.connect(
    #     host = "localhost",
    #     user = "root",
    #     password = "admin",
    #     database = "achadoseperdidos"
    # )
    try:
        conexao = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conexao
    except Exception as e:
        print(f'Erro ao conectar {e}')
        return None

def fechar_conexao(conexao):
    if conexao:
        conexao.close()