from flask import Flask, render_template, request, redirect, url_for, Response
import pickle
import sqlite3
import csv
import io
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "history.db"

with open(BASE_DIR / "model.pkl", "rb") as file:
    model = pickle.load(file)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                result TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)


init_db()


@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    message = ""

    if request.method == "POST":
        message = request.form.get("message", "").strip()

        if message:
            result = str(model.predict([message])[0])

            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO history (message, result, timestamp) VALUES (?, ?, ?)",
                    (
                        message,
                        result,
                        datetime.now().strftime("%d-%m-%Y %I:%M %p")
                    )
                )
        else:
            result = "Please enter a message"

    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM history"
        ).fetchone()[0]

        spam_count = conn.execute(
            "SELECT COUNT(*) FROM history WHERE LOWER(result) = 'spam'"
        ).fetchone()[0]

        safe_count = conn.execute(
            """SELECT COUNT(*) FROM history
               WHERE LOWER(result) IN ('not spam', 'ham', 'safe')"""
        ).fetchone()[0]

        recent = conn.execute(
            """SELECT message, result, timestamp
               FROM history ORDER BY id DESC LIMIT 5"""
        ).fetchall()

    return render_template(
    "index.html",
    result=result,
    message=message,
    total=total,
    spam_count=spam_count,
    safe_count=safe_count,
    recent=recent,
    chart_spam=spam_count,
    chart_safe=safe_count
)


@app.route("/history")
def history():
    search = request.args.get("search", "").strip()
    filter_by = request.args.get("filter", "all")

    query = """
        SELECT id, message, result, timestamp
        FROM history
        WHERE message LIKE ?
    """
    params = [f"%{search}%"]

    if filter_by == "spam":
        query += " AND LOWER(result) = 'spam'"
    elif filter_by == "safe":
        query += " AND LOWER(result) IN ('not spam', 'ham', 'safe')"

    query += " ORDER BY id DESC"

    with sqlite3.connect(DB_PATH) as conn:
        records = conn.execute(query, params).fetchall()
    return render_template(
    "index.html",
    result=result,
    message=message,
    total=total,
    spam_count=spam_count,
    safe_count=safe_count,
    recent=recent,
    chart_spam=spam_count,
    chart_safe=safe_count
)



@app.route("/download-report")
def download_report():
    with sqlite3.connect(DB_PATH) as conn:
        records = conn.execute(
            """SELECT id, message, result, timestamp
               FROM history ORDER BY id DESC"""
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Message", "Prediction", "Date & Time"])
    writer.writerows(records)

    csv_content = "\ufeff" + output.getvalue()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                "attachment; filename=spam_classifier_report.csv"
        }
    )


@app.route("/clear-history", methods=["POST"])
def clear_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM history")

    return redirect(url_for("history"))


if __name__ == "__main__":
    app.run(debug=True)
chart_spam = spam_count
chart_safe = safe_count
chart_spam=chart_spam,
chart_safe=chart_safe,