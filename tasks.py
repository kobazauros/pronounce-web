from celery import shared_task
from flask import current_app
from models import Submission, db
from analysis_engine import process_submission
import logging

# Configure logger
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def async_process_submission(self, submission_id):
    """
    Background task to process audio submission.
    """
    logger.info(f"Task started: Processing submission {submission_id}")

    try:
        # Re-query submission inside the task/app context
        sub = Submission.query.get(submission_id)
        if not sub:
            logger.error(f"Submission {submission_id} not found.")
            return {"status": "error", "message": "Submission not found"}

        # Run the existing synchronous analysis logic
        success = process_submission(submission_id)

        if success:
            # Refresh to get the analysis results that were saved to DB
            db.session.refresh(sub)
            result = sub.analysis

            # Re-implement the scoring logic here or fetch from DB if stored
            # (Logic copied/adapted from flask_app.py to ensure consistent return data)
            dist = result.distance_bark if result and result.distance_bark else 0
            score_val = max(0, min(100, int(100 - (dist * 20))))

            # Simple Category Logic
            score_cat = "danger"
            if dist < 1.5:
                score_cat = "success"
            elif dist < 3.0:
                score_cat = "warning"

            # Recommendation Logic
            recommendation = None
            if dist >= 1.5 and result:
                f1_diff = (
                    (result.f1_norm - result.f1_ref)
                    if (result.f1_norm and result.f1_ref)
                    else 0
                )
                f2_diff = (
                    (result.f2_norm - result.f2_ref)
                    if (result.f2_norm and result.f2_ref)
                    else 0
                )
                tips = []
                if abs(f2_diff) > 100:
                    tips.append(
                        "move your tongue slightly back"
                        if f2_diff > 0
                        else "move your tongue slightly forward"
                    )
                if abs(f1_diff) > 50:
                    tips.append(
                        "raise your tongue slightly"
                        if f1_diff > 0
                        else "lower your tongue slightly"
                    )

                if tips:
                    recommendation = "Try to " + " and ".join(tips) + "."
                elif dist >= 3.5:
                    recommendation = (
                        "Focus on matching the sample pronunciation more closely."
                    )
                else:
                    recommendation = "Good effort! Keep practicing."

            # Update simplified score on submission if not already done
            sub.score = score_val
            db.session.commit()

            return {
                "status": "success",
                "score": score_val,
                "category": score_cat,
                "distance": f"{dist:.2f} Bark",
                "analysis": {
                    "distance_bark": round(dist, 2),
                    "recommendation": recommendation,
                },
            }
        else:
            return {"status": "error", "message": "Processing failed in engine"}

    except Exception as e:
        logger.error(f"Task failed: {e}")
        # self.retry(exc=e, countdown=5) # Optional retry
        return {"status": "error", "message": str(e)}
