import sys
import os

print("Executable:", sys.executable)
print("Path:", sys.path)

try:
    import flask

    print("Flask location:", flask.__file__)
except ImportError as e:
    print("Error importing flask:", e)

try:
    import pytest

    print("Pytest location:", pytest.__file__)
except ImportError as e:
    print("Error importing pytest:", e)

# Try importing app
try:
    sys.path.append(os.getcwd())
    import flask_app

    print("Flask App imported successfully")
except ImportError as e:
    print("Error importing flask_app:", e)
except Exception as e:
    print("Error running flask_app:", e)
