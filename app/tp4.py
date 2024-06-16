from flask import Flask, Blueprint, render_template
import random
import math

app = Flask(__name__)

# Define the blueprint
tp4 = Blueprint('tp4', __name__, template_folder='templates')

def exponential_random(mean):
    return -mean * math.log(1 - random.random())

def generate_random_data():
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
            **{f"{process}_arrival_time_between": f"{exponential_random(means[process]):.2f}" for process in means if "_service" not in process},
            **{f"{process}_arrival_next": f"{exponential_random(means[process]):.2f}" for process in means if "_service" not in process},
            **{f"end_{process}_rnd": "" for process in means if "_service" not in process},
            **{f"end_{process}_time": "" for process in means if "_service" not in process},
            **{f"end_{process}": "" for process in means if "_service" not in process},
            **{f"{process}_state": "Free" for process in means if "_service" not in process},
            **{f"{process}_queue_{i}": 0 for process in means if "_service" not in process for i in range(1, 4)},
            **{f"ac_waiting_time_{process}": 0 for process in means if "_service" not in process},
            **{f"passengers_waited_{process}": 0 for process in means if "_service" not in process},
            "passenger_1_state": "",
            "passenger_2_state": "",
            "passenger_3_state": "",
        }

    rows = [create_initial_row()]
    event_counts = {process: 0 for process in means if "_service" not in process}

    for i in range(1, 10):
        prev_row = rows[-1]
        next_event, clock = min(
            {f"{event}_arrival": float(prev_row[f"{event}_arrival_next"]) for event in means if "_service" not in event}.items(), 
            key=lambda x: x[1]
        )

        event_counts[next_event.split('_')[0]] += 1
        event_name = next_event.split('_')[0]

        new_row = {**prev_row}
        # Reset arrival columns
        for process in means:
            if "_service" not in process:
                new_row[f"{process}_arrival_rnd"] = ""
                new_row[f"{process}_arrival_time_between"] = ""

        new_row.update({
            "event": f"{event_name.capitalize()} arrival {event_name.capitalize()[:3]}_{event_counts[event_name]}",
            "clock": clock,
            f"{event_name}_arrival_rnd": f"{random.random():.4f}",
            f"{event_name}_arrival_time_between": f"{exponential_random(means[event_name]):.2f}",
            f"{event_name}_arrival_next": f"{clock + exponential_random(means[event_name]):.2f}",
        })

        if f"end_{event_name}" in new_row:
            rnd_end = random.random()
            end_time = exponential_random(means[f"{event_name}_service"])
            new_row.update({
                f"end_{event_name}_rnd": f"{rnd_end:.4f}",
                f"end_{event_name}_time": f"{end_time:.2f}",
                f"end_{event_name}": f"{clock + end_time:.2f}",
            })

        rows.append(new_row)

    return rows

@tp4.route("/tp4")
def tp4_render():
    data = generate_random_data()
    return render_template("tp4.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)