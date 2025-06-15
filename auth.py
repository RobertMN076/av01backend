import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

# Ajusta as importações para serem relativas ao pacote
from db import get_db, mysql_db # Importa também o objeto mysql_db para o commit
import MySQLdb # Importa MySQLdb para acessar IntegrityError

bp = Blueprint('auth', __name__, url_prefix='/auth')


def get_user(id):
    """Obtém um usuário do banco de dados pelo ID, ou aborta 404 se não encontrado."""
    db_cursor = get_db() # Obtém o cursor
    db_cursor.execute( # Executa a consulta no cursor
        'SELECT id, username FROM user WHERE id = %s', (id,) # Use %s para MySQL
    )
    user = db_cursor.fetchone() # fetchone() é chamado no cursor

    return user

@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Permite o registro de novos usuários."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_cursor = get_db() # Obtém o cursor
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db_cursor.execute( # Executa a inserção no cursor
                    "INSERT INTO user (username, password) VALUES (%s, %s)", # Use %s para MySQL
                    (username, generate_password_hash(password)),
                )
                mysql_db.connection.commit() # Commita as alterações
            except MySQLdb.IntegrityError: # Exceção de integridade do MySQLdb
                error = f"User {username} is already registered."
            except Exception as e: # Captura outras exceções genéricas do DB
                error = f"An error occurred during registration: {e}"
                mysql_db.connection.rollback() # Faz rollback em caso de erro
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Permite o login de usuários existentes."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_cursor = get_db() # Obtém o cursor
        error = None
        db_cursor.execute( # Executa a consulta no cursor
            'SELECT * FROM user WHERE username = %s', (username,) # Use %s para MySQL
        )
        user = db_cursor.fetchone() # fetchone() é chamado no cursor

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    """Carrega o usuário logado antes de cada requisição."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        db_cursor = get_db() # Obtém o cursor
        db_cursor.execute( # Executa a consulta no cursor
            'SELECT * FROM user WHERE id = %s', (user_id,) # Use %s para MySQL
        )
        g.user = db_cursor.fetchone() # fetchone() é chamado no cursor

@bp.route('/logout')
def logout():
    """Desloga o usuário."""
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    """Decorator para exigir login em certas rotas."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """Permite a atualização de um usuário."""
    user = get_user(id) # get_user já usa o novo padrão

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'

        if error is not None:
            flash(error)
        else:
            db_cursor = get_db() # Obtém o cursor
            db_cursor.execute( # Executa a atualização no cursor
                'UPDATE user SET username = %s, password = %s' # Use %s para MySQL
                ' WHERE id = %s', # Use %s para MySQL
                (username, generate_password_hash(password), id)
            )
            mysql_db.connection.commit() # Commita as alterações
            return redirect(url_for('tasklist.index')) # Redireciona para a lista de tarefas após a atualização

    return render_template('auth/updateuser.html', user=user)


@bp.route('/<int:id>/delete-user', methods=('POST',))
@login_required
def delete_user(id):
    """Permite a exclusão de um usuário."""
    user_to_delete = get_user(id)

    if user_to_delete is None: # Verifica se o usuário existe antes de tentar deletar
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.login'))

    if user_to_delete['id'] != g.user['id']:
        flash('Você não tem permissão para deletar esta conta.', 'error')
        return redirect(url_for('auth.login')) # Ou outro redirecionamento apropriado

    db_cursor = get_db() # Obtém o cursor
    try:
        db_cursor.execute('DELETE FROM user WHERE id = %s', (id,)) # Use %s para MySQL
        mysql_db.connection.commit() # Commita as alterações

        if user_to_delete['id'] == g.user['id']:
            logout() # Se o próprio usuário se deletou, desloga
            flash(f"Sua conta '{user_to_delete['username']}' foi deletada com sucesso.", 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(f"A conta '{user_to_delete['username']}' foi deletada com sucesso.", 'success')
            return redirect(url_for('index')) # Redireciona para a página principal se deletou outro usuário (admin)

    except Exception as e:
        # Importante: para rollback, precisamos do objeto de conexão
        mysql_db.connection.rollback() # Faz rollback em caso de erro
        flash(f"Ocorreu um erro ao deletar a conta: {e}", 'error')

    return redirect(url_for('auth.login'))

