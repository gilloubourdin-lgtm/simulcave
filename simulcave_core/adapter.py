from simulcave_core.engine import run_simulation


def simulate_from_dict(data: dict) -> dict:
    return run_simulation(data)