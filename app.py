from flask import Flask, request, render_template, jsonify
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib
import io
import base64
import random
import math

matplotlib.use("Agg")
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

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
    """
    Calculate the critical value for the Chi-squared test for a given alpha level.

    df: degrees of freedom
    alpha: significance level (default 0.05)
    """
    return stats.chi2.ppf(1 - alpha, df)


def combinar_intervalos(observados, esperados):
    """
    Merge intervals to ensure all expected frequencies are at least 5.

    Parameters:
    o (np.array): observed frequencies
    e (np.array): expected frequencies

    Returns:
    tuple: (merged observed frequencies, merged expected frequencies)
    """
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
                "Max": (
                    max_diferencia if i == len(limites_intervalo) - 2 else None
                ),
            }
        )
    return tabla_ks


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

@app.route("/generate", methods=["POST"])
def generar_numeros():
    print("Petición recibida:", request.json)
    try:
        content = request.json
        n = int(content["muestra"])
        distribucion = content["distribucion"]
        params = content["params"]
        intervalos = int(content["intervalos"])
        ks_critical = obtener_valor_critico_ks(n)

        if distribucion == "uniforme":
            a = float(params.get("a", 0))
            b = float(params.get("b", 1))
            if a >= b:
                raise ValueError("'a' debe ser menor a 'b'.")

            data = generador_uniforme(a, b, n)
            frecuenciasEsperadas = np.full(intervalos, n / intervalos)
            probFrecuenciasEsp = np.array(
                list(map(lambda x: x / n, frecuenciasEsperadas))
            )
            chi_critical = valor_critico_chi2(intervalos - 1, 0.05)
            probFrecuenciasEspAc = []
            acumulador = 0
            for i in range(len(probFrecuenciasEsp)):
                acumulador += probFrecuenciasEsp[i]
                probFrecuenciasEspAc.append(acumulador)

            bin_edges = np.linspace(a, b, intervalos + 1)

        elif distribucion == "exponencial":
            lambd = float(params.get("lambda", 1))
            if lambd <= 0:
                raise ValueError("Lambda debe ser positivo.")
            scale = 1 / lambd
            chi_critical = valor_critico_chi2(intervalos - 2, 0.05)

            data = generador_exponencial(scale, n)
            upper_bound = stats.expon.ppf(0.99, scale=scale)  # 99th percentile
            bin_edges = np.linspace(0, upper_bound, intervalos + 1)

            probFrecuenciasEspAc = stats.expon.cdf(bin_edges, scale=scale)
            probFrecuenciasEsp = np.diff(probFrecuenciasEspAc)
            frecuenciasEsperadas = probFrecuenciasEsp * n

        elif distribucion == "normal":
            mu = float(params.get("mu", 0))
            sigma = float(params.get("sigma", 1))
            if sigma <= 0:
                raise ValueError("Sigma debe ser positivo.")
            chi_critical = valor_critico_chi2(intervalos - 3, 0.05)

            data = generador_normal(mu, sigma, n)

            lower_bound = stats.norm.ppf(0.005, mu, sigma)
            upper_bound = stats.norm.ppf(0.995, mu, sigma)
            bin_edges = np.linspace(lower_bound, upper_bound, intervalos + 1)
            probFrecuenciasEspAc = stats.norm.cdf(bin_edges, mu, sigma)
            probFrecuenciasEsp = np.diff(probFrecuenciasEspAc)
            frecuenciasEsperadas = probFrecuenciasEsp * n
        else:
            raise ValueError("El tipo de distribución seleccionado tiene un error.")

        data = np.round(data, 4)

        # Generar histograma
        fig, ax = plt.subplots()
        counts, bins, patches = ax.hist(
            data, bins=bin_edges, color="blue", edgecolor="black"
        )
        ax.set_xlabel("Valor")
        ax.set_ylabel("Frecuencia")
        plt.title("Histograma")

        # Histograma a PNG
        img = io.BytesIO()
        plt.savefig(img, format="png")
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf8")

        # Ajuste de Frecuencias esperadas para coincidir frecuencia observada
        frecuenciasEsperadas *= counts.sum() / frecuenciasEsperadas.sum()

        # Prueba de bondad de ajuste
        try:
            chi2_stat = chi_cuadrado_manual(counts, frecuenciasEsperadas)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        chi2_stat_scipy, chi2_p_scipy = stats.chisquare(
            counts, f_exp=frecuenciasEsperadas
        )
        # Calcular Ks..
        ksCalculado = estadistico_ks(counts, frecuenciasEsperadas)            

        c_values = (frecuenciasEsperadas - counts) ** 2 / frecuenciasEsperadas
        c_ac_values = np.cumsum(c_values)

        # Build rows for the Chi-squared table
        chi_squared_table = []
        for i in range(len(bin_edges) - 1):
            row = {
                "limite_inferior": bin_edges[i],
                "limite_superior": bin_edges[i + 1],
                "fo": counts[i],
                "fe": frecuenciasEsperadas[i],
                "c": c_values[i],
                "c_ac": c_ac_values[i],
            }
            chi_squared_table.append(row)

        ks_table = generar_tabla_ks(bin_edges, counts, frecuenciasEsperadas)

        data_min = np.min(data)
        data_max = np.max(data)
        data_range = data_max - data_min
        num_bins = int(np.sqrt(n)) + 1
        bin_amplitude = data_range / num_bins
        data_mean = np.mean(data)

        result = {
            "histogram": "data:image/png;base64,{}".format(plot_url),
            "chi_square_stat": np.round(chi2_stat, 4),
            "kolmogorovStat": np.round(ksCalculado, 4),
            "data": data.tolist(),
            "sample_size": n,
            "min": np.round(data_min, 4),
            "max": np.round(data_max, 4),
            "range": np.round(data_range, 4),
            "bin_amplitude": np.round(bin_amplitude, 4),
            "mean": np.round(data_mean, 4),
            "chi_critical": np.round(chi_critical, 4),
            "ks_critical": np.round(ks_critical, 4),
            "chi_squared_table": chi_squared_table,
            "ks_table": ks_table,
        }

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False)
