from flask import Flask, render_template
import database as db


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


def main():
    db.init(app, 'benford.db')
    app.run()


if __name__ == '__main__':
    main()
