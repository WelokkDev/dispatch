"""
Server-Sent Events (SSE) for real-time push to the dashboard.
Call broadcast(event) to push to all connected clients.
"""

import json
import queue
import threading

# Each client gets a queue; we push event dicts (JSON-serializable)
_clients: list[queue.Queue] = []
_lock = threading.Lock()


def subscribe():
    """Register a new client. Returns a queue that will receive event dicts."""
    q = queue.Queue()
    with _lock:
        _clients.append(q)
    return q


def unsubscribe(q):
    """Remove a client queue."""
    with _lock:
        try:
            _clients.remove(q)
        except ValueError:
            pass


def broadcast(event: dict):
    """Send event to all connected clients. Event must be JSON-serializable."""
    with _lock:
        clients = list(_clients)
    for q in clients:
        try:
            q.put_nowait(event)
        except queue.Full:
            pass
