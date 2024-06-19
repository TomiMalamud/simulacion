from flask import Flask, Blueprint, render_template
import random
import math

app = Flask(__name__)

tp4 = Blueprint('tp4', __name__, template_folder='templates')

def exponential_random(mean, rnd):
    return -mean * math.log(1 - rnd)

def initialize_means():
    return {
        "checkin": 1.2,
        "security": 1.5,
        "passport": 2.4,
        "boarding": 1.0,
        "checkin_service": 60 / 15,
        "security_service": 60 / 20,
        "passport_service": 60 / 12,
        "boarding_service": 60 / 25,
    }

def create_initial_row(means):
    initial_row = {
        "event": "Initialization",
        "clock": 0    
    }

    for process in means:
        if "_service" not in process:
            initial_row[f"{process}_arrival_rnd"] = f"{random.random():.4f}"
            initial_row[f"{process}_arrival_time_between"] = ""
            initial_row[f"{process}_arrival_next"] = ""
            initial_row[f"end_{process}_rnd"] = ""
            initial_row[f"end_{process}_time"] = ""
            for server_id in range(1, 4 if process in ["checkin", "boarding"] else 3):
                initial_row[f"end_{process}_{server_id}"] = float('inf')
                initial_row[f"{process}_state_{server_id}"] = "Free"
            initial_row[f"{process}_queue"] = 0
            initial_row[f"ac_waiting_time_{process}"] = 0
            initial_row[f"passengers_waited_{process}"] = 0

    return initial_row

def update_service_state(new_row, event_name, means, clock, passenger_states, event_id_map, passenger_id_map):
    server_count = 3 if event_name in ["checkin", "boarding"] else 2
    all_busy = True
    for server_id in range(1, server_count + 1):
        if new_row[f"{event_name}_state_{server_id}"] == "Free":
            all_busy = False
            new_row[f"{event_name}_state_{server_id}"] = "Busy"
            rnd_end = random.random()
            end_time = exponential_random(means[f"{event_name}_service"], rnd_end)
            new_row[f"end_{event_name}_rnd"] = f"{rnd_end:.4f}"
            new_row[f"end_{event_name}_time"] = f"{end_time:.2f}"
            new_row[f"end_{event_name}_{server_id}"] = f"{clock + end_time:.2f}"
            event_id = event_id_map[event_name]
            event_id_map[f"end_{event_name}_{event_id}_{server_id}"] = f"{event_name.capitalize()[:3]}_{event_id}_{server_id}"
            passenger_id = passenger_id_map["current_passenger_id"]
            passenger_states[passenger_id] = f"in_{event_name} {event_name.capitalize()[:3]}_{event_id}_{server_id}"
            new_row[f"passenger_{passenger_id}_state"] = passenger_states[passenger_id]
            break
    if all_busy:
        new_row[f"{event_name}_queue"] += 1

def simulate():
    means = initialize_means()
    rows = [create_initial_row(means)]
    arrival_counts = {process: 0 for process in means if "_service" not in process}
    event_id_map = {process: 0 for process in means if "_service" not in process}
    passenger_id_map = {"current_passenger_id": 0}
    passenger_states = {}

    # Initialize arrival times
    for process in means:
        if "_service" not in process:
            rnd = float(rows[0][f"{process}_arrival_rnd"])
            arrival_time_between = exponential_random(means[process], rnd)
            rows[0][f"{process}_arrival_time_between"] = f"{arrival_time_between:.2f}"
            rows[0][f"{process}_arrival_next"] = f"{arrival_time_between:.2f}"

    for i in range(1, 10):
        prev_row = rows[-1]
        events_times = {}

        for event in means:
            if "_service" not in event:
                events_times[f"{event}_arrival"] = float(prev_row[f"{event}_arrival_next"])
                server_count = 3 if event in ["checkin", "boarding"] else 2
                for server_id in range(1, server_count + 1):
                    events_times[f"end_{event}_{server_id}"] = float(prev_row[f"end_{event}_{server_id}"])

        next_event, clock = min(events_times.items(), key=lambda x: x[1])

        new_row = prev_row.copy()

        if "end" in next_event:
            parts = next_event.split('_')
            event_name = parts[1]
            server_id = parts[2]
            event_id = f"{event_name.capitalize()[:3]}_{event_id_map[event_name]}"
            # Remove passenger state
            passenger_key = None
            for key, value in passenger_states.items():
                if value.endswith(f"{event_id}_{server_id}"):
                    passenger_key = key
                    break
            if passenger_key:
                new_row[f"passenger_{passenger_key}_state"] = "-"
                passenger_states[passenger_key] = "-"
        else:
            event_name = next_event.split('_')[0]
            arrival_counts[event_name] += 1
            event_id_map[event_name] += 1
            event_id = f"{event_name.capitalize()[:3]}_{arrival_counts[event_name]}"
            passenger_id_map["current_passenger_id"] += 1
            new_passenger_id = passenger_id_map["current_passenger_id"]

        for process in means:
            if "_service" not in process:
                new_row[f"{process}_arrival_rnd"] = ""
                new_row[f"{process}_arrival_time_between"] = ""

        if "arrival" in next_event:
            new_row["event"] = f"{event_name.capitalize()} arrival {event_id}"
            new_row["clock"] = clock
            new_row[f"{event_name}_arrival_rnd"] = f"{random.random():.4f}"

            rnd_arrival = float(new_row[f"{event_name}_arrival_rnd"])
            arrival_time_between = exponential_random(means[event_name], rnd_arrival)
            new_row[f"{event_name}_arrival_time_between"] = f"{arrival_time_between:.2f}"
            new_row[f"{event_name}_arrival_next"] = f"{clock + arrival_time_between:.2f}"

            update_service_state(new_row, event_name, means, clock, passenger_states, event_id_map, passenger_id_map)

        elif "end" in next_event:
            new_row["event"] = f"End {event_name.capitalize()} ({server_id}) {event_id}"
            new_row["clock"] = clock
            new_row[f"end_{event_name}_rnd"] = ""
            new_row[f"end_{event_name}_time"] = ""
            new_row[f"end_{event_name}_{server_id}"] = float('inf')

            for i in range(1, 4 if event_name in ["checkin", "boarding"] else 3):
                if new_row[f"{event_name}_state_{i}"] == "Busy":
                    new_row[f"{event_name}_state_{i}"] = "Free"
                    if new_row[f"{event_name}_queue"] > 0:
                        new_row[f"{event_name}_queue"] -= 1
                        update_service_state(new_row, event_name, means, clock, passenger_states, event_id_map, passenger_id_map)
                    break

        # Ensure passenger states are updated in the new row
        for key in passenger_states:
            new_row[f"passenger_{key}_state"] = passenger_states.get(key, "-")

        rows.append(new_row)

    for row in rows:
        for key, value in row.items():
            if value == float('inf'):
                row[key] = ""
    passenger_count = passenger_id_map["current_passenger_id"]

    return rows, passenger_count


@tp4.route("/tp4")
def tp4_render():
    data, passenger_count = simulate()
    return render_template("tp4.html", data=data, passenger_count=passenger_count)

if __name__ == "__main__":
    app.register_blueprint(tp4)
    app.run(debug=True)
