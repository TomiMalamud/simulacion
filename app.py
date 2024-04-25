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

def manual_chi_square(o, e):
    """
    Manually compute the Chi-Squared test statistic.
    o: observed frequencies (counts from histogram)
    e: expected frequencies
    """
    if any(f < 5 for f in e):  # Chi-squared test requirement
        raise ValueError("All expected frequencies must be at least 5")
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


@app.route("/generate", methods=["POST"])
def generate_numbers():
    print("Petición requisido:", request.json)
    try:
        content = request.json
        n = int(content["muestra"])
        distribucion = content["distribucion"]
        params = content["params"]
        intervalos = int(content["intervalos"])

        if distribucion == "uniforme":
            a = float(params.get("a", 0))
            b = float(params.get("b", 1))
            if a >= b:
                raise ValueError("'a' debe ser menor a 'b'.")
            
            # Generación variables aleatorias uniformes...
            data = uniform_generator(a, b, n)
            expected_freq = np.full(intervalos, n / intervalos)
            bin_edges = np.linspace(a, b, intervalos + 1)

        elif distribucion == "exponencial":
            lambd = float(params.get("lambda", 1))
            if lambd <= 0:
                raise ValueError("Lambda debe ser positivo.")
            scale = 1/lambd

            # Generar variables aleatorias exponenciales negativas...
            data = exponential_generator(scale, n)
            upper_bound = stats.expon.ppf(0.99, scale=scale)  # 99th percentile
            bin_edges = np.linspace(0, upper_bound, intervalos + 1)
            cdf_values = stats.expon.cdf(bin_edges, scale=scale)
            expected_freq = np.diff(cdf_values) * n

        elif distribucion == "normal":
            mu = float(params.get("mu", 0))
            sigma = float(params.get("sigma", 1))
            if sigma <= 0:
                raise ValueError("Sigma debe ser positivo.")
            
            # Generar variables aleatorias normales...
            data = normal_generator(mu, sigma, n)
            lower_bound = stats.norm.ppf(0.005, mu, sigma)  
            upper_bound = stats.norm.ppf(0.995, mu, sigma)  
            bin_edges = np.linspace(lower_bound, upper_bound, intervalos + 1)
            cdf_values = stats.norm.cdf(bin_edges, mu, sigma)
            expected_freq = np.diff(cdf_values) * n
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
        expected_freq *= (counts.sum() / expected_freq.sum())

        # Prueba de bondad de ajuste
        try:
            chi2_stat = manual_chi_square(counts, expected_freq)
            chi2_p = 1 - stats.chi2.cdf(chi2_stat, df=len(counts) - 1 - len(params))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        chi2_stat_scipy, chi2_p_scipy = stats.chisquare(counts, f_exp=expected_freq)

        # Print both statistics for comparison
        print("Manual Chi-Squared Statistic:", chi2_stat)
        print("Scipy Chi-Squared Statistic:", chi2_stat_scipy)


        # Parametrización de KS basado en la distribución
        if distribucion == "uniforme":
            ks_stat, ks_p = stats.kstest(data, 'uniform', args=(a, b-a))
        elif distribucion == "exponencial":
            ks_stat, ks_p = stats.kstest(data, 'expon', args=(0, 1/lambd))
        elif distribucion == "normal":
            ks_stat, ks_p = stats.kstest(data, 'norm', args=(mu, sigma))
        else:
            ks_stat, ks_p = None, None  # Default or error handling case

        data_min = np.min(data)
        data_max = np.max(data)
        data_range = data_max - data_min
        num_bins = int(np.sqrt(n)) + 1
        bin_amplitude = data_range / num_bins
        data_mean = np.mean(data)        
        
        result = {
            "histogram": "data:image/png;base64,{}".format(plot_url),
            "chi_square_stat": np.round(chi2_stat, 4),
            "chi_square_p": np.round(chi2_p, 4),
            "kolmogorov_stat": np.round(ks_stat, 4),
            "kolmogorov_p": np.round(ks_p, 4),
            "data": data.tolist(),
            "sample_size": n,
            "min": np.round(data_min, 4),
            "max": np.round(data_max, 4),
            "range": np.round(data_range, 4),
            "number_of_bins": num_bins,
            "bin_amplitude": np.round(bin_amplitude, 4),
            "mean": np.round(data_mean, 4),
            }        
        print(data.tolist())
        return jsonify(result)
        

    except ValueError as e:
        return jsonify({"error": str(e)}), 400  

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)