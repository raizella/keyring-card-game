import flask
from flask import request, jsonify
import json
from card_game_keyring import *

game = CardGame()

app = flask.Flask(__name__)
app.config["DEBUG"] = True

#prev route no longer used
@app.route("/cg_input/<alternate_cli>", methods=["GET", "POST"])
def api_cg_start(alternate_cli):
    text_output = game.move(alternate_cli)
    return jsonify(text_output)


@app.route("/home", methods=["GET"])
def home():
    text_output = 'Do you want to play a game?\n <a href="/opponentSelection"> Yes </a>'
    # todo consider adding no
    return text_output


@app.route("/opponentSelection", methods=["GET"])
def opponentSelection():
    text_output = (
        'Do you want an <a href="/start_cg/A"> aggressive (A) </a> opponent or an <a href="/start_cg/Q"> acquisative (Q) opponent?'
    )
    # todo add links
    return text_output


@app.route("/start_cg/<opponent_selection>", methods=["GET", "POST"])
def start_cg(opponent_selection):
    if opponent_selection == "A":
        text_output = game.start(True)
    elif opponent_selection == "Q":
        text_output = game.start(False)
    else:
        text_output = "Invalid opponent option, defaulting to acquisative"
        text_output += game.start(False)
    return text_output


@app.route("/main_turn/<move>", methods=["GET", "POST"])
def main_turn(move):
    # todo check if valid move
    # todo verify game has started already
    return game.playerMoveMainTurn(move)


@app.route("/buy_screen/<move>", methods=["GET", "POST"])
def buy_screen(move):
    # todo check if valid move
    # todo verify game has started already
    # should probably also verify that currently in buy screen but that's lower pri
    return game.playerOneMoveBuyScreen(move)


def main():
    app.run()


if __name__ == "__main__":
    main()
