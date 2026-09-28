# -*- coding: utf-8 -*-

"""
TAMU — Atualização automática da Dashboard

Consulta a API Stays usando a data de criação da reserva,
reconstrói o histórico e mantém as informações dos 72
apartamentos da operação.

Independente do New_monitor_reservas.py.
"""

import os
import json
import time
from datetime import date, timedelta

import requests
from requests.auth import HTTPBasicAuth


# ============================================================
# CONFIGURAÇÃO
# ============================================================

URL_API = "https://mdc.stays.com.br"
ENDPOINT = f"{URL_API}/external/v1/booking/reservations-export"

LOGIN = os.getenv("STAYS_LOGIN")
SENHA = os.getenv("STAYS_SENHA")

ARQUIVO_ANALISE = "analise_reservas_apartamentos.json"

DATA_INICIO = date(2025, 1, 1)
DATA_FIM = date.today()

TIMEOUT = 180
TENTATIVAS = 3


# ============================================================
# SESSÃO
# ============================================================

def criar_sessao():

    if not LOGIN or not SENHA:
        raise RuntimeError(
            "STAYS_LOGIN e STAYS_SENHA não foram configurados."
        )

    session = requests.Session()

    session.auth = HTTPBasicAuth(
        LOGIN,
        SENHA,
    )

    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
    })

    return session


# ============================================================
# DATAS
# ============================================================

def primeiro_dia_mes(d):

    return d.replace(day=1)


def proximo_mes(d):

    if d.month == 12:
        return date(
            d.year + 1,
            1,
            1,
        )

    return date(
        d.year,
        d.month + 1,
        1,
    )


def ultimo_dia_mes(d):

    return proximo_mes(d) - timedelta(days=1)


# ============================================================
# EXTRAÇÃO DA RESPOSTA
# ============================================================

def extrair_lista_reservas(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        for chave in (
            "reservations",
            "reserves",
            "data",
            "results",
            "items",
        ):

            valor = data.get(chave)

            if isinstance(valor, list):
                return valor

        if "_id" in data or "id" in data:
            return [data]

    return []


# ============================================================
# CONSULTA STAYS
# ============================================================

def consultar_periodo(
    session,
    inicio,
    fim,
):

    payload = {
        "from": inicio.isoformat(),
        "to": fim.isoformat(),
        "dateType": "creation",
    }

    ultimo_erro = None

    for tentativa in range(
        1,
        TENTATIVAS + 1,
    ):

        try:

            print(
                f"Consultando "
                f"{inicio} -> {fim} "
                f"(tentativa "
                f"{tentativa}/{TENTATIVAS})"
            )

            response = session.post(
                ENDPOINT,
                json=payload,
                timeout=TIMEOUT,
            )

            if response.status_code != 200:

                try:
                    detalhe = response.json()
                except Exception:
                    detalhe = response.text[:500]

                raise RuntimeError(
                    f"HTTP {response.status_code}: "
                    f"{detalhe}"
                )

            reservas = extrair_lista_reservas(
                response.json()
            )

            print(
                f"  Reservas retornadas: "
                f"{len(reservas)}"
            )

            return reservas

        except Exception as exc:

            ultimo_erro = exc

            print(
                f"  Erro: {exc}"
            )

            if tentativa < TENTATIVAS:

                espera = 5 * tentativa

                print(
                    f"  Aguardando "
                    f"{espera}s..."
                )

                time.sleep(espera)

    raise RuntimeError(
        f"Falha ao consultar "
        f"{inicio} -> {fim}: "
        f"{ultimo_erro}"
    )


# ============================================================
# FUNÇÕES DE RESERVA
# ============================================================

def id_reserva(reserva):

    return str(
        reserva.get("_id")
        or reserva.get("id")
        or ""
    ).strip()


def codigo_apartamento(reserva):

    listing = (
        reserva.get("listing")
        or {}
    )

    codigo = (
        listing.get("internalName")
        or reserva.get("internalName")
        or ""
    )

    return str(codigo).strip().upper()


def canal_reserva(reserva):

    canal = str(
        reserva.get("canal")
        or reserva.get("channel")
        or reserva.get("partnerName")
        or ""
    ).strip().lower()

    if "booking" in canal:
        return "Booking"

    if "airbnb" in canal:
        return "Airbnb"

    if "website" in canal:
        return "Website"

    if canal:
        return "Outro"

    return "Sem canal"


def data_criacao(reserva):

    return str(
        reserva.get("creationDate")
        or reserva.get("creationDateTime")
        or ""
    )[:10]


def data_checkin(reserva):

    return str(
        reserva.get("checkInDate")
        or ""
    )[:10]


def data_checkout(reserva):

    return str(
        reserva.get("checkOutDate")
        or ""
    )[:10]


def status_reserva(reserva):

    valor = (
        reserva.get("status")
        or reserva.get("reservationStatus")
        or reserva.get("bookingStatus")
        or ""
    )

    if isinstance(valor, dict):

        valor = (
            valor.get("name")
            or valor.get("status")
            or ""
        )

    return str(valor)


# ============================================================
# RESPONSÁVEL PELA RESERVA
# ============================================================

def responsavel_reserva(
    apartamento,
    canal,
):

    # Toda reserva Booking pertence à Evellyn.
    if canal == "Booking":
        return "Evellyn"

    # Airbnb segue o responsável pelo apartamento.
    if canal == "Airbnb":

        return apartamento.get(
            "responsavel_apto",
            "Não definido",
        )

    return "Não definido"


# ============================================================
# PRINCIPAL
# ============================================================

def main():

    print("=" * 70)
    print(
        "TAMU — ATUALIZAÇÃO AUTOMÁTICA DA DASHBOARD"
    )
    print("=" * 70)

    if not os.path.exists(
        ARQUIVO_ANALISE
    ):

        raise RuntimeError(
            f"{ARQUIVO_ANALISE} "
            "não encontrado."
        )

    # --------------------------------------------------------
    # LER BASE ATUAL DOS 72 APARTAMENTOS
    # --------------------------------------------------------

    with open(
        ARQUIVO_ANALISE,
        encoding="utf-8",
    ) as f:

        analise_atual = json.load(f)

    apartamentos = analise_atual.get(
        "apartamentos",
        [],
    )

    if not apartamentos:

        raise RuntimeError(
            "A base atual não contém "
            "os apartamentos da operação."
        )

    apt_por_codigo = {
        str(
            apto.get(
                "codigo_apto",
                "",
            )
        ).strip().upper(): apto
        for apto in apartamentos
    }

    print(
        f"Apartamentos cadastrados: "
        f"{len(apt_por_codigo)}"
    )

    # --------------------------------------------------------
    # CONSULTAR STAYS
    # --------------------------------------------------------

    session = criar_sessao()

    todas_reservas = {}

    cursor = DATA_INICIO

    while cursor <= DATA_FIM:

        inicio = primeiro_dia_mes(
            cursor
        )

        fim = min(
            ultimo_dia_mes(cursor),
            DATA_FIM,
        )

        reservas = consultar_periodo(
            session,
            inicio,
            fim,
        )

        for reserva in reservas:

            rid = id_reserva(
                reserva
            )

            if rid:
                todas_reservas[rid] = reserva

        cursor = proximo_mes(
            inicio
        )

    reservas = list(
        todas_reservas.values()
    )

    print()
    print(
        f"Reservas únicas encontradas: "
        f"{len(reservas)}"
    )

    # --------------------------------------------------------
    # CRUZAR RESERVAS COM APARTAMENTOS
    # --------------------------------------------------------

    linhas = []
    reservas_sem_apto = []

    for reserva in reservas:

        codigo = codigo_apartamento(
            reserva
        )

        apartamento = apt_por_codigo.get(
            codigo
        )

        if not apartamento:

            reservas_sem_apto.append({
                "codigo_apto": codigo,
                "canal": canal_reserva(
                    reserva
                ),
                "id_reserva": id_reserva(
                    reserva
                ),
            })

            continue

        canal = canal_reserva(
            reserva
        )

        criacao = data_criacao(
            reserva
        )

        ano = ""
        mes = ""

        if len(criacao) >= 7:

            ano = criacao[:4]
            mes = criacao[:7]

        linha = {
            "id_reserva": id_reserva(
                reserva
            ),

            "codigo_apto": codigo,

            "responsavel_apto":
                apartamento.get(
                    "responsavel_apto",
                    "Não definido",
                ),

            "responsavel_reserva":
                responsavel_reserva(
                    apartamento,
                    canal,
                ),

            "canal": canal,

            "ano": ano,

            "mes": mes,

            "checkin":
                data_checkin(
                    reserva
                ),

            "checkout":
                data_checkout(
                    reserva
                ),

            "status":
                status_reserva(
                    reserva
                ),
        }

        linhas.append(
            linha
        )

    # --------------------------------------------------------
    # RECALCULAR RESUMO DOS APARTAMENTOS
    # --------------------------------------------------------

    por_apto = {}

    for codigo, apartamento in apt_por_codigo.items():

        por_apto[codigo] = {
            "codigo_apto": codigo,
            "responsavel_apto":
                apartamento.get(
                    "responsavel_apto",
                    "Não definido",
                ),
            "reservas_2025": 0,
            "reservas_2026": 0,
            "reservas_total": 0,
            "airbnb": 0,
            "booking": 0,
            "website": 0,
            "outro": 0,
            "sem_canal": 0,
        }

    for linha in linhas:

        codigo = linha[
            "codigo_apto"
        ]

        info = por_apto.get(
            codigo
        )

        if not info:
            continue

        info["reservas_total"] += 1

        ano = linha["ano"]

        if ano == "2025":
            info["reservas_2025"] += 1

        elif ano == "2026":
            info["reservas_2026"] += 1

        canal = linha["canal"]

        if canal == "Airbnb":
            info["airbnb"] += 1

        elif canal == "Booking":
            info["booking"] += 1

        elif canal == "Website":
            info["website"] += 1

        elif canal == "Outro":
            info["outro"] += 1

        else:
            info["sem_canal"] += 1

    resultado_aptos = list(
        por_apto.values()
    )

    # --------------------------------------------------------
    # GERAR NOVA BASE
    # --------------------------------------------------------

    saida = {

        "regras": {

            "booking_responsavel":
                "Evellyn",

            "airbnb_responsavel":
                "responsavel_apto",

            "outros_canais":
                "Não definido",

            "apartamentos_considerados":
                len(resultado_aptos),

            "atualizado_em":
                date.today().isoformat(),
        },

        "totais": {

            "reservas_historico":
                len(reservas),

            "reservas_nossos_aptos":
                len(linhas),

            "reservas_sem_apto":
                len(reservas_sem_apto),
        },

        "reservas":
            linhas,

        "apartamentos":
            resultado_aptos,

        "reservas_sem_apto":
            reservas_sem_apto,
    }

    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    with open(
        ARQUIVO_ANALISE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            saida,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 70)
    print("ATUALIZAÇÃO CONCLUÍDA")
    print("=" * 70)

    print(
        f"Reservas totais: "
        f"{len(reservas)}"
    )

    print(
        f"Reservas nos nossos apartamentos: "
        f"{len(linhas)}"
    )

    print(
        f"Reservas sem apartamento: "
        f"{len(reservas_sem_apto)}"
    )

    print(
        f"Apartamentos: "
        f"{len(resultado_aptos)}"
    )


if __name__ == "__main__":
    main()
