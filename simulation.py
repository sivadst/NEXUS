# ==========================
# NEXUS - SIMULATION MODULE
# ==============================

import random
from collections import deque


def simulate_crowd(crowd):
    """
    Simulate crowd changes using a queue (FIFO)
    """

    # Create queue of locations
    q = deque(crowd.keys())

    while q:
        location = q.popleft()

        # Randomly increase or decrease crowd
        change = random.choice([-1, 0, 1])

        new_value = crowd[location] + change

        # Keep crowd in range 1–5
        crowd[location] = max(1, min(5, new_value))


def simulate_hazard(hazard):
    """
    Simulate hazard at random location
    """

    # Reset all hazards
    for loc in hazard:
        hazard[loc] = 0

    # Choose random location for hazard
    danger_spot = random.choice(list(hazard.keys()))

    # Mark hazard
    hazard[danger_spot] = 1

    return danger_spot