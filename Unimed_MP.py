from pyomo.environ import *
import pyomo.environ as pyEnv
import random
import pandas as pd
import numpy as np
import os
import copy
from os.path import join 

def carregarDados(arquivo_dados = os.path.join("..", "data", "Dados.xlsx" )):

    trabalhadores = pd.read_excel(arquivo_dados, sheet_name = 0)
    funcoes = pd.read_excel(arquivo_dados, sheet_name = 2)
    farmacias = pd.read_excel(arquivo_dados, sheet_name = 3)
    turnos = pd.read_excel(arquivo_dados, sheet_name = 4)
    folgas = pd.read_excel(arquivo_dados, sheet_name = 5)
    score = pd.read_excel(arquivo_dados, sheet_name = 6)
    dados_demanda_0 = pd.read_excel(arquivo_dados, sheet_name = 7)
    dados_demanda_1 = pd.read_excel(arquivo_dados, sheet_name = 8)
    dados_demanda_2 = pd.read_excel(arquivo_dados, sheet_name = 9)
    dados_demanda_3 = pd.read_excel(arquivo_dados, sheet_name = 10)
    dados_demanda_4 = pd.read_excel(arquivo_dados, sheet_name = 11)
    dados_demanda_5 = pd.read_excel(arquivo_dados, sheet_name = 12)
    dados_demanda_6 = pd.read_excel(arquivo_dados, sheet_name = 13)
    dados_demanda_7 = pd.read_excel(arquivo_dados, sheet_name = 14)

    return trabalhadores, funcoes, farmacias, turnos, folgas, score, dados_demanda_0, dados_demanda_1, dados_demanda_2, dados_demanda_3, dados_demanda_4, dados_demanda_5, dados_demanda_6, dados_demanda_7


def dadosGerais():

    trabalhadores, funcoes, farmacias, turnos, folgas, score, dados_demanda_0, dados_demanda_1, dados_demanda_2, dados_demanda_3, dados_demanda_4, dados_demanda_5, dados_demanda_6, dados_demanda_7 = carregarDados()
   
    # Conjunto/Indices
    n_trabalhadores = len(trabalhadores)
    n_turnos = len(turnos) * 7
    n_farmacias = len(farmacias)
    n_tipos = len(funcoes)
    trabalhador = list(range(n_trabalhadores))  #W
    horizonte = list(range(n_turnos)) #S
    farmacia = list(range(n_farmacias)) #K
    tipos = list(range(n_tipos)) #T
    tipo_trab = [] #WT

    # Parâmetros
    dados_folgas = folgas.drop('FUN', axis=1)
    a_trab = dados_folgas.values.tolist() #aij
    dados_score = score.drop('NOMES', axis=1)
    b_trab = dados_score.values.tolist() #bik

    dados_demanda_0 = dados_demanda_0.drop('FARMACIA', axis=1)
    dados_demanda_1 = dados_demanda_1.drop('FARMACIA', axis=1)
    dados_demanda_2 = dados_demanda_2.drop('FARMACIA', axis=1)
    dados_demanda_3 = dados_demanda_3.drop('FARMACIA', axis=1)
    dados_demanda_4 = dados_demanda_4.drop('FARMACIA', axis=1)
    dados_demanda_5 = dados_demanda_5.drop('FARMACIA', axis=1)
    dados_demanda_6 = dados_demanda_6.drop('FARMACIA', axis=1)
    dados_demanda_7 = dados_demanda_7.drop('FARMACIA', axis=1)

    turn_njkt = round(n_turnos/4)

    bloco = dados_demanda_0.values.tolist() * turn_njkt 
    central = dados_demanda_1.values.tolist() * turn_njkt 
    internamento = dados_demanda_2.values.tolist() * turn_njkt 
    kit = dados_demanda_3.values.tolist() * turn_njkt 
    materno = dados_demanda_4.values.tolist() * turn_njkt 
    urgencia = dados_demanda_5.values.tolist() * turn_njkt 
    uti_geral = dados_demanda_6.values.tolist() * turn_njkt 
    uti_ped = dados_demanda_7.values.tolist() * turn_njkt 

    n_dem_farm = [bloco, central, internamento, kit, materno, urgencia, uti_geral, uti_ped]

    turnos_folga_tipo_trab = []  #ST
    folgas_iniciais = n_trabalhadores * [0]  #RI
    auxiliar = []
    assistente = []
    farmaceutico = []
    n_max_shifts = []
    nomes = list(range(n_farmacias))
    nomes_trab = []
    nomes_locais = list(range(n_farmacias))
    nomes_farm = []
    num_trabalhadores_tipos = []
    div_turnos = len(horizonte)//2

    for i in range(n_trabalhadores):
        if trabalhadores.FUNCAO[i] == 'AUXILIAR':
            auxiliar.append(i)
            num_trabalhadores_tipos.append(2)
        elif trabalhadores.FUNCAO[i] == 'ASSISTENTE':
            assistente.append(i)
            num_trabalhadores_tipos.append(1)
        else:
            farmaceutico.append(i)
            num_trabalhadores_tipos.append(0)

    tipo_trab = [farmaceutico, assistente, auxiliar]

    for i in range(len(funcoes)):
        turnos_folga_tipo_trab.append(funcoes.loc[i, 'FOLGAS'])
        n_max_shifts.append(funcoes.loc[i, 'N_MAX_TURNO'])

    for i in range(len(trabalhadores)):
        nomes_trab.append(trabalhadores.loc[i, 'TRABALHADOR'])

    for i in range(len(farmacias)):
        nomes_farm.append(farmacias.loc[i, 'FARMACIA'])

    for i in farmacia:
        nomes[i] = list(range(n_trabalhadores))

    for i in farmacia:
        nomes_locais[i] = list(range(n_farmacias))

    return trabalhador, horizonte, farmacia, tipos, tipo_trab, a_trab, b_trab, n_dem_farm, folgas_iniciais, turnos_folga_tipo_trab, div_turnos


# def solveModel(horizonte, folgas, solucao):
def solveModel():

    # Declarando o modelo.
    model = pyEnv.ConcreteModel()

    # Variáveis de Decisão
    model.x = pyEnv.Var(trabalhador, horizonte, farmacia, domain=pyEnv.Binary)
    model.y = pyEnv.Var(trabalhador, farmacia, domain=pyEnv.Binary)
    model.z = pyEnv.Var(domain=pyEnv.NonNegativeReals)

    def func_objetivo(model):
        return (model.z + sum(b_trab[i][k] * model.y[i, k] for i in trabalhador for k in farmacia) + sum(model.x[i,j,k] for i in trabalhador for j in horizonte for k in farmacia))

    model.objetivo = pyEnv.Objective(rule = func_objetivo, sense = pyEnv.minimize)

    # Construtor de Restrições
    model.constrs = pyEnv.ConstraintList()

    # Restrições
    # R1: Calculam o número máximo de shifts aos quais um trabalhador é alocado
    for t in tipos:
        for i in tipo_trab[t]:
            model.constrs.add(model.z >= (1 / turnos_folga_tipo_trab[t]) * sum(a_trab[i][j] * model.x[i, j, k] for j in horizonte for k in farmacia))

    # R2: Impõem que cada trabalhador só pode ser alocado em no máximo uma farmácia em cada período.
    for i in trabalhador:
        for j in horizonte:
            if a_trab[i][j] == 0:
                continue
            model.constrs.add(expr=sum(a_trab[i][j] * model.x[i, j, k] for k in farmacia) <= 1)
                
    # R3: Vincula as variáveis x e y contando que um determinando empregador só pode trabalhar na farmácia naquele turno.
    for i in trabalhador:
        for j in horizonte:
            for k in farmacia:
                    model.constrs.add(expr=model.y[i, k] >= a_trab[i][j] * model.x[i, j, k])

    # R4: limita o número de farmácias em que o trabalhador pode ser alocado no horizonte
    for i in trabalhador:
        model.constrs.add(expr=sum(model.y[i, k] for k in farmacia) <= 1)

    # R5: Garantem que o número necessário de trabalhadores de um certo tipo em cada farmácia será sempre respeitado.        
    for j in horizonte:
        for k in farmacia:
            for t in tipos:
                model.constrs.add(expr=sum(a_trab[i][j] * model.x[i, j, k] for i in tipo_trab[t]) == n_dem_farm[k][j][t])

    # R6: Impõem que um trabalhador só pode ser alocado no máximo 1 vez em um número consecutivo de shifts igual o número de folgas
    for t in tipos:
        for i in tipo_trab[t]:
            horas_iniciais = list(range(len(horizonte) - turnos_folga_tipo_trab[t] - 1 + 1))
            for h in horas_iniciais:
                if (h) > 54:
                    folgas = list(range(h, 60))
                else:
                    folgas = list(range(h, (h + turnos_folga_tipo_trab[t])+1))
                    model.constrs.add(expr=sum(model.x[i, j, k] for k in farmacia for j in folgas) <= 1)

    # R7: Se hour turnos de folga passando de um mês para o outro dado pelo tipo de trabalhador
    for i in trabalhador:
        if folgas_iniciais[i] == 0:
            continue
        for k in farmacia:
            model.constrs.add(expr=sum(model.x[i, j, k] for j in range(0, turnos_folga_tipo_trab[i])) == 0)

    opt = pyEnv.SolverFactory('cplex')
    resultados = opt.solve(model, tee=True)
    # resultados = opt.solve(model)

    return resultados, model


def pega_sol(model):
    modelo_x = [[[0 for k in range(farmacia)] for j in range(horizonte)] for i in range(trabalhador)]
    indices = list(model.x.keys())
    for i,j,k in indices:
        if model.x[i,j,k] >= 0.95:
            modelo_x[i][j][k] = model.x[i,j,k].value
            print(modelo_x)

    # lista = list(model.x.keys())
    # for i in lista:
    #     if model.x[i]() != 0:
    #         s = str(i) + ' = ' + str(model.x[i]())
    #         modelo_x.append((s) + '\n')
    #         print(modelo_x)

# def calcula_folgas(solucao):
#     return folgas


if(__name__ == "__main__"):

    trabalhador, horizonte, farmacia, tipos, tipo_trab, a_trab, b_trab, n_dem_farm, folgas_iniciais, turnos_folga_tipo_trab, div_turnos = dadosGerais()
    modelo = solveModel()
    pega_sol(modelo)


    # passo = 15
    # for p in range(0, len(horizonte), passo):
    #     periodo = list(range(p, p + passo))
    #     # resultado, modelo = solveModel(periodo, folgas, solucao)
    #     resultado, modelo = solveModel(periodo, solucao)
    #     solucao = pega_sol(modelo)
        # folgas = calcula_folgas(solucao)

    
