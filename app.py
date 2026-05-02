from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
DATABASE = os.path.join(os.path.dirname(__file__), "oni.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS builds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            materials TEXT,
            priority TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'planned',
            screenshot TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS seeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed TEXT NOT NULL,
            name TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# --- Phases ---

@app.route("/api/phases", methods=["GET"])
def get_phases():
    conn = get_db()
    phases = conn.execute("SELECT * FROM phases ORDER BY sort_order, id").fetchall()
    result = []
    for phase in phases:
        builds = conn.execute(
            "SELECT * FROM builds WHERE phase_id = ? ORDER BY sort_order, id",
            (phase["id"],),
        ).fetchall()
        p = dict(phase)
        p["builds"] = [dict(b) for b in builds]
        result.append(p)
    conn.close()
    return jsonify(result)


@app.route("/api/phases", methods=["POST"])
def create_phase():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    description = data.get("description", "").strip()
    conn = get_db()
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM phases").fetchone()[0]
    cur = conn.execute(
        "INSERT INTO phases (name, description, sort_order) VALUES (?, ?, ?)",
        (name, description, max_order),
    )
    conn.commit()
    phase = conn.execute("SELECT * FROM phases WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    p = dict(phase)
    p["builds"] = []
    return jsonify(p), 201


@app.route("/api/phases/<int:phase_id>", methods=["PUT"])
def update_phase(phase_id):
    data = request.get_json()
    conn = get_db()
    conn.execute(
        "UPDATE phases SET name = ?, description = ? WHERE id = ?",
        (data.get("name", "").strip(), data.get("description", "").strip(), phase_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/phases/<int:phase_id>", methods=["DELETE"])
def delete_phase(phase_id):
    conn = get_db()
    conn.execute("DELETE FROM phases WHERE id = ?", (phase_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# --- Builds ---

@app.route("/api/phases/<int:phase_id>/builds", methods=["POST"])
def create_build(phase_id):
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    conn = get_db()
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM builds WHERE phase_id = ?",
        (phase_id,),
    ).fetchone()[0]
    cur = conn.execute(
        "INSERT INTO builds (phase_id, name, description, materials, priority, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
        (
            phase_id,
            name,
            data.get("description", "").strip(),
            data.get("materials", "").strip(),
            data.get("priority", "normal"),
            max_order,
        ),
    )
    conn.commit()
    build = conn.execute("SELECT * FROM builds WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(build)), 201


@app.route("/api/builds/<int:build_id>", methods=["PUT"])
def update_build(build_id):
    data = request.get_json()
    conn = get_db()
    conn.execute(
        """UPDATE builds SET name = ?, description = ?, materials = ?,
           priority = ?, status = ? WHERE id = ?""",
        (
            data.get("name", "").strip(),
            data.get("description", "").strip(),
            data.get("materials", "").strip(),
            data.get("priority", "normal"),
            data.get("status", "planned"),
            build_id,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/builds/<int:build_id>", methods=["DELETE"])
def delete_build(build_id):
    conn = get_db()
    conn.execute("DELETE FROM builds WHERE id = ?", (build_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# --- Seeds ---

@app.route("/api/seeds", methods=["GET"])
def get_seeds():
    conn = get_db()
    seeds = conn.execute("SELECT * FROM seeds ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(s) for s in seeds])


@app.route("/api/seeds", methods=["POST"])
def create_seed():
    data = request.get_json()
    seed = data.get("seed", "").strip()
    if not seed:
        return jsonify({"error": "Seed is required"}), 400
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO seeds (seed, name, notes) VALUES (?, ?, ?)",
        (seed, data.get("name", "").strip(), data.get("notes", "").strip()),
    )
    conn.commit()
    s = conn.execute("SELECT * FROM seeds WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(s)), 201


@app.route("/api/seeds/<int:seed_id>", methods=["DELETE"])
def delete_seed(seed_id):
    conn = get_db()
    conn.execute("DELETE FROM seeds WHERE id = ?", (seed_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# --- Screenshots ---

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


@app.route("/api/screenshots", methods=["GET"])
def list_screenshots():
    files = []
    if os.path.exists(SCREENSHOTS_DIR):
        for f in sorted(os.listdir(SCREENSHOTS_DIR)):
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                files.append(f)
    return jsonify(files)


@app.route("/screenshots/<path:filename>")
def serve_screenshot(filename):
    return send_from_directory(SCREENSHOTS_DIR, filename)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
