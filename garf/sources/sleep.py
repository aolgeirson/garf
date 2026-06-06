from garf.sources.base import DailySummarySource


class Sleep(DailySummarySource):
    client_method = "get_sleep_data"
    update_columns = ["sleep_score", "sleep_duration_s"]

    def extract(self, raw: dict) -> dict:
        dto = raw.get("dailySleepDTO") or {}
        scores = dto.get("sleepScores") or {}
        overall = scores.get("overall") or {}
        return {
            "sleep_score": overall.get("value"),
            "sleep_duration_s": dto.get("sleepTimeSeconds"),
        }
