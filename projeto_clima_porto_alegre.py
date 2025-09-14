#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Projeto (Fase 2) - Lógica e Programação de Computadores
-------------------------------------------------------
Conjunto de dados: clima diário de Porto Alegre (1961–2016) no formato CSV.

REQUISITOS ATENDIDOS
- Leitura do arquivo CSV (caminho relativo) e carga dos dados em memória
  (lista de dicionários).
- Preparação/tratamento básico dos dados (conversão de tipos, datas,
  tratamento de ausências).
- Visualização textual por intervalo (mês/ano inicial e final) e seleção
  de colunas: (1) todos, (2) precipitação, (3) temperaturas (máx/mín/média),
  (4) umidade e vento.
- “Mês mais chuvoso” (mês/ano com maior soma de precipitação) usando
  dicionário e função.
- Médias da temperatura mínima para um mês escolhido nos últimos 11 anos
  (2006 a 2016), armazenadas em dicionário (ano → média), com validação.
- Gráfico de barras com essas médias e rótulos legíveis.
- Média geral (2006–2016) da temperatura mínima do mês escolhido.
- Organização em funções e documentação (docstrings e comentários).
- **Sem caminho absoluto**: o programa espera o CSV na MESMA PASTA do .py.

COMO EXECUTAR
1) Coloque este arquivo .py e o CSV no MESMO diretório.
2) No terminal, rode:  `python3 projeto_clima_porto_alegre.py`
3) Siga o menu interativo.

OBSERVAÇÕES DE TRATAMENTO DE DADOS
- O arquivo CSV não é modificado.
- Entradas vazias em campos numéricos são lidas como None e ignoradas em
  somas/médias (ex.: precipitação/temperaturas ausentes).
- Datas estão no formato dd/mm/aaaa e são convertidas para objetos datetime.date.
- Campos esperados no CSV (cabeçalho): 
  data, precip, maxima, minima, horas_insol, temp_media, um_relativa, vel_vento
  (Se variações no cabeçalho forem encontradas, o programa tenta mapear pelos
   prefixos dos nomes e avisa se algo essencial não for localizado.)

Autor: (seu nome)
Data: (data da entrega)
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, date
from typing import Dict, List, Tuple, Iterable, Optional

# TENTAR importar matplotlib para o gráfico. Caso não exista, avisaremos no uso.
try:
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False


# ----------------------------
# Tipos e constantes auxiliares
# ----------------------------

Registro = Dict[str, object]  # chaves: 'data','precip','maxima','minima','temp_media','um_relativa','vel_vento'

CSV_NOME_PADRAO = "Anexo_Arquivo_Dados_Projeto_Logica_e_programacao_de_computadores.csv"


# ----------------------------
# Funções utilitárias de data
# ----------------------------

def parse_data_br(txt: str) -> date:
    """Converte 'dd/mm/aaaa' em datetime.date. Lança ValueError se inválido."""
    return datetime.strptime(txt.strip(), "%d/%m/%Y").date()


def dentro_periodo(d: date, mes_ini: int, ano_ini: int, mes_fim: int, ano_fim: int) -> bool:
    """
    Retorna True se a data 'd' estiver no intervalo [mes_ini/ano_ini .. mes_fim/ano_fim] (inclusive),
    comparando por (ano, mês).
    """
    ini = (ano_ini, mes_ini)
    fim = (ano_fim, mes_fim)
    cur = (d.year, d.month)
    return ini <= cur <= fim


def nome_mes_pt(m: int) -> str:
    """Nome do mês em português (1-12)."""
    nomes = ["janeiro","fevereiro","março","abril","maio","junho",
             "julho","agosto","setembro","outubro","novembro","dezembro"]
    return nomes[m-1] if 1 <= m <= 12 else f"mês {m}"


# ---------------------------------
# Carga e preparação do arquivo CSV
# ---------------------------------

def _mapear_colunas(header: List[str]) -> Dict[str, str]:
    """
    Tenta mapear as colunas necessárias (data, precip, maxima, minima, temp_media, um_relativa, vel_vento)
    mesmo que os nomes no CSV tenham pequenas variações. Retorna um dicionário mapeando o nome padronizado
    → nome real no CSV. Lança KeyError caso algo essencial não seja encontrado.
    """
    # normalizamos nomes do cabeçalho
    hnorm = [h.strip().lower() for h in header]

    # procura por entradas cujo prefixo combine
    def achar(prefixos: Iterable[str]) -> Optional[str]:
        for pref in prefixos:
            for h in header:
                if h.strip().lower().startswith(pref):
                    return h
        return None

    mapa = {}
    # data
    col = achar(["data"])
    if not col:
        raise KeyError("Coluna 'data' não encontrada no CSV.")
    mapa["data"] = col

    # precipitação
    col = achar(["precip", "precipit"])
    if not col:
        raise KeyError("Coluna de precipitação não encontrada (ex.: 'precip').")
    mapa["precip"] = col

    # temperaturas
    col = achar(["maxima", "tmax", "temp_max"])
    mapa["maxima"] = col if col else achar(["max"]) or "maxima"  # tolerante

    col = achar(["minima", "tmin", "temp_min"])
    mapa["minima"] = col if col else achar(["min"]) or "minima"

    # temperatura média (opcional para visualização)
    col = achar(["temp_media", "tmed", "tempmed", "temperatura média", "media"])
    mapa["temp_media"] = col if col else ""

    # umidade relativa
    col = achar(["um_relativa", "umidade", "ur"])
    mapa["um_relativa"] = col if col else ""

    # velocidade do vento
    col = achar(["vel", "vento", "vel_vento", "velocidade"])
    mapa["vel_vento"] = col if col else ""

    return mapa


def _to_float(s: str) -> Optional[float]:
    """Converte string para float. Retorna None se vazio/traço/valor inválido."""
    if s is None:
        return None
    txt = str(s).strip().replace(",", ".")  # tolerar vírgula decimal
    if txt == "" or txt == "-" or txt.lower() == "na":
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def carregar_dados_csv(caminho_relativo: str = CSV_NOME_PADRAO) -> List[Registro]:
    """
    Lê o CSV localizado na mesma pasta do script e retorna uma lista de dicionários padronizados.
    Não utiliza caminho absoluto. Se o arquivo não for encontrado, orienta o usuário.
    """
    # Caminho relativo à pasta do script
    pasta_script = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(pasta_script, caminho_relativo)

    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado em: {caminho}\n"
            f"Coloque o CSV na mesma pasta do programa ou informe outro nome no código."
        )

    registros: List[Registro] = []
    with open(caminho, "r", encoding="utf-8", newline="") as arq:
        leitor = csv.DictReader(arq)
        header = leitor.fieldnames or []
        mapa = _mapear_colunas(header)

        for lin in leitor:
            try:
                d = parse_data_br(lin[mapa["data"]])
            except Exception:
                # Se a data estiver inválida, descartamos a linha.
                continue

            reg: Registro = {
                "data": d,
                "precip": _to_float(lin.get(mapa["precip"], "")),
                "maxima": _to_float(lin.get(mapa["maxima"], "")) if mapa["maxima"] else None,
                "minima": _to_float(lin.get(mapa["minima"], "")) if mapa["minima"] else None,
                "temp_media": _to_float(lin.get(mapa["temp_media"], "")) if mapa["temp_media"] else None,
                "um_relativa": _to_float(lin.get(mapa["um_relativa"], "")) if mapa["um_relativa"] else None,
                "vel_vento": _to_float(lin.get(mapa["vel_vento"], "")) if mapa["vel_vento"] else None,
            }
            registros.append(reg)

    return registros


# -----------------------------------
# Visualização textual (item a)
# -----------------------------------

def filtrar_por_intervalo(registros: List[Registro], mes_ini: int, ano_ini: int, mes_fim: int, ano_fim: int) -> List[Registro]:
    """Filtra os registros por um intervalo (mês/ano inicial → mês/ano final), inclusive."""
    out = [r for r in registros if dentro_periodo(r["data"], mes_ini, ano_ini, mes_fim, ano_fim)]
    # Ordena por data crescente para impressão legível
    out.sort(key=lambda r: r["data"])
    return out


def imprimir_registros(regs: List[Registro], modo: int) -> None:
    """
    Imprime os registros conforme o modo escolhido:
      1 = todos os dados
      2 = apenas precipitação
      3 = apenas temperaturas (máxima, mínima e média se disponível)
      4 = apenas umidade e vento
    Inclui cabeçalho.
    """
    if not regs:
        print("Nenhum registro para o período informado.")
        return

    if modo == 1:
        cab = "DATA       | PRECIP(mm) | T_MAX(°C) | T_MIN(°C) | T_MED(°C) | UMID(%) | VENTO(m/s)"
    elif modo == 2:
        cab = "DATA       | PRECIP(mm)"
    elif modo == 3:
        cab = "DATA       | T_MAX(°C) | T_MIN(°C) | T_MED(°C)"
    elif modo == 4:
        cab = "DATA       | UMID(%) | VENTO(m/s)"
    else:
        print("Modo inválido.")
        return

    print(cab)
    print("-"*len(cab))
    for r in regs:
        d = r["data"].strftime("%d/%m/%Y")
        if modo == 1:
            print(f"{d:10} | {fmt(r['precip'], 1):>10} | {fmt(r['maxima'],1):>9} | {fmt(r['minima'],1):>9} | {fmt(r['temp_media'],1):>9} | {fmt(r['um_relativa'],1):>7} | {fmt(r['vel_vento'],1):>10}")
        elif modo == 2:
            print(f"{d:10} | {fmt(r['precip'], 1):>10}")
        elif modo == 3:
            print(f"{d:10} | {fmt(r['maxima'],1):>8} | {fmt(r['minima'],1):>8} | {fmt(r['temp_media'],1):>8}")
        elif modo == 4:
            print(f"{d:10} | {fmt(r['um_relativa'],1):>7} | {fmt(r['vel_vento'],1):>10}")


def fmt(v: Optional[float], casas: int = 1) -> str:
    """Formata float com N casas. Retorna '-' se None."""
    if v is None:
        return "-"
    return f"{v:.{casas}f}"


# -----------------------------------
# Mês mais chuvoso (item b)
# -----------------------------------

def mes_mais_chuvoso(registros: List[Registro]) -> Tuple[int, int, float]:
    """
    Retorna (ano, mês, total_precip) do mês mais chuvoso considerando TODOS os dados.
    Implementação com dicionário: chave = (ano, mês) → soma de precipitação.
    Valores None são ignorados.
    """
    soma_por_mes: Dict[Tuple[int,int], float] = {}
    for r in registros:
        p = r.get("precip")
        if p is None:
            continue
        chave = (r["data"].year, r["data"].month)
        soma_por_mes[chave] = soma_por_mes.get(chave, 0.0) + p

    if not soma_por_mes:
        raise ValueError("Não há dados de precipitação válidos para cálculo.")

    # encontra a chave com maior soma
    (ano, mes), total = max(soma_por_mes.items(), key=lambda kv: kv[1])
    return ano, mes, total


# -----------------------------------
# Médias temp mínima 2006–2016 (itens c, d, e)
# -----------------------------------

def medias_minimas_mes_2006_2016(registros: List[Registro], mes: int) -> Dict[int, float]:
    """
    Calcula, para cada ano de 2006 a 2016, a média da TEMPERATURA MÍNIMA do mês 'mes' (1..12).
    Retorna dicionário {ano: média}. Dias sem mínima são ignorados na média.
    """
    if not (1 <= mes <= 12):
        raise ValueError("Mês inválido. Use valores entre 1 e 12.")

    # agregação: ano → [valores_minima]
    vals: Dict[int, List[float]] = {ano: [] for ano in range(2006, 2017)}
    for r in registros:
        d: date = r["data"]
        if d.year in vals and d.month == mes:
            v = r.get("minima")
            if isinstance(v, (int, float)):
                vals[d.year].append(float(v))

    # média por ano (considerando somente se houver ao menos 1 valor)
    medias: Dict[int, float] = {}
    for ano, lista in vals.items():
        if lista:
            medias[ano] = sum(lista) / len(lista)
        else:
            # Se não há dados para o ano, não incluímos a chave (poderia incluir como None)
            # O gráfico e a média geral apenas ignoram anos sem dados.
            pass
    return medias


def plotar_barras_medias_minimas(medias: Dict[int, float], mes: int) -> Optional[str]:
    """
    Gera um gráfico de barras (arquivo PNG) com as médias fornecidas.
    Retorna caminho do arquivo gerado, ou None se matplotlib indisponível.
    """
    if not _HAS_MPL:
        print("matplotlib não está disponível. Instale para gerar o gráfico (pip install matplotlib).")
        return None

    if not medias:
        print("Sem dados para plotar.")
        return None

    anos = sorted(medias.keys())
    valores = [medias[a] for a in anos]

    plt.figure(figsize=(10, 5))
    plt.bar(anos, valores)
    plt.title(f"Média da temperatura mínima em {nome_mes_pt(mes)} (2006–2016)")
    plt.xlabel("Ano")
    plt.ylabel("Temperatura mínima média (°C)")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    nome_arquivo = f"grafico_minimas_{mes:02d}_2006_2016.png"
    plt.savefig(nome_arquivo, dpi=150)
    print(f"Gráfico salvo como: {nome_arquivo}")
    # plt.show()  # opcional para abrir janela interativa
    return nome_arquivo


def media_geral(medias: Dict[int, float]) -> Optional[float]:
    """Calcula a média geral a partir do dicionário de médias (ano → média)."""
    if not medias:
        return None
    vs = list(medias.values())
    return sum(vs) / len(vs)


# ----------------------------
# Interface de usuário (menu)
# ----------------------------

def ler_int(prompt: str, minimo: Optional[int] = None, maximo: Optional[int] = None) -> int:
    """Lê um inteiro com validação opcional de faixa."""
    while True:
        try:
            v = int(input(prompt).strip())
            if minimo is not None and v < minimo:
                print(f"Valor mínimo é {minimo}.")
                continue
            if maximo is not None and v > maximo:
                print(f"Valor máximo é {maximo}.")
                continue
            return v
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")


def menu(registros: List[Registro]) -> None:
    """Exibe o menu de opções e executa as funcionalidades requeridas."""
    while True:
        print("\n=== MENU ===")
        print("1) Visualizar intervalo (texto)")
        print("2) Mês mais chuvoso (todo o período)")
        print("3) Médias da temp. mínima para um mês (2006–2016)")
        print("4) Gráfico das médias (item 3)")
        print("5) Média geral da temp. mínima (2006–2016) para o mês escolhido")
        print("0) Sair")
        op = ler_int("Escolha uma opção: ", 0, 5)

        if op == 0:
            print("Encerrando. Obrigado!")
            break

        elif op == 1:
            print("\n- Intervalo (mês/ano) -")
            mes_ini = ler_int("Mês inicial (1-12): ", 1, 12)
            ano_ini = ler_int("Ano inicial (ex.: 1961): ")
            mes_fim = ler_int("Mês final (1-12): ", 1, 12)
            ano_fim = ler_int("Ano final (ex.: 2016): ")

            if (ano_ini, mes_ini) > (ano_fim, mes_fim):
                print("Intervalo inválido: início é posterior ao fim.")
                continue

            print("\nO que deseja ver?")
            print("1) Todos os dados")
            print("2) Só precipitação")
            print("3) Só temperaturas (máx/mín/méd)")
            print("4) Só umidade e vento")
            modo = ler_int("Escolha (1-4): ", 1, 4)

            regs = filtrar_por_intervalo(registros, mes_ini, ano_ini, mes_fim, ano_fim)
            imprimir_registros(regs, modo)

        elif op == 2:
            ano, mes, total = mes_mais_chuvoso(registros)
            print(f"Mês mais chuvoso: {nome_mes_pt(mes)} de {ano} | Total precipitação = {total:.1f} mm")

        elif op == 3:
            mes = ler_int("Informe o mês (1-12): ", 1, 12)
            medias = medias_minimas_mes_2006_2016(registros, mes)
            if not medias:
                print("Sem dados suficientes para esse mês no período 2006–2016.")
            else:
                print(f"Médias da temperatura mínima — {nome_mes_pt(mes)} (2006–2016):")
                print("Ano | Média (°C)")
                print("----------------")
                for ano in sorted(medias):
                    print(f"{ano} | {medias[ano]:.2f}")

        elif op == 4:
            mes = ler_int("Informe o mês (1-12) para o gráfico: ", 1, 12)
            medias = medias_minimas_mes_2006_2016(registros, mes)
            arq = plotar_barras_medias_minimas(medias, mes)
            if arq:
                print("Gráfico gerado com sucesso.")

        elif op == 5:
            mes = ler_int("Informe o mês (1-12): ", 1, 12)
            medias = medias_minimas_mes_2006_2016(registros, mes)
            mg = media_geral(medias)
            if mg is None:
                print("Sem dados suficientes para calcular a média geral.")
            else:
                print(f"Média geral da temperatura mínima em {nome_mes_pt(mes)} (2006–2016): {mg:.2f} °C")

        else:
            print("Opção inválida.")


def main() -> None:
    """Ponto de entrada do programa."""
    print("Carregando dados... (aguarde)")
    try:
        registros = carregar_dados_csv(CSV_NOME_PADRAO)
    except FileNotFoundError as e:
        print(e)
        return
    except KeyError as e:
        print(f"Erro no cabeçalho do CSV: {e}")
        return

    # Breve resumo
    if registros:
        print(f"Registros carregados: {len(registros)}")
        d0, d1 = registros[0]["data"], registros[-1]["data"]
        print(f"Período carregado: {d0.strftime('%d/%m/%Y')} a {d1.strftime('%d/%m/%Y')}")

    # Chama o menu
    menu(registros)


if __name__ == "__main__":
    main()
