import flask
from flask import Flask
from price_updater import updater
import sqlite3

app = Flask(__name__)


# НЕ ЗАБЫТЬ УДАЛИТЬ ОБЪЕКТЫ, У КОТОРЫХ НЕТ ОПИСАНИЯ

@app.route('/api/v1/getall/<string:cat_name>')
def getall(cat_name):
    conn = sqlite3.connect('test_items.db')
    cur = conn.cursor()
    cur.execute(f"select * from {cat_name}")
    r = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return flask.jsonify({'items': r})



@app.route('/api/v1/getone/<string:cat_name>/<string:tag>')
def getone(cat_name, tag):
    conn = sqlite3.connect('test_items.db')
    cur = conn.cursor()
    cur.execute(f"select * from {cat_name} where tag=?", (tag,))
    r = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return flask.jsonify({'item': r})


@app.route('/api/v1/update_price/<string:cat_name>/<string:tag>')
def update_price(cat_name, tag):
    conn = sqlite3.connect('test_items.db')
    cur = conn.cursor()
    cur.execute(f"select * from {cat_name} where tag=?", (tag,))
    shops = cur.fetchone()
    new_shops = updater(shops[2])
    cur.execute(f'update {cat_name} set shops=? where tag=?', (new_shops,shops[0]))
    return flask.jsonify({'items': 'some_item'})


if __name__ == '__main__':
    app.run(debug=True)