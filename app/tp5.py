import random
from flask import Flask, Blueprint, render_template, request
from .tp4y5utils import *
import time

app = Flask(__name__)
tp5 = Blueprint("tp5", __name__, template_folder="templates")


def simulate(
    start_row,
    additional_rows,
    total_rows,
    checkin_arrivals,
    checkin_servers,
    ends_checkin,
    security_arrivals,
    ends_security,
    passport_arrivals,
    ends_passport,
    boarding_arrivals,
    ends_boarding,
    emabalaje_arrivals,
    ends_embalaje,
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
        emabalaje_arrivals,
        ends_embalaje
    )
    all_rows = [create_initial_row(means, checkin_servers)]
    rows_to_show = []
    arrival_counts = {event: 0 for event in means if "_service" not in event}
    event_id_map = {event: 0 for event in means if "_service" not in event}
    passenger_id_map = {"current_passenger_id": 0}
    passenger_states = {}
    passengers_in_range = set()  # New set to track active passengers
    occupation_start_times = {}
    passenger_completed = 0
    max_security_queue = 0
    cantidad_promedio_cola = 0
    passport_queue_time_sum = 0 
    power_outage = False
    power_outage_start_time = 0
    suspended_services = {}

    # Initialize arrival times
    for process in means:
        if "_service" not in process:
            rnd = float(all_rows[0][f"{process}_arrival_rnd"])
            if process == "power_outage":
                arrival_time_between = power_outage_time(rnd)
            else:
                arrival_time_between = exponential_random(means[process], rnd)
            all_rows[0][f"{process}_arrival_time_between"] = f"{arrival_time_between:.2f}"
            all_rows[0][f"{process}_arrival_next"] = f"{arrival_time_between:.2f}"
            all_rows[0][f"ac_waiting_time_{process}"] = "0.00"
            all_rows[0][f"average_time_{process}"] = "0.00"
            all_rows[0][f"occupation_time_{process}"] = "0.00"

            server_count = (
                checkin_servers
                if process == "checkin"
                else (3 if process == "boarding" else 2)
            )

            for server_id in range(1, server_count + 1):
                all_rows[0][f"end_{process}_{server_id}"] = ""

    rows_to_show.append(all_rows[0])

    row_count = 0
    rows_shown = 0
    total_rows = 10000 if total_rows > 50000 else total_rows

    while row_count <= total_rows:
        print("Filas antes de procesar: ",len(all_rows))
        print("Cantidad de filas procesadas:", row_count)
        prev_row = all_rows[-1]
        if row_count != 0:
            all_rows.pop()
        print("Filas procesadas menos 1: ",len(all_rows))
        events_times = {}

        for event in means:
            if "_service" not in event:
                events_times[f"{event}_arrival"] = float(prev_row[f"{event}_arrival_next"])
                if event != "power_outage":
                    server_count = checkin_servers if event == "checkin" else (3 if event == "boarding" else 2)
                    for server_id in range(1, server_count + 1):
                        end_time = prev_row[f"end_{event}_{server_id}"]
                        if end_time != "" and end_time != float("inf"):
                            events_times[f"end_{event}_{server_id}"] = float(end_time)
        
        # Add end_power_outage to events_times if there's an ongoing outage
        if prev_row["power_outage"]:
            events_times["end_power_outage"] = prev_row["end_power_outage"]

        next_event, clock = min(events_times.items(), key=lambda x: x[1])
    

        new_row = prev_row.copy()
        new_row["clock"] = clock
        new_row["row_id"] = row_count + 1


#        if new_row["clock"] == prev_row["clock"]:
#            new_row["clock"] += 0.00000001


        for process in means:
            if "_service" not in process:
                new_row[f"{process}_arrival_rnd"] = ""
                new_row[f"{process}_arrival_time_between"] = ""

        if next_event == "power_outage_arrival" and not new_row["power_outage"]:
            new_row["power_outage"] = True
            new_row["event"] = "Power Outage Start"
            new_row["power_outage_arrival_rnd"] = f"{random.random():.4f}"
            rnd = float(new_row["power_outage_arrival_rnd"])
            arrival_time_between = power_outage_time(rnd)
            new_row["power_outage_arrival_time_between"] = f"{arrival_time_between:.2f}"
            new_row["power_outage_arrival_next"] = f"{clock + arrival_time_between:.2f}"
            
            power_outage_duration_time = power_outage_duration(clock)
            new_row["power_outage_time"] = f"{power_outage_duration_time:.2f}"
            new_row["end_power_outage"] = clock + power_outage_duration_time

            # Only suspend passport services
            event = "passport"
            server_count = 2  # Assuming passport has 2 servers
            suspended_services[event] = []
            for server_id in range(1, server_count + 1):
                if new_row[f"{event}_state_{server_id}"] == "Busy":
                    suspended_time = float(new_row[f"end_{event}_{server_id}"]) - clock
                    suspended_services[event].append((server_id, suspended_time))
                new_row[f"end_{event}_{server_id}"] = float("inf")
                new_row[f"{event}_state_{server_id}"] = "Suspended"


        elif next_event == "end_power_outage":
            new_row["power_outage"] = False
            new_row["event"] = "Power Outage End"
            new_row["end_power_outage"] = float('inf')

            # Resume only passport services
            event = "passport"
            if event in suspended_services:
                for server_id, suspended_time in suspended_services[event]:
                    new_row[f"end_{event}_{server_id}"] = clock + suspended_time
                    new_row[f"{event}_state_{server_id}"] = "Busy"
            suspended_services.clear()


        elif "end" in next_event:
            parts = next_event.split("_")
            event_name = parts[1]
            server_id = parts[2]
            # Skip passport events during power outage
            if new_row["power_outage"] and event_name == "passport":
                continue

            if f"end_{event_name}_{server_id}" in event_id_map:
                event_id, passenger_id, _ = event_id_map[f"end_{event_name}_{server_id}"] 
                new_row["event"] = (f"End {event_name.capitalize()} ({server_id}) {event_id}")
                new_row[f"{event_name}_state_{server_id}"] = "Free"

                if passenger_id in passenger_states:
                    new_row[f"passenger_{passenger_id}_state"] = "-"
                    passenger_states[passenger_id] = "-"

                passenger_completed += 1
                new_row["amount_people_attended"] = passenger_completed

                new_row[f"end_{event_name}_rnd"] = ""
                new_row[f"end_{event_name}_time"] = ""
                new_row[f"end_{event_name}_{server_id}"] = ""

                del event_id_map[f"end_{event_name}_{server_id}"]

                handle_queue(
                    new_row,
                    event_name,
                    means,
                    clock,
                    passenger_states,
                    event_id_map,
                    passenger_id_map,
                    checkin_servers,
                    occupation_start_times,
                )
                all_free = all(
                    new_row[f"{event_name}_state_{i}"] == "Free"
                    for i in range(1, server_count + 1)
                )
                if all_free and event_name in occupation_start_times:
                    occupation_time = clock - occupation_start_times[event_name]
                    prev_occupation_time = float(
                        new_row[f"occupation_time_{event_name}"]
                    )
                    new_row[f"occupation_time_{event_name}"] = (
                        f"{prev_occupation_time + occupation_time:.2f}"
                    )
                    del occupation_start_times[event_name]

            else:
                print(f"Warning: No matching end event found for {next_event}")

        else:
            event_name = next_event.split("_")[0]

            # Skip passport arrivals during power outage
            if new_row["power_outage"] and event_name == "passport":
                continue

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
                checkin_servers,
                occupation_start_times,
            ):
                new_row[f"{event_name}_queue"] += 1
                passenger_states[new_passenger_id] = f"in_queue_{event_name}"
                new_row[f"passenger_{new_passenger_id}_state"] = passenger_states[
                    new_passenger_id
                ]
                new_row[f"passenger_{new_passenger_id}_started_waiting"] = (
                    clock  # Initialize when the passenger starts waiting
                )
                # Actualizar el máximo de la cola de seguridad
                if event_name == "security":
                    max_security_queue = max(max_security_queue, new_row["security_queue"])

            new_row["amount_people_attended"] = passenger_completed
        

        # Agregar el máximo de la cola de seguridad a cada fila
        new_row["max_amount_sec_queue"] = max_security_queue


        # Ensure passenger states are updated in the new row
        for key in passenger_states:
            new_row[f"passenger_{key}_state"] = passenger_states.get(key, "-")

        for event in means:
            if "_service" not in event:
                new_row[f"ac_waiting_time_{event}"] = new_row.get(
                    f"ac_waiting_time_{event}", "0.00"
                )
                ac_waiting_time = float(new_row[f"ac_waiting_time_{event}"])
                event_count = arrival_counts[event]
                if event_count > 0:
                    average_time = ac_waiting_time / event_count
                    new_row[f"average_time_{event}"] = f"{average_time:.2f}"
                else:
                    new_row[f"average_time_{event}"] = "0.00"
                
                if event == "passport":
                    passport_queue_time_sum = ac_waiting_time  # Actualiza la suma del tiempo de espera para pasaporte
                
                if clock > 0:
                    cantidad_promedio_cola = passport_queue_time_sum / clock
                    new_row["promedy_amount_passport_queue"] = f"{cantidad_promedio_cola:.2f}"
                else:
                    new_row["promedy_amount_passport_queue"] = "0.00"


                if event in occupation_start_times:
                    current_occupation_time = clock - occupation_start_times[event]
                    prev_occupation_time = float(new_row[f"occupation_time_{event}"])
                    new_row[f"occupation_time_{event}"] = (
                        f"{prev_occupation_time + current_occupation_time:.2f}"
                    )
                    occupation_start_times[event] = (
                        clock  # Reset start time for next calculation
                    )

                # Calculate and store percent_time_{event}
                occupation_time = float(new_row[f"occupation_time_{event}"])
                if clock > 0:
                    percent_time = (occupation_time / clock) * 100
                    new_row[f"percent_time_{event}"] = f"{percent_time:.2f}"
                else:
                    new_row[f"percent_time_{event}"] = "0.00"

        all_rows.append(new_row)
        print("Filas después de procesar:  ",len(all_rows))

        if row_count >= start_row and rows_shown < additional_rows:
            rows_to_show.append(new_row)
            rows_shown += 1
            passengers_in_range.update(
                key for key in passenger_states if f"passenger_{key}_state" in new_row
            )

        row_count += 1

    # Final update for occupation times
    for event in occupation_start_times:
        occupation_time = clock - occupation_start_times[event]
        prev_occupation_time = float(all_rows[-1][f"occupation_time_{event}"])
        all_rows[-1][
            f"occupation_time_{event}"
        ] = f"{prev_occupation_time + occupation_time:.2f}"

    passengers_in_range = set(sorted(passengers_in_range)[:100])
    # Remove passenger state information for passengers not in passengers_in_range
    for row in rows_to_show:
        for key in list(row.keys()):
            if key.startswith("passenger_") and key.endswith("_state"):
                passenger_id = int(key.split("_")[1])
                if passenger_id not in passengers_in_range:
                    del row[key]

    if rows_to_show[-1] != all_rows[-1]:
        rows_to_show.append(all_rows[-1])

    for row in rows_to_show:
        for key, value in row.items():
            if value == float("inf"):
                row[key] = ""

    passenger_count = passenger_id_map["current_passenger_id"]

    final_averages = {event: float(all_rows[-1][f"average_time_{event}"]) for event in arrival_counts.keys()}
    final_percents = {event: float(all_rows[-1][f"percent_time_{event}"]) for event in arrival_counts.keys()}
    print("Final Averages:", final_averages)
    print("Final Percents:", final_percents)

    return rows_to_show, passenger_count, passengers_in_range, final_averages, final_percents, passenger_completed, max_security_queue, cantidad_promedio_cola


@tp5.route("/tp5", methods=["GET"])
def tp5_render():
    data = None
    passenger_count = 0
    passengers_in_range = []
    checkin_servers = 3
    final_averages = {}
    final_percents = {}
    min_avg_event = None
    passengers_completed = 0
    max_security_queue = 0
    cantidad_promedio_cola = 0

    if request.args:
        start_row = int(request.args.get("start_row", default=0, type=int))
        additional_rows = int(
            request.args.get("additional_rows", default=300, type=int)
        )
        total_rows = int(request.args.get("total_rows", default=1000, type=int))
        checkin_arrivals = int(
            request.args.get("checkin_arrivals", default=50, type=int)
        )
        checkin_servers = int(request.args.get("checkin_servers", default=3, type=int))
        ends_checkin = int(request.args.get("ends_checkin", default=15, type=int))
        security_arrivals = int(
            request.args.get("security_arrivals", default=40, type=int)
        )
        ends_security = int(request.args.get("ends_security", default=20, type=int))
        passport_arrivals = int(
            request.args.get("passport_arrivals", default=25, type=int)
        )
        ends_passport = int(request.args.get("ends_passport", default=12, type=int))
        boarding_arrivals = int(
            request.args.get("boarding_arrivals", default=60, type=int)
        )
        ends_boarding = int(request.args.get("ends_boarding", default=25, type=int))

        embalaje_arrivals = int(
            request.args.get("embalaje_arrivals", default=60, type=int)
        )

        ends_embalaje = int(request.args.get("ends_embalaje", default=25, type=int))
        start_time = time.time()


        data, passenger_count, passengers_in_range, final_averages, final_percents, passengers_completed, max_security_queue, cantidad_promedio_cola = (
            simulate(
                start_row,
                additional_rows,
                total_rows,
                checkin_arrivals,
                checkin_servers,
                ends_checkin,
                security_arrivals,
                ends_security,
                passport_arrivals,
                ends_passport,
                boarding_arrivals,
                ends_boarding,
                embalaje_arrivals,
                ends_embalaje
            )
        )

        end_time = time.time()  # End the timer
        processing_time = end_time - start_time  # Calculate the elapsed time

        print(
            f"Processing time: {processing_time:.2f} seconds"
        )  # Print the processing time
        if final_averages:
            min_avg_event = min(final_averages, key=final_averages.get)
        print("Min Average Event:", min_avg_event)
        print("Final Averages:", final_averages)

    return render_template(
        "tp5.html",
        data=data,
        passenger_count=passenger_count,
        passengers_in_range=passengers_in_range,
        request=request,
        checkin_servers=checkin_servers,
        final_averages=final_averages,
        final_percents=final_percents,
        min_avg_event=min_avg_event,
        passengers_completed = passengers_completed,
        max_security_queue = max_security_queue,
        cantidad_promedio_cola = round(cantidad_promedio_cola,2)
    )


if __name__ == "__main__":
    app.register_blueprint(tp5)
    app.run(debug=True)
