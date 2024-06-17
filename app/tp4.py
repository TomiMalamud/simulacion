from flask import Flask, Blueprint, render_template
import random
import math

app = Flask(__name__)

tp4 = Blueprint('tp4', __name__, template_folder='templates')

def exponential_random(mean, rnd):
    return -mean * math.log(1 - rnd)

def simulate():
    means = {
        "checkin": 1.2,
        "security": 1.5,
        "passport": 2.4,
        "boarding": 1.0,
        "checkin_service": 60/15,
        "security_service": 60/20,
        "passport_service": 60/12,
        "boarding_service": 60/25,
    }

    def create_initial_row():
        return {
            "event": "Initialization",
            "clock": 0,
            **{f"{process}_arrival_rnd": f"{random.random():.4f}" for process in means if "_service" not in process},
            **{f"{process}_arrival_time_between": "" for process in means if "_service" not in process},
            **{f"{process}_arrival_next": "" for process in means if "_service" not in process},
            **{f"end_{process}_rnd": "" for process in means if "_service" not in process},
            **{f"end_{process}_time": "" for process in means if "_service" not in process},
            **{f"end_{process}": float('inf') for process in means if "_service" not in process},
            **{f"{process}_queue": 0 for process in means if "_service" not in process},
            **{f"{process}_state_{i}": "Free" for process in means if "_service" not in process for i in range(1, 4)},
            **{f"ac_waiting_time_{process}": 0 for process in means if "_service" not in process},
            **{f"passengers_waited_{process}": 0 for process in means if "_service" not in process},
        }

    def update_service_state(new_row, event_name, means, clock):
        for i in range(1, 4):
            if new_row[f"{event_name}_state_{i}"] == "Free":
                new_row[f"{event_name}_state_{i}"] = "Busy"
                rnd_end = random.random()
                end_time = exponential_random(means[f"{event_name}_service"], rnd_end)
                new_row[f"end_{event_name}_rnd"] = f"{rnd_end:.4f}"
                new_row[f"end_{event_name}_time"] = f"{end_time:.2f}"
                new_row[f"end_{event_name}"] = f"{clock + end_time:.2f}"
                return
        new_row[f"{event_name}_queue"] += 1

    rows = [create_initial_row()]
    event_counts = {process: 0 for process in means if "_service" not in process}

    # Initialize arrival times
    for process in means:
        if "_service" not in process:
            rnd = float(rows[0][f"{process}_arrival_rnd"])
            rows[0][f"{process}_arrival_time_between"] = f"{exponential_random(means[process], rnd):.2f}"
            rows[0][f"{process}_arrival_next"] = f"{exponential_random(means[process], rnd):.2f}"

    for i in range(1, 10):
        prev_row = rows[-1]
        # Determine the next event by finding the minimum value in arrival_next and end event columns
        events_times = {f"{event}_arrival": float(prev_row[f"{event}_arrival_next"]) for event in means if "_service" not in event}
        events_times.update({f"end_{event}": float(prev_row[f"end_{event}"]) for event in means if "_service" not in event})
        
        next_event, clock = min(events_times.items(), key=lambda x: x[1])

        print(f"Next event: {next_event}, Clock: {clock}")  # Debug statement

        if "end" in next_event:
            event_name = next_event.split('_')[1]
            event_counts[event_name] += 1
        else:
            event_name = next_event.split('_')[0]
            event_counts[event_name] += 1

        new_row = {**prev_row}
        # Reset arrival columns
        for process in means:
            if "_service" not in process:
                new_row[f"{process}_arrival_rnd"] = ""
                new_row[f"{process}_arrival_time_between"] = ""

        if "arrival" in next_event:
            new_row.update({
                "event": f"{event_name.capitalize()} arrival {event_name.capitalize()[:3]}_{event_counts[event_name]}",
                "clock": clock,
                f"{event_name}_arrival_rnd": f"{random.random():.4f}",
            })

            rnd_arrival = float(new_row[f"{event_name}_arrival_rnd"])
            new_row.update({
                f"{event_name}_arrival_time_between": f"{exponential_random(means[event_name], rnd_arrival):.2f}",
                f"{event_name}_arrival_next": f"{clock + exponential_random(means[event_name], rnd_arrival):.2f}",
            })

            update_service_state(new_row, event_name, means, clock)

        elif "end" in next_event:
            new_row.update({
                "event": f"End {event_name.capitalize()} {event_name.capitalize()[:3]}_{event_counts[event_name]}",
                "clock": clock,
                f"end_{event_name}_rnd": "",
                f"end_{event_name}_time": "",
                f"end_{event_name}": float('inf'),
            })
            # Free the server and check if anyone is in queue
            for i in range(1, 4):
                if new_row[f"{event_name}_state_{i}"] == "Busy":
                    new_row[f"{event_name}_state_{i}"] = "Free"
                    if new_row[f"{event_name}_queue"] > 0:
                        new_row[f"{event_name}_queue"] -= 1
                        update_service_state(new_row, event_name, means, clock)
                    break

        rows.append(new_row)
    # Replace 'inf' with blank in the final data
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
