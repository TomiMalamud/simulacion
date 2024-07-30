from flask import Flask, Blueprint, render_template, request
import random

app = Flask(__name__)
final = Blueprint("final", __name__, template_folder="templates")


def generate_simulation_data(start_row, additional_rows):
    simulation_data = []
    clock = 0
    next_arrival = 0
    end_unloading = float("inf")
    silo_emptying = float("inf")  # Initialize to infinity
    silo_states = ["Free", "Free", "Free", "Free"]
    silos_flour = [0, 0, 0, 0]  # Flour amounts in silos 1-4
    current_supplying_silo = None
    tube_queue = 0
    current_unloading_silo = None
    remaining_truck_load = 0

    def select_free_silo():
        return next(
            (i for i, state in enumerate(silo_states) if state == "Free"), None
        )

    for i in range(start_row, start_row + additional_rows):
        rnd = random.random()
        time_between_arrivals = 5 + (9 - 5) * rnd  # Uniform between 5 and 9

        rnd_end_unloading = random.random()
        unloading_time = 2  # Constant 2 hours, because the differential equation will be solved later

        if i == 0:
            next_arrival = clock + time_between_arrivals
            rnd_load = random.random()
            truck_load = 10 if rnd_load < 0.5 else 12  # Equally probable 10 or 12 tons

            row = {
                "index": 0,
                "event": "Initialization",
                "clock": 0,
                "rnd": round(rnd, 2),
                "time_between_arrivals": round(time_between_arrivals, 2),
                "next_arrival": round(next_arrival, 2),
                "rnd_load": round(rnd_load, 2),
                "truck_load": truck_load,
                "rnd_end_unloading": "",
                "unloading_time": "",
                "end_unloading": "",
                "silo_emptying": "",
                "silo_1_state": silo_states[0],
                "silo_2_state": silo_states[1],
                "silo_3_state": silo_states[2],
                "silo_4_state": silo_states[3],
                "silo_1_flour": round(silos_flour[0], 2),
                "silo_2_flour": round(silos_flour[1], 2),
                "silo_3_flour": round(silos_flour[2], 2),
                "silo_4_flour": round(silos_flour[3], 2),
                "tube_queue": tube_queue,
                "tube_state": "Free",
            }
            simulation_data.append(row)
            continue

        # Find the minimum time and corresponding event based on the previous row
        prev_row = simulation_data[-1]
        min_time = min(
            prev_row["next_arrival"],
            prev_row["end_unloading"] if prev_row["end_unloading"] else float("inf"),
            prev_row["silo_emptying"] if prev_row["silo_emptying"] else float("inf"),
        )

        if min_time == prev_row["next_arrival"]:
            event = "Truck Arrival"
        elif min_time == prev_row["end_unloading"]:
            event = "End of Unloading"
        elif min_time == prev_row["silo_emptying"]:
            event = "Silo Emptying"

        clock = min_time

        # Event-based logic

        if event == "Truck Arrival":
            next_arrival = clock + time_between_arrivals
            if prev_row["end_unloading"] == "":
                end_unloading = clock + unloading_time
            else:
                end_unloading = prev_row["end_unloading"]
            rnd_load = random.random()
            truck_load = 10 if rnd_load < 0.5 else 12
            remaining_truck_load = truck_load
            if prev_row["tube_state"] == "Free":
                tube_state = "Busy"
                empty_silo = select_free_silo()
                if empty_silo is not None:
                    silo_states[empty_silo] = "Being filled"
                    current_unloading_silo = empty_silo
            else:
                tube_state = "Busy"
                tube_queue += 1
            silo_emptying = prev_row["silo_emptying"]

        elif event == "End of Unloading":
            next_arrival = prev_row["next_arrival"]
            end_unloading = ""
            if current_unloading_silo is not None:
                space_available = 20 - silos_flour[current_unloading_silo]
                if remaining_truck_load <= space_available:
                    silos_flour[current_unloading_silo] += remaining_truck_load
                    remaining_truck_load = 0
                    if silos_flour[current_unloading_silo] == 20:
                        silo_states[current_unloading_silo] = "Full"
                    else:
                        silo_states[current_unloading_silo] = "Free"
                    current_unloading_silo = None
                else:
                    silos_flour[current_unloading_silo] = 20
                    silo_states[current_unloading_silo] = "Full"
                    remaining_truck_load -= space_available
                    event = "Change of silo for unloading"
                    end_unloading = prev_row["end_unloading"]
                    clock = (
                        prev_row["clock"] + 1 / 6
                    )  # Add 1/6 hour for silo change preparation
                    new_silo = select_free_silo()
                    if new_silo is not None:
                        current_unloading_silo = new_silo
                        silo_states[new_silo] = "Being filled"
                    else:
                        # No available silo, stop unloading
                        current_unloading_silo = None
                        tube_state = "Free"

            if remaining_truck_load == 0:
                if prev_row["tube_queue"] > 0:
                    tube_queue = prev_row["tube_queue"] - 1
                else:
                    tube_queue = 0
                    tube_state = "Free"

            # Calculate silo_emptying after unloading
            if any(amount > 0 for amount in silos_flour):
                silo_emptying = clock + 1
            else:
                silo_emptying = ""

        elif event == "Silo Emptying":
            next_arrival = prev_row["next_arrival"]
            end_unloading = prev_row["end_unloading"]

            if (
                current_supplying_silo is None
                or silos_flour[current_supplying_silo] == 0
            ):
                current_supplying_silo = next(
                    (
                        i
                        for i, amount in enumerate(silos_flour)
                        if amount > 0 and silo_states[i] not in ["Being filled", "Supplying Plant"]
                    ),
                    None,
                )

            if current_supplying_silo is not None:
                silos_flour[current_supplying_silo] = max(
                    silos_flour[current_supplying_silo] - 0.5, 0
                )
                if silos_flour[current_supplying_silo] == 0:
                    silo_states[current_supplying_silo] = "Free"
                    current_supplying_silo = next(
                        (
                            i
                            for i, amount in enumerate(silos_flour)
                            if amount > 0 and silo_states[i] not in ["Being filled", "Supplying Plant"]
                        ),
                        None,
                    )
                else:
                    silo_states[current_supplying_silo] = "Supplying Plant"

            # Update silo_emptying
            if current_supplying_silo is not None or any(amount > 0 for amount in silos_flour):
                silo_emptying = clock + 1
            else:
                silo_emptying = ""

        for silo in range(4):
            if silo != current_supplying_silo:
                if silos_flour[silo] > 0 and silo_states[silo] not in [
                    "Being filled",
                    "Full",
                    "Supplying Plant"
                ]:
                    silo_states[silo] = "Full" if silos_flour[silo] == 20 else "Free"

        row = {
            "index": i,
            "event": event,
            "clock": round(clock, 2),
            "rnd": round(rnd, 2),
            "time_between_arrivals": round(time_between_arrivals, 2),
            "next_arrival": round(next_arrival, 2),
            "rnd_load": round(rnd_load, 2),
            "truck_load": truck_load,
            "rnd_end_unloading": round(rnd_end_unloading, 2),
            "unloading_time": unloading_time,
            "end_unloading": (
                round(end_unloading, 2)
                if isinstance(end_unloading, (int, float))
                and end_unloading != float("inf")
                else ""
            ),
            "silo_emptying": (
                round(silo_emptying, 2)
                if isinstance(silo_emptying, (int, float))
                and silo_emptying != float("inf")
                else silo_emptying
            ),
            "silo_1_state": silo_states[0],
            "silo_2_state": silo_states[1],
            "silo_3_state": silo_states[2],
            "silo_4_state": silo_states[3],
            "silo_1_flour": round(silos_flour[0], 2),
            "silo_2_flour": round(silos_flour[1], 2),
            "silo_3_flour": round(silos_flour[2], 2),
            "silo_4_flour": round(silos_flour[3], 2),
            "tube_queue": tube_queue,
            "tube_state": tube_state,
            "remaining_truck_load": round(remaining_truck_load, 2),
        }

        simulation_data.append(row)

    return simulation_data


@final.route("/tp-final", methods=["GET"])
def tp_final():
    start_row = int(request.args.get("start_row", 0))
    additional_rows = int(request.args.get("additional_rows", 10))
    total_rows = int(request.args.get("total_rows", 10))

    simulation_data = generate_simulation_data(start_row, additional_rows)

    return render_template("tp-final.html", simulation_data=simulation_data)


if __name__ == "__main__":
    app.register_blueprint(final)
    app.run(debug=True)