import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv(r"C:\Users\ajona\PycharmProjects\PLN\oficial\unificado.csv")

print("Iniciando análise de comprimento de caracteres...")


# --- 2. Calcular os Percentis (O que você perguntou) ---
p90 = df['length'].quantile(0.90)
p95 = df['length'].quantile(0.95)
p99 = df['length'].quantile(0.99)
max_len = df['length'].max()
avg_len = df['length'].mean()

print("\n--- Tabela de Percentis (Comprimento de Caracteres) ---")
print(f"Total amostras: {df['Comentário'].count()}")
print(f"Média de Caracteres: {avg_len:.0f}")
print(f"P90 (90% dos dados): {p90:.0f} caracteres ou menos")
print(f"P95 (95% dos dados): {p95:.0f} caracteres ou menos")
print(f"P99 (99% dos dados): {p99:.0f} caracteres ou menos")
print(f"Comprimento Máximo: {max_len:.0f} caracteres")
print("-------------------------------------------------------")


corte_caracteres = 111

# --- 4. Plotar o Gráfico de Distribuição (para seu TCC) ---
print("\nGerando gráfico de distribuição...")

plt.figure(figsize=(12, 7))
sns.histplot(
    data=df,
    x='length',
    kde=True, # Adiciona a linha de densidade (KDE)
    bins=100, # Divide em 100 "barras"
    color='blue'
)
plt.title('Distribuição do Comprimento de Caracteres (EDA)', fontsize=16)
plt.xlabel('Número de Caracteres', fontsize=12)
plt.ylabel('Contagem de Comentários', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.6)

# Adiciona linhas verticais para os P95 e seu corte de 130
plt.axvline(
    x=p95,
    color='red',
    linestyle='--',
    label=f'P95 ({p95:.0f} caracteres)'
)
plt.axvline(
    x=corte_caracteres,
    color='green',
    linestyle=':',
    lw=3,
    label=f'Corte de {corte_caracteres} caracteres'
)

# Ajusta o limite do eixo X para focar na parte importante
# (Baseado no P99 para não mostrar outliers extremos)
plt.xlim(0, p99 * 1.2)

plt.legend()
plt.tight_layout()
plt.show()