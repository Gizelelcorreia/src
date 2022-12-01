# Importando as bibliotecas
from email import generator
import pandas as pd
import numpy as np
import os
from pyomo.environ import *

# =============================================== DADOS DO MODELO =====================================================#
#reads data file in universal format (windows and unix)
arquivo_dados = os.path.join("..", "data", "Dados.xlsx")

#loads data into data structures
dados_trabalhadores = pd.read_excel(arquivo_dados, sheet_name = 0)
dados_dia = pd.read_excel(arquivo_dados, sheet_name = 1)
dados_funcao = pd.read_excel(arquivo_dados, sheet_name = 2)
dados_farmacias = pd.read_excel(arquivo_dados, sheet_name = 3)
dados_turnos = pd.read_excel(arquivo_dados, sheet_name = 4)
dados_folgas = pd.read_excel(arquivo_dados, sheet_name = 5)
dados_score = pd.read_excel(arquivo_dados, sheet_name = 6)
dados_demanda_0 = pd.read_excel(arquivo_dados, sheet_name = 7)
dados_demanda_1 = pd.read_excel(arquivo_dados, sheet_name = 8)
dados_demanda_2 = pd.read_excel(arquivo_dados, sheet_name = 9)
dados_demanda_3 = pd.read_excel(arquivo_dados, sheet_name = 10)
dados_demanda_4 = pd.read_excel(arquivo_dados, sheet_name = 11)
dados_demanda_5 = pd.read_excel(arquivo_dados, sheet_name = 12)
dados_demanda_6 = pd.read_excel(arquivo_dados, sheet_name = 13)
dados_demanda_7 = pd.read_excel(arquivo_dados, sheet_name = 14)

# Conjunto/Indices
n_trabalhadores = len(dados_trabalhadores)
n_turnos = len(dados_turnos) * 30
n_farmacias = len(dados_farmacias)
n_tipos = len(dados_funcao)
trabalhador = list(range(n_trabalhadores))  #W
turno = list(range(n_turnos)) #S
farmacia = list(range(n_farmacias)) #K
tipos = list(range(n_tipos)) #T
tipo_trab= [] #WT

# Parâmetros
dados_folgas = dados_folgas.drop('FUN', axis=1)
a_trab = dados_folgas.values.tolist() #aij
dados_score = dados_score.drop('NOMES', axis=1)
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
div_turnos = len(turno)//2

for i in range(n_trabalhadores):
    if dados_trabalhadores.FUNCAO[i] == 'AUXILIAR':
        auxiliar.append(i)
        num_trabalhadores_tipos.append(2)
    elif dados_trabalhadores.FUNCAO[i] == 'ASSISTENTE':
        assistente.append(i)
        num_trabalhadores_tipos.append(1)
    else:
        farmaceutico.append(i)
        num_trabalhadores_tipos.append(0)

tipo_trab = [farmaceutico, assistente, auxiliar]

for i in range(len(dados_funcao)):
    turnos_folga_tipo_trab.append(dados_funcao.loc[i, 'FOLGAS'])
    n_max_shifts.append(dados_funcao.loc[i, 'N_MAX_TURNO'])

for i in range(len(dados_trabalhadores)):
    nomes_trab.append(dados_trabalhadores.loc[i, 'TRABALHADOR'])

for i in range(len(dados_farmacias)):
    nomes_farm.append(dados_farmacias.loc[i, 'FARMACIA'])

for i in farmacia:
    nomes[i] = list(range(n_trabalhadores))

for i in farmacia:
    nomes_locais[i] = list(range(n_farmacias))
#============================================== MODELO, VARIÁVEIS E RESTRIÇÕES ======================================#

# # Declarando o modelo.
model = ConcreteModel()

# Variáveis de Decisão
model.x = Var(trabalhador, turno, farmacia, domain=Binary)
model.y = Var(trabalhador, farmacia, domain=Binary)
model.z = Var(domain=NonNegativeReals)

# Função objetivo

# Tenta min. o número de shifts que um trabalhador é alocado e conta o beneficio de ter o trabalhador i na farmacia k
model.obj = Objective(expr=model.z + sum(b_trab[i][k] * model.y[i, k] for i in trabalhador for k in farmacia) + sum(model.x[i,j,k] for i in trabalhador for j in turno for k in farmacia))

# Construtor de Restrições
model.constrs = ConstraintList()

# Restrições
# R1: Calculam o número máximo de shifts aos quais um trabalhador é alocado
for t in tipos:
    for i in tipo_trab[t]:
        model.constrs.add(model.z >= (1 / turnos_folga_tipo_trab[t]) * sum(a_trab[i][j] * model.x[i, j, k] for j in turno for k in farmacia))

# R2: Impõem que cada trabalhador só pode ser alocado em no máximo uma farmácia em cada período.
for i in trabalhador:
    for j in turno:
        if a_trab[i][j] == 0:
            continue
        model.constrs.add(expr=sum(a_trab[i][j] * model.x[i, j, k] for k in farmacia) <= 1)

# R3: Vincula as variáveis x e y contando que um determinando empregador só pode trabalhar na farmácia naquele turno.
for i in trabalhador:
    for j in turno:
        for k in farmacia:
            model.constrs.add(expr=model.y[i, k] >= a_trab[i][j] * model.x[i, j, k])

# R4: limita o número de farmácias em que o trabalhador pode ser alocado no horizonte
for i in trabalhador:
    model.constrs.add(expr=sum(model.y[i, k] for k in farmacia) <= 1)

# R5: Garantem que o número necessário de trabalhadores de um certo tipo em cada farmácia será sempre respeitado.        
for j in turno:
    for k in farmacia:
        for t in tipos:
            model.constrs.add(expr=sum(a_trab[i][j] * model.x[i, j, k] for i in tipo_trab[t]) == n_dem_farm[k][j][t])

# R6: Impõem que um trabalhador só pode ser alocado no máximo 1 vez em um número consecutivo de shifts igual o número de folgas
for t in tipos:
    for i in tipo_trab[t]:
        horas_iniciais = list(range(len(turno) - turnos_folga_tipo_trab[t] - 1 + 1))
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

#==================================================== RESOLUÇÃO ======================================================#

opt = SolverFactory('cplex')
# # opt.options['timelimit'] = 100
resultados = opt.solve(model, tee=True)

print("\n\nDone!\n\n")

# ==================================================== RESULTADOS ====================================================#

#Escrever o Lpfile
# filename = os.path.join(os.path.dirname(__file__), 'model.lp')
# model.write(filename, io_options={'symbolic_solver_labels': True})

# Escrever o resultado
# with open('tt_01.txt', 'w') as arquivo:
#     lista = list(model.x.keys())
#     for i in lista:
#         # if model.x[i]() != 0:
#         s = str(i) + ' = ' + str(model.x[i]())
#         arquivo.write((s) + '\n')

# ================================================= GERADOR DE ESCALA =================================================#

# # Gerador de escalas
# resultado_escala = list(range(n_farmacias))
# for k in farmacia:
#     resultado_escala[k] = list(range(n_turnos))

# for k in farmacia:
#     for j in turno:
#          resultado_escala[k][j] = list(range(n_trabalhadores))

# for k in farmacia:
#     for j in turno:
#         for i in trabalhador:
#             resultado_escala[k][j][i] = value(model.x[i,j,k])

# escala_farmacias = []
# escala_trabalhadores = []
# for k in farmacia:
#     for i in trabalhador:
#         a = 0
#         for j in turno:
#             a = a+resultado_escala[k][j][i]
#         if a == 0:
#             if k not in escala_farmacias:
#                 escala_farmacias.append(k)
#                 escala_trabalhadores.append([])
#             escala_trabalhadores[k].append(i)

# for i in escala_farmacias:
#     for j in turno:
#         for k in escala_trabalhadores[i]:
#             resultado_escala[i][j][k] = k

# for i in escala_farmacias:
#     for j in turno:
#         for k in escala_trabalhadores[i]:
#             resultado_escala[i][j].pop(resultado_escala[i][j].index(k))

# for i in escala_farmacias:
#     for k in escala_trabalhadores[i]:
#         nomes[i].pop(nomes[i].index(k))

# nomes_p=[]
# for i in range(len(nomes)):
#     nomes_p.append([])
# for i in range(len(nomes)):
#     for k in nomes[i]:
#         nomes_p[i].append(nomes_trab[k])

# nomes_f=[]
# for i in range(len(nomes_locais)):
#     nomes_f.append([])
# for i in range(len(nomes_locais)):
#     for k in nomes_locais[i]:
#         nomes_f[i].append(nomes_farm[k])

# resultados_f = list(range(n_farmacias))
# for i in farmacia:
#     resultados_f[i] = list(range(div_turnos))

# for i in farmacia:
#     for j in range(div_turnos):
#          resultados_f[i][j]=list(range(len(resultado_escala[i][j])))

# for i in farmacia:
#     for j in range(div_turnos):
#         for k in range(len(resultado_escala[i][j])):
#                 if resultado_escala[i][2*j][k] == 0:
#                     if resultado_escala[i][(2*j)+1][k] == 1:
#                         resultados_f[i][j][k]="N"
#                     else:
#                         resultados_f[i][j][k]= " "
#                 else:
#                     if resultado_escala[i][(2*j)+1][k] == 0:
#                         resultados_f[i][j][k] = "D" 
#                     else:
#                         print("problema", i, j*2, j*2+1, k)        

# # Gerador base
# print(' >>>>>>Gerador de Escalas<<<<<<<' )
# opcao = 0
# export = 0
# while opcao != 2:
#     print('''[1] Sim
# [2] Não''')
#     try:
#         opcao = int(input(' >>>>>> Deseja continuar??\n'))
#         if opcao == 1:
#             gerar_escala = int(input("Digite o número da farmácia:\n"))
#             if gerar_escala <= 9:
#                 table = pd.DataFrame(index=nomes_p[gerar_escala])
#                 dia = 1
#                 for i in range(div_turnos):
#                     table[f'Dia {i+1}'] = resultados_f[gerar_escala][i]
#                 print('Farmácia {}'.format(nomes_farm[gerar_escala]))
#                 print(table)
#                 print("=-=" * 15)
#                 print('           Sua escala foi gerada!      ')
#                 print("=-=" * 15)

#                 print(' >>>>>>> Deseja exporta o resultado??\n')
#                 print('''[1] Sim
# [2] Não''')
#                 try:
#                     export = int(input('>>>>>> Exportar??\n'))
#                     if export == 1:
#                         with pd.ExcelWriter("Escalas_{}.xlsx".format(gerar_escala)) as writer:
#                             table.to_excel(writer, sheet_name= f'Farmácia {nomes_farm[gerar_escala]}', na_rep= '#N/A', header = True)
#                     elif export == 2:
#                         continue
#                     else:
#                         print('Opção invalida!! Tente novamente,')
#                 except:
#                     print("Infelizmente tivemos um erro :(")
#             else:
#                 print("Opção invalida!! Tente novamente.")
#         elif opcao == 2:
#             break
#         else:
#             print("Opção invalida!! Tente novamente.")
#             print("=-=" * 15)
#     except:
#         print("Infelizmente tivemos um erro :( Tente novamente!")
# print("=-=" * 15)
# print('       Fim do programa! Volte sempre!')

# # if(__name__ == "__main__"):
# #     gerador_escala()

print ("folgas ", folgas)