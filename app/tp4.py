from flask import Blueprint, render_template, request, jsonify
import random, math

tp4 = Blueprint('tp4', __name__, template_folder='templates')

@tp4.route("/tp4")
def tp4_render():
    return render_template("tp4.html")

@tp4.route('/colas', methods=['POST'])
def simular_colas():
    data = request.json
    lineas_simulación = data["dias_simulación"]
    linea_inicial_mostrar = data["linea_incial"]
    linea_final_mostrar = data["linea_final"]

    # Las medias de llegadas están en horas --> Ej: 50 pasajeros por hora --> Pasarlo a 1 pasajero cada 1,2 min en la simulación
    tasa_llegadas_checkin = data['tasa_checkin']
    tasa_llegadas_seguridad = data['tasa_seguridad']
    tasa_llegadas_control = data['tasa_control']
    tasa_llegadas_embarque = data['tasa_embarque']

    # Las medias de fin están en horas --> Ej: 50 pasajeros por hora --> Pasarlo a 1 pasajero cada 1,2 min en la simulación
    tasa_fin_checkin = data["tasa_fin_checkin"]
    tasa_fin_seguridad = data["tasa_fin_seguridad"]
    tasa_fin_control = data["tasa_fin_control"]
    tasa_fin_embarque = data["tasa_fin_embarque"]


    vector1 = []
    vector2 = []
    linea = 0
    reloj = 0
    tiempo_espera_total = 0
    tiempo_espera_prom = 0
    tiempo_utilización_checkin = 0
    tiempo_utilización_sec = 0
    tiempo_utilización_control = 0
    tiempo_utilización_embarque = 0
    porcent_utilización_checkin = 0
    porcent_utilización_sec = 0
    porcent_utilización_control = 0
    porcent_utilización_embarque = 0

    while linea <= lineas_simulación:
        if linea == 0:
           # Check in
            cola_check = 0
            tiempo_prox_llegada_check, rnd = calcular_llegada(tasa_llegadas_checkin)
            proxima_llegada_check = reloj + tiempo_prox_llegada_check
            
            # Mostradores Check In
            hora_fin_mostrador1 = 0
            hora_fin_mostrador2 = 0
            hora_fin_mostrador3 = 0

            # Seguridad
            cola_sec = 0
            tiempo_prox_llegada_sec, rnd_sec = calcular_llegada(tasa_llegadas_seguridad)
            proxima_llegada_sec = reloj + tiempo_prox_llegada_sec
            
            # Puntos de control seguridad
            hora_fin_punto1 = 0
            hora_fin_punto2 = 0

            # Control pasaporte
            cola_pasaporte = 0
            tiempo_prox_llegada_pasap, rnd_pasap = calcular_llegada(tasa_llegadas_control)
            proxima_llegada_pasap = reloj + tiempo_prox_llegada_pasap
            
            # Puntos de control seguridad
            hora_fin_oficial1 = 0
            hora_fin_oficial2 = 0

            # Embarque
            cola_embarque = 0
            tiempo_prox_llegada_emb, rnd_emb = calcular_llegada(tasa_llegadas_embarque)
            proxima_llegada_emb = reloj + tiempo_prox_llegada_emb
            
            # Puntos de control seguridad
            hora_fin_puerta1 = 0
            hora_fin_puerta2 = 0
            hora_fin_puerta3 = 0


            vector_checkin = [ cola_check , rnd,tiempo_prox_llegada_check, proxima_llegada_check, "Libre", hora_fin_mostrador1,
                            "Libre", hora_fin_mostrador2, "Libre", hora_fin_mostrador3]
            
            vector_seguridad = [cola_sec,  rnd_sec ,tiempo_prox_llegada_sec, proxima_llegada_sec, 
                                "Libre", hora_fin_punto1, "Libre", hora_fin_punto2]
            
            vector_pasaporte = [cola_pasaporte,  rnd_pasap , tiempo_prox_llegada_pasap, 
                                proxima_llegada_pasap, "Libre", hora_fin_oficial1, "Libre", hora_fin_oficial2]


            vector_embarque = [cola_embarque,  rnd_emb, tiempo_prox_llegada_emb, proxima_llegada_emb,
                            "Libre", hora_fin_puerta1, "Libre", hora_fin_puerta2, "Libre", hora_fin_puerta3]


            vector_estadísticos = [    tiempo_espera_total, tiempo_espera_prom, tiempo_utilización_checkin, tiempo_utilización_sec,
                                   tiempo_utilización_control, tiempo_utilización_embarque, porcent_utilización_checkin, porcent_utilización_sec,
                                   porcent_utilización_control, porcent_utilización_embarque]

            vector1.extend(["Inicio", reloj, vector_checkin, vector_seguridad, vector_pasaporte,
                             vector_embarque, vector_estadísticos])

        # Trabajar modificando el vector 2...
        elif linea % 2 != 0:
            proximos_eventos = [proxima_llegada_check, proxima_llegada_emb, proxima_llegada_pasap, proxima_llegada_sec, hora_fin_mostrador1,
                                hora_fin_mostrador2, hora_fin_mostrador3, hora_fin_oficial1, hora_fin_oficial2, hora_fin_punto1, 
                                hora_fin_punto2, hora_fin_puerta1, hora_fin_puerta2, hora_fin_puerta3]
            
            proximo_evento = min(proximos_eventos)
            while proximo_evento == 0:
                proximos_eventos.pop()
                proximo_evento = min(proximos_eventos) 
            
            pass

        # Trabajar modificando el vector 1...
        elif linea % 2 == 0:
            pass

        # Hay que ir creando vectores por cada línea de simulación...
        while linea_inicial_mostrar <= linea <= linea_final_mostrar:
            pass


def calcular_llegada(tasa_llegadas):
    rnd = random.random()
    tiempo_prox_llegada = -(1/tasa_llegadas) - math.log(1-rnd)
    return tiempo_prox_llegada, rnd




