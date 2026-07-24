import csv
import re
from collections import Counter

caminho_entrada = "arquivo.csv"
caminho_saida = "arquivo_corrigido.csv"
caminho_log = "log_correcoes.txt"

DELIMITADOR = ","
TEM_CABECALHO = True
VALOR_NULO = ""  # pode trocar para None, "NULL", etc. conforme a necessidade

# ----------------------------------------------------------------------
# 1. LEITURA
# ----------------------------------------------------------------------
with open(caminho_entrada, newline='', encoding='latin1') as f:
    leitor = csv.reader(f, delimiter=DELIMITADOR)
    todas_linhas = list(leitor)

if TEM_CABECALHO:
    cabecalho = todas_linhas[0]
    linhas = todas_linhas[1:]
else:
    cabecalho = None
    linhas = todas_linhas

contagem_colunas = [len(linha) for linha in linhas]
moda = Counter(contagem_colunas).most_common(1)[0][0]
print(f"Moda de colunas por linha: {moda}")

# ----------------------------------------------------------------------
# 2. PERFIL DE CADA COLUNA (aprendido com as linhas corretas)
# ----------------------------------------------------------------------
def classifica_valor(valor):
    valor = valor.strip()
    if valor == "":
        return "vazio"
    if re.fullmatch(r"-?\d+", valor):
        return "inteiro"
    if re.fullmatch(r"-?\d+[.,]\d+", valor):
        return "decimal"
    if re.fullmatch(r"\d{2}[/-]\d{2}[/-]\d{2,4}", valor):
        return "data"
    if re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.-]+", valor):
        return "email"
    return "texto"

linhas_ok = [linha for linha in linhas if len(linha) == moda]

perfil_colunas = []
for col_idx in range(moda):
    tipos = [classifica_valor(linha[col_idx]) for linha in linhas_ok]
    tipo_predominante, _ = Counter(tipos).most_common(1)[0]
    tamanho_medio = sum(len(linha[col_idx]) for linha in linhas_ok) / max(len(linhas_ok), 1)
    # % de linhas em que essa coluna costuma vir vazia (ajuda a achar onde falta o valor)
    taxa_vazio = sum(1 for t in tipos if t == "vazio") / max(len(tipos), 1)
    perfil_colunas.append({
        "tipo": tipo_predominante,
        "tamanho_medio": tamanho_medio,
        "taxa_vazio": taxa_vazio,
    })

# ----------------------------------------------------------------------
# 3. FUNÇÃO QUE PONTUA O QUANTO UMA LINHA CANDIDATA "BATE" COM O PERFIL
# ----------------------------------------------------------------------
def pontuar_linha(linha_candidata):
    if len(linha_candidata) != moda:
        return -1
    pontos = 0
    for col_idx, valor in enumerate(linha_candidata):
        perfil = perfil_colunas[col_idx]
        tipo_valor = classifica_valor(valor)

        if tipo_valor == "vazio":
            # premia inserir nulo em colunas que costumam ser vazias,
            # penaliza inserir nulo em colunas que quase nunca são vazias
            pontos += perfil["taxa_vazio"] * 3 - (1 - perfil["taxa_vazio"]) * 1.5
            continue

        if tipo_valor == perfil["tipo"]:
            pontos += 2
        elif perfil["tipo"] == "texto" and tipo_valor == "texto":
            pontos += 1

        diff_tamanho = abs(len(valor) - perfil["tamanho_medio"])
        pontos -= diff_tamanho * 0.02
    return pontos

# ----------------------------------------------------------------------
# 4. GERA CANDIDATAS PARA EXCESSO (mesclagem) E PARA FALTA (inserção)
# ----------------------------------------------------------------------
def gerar_candidatas_excesso(linha, excedente):
    candidatas = []
    qtd_original = len(linha)
    tamanho_bloco = excedente + 1

    for inicio in range(0, qtd_original - tamanho_bloco + 1):
        nova = (
            linha[:inicio]
            + [DELIMITADOR.join(linha[inicio: inicio + tamanho_bloco])]
            + linha[inicio + tamanho_bloco:]
        )
        if len(nova) == moda:
            candidatas.append((inicio, nova))
    return candidatas

def gerar_candidatas_falta(linha, faltam):
    """
    Gera candidatas inserindo 'faltam' valores nulos em posições possíveis.
    Quando falta mais de 1 valor, testa inserir o bloco de nulos em cada
    posição possível (mantém simples: bloco contíguo de nulos).
    """
    candidatas = []
    qtd_original = len(linha)

    for inicio in range(0, qtd_original + 1):
        nova = linha[:inicio] + [VALOR_NULO] * faltam + linha[inicio:]
        if len(nova) == moda:
            candidatas.append((inicio, nova))
    return candidatas

# ----------------------------------------------------------------------
# 5. PROCESSA AS LINHAS
# ----------------------------------------------------------------------
linhas_corrigidas = []
log_eventos = []

for i, linha in enumerate(linhas):
    qtd = len(linha)
    numero_linha = i + (2 if TEM_CABECALHO else 1)

    if qtd == moda:
        linhas_corrigidas.append(linha)
        continue

    diferenca = qtd - moda

    # ---------------- EXCESSO: provável vírgula sem aspas ----------------
    if diferenca > 0:
        candidatas = gerar_candidatas_excesso(linha, diferenca)

        if not candidatas:
            log_eventos.append(
                f"[Linha {numero_linha}] EXCESSO ({qtd} -> {moda}): "
                f"nenhuma combinação válida encontrada. Mantida para revisão manual: {linha}"
            )
            linhas_corrigidas.append(linha)
            continue

        melhor_inicio, melhor_linha = max(candidatas, key=lambda c: pontuar_linha(c[1]))
        melhor_pontuacao = pontuar_linha(melhor_linha)

        coluna_nome = cabecalho[melhor_inicio] if cabecalho else f"índice {melhor_inicio}"
        log_eventos.append(
            f"[Linha {numero_linha}] EXCESSO ({qtd} -> {moda}): "
            f"mesclagem identificada na coluna '{coluna_nome}' (pontuação={melhor_pontuacao:.2f}) | "
            f"original={linha} | corrigida={melhor_linha}"
        )
        linhas_corrigidas.append(melhor_linha)

    # ---------------- FALTA: provável coluna ausente ----------------
    else:
        faltam = abs(diferenca)
        candidatas = gerar_candidatas_falta(linha, faltam)

        if not candidatas:
            log_eventos.append(
                f"[Linha {numero_linha}] FALTA ({qtd} -> {moda}): "
                f"nenhuma combinação válida encontrada. Mantida para revisão manual: {linha}"
            )
            linhas_corrigidas.append(linha)
            continue

        melhor_inicio, melhor_linha = max(candidatas, key=lambda c: pontuar_linha(c[1]))
        melhor_pontuacao = pontuar_linha(melhor_linha)

        if cabecalho:
            colunas_afetadas = ", ".join(
                f"'{cabecalho[idx]}'" for idx in range(melhor_inicio, melhor_inicio + faltam)
            )
        else:
            colunas_afetadas = f"índices {melhor_inicio} a {melhor_inicio + faltam - 1}"

        log_eventos.append(
            f"[Linha {numero_linha}] FALTA ({qtd} -> {moda}): "
            f"valor(es) nulo(s) inserido(s) na(s) coluna(s) {colunas_afetadas} "
            f"(pontuação={melhor_pontuacao:.2f}) | "
            f"original={linha} | corrigida={melhor_linha}"
        )
        linhas_corrigidas.append(melhor_linha)

# ----------------------------------------------------------------------
# 6. SALVA RESULTADOS
# ----------------------------------------------------------------------
saida_final = ([cabecalho] if cabecalho else []) + linhas_corrigidas

with open(caminho_saida, "w", newline='', encoding='latin1') as f:
    escritor = csv.writer(f, delimiter=DELIMITADOR)
    escritor.writerows(saida_final)

with open(caminho_log, "w", encoding='latin1') as f:
    if log_eventos:
        f.write(f"Moda de colunas: {moda}\n")
        f.write(f"Total de linhas corrigidas: {len(log_eventos)}\n\n")
        f.write("\n".join(log_eventos))
    else:
        f.write("Nenhuma correção necessária.")

print(f"\nCSV corrigido salvo em: {caminho_saida}")
print(f"Log de correções salvo em: {caminho_log}")
print(f"Total de linhas alteradas: {len(log_eventos)}")
