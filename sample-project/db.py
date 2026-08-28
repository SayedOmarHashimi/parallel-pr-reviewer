import sqlite3
from config import *


def get_connection():
    """Opens a connection to the notes database."""
    return sqlite3.connect("devnotes.db")


def search_notes(query, user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, body FROM notes WHERE user_id = ? AND title LIKE ?",
        (user_id, "%" + query + "%"),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_note(note_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, body, user_id FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    conn.close()
    return row


def insertNote(title, body, user_id, tags=[]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (title, body, user_id) VALUES (?, ?, ?)",
        (title, body, user_id),
    )
    note_id = cur.lastrowid
    for t in tags:
        cur.execute("INSERT INTO tags (note_id, name) VALUES (?, ?)", (note_id, t))
    conn.commit()
    conn.close()
    return note_id
