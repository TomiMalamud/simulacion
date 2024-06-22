import math
import random


def exponential_random(mean, rnd):
    while rnd == 1.0:
        rnd = random.random()
    return -mean * math.log(1 - rnd)


def initialize_means(
    checkin_arrivals,
    ends_checkin,
    security_arrivals,
    ends_security,
    passport_arrivals,
    ends_passport,
    boarding_arrivals,
    ends_boarding,
    embalaje_arrivals,
    ends_embalaje
):
    return {
        "checkin": 60 / checkin_arrivals,
        "security": 60 / security_arrivals,
        "passport": 60 / passport_arrivals,
        "boarding": 60 / boarding_arrivals,
        "embalaje": 60 / embalaje_arrivals,
        "checkin_service": 60 / ends_checkin,
        "security_service": 60 / ends_security,
        "passport_service": 60 / ends_passport,
        "boarding_service": 60 / ends_boarding,
        "embalaje_service": 60 / ends_embalaje,
    }


def create_initial_row(means, checkin_servers):
    initial_row = {"row_id": 0, "event": "Initialization", "clock": 0}

    for event in means:
        if "_service" not in event:
            initial_row[f"{event}_arrival_rnd"] = f"{random.random():.4f}"
            initial_row[f"{event}_arrival_time_between"] = ""
            initial_row[f"{event}_arrival_next"] = ""
            initial_row[f"end_{event}_rnd"] = ""
            initial_row[f"end_{event}_time"] = ""
            
            server_count = checkin_servers if event == "checkin" else (3 if event == "boarding" else 2)
            
            for server_id in range(1, server_count + 1):
                initial_row[f"end_{event}_{server_id}"] = float("inf")
                initial_row[f"{event}_state_{server_id}"] = "Free"
                
            initial_row[f"{event}_queue"] = 0
            initial_row[f"ac_waiting_time_{event}"] = 0
            initial_row[f"passengers_waited_{event}"] = 0

    return initial_row


def update_service_state(
    new_row, event, means, clock, passenger_states, event_id_map, passenger_id, checkin_servers, occupation_start_times
):
    server_count = checkin_servers if event == "checkin" else (3 if event == "boarding" else 2)
    all_free_before = all(new_row[f"{event}_state_{i}"] == "Free" for i in range(1, server_count + 1))

    for server_id in range(1, server_count + 1):
        if new_row[f"{event}_state_{server_id}"] == "Free":
            new_row[f"{event}_state_{server_id}"] = "Busy"
            rnd_end = random.random()
            end_time = exponential_random(means[f"{event}_service"], rnd_end)
            new_row[f"end_{event}_rnd"] = f"{rnd_end:.4f}"
            new_row[f"end_{event}_time"] = f"{end_time:.2f}"
            end_clock = clock + end_time
            new_row[f"end_{event}_{server_id}"] = f"{end_clock:.2f}"
            event_id = event_id_map[event]
            event_id_map[f"end_{event}_{server_id}"] = (
                f"{event.capitalize()[:3]}_{event_id}",
                passenger_id,
                end_clock,
            )
            passenger_states[passenger_id] = (
                f"in_{event} {event.capitalize()[:3]}_{event_id}"
            )
            new_row[f"passenger_{passenger_id}_state"] = passenger_states[passenger_id]
            new_row[f"passenger_{passenger_id}_started_waiting"] = "-"
            if all_free_before and event not in occupation_start_times:
                occupation_start_times[event] = clock

            return True
    return False


def handle_queue(
    new_row, event, means, clock, passenger_states, event_id_map, passenger_id_map, checkin_servers, occupation_start_times
):
    if new_row[f"{event}_queue"] > 0:
        new_row[f"{event}_queue"] -= 1
        queued_passengers = [
            id
            for id, state in passenger_states.items()
            if state == f"in_queue_{event}"
        ]
        if queued_passengers:
            passenger_id = min(queued_passengers)
            
            # Calculate waiting time
            started_waiting = float(new_row[f"passenger_{passenger_id}_started_waiting"])
            waiting_time = clock - started_waiting
            
            # Update accumulated waiting time
            prev_ac_waiting_time = float(new_row.get(f"ac_waiting_time_{event}", 0))
            new_row[f"ac_waiting_time_{event}"] = f"{prev_ac_waiting_time + waiting_time:.2f}"
            
            # Reset started_waiting time
            new_row[f"passenger_{passenger_id}_started_waiting"] = "-"
            
            update_service_state(
                new_row,
                event,
                means,
                clock,
                passenger_states,
                event_id_map,
                passenger_id,
                checkin_servers,
                occupation_start_times
            )
