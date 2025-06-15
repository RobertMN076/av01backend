import os

from flask import Flask


def create_app(test_config=None):
    # cria e configura o app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # Removido: DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        # Adicionado: Configurações do Banco de Dados MySQL
        MYSQL_HOST='localhost',
        MYSQL_USER='root',
        MYSQL_PASSWORD='', # Senha vazia para o usuário 'root' do XAMPP
        MYSQL_DB='todolist', # <<< MUITO IMPORTANTE: MUDAR PARA O NOME DO SEU BANCO DE DADOS REAL!
        MYSQL_CHARSET='utf8mb4' # Garante suporte a caracteres especiais e emojis
    )

    if test_config is None:
        # carrega a configuração da instância, se existir, quando não estiver testando
        app.config.from_pyfile('config.py', silent=True)
    else:
        # carrega a configuração de teste se for passada
        app.config.from_mapping(test_config)

    # garante que a pasta da instância exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # uma página simples que diz olá
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    # Importa e inicializa o módulo db
    from . import db
    db.init_app(app) # Isso inicializa Flask-MySQLdb com o app e registra callbacks

    # Importa e registra os blueprints
    from . import auth
    app.register_blueprint(auth.bp)

    from . import tasklist
    app.register_blueprint(tasklist.bp)
    app.add_url_rule('/', endpoint='index')

    from . import task
    app.register_blueprint(task.bp)

    return app

