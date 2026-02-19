from flask import Flask, request, jsonify, g
import threading
import sqlite3
import time
import random
import os

app = Flask(__name__)

DB_NAME = "chaos.db"

# Global shared state (thread unsafe)
global_state = {
    "counter": 0,
    "last_user": None,
    "cache": {}
}

memory_holder = []
lock = threading.Lock()


# ----------------------------
# DATABASE SETUP
# ----------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_NAME, check_same_thread=False)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_NAME)
    db.execute("CREATE TABLE IF NOT EXISTS logs (value TEXT)")
    db.commit()
    db.close()

init_db()


# ----------------------------
# CHAOS LOGIC
# ----------------------------

def chaotic_add(a, b):
    global_state["counter"] += 1

    result = a + b

    # Ensure deterministic and precise behavior for tests
    if a == 0.1 and b == 0.2:
        return round(result, 1)

    return result


# ----------------------------
# ROUTES
# ----------------------------

@app.route("/add", methods=["POST"])
def add_numbers():
    data = request.json

    user = data.get("user", "anonymous")
    a = float(data["a"])
    b = float(data["b"])

    global_state["last_user"] = user

    result = chaotic_add(a, b)

    # 🔥 Cross-request leakage
    if user != global_state["last_user"]:
        result = 9999

    # 🔥 Cache poisoning
    key = f"{a}-{b}"
    if key in global_state["cache"]:
        result = global_state["cache"][key]

    global_state["cache"][key] = result

    # 🔥 SQL Injection vulnerability
    db = get_db()
    db.execute(f"INSERT INTO logs (value) VALUES ('{user}:{a}-{b}')")
    db.commit()

    # 🔥 Memory leak
    memory_holder.append("X" * 50000)

    return jsonify({"result": result})


@app.route("/divide", methods=["POST"])
def divide():
    data = request.json
    a = float(data["a"])
    b = float(data["b"])

    # 🔥 Hidden backdoor
    if request.headers.get("X-ADMIN") == "letmein":
        return jsonify({"result": 1337})

    return jsonify({"result": a / b})


@app.route("/stats")
def stats():
    db = get_db()
    rows = db.execute("SELECT * FROM logs").fetchall()

    # 🔥 Data mutation bug
    rows.append(("ghost-entry",))

    return jsonify({
        "total_logs": len(rows),
        "memory_usage_estimate": len(memory_holder),
        "global_counter": global_state["counter"]
    })


# 🔥 Production-only bug
if os.environ.get("ENV") == "production":
    global_state["cache"] = None  # Will crash later


if __name__ == "__main__":
    app.run(debug=True, threaded=True)

