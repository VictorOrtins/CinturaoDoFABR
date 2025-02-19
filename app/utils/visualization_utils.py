from datetime import datetime

import matplotlib.colors as mcolors
import pandas as pd

import plotly.express as px

def get_cores(teams_df, x):
    cores = teams_df.set_index('Nome').loc[x, 'Cor Primária'].tolist()
    cores = [mcolors.to_hex(c) for c in cores]

    return cores

def get_teams_urls(teams_df, x):
    urls = teams_df.set_index('Nome').loc[x, 'URL da Imagem'].tolist()

    return urls

def get_most_cinturao_defenses(games_df, teams_df):
    defensores_de_titulo = games_df['Defensor do Título'].value_counts().sort_values(ascending=False)[:10]
    defensores_de_titulo = defensores_de_titulo[defensores_de_titulo.index != ' - '][:10]

    x = defensores_de_titulo.index.to_list()
    y = [int(defesa) for defesa in list(defensores_de_titulo.values)]

    plot_df = pd.DataFrame({'Times': x, 'Defesas': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Defesas', y='Times', color="Times", color_discrete_sequence=cores, orientation='h').update_layout(template='seaborn', showlegend=False)

    return fig

def get_most_cinturao_wins(games_df, teams_df):
    vencedores_do_titulo = games_df[games_df['Vencedor'] != games_df['Defensor do Título']]['Vencedor'].value_counts().sort_values(ascending=False)[:10]

    x = vencedores_do_titulo.index.to_list()
    y = [int(defesa) for defesa in list(vencedores_do_titulo.values)]

    plot_df = pd.DataFrame({'Times': x, 'Conquistas': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Conquistas', y='Times', color='Times', color_discrete_sequence=cores, orientation='h').update_layout(template='seaborn', showlegend=False)
    return fig

def get_teams_with_most_games(games_df, teams_df):
    valendo_cinturao = games_df['Mandante'].value_counts().add(games_df['Visitante'].value_counts(), fill_value=0).sort_values(ascending=False).astype(int)[:10]

    x = valendo_cinturao.index.to_list()
    y = valendo_cinturao.to_list()

    plot_df = pd.DataFrame({'Times': x, 'Partidas': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Partidas', y='Times', color='Times', color_discrete_sequence=cores, orientation='h').update_layout(template='seaborn', showlegend=False)
    return fig

def get_teams_with_most_losses(games_df, teams_df):
    mandantes_perderam_jogo_titulo = games_df[games_df['Vencedor'] != games_df['Mandante']]
    visitantes_perderam_jogo_titulo = games_df[games_df['Vencedor'] != games_df['Visitante']]

    mandantes_perderam_jogo_titulo = mandantes_perderam_jogo_titulo['Mandante']
    visitantes_perderam_jogo_titulo = visitantes_perderam_jogo_titulo['Visitante']

    perderam_jogo_titulo = pd.concat([mandantes_perderam_jogo_titulo, visitantes_perderam_jogo_titulo], ignore_index=True)

    perderam_jogo_titulo = perderam_jogo_titulo.value_counts().sort_values(ascending=False)[:10]


    x = perderam_jogo_titulo.index.to_list()
    y = perderam_jogo_titulo.values

    plot_df = pd.DataFrame({'Times': x, 'Derrotas': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Derrotas', y='Times', color='Times', color_discrete_sequence=cores, orientation='h').update_layout(template='seaborn', showlegend=False)
    return fig

def get_teams_with_most_cinturao_losses(games_df, teams_df):
    perdedores_do_titulo: pd.Series = games_df[(games_df['Vencedor'] != games_df['Defensor do Título'])]['Defensor do Título'].value_counts().sort_values(ascending=False)
    perdedores_do_titulo = perdedores_do_titulo[perdedores_do_titulo.index != ' - '][:10]

    x = perdedores_do_titulo.index.to_list()
    y = [int(defesa) for defesa in list(perdedores_do_titulo.values)]


    plot_df = pd.DataFrame({'Times': x, 'Derrotas': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Derrotas', y='Times', color='Times', color_discrete_sequence=cores, orientation='h').update_layout(template='seaborn', showlegend=False)
    return fig

def get_teams_with_most_days_with_cinturao(games_df, teams_df):
    resultados = []

    ultimo_vencedor = games_df['Vencedor'].iloc[-1]

    for vencedor in games_df['Vencedor'].value_counts().index:
        cinturao_games_by_team = games_df[ (games_df['Vencedor'] == vencedor) | (games_df['Defensor do Título'] == vencedor) ].reset_index(drop=True)

        dias_com_cinturao = 0
        data_ultima_vitoria = None
        formato_data = '%Y-%m-%d %H:%M:%S'

        for _, row in cinturao_games_by_team.iterrows():
            if row['Vencedor'] == vencedor:
                if data_ultima_vitoria is None:
                    data_ultima_vitoria = datetime.strptime(row['Data'], formato_data)
                else:
                    data_vitoria = datetime.strptime(row['Data'], formato_data)
                    dias_com_cinturao += (data_vitoria - data_ultima_vitoria).days
                    data_ultima_vitoria = data_vitoria

            else:
                data_derrota = datetime.strptime(row['Data'], formato_data)
                dias_com_cinturao += (data_derrota - data_ultima_vitoria).days

                data_ultima_vitoria = None

        if vencedor == ultimo_vencedor:
            data_hoje = datetime.strptime(datetime.now().strftime(formato_data), formato_data)
            dias_com_cinturao += (data_hoje - data_ultima_vitoria).days

        resultados.append({'Time': vencedor, 'Dias': dias_com_cinturao})

    dias_com_titulo = pd.DataFrame(resultados)

    dias_com_titulo = dias_com_titulo.sort_values(by=['Dias'], ascending=False)[:10]

    x = dias_com_titulo['Time'].to_list()
    y = dias_com_titulo['Dias'].to_list()

    plot_df = pd.DataFrame({'Times': x, 'Dias': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Dias', y='Times', color='Times', color_discrete_sequence=cores, orientation='h').update_layout(template='seaborn', showlegend=False)

    return fig

def get_teams_with_most_consecutive_days_with_cinturao(games_df, teams_df):
    resultados = []

    ultimo_vencedor = games_df['Vencedor'].iloc[-1]


    for vencedor in games_df['Vencedor'].value_counts().index:
        cinturao_games_by_team = games_df[ (games_df['Vencedor'] == vencedor) | (games_df['Defensor do Título'] == vencedor) ].reset_index(drop=True)

        dias_com_cinturao = 0
        data_ultima_vitoria = None
        formato_data = '%Y-%m-%d %H:%M:%S'
        dias_com_cinturao_max = 0

        for _, row in cinturao_games_by_team.iterrows():
            if row['Vencedor'] == vencedor:
                if data_ultima_vitoria is None:
                    data_ultima_vitoria = datetime.strptime(row['Data'], formato_data)
                else:
                    data_vitoria = datetime.strptime(row['Data'], formato_data)
                    dias_com_cinturao += (data_vitoria - data_ultima_vitoria).days
                    data_ultima_vitoria = data_vitoria

            else:
                data_derrota = datetime.strptime(row['Data'], formato_data)
                dias_com_cinturao += (data_derrota - data_ultima_vitoria).days

                if dias_com_cinturao > dias_com_cinturao_max:
                    dias_com_cinturao_max = dias_com_cinturao

                dias_com_cinturao = 0

                data_ultima_vitoria = None

        if vencedor == ultimo_vencedor:
            data_hoje = datetime.strptime('2025-01-25 18:00:00', formato_data)
            dias_com_cinturao_max += (data_hoje - data_ultima_vitoria).days

        resultados.append({'Time': vencedor, 'Dias': dias_com_cinturao_max})

    dias_com_titulo_consecutivos = pd.DataFrame(resultados)

    dias_com_titulo_consecutivos = dias_com_titulo_consecutivos.sort_values(by=['Dias'], ascending=False)[:10]


    x = dias_com_titulo_consecutivos['Time'].to_list()
    y = dias_com_titulo_consecutivos['Dias'].to_list()

    plot_df = pd.DataFrame({'Times': x, 'Dias': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Dias', y='Times', color='Times', color_discrete_sequence=cores, orientation='h').update_layout(template='seaborn', showlegend=False)

    return fig

def get_teams_with_most_consecutive_games_with_cinturao(games_df, teams_df):
    resultados = []

    for vencedor in games_df['Vencedor'].value_counts().index:
        cinturao_games_by_team = games_df[ (games_df['Vencedor'] == vencedor) | (games_df['Defensor do Título'] == vencedor) ].reset_index(drop=True)

        jogos_com_cinturao = 0
        jogos_com_cinturao_max = 0

        for _, row in cinturao_games_by_team.iterrows():
            if row['Vencedor'] == vencedor:
                jogos_com_cinturao += 1

            else:
                if jogos_com_cinturao > jogos_com_cinturao_max:
                    jogos_com_cinturao_max = jogos_com_cinturao

                jogos_com_cinturao = 0

        resultados.append({'Time': vencedor, 'Jogos': jogos_com_cinturao_max})

    jogos_com_titulo_consecutivos = pd.DataFrame(resultados)

    jogos_com_titulo_consecutivos = jogos_com_titulo_consecutivos.sort_values(by=['Jogos'], ascending=False)[:10]

    x = jogos_com_titulo_consecutivos['Time'].to_list()
    y = jogos_com_titulo_consecutivos['Jogos'].astype(int).to_list()

    plot_df = pd.DataFrame({'Times': x, 'Jogos': y})
    cores = get_cores(teams_df, x)

    fig = px.bar(plot_df, x='Jogos', y='Times', color='Times', color_discrete_sequence=cores,orientation='h').update_layout(template='seaborn', showlegend=False)
    
    return fig