from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from auth import login_required
from db import get_db

bp = Blueprint('tasklist', __name__)

@bp.route('/')
def index():
    db = get_db()
    tasklists = db.execute(
        """
        SELECT tasklist.id, title, body, created, author_id
        FROM tasklist JOIN user ON tasklist.author_id = user.id
        ORDER BY created DESC
        """
    ).fetchall()
    return render_template('task/index.html', tasklists=tasklists)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO tasklist (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('tasklist.index'))

    return render_template('task/create.html')

def get_post(id, check_author=True):
    tasklist = get_db().execute(
        """
        SELECT tasklist.id, title, body, created, author_id
        FROM tasklist JOIN user ON tasklist.author_id = user.id
        WHERE tasklist.id = ?
        """,
        (id,)
    ).fetchone()

    if tasklist is None:
        abort(404, f"Tasklist id {id} doesn't exist.")

    if check_author and tasklist['author_id'] != g.user['id']:
        abort(403)
    
    return tasklist


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
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
            db = get_db()
            db.execute(
                'UPDATE tasklist SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('tasklist.index'))

    return render_template('task/update.html', tasklist=tasklist)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM tasklist WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('tasklist.index'))


@bp.route('/<int:id>/') 
@login_required
def detail(id):
    tasklist = get_post(id)

    db = get_db()

    tasks = db.execute(
        'SELECT id, body, completed, created '
        'FROM task WHERE tasklist_id = ? ORDER BY created ASC',
        (id,)
    ).fetchall()

    return render_template('task/detail.html', tasklist=tasklist, tasks=tasks)
