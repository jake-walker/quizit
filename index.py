from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit
import json
import quiz
from urllib.parse import parse_qs
import time
import config as cfg

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

players = []

current_quiz = None

config = cfg.load()

@app.route("/")
def player():
  return render_template("player.html.j2", config=config)

@app.route("/admin")
def admin():
  quizzes = quiz.available_quizzes()
  return render_template("admin.html.j2", quizzes=quizzes)

@socketio.on("connect")
def player_connect():
  q = parse_qs(request.query_string)
  q = {key.decode("utf-8"): value[0].decode("utf-8") for (key, value) in q.items()}
  admin = False
  if "token" in q:
    if (q["token"] == "testing123"):
      join_room("admin")
      admin = True
  else:
    players.append(request.sid)
    if (current_quiz != None):
      broadcast_next_question(current_quiz.current_question(), broadcast=False)
  print("=== {} {} connected! ===".format("Admin" if admin else "Player", request.sid))
  status_update()

@socketio.on("disconnect")
def player_disconnect():
  if request.sid in players:
    players.remove(request.sid)
  print("Player disconnected!")
  status_update()

@socketio.on("admin_command")
def admin_command_event(json):
  global current_quiz
  if (json["action"] == "load_quiz"):
    if ("filename" in json):
      print("Loading quiz {}...".format(json["filename"]))
      current_quiz = quiz.Quiz(json["filename"])
      print("Loaded {}!".format(current_quiz.data["name"]))
    else:
      print("Unloading quiz {}...".format(current_quiz.data["name"]))
      current_quiz = None
      print("Unloaded quiz!")
  elif (json["action"] == "next_question"):
    q = current_quiz.next_question()
    print("Next question " + str(q))
    if (q != "finish"):
      broadcast_next_question(q)
  elif (json["action"] == "start_question"):
    broadcast_start_question()
  status_update()
  print("Received command " + str(json))

def broadcast_next_question(question, broadcast=True):
  if isinstance(question, dict):
    emit("next_question", {
      "prompt": question["prompt"],
      "type": question["type"],
      "answers": question["answers"]
    }, broadcast=broadcast)

def broadcast_start_question(start_time=5, answer_time=20):
  emit("start_question", {
    "start_time": start_time,
    "answer_time": answer_time
  }, broadcast=True)

def status_update():
  global current_quiz
  global players
  msg = {
    "quiz": (current_quiz.data if current_quiz != None else False),
    "quiz_path": (current_quiz.file if current_quiz != None else False),
    "question": (current_quiz.current_question() if current_quiz != None else False),
    "question_position": ((current_quiz._current + 1) if current_quiz != None else False),
    "players": players
  }
  print("Sending status update " + str(msg))
  emit("admin_status", msg, room="admin")

if __name__ == "__main__":
  socketio.run(app, debug=True, host="0.0.0.0")