from flask import Flask, Blueprint, render_template, request
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

def simulate(start_line, end_line, total_rows):
    means = initialize_means()
    all_rows = [create_initial_row(means)]
    rows_to_show = []
    arrival_counts = {process: 0 for process in means if "_service" not in process}
    event_id_map = {process: 0 for process in means if "_service" not in process}
    passenger_id_map = {"current_passenger_id": 0}
    passenger_states = {}
    tiempo_espera_checkin = 0
    tiempo_espera_checkin_prom = 0
    tiempo_espera_seguridad = 0
    tiempo_espera_sec_prom = 0
    tiempo_espera_pasaportes = 0 
    tiempo_espera_pasap_prom = 0
    tiempo_espera_embaque = 0
    tiempo_espera_emb_prom = 0

    tiempo_ocupacion_checkin = 0 
    porcent_ocup_checkin = 0
    tiempo_ocupacion_sec = 0
    porcent_ocup_sec = 0
    tiempo_ocupacion_pasap = 0
    porcent_ocup_pasap = 0
    tiempo_ocupacion_embarque = 0 
    porcent_ocup_embarq = 0


    # Initialize arrival times
    for process in means:
        if "_service" not in process:
            rnd = float(all_rows[0][f"{process}_arrival_rnd"])
            arrival_time_between = exponential_random(means[process], rnd)
            all_rows[0][f"{process}_arrival_time_between"] = f"{arrival_time_between:.2f}"
            all_rows[0][f"{process}_arrival_next"] = f"{arrival_time_between:.2f}"

    row_count = 1
    while row_count <= total_rows:
        prev_row = all_rows[-1]
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


        # Para el estadístico del punto 1 (tiempo de espera promedio por servicio)...
        if new_row["checkin_queue"] > 0:
            tiempo_espera_checkin += (new_row["clock"] - prev_row["clock"])
            tiempo_espera_checkin_prom += (tiempo_espera_checkin/new_row["checkin_queue"])
            new_row["promedy_time_checkin"] = round(tiempo_espera_checkin_prom,2)

        if new_row["security_queue"] > 0:
            tiempo_espera_seguridad += (new_row["clock"] - prev_row["clock"])
            tiempo_espera_sec_prom += (tiempo_espera_seguridad/new_row["security_queue"])
            new_row["promedy_time_security"] = round(tiempo_espera_sec_prom,2)

        if new_row["passport_queue"] > 0:
            tiempo_espera_pasaportes += (new_row["clock"] - prev_row["clock"])            
            tiempo_espera_pasap_prom += (tiempo_espera_pasaportes/new_row["passport_queue"])
            new_row["promedy_time_passport"] = round(tiempo_espera_pasap_prom,2)

        if new_row["boarding_queue"] > 0:
            tiempo_espera_embaque += (new_row["clock"] - prev_row["clock"])            
            tiempo_espera_emb_prom += (tiempo_espera_embaque/new_row["boarding_queue"])
            new_row["promedy_time_boarding"] = round(tiempo_espera_emb_prom,2)

        # Para la parte 2 del punto 1...
        for i in range(1, 4):
            if new_row[f"checkin_state_{i}"] == "Busy":   
                tiempo_ocupacion_checkin += (new_row["clock"] - prev_row["clock"])
                porcent_ocup_checkin = (tiempo_ocupacion_checkin/new_row["clock"]) * 100
                new_row["ocupation_time_checkin"] = round(tiempo_ocupacion_checkin,2)
                new_row["porcent_time_checkin"] = round(porcent_ocup_checkin,2)
                break

        for i in range(1, 3):
            if new_row[f"security_state_{i}"] == "Busy":   
                tiempo_ocupacion_sec += (new_row["clock"] - prev_row["clock"])
                porcent_ocup_sec = (tiempo_ocupacion_sec/new_row["clock"]) * 100
                new_row["ocupation_time_security"] = round(tiempo_ocupacion_sec,2)
                new_row["porcent_time_security"] = round(porcent_ocup_sec,2)
                break

        for i in range(1, 3):
            if new_row[f"passport_state_{i}"] == "Busy":   
                tiempo_ocupacion_pasap += (new_row["clock"] - prev_row["clock"])
                porcent_ocup_pasap = (tiempo_ocupacion_pasap/new_row["clock"]) * 100
                new_row["ocupation_time_passport"] = round(tiempo_ocupacion_pasap,2)
                new_row["porcent_time_passport"] = round(porcent_ocup_pasap,2)
                break

        for i in range(1, 4):
            if new_row[f"boarding_state_{i}"] == "Busy":   
                tiempo_ocupacion_embarque += (new_row["clock"] - prev_row["clock"])
                porcent_ocup_embarq = (tiempo_ocupacion_embarque/new_row["clock"]) * 100
                new_row["ocupation_time_boarding"] = round(tiempo_ocupacion_embarque, 2)
                new_row["porcent_time_boarding"] = round(porcent_ocup_embarq,2)
                break
        # Ensure passenger states are updated in the new row
        for key in passenger_states:
            new_row[f"passenger_{key}_state"] = passenger_states.get(key, "-")

        all_rows.append(new_row)

        if row_count >= start_line and row_count <= end_line:
            rows_to_show.append(new_row)

        row_count += 1

    for row in rows_to_show:
        for key, value in row.items():
            if value == float('inf'):
                row[key] = ""
    passenger_count = passenger_id_map["current_passenger_id"]

    return rows_to_show, passenger_count

@tp4.route('/tp4', methods=['GET'])
def tp4_render():
    start_line = int(request.args.get("start_line", default=0, type=int))
    end_line = int(request.args.get("end_line",default=10, type=int))
    total_rows = int(request.args.get("total_rows",default=10, type=int))
    data, passenger_count = simulate(start_line, end_line, total_rows)
    return render_template("tp4.html", data=data, passenger_count=passenger_count)

if __name__ == "__main__":
    app.register_blueprint(tp4)
    app.run(debug=True)
