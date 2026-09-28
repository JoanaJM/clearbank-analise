import pandas as pd
from datetime import datetime

LIMITE_SUSPEITO = 10000.00

def ler_transacoes(file_name):
    try:
        dataset = pd.read_csv(file_name)
    except FileNotFoundError:
        return print("Arquivo não encontrado.")
    except Exception as e:
        return print("Erro ", e)
    return dataset

def validar_transacao(row):

    def valid_id(id):
        if isinstance(id, type(float('nan'))):
            return False
        if isinstance(id, int):
            return True
        return False
    
    def valid_client_id(id):
        if isinstance(id, type(float('nan'))):
            return False
        return True

    def valid_transaction_type(transaction_type):
        if transaction_type in ('debito', 'credito'):
            return True
        return False

    def valid_value(value):
        if value > 0:
            return True
        return False

    def invalid_input(value, target_type, default=None):
        try:
            return target_type(value)
        except (ValueError, TypeError):
            return default

    if not invalid_input(row['id'], int):
        return None
    else:
        id = int(row['id'])
        if not valid_id(id):
            return None

    if not invalid_input(row['cliente_id'], str):
        return None
    else:
        client_id = row['cliente_id']
        if not valid_client_id(client_id):
            return None

    try:
        date = datetime.strptime(row['data'], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

    if not valid_transaction_type(row['tipo']):                                                                                                                    
        return None
       
    if not invalid_input(row['valor'], float):
        return None
    else:
        value = float(row['valor'])         
        if not valid_value(value):
            return None
        
    return [id, date, client_id, row['tipo'], value, row['descricao'], row['categoria']]

def dates(dataset):
    dfgrouped = {
        str(mes): grupo
        for mes, grupo in dataset.groupby(dataset['data'].dt.to_period('M'))
    }
    
    days = max(dataset['data']) - min(dataset['data'])

    return days, dfgrouped


def gerar_relatorio(dataset):

    dataset = pd.DataFrame(dataset)
    days, dfgrouped = dates(dataset)
    
    sustransactions = []
    report = dict()
    for month in dfgrouped:
        credito = []
        debito = []

        monthlyReport = dict()
        for row in dfgrouped[month].values:
            if row[4] > LIMITE_SUSPEITO: 
                date = datetime.strftime(row[1], "%Y-%m-%d")
                sustransactions.append(
                    {
                    "id": row[0],
                    "cliente_id": row[2],
                    "data": date,
                    "valor": row[4]
                    }
                )
                continue

            elif row[3] == 'credito':
                credito.append(row[4])
            elif row[3] == 'debito':
                debito.append(row[4])
        
        total_credito = sum(credito)
        total_debito = sum(debito)

        saldo = total_credito - total_debito
        media = (total_credito + total_debito) / (len(credito) + len(debito))
        maior_valor = max(credito + debito)
        menor_valor = min(credito + debito)

        monthlyReport = {
            "quantidade": (len(credito) + len(debito)),
            "total_credito": total_credito,
            "total_debito": total_debito,
            "saldo": saldo,
            "media": media,
            "maior_valor": maior_valor,
            "menor_valor": menor_valor
        }

        report[month] = monthlyReport

    return report, sustransactions

import json

def salvar_json(reports, stats, sustransactions):

    reportDate = datetime.now().strftime("%Y-%m")
    jsonDict = dict()

    jsonDict["gerado_em"]= str(reportDate)
    jsonDict["total_transacoes_validas"] = stats['valid']
    jsonDict["total_transacoes_invalidas" ]= stats['invalid']
    jsonDict["resumo_mensal"] = dict(reports)
    jsonDict["transacoes_suspeitas"] = sustransactions    
    
    with open('relatorio_pandas.json', 'w', encoding='utf-8') as f:
        json.dump(jsonDict, f, ensure_ascii=False, indent=2)

    return 0

def exibir_relatorio(report, sustransactions):
    def freais(value):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    for mes, data in report.items():
        print(f"===== RELATÓRIO MENSAL =====")
        print(f"Mês: {mes}")
        print(f"  Transações:  \t{data['quantidade']}")
        print(f"  Total crédito: {freais(data['total_credito'])}")
        print(f"  Total débito:  {freais(data['total_debito'])}")
        print(f"  Saldo:  \t {freais(data['saldo'])}")
        print(f"  Média:  \t {freais(data['media'])}")
        print(f"  Maior valor: \t {freais(data['maior_valor'])}")
        print(f"  Menor valor: \t {freais(data['menor_valor'])}")

    if sustransactions == []:
        print("Nenhuma transação suspeita encontrada.")
    else:
        print(f"===== TRANSAÇÕES SUSPEITAS =====")
        for logs in sustransactions:
            print(f"ID: {logs['id']} | Cliente: {logs['cliente_id']} | Data: {logs['data']} | Valor: {freais(logs['valor'])}")
        

    return 0




file_name='transacoes.csv'

raw_file = ler_transacoes(file_name)

dataset = []
invalid = 0
for i, row in raw_file.iterrows():
    if validar_transacao(row) is not None:
        dataset.append(validar_transacao(row))
    else:
        invalid += 1

df = pd.DataFrame(dataset, columns=raw_file.columns)

print("Total de linhas lidas", len(raw_file))
print("Total de linhas válidas", len(dataset))
print("Total de linhas inválidas", invalid)
stats = dict()
stats['valid'] = len(dataset)
stats['invalid'] = invalid
report, sustransactions = gerar_relatorio(df)
salvar_json(report, stats, sustransactions)
exibir_relatorio(report, sustransactions)



import matplotlib.pyplot as plt

month = report.keys()
saldo = [month_data['saldo'] for month_data in report.values() if 'saldo' in month_data]
total_debitos = [month_data['total_debito'] for month_data in report.values() if 'total_debito' in month_data]
total_credito = [month_data['total_credito'] for month_data in report.values() if 'total_credito' in month_data]


fig = plt.figure(figsize=(10, 10))
plt.bar(month, saldo)

plt.title("Saldo mensal")
plt.xlabel("Mês")
plt.ylabel("Saldo (R$)")
plt.show()
fig.savefig('grafico.png')



fig = plt.figure(figsize=(10, 10))

plt.plot(month, total_debitos)

plt.title("Débitos mensais")
plt.xlabel("Mês")
plt.ylabel("Débito (R$)")
plt.show()
fig.savefig('grafico2.png')


fig = plt.figure(figsize=(10, 10))

plt.bar(month, total_credito, label='crédito')
plt.bar(month, total_debitos, label='débito')

plt.title("Saldo mensal")
plt.xlabel("Mês")
plt.ylabel("Valor (R$)")
plt.legend()
plt.show()

fig.savefig('grafico3.png')