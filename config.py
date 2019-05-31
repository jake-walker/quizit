import yaml

def load():
  file = open("config.yaml", "r")
  data = yaml.load(file, Loader=yaml.FullLoader)
  return data