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

ks_critical_values = {
    1: 0.975, 2: 0.842, 3: 0.708, 4: 0.624, 5: 0.563, 6: 0.521, 7: 0.486,
    8: 0.457, 9: 0.432, 10: 0.410, 11: 0.391, 12: 0.375, 13: 0.361, 14: 0.349,
    15: 0.338, 16: 0.328, 17: 0.318, 18: 0.309, 19: 0.301, 20: 0.294, 21: 0.287,
    22: 0.281, 23: 0.275, 24: 0.269, 25: 0.264, 26: 0.259, 27: 0.254, 28: 0.250,
    29: 0.246, 30: 0.242, 31: 0.238, 32: 0.234, 33: 0.231, 34: 0.227, 35: 0.224
}

def chi_squared_critical_value(df, alpha=0.05):
    """
    Calculate the critical value for the Chi-squared test for a given alpha level.
    
    df: degrees of freedom
    alpha: significance level (default 0.05)
    """
    return stats.chi2.ppf(1 - alpha, df)

def merge_intervals(o, e):
    """
    Merge intervals to ensure all expected frequencies are at least 5.

    Parameters:
    o (np.array): observed frequencies
    e (np.array): expected frequencies

    Returns:
    tuple: (merged observed frequencies, merged expected frequencies)
    """
    merged_o = []
    merged_e = []

    temp_o = 0
    temp_e = 0

    for observed, expected in zip(o, e):
        temp_o += observed
        temp_e += expected

        # Merge until the expected frequency is at least 5
        if temp_e >= 5:
            merged_o.append(temp_o)
            merged_e.append(temp_e)
            temp_o = 0
            temp_e = 0

    # Ensure no data is left behind in case the last interval is less than 5
    if temp_e > 0:
        if merged_e:
            merged_o[-1] += temp_o
            merged_e[-1] += temp_e
        else:
            merged_o.append(temp_o)
            merged_e.append(temp_e)

    return np.array(merged_o), np.array(merged_e)


def get_ks_critical_value(n):
    """
    Retrieve the critical value for the Kolmogorov-Smirnov test given a sample size.
    Uses hardcoded values for n <= 35 and an approximation for larger n.
    
    Parameters:
    - n (int): sample size
    
    Returns:
    - float: critical value for the KS test
    """
    if n <= 0:
        raise ValueError("Sample size must be greater than zero.")
    if n in ks_critical_values:
        return ks_critical_values[n]
    return 1.36 / np.sqrt(n)  # Use approximation for larger sample sizes

def manual_chi_square(o, e):
    """
    Manually compute the Chi-Squared test statistic after ensuring all expected frequencies are at least 5.

    Parameters:
    o (np.array): observed frequencies
    e (np.array): expected frequencies

    Returns:
    float: Chi-squared statistic
    """
    # Merge intervals if necessary
    if any(f < 5 for f in e):
        o, e = merge_intervals(o, e)

    chi2 = np.sum((o - e) ** 2 / e)
    return chi2


# Funciones para generar los datos aleatorios de las diferentes distriibuciones...

def uniform_generator(a, b, n):
    numeros_aleatorios = []
    for i in range(n):
        numero_aleatorio = a + random.random() * (b - a)
        numeros_aleatorios.append(numero_aleatorio)
    return numeros_aleatorios


def exponential_generator(scale, n):
    numeros_aleatorios = []
    for i in range(n):
        num_random = random.random()
        numero_aleatorio = -scale * math.log(1 - num_random)
        numeros_aleatorios.append(numero_aleatorio)
    return numeros_aleatorios


def normal_generator(mu, sigma, n):
    numeros_aleatorios = []

    while len(numeros_aleatorios) < n:
        numero_aleatorio1 = random.random()
        numero_aleatorio2 = random.random()

        normal1 = (math.sqrt(-2*math.log(numero_aleatorio1)) * math.cos(2*math.pi*numero_aleatorio2)) * sigma + mu
        normal2 = (math.sqrt(-2*math.log(numero_aleatorio2)) * math.cos(2*math.pi*numero_aleatorio1)) * sigma + mu
        
        numeros_aleatorios.append(normal1)
        numeros_aleatorios.append(normal2)
    
    return numeros_aleatorios


def calcularProbObservadas(frecuencias, n):
    probFrecObservadas = np.array(list(map(lambda x: x / n, frecuencias)))
    probFrecObsAc = []
    acumulador = 0
    for i in range(len(probFrecObservadas)):
        acumulador += probFrecObservadas[i]
        probFrecObsAc.append(acumulador)
    return probFrecObsAc

import numpy as np

def ks_statistic(observed_freq, expected_freq):
    """
    Calculate the Kolmogorov-Smirnov statistic.
    
    Parameters:
    observed_freq (list or np.array): The observed frequencies.
    expected_freq (list or np.array): The expected frequencies.
    
    Returns:
    float: The Kolmogorov-Smirnov statistic.
    """
    # Convert frequencies to cumulative probabilities
    cum_observed = np.cumsum(observed_freq) / np.sum(observed_freq)
    cum_expected = np.cumsum(expected_freq) / np.sum(expected_freq)
    
    # Calculate the KS statistic
    ks = np.max(np.abs(cum_observed - cum_expected))
    
    return ks


def calcularKs(probfrecObsAc, probfrecEspAc, distribucion):
    probfrecObsAc = np.array(probfrecObsAc)
    probfrecEspAc = np.array(probfrecEspAc)
    if distribucion == "normal" or distribucion == "exponencial":
        ksCalculado = np.max(np.abs(probfrecObsAc - probfrecEspAc[:-1]))
    else:
        ksCalculado = np.max(np.abs(probfrecObsAc - probfrecEspAc))
    return ksCalculado


@app.route("/generate", methods=["POST"])
def generate_numbers():
    print("Petición recibida:", request.json)
    try:
        content = request.json
        n = int(content["muestra"])
        distribucion = content["distribucion"]
        params = content["params"]
        intervalos = int(content["intervalos"])
        ks_critical = get_ks_critical_value(n)

        if distribucion == "uniforme":
            a = float(params.get("a", 0))
            b = float(params.get("b", 1))
            if a >= b:
                raise ValueError("'a' debe ser menor a 'b'.")
            
            # Generación variables aleatorias uniformes...
            data = uniform_generator(a, b, n)
            #Calcular las frecuencias esperadas de los intervalos
            frecuenciasEsperadas = np.full(intervalos, n / intervalos)
            probFrecuenciasEsp = np.array(list(map(lambda x: x / n, frecuenciasEsperadas)))
            chi_critical = chi_squared_critical_value(intervalos - 1,0.05)
            # Crear array con las probabilidades esperadas acumuladas
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
            scale = 1/lambd
            chi_critical = chi_squared_critical_value(intervalos - 2,0.05)

            # Generar variables aleatorias exponenciales negativas...
            data = exponential_generator(scale, n)
            upper_bound = stats.expon.ppf(0.99, scale=scale)  # 99th percentile
            bin_edges = np.linspace(0, upper_bound, intervalos + 1)

            # Calcular la probabilidad acumulativa de cada uno de los intervalos...
            probFrecuenciasEspAc = stats.expon.cdf(bin_edges, scale=scale)
            # Calcular frecuencias esperadas de cada intervalo...
            # Diff crea un array con las diferencias entre elementos consecutivos de un array... 
            probFrecuenciasEsp = np.diff(probFrecuenciasEspAc)
            frecuenciasEsperadas = probFrecuenciasEsp * n

        elif distribucion == "normal":
            mu = float(params.get("mu", 0))
            sigma = float(params.get("sigma", 1))
            if sigma <= 0:
                raise ValueError("Sigma debe ser positivo.")
            chi_critical = chi_squared_critical_value(intervalos - 3,0.05)
            
            # Generar variables aleatorias normales...
            data = normal_generator(mu, sigma, n)

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
        counts, bins, patches = ax.hist(data, bins=bin_edges, color="blue", edgecolor="black")
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        plt.title("Histogram")

        # Histograma a PNG
        img = io.BytesIO()
        plt.savefig(img, format="png")
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf8")

        # Ajuste de Frecuencias esperadas para coincidir frecuencia observada
        frecuenciasEsperadas *= (counts.sum() / frecuenciasEsperadas.sum())

        # Prueba de bondad de ajuste
        try:
            chi2_stat = manual_chi_square(counts, frecuenciasEsperadas)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        chi2_stat_scipy, chi2_p_scipy = stats.chisquare(counts, f_exp=frecuenciasEsperadas)

        # Print both statistics for comparison
        print("Manual Chi-Squared Statistic:", chi2_stat)
        print("Scipy Chi-Squared Statistic:", chi2_stat_scipy)
        print("chi-critical: ", chi_critical)
        print("ks-critical: ", ks_critical)

        # Calcular Ks..
        probFrecuenciasObsAc = calcularProbObservadas(counts, n)
        ksCalculado = calcularKs(probFrecuenciasObsAc,probFrecuenciasEspAc, distribucion)
        ksCalculadoGPT= ks_statistic(counts, frecuenciasEsperadas)        
        print(ksCalculado, ksCalculadoGPT)
        

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
            "number_of_bins": num_bins,
            "bin_amplitude": np.round(bin_amplitude, 4),
            "mean": np.round(data_mean, 4),
            "chi_critical": np.round(chi_critical, 4),
            "ks_critical": np.round(ks_critical, 4),
            }        

        return jsonify(result)
        

    except ValueError as e:
        return jsonify({"error": str(e)}), 400  

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)