import random
import math
from flask import Flask, Blueprint, render_template, request

app = Flask(__name__)
tp4 = Blueprint("tp4", __name__, template_folder="templates")


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
):
    return {
        "checkin": 60 / checkin_arrivals,
        "security": 60 / security_arrivals,
        "passport": 60 / passport_arrivals,
        "boarding": 60 / boarding_arrivals,
        "checkin_service": 60 / ends_checkin,
        "security_service": 60 / ends_security,
        "passport_service": 60 / ends_passport,
        "boarding_service": 60 / ends_boarding,
    }


def create_initial_row(means):
    initial_row = {"row_id": 0, "event": "Initialization", "clock": 0}

    for process in means:
        if "_service" not in process:
            initial_row[f"{process}_arrival_rnd"] = f"{random.random():.4f}"
            initial_row[f"{process}_arrival_time_between"] = ""
            initial_row[f"{process}_arrival_next"] = ""
            initial_row[f"end_{process}_rnd"] = ""
            initial_row[f"end_{process}_time"] = ""
            for server_id in range(1, 4 if process in ["checkin", "boarding"] else 3):
                initial_row[f"end_{process}_{server_id}"] = float("inf")
                initial_row[f"{process}_state_{server_id}"] = "Free"
            initial_row[f"{process}_queue"] = 0
            initial_row[f"ac_waiting_time_{process}"] = 0
            initial_row[f"passengers_waited_{process}"] = 0

    return initial_row


def update_service_state(
    new_row, event_name, means, clock, passenger_states, event_id_map, passenger_id
):
    server_count = 3 if event_name in ["checkin", "boarding"] else 2
    for server_id in range(1, server_count + 1):
        if new_row[f"{event_name}_state_{server_id}"] == "Free":
            new_row[f"{event_name}_state_{server_id}"] = "Busy"
            rnd_end = random.random()
            end_time = exponential_random(means[f"{event_name}_service"], rnd_end)
            new_row[f"end_{event_name}_rnd"] = f"{rnd_end:.4f}"
            new_row[f"end_{event_name}_time"] = f"{end_time:.2f}"
            end_clock = clock + end_time
            new_row[f"end_{event_name}_{server_id}"] = f"{end_clock:.2f}"
            event_id = event_id_map[event_name]
            event_id_map[f"end_{event_name}_{server_id}"] = (
                f"{event_name.capitalize()[:3]}_{event_id}",
                passenger_id,
                end_clock,
            )
            passenger_states[passenger_id] = (
                f"in_{event_name} {event_name.capitalize()[:3]}_{event_id}"
            )
            new_row[f"passenger_{passenger_id}_state"] = passenger_states[passenger_id]
            return True
    return False


def handle_queue(
    new_row, event_name, means, clock, passenger_states, event_id_map, passenger_id_map
):
    if new_row[f"{event_name}_queue"] > 0:
        new_row[f"{event_name}_queue"] -= 1
        queued_passengers = [
            id
            for id, state in passenger_states.items()
            if state == f"in_queue_{event_name}"
        ]
        if queued_passengers:
            passenger_id = min(queued_passengers)
            update_service_state(
                new_row,
                event_name,
                means,
                clock,
                passenger_states,
                event_id_map,
                passenger_id,
            )


def simulate(
    start_row,
    additional_rows,
    total_rows,
    checkin_arrivals,
    ends_checkin,
    security_arrivals,
    ends_security,
    passport_arrivals,
    ends_passport,
    boarding_arrivals,
    ends_boarding,
):
    means = initialize_means(
        checkin_arrivals,
        ends_checkin,
        security_arrivals,
        ends_security,
        passport_arrivals,
        ends_passport,
        boarding_arrivals,
        ends_boarding,
    )
    all_rows = [create_initial_row(means)]
    rows_to_show = []
    arrival_counts = {process: 0 for process in means if "_service" not in process}
    event_id_map = {process: 0 for process in means if "_service" not in process}
    passenger_id_map = {"current_passenger_id": 0}
    passenger_states = {}
    active_passengers = set()  # New set to track active passengers

    # Initialize arrival times
    for process in means:
        if "_service" not in process:
            rnd = float(all_rows[0][f"{process}_arrival_rnd"])
            arrival_time_between = exponential_random(means[process], rnd)
            all_rows[0][
                f"{process}_arrival_time_between"
            ] = f"{arrival_time_between:.2f}"
            all_rows[0][f"{process}_arrival_next"] = f"{arrival_time_between:.2f}"

    rows_to_show.append(all_rows[0])

    row_count = 0
    rows_shown = 0
    while row_count <= total_rows:
        prev_row = all_rows[-1]
        events_times = {}

        for event in means:
            if "_service" not in event:
                events_times[f"{event}_arrival"] = float(
                    prev_row[f"{event}_arrival_next"]
                )
                server_count = 3 if event in ["checkin", "boarding"] else 2
                for server_id in range(1, server_count + 1):
                    end_time = prev_row[f"end_{event}_{server_id}"]
                    if end_time != "":
                        events_times[f"end_{event}_{server_id}"] = float(end_time)

        next_event, clock = min(events_times.items(), key=lambda x: x[1])

        new_row = prev_row.copy()
        new_row["clock"] = clock
        new_row["row_id"] = row_count + 1

        for process in means:
            if "_service" not in process:
                new_row[f"{process}_arrival_rnd"] = ""
                new_row[f"{process}_arrival_time_between"] = ""

        if "end" in next_event:
            parts = next_event.split("_")
            event_name = parts[1]
            server_id = parts[2]

            if f"end_{event_name}_{server_id}" in event_id_map:
                event_id, passenger_id, _ = event_id_map[
                    f"end_{event_name}_{server_id}"
                ]

                new_row["event"] = (
                    f"End {event_name.capitalize()} ({server_id}) {event_id}"
                )

                if passenger_id in passenger_states:
                    new_row[f"passenger_{passenger_id}_state"] = "-"
                    passenger_states[passenger_id] = "-"

                new_row[f"end_{event_name}_rnd"] = ""
                new_row[f"end_{event_name}_time"] = ""
                new_row[f"end_{event_name}_{server_id}"] = ""
                new_row[f"{event_name}_state_{server_id}"] = "Free"

                del event_id_map[f"end_{event_name}_{server_id}"]

                handle_queue(
                    new_row,
                    event_name,
                    means,
                    clock,
                    passenger_states,
                    event_id_map,
                    passenger_id_map,
                )
            else:
                print(f"Warning: No matching end event found for {next_event}")

        else:
            event_name = next_event.split("_")[0]
            arrival_counts[event_name] += 1
            event_id_map[event_name] += 1
            event_id = f"{event_name.capitalize()[:3]}_{arrival_counts[event_name]}"
            passenger_id_map["current_passenger_id"] += 1
            new_passenger_id = passenger_id_map["current_passenger_id"]

            new_row["event"] = f"{event_name.capitalize()} arrival {event_id}"
            new_row[f"{event_name}_arrival_rnd"] = f"{random.random():.4f}"

            rnd_arrival = float(new_row[f"{event_name}_arrival_rnd"])
            arrival_time_between = exponential_random(means[event_name], rnd_arrival)
            new_row[f"{event_name}_arrival_time_between"] = (
                f"{arrival_time_between:.2f}"
            )
            new_row[f"{event_name}_arrival_next"] = (
                f"{clock + arrival_time_between:.2f}"
            )

            if not update_service_state(
                new_row,
                event_name,
                means,
                clock,
                passenger_states,
                event_id_map,
                new_passenger_id,
            ):
                new_row[f"{event_name}_queue"] += 1
                passenger_states[new_passenger_id] = f"in_queue_{event_name}"
                new_row[f"passenger_{new_passenger_id}_state"] = passenger_states[
                    new_passenger_id
                ]
        for key, state in passenger_states.items():
            if state != "-":
                active_passengers.add(key)
            elif key in active_passengers:
                active_passengers.remove(key)

        # Ensure passenger states are updated in the new row
        for key in passenger_states:
            new_row[f"passenger_{key}_state"] = passenger_states.get(key, "-")

        all_rows.append(new_row)

        if row_count >= start_row and rows_shown < additional_rows:
            rows_to_show.append(new_row)
            rows_shown += 1

        row_count += 1

    if rows_to_show[-1] != all_rows[-1]:
        rows_to_show.append(all_rows[-1])

    for row in rows_to_show:
        for key, value in row.items():
            if value == float("inf"):
                row[key] = ""
    
    passenger_count = passenger_id_map["current_passenger_id"]

    return rows_to_show, passenger_count, active_passengers


@tp4.route("/tp4", methods=["GET"])
def tp4_render():
    start_row = int(request.args.get("start_row", default=0, type=int))
    additional_rows = int(request.args.get("additional_rows", default=100, type=int))
    total_rows = int(request.args.get("total_rows", default=100, type=int))
    checkin_arrivals = int(request.args.get("checkin_arrivals", default=50, type=int))
    ends_checkin = int(request.args.get("ends_checkin", default=15, type=int))
    security_arrivals = int(request.args.get("security_arrivals", default=40, type=int))
    ends_security = int(request.args.get("ends_security", default=20, type=int))
    passport_arrivals = int(request.args.get("passport_arrivals", default=25, type=int))
    ends_passport = int(request.args.get("ends_passport", default=12, type=int))
    boarding_arrivals = int(request.args.get("boarding_arrivals", default=60, type=int))
    ends_boarding = int(request.args.get("ends_boarding", default=25, type=int))

    data, passenger_count, active_passengers = simulate(
        start_row,
        additional_rows,
        total_rows,
        checkin_arrivals,
        ends_checkin,
        security_arrivals,
        ends_security,
        passport_arrivals,
        ends_passport,
        boarding_arrivals,
        ends_boarding,
    )
    return render_template(
        "tp4.html", data=data, passenger_count=passenger_count, active_passengers=active_passengers, request=request
    )


if __name__ == "__main__":
    app.register_blueprint(tp4)
    app.run(debug=True)
