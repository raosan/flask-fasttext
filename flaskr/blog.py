import json
import fasttext
import math
import numpy as np
import os
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
            # function to get sentence vector
            wordToVec = title + ' ' + body
            formattedString = wordToVec.replace("\r\n", "")
            print(formattedString)
        
            # fastText 
            model = fasttext.load_model("cc.id.300.bin")
            vector = model.get_sentence_vector(formattedString)
            vectorList = vector.tolist()

            # insert vector to db 
            listToStr = ' '.join(map(str, vector.tolist()))

            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id, vector)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], listToStr)
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
def get_courses_similarity(id):
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
        item['cosine_val']  = cosine(data['vector'], item['vector'])
        item['vector'] = ''

    all.sort(key=get_my_key, reverse=True)
    data['similar_courses'] = all
    data['vector'] = ''

    return Response(json.dumps(data),  mimetype='application/json')

def get_my_key(obj):
  return obj['cosine_val']

def cosine(array1, array2):
    a = 0
    i = 0
    while i < len(array1):
        a = a + (array1[i] * array2[i])
        i += 1

    b = 0
    c = 0
    j = 0
    while j < len(array1):
        b = b + (array1[j] ** 2)
        c = c + (array2[j] ** 2)
        j += 1
    
    answer = a / (math.sqrt(b) * math.sqrt(c))

    return answer


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