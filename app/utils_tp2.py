import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib
import io
import base64
import random
import math

matplotlib.use("Agg")

valores_criticos_ks = {
    1: 0.975,
    2: 0.842,
    3: 0.708,
    4: 0.624,
    5: 0.563,
    6: 0.521,
    7: 0.486,
    8: 0.457,
    9: 0.432,
    10: 0.410,
    11: 0.391,
    12: 0.375,
    13: 0.361,
    14: 0.349,
    15: 0.338,
    16: 0.328,
    17: 0.318,
    18: 0.309,
    19: 0.301,
    20: 0.294,
    21: 0.287,
    22: 0.281,
    23: 0.275,
    24: 0.269,
    25: 0.264,
    26: 0.259,
    27: 0.254,
    28: 0.250,
    29: 0.246,
    30: 0.242,
    31: 0.238,
    32: 0.234,
    33: 0.231,
    34: 0.227,
    35: 0.224,
}


def valor_critico_chi2(df, alpha=0.05):
    return stats.chi2.ppf(1 - alpha, df)


def combinar_intervalos(observados, esperados):
    combinado_observados = []
    combinado_esperados = []

    temporal_observados = 0
    temporal_esperados = 0

    for observado, esperado in zip(observados, esperados):
        temporal_observados += observado
        temporal_esperados += esperado

        if temporal_esperados >= 5:
            combinado_observados.append(temporal_observados)
            combinado_esperados.append(temporal_esperados)
            temporal_observados = 0
            temporal_esperados = 0

    if temporal_esperados > 0:
        if combinado_esperados:
            combinado_observados[-1] += temporal_observados
            combinado_esperados[-1] += temporal_esperados
        else:
            combinado_observados.append(temporal_observados)
            combinado_esperados.append(temporal_esperados)

    return np.array(combinado_observados), np.array(combinado_esperados)


def generar_tabla_ks(limites_intervalo, conteos, frecuencias_esperadas):
    total_fo = sum(conteos)
    total_fe = sum(frecuencias_esperadas)

    Po = conteos / total_fo
    Pe = frecuencias_esperadas / total_fe

    Po_acumulado = np.cumsum(Po)
    Pe_acumulado = np.cumsum(Pe)

    diferencias_absolutas = np.abs(Po_acumulado - Pe_acumulado)
    max_diferencia = np.max(diferencias_absolutas)

    tabla_ks = []
    for i in range(len(limites_intervalo) - 1):
        tabla_ks.append(
            {
                "limite_inferior": limites_intervalo[i],
                "limite_superior": limites_intervalo[i + 1],
                "fo": conteos[i],
                "fe": frecuencias_esperadas[i],
                "Po": Po[i],
                "Pe": Pe[i],
                "Po(AC)": Po_acumulado[i],
                "Pe(AC)": Pe_acumulado[i],
                "|Po(AC)-Pe(AC)|": diferencias_absolutas[i],
                "Max": (max_diferencia if i == len(limites_intervalo) - 2 else None),
            }
        )
    return tabla_ks


def combine_chi_squared_rows(bin_edges, counts, expected_freqs, threshold=5):
    combined_data = []
    accumulated_fo = 0
    accumulated_fe = 0
    lower_bound = bin_edges[0]

    for i in range(len(bin_edges) - 1):
        accumulated_fo += counts[i]
        accumulated_fe += expected_freqs[i]

        # Revisar si la frecuencia esperada acumulada es mayor a 5
        if accumulated_fe >= threshold:
            upper_bound = bin_edges[i + 1]
            # Si se cumple, finaliza este agrupamiento
            c_value = ((accumulated_fe - accumulated_fo) ** 2) / accumulated_fe
            combined_data.append(
                {
                    "limite_inferior": lower_bound,
                    "limite_superior": upper_bound,
                    "fo": accumulated_fo,
                    "fe": accumulated_fe,
                    "c": c_value,
                }
            )

            # Crea un nuevo grupo
            accumulated_fo = 0
            accumulated_fe = 0
            lower_bound = bin_edges[i + 1]

    # Suma el último grupo si no fue sumado
    if accumulated_fe > 0:
        upper_bound = bin_edges[-1]
        c_value = ((accumulated_fe - accumulated_fo) ** 2) / accumulated_fe
        combined_data.append(
            {
                "limite_inferior": lower_bound,
                "limite_superior": upper_bound,
                "fo": accumulated_fo,
                "fe": accumulated_fe,
                "c": c_value,
            }
        )

    # Recalcula el estadístico acumulado
    cumulative = 0
    for row in combined_data:
        cumulative += row["c"]
        row["c_ac"] = cumulative

    return combined_data


def obtener_valor_critico_ks(tamano_muestra):
    if tamano_muestra <= 0:
        raise ValueError("El tamaño de la muestra debe ser mayor a cero.")
    if tamano_muestra in valores_criticos_ks:
        return valores_criticos_ks[tamano_muestra]
    return 1.36 / np.sqrt(tamano_muestra)


def chi_cuadrado_manual(observados, esperados):
    if any(f < 5 for f in esperados):
        observados, esperados = combinar_intervalos(observados, esperados)

    chi2 = np.sum((observados - esperados) ** 2 / esperados)
    return chi2


def generador_uniforme(a, b, n):
    numeros_aleatorios = []
    for i in range(n):
        numero_aleatorio = a + random.random() * (b - a)
        numeros_aleatorios.append(numero_aleatorio)
    return numeros_aleatorios


def generador_exponencial(escala, n):
    numeros_aleatorios = []
    for i in range(n):
        num_aleatorio = random.random()
        numero_aleatorio = -escala * math.log(1 - num_aleatorio)
        numeros_aleatorios.append(numero_aleatorio)
    return numeros_aleatorios


def generador_normal(mu, sigma, n):
    numeros_aleatorios = []

    while len(numeros_aleatorios) < n:
        num_aleatorio1 = random.random()
        num_aleatorio2 = random.random()

        normal1 = (
            math.sqrt(-2 * math.log(num_aleatorio1))
            * math.cos(2 * math.pi * num_aleatorio2)
        ) * sigma + mu
        normal2 = (
            math.sqrt(-2 * math.log(num_aleatorio2))
            * math.cos(2 * math.pi * num_aleatorio1)
        ) * sigma + mu

        numeros_aleatorios.append(normal1)
        numeros_aleatorios.append(normal2)

    return numeros_aleatorios


def estadistico_ks(observed_freq, expected_freq):
    cum_observed = np.cumsum(observed_freq) / np.sum(observed_freq)
    cum_expected = np.cumsum(expected_freq) / np.sum(expected_freq)

    ks = np.max(np.abs(cum_observed - cum_expected))

    return ks