from datetime import datetime, timezone

from garf.sources.base import WorkoutSource


class Workouts(WorkoutSource):
    def extract_activity(self, activity: dict) -> dict:
        start = datetime.strptime(
            activity["startTimeGMT"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        return {
            "activity_id": activity["activityId"],
            "activity_type": (activity.get("activityType") or {}).get("typeKey"),
            "start_time": start,
            "duration_s": activity.get("duration"),
            "distance_m": activity.get("distance"),
            "calories": activity.get("calories"),
            "avg_hr": activity.get("averageHR"),
            "max_hr": activity.get("maxHR"),
        }
