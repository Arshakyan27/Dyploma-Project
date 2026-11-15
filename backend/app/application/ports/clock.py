from collections.abc import Callable
from datetime import datetime

# Returns the current timezone-aware (UTC) time.
Clock = Callable[[], datetime]
