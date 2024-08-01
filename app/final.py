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
        return next((i for i, state in enumerate(silo_states) if state == "Free"), None)

    for i in range(start_row, start_row + additional_rows):
        rnd = random.random()
        time_between_arrivals = 5 + (9 - 5) * rnd  # Uniform between 5 and 9

        if i == 0:
            next_arrival = clock + time_between_arrivals

            row = {
                "index": 0,
                "event": "Initialization",
                "clock": 0,
                "rnd": round(rnd, 2),
                "time_between_arrivals": round(time_between_arrivals, 2),
                "next_arrival": round(next_arrival, 2),
                "rnd_load": "",
                "truck_load": "",
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
            rnd_load = random.random()
            truck_load = 10 if rnd_load < 0.5 else 12
            unloading_time = 0.2160 if truck_load == 10 else 0.2300

            if prev_row["tube_state"] == "Free":
                tube_state = "Busy"
                empty_silo = select_free_silo()
                if empty_silo is not None:
                    silo_states[empty_silo] = "Being filled"
                    current_unloading_silo = empty_silo
                    end_unloading = clock + unloading_time
                else:
                    # No empty silo available, add to tube queue
                    tube_queue += 1
                    end_unloading = prev_row["end_unloading"]
            else:
                # Tube is busy, add to tube queue
                tube_state = "Busy"
                tube_queue += 1
                rnd_load = prev_row["rnd_load"]
                truck_load = prev_row["truck_load"]
                unloading_time = prev_row["unloading_time"]
                end_unloading = prev_row["end_unloading"]

            remaining_truck_load = truck_load
            silo_emptying = prev_row["silo_emptying"]

        elif event == "End of Unloading":
            rnd = ""
            time_between_arrivals = ""
            next_arrival = prev_row["next_arrival"]
            end_unloading = ""
            rnd_load = ""
            truck_load = ""
            unloading_time = ""

            if current_unloading_silo is not None:
                space_available = 20 - silos_flour[current_unloading_silo]
                if remaining_truck_load <= space_available:
                    silos_flour[current_unloading_silo] += remaining_truck_load
                    remaining_truck_load = 0
                    if silos_flour[current_unloading_silo] == 20:
                        silo_states[current_unloading_silo] = "Full"
                    else:
                        # Check if this is the only silo with flour
                        if all(
                            flour == 0
                            for i, flour in enumerate(silos_flour)
                            if i != current_unloading_silo
                        ):
                            silo_states[current_unloading_silo] = "Supplying Plant"
                            current_supplying_silo = current_unloading_silo
                        else:
                            silo_states[current_unloading_silo] = "Free"
                    current_unloading_silo = None
                else:
                    silos_flour[current_unloading_silo] = 20
                    silo_states[current_unloading_silo] = "Full"
                    remaining_truck_load -= space_available
                    event = "Change of silo for unloading"
                    end_unloading = (
                        clock + 1 / 6
                    )  # Add 1/6 hour for silo change preparation
                    current_unloading_silo = None  # Reset current unloading silo

            if remaining_truck_load == 0:
                if tube_queue > 0:
                    # Start unloading the next truck in queue
                    tube_queue -= 1
                    empty_silo = select_free_silo()
                    if empty_silo is not None:
                        silo_states[empty_silo] = "Being filled"
                        current_unloading_silo = empty_silo
                        # Assume the next truck in queue has the same unloading time
                        end_unloading = clock + (
                            0.2160 if random.random() < 0.5 else 0.2300
                        )
                    else:
                        tube_state = "Free"
                else:
                    tube_state = "Free"

            # Calculate silo_emptying after unloading
            if any(amount > 0 for amount in silos_flour):
                silo_emptying = clock + 1
            else:
                silo_emptying = ""

        elif event == "Silo Emptying":
            rnd = ""
            time_between_arrivals = ""
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
                        if amount > 0
                        and silo_states[i] not in ["Being filled", "Supplying Plant"]
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
                            if amount > 0
                            and silo_states[i]
                            not in ["Being filled", "Supplying Plant"]
                        ),
                        None,
                    )
                else:
                    silo_states[current_supplying_silo] = "Supplying Plant"

            # Update silo_emptying
            if current_supplying_silo is not None or any(
                amount > 0 for amount in silos_flour
            ):
                silo_emptying = clock + 1
            else:
                silo_emptying = ""

        for silo in range(4):
            if silo != current_supplying_silo:
                if silos_flour[silo] > 0 and silo_states[silo] not in [
                    "Being filled",
                    "Full",
                    "Supplying Plant",
                ]:
                    silo_states[silo] = "Full" if silos_flour[silo] == 20 else "Free"

        row = {
            "index": i,
            "event": event,
            "clock": round(clock, 2),
            "rnd": round(rnd, 2) if isinstance(rnd, float) else "",
            "time_between_arrivals": (
                round(time_between_arrivals, 2) if time_between_arrivals else ""
            ),
            "next_arrival": round(next_arrival, 2),
            "rnd_load": round(rnd_load, 2) if isinstance(rnd_load, float) else "",
            "truck_load": truck_load if isinstance(truck_load, int) else "",
            "unloading_time": (
                unloading_time if isinstance(unloading_time, float) else ""
            ),
            "end_unloading": (
                round(end_unloading, 3)
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
            "remaining_truck_load": (
                round(remaining_truck_load, 2)
                if isinstance(remaining_truck_load, (int, float))
                else ""
            ),
        }

        simulation_data.append(row)

    return simulation_data


@final.route("/tp-final", methods=["GET"])
def tp_final():
    start_row = int(request.args.get("start_row", 0))
    additional_rows = int(request.args.get("additional_rows", 100))
    total_rows = int(request.args.get("total_rows", 100))

    simulation_data = generate_simulation_data(start_row, additional_rows)

    return render_template("tp-final.html", simulation_data=simulation_data)


if __name__ == "__main__":
    app.register_blueprint(final)
    app.run(debug=True)
