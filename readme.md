# Aplicación Web para Generación de Números Aleatorios

Esta aplicación web genera una serie de números aleatorios basada en distribuciones seleccionadas por el usuario y proporciona análisis estadísticos y visualizaciones de estos números.

## Funcionalidades

- Generación de números aleatorios desde distribuciones Uniforme, Exponencial y Normal.
- Visualización de la distribución de estos números a través de histogramas.
- Realización y visualización de resultados de pruebas Chi-cuadrado y Kolmogorov-Smirnov.

## Instalación

Sigue estos pasos para configurar el entorno del proyecto y ejecutar la aplicación.

### Configuración

1. **Clonar el Repositorio**

   ```bash
   git clone https://github.com/TomiMalamud/simulacion.git
   ```

2. **Crear un Entorno Virtual** 

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
   ```

   También se puede hacer con ctrl+shift+p y seleccionar Python: Create Environment > Venv y seguir los pasos

3. **Instalar Dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la Aplicación**

   ```bash
   python app.py
   ```

   Esto iniciará el servidor Flask en `http://127.0.0.1:5000/`. Hacé click en el link que sale en la terminal

## Uso

1. **Seleccionar el Tipo de Distribución** - Elige entre Uniforme, Exponencial o Normal.
2. **Introducir los Parámetros Requeridos** para la distribución elegida.
3. **Especificar el Tamaño de la Muestra** - El número de números aleatorios a generar.
4. **Elegir el Número de Intervalos** para el histograma.
5. **Haz clic en 'Generar'** para ver el histograma y los resultados de las pruebas estadísticas.

Los números generados y su histograma se mostrarán en la página, junto con los resultados de las pruebas Chi-cuadrado y Kolmogorov-Smirnov.
