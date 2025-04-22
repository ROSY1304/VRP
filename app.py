from flask import Flask, request, render_template
import math
from operator import itemgetter

app = Flask(__name__)

def distancia(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)

def en_ruta(rutas, c):
    for r in rutas:
        if c in r:
            return r
    return None

def peso_ruta(ruta, pedidos):
    return sum(pedidos[c] for c in ruta)

def paquetes_ruta(ruta, pedidos):
    return sum(pedidos[c] for c in ruta)  # Cambié esto para contar los paquetes

def distancia_ruta(ruta, coord, almacen):
    total = distancia(almacen, coord[ruta[0]]) + distancia(coord[ruta[-1]], almacen)
    for i in range(len(ruta) - 1):
        total += distancia(coord[ruta[i]], coord[ruta[i + 1]])
    return total

def combustible_ruta(ruta, coord, almacen, consumo_por_km):
    return distancia_ruta(ruta, coord, almacen) * consumo_por_km

def vrp_voraz(coord, pedidos, almacen, max_carga, max_combustible, consumo_por_km, max_distancia, max_paquetes):
    s = {}
    for c1 in coord:
        for c2 in coord:
            if c1 != c2 and (c2, c1) not in s:
                d_c1_c2 = distancia(coord[c1], coord[c2])
                d_c1_alm = distancia(coord[c1], almacen)
                d_c2_alm = distancia(coord[c2], almacen)
                s[c1, c2] = d_c1_alm + d_c2_alm - d_c1_c2
    s = sorted(s.items(), key=itemgetter(1), reverse=True)

    rutas = []
    for (c1, c2), _ in s:
        rc1 = en_ruta(rutas, c1)
        rc2 = en_ruta(rutas, c2)

        if rc1 is None and rc2 is None:
            nueva = [c1, c2]
            if (peso_ruta(nueva, pedidos) <= max_carga and
                combustible_ruta(nueva, coord, almacen, consumo_por_km) <= max_combustible and
                distancia_ruta(nueva, coord, almacen) <= max_distancia and
                paquetes_ruta(nueva, pedidos) <= max_paquetes):
                rutas.append(nueva)
        elif rc1 is not None and rc2 is None:
            if rc1[0] == c1:
                nueva = [c2] + rc1
            elif rc1[-1] == c1:
                nueva = rc1 + [c2]
            else:
                continue
            if (peso_ruta(nueva, pedidos) <= max_carga and
                combustible_ruta(nueva, coord, almacen, consumo_por_km) <= max_combustible and
                distancia_ruta(nueva, coord, almacen) <= max_distancia and
                paquetes_ruta(nueva, pedidos) <= max_paquetes):
                rutas[rutas.index(rc1)] = nueva
        elif rc1 is None and rc2 is not None:
            if rc2[0] == c2:
                nueva = [c1] + rc2
            elif rc2[-1] == c2:
                nueva = rc2 + [c1]
            else:
                continue
            if (peso_ruta(nueva, pedidos) <= max_carga and
                combustible_ruta(nueva, coord, almacen, consumo_por_km) <= max_combustible and
                distancia_ruta(nueva, coord, almacen) <= max_distancia and
                paquetes_ruta(nueva, pedidos) <= max_paquetes):
                rutas[rutas.index(rc2)] = nueva
        elif rc1 != rc2:
            nueva = rc1 + rc2
            if (peso_ruta(nueva, pedidos) <= max_carga and
                combustible_ruta(nueva, coord, almacen, consumo_por_km) <= max_combustible and
                distancia_ruta(nueva, coord, almacen) <= max_distancia and
                paquetes_ruta(nueva, pedidos) <= max_paquetes):
                rutas.remove(rc1)
                rutas.remove(rc2)
                rutas.append(nueva)

    # Añadir detalles de cada ruta con el total de paquetes repartidos
    rutas_detalles = []
    for ruta in rutas:
        distancia_total = distancia_ruta(ruta, coord, almacen)
        combustible_total = combustible_ruta(ruta, coord, almacen, consumo_por_km)
        paquetes_totales = paquetes_ruta(ruta, pedidos)  # Calcular total de paquetes
        rutas_detalles.append({
            "ruta": " -> ".join(ruta),  # Crear un string legible de las ciudades
            "distancia_total": distancia_total,
            "combustible_total": combustible_total,
            "paquetes_totales": paquetes_totales  # Añadir el total de paquetes
        })

    return rutas_detalles

@app.route("/", methods=["GET", "POST"])
def index():
    rutas = []
    if request.method == "POST":
        ciudades = request.form.getlist("ciudad[]")
        lats = list(map(float, request.form.getlist("lat[]")))
        lons = list(map(float, request.form.getlist("lon[]")))
        pedidos_list = list(map(int, request.form.getlist("pedidos[]")))

        coord = {ciudades[i]: (lats[i], lons[i]) for i in range(len(ciudades))}
        pedidos = {ciudades[i]: pedidos_list[i] for i in range(len(ciudades))}

        almacen = [float(request.form["almacen_lat"]), float(request.form["almacen_lon"])]
        max_carga = float(request.form["max_carga"])
        max_combustible = float(request.form["max_combustible"])
        consumo_por_km = float(request.form["consumo_por_km"])
        max_distancia = float(request.form["max_distancia"])
        max_paquetes = int(request.form["max_paquetes"])

        rutas = vrp_voraz(coord, pedidos, almacen, max_carga, max_combustible, consumo_por_km, max_distancia, max_paquetes)

    return render_template("index.html", rutas=rutas)

if __name__ == "__main__":
    app.run(debug=True)
