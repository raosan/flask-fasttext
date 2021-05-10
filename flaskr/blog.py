import json
import fasttext
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, Response
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT id, title, body'
        ' FROM post'
    ).fetchall()

    return render_template('blog/index.html', posts=posts)

@bp.route('/vectors')
def vectors():
    db = get_db()
    posts = db.execute(
        'SELECT id, title, body, vector'
        ' FROM post'
    ).fetchall()

    data = []
    columns = ['id', 'title', 'body', 'vector']

    for post in posts:
        data.append(dict(zip(columns, post)))
    
    for item in data:
        item['vector'] = list(map(lambda x: float(x), item['vector'].split()))

    # function to get sentence vector
    # for item in data:
        # item['wordToVec'] = item['title'] + ' ' + item['body']
       
        # # fastText 
        # model = fasttext.load_model("cc.id.300.bin")
        # vector = model.get_sentence_vector(item['wordToVec'])
        # item['vector'] = vector.tolist()

        # # insert vector to db 
        # listToStr = ' '.join(map(str, vector.tolist()))
        # db.execute(
        #     'UPDATE post SET vector = ?'
        #     ' WHERE id = ?',
        #     (listToStr, item['id'])
        # )
        # db.commit()
  
    return Response(json.dumps(data),  mimetype='application/json')


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
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>')
def get_imilarity(id):
    db = get_db()
    post = db.execute(
        'SELECT id, title, body, vector' 
        ' FROM post'
        ' WHERE id = ?',
        (id,)
    ).fetchone()

    column = ['id', 'title', 'body', 'vector', 'similar_courses']  #To get column names
    data = dict(zip(column, post))
    data['vector'] = list(map(lambda x: float(x), data['vector'].split()))

    posts = db.execute(
        'SELECT id, title, body, vector'
        ' FROM post'
        ' WHERE id != ?',
        (id,)
    ).fetchall()
    
    all = []
    columns = ['id', 'title', 'body', 'vector']

    for p in posts:
        all.append(dict(zip(columns, p)))

    for item in all:
        item['vector'] = list(map(lambda x: float(x), item['vector'].split()))

    data['similar_courses'] = all

    get_similarity(data, all)

    return Response(json.dumps(data),  mimetype='application/json')


def get_similarity(data, all):
    # for item in 
    print('hello')    


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

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
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))