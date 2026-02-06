import os
import random
from flask import Flask, render_template, request, jsonify

from data.cache import TTLCache
from data.provider_fake import FakeProvider

# ======================
# CONFIG / PROVIDER
# ======================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# Cache TTL configurável via ambiente (Render: Environment Variables)
# Ex: CACHE_TTL=60
cache = TTLCache()
provider = FakeProvider(cache=cache, ttl_seconds=int(os.getenv("CACHE_TTL", "60")))


def _flatten_jogo(jogo: dict) -> dict:
    """
    Compatibilidade com templates antigos:
    Se vier no formato novo (com jogo["metricas"]), copia as métricas para o topo.
    Assim continua existindo: j["chutes"], j["chutes_prob"], etc.
    """
    metricas = jogo.get("metricas")
    if isinstance(metricas, dict):
        for k, v in metricas.items():
            if k not in jogo:
                jogo[k] = v
    return jogo


def _get_jogos_flat(days: int = 25) -> list[dict]:
    jogos_raw = provider.get_jogos(days=days)
    return [_flatten_jogo(dict(j)) for j in jogos_raw]


# ======================
# PÁGINA INICIAL
# ======================
@app.route("/")
def home():
    jogos = _get_jogos_flat(days=25)
    return render_template("home.html", jogos=jogos)


# ======================
# SUGESTÃO DE APOSTA (ANTIGO INDEX)
# ======================
@app.route("/sugestoes")
def sugestoes():
    jogos = _get_jogos_flat(days=25)

    data_filter = request.args.get("data", "")
    comp_filter = request.args.get("competicao", "")
    equipe_filter = request.args.get("equipe", "")

    filtrados = jogos

    if data_filter:
        filtrados = [j for j in filtrados if j.get("data") == data_filter]
    if comp_filter:
        filtrados = [j for j in filtrados if j.get("competicao") == comp_filter]
    if equipe_filter:
        filtrados = [
            j for j in filtrados
            if equipe_filter in (j.get("time_casa"), j.get("time_fora"))
        ]

    metricas = [
        "chutes", "chutes_ao_gol", "gols", "faltas",
        "cartoes", "laterais", "escanteios", "tiros_meta"
    ]

    # Bingo do Dia
    bingo = []
    for j in filtrados:
        for m in metricas:
            prob_key = f"{m}_prob"
            prob = j.get(prob_key)
            if prob is not None and prob >= 75:
                bingo.append({
                    "jogo": f"{j.get('time_casa')} vs {j.get('time_fora')}",
                    "metric": m,
                    "valor": j.get(m),
                    "prob": prob
                })

    bingo = sorted(bingo, key=lambda x: x["prob"], reverse=True)[:7]

    # Melhores jogos
    top_jogos = filtrados[:6]

    competicoes = sorted(set(j.get("competicao") for j in jogos if j.get("competicao")))
    equipes_list = sorted(
        set(t for j in jogos for t in (j.get("time_casa"), j.get("time_fora")) if t)
    )

    return render_template(
        "index.html",
        bingo=bingo,
        top_jogos=top_jogos,
        competicoes=competicoes,
        equipes=equipes_list,
        data_filter=data_filter,
        comp_filter=comp_filter,
        equipe_filter=equipe_filter
    )


# ======================
# RANKING DE EQUIPES
# ======================
@app.route("/ranking/equipes")
def ranking_equipes():
    jogos = _get_jogos_flat(days=25)

    metricas = [
        "chutes", "chutes_ao_gol", "gols", "faltas",
        "cartoes", "laterais", "escanteios", "tiros_meta"
    ]

    ranking_data = {}

    for m in metricas:
        lista = []
        prob_key = f"{m}_prob"
        for j in jogos:
            lista.append({
                "time_casa": j.get("time_casa"),
                m: j.get(m),
                "prob": j.get(prob_key)
            })

        ranking_data[m] = sorted(
            lista,
            key=lambda x: (x["prob"] if x["prob"] is not None else -1),
            reverse=True
        )[:10]

    return render_template(
        "ranking_equipes.html",
        ranking_equipes=ranking_data
    )


# ======================
# RANKING DE JOGADORES (MIGRADO PARA PROVIDER ✅)
# ======================
@app.route("/ranking/jogadores")
def ranking_jogadores():
    jogs = provider.get_ranking_jogadores()

    metricas = ["chutes", "chutes_ao_gol", "faltas", "desarmes"]
    ranking_data = {}

    for m in metricas:
        lista = []
        for j in jogs:
            lista.append({
                "nome": j.get("nome"),
                m: j.get(m),
                "prob": j.get(f"{m}_prob")
            })

        ranking_data[m] = sorted(
            lista,
            key=lambda x: (x["prob"] if x["prob"] is not None else -1),
            reverse=True
        )[:10]

    return render_template(
        "ranking_jogadores.html",
        ranking_jogadores=ranking_data
    )


# ======================
# H2H (SIMULADO)
# ======================
@app.route("/h2h")
def h2h():
    time1 = request.args.get("time1")
    time2 = request.args.get("time2")

    jogos_h2h = []
    for _ in range(10):
        jogos_h2h.append({
            "chutes": random.randint(5, 20),
            "chutes_ao_gol": random.randint(2, 15),
            "gols1": random.randint(0, 5),
            "gols2": random.randint(0, 5),
            "faltas": random.randint(5, 20),
            "cartoes": random.randint(0, 5),
            "laterais": random.randint(0, 10),
            "escanteios": random.randint(0, 10),
            "tiros_meta": random.randint(0, 10)
        })

    return jsonify({
        "time1": time1,
        "time2": time2,
        "jogos": jogos_h2h
    })


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug)
