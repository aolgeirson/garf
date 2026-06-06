from garf.sources.base import DailySummarySource


class Calories(DailySummarySource):
    client_method = "get_stats"
    update_columns = ["total_kilocalories", "active_kilocalories", "bmr_kilocalories"]

    def extract(self, raw: dict) -> dict:
        return {
            "total_kilocalories": raw.get("totalKilocalories"),
            "active_kilocalories": raw.get("activeKilocalories"),
            "bmr_kilocalories": raw.get("bmrKilocalories"),
        }
