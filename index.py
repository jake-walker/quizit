from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit
import json
import quiz
from urllib.parse import parse_qs
import time
import config as cfg
import math

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
  return render_template("admin.html.j2", quizzes=quizzes, config=config)

@socketio.on("connect")
def player_connect():
  global players
  q = parse_qs(request.query_string)
  q = {key.decode("utf-8"): value[0].decode("utf-8") for (key, value) in q.items()}
  admin = False
  if "token" in q:
    if (q["token"] == "testing123"):
      join_room("admin")
      admin = True
  else:
    players.append({
      "id": request.sid,
      "active": True,
      "name": "",
      "team": "",
      "ready": False,
      "guid": "",
      "score": 0
    })
    if (current_quiz != None):
      broadcast_next_question(current_quiz.current_question(), broadcast=False)
  print("=== {} {} connected! ===".format("Admin" if admin else "Player", request.sid))
  status_update()

@socketio.on("disconnect")
def player_disconnect():
  global players
  player_index = next((i for (i, x) in enumerate(players) if x["id"] == request.sid), None)
  if (player_index != None):
    players[player_index]["active"] = False
  print("Player disconnected!")
  status_update()

# TODO: Make sure that this only accepts messages from admins.
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
    q = current_quiz.current_question()
    print(q)
    broadcast_start_question(answer_time=q["time"])
  elif (json["action"] == "show_feedback"):
    emit("answer_feedback", {
      "show": True
    }, broadcast=True)
  status_update()
  print("Received command " + str(json))

@socketio.on("player_command")
def player_command_event(json):
  global current_quiz
  global players
  if (json["action"] == "ready"):
    player_index = next((i for (i, x) in enumerate(players) if x["id"] == request.sid), None)
    if (player_index != None):
      players[player_index]["name"] = json["name"]
      players[player_index]["team"] = json["team"]
      players[player_index]["ready"] = json["ready"]
      players[player_index]["guid"] = json["guid"]
      players[player_index]["active"] = True
    # Send a status update to the admin dashboard
    status_update()
  # This 'recovers' a game session (e.g if a user disconnects)
  elif (json["action"] == "fetch"):
    # Get the player with the same GUID
    player_index = next((i for (i, x) in enumerate(players) if x["guid"] == json["guid"]), None)
    # If we could find a player with the same GUID
    if (player_index != None):
      # Get the 'old' player object
      old_player_index = next((i for (i, x) in enumerate(players) if x["id"] == request.sid), None)
      # Delete the object
      if (old_player_index != None):
        del players[old_player_index]
      # Update the player's ID to the current socket ID
      players[player_index]["id"] = request.sid
      # Send all the details to update client
      emit("set_player", players[player_index])
  elif (json["action"] == "answer"):
    print(str(request.sid) + " answered " + str(json["answer"]) + " in " + str(json["answerTime"]) + "seconds")
    score = 0
    q = current_quiz.current_question()
    if (json["answer"] == q["correct"]):
      # Base score
      score += q["score"]
      # Time score
      time_score = math.ceil((int(json["answerTime"]) / q["time"]) * 10)
      score += time_score

      player_index = next((i for (i, x) in enumerate(players) if x["id"] == request.sid), None)
      players[player_index]["score"] += score

      emit("answer_feedback", {
        "correct": True,
        "score": score
      })
    else:
      emit("answer_feedback", {
        "correct": False,
        "score": 0
      })
  elif (json["action"] == "leaderboard"):
    # TODO: Only send points, position and person/team infront and behind.
    player = player_leaderboard()
    team = team_leaderboard()
    emit("leaderboard", {
      "player": player,
      "team": team
    })
  else:
    print(json["action"], json)

def player_leaderboard():
  global players

  temp = []

  for player in players:
    if (player["active"] and player["ready"]):
      temp.append(player)

  return sorted(temp, key=lambda p: p["score"], reverse=True)

def team_leaderboard():
  global players
  leaderboard = {}
  for player in players:
    if (player["active"] and player["ready"]):
      if (player["team"] in leaderboard):
        leaderboard[player["team"]] += player["score"]
      else:
        leaderboard[player["team"]] = player["score"]
  
  output = []

  for key, value in leaderboard.items():
    output.append({
      "team": key,
      "score": value
    })
  
  return sorted(output, key=lambda t: t["score"], reverse=True)

def broadcast_next_question(question, broadcast=True):
  if isinstance(question, dict):
    emit("next_question", {
      "prompt": question["prompt"],
      "type": question["type"],
      "answers": question["answers"]
    }, broadcast=broadcast)

def broadcast_start_question(start_time=5, answer_time=20):
  print("Starting question with " + str(start_time) + " seconds prep and " + str(answer_time) + " seconds answering time.")
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