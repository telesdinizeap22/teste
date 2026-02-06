import os
import random
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# ======================
# DADOS SIMULADOS
# ======================

equipes = [
    "Real Madrid", "Barcelona", "Manchester United",
    "Liverpool", "Bayern", "PSG"
]

jogadores = [
    "Jogador A", "Jogador B", "Jogador C",
    "Jogador D", "Jogador E", "Jogador F"
]

# ----------------------
# GERA JOGOS
# ----------------------
def gerar_jogos():
    jogos = []
    for i in range(25):
        t1, t2 = random.sample(equipes, 2)
        jogos.append({
            "time_casa": t1,
            "time_fora": t2,
            "chutes": random.randint(5, 20),
            "chutes_prob": random.randint(60, 100),
            "chutes_ao_gol": random.randint(2, 15),
            "chutes_ao_gol_prob": random.randint(60, 100),
            "gols": random.randint(0, 5),
            "gols_prob": random.randint(60, 100),
            "faltas": random.randint(5, 20),
            "faltas_prob": random.randint(60, 100),
            "cartoes": random.randint(0, 5),
            "cartoes_prob": random.randint(60, 100),
            "laterais": random.randint(0, 10),
            "laterais_prob": random.randint(60, 100),
            "escanteios": random.randint(0, 10),
            "escanteios_prob": random.randint(60, 100),
            "tiros_meta": random.randint(0, 10),
            "tiros_meta_prob": random.randint(60, 100),
            "data": (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "competicao": random.choice([
                "La Liga", "Premier League",
                "Bundesliga", "Serie A", "Ligue 1"
            ])
        })
    return jogos


# ----------------------
# GERA JOGADORES
# ----------------------
def gerar_jogadores():
    lista = []
    for j in jogadores:
        lista.append({
            "nome": j,
            "chutes": random.randint(0, 10),
            "chutes_prob": random.randint(60, 100),
            "chutes_ao_gol": random.randint(0, 8),
            "chutes_ao_gol_prob": random.randint(60, 100),
            "faltas": random.randint(0, 5),
            "faltas_prob": random.randint(60, 100),
            "desarmes": random.randint(0, 10),
            "desarmes_prob": random.randint(60, 100)
        })
    return lista


# ======================
# DADOS GLOBAIS
# ======================
jogos = gerar_jogos()
jogs = gerar_jogadores()

# ======================
# PÁGINA INICIAL
# ======================
@app.route("/")
def home():
    return render_template("home.html")

# ======================
# SUGESTÃO DE APOSTA (ANTIGO INDEX)
# ======================
@app.route("/sugestoes")
def sugestoes():
    data_filter = request.args.get("data", "")
    comp_filter = request.args.get("competicao", "")
    equipe_filter = request.args.get("equipe", "")

    filtrados = jogos

    if data_filter:
        filtrados = [j for j in filtrados if j["data"] == data_filter]
    if comp_filter:
        filtrados = [j for j in filtrados if j["competicao"] == comp_filter]
    if equipe_filter:
        filtrados = [
            j for j in filtrados
            if equipe_filter in (j["time_casa"], j["time_fora"])
        ]

    metricas = [
        "chutes", "chutes_ao_gol", "gols", "faltas",
        "cartoes", "laterais", "escanteios", "tiros_meta"
    ]

    # Bingo do Dia
    bingo = []
    for j in filtrados:
        for m in metricas:
            if j[f"{m}_prob"] >= 75:
                bingo.append({
                    "jogo": f"{j['time_casa']} vs {j['time_fora']}",
                    "metric": m,
                    "valor": j[m],
                    "prob": j[f"{m}_prob"]
                })

    bingo = sorted(bingo, key=lambda x: x["prob"], reverse=True)[:7]

    # Melhores jogos
    top_jogos = filtrados[:6]

    competicoes = sorted(set(j["competicao"] for j in jogos))
    equipes_list = sorted(
        set(t for j in jogos for t in (j["time_casa"], j["time_fora"]))
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
    metricas = [
        "chutes", "chutes_ao_gol", "gols", "faltas",
        "cartoes", "laterais", "escanteios", "tiros_meta"
    ]

    ranking_data = {}

    for m in metricas:
        lista = []
        for j in jogos:
            lista.append({
                "time_casa": j["time_casa"],
                m: j[m],
                "prob": j[f"{m}_prob"]
            })

        ranking_data[m] = sorted(
            lista, key=lambda x: x["prob"], reverse=True
        )[:10]

    return render_template(
        "ranking_equipes.html",
        ranking_equipes=ranking_data
    )

# ======================
# RANKING DE JOGADORES
# ======================
@app.route("/ranking/jogadores")
def ranking_jogadores():
    metricas = ["chutes", "chutes_ao_gol", "faltas", "desarmes"]

    ranking_data = {}

    for m in metricas:
        lista = []
        for j in jogs:
            lista.append({
                "nome": j["nome"],
                m: j[m],
                "prob": j[f"{m}_prob"]
            })

        ranking_data[m] = sorted(
            lista, key=lambda x: x["prob"], reverse=True
        )[:10]

    return render_template(
        "ranking_jogadores.html",
        ranking_jogadores=ranking_data
    )

# ======================
# H2H
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
    app.run(debug=True)
