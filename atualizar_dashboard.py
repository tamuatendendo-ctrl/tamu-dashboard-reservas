# -*- coding: utf-8 -*-

"""
TAMU — Atualização automática da Dashboard

Consulta a API Stays usando a data de criação da reserva,
reconstrói o histórico e mantém as informações do cadastro mestre
dos 72 apartamentos da operação.

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

# Reservas futuras: consulta por data de check-in (arrival).
# Mantemos 12 meses à frente para alimentar a seção de reservas futuras.
DATA_INICIO_FUTURO = date.today()
DATA_FIM_FUTURO = date.today() + timedelta(days=365)

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
    date_type="creation",
):

    payload = {
        "from": inicio.isoformat(),
        "to": fim.isoformat(),
        "dateType": date_type,
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
                f"(dateType={date_type}, tentativa "
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


def normalizar_codigo_apto(codigo):

    # A Stays pode retornar o mesmo apartamento com espaços
    # internos (ex.: "161136 A"), enquanto o cadastro mestre
    # usa "161136A".
    return "".join(
        str(codigo or "").upper().split()
    )


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

    return normalizar_codigo_apto(codigo)


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

    # Na API Stays, o estado operacional da reserva vem em
    # "type" (booked, reserved, canceled, blocked, maintenance).
    # Os campos status/reservationStatus/bookingStatus podem vir vazios.
    valor = reserva.get("type")

    if valor:
        return str(valor).strip().lower()

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

    return str(valor).strip().lower()


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
    # LER CADASTRO MESTRE DOS 72 APARTAMENTOS
    # --------------------------------------------------------
    # O cadastro mestre é a fonte oficial da operação.
    # Não usamos a lista de "apartamentos" do JSON analítico,
    # pois ela pode ter sido reduzida por cruzamentos anteriores.

    ARQUIVO_MESTRE = "apartamentos_mestre.json"

    if not os.path.exists(ARQUIVO_MESTRE):
        raise RuntimeError(
            f"{ARQUIVO_MESTRE} não encontrado. "
            "Mantenha o cadastro mestre no mesmo diretório."
        )

    with open(
        ARQUIVO_MESTRE,
        encoding="utf-8",
    ) as f:
        mestre_data = json.load(f)

    apartamentos = mestre_data.get(
        "apartamentos",
        []
    ) if isinstance(mestre_data, dict) else mestre_data

    if not apartamentos:
        raise RuntimeError(
            "O cadastro mestre não contém apartamentos da operação."
        )

    apt_por_codigo = {
        normalizar_codigo_apto(
            apto.get(
                "codigo_apto",
                "",
            )
        ): apto
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

    # --------------------------------------------------------
    # HISTÓRICO — DATA DE CRIAÇÃO
    # --------------------------------------------------------

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
            date_type="creation",
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

    print()
    print(
        f"Reservas únicas após histórico: "
        f"{len(todas_reservas)}"
    )

    # --------------------------------------------------------
    # FUTURO — DATA DE CHECK-IN (ARRIVAL)
    # --------------------------------------------------------
    #
    # Esta segunda consulta é necessária porque a busca por
    # creation não é suficiente para alimentar os meses futuros.
    # A API Stays aceita dateType=arrival para buscar pela data
    # de check-in.
    #

    print()
    print(
        "Consultando reservas futuras por check-in "
        f"({DATA_INICIO_FUTURO} -> {DATA_FIM_FUTURO})"
    )

    cursor = primeiro_dia_mes(DATA_INICIO_FUTURO)

    while cursor <= DATA_FIM_FUTURO:

        inicio = max(
            primeiro_dia_mes(cursor),
            DATA_INICIO_FUTURO,
        )

        fim = min(
            ultimo_dia_mes(cursor),
            DATA_FIM_FUTURO,
        )

        reservas_futuras = consultar_periodo(
            session,
            inicio,
            fim,
            date_type="arrival",
        )

        for reserva in reservas_futuras:

            rid = id_reserva(
                reserva
            )

            if rid and rid not in todas_reservas:
                todas_reservas[rid] = reserva

        cursor = proximo_mes(
            cursor
        )

    reservas = list(
        todas_reservas.values()
    )

    print()
    print(
        f"Reservas únicas após histórico + futuro: "
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

            "tipo":
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

        # Apenas reservas efetivas entram nos indicadores de
        # volume/performance. Bloqueios e manutenção são eventos
        # operacionais do calendário, não reservas.
        if linha.get("status") in {"blocked", "maintenance"}:
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

            "reservas_futuras_checkin":
                sum(
                    1
                    for linha in linhas
                    if linha.get("checkin")
                    and linha.get("checkin") >= date.today().isoformat()
                ),

            "reservas_nossos_aptos":
                len(linhas),

            "reservas_sem_apto":
                len(reservas_sem_apto),

            "reservas_booked":
                sum(1 for linha in linhas if linha.get("status") == "booked"),

            "reservas_reserved":
                sum(1 for linha in linhas if linha.get("status") == "reserved"),

            "reservas_canceled":
                sum(1 for linha in linhas if linha.get("status") == "canceled"),

            "reservas_blocked":
                sum(1 for linha in linhas if linha.get("status") == "blocked"),

            "reservas_maintenance":
                sum(1 for linha in linhas if linha.get("status") == "maintenance"),
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
        "Tipos: "
        f"booked={sum(1 for linha in linhas if linha.get('status') == 'booked')}, "
        f"reserved={sum(1 for linha in linhas if linha.get('status') == 'reserved')}, "
        f"canceled={sum(1 for linha in linhas if linha.get('status') == 'canceled')}, "
        f"blocked={sum(1 for linha in linhas if linha.get('status') == 'blocked')}, "
        f"maintenance={sum(1 for linha in linhas if linha.get('status') == 'maintenance')}"
    )

    print(
        f"Apartamentos: "
        f"{len(resultado_aptos)}"
    )


if __name__ == "__main__":
    main()
