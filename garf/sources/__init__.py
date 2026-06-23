from garf.sources.training_state import TrainingStatus
from garf.sources.base import Source
from garf.sources.calories import Calories
from garf.sources.heart_rate import HeartRate, RestingHeartRate
from garf.sources.sleep import Sleep
from garf.sources.workouts import Workouts

REGISTRY: list[Source] = [
    HeartRate(),
    RestingHeartRate(),
    Sleep(),
    Calories(),
    Workouts(),
    TrainingStatus(),
]
