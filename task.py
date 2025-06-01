from flask import Blueprint, request, redirect, url_for, flash, render_template, g, abort
from db import get_db
from auth import login_required



bp = Blueprint('task', __name__, url_prefix='/task')

def get_task(id, check_tasklist_author=True): 
    db = get_db()
    task = db.execute(
        """
        SELECT task.id, task.body, task.completed, task.created, task.tasklist_id, task.created, tasklist.author_id
        FROM task JOIN tasklist ON task.tasklist_id = tasklist.id
        WHERE task.id = ?
        """,
        (id,)
    ).fetchone()

    if task is None:
        abort(404, f"Task id {id} não existe.")


    if check_tasklist_author and task['author_id'] != g.user['id']:
        abort(403) 

    return task


@bp.route('/<int:tasklist_id>/create', methods=('GET', 'POST'))
@login_required
def create(tasklist_id):

    from . tasklist import get_post as get_tasklist_obj
    tasklist = get_tasklist_obj(tasklist_id)

    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            error = 'Descrição da tarefa é obrigatória.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO task (tasklist_id, body) VALUES (?, ?)',
                (tasklist_id, body)
            )
            db.commit()
            flash('Tarefa adicionada com sucesso!', 'success')

            return redirect(url_for('tasklist.detail', id=tasklist_id)) 
        
    return render_template('create.html', tasklist_id=tasklist_id)



@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):

    task = get_task(id) 

    db = get_db()
    db.execute('DELETE FROM task WHERE id = ?', (id,))
    db.commit()
    flash('Tarefa excluída com sucesso!', 'info')

    return redirect(url_for('tasklist.detail', id=task['tasklist_id']))




@bp.route('/<int:id>/toggle-complete', methods=('POST',))
@login_required
def toggle_complete(id):

    task = None 

    try:
        
        task = get_task(id)

        current_completed_status = int(task['completed']) 

        new_completed_status = 1 if current_completed_status == 0 else 0

        db = get_db()
        db.execute(
            'UPDATE task SET completed = ? WHERE id = ?',
            (new_completed_status, id)
        )
        db.commit() 

        flash(f"Status da tarefa '{task['body']}' atualizado para {'Completa' if new_completed_status == 1 else 'Pendente'}.", 'success')
        return redirect(url_for('tasklist.detail', id=task['tasklist_id']))

    except Exception as e:
        
        db = get_db()
        if db:
            db.rollback() 