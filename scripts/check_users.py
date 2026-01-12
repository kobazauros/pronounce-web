from flask_app import app, db, User

with app.app_context():
    count = User.query.count()
    print(f"Total Users: {count}")

    users = User.query.order_by(User.id.desc()).limit(5).all()
    for u in users:
        print(f"- {u.username} (ID: {u.student_id})")
