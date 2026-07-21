from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor OK"

print("Antes do app.run()")

app.run(host="127.0.0.1", port=5000, debug=False)

print("Depois do app.run()")