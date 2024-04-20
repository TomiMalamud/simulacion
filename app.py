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
            a = float(params.get("a", 0))  # Default a to 0 if not provided
            b = float(params.get("b", 1))  # Default b to 1 if not provided
            if a >= b:
                raise ValueError(
                    "For a uniforme distribucion, 'a' must be less than 'b'."
                )
            data = np.random.uniform(a, b, n)
        elif distribucion == "exponencial":
            lambd = float(
                params.get("lambda", 1)
            )  # Default lambda to 1 if not provided
            if lambd <= 0:
                raise ValueError(
                    "Lambda must be positive for exponential distribucion."
                )
            data = np.random.exponential(1 / lambd, n)
        elif distribucion == "normal":
            mu = float(params.get("mu", 0))  # Default mu to 0 if not provided
            sigma = float(params.get("sigma", 1))  # Default sigma to 1 if not provided
            if sigma <= 0:
                raise ValueError("Sigma must be positive for normal distribucion.")
            data = np.random.normal(mu, sigma, n)
        else:
            raise ValueError("Unsupported distribucion type specified.")

        data = np.round(data, 4)

        # Generate histogram
        fig, ax = plt.subplots()
        counts, bins, patches = ax.hist(
            data, bins=intervalos, color="blue", edgecolor="black"
        )
        ax.set_xlabel("Valor")
        ax.set_ylabel("Frecuencia")
        plt.title("Histograma")

        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format="png")
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf8")

        # Goodness-of-fit tests
        chi2_stat, chi2_p = stats.chisquare(counts)
        d_stat, ks_p = stats.kstest(data, "norm", args=(np.mean(data), np.std(data)))

        return jsonify(
            {
                "histogram": "data:image/png;base64,{}".format(plot_url),
                "chi_square_stat": np.round(chi2_stat, 4),
                "chi_square_p": np.round(chi2_p, 4),
                "kolmogorov_stat": np.round(d_stat, 4),
                "kolmogorov_p": np.round(ks_p, 4),
                "data": data.tolist(),  # Include the data series in the response
            }
        )
    except Exception as e:
        print(e)  # Print error message to stdout
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False)
