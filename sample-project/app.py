from flask import Flask, request, jsonify
import traceback

from config import DEBUG, PAGE_SIZE, MAX_NOTE_LENGTH
from db import search_notes, get_note, insertNote, delete_note
from auth import current_user_id, isAdmin, hash_password, verify_password
from utils import slugify, truncate, parse_tags, applyFilterExpression

app = Flask(__name__)


@app.route("/notes/search")
def search():
    q = request.args.get("q", "")
    uid = current_user_id(request.headers.get("Authorization"))
    results = search_notes(q, uid)
    return jsonify([{"id": r[0], "title": r[1], "excerpt": truncate(r[2])} for r in results[:PAGE_SIZE]])


@app.route("/notes/<int:note_id>")
def read_note(note_id):
    row = get_note(note_id)
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": row[0], "title": row[1], "body": row[2], "slug": slugify(row[1])})


@app.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json()
    uid = current_user_id(request.headers.get("Authorization"))
    if len(data["body"]) > MAX_NOTE_LENGTH:
        return jsonify({"error": "too long"}), 400
    note_id = insertNote(data["title"], data["body"], uid, parse_tags(data.get("tags", "")))
    return jsonify({"id": note_id}), 201


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def remove_note(note_id):
    if not isAdmin(request.headers):
        return jsonify({"error": "forbidden"}), 403
    delete_note(note_id)
    return "", 204


@app.route("/notes/filter", methods=["POST"])
def filter_notes():
    body = request.get_json()
    uid = current_user_id(request.headers.get("Authorization"))
    notes = search_notes("", uid)
    try:
        return jsonify(applyFilterExpression(notes, body["expression"]))
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    return jsonify({"password_hash": hash_password(data["password"])}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
