"""
Quiz specific code
"""

import glob
import yaml

def available_quizzes():
  output = []
  for quiz in glob.glob("quizzes/*.yaml"):
    file = open(quiz, "r")
    data = yaml.load(file)
    output.append({
      "data": data,
      "file": quiz
    })
  return output

class Quiz():
  def __init__(self, quiz_path):
    try:
      file = open(quiz_path, "r")
    except FileNotFoundError:
      print("File not found!")
      return
    
    self.file = quiz_path
    self.data = yaml.load(file)
    self._current = -1
  
  def next_question(self):
    questions = len(self.data["questions"]) - 1
    if self._current < questions:
      self._current += 1
    else:
      self._current = -2
      return "finish"
    return self.data["questions"][self._current]
  
  def current_question(self):
    if self._current == -1:
      return "start"
    elif self._current == -2:
      return "finish"
    else:
      return self.data["questions"][self._current]