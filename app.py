# app.py
from flask import Flask, jsonify
import aiosqlite
import asyncio

app = Flask(__name__)


@app.route("/")
def index():
    return app.send_static_file('index.html')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run(debug=True))
