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
            a = float(params.get("a", 0))  # Default a 0
            b = float(params.get("b", 1))  # Default b 1
            if a >= b:
                raise ValueError(
                    "Para distribución uniforme, 'a' debe ser menor a 'b'."
                )
            data = np.random.uniform(a, b, n)
            expected_freq = np.full(intervalos, n / intervalos)
        elif distribucion == "exponencial":
            lambd = float(params.get("lambda", 1))  # Default lambda 1
            if lambd <= 0:
                raise ValueError("Lambda debe ser positivo.")
            data = np.random.exponential(1 / lambd, n)
            bin_edges = np.linspace(data.min(), data.max(), intervalos + 1)
            cdf_values = stats.expon.cdf(bin_edges, scale=1/lambd)
            expected_freq = np.diff(cdf_values) * n

        elif distribucion == "normal":
            mu = float(params.get("mu", 0))  # Default mu 0
            sigma = float(params.get("sigma", 1))  # Default sigma 1
            if sigma <= 0:
                raise ValueError("Sigma debe ser positivo.")
            data = np.random.normal(mu, sigma, n)
            bin_edges = np.linspace(data.min(), data.max(), intervalos + 1)
            cdf_values = stats.norm.cdf(bin_edges, mu, sigma)
            expected_freq = np.diff(cdf_values) * n
            
        else:
            raise ValueError("Error en la selección de tipo de distribución.")

        data = np.round(data, 4)

        # Generar histograma
        fig, ax = plt.subplots()
        counts, bins, patches = ax.hist(
            data, bins=intervalos, color="blue", edgecolor="black"
        )
        ax.set_xlabel("Valor")
        ax.set_ylabel("Frecuencia")
        plt.title("Histograma")

        # Gráfico a PNG
        img = io.BytesIO()
        plt.savefig(img, format="png")
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf8")
        expected_freq *= (counts.sum() / expected_freq.sum())

        # Prueba de bondad de ajuste
        chi2_stat, chi2_p = stats.chisquare(counts, f_exp=expected_freq)
        d_stat, ks_p = stats.kstest(data, "norm", args=(np.mean(data), np.std(data)))

        return jsonify(
            {
                "histogram": "data:image/png;base64,{}".format(plot_url),
                "chi_square_stat": np.round(chi2_stat, 4),
                "chi_square_p": np.round(chi2_p, 4),
                "kolmogorov_stat": np.round(d_stat, 4),
                "kolmogorov_p": np.round(ks_p, 4),
                "data": data.tolist(),
            }
        )
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False)
