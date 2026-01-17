from flask_app import app
from models import User, Submission

print("Starting Debug...")
try:
    with app.app_context():
        u = User.query.get(2)
        if not u:
            print("User 2 not found!")
            exit()

        print(f"User: {u.username} (ID: {u.id})")

        # Mimic the route logic
        subs = u.submissions.order_by(Submission.timestamp.desc()).all()
        print(f"Found {len(subs)} submissions.")

        for s in subs:
            print(f"checking Sub {s.id} (WordID {s.word_id})...")
            # This access triggers the relationship load
            tw = s.target_word
            print(f"  -> TargetWord Object: {tw}")

            if tw is None:
                print(
                    "  !!! CRITICAL: target_word is None! This will crash the template."
                )
            else:
                print(f"  -> Text: {tw.text}")

except Exception as e:
    print(f"CRASHED: {e}")
    import traceback

    traceback.print_exc()
