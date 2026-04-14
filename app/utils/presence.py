import time
import threading

# Configuration
ONLINE_TIMEOUT = 300  # 5 minutes
check_interval = 60

class PresenceTracker:
    def __init__(self):
        # { user_id: timestamp }
        self._last_seen = {}
        
        # { user_id: "START_MONITORING" }
        self._pending_commands = {}
        
        self._lock = threading.Lock()

    def update_seen(self, user_id):
        with self._lock:
            self._last_seen[user_id] = time.time()

    def is_online(self, user_id):
        with self._lock:
            last = self._last_seen.get(user_id)
            if not last: return False
            return (time.time() - last) < ONLINE_TIMEOUT

    def set_command(self, user_id, command):
        with self._lock:
            self._pending_commands[user_id] = command

    def pop_command(self, user_id):
        with self._lock:
            return self._pending_commands.pop(user_id, None)

    def get_online_users(self):
        cutoff = time.time() - ONLINE_TIMEOUT
        with self._lock:
            return [uid for uid, t in self._last_seen.items() if t > cutoff]

# Singleton
tracker = PresenceTracker()
