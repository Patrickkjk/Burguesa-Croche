import logging
import math
import os
import re

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import httpx

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.database import conectar


router = APIRouter(
    prefix="/frete",
    tags=["Frete"],
)

logger = logging.getLogger(__name__)


# MODELO DA SOLICITAÇÃO

class CotacaoFrete(BaseModel):
    produto_id: int = Field(
        gt=0,
        description="Identificador da peça cadastrada.",
    )

    cep_destino: str = Field(
        pattern=r"^[0-9]{5}-?[0-9]{3}$",
        description="CEP com oito números, com ou sem hífen.",
    )


# CONFIGURAÇÃO DA INTEGRAÇÃO

def obter_configuracao():
    ambiente = os.getenv(
        "MELHOR_ENVIO_AMBIENTE",
        "sandbox",
    ).strip().lower()

    if ambiente not in {"sandbox", "producao"}:
        raise HTTPException(
            status_code=503,
            detail="O ambiente da integração de frete está inválido.",
        )

    token = os.getenv("MELHOR_ENVIO_TOKEN", "").strip()
    cep_origem = os.getenv("MELHOR_ENVIO_CEP_ORIGEM", "").strip()
    email_contato = os.getenv("MELHOR_ENVIO_EMAIL_CONTATO", "").strip()

    # Aceita CEP de origem com ou sem hífen.
    if re.fullmatch(r"[0-9]{5}-?[0-9]{3}", cep_origem):
        cep_origem = cep_origem.replace("-", "")
    else:
        cep_origem = ""

    if (
        not token
        or "\n" in token
        or "\r" in token
        or not cep_origem
        or "@" not in email_contato
        or "\n" in email_contato
        or "\r" in email_contato
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "A consulta de frete ainda não está configurada. "
                "Consulte o envio com a atendente."
            ),
        )

    base_url = (
        "https://sandbox.melhorenvio.com.br"
        if ambiente == "sandbox"
        else "https://melhorenvio.com.br"
    )

    return {
        "ambiente": ambiente,
        "token": token,
        "cep_origem": cep_origem,
        "email_contato": email_contato,
        "base_url": base_url,
    }


# CONSULTA DA PEÇA NO BANCO

def buscar_produto_para_frete(produto_id):
    conexao = conectar()

    try:
        linha = conexao.execute(
            """
            SELECT *
            FROM produtos
            WHERE id = ?
              AND publicado = 1
              AND disponivel = 1
            """,
            (produto_id,),
        ).fetchone()

        if linha is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Peça não encontrada ou não disponível "
                    "para consulta de frete."
                ),
            )

        return dict(linha)

    finally:
        conexao.close()


# VALIDAÇÕES DOS DADOS

def numero_positivo(valor):
    try:
        numero = float(valor)

    except (TypeError, ValueError, OverflowError):
        return None

    if not math.isfinite(numero) or numero <= 0:
        return None

    return numero


def valor_monetario(valor):
    try:
        numero = Decimal(str(valor))

        if not numero.is_finite() or numero < 0:
            return None

        arredondado = numero.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        resultado = float(arredondado)

        if not math.isfinite(resultado):
            return None

        return resultado

    except (
        InvalidOperation,
        TypeError,
        ValueError,
        OverflowError,
    ):
        return None


def montar_volume(produto):
    campos = {
        "weight": "peso_envio_kg",
        "height": "altura_envio_cm",
        "width": "largura_envio_cm",
        "length": "comprimento_envio_cm",
    }

    volume = {}

    for campo_api, campo_banco in campos.items():
        valor = numero_positivo(produto.get(campo_banco))

        if valor is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Esta peça ainda não possui peso e dimensões "
                    "de envio completos. Consulte a atendente."
                ),
            )

        volume[campo_api] = valor

    preco = valor_monetario(produto.get("preco"))

    if preco is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "O valor da peça precisa ser confirmado "
                "antes de calcular o envio."
            ),
        )

    # O valor declarado vai em options.insurance_value (ver a rota).
    return volume, preco


# ORGANIZAÇÃO DAS OPÇÕES RETORNADAS

def extrair_opcoes_correios(resultados):
    opcoes = []

    for item in resultados:
        if not isinstance(item, dict):
            continue

        if item.get("error") or item.get("errors"):
            continue

        empresa = item.get("company")

        if not isinstance(empresa, dict):
            continue

        nome_empresa = str(empresa.get("name", "")).strip()

        # A plataforma pode retornar outras transportadoras.
        # No nosso catálogo, exibiremos somente Correios.
        if nome_empresa.casefold() != "correios":
            continue

        valor = valor_monetario(item.get("custom_price"))

        if valor is None:
            continue

        opcoes.append({
            "id": item.get("id"),
            "servico": item.get("name"),
            "transportadora": nome_empresa,
            "valor": valor,
            "moeda": item.get("currency") or "BRL",
            "prazo_transporte": item.get("custom_delivery_time"),
            "faixa_prazo_transporte": item.get("custom_delivery_range"),
        })

    opcoes.sort(key=lambda opcao: opcao["valor"])

    return opcoes


# ROTA DE COTAÇÃO

@router.post("/cotar")
async def cotar_frete(dados: CotacaoFrete):
    config = obter_configuracao()

    # O acesso SQLite é síncrono. Executamos a consulta
    # em uma thread para não bloquear a rota assíncrona.
    produto = await run_in_threadpool(
        buscar_produto_para_frete,
        dados.produto_id,
    )

    volume, valor_declarado = montar_volume(produto)

    cep_destino = dados.cep_destino.replace("-", "")

    payload = {
        "from": {
            "postal_code": config["cep_origem"],
        },
        "to": {
            "postal_code": cep_destino,
        },
        "volumes": [
            volume,
        ],
        "options": {
            "insurance_value": valor_declarado,
            "receipt": False,
            "own_hand": False,
        },
    }

    headers = {
        "Authorization": f"Bearer {config['token']}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": f"BurguesaCroche ({config['email_contato']})",
    }

    url = f"{config['base_url']}/api/v2/me/shipment/calculate"

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0),
        ) as client:
            resposta = await client.post(
                url,
                headers=headers,
                json=payload,
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=(
                "A consulta de frete demorou mais que o esperado. "
                "Tente novamente."
            ),
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail=(
                "Não foi possível conectar ao serviço de frete. "
                "Tente novamente mais tarde."
            ),
        )

    if resposta.status_code in (401, 403):
        logger.warning(
            "Melhor Envio recusou a autenticação/permissão: HTTP %s",
            resposta.status_code,
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "A integração de frete precisa de revisão "
                "das credenciais ou permissões."
            ),
        )

    if resposta.status_code == 429:
        raise HTTPException(
            status_code=503,
            detail=(
                "O serviço de frete atingiu um limite temporário. "
                "Tente novamente mais tarde."
            ),
        )

    if resposta.status_code in (400, 422):
        logger.warning(
            "Melhor Envio rejeitou a cotação: HTTP %s - %s",
            resposta.status_code,
            resposta.text[:500],
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Não foi possível cotar com os dados informados. "
                "Confira o CEP e os dados da embalagem."
            ),
        )

    if not resposta.is_success:
        logger.warning(
            "Falha na cotação Melhor Envio: HTTP %s",
            resposta.status_code,
        )

        raise HTTPException(
            status_code=502,
            detail="O serviço de frete está indisponível no momento.",
        )

    try:
        resultados = resposta.json()

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="O serviço de frete retornou uma resposta inválida.",
        )

    if not isinstance(resultados, list):
        raise HTTPException(
            status_code=502,
            detail="O serviço de frete retornou um formato inesperado.",
        )

    opcoes = extrair_opcoes_correios(resultados)

    teste = config["ambiente"] == "sandbox"

    return {
        "produto_id": produto["id"],
        "produto_nome": produto["nome"],
        "cep_destino": cep_destino,
        "ambiente": config["ambiente"],
        "teste": teste,
        "prazo_producao": produto.get("prazo_producao") or "",
        "opcoes": opcoes,
        "aviso": (
            "SIMULAÇÃO DE TESTE. Não apresentar como cotação real."
            if teste
            else (
                "Estimativa de envio pelos Correios via Melhor Envio. "
                "Valor e prazo sujeitos à confirmação no atendimento. "
                "O prazo de produção é separado do transporte."
            )
        ),
        "mensagem": (
            ""
            if opcoes
            else (
                "Nenhuma opção dos Correios disponível "
                "nesta consulta. Fale com a atendente."
            )
        ),
    }