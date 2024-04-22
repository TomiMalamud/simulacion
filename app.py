from flask import Flask, request, render_template, jsonify
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib
import io
import base64

matplotlib.use("Agg")
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_numbers():
    print("Request received:", request.json)
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
                raise ValueError("For a uniform distribution, 'a' must be less than 'b'.")
            data = np.random.uniform(a, b, n)
            expected_freq = np.full(intervalos, n / intervalos)
            bin_edges = np.linspace(a, b, intervalos + 1)
        elif distribucion == "exponencial":
            lambd = float(params.get("lambda", 1))
            if lambd <= 0:
                raise ValueError("Lambda must be positive.")
            data = np.random.exponential(1 / lambd, n)
            scale = 1/lambd
            upper_bound = stats.expon.ppf(0.99, scale=scale)  # 99th percentile
            bin_edges = np.linspace(0, upper_bound, intervalos + 1)
            cdf_values = stats.expon.cdf(bin_edges, scale=scale)
            expected_freq = np.diff(cdf_values) * n
        elif distribucion == "normal":
            mu = float(params.get("mu", 0))
            sigma = float(params.get("sigma", 1))
            if sigma <= 0:
                raise ValueError("Sigma must be positive.")
            data = np.random.normal(mu, sigma, n)
            lower_bound = stats.norm.ppf(0.005, mu, sigma)  
            upper_bound = stats.norm.ppf(0.995, mu, sigma)  
            bin_edges = np.linspace(lower_bound, upper_bound, intervalos + 1)
            cdf_values = stats.norm.cdf(bin_edges, mu, sigma)
            expected_freq = np.diff(cdf_values) * n
        else:
            raise ValueError("Invalid distribution type selected.")

        data = np.round(data, 4)

        # Generar histograma
        fig, ax = plt.subplots()
        counts, bins, patches = ax.hist(data, bins=bin_edges, color="blue", edgecolor="black")
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        plt.title("Histogram")

        # Plot a PNG
        img = io.BytesIO()
        plt.savefig(img, format="png")
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf8")

        # Ajuste de Frecuencias esperadas para coincidir frecuencia observada
        expected_freq *= (counts.sum() / expected_freq.sum())

        # Prueba de bondad de ajuste
        chi2_stat, chi2_p = stats.chisquare(counts, f_exp=expected_freq)
        
        # Parametrización de KS basado en la distribución
        if distribucion == "uniforme":
            ks_stat, ks_p = stats.kstest(data, 'uniform', args=(a, b-a))
        elif distribucion == "exponencial":
            ks_stat, ks_p = stats.kstest(data, 'expon', args=(0, 1/lambd))
        elif distribucion == "normal":
            ks_stat, ks_p = stats.kstest(data, 'norm', args=(mu, sigma))

        return jsonify({
            "histogram": "data:image/png;base64,{}".format(plot_url),
            "chi_square_stat": np.round(chi2_stat, 4),
            "chi_square_p": np.round(chi2_p, 4),
            "kolmogorov_stat": np.round(ks_stat, 4),
            "kolmogorov_p": np.round(ks_p, 4),
            "data": data.tolist(),
        })
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)