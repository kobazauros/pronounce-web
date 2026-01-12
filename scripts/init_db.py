from flask_app import app, db, SystemConfig

with app.app_context():
    print("Creating all tables...")
    db.create_all()

    # Ensure default config exists
    if not SystemConfig.get("maintenance_mode"):
        print("Setting default maintenance_mode=False")
        SystemConfig.set("maintenance_mode", "False")

    db.session.commit()
    print("Database initialized successfully.")
