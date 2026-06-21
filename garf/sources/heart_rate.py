from garf.sources.base import TimeSeriesSource, DailySummarySource


class HeartRate(TimeSeriesSource):
    metric = "heart_rate"
    client_method = "get_heart_rates"
    value_key = "heartRateValues"


class RestingHeartRate(DailySummarySource):
    client_method = "get_stats"
    update_columns = ["resting_hr"]

    def extract(self, raw: dict) -> dict:
        return {"resting_hr": raw.get("restingHeartRate")}
    

# class Sleep(DailySummarySource):
#     client_method = "get_sleep_data"
#     update_columns = ["sleep_score", "sleep_duration_s"]
#
#     def extract(self, raw: dict) -> dict:
#         dto = raw.get("dailySleepDTO") or {}
#         scores = dto.get("sleepScores") or {}
#         overall = scores.get("overall") or {}
#         return {
#             "sleep_score": overall.get("value"),
#             "sleep_duration_s": dto.get("sleepTimeSeconds"),
#         }
