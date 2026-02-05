from flask import Flask, render_template, request, jsonify
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# Simulação de times e jogadores
equipes = ["Real Madrid", "Barcelona", "Manchester United", "Liverpool", "Bayern", "PSG"]
jogadores = ["Jogador A", "Jogador B", "Jogador C", "Jogador D", "Jogador E", "Jogador F"]

# Simula últimos 25 jogos para cada time
def gerar_jogos():
    jogos = []
    for i in range(25):
        t1, t2 = random.sample(equipes, 2)
        jogo = {
            "time_casa": t1,
            "time_fora": t2,
            "chutes": random.randint(5,20),
            "chutes_prob": random.randint(60,100),
            "chutes_ao_gol": random.randint(2,15),
            "chutes_ao_gol_prob": random.randint(60,100),
            "gols": random.randint(0,5),
            "gols_prob": random.randint(60,100),
            "faltas": random.randint(5,20),
            "faltas_prob": random.randint(60,100),
            "cartoes": random.randint(0,5),
            "cartoes_prob": random.randint(60,100),
            "laterais": random.randint(0,10),
            "laterais_prob": random.randint(60,100),
            "escanteios": random.randint(0,10),
            "escanteios_prob": random.randint(60,100),
            "tiros_meta": random.randint(0,10),
            "tiros_meta_prob": random.randint(60,100),
            "data": (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "competicao": random.choice(["La Liga", "Premier League", "Bundesliga", "Serie A", "Ligue 1"])
        }
        jogos.append(jogo)
    return jogos

# Simula jogadores
def gerar_jogadores():
    jogs = []
    for j in jogadores:
        jogs.append({
            "nome": j,
            "chutes": random.randint(0,10),
            "chutes_prob": random.randint(60,100),
            "chutes_ao_gol": random.randint(0,8),
            "chutes_ao_gol_prob": random.randint(60,100),
            "faltas": random.randint(0,5),
            "faltas_prob": random.randint(60,100),
            "desarmes": random.randint(0,10),
            "desarmes_prob": random.randint(60,100)
        })
    return jogs

# Dados globais
jogos = gerar_jogos()
jogs = gerar_jogadores()

# Página Inicial
@app.route("/")
def index():
    data_filter = request.args.get("data","")
    comp_filter = request.args.get("competicao","")
    equipe_filter = request.args.get("equipe","")

    # Filtra os jogos
    filtrados = jogos
    if data_filter:
        filtrados = [j for j in filtrados if j["data"]==data_filter]
    if comp_filter:
        filtrados = [j for j in filtrados if j["competicao"]==comp_filter]
    if equipe_filter:
        filtrados = [j for j in filtrados if equipe_filter in [j["time_casa"], j["time_fora"]]]

    # Bingo do Dia (5-7 métricas aleatórias, prob >=75)
    bingo = []
    for j in filtrados:
        for m in ["chutes","chutes_ao_gol","gols","faltas","cartoes","laterais","escanteios","tiros_meta"]:
            prob = j[m+"_prob"]
            if prob>=75:
                bingo.append({"jogo":f"{j['time_casa']} vs {j['time_fora']}",
                              "metric":m,
                              "valor":j[m],
                              "prob":prob})
    bingo = sorted(bingo,key=lambda x: x["prob"], reverse=True)[:7]

    # Melhores Jogos do Dia (6 jogos, métricas prob >=70)
    top_jogos = []
    for j in filtrados:
        if any(j[m+"_prob"]>=70 for m in ["chutes","chutes_ao_gol","gols","faltas","cartoes","laterais","escanteios","tiros_meta"]):
            top_jogos.append(j)
    top_jogos = top_jogos[:6]

    # Competicoes e equipes para filtro
    competicoes = sorted(list(set([j["competicao"] for j in jogos])))
    equipes_list = sorted(list(set([t for j in jogos for t in [j["time_casa"],j["time_fora"]]])))

    return render_template("index.html",
                           bingo=bingo,
                           top_jogos=top_jogos,
                           competicoes=competicoes,
                           equipes=equipes_list,
                           data_filter=data_filter,
                           comp_filter=comp_filter,
                           equipe_filter=equipe_filter)

# Ranking de Equipes
@app.route("/ranking/equipes")
def ranking_equipes():
    ranking = sorted(jogos, key=lambda x: x["gols_prob"], reverse=True)[:5]
    return render_template("ranking_equipes.html", ranking=ranking)

# Ranking de Jogadores
@app.route("/ranking/jogadores")
def ranking_jogadores():
    ranking = sorted(jogs, key=lambda x: x["chutes_prob"], reverse=True)[:5]
    return render_template("ranking_jogadores.html", ranking=ranking)

# H2H
@app.route("/h2h")
def h2h():
    time1 = request.args.get("time1")
    time2 = request.args.get("time2")
    h2h_jogos = []

    # Simula 10 jogos H2H entre os times
    for _ in range(10):
        j = {
            "chutes": random.randint(5,20),
            "chutes_ao_gol": random.randint(2,15),
            "gols1": random.randint(0,5),
            "gols2": random.randint(0,5),
            "faltas": random.randint(5,20),
            "cartoes": random.randint(0,5),
            "laterais": random.randint(0,10),
            "escanteios": random.randint(0,10),
            "tiros_meta": random.randint(0,10)
        }
        h2h_jogos.append(j)

    return jsonify({"time1":time1,"time2":time2,"jogos":h2h_jogos})

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
