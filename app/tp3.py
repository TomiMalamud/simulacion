from flask import Blueprint, render_template, request, jsonify
import random

tp3 = Blueprint('tp3', __name__, template_folder='templates')

@tp3.route("/tp3")
def tp3_render():
    return render_template("tp3.html")

@tp3.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    valores_demanda = data['valores_demanda']
    prob_demanda = data['prob_demanda']
    valores_adelanto = data['valores_adelanto']
    prob_adelanto = data['prob_adelanto']
    inventario_inicial = data['inventario_inicial']
    cantidad_pedido = data['cantidad_pedido']
    costo_almacenamiento_por_unidad_por_semana = data['costo_almacenamiento_por_unidad_por_semana']
    costo_pedido = data['costo_pedido']
    costo_desabastecimiento_por_unidad = data['costo_desabastecimiento_por_unidad']
    num_semanas = data['num_semanas']
    politica = data['politica']
    dias_por_semana = data['dias_por_semana']
    num_dias = num_semanas * dias_por_semana
    next_inventory_check = 0  # Initialize the day from which inventory can be re-evaluated after an order
    costo_acumulado=0

    inventario = inventario_inicial
    entregas_pendientes = []
    tabla = []

    for dia in range(num_dias):
        nombre_dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][dia % dias_por_semana]
        demanda_diaria, rnd_demanda = calcular_demanda(valores_demanda, prob_demanda) 

        # Update inventory with today's deliveries
        entregas_para_hoy = [cantidad for entrega_dia, cantidad in entregas_pendientes if entrega_dia == dia]
        if entregas_para_hoy:
            inventario += sum(entregas_para_hoy)
        entregas_pendientes = [(entrega_dia, cantidad) for entrega_dia, cantidad in entregas_pendientes if entrega_dia > dia]

        # Demand processing
        costo_desabastecimiento = 0
        if inventario < demanda_diaria:
            costo_desabastecimiento = (demanda_diaria - inventario) * costo_desabastecimiento_por_unidad
            inventario = 0
        else:
            inventario -= demanda_diaria

        # Weekly storage cost
        costo_almacenamiento = (costo_almacenamiento_por_unidad_por_semana * inventario) if dia % dias_por_semana == 0 else 0

        # Order placement logic
        pedido_realizado = False
        if (politica == 'A' and nombre_dia == "Lunes") or (politica == 'B' and inventario <= 5 and dia >= next_inventory_check):
            adelanto, rnd_adelanto = calcular_adelanto(valores_adelanto, prob_adelanto) 
            entrega_dia = dia + 4 - adelanto
            entregas_pendientes.append((entrega_dia, cantidad_pedido))
            next_inventory_check = entrega_dia
            pedido_realizado = True
        costos_totales = costo_almacenamiento + (costo_pedido if pedido_realizado else 0) + costo_desabastecimiento
        costo_acumulado += costos_totales
        costo_promedio_diario = costo_acumulado / (dia + 1)

        # Record results
        tabla.append({
            "dia": nombre_dia,
            "num_dia": dia,
            "rnd_demanda": rnd_demanda,
            "demanda": demanda_diaria,
            "inventario": inventario,
            "pedido_realizado": pedido_realizado,
            "rnd_adelanto": rnd_adelanto if pedido_realizado else 0,
            "dias_adelanto": adelanto if pedido_realizado else 0,
            "costo_almacenamiento": costo_almacenamiento,
            "costo_pedido": costo_pedido if pedido_realizado else 0,
            "costo_desabastecimiento": costo_desabastecimiento,
            "costos_totales": costo_almacenamiento + (costo_pedido if pedido_realizado else 0) + costo_desabastecimiento,
            "costos_totales": costos_totales,
            "costos_acumulados": costo_acumulado,
            "costo_promedio_diario": round(costo_promedio_diario, 2)

        })

    resultado = {
        'costo_total': sum(item['costos_totales'] for item in tabla),
        'costo_promedio_total': sum(item['costos_totales'] for item in tabla) / num_dias,
        'tabla': tabla
    }

    return jsonify(resultado)


def calcular_adelanto(valores_adelanto, prob_adelanto):
    rnd_adelanto = round(random.random(),2)
    # Acumula las probabilidades para encontrar el valor correspondiente
    acumulado = 0
    for demanda, probabilidad in zip(valores_adelanto, prob_adelanto):
        acumulado += probabilidad
        if rnd_adelanto < acumulado:
            return demanda, rnd_adelanto
    return valores_adelanto[-1], rnd_adelanto

def calcular_demanda(valores_demanda, prob_demanda):
    rnd_demanda = round(random.random(), 2)
    acumulado = 0
    for demanda, probabilidad in zip(valores_demanda, prob_demanda):
        acumulado += probabilidad
        if rnd_demanda < acumulado:
            return demanda, rnd_demanda
    return valores_demanda[-1], rnd_demanda