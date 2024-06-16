from flask import Flask, Blueprint, render_template
import random
import math

app = Flask(__name__)

# Define the blueprint
tp4 = Blueprint('tp4', __name__, template_folder='templates')

def generate_random_data():
    # Generate random numbers
    rnd_checkin = random.random()
    rnd_security = random.random()
    rnd_passport = random.random()
    rnd_boarding = random.random()
    
    # Calculate time between arrivals using the exponential distribution formula
    lambda_checkin = 60/50
    lambda_security = 60/45
    lambda_passport = 60/25
    lambda_boarding = 60/60

    tba_checkin = -lambda_checkin * math.log(1 - rnd_checkin)
    tba_security = -lambda_security * math.log(1 - rnd_security)
    tba_passport = -lambda_passport * math.log(1 - rnd_passport)
    tba_boarding = -lambda_boarding * math.log(1 - rnd_boarding)

    # Initialize data for the table
    initial_data = [
        {
            "event": "Initialization",
            "clock": 0,
            "checkin_arrival_rnd": f"{rnd_checkin:.4f}",
            "checkin_arrival_time_between": f"{tba_checkin:.2f}",
            "checkin_arrival_next": f"{tba_checkin:.2f}",
            "security_arrival_rnd": f"{rnd_security:.4f}",
            "security_arrival_time_between": f"{tba_security:.2f}",
            "security_arrival_next": f"{tba_security:.2f}",
            "passport_arrival_rnd": f"{rnd_passport:.4f}",
            "passport_arrival_time_between": f"{tba_passport:.2f}",
            "passport_arrival_next": f"{tba_passport:.2f}",
            "boarding_arrival_rnd": f"{rnd_boarding:.4f}",
            "boarding_arrival_time_between": f"{tba_boarding:.2f}",
            "boarding_arrival_next": f"{tba_boarding:.2f}",
            "end_checkin_rnd": "",
            "end_checkin_time": "",
            "end_checkin": "",
            "end_security_rnd": "",
            "end_security_time": "",
            "end_security": "",
            "end_passport_rnd": "",
            "end_passport_time": "",
            "end_passport": "",
            "end_boarding_rnd": "",
            "end_boarding_time": "",
            "end_boarding": "",
            "checkin_state": "Free",
            "checkin_queue_1": 0,
            "checkin_queue_2": 0,
            "checkin_queue_3": 0,
            "security_state": "Free",
            "security_queue_1": 0,
            "security_queue_2": 0,
            "passport_state": "Free",
            "passport_queue_1": 0,
            "passport_queue_2": 0,
            "boarding_state": "Free",
            "boarding_queue_1": 0,
            "boarding_queue_2": 0,
            "boarding_queue_3": 0,
            "ac_waiting_time_checkin": 0,
            "passengers_waited_checkin": 0,
            "ac_waiting_time_security": 0,
            "passengers_waited_security": 0,
            "ac_waiting_time_passport": 0,
            "passengers_waited_passport": 0,
            "ac_waiting_time_boarding": 0,
            "passengers_waited_boarding": 0,
            "passenger_1_state": "",
            "passenger_2_state": "",
            "passenger_3_state": "",
        }
    ]
    return initial_data

@tp4.route("/tp4")
def tp4_render():
    data = generate_random_data()
    return render_template("tp4.html", data=data)

# Register the blueprint
app.register_blueprint(tp4)

if __name__ == "__main__":
    app.run(debug=True)