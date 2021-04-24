import flask
from flask import jsonify, request

from . import db_session
from .products import Products

blueprint = flask.Blueprint(
    'products_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/products')
def get_products():
    db_sess = db_session.create_session()
    products = db_sess.query(Products).all()
    return jsonify(
        {
            'products':
                [item.to_dict(only=('title', 'content', 'price', 'user.name'))
                 for item in products]
        }
    )


@blueprint.route('/api/products/<int:products_id>', methods=['GET'])
def get_one_products(products_id):
    db_sess = db_session.create_session()
    products = db_sess.query(Products).get(products_id)
    if not products:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'products': products.to_dict(only=(
                'title', 'content', 'price', 'user_id'))
        }
    )


@blueprint.route('/api/products', methods=['POST'])
def create_products():
    if not request.json:
        return jsonify({'error': 'Empty request'})
    elif not all(key in request.json for key in
                 ['title', 'content', 'price', 'user_id']):
        return jsonify({'error': 'Bad request'})
    db_sess = db_session.create_session()
    products = Products(
        title=request.json['title'],
        content=request.json['content'],
        price=request.json['price'],
        user_id=request.json['user_id']
    )
    db_sess.add(products)
    db_sess.commit()
    return jsonify({'success': 'OK'})


@blueprint.route('/api/products/<int:products_id>', methods=['DELETE'])
def delete_products(products_id):
    db_sess = db_session.create_session()
    products = db_sess.query(Products).get(products_id)
    if not products:
        return jsonify({'error': 'Not found'})
    db_sess.delete(products)
    db_sess.commit()
    return jsonify({'success': 'OK'})
