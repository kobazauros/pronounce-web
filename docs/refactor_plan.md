# Refactoring and Optimization Plan

This document outlines a strategic plan to refactor key areas of the application. The focus is on improving performance, scalability, and production-readiness by addressing identified bottlenecks in VTLN calculation, static file serving, and configuration management.

---

### 1. VTLN Calculation Scaling

**Problem:** The current VTLN `alpha` calculation in `analysis_engine.py` is inefficient. For every submission, it performs a heavy database query, joining `AnalysisResult` and `Submission` tables to fetch all of a user's historical formant ratios. This process is not scalable and will lead to significant performance degradation as users accumulate more recordings.

**Solution:** Denormalize the formant ratio data by caching it on the `User` model. We will add two new columns: `vtln_alpha` to store the calculated median, and `vtln_ratios` to store a running list of all raw ratios. This eliminates the need for expensive joins on every analysis.

**Implementation Steps:**

1.  **Modify `models.py`:**
    *   Add `vtln_alpha = db.Column(db.Float)` to the `User` model to store the cached median value.
    *   Add `vtln_ratios = db.Column(db.JSON)` to the `User` model to store the list of historical `f1_raw/f1_ref` and `f2_raw/f2_ref` values.

2.  **Database Migration:**
    *   Generate a new Alembic migration script to add the `vtln_alpha` and `vtln_ratios` columns to the `user` table.
    *   Run the migration to apply the schema changes.

3.  **Refactor `analysis_engine.py`:**
    *   In the `process_submission` function, fetch the user object.
    *   Instead of querying the `AnalysisResult` table, retrieve the historical ratios directly from `user.vtln_ratios`.
    *   Append the newly calculated ratios from the current submission to this list.
    *   Compute the new median `alpha` from the updated list.
    *   Save the new median to `user.vtln_alpha` and the updated list to `user.vtln_ratios`.
    *   Commit the changes to the user object in the database session.

4.  **Data Backfill (Optional but Recommended):**
    *   Create a one-time script to populate the `vtln_ratios` and `vtln_alpha` for all existing users based on their submission history. This will ensure a seamless transition.

---

### 2. Static Asset Handling in Production

**Problem:** User-uploaded audio files are currently served by the `/uploads/<path:filename>` route in `flask_app.py`, which uses Flask's `send_from_directory`. This method is inefficient and insecure for a production environment, as it ties up the Python application worker to serve static files and lacks the robustness of a dedicated web server.

**Solution:** Offload static file serving to Nginx using the `X-Accel-Redirect` header. The Flask route will remain as the access point to perform authentication and authorization, but Nginx will handle the actual file transmission. This is a secure and highly performant approach.

**Implementation Steps:**

1.  **Modify `deploy/nginx.conf`:**
    *   Define a new `internal` location block (e.g., `/protected_uploads/`). This location will not be directly accessible from the web.
    *   Use an `alias` directive within this block to point to the application's upload folder on the filesystem.

    ```nginx
    location /protected_uploads/ {
      internal;
      alias /path/to/your/project/submissions/;
    }
    ```

2.  **Refactor `flask_app.py`:**
    *   In the `serve_upload` route, keep all existing logic for authenticating the user and verifying their permission to access the requested file.
    *   Instead of calling `send_from_directory`, create a new response object.
    *   Set the `X-Accel-Redirect` header on the response, with the value pointing to the internal Nginx location (e.g., `/protected_uploads/1/some_file.mp3`).
    *   Set the `Content-Type` header appropriately.
    *   Return this new response. Flask will send the empty response with the special header, and Nginx will intercept it and serve the file.

---

### 3. Synchronous Configuration Caching

**Problem:** The `check_for_maintenance` function, decorated with `@before_request`, is executed for every single request made to the application. Inside this function, `SystemConfig.get_bool('maintenance_mode')` performs a database query. This results in at least one unnecessary database hit for every API call, page load, and static asset request, adding latency and load.

**Solution:** Implement a caching layer for system configuration values. By caching the maintenance mode status in memory for a short period (e.g., 60 seconds), we can virtually eliminate these repetitive database queries.

**Implementation Steps:**

1.  **Update Dependencies:**
    *   Add `Flask-Caching` to the `requirements.txt` file.
    *   Run `pip install -r requirements.txt`.

2.  **Initialize Cache in `flask_app.py`:**
    *   Import the `Cache` class.
    *   Instantiate it with a simple in-memory configuration:
        ```python
        from flask_caching import Cache

        app = Flask(__name__)
        cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
        ```

3.  **Apply Caching in `models.py`:**
    *   Import the `cache` object from your Flask app instance.
    *   Apply the `@cache.memoize()` decorator to the `get` class method within the `SystemConfig` model.
    *   Set a reasonable timeout to ensure configuration changes are picked up without requiring an application restart.

    ```python
    from your_app import cache # Adjust import as needed

    class SystemConfig(db.Model):
        # ... existing model ...

        @classmethod
        @cache.memoize(timeout=60) # Cache for 60 seconds
        def get(cls, key: str) -> str | None:
            # ... existing method logic ...
    ```
