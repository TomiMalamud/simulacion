from flask import Blueprint, render_template, request, jsonify
import random

tp3 = Blueprint('tp3', __name__, template_folder='templates')

@tp3.route("/tp3")
def tp3_render():
    return render_template("tp3.html")

@tp3.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    demand_values = data['demand_values']
    demand_prob = data['demand_prob']
    advance_values = data['advance_values']
    advance_prob = data['advance_prob']
    initial_inventory = data['initial_inventory']
    order_quantity = data['order_quantity']
    holding_cost_per_unit_per_week = data['holding_cost_per_unit_per_week']
    ordering_cost = data['ordering_cost']
    stockout_cost_per_unit = data['stockout_cost_per_unit']
    num_weeks = data['num_weeks']
    days_per_week = data['days_per_week']
    num_days = num_weeks * days_per_week

    # Initialize variables
    inventory = initial_inventory
    total_holding_cost = 0
    total_ordering_cost = 0
    total_stockout_cost = 0
    total_cost = 0
    next_order_delivery_day = -1
    order_placed = False
    weekly_holding_cost = 0

    # Weekdays for reference
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Result table
    table = []

    # Run simulation for the specified number of days
    for day in range(num_days):
        day_name = weekdays[day % days_per_week]
        rnd_demand = random.random()
        rnd_advance = random.random()
        daily_demand = random.choices(demand_values, demand_prob)[0]

        if inventory < daily_demand:
            stockout_units = daily_demand - inventory
            stockout_cost = stockout_units * stockout_cost_per_unit
            inventory = 0
        else:
            stockout_cost = 0
            inventory -= daily_demand

        if day % days_per_week == 0:
            holding_cost = inventory * holding_cost_per_unit_per_week
            total_holding_cost += holding_cost
            weekly_holding_cost = holding_cost / days_per_week
        else:
            holding_cost = 0

        if day % days_per_week == 0 and not order_placed:
            next_order_delivery_day = day + (days_per_week - 2) - random.choices(advance_values, advance_prob)[0]
            total_ordering_cost += ordering_cost
            order_placed = True
        else:
            ordering_cost = 0

        if day == next_order_delivery_day:
            inventory += order_quantity
            order_placed = False

        total_cost += holding_cost + stockout_cost

        days_in_advance = random.choices(advance_values, advance_prob)[0]

        table.append({
            "day": day_name,
            "day_num": day,
            "rnd_demand": rnd_demand,
            "demand": daily_demand,
            "stock": inventory,
            "order_placed": order_placed,
            "rnd_advance": rnd_advance,
            "days_in_advance": days_in_advance,
            "holding_cost": holding_cost if day % days_per_week == 0 else weekly_holding_cost,
            "ordering_cost": ordering_cost,
            "stockout_cost": stockout_cost
        })

    result = {
        'total_holding_cost': total_holding_cost,
        'total_ordering_cost': total_ordering_cost,
        'total_stockout_cost': total_stockout_cost,
        'total_cost': total_cost,
        'average_holding_cost': total_holding_cost / num_days,
        'average_ordering_cost': total_ordering_cost / num_days,
        'average_stockout_cost': total_stockout_cost / num_days,
        'average_total_cost': total_cost / num_days,
        'table': table
    }

    return jsonify(result)

