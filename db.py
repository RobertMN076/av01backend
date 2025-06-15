from flask import current_app, g
from flask_mysqldb import MySQL
import MySQLdb.cursors
import click # Importa click para o comando CLI
import re # Importa re para dividir o schema.sql

# Declaração do objeto MySQL. Ele será inicializado em init_app.
mysql_db = MySQL()

def get_db():
    """
    Obtém um cursor do MySQL para a conexão atual.
    O cursor é armazenado em g.db para ser reutilizado durante a requisição.
    """
    if 'db_cursor' not in g:
        # Pega a conexão do MySQL. Flask-MySQLdb gerencia o pool de conexões.
        # Usa DictCursor para que os resultados das consultas sejam dicionários.
        g.db_cursor = mysql_db.connection.cursor(MySQLdb.cursors.DictCursor)
    return g.db_cursor

def close_db(e=None):
    """
    Fecha o cursor do banco de dados ao final da requisição.
    """
    db_cursor = g.pop('db_cursor', None) # Pega o cursor armazenado em g

    if db_cursor is not None:
        db_cursor.close() # Fecha o cursor, liberando os recursos

def init_db():
    """
    Inicializa o banco de dados executando o script SQL do schema.
    Para MySQL, é necessário executar cada comando SQL separadamente.
    """
    cursor = get_db() # Obtém um cursor

    # Abre o arquivo schema.sql e lê seu conteúdo
    with current_app.open_resource('schema.sql') as f:
        schema_script = f.read().decode('utf8')

    # Divide o script em comandos individuais usando ponto e vírgula como delimitador,
    # ignorando linhas vazias ou comentários.
    # O regex re.split(r';\s*$', ...) é usado para garantir que apenas semicolons no final da linha
    # sejam usados como delimitadores, evitando problemas com semicolons dentro de strings ou comentários.
    commands = [cmd.strip() for cmd in re.split(r';\s*$', schema_script, flags=re.MULTILINE) if cmd.strip()]

    for command in commands:
        try:
            cursor.execute(command) # Executa cada comando SQL
        except Exception as e:
            # Imprime o comando que causou o erro para facilitar a depuração
            print(f"Erro ao executar SQL: {command}\nErro: {e}")
            raise # Re-lança a exceção para que o Flask a capture

    # Confirma as alterações no banco de dados
    mysql_db.connection.commit()

@click.command('init-db')
def init_db_command():
    """Limpa os dados existentes e cria novas tabelas."""
    init_db()
    click.echo('Banco de dados inicializado.')

def init_app(app):
    """
    Registra as funções de callback para a aplicação Flask.
    """
    # Inicializa o objeto MySQL com a aplicação Flask.
    # As configurações de conexão (MYSQL_HOST, MYSQL_USER, etc.) devem estar em app.config
    mysql_db.init_app(app)

    # Garante que o cursor seja fechado automaticamente ao final de cada requisição
    app.teardown_appcontext(close_db)
    # Adiciona o comando 'init-db' ao CLI do Flask
    app.cli.add_command(init_db_command)

