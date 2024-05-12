from flask import Blueprint, render_template, request, jsonify
from .utils_tp2 import *
from .utils_tp3 import *

app_views = Blueprint("app_views", __name__)


@app_views.route("/")
def index():
    return render_template("index.html")


@app_views.route("/tp2")
def tp2():
    return render_template("tp2.html")


@app_views.route("/generate", methods=["POST"])
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
            upper_bound = stats.expon.ppf(0.99, scale=scale)
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
        plt.style.use("dark_background")

        fig, ax = plt.subplots()

        counts, bins, patches = ax.hist(
            data, bins=bin_edges, color="orange", edgecolor="black"
        )

        ax.set_xlabel("Valor")
        ax.set_ylabel("Frecuencia")
        plt.title("Histograma")

        # Histograma a PNG
        img = io.BytesIO()
        plt.savefig(img, format="png", facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf8")

        # Ajuste de Frecuencias esperadas para coincidir frecuencia observada
        frecuenciasEsperadas *= counts.sum() / frecuenciasEsperadas.sum()

        # Prueba de bondad de ajuste
        try:
            chi_squared_table = combine_chi_squared_rows(
                bin_edges, counts, frecuenciasEsperadas
            )
            chi2_stat = sum(row["c"] for row in chi_squared_table)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        chi2_stat_scipy, chi2_p_scipy = stats.chisquare(
            counts, f_exp=frecuenciasEsperadas
        )
        print(
            "Chi2 manual:", chi2_stat, "Chi2 scipy:", chi2_stat_scipy
        )  # falla si n < 50
        ksCalculado = estadistico_ks(counts, frecuenciasEsperadas)

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


# @app_views.route("/montecarlo", methods=["POST"])
# def montecarlo():
