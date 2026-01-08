import shutil
from pathlib import Path

# Define the target structure based on the Roadmap
NEW_DIRS = [
    "audio",
    "instance",
    "migrations",
    "scripts",
    "static/css",
    "static/js",
    "submissions/pre",
    "submissions/post",
    "templates/dashboards",
    "tests",
]

# Map existing files to new locations
# Format: "current_filename": "new_path"
MOVES = {
    "styles.css": "static/css/styles.css",
    "script.js": "static/js/script.js",
    "index.html": "templates/index.html",
    # We will keep these in root for now, but they will eventually move or be refactored
    "analyze_vowels.py": "analyze_vowels.py",
    "flask_app.py": "flask_app.py",
    "requirements.txt": "requirements.txt",
    "readme.md": "readme.md",
}


def scaffold():
    base_path = Path(".")
    print(f"📂 Setting up structure in: {base_path.absolute()}")

    # 1. Create Directories
    for d in NEW_DIRS:
        dir_path = base_path / d
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"   ✅ Created: {d}/")
        else:
            print(f"   bw Exists: {d}/")

    # 2. Create Empty Files (Placeholders for new roadmap items)
    placeholders = [
        "templates/base.html",
        "templates/login.html",
        "templates/register.html",
        "templates/dashboards/teacher_view.html",
        "templates/dashboards/student_detail.html",
        "templates/dashboards/admin_view.html",
        "scripts/migrate_legacy.py",
        "models.py",
        "config.py",
        "auth_routes.py",
    ]

    for p in placeholders:
        file_path = base_path / p
        if not file_path.exists():
            file_path.touch()
            print(f"   📄 Created empty file: {p}")

    # 3. Move Existing Files (Safely)
    for src_name, dest_name in MOVES.items():
        src = base_path / src_name
        dest = base_path / dest_name

        # Only move if source exists and destination doesn't
        if src.exists():
            if not dest.exists():
                shutil.move(str(src), str(dest))
                print(f"   🚚 Moved: {src_name} -> {dest_name}")
            elif src.samefile(dest):
                pass  # Already there
            else:
                print(
                    f"   ⚠️  Skipped: {dest_name} already exists (Manual check required)"
                )
        else:
            # It's okay if some source files don't exist yet
            pass

    print("\n🎉 Structure update complete! You are ready for Phase 1.")


if __name__ == "__main__":
    scaffold()
