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
        "clock": 0,
        "passenger_1_state": "",
        "passenger_2_state": "",
        "passenger_3_state": ""
    }
    
    for process in means:
        if "_service" not in process:
            initial_row[f"{process}_arrival_rnd"] = f"{random.random():.4f}"
            initial_row[f"{process}_arrival_time_between"] = ""
            initial_row[f"{process}_arrival_next"] = ""
            initial_row[f"end_{process}_rnd"] = ""
            initial_row[f"end_{process}_time"] = ""
            initial_row[f"end_{process}"] = float('inf')
            initial_row[f"{process}_queue"] = 0
            for i in range(1, 4):
                initial_row[f"{process}_state_{i}"] = "Free"
            initial_row[f"ac_waiting_time_{process}"] = 0
            initial_row[f"passengers_waited_{process}"] = 0
    
    return initial_row

def update_service_state(new_row, event_name, means, clock, passenger_states):
    for i in range(1, 4):
        if new_row[f"{event_name}_state_{i}"] == "Free":
            new_row[f"{event_name}_state_{i}"] = "Busy"
            rnd_end = random.random()
            end_time = exponential_random(means[f"{event_name}_service"], rnd_end)
            new_row[f"end_{event_name}_rnd"] = f"{rnd_end:.4f}"
            new_row[f"end_{event_name}_time"] = f"{end_time:.2f}"
            new_row[f"end_{event_name}"] = f"{clock + end_time:.2f}"
            passenger_states.append(f"in_{event_name}")
            return
    new_row[f"{event_name}_queue"] += 1
    passenger_states.append(f"waiting_{event_name}")

def simulate():
    means = initialize_means()
    rows = [create_initial_row(means)]
    event_counts = {process: 0 for process in means if "_service" not in process}

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
                events_times[f"end_{event}"] = float(prev_row[f"end_{event}"])
        
        next_event, clock = min(events_times.items(), key=lambda x: x[1])

        if "end" in next_event:
            event_name = next_event.split('_')[1]
        else:
            event_name = next_event.split('_')[0]
        event_counts[event_name] += 1

        new_row = prev_row.copy()

        for process in means:
            if "_service" not in process:
                new_row[f"{process}_arrival_rnd"] = ""
                new_row[f"{process}_arrival_time_between"] = ""

        passenger_states = []
        if "arrival" in next_event:
            new_row["event"] = f"{event_name.capitalize()} arrival {event_name.capitalize()[:3]}_{event_counts[event_name]}"
            new_row["clock"] = clock
            new_row[f"{event_name}_arrival_rnd"] = f"{random.random():.4f}"

            rnd_arrival = float(new_row[f"{event_name}_arrival_rnd"])
            arrival_time_between = exponential_random(means[event_name], rnd_arrival)
            new_row[f"{event_name}_arrival_time_between"] = f"{arrival_time_between:.2f}"
            new_row[f"{event_name}_arrival_next"] = f"{clock + arrival_time_between:.2f}"

            update_service_state(new_row, event_name, means, clock, passenger_states)

        elif "end" in next_event:
            new_row["event"] = f"End {event_name.capitalize()} {event_name.capitalize()[:3]}_{event_counts[event_name]}"
            new_row["clock"] = clock
            new_row[f"end_{event_name}_rnd"] = ""
            new_row[f"end_{event_name}_time"] = ""
            new_row[f"end_{event_name}"] = float('inf')

            for i in range(1, 4):
                if new_row[f"{event_name}_state_{i}"] == "Busy":
                    new_row[f"{event_name}_state_{i}"] = "Free"
                    if new_row[f"{event_name}_queue"] > 0:
                        new_row[f"{event_name}_queue"] -= 1
                        update_service_state(new_row, event_name, means, clock, passenger_states)
                    break

        for j in range(len(passenger_states)):
            new_row[f"passenger_{j + 1}_state"] = passenger_states[j]

        rows.append(new_row)

    for row in rows:
        for key, value in row.items():
            if value == float('inf'):
                row[key] = ""

    return rows

@tp4.route("/tp4")
def tp4_render():
    data = simulate()
    return render_template("tp4.html", data=data)

if __name__ == "__main__":
    app.register_blueprint(tp4)
    app.run(debug=True)
