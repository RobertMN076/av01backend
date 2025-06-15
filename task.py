from flask import Blueprint, request, redirect, url_for, flash, render_template, g, abort
# Ajusta as importações para serem relativas ao pacote
from db import get_db, mysql_db # Importa também o objeto mysql_db para o commit
from auth import login_required

bp = Blueprint('task', __name__, url_prefix='/task')

def get_task(id, check_tasklist_author=True):
    """
    Obtém uma tarefa do banco de dados pelo ID, opcionalmente verificando o autor da tasklist pai.
    """
    db_cursor = get_db() # Obtém o cursor
    db_cursor.execute( # Executa a consulta no cursor
        """
        SELECT task.id, task.body, task.completed, task.created, task.tasklist_id, tasklist.author_id
        FROM task JOIN tasklist ON task.tasklist_id = tasklist.id
        WHERE task.id = %s
        """, # Use %s para MySQL
        (id,)
    )
    task = db_cursor.fetchone() # fetchone() é chamado no cursor

    if task is None:
        abort(404, f"Task id {id} não existe.")

    if check_tasklist_author and task['author_id'] != g.user['id']:
        abort(403)

    return task


@bp.route('/<int:tasklist_id>/create', methods=('GET', 'POST'))
@login_required
def create(tasklist_id):
    """
    Permite criar uma nova tarefa para uma tasklist específica.
    """
    # Importa get_post do módulo tasklist para obter o objeto tasklist pai
    from .tasklist import get_post as get_tasklist_obj
    tasklist = get_tasklist_obj(tasklist_id) # Garante que a tasklist existe e o usuário tem acesso

    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            error = 'Descrição da tarefa é obrigatória.'

        if error is not None:
            flash(error)
        else:
            db_cursor = get_db() # Obtém o cursor
            db_cursor.execute( # Executa a inserção no cursor
                'INSERT INTO task (tasklist_id, body) VALUES (%s, %s)', # Use %s para MySQL
                (tasklist_id, body)
            )
            mysql_db.connection.commit() # Commita as alterações
            flash('Tarefa adicionada com sucesso!', 'success')

            return redirect(url_for('tasklist.detail', id=tasklist_id))

    return render_template('create.html', tasklist_id=tasklist_id)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """
    Permite deletar uma tarefa.
    """
    task = get_task(id) # Garante que a tarefa existe e o usuário tem permissão para deletá-la

    db_cursor = get_db() # Obtém o cursor
    db_cursor.execute('DELETE FROM task WHERE id = %s', (id,)) # Use %s para MySQL
    mysql_db.connection.commit() # Commita as alterações
    flash('Tarefa excluída com sucesso!', 'info')

    return redirect(url_for('tasklist.detail', id=task['tasklist_id']))


@bp.route('/<int:id>/toggle-complete', methods=('POST',))
@login_required
def toggle_complete(id):
    """
    Alterna o status de conclusão de uma tarefa.
    """
    task = None

    try:
        task = get_task(id) # Obtém a tarefa e verifica permissões

        # O campo 'completed' no MySQLdb com DictCursor pode vir como int diretamente
        # ou, dependendo da configuração da coluna, como bool ou bytes.
        # Converter para int para garantir a lógica de alternância.
        current_completed_status = int(task['completed'])

        new_completed_status = 1 if current_completed_status == 0 else 0

        db_cursor = get_db() # Obtém o cursor
        db_cursor.execute( # Executa a atualização no cursor
            'UPDATE task SET completed = %s WHERE id = %s', # Use %s para MySQL
            (new_completed_status, id)
        )
        mysql_db.connection.commit() # Commita as alterações

        flash(f"Status da tarefa '{task['body']}' atualizado para {'Completa' if new_completed_status == 1 else 'Pendente'}.", 'success')
        return redirect(url_for('tasklist.detail', id=task['tasklist_id']))

    except Exception as e:
        # Em caso de erro, tenta fazer o rollback da conexão
        flash(f"Ocorreu um erro ao atualizar o status da tarefa: {e}", 'error')
        db_cursor = g.pop('db_cursor', None) # Tenta pegar o cursor do g
        if db_cursor and mysql_db.connection: # Verifica se o cursor e a conexão existem
            mysql_db.connection.rollback() # Faz rollback da conexão


    # Se ocorrer um erro e não houver um redirecionamento, garante que o usuário seja levado de volta
    # para a página da tasklist, para evitar que a requisição fique "pendurada".
    # Isso é especialmente importante em um bloco try-except que pode não ter um 'return'.
    if task:
        return redirect(url_for('tasklist.detail', id=task['tasklist_id']))
    else:
        # Se 'task' for None (ex: get_task falhou com 404 antes do try/except),
        # redireciona para um local seguro, como a página principal ou login.
        return redirect(url_for('index')) # ou url_for('auth.login') dependendo da lógica do app

