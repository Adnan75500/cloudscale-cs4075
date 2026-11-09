
from flask import Flask

app = Flask(__name__)

@app.get("/health")
def health():
    return "ok"

@app.get("/burn")
def burn():
    # Deliberate CPU work, used only for the scaling demo
    return str(sum(i * i for i in range(2_000_000)))

@app.get("/")
def home():
    return "CloudScale is alive"
