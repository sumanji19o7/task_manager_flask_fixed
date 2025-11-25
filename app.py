from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Task {self.id} - {self.title}>"


with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date_raw = request.form.get("due_date", "").strip()

        if not title:
            flash("Task title is required.", "error")
            return redirect(url_for("index"))

        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format.", "error")

        new_task = Task(
            title=title,
            description=description if description else None,
            due_date=due_date
        )
        db.session.add(new_task)
        db.session.commit()
        flash("Task added!", "success")
        return redirect(url_for("index"))


    sort = request.args.get("sort", "created_at")
    status_filter = request.args.get("status", "all")

    query = Task.query

    if status_filter == "active":
        query = query.filter_by(completed=False)
    elif status_filter == "completed":
        query = query.filter_by(completed=True)

    if sort == "due_date":
        query = query.order_by(Task.due_date.is_(None), Task.due_date.asc())
    elif sort == "title":
        query = query.order_by(Task.title.asc())
    else:
        query = query.order_by(Task.created_at.desc())

    tasks = query.all()
    return render_template("index.html", tasks=tasks, sort=sort, status_filter=status_filter)

@app.route("/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    flash("Task status updated.", "success")
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "success")
    return redirect(url_for("index"))

@app.route("/clear_completed", methods=["POST"])
def clear_completed():
    Task.query.filter_by(completed=True).delete()
    db.session.commit()
    flash("Completed tasks cleared.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)