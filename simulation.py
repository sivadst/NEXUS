from collections import deque

class EventSimulator:
    def __init__(self):
        # FIFO Queue for real-time event processing
        self.event_queue = deque()

    def enqueue_event(self, event_type, u, v, value):
        """
        event_type: 'hazard' or 'crowd'
        """
        self.event_queue.append((event_type, u, v, value))

    def process_events(self, graph):
        """
        Pops all pending events from the queue and updates the graph state.
        """
        processed_count = 0
        while self.event_queue:
            e_type, u, v, val = self.event_queue.popleft()
            graph.update_edge_state(u, v, e_type, val)
            processed_count += 1
        return processed_count