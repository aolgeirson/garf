from garf.sources.base import TimeSeriesSource


class HeartRate(TimeSeriesSource):
    metric = "heart_rate"
    client_method = "get_heart_rates"
    value_key = "heartRateValues"
