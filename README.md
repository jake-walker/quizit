# Quizit

Quizit is an **offline-first** live quiz application designed for places with no internet access. It is similar to applications like [Kahoot](https://kahoot.com/).

Quizit is designed to be run on a laptop or single board computer. Each of the players then connect from their phones to the IP address of the 'server'.

Quizit was originally made for an event in less than a week. The venue didn't have internet and we wanted to still have a 'Kahoot-like' quiz.

## Issues

This is definitely not perfect code so you should expect bugs and big issues. Some of the problems at the moment are:

- **Authentication:** Admin commands are currently unauthenticated and can be run by a normal player. The admin page also has no password.
- Lots of data is sent and stored on the client, some of this data perhaps isn't needed. More data can be processed on the server side to save on individual device processing.

## Creating a Quiz

Quizes are stored in YAML files for easy editing. Below is the format of a quiz.

* `name` is the name of the quiz and (at the moment) is only shown in the admin area.
* `questions` contains each of the questions in the quiz.
  * `type` (at the moment) can only be **choice**
  * `prompt` is the question that is shown on the player's devices.
  * `answers` is an array with possible answers to the prompt. *The number of answers doesn't have to be 4.*
  * `correct` is the **exact** value of the correct answer.
  * `score` is the **base** score value for the particular question. A time bonus (0 to 10 points) is applied which depends on how quickly the question is answered in the given time.
  * `time` is the number of seconds that players have to answer. This shouldn't be too long because (at the moment) questions cannot be skipped (i.e the full time must elapse).

```yaml
name: "Alphabet Quiz"
questions:
  - type: choice
    prompt: What is the first letter of the alphabet?
    answers: [A, B, C, D]
    correct: A
    score: 5
    time: 5
  - type: choice
    prompt: What is the third letter of the alphabet?
    answers: [A, B, C, D]
    correct: C
    score: 10
    time: 5
```

## Setting Team Names

Teams are stored in the `config.yaml` file in the root of Quizit. Players will **have** to select a team to join the quiz. If the quiz is all against all, one team can be set.

* `teams` list of teams
  * `id` is a machine friendly name for the team (anything can go here as long as it is unique)
  * `name` is the human friendly name for the team, this will be shown on player's devices

```yaml
teams:
  - id: "1"
    name: "Team 1"
  - id: "2"
    name: "Team 2"
  - id: "3"
    name: "Team 3"
```