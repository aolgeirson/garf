from garf.sources.base import DailySummarySource


class TrainingStatus(DailySummarySource):
    client_method = "get_training_status"
    update_columns = ["training_status", "training_status_phrase"]

    def extract(self, raw: dict) -> dict:
        # Status lives per-device under mostRecentTrainingStatus; take the
        # primary training device, falling back to any reporting device.
        latest = (raw.get("mostRecentTrainingStatus") or {}).get(
            "latestTrainingStatusData"
        ) or {}
        entries = list(latest.values())
        entry = next(
            (e for e in entries if e.get("primaryTrainingDevice")),
            entries[0] if entries else {},
        )
        return {
            "training_status": entry.get("trainingStatus"),
            "training_status_phrase": entry.get("trainingStatusFeedbackPhrase"),
        }
