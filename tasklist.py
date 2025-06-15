from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db, mysql_db # Importa também o objeto mysql_db para o commit

bp = Blueprint('tasklist', __name__)

@bp.route('/')
def index():
    """
    Exibe uma lista de tarefas, incluindo informações do autor.
    """
    db_cursor = get_db() # get_db() agora retorna o cursor do MySQL

    # Executa a consulta e armazena o resultado da execução (que é o próprio cursor)
    # na mesma variável para clareza e para garantir que fetchall seja chamado no cursor.
    db_cursor.execute(
        """
        SELECT tasklist.id, title, body, created, author_id, username
        FROM tasklist JOIN user ON tasklist.author_id = user.id
        ORDER BY created DESC
        """
    )
    tasklists = db_cursor.fetchall() # fetchall() é chamado no cursor que acabou de executar

    return render_template('task/index.html', tasklists=tasklists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """
    Permite criar uma nova tasklist.
    """
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db_cursor = get_db() # Obtém o cursor
            db_cursor.execute(
                'INSERT INTO tasklist (title, body, author_id)'
                ' VALUES (%s, %s, %s)', # MySQL usa %s como placeholder
                (title, body, g.user['id'])
            )
            mysql_db.connection.commit() # Commita as alterações no banco de dados MySQL
            return redirect(url_for('tasklist.index'))

    return render_template('task/create.html')

def get_post(id, check_author=True):
    """
    Obtém uma tasklist pelo ID, opcionalmente verificando o autor.
    """
    db_cursor = get_db() # Obtém o cursor
    db_cursor.execute(
        """
        SELECT tasklist.id, title, body, created, author_id, username
        FROM tasklist JOIN user ON tasklist.author_id = user.id
        WHERE tasklist.id = %s
        """, # MySQL usa %s como placeholder
        (id,)
    )
    tasklist = db_cursor.fetchone() # fetchone() é chamado no cursor

    if tasklist is None:
        abort(404, f"Tasklist id {id} doesn't exist.")

    if check_author and tasklist['author_id'] != g.user['id']:
        abort(403)
    
    return tasklist


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """
    Permite atualizar uma tasklist existente.
    """
    tasklist = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db_cursor = get_db() # Obtém o cursor
            db_cursor.execute(
                'UPDATE tasklist SET title = %s, body = %s' # MySQL usa %s
                ' WHERE id = %s', # MySQL usa %s
                (title, body, id)
            )
            mysql_db.connection.commit() # Commita as alterações
            return redirect(url_for('tasklist.index'))

    return render_template('task/update.html', tasklist=tasklist)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """
    Permite deletar uma tasklist.
    """
    get_post(id) # Garante que a tasklist existe e que o usuário tem permissão
    db_cursor = get_db() # Obtém o cursor
    db_cursor.execute('DELETE FROM tasklist WHERE id = %s', (id,)) # MySQL usa %s
    mysql_db.connection.commit() # Commita as alterações
    return redirect(url_for('tasklist.index'))


@bp.route('/<int:id>/')
@login_required
def detail(id):
    """
    Exibe os detalhes de uma tasklist e suas tarefas associadas.
    """
    tasklist = get_post(id)

    db_cursor = get_db() # Obtém o cursor

    db_cursor.execute( # Executa a consulta
        'SELECT id, body, completed, created '
        'FROM task WHERE tasklist_id = %s ORDER BY created ASC', # MySQL usa %s
        (id,)
    )
    tasks = db_cursor.fetchall() # Chama fetchall no cursor

    return render_template('task/detail.html', tasklist=tasklist, tasks=tasks)
