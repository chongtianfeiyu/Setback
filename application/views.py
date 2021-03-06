"""
To do:
- Switch to websockets
  -Miguel Greenberg's FlaskSocketIO?
    -Won't work on Dreamhost apparantly?
- Switch all hacky json lists to tables
"""

import os

from random import shuffle
from flask import Flask, render_template, request, redirect, url_for
from flask import session, has_request_context, jsonify
from flask.ext.login import LoginManager, login_required, login_user
from flask.ext.login import current_user, logout_user, AnonymousUserMixin
from werkzeug.local import LocalProxy

from Game import Game
from User import User, GamePlayers
from GameView import GameView
from config import DIRECTORY, SECRET_KEY, db_session, hashulate, init_db
from forms import LoginForm

app = Flask(__name__)
app.secret_key = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

game_view = LocalProxy(lambda:get_game_view())

def get_game_view():
    """Loads the GameView object for each response."""
    if has_request_context() and current_user.is_authenticated():
        if request.args.get('game'):
            session['current_game'] = request.args.get('game')
        if session.get('current_game', False):
            return current_user.view(Game.get(session['current_game']))
    return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in or creates a new user in the database."""
    form = LoginForm(request.form)
    validates = request.method == 'POST' and form.validate()
    if validates:
        username = request.form.get('username')
        password = request.form.get('password')
        if not User.username_taken(username):
            user = User(username=username, password=hashulate(password))
            db_session.add(user)
            db_session.commit()
            login_user(user)
            return redirect(request.args.get("next") or url_for("home"))
        elif User.check_password(User.id_from_name(username), 
                                 request.form.get('password')):
            login_user(User(id=User.id_from_name(username)))
            return redirect(request.args.get("next") or url_for("home"))
    return render_template('login.html', form=form)


@app.route('/')
@login_required
def home():
    """Serves up the setback client-side application."""
    return render_template('dashboard.html', user=current_user)


@app.route('/game', methods=['GET', 'POST'])
@login_required
def games():
    """API inpoint for Games collection. GET requests return the user's game
       collection. POST creates a new game."""
    if request.method == 'POST':
        game = Game()
        player1 = int(request.form.get('player1'))
        player2 = int(request.form.get('player2'))
        player3 = int(request.form.get('player3'))
        player4 = int(request.form.get('player4'))
        User.get(player1).join_game(game, 0)
        User.get(player2).join_game(game, 1)
        User.get(player3).join_game(game, 2)
        User.get(player4).join_game(game, 3)
        db_session.flush()
        game.deal()
        db_session.commit()
        session['current_game'] = game.id
    return jsonify(current_user.current_games())


@app.route('/game/<int:game_id>', methods=['POST', 'GET'])
@login_required
def game(game_id):
    """API inpoint for Game objects. GET returns the JSON representation of the
       object for the client. POST lets the user play a card."""
    session['current_game'] = game_id
    if request.method == 'GET':
        time = float(request.args.get('timestamp'))
        return jsonify(game_view.view()) if not game_view.is_fresh(time) else 'null'
    elif request.method == 'POST':
        bid = request.form.get('bid')
        card = request.form.get('card')
        trump = request.form.get('trump')
        if bid:
            game_view.bid(int(bid))
        elif card:
            game_view.play_card(card)
        elif trump:
            game_view.set_trump(trump)
        db_session.commit()
        return jsonify(game_view.view())


@app.route('/user')
@login_required
def get_users():
    """API inpoint that returns a JSON encoded object where the keys are User id
       numbers and the values are usernames."""
    return jsonify(User.get_users())


@app.route('/user/<int:user_id>')
@login_required
def name_from_id(user_id):
    """API inpoint that returns the User's information if querying themself,
       else returns the User's username."""
    if current_user.id == user_id:
        return jsonify(current_user.model())
    return User.get(user_id).username


@app.route('/logout')
@login_required
def logout():
    """Logs the user out."""
    logout_user()
    return redirect(url_for('login'))


@app.before_first_request
def setup():
    """Initializes the sqlite3 database used in development."""
    if not os.path.isfile(os.path.join(DIRECTORY, 'test.db')):
        init_db()


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
