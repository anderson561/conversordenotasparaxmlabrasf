"""NFS-e da Prefeitura Municipal do Natal/RN - "Nota Natalense" (`LAYOUT_NATAL`).

Achado real 2026-11-19: NFS-e nº 0000000015 (`PRISCILA FARIAS_NF15.pdf`, 1
página SEM camada de texto - só OCR), PRISCILA FARIAS CARVALHO VALIAS ->
NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA, R$ 20.857,95,
prestador do Simples Nacional. Sem layout próprio a página caía em
`LAYOUT_GENERICO`, era descartada como "Layout não reconhecido" e a conversão
terminava com a mensagem enganosa "parece ser baseado em imagem/scan ou
vazio" - nenhum XML.

Estrutura impressa (o Tesseract lê rótulo e valor na MESMA linha):

- cabeçalho "Prefeitura Municipal do Natal" / "Secretaria Municipal de
  Finanças" / "Nota Fiscal de Serviços Eletrônica - NFS-e" / "Nota Natalense",
  com "Nº da Nota", "Competência: MAR/2026", "Data Prestação Serviço",
  "Nº da Nota Substituída", "Data/Hora de Emissão: dd/mm/aaaa às hh:mm:ss" e
  "Código de Verificação";
- blocos "Prestador de Serviços" e "Tomador de Serviços" (endereço numa
  linha só: "<logradouro>, <número>, [<complemento>,] <bairro>, <CEP>");
- "Serviços": "7.01.04 - <descrição>" (item 7.01 da LC 116 + desdobramento
  municipal), "NBS: ...", grade "Item | Descrição | Quant. | Vlr. Unitário |
  Valor Total" e "Valor Total da NFS-e R$";
- grade de 2 linhas "Deduções | Base Cálculo | Alíquota | Valor do ISS |
  Outras Retenções" e "INSS | IRPJ | CSLL | COFINS | PIS/PASEP". Prestador do
  Simples Nacional sai com "*,**" (mascarado) nas 4 primeiras células, que o
  OCR nem sempre lê - mascarado e em branco ficam indistinguíveis no texto.

Função pura sobre texto (testável sem PDF), exceto `reler_linha_endereco`,
que faz um recorte OCR pontual. Onde a leitura não fecha: sentinela + aviso,
nunca valor fabricado.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from ..models.nfse_models import Endereco, Entidade, Valores

CODIGO_IBGE_NATAL = '2408102'

_SENTINELA_DOC = '00000000000000'
_SENTINELA_NUMERO = '00000000'
_SENTINELA_CODIGO_VERIFICACAO = '000000000'
_DISCRIMINACAO_PADRAO = 'Serviços prestados conforme nota fiscal.'

# O cabeçalho da prefeitura fica no topo: um "Natal" lá no meio é endereço de
# prestador/tomador de nota de OUTRA cidade, nunca o cabeçalho.
_JANELA_CABECALHO = 600

_MOEDA = r'\d{1,3}(?:\.\d{3})*,\d{2,4}'
# Célula mascarada pela prefeitura ("*,**"); o OCR pode trocar a vírgula.
_MASCARA = r'\*+\s*[,.]?\s*\*+'
_DOC = r'\d{2}\.?\d{3}\.?\d{3}\s*/?\s*\d{4}\s*-?\s*\d{2}|\d{3}\.?\d{3}\.?\d{3}\s*-?\s*\d{2}'

_MESES = {
    'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12,
}

# Domínios de webmail para corrigir, em e-mail TODO MAIÚSCULO, o "@" que o
# OCR lê como "Q"/"QQ" ("PFCVALIASQGMAIL.COM"). Fora desta lista não há como
# saber qual maiúscula é o "@": o e-mail é descartado em vez de inventado.
_WEBMAILS = r'GMAIL|HOTMAIL|YAHOO|OUTLOOK|LIVE|ICLOUD|UOL|BOL|TERRA|IG'


@dataclass
class NotaNatal:
    numero: str
    codigo_verificacao: str
    data_emissao: datetime
    competencia: datetime
    prestador: Entidade
    tomador: Entidade
    discriminacao: str
    codigo_servico: str
    valores: Valores
    optante_simples: bool = False
    regime_especial: Optional[str] = None
    avisos: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def eh_natal(texto: str) -> bool:
    """Cabeçalho da Prefeitura do Natal no topo + título da NFS-e + marca
    "Nota Natalense" ou "Secretaria Municipal de Finanças" + os 2 blocos de
    entidade. A palavra "Natal" solta (município de prestador/tomador de
    outra prefeitura) nunca basta."""
    if not texto:
        return False
    topo = texto[:_JANELA_CABECALHO]
    return bool(
        re.search(r'Prefeitura\s+Municipal\s+d[oe]\s+Natal\b', topo, re.IGNORECASE)
        and re.search(r'Nota\s+Natalense|Secretaria\s+Municipal\s+de\s+Finan[çc]as', topo, re.IGNORECASE)
        and re.search(r'Nota\s+Fiscal\s+de\s+Servi[çc]os?\s+Eletr[ôo]nica|NFS-?e', topo, re.IGNORECASE)
        and re.search(r'Prestador\s+de\s+Servi[çc]os?', texto, re.IGNORECASE)
        and re.search(r'Tomador\s+de\s+Servi[çc]os?', texto, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _colapsa(s: Optional[str]) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def _sem_acento(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _valor_br(s: str) -> float:
    return float(s.replace('.', '').replace(',', '.'))


def _br(x: float) -> str:
    return f"{x:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')


def _rotulo_linha(bloco: str, rotulo: str) -> Optional[str]:
    """Valor na MESMA linha do rótulo; None se o campo veio em branco (nunca
    captura a linha seguinte)."""
    m = re.search(r'(?:^|[ \t])' + rotulo + r'[ \t]*:[ \t|]*([^\n]*)', bloco, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    # Corta no próximo rótulo da mesma linha ("Telefone: (84) ... E-mail: ...").
    valor = re.split(r'\s+(?:E-?\s?mail|UF|Estado|Inscri[çc][ãa]o\s+Municipal)\s*:', m.group(1),
                     maxsplit=1, flags=re.IGNORECASE)[0]
    return _colapsa(valor) or None


def corrigir_email(raw: Optional[str]) -> Optional[str]:
    """E-mail lido pelo OCR. O "@" sai como maiúscula(s) solta(s):
    "lorenaQQnauticamoveis.com" (minúsculas em volta - inequívoco) ou
    "PFCVALIASQGMAIL.COM" (tudo maiúsculo - só corrigido antes de um
    domínio de webmail conhecido). Sem correção segura -> None."""
    s = (raw or '').strip().strip('|').strip()
    if not s:
        return None
    if re.fullmatch(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', s):
        return s
    m = re.fullmatch(r'([a-z0-9._+-]+)[A-Z]+([a-z0-9-]+(?:\.[a-z0-9-]+)+)', s)
    if m:
        return f"{m.group(1)}@{m.group(2)}"
    m = re.fullmatch(r'([A-Z0-9._+-]+?)Q{1,2}((?:' + _WEBMAILS + r')(?:\.[A-Z]{2,4})+)', s)
    if m:
        return f"{m.group(1)}@{m.group(2)}"
    return None


def _telefone(raw: Optional[str]) -> Optional[str]:
    digitos = re.sub(r'\D', '', raw or '')
    return digitos if len(digitos) in (10, 11) else None


def separar_endereco(raw: Optional[str]) -> Tuple[str, str, Optional[str], str, str]:
    """"<logradouro>, <número>, [<complemento>, ...] <bairro>, <CEP>" ->
    (logradouro, número, complemento, bairro, CEP só dígitos)."""
    partes = [p.strip() for p in _colapsa(raw).split(',') if p.strip()]
    cep = ''
    if partes and re.fullmatch(r'\d{5}\s*-?\s*\d{3}', partes[-1]):
        cep = re.sub(r'\D', '', partes.pop())
    if not partes:
        return 'Não informado', 'S/N', None, 'Não informado', cep
    logradouro = partes.pop(0)
    numero = 'S/N'
    if partes and re.fullmatch(r'\d+[A-Za-z]?|S\s*/?\s*N', partes[0], re.IGNORECASE):
        numero = re.sub(r'\s+', '', partes.pop(0)).upper()
    bairro = partes.pop() if partes else 'Não informado'
    complemento = ', '.join(partes) or None
    return logradouro, numero, complemento, bairro, cep


def _item_lc116(texto: str, avisos: List[str]) -> str:
    """"7.01.04 - Arquitetura..." -> "0701". O 3º segmento ("04") é o
    desdobramento municipal de Natal, não faz parte do item da LC 116."""
    m = re.search(r'^\s*(\d{1,2})\s*\.\s*(\d{2})(?:\s*\.\s*\d{1,3})?\s*-\s*\S', texto, re.MULTILINE)
    if m:
        if 1 <= int(m.group(1)) <= 40:
            return m.group(1).zfill(2) + m.group(2)
        avisos.append(f"Item de serviço impresso ({m.group(1)}.{m.group(2)}) não existe na lista da "
                      "LC 116/2003 - mantido como \"0000\"; classificar o serviço manualmente")
        return '0000'
    avisos.append("Item da lista de serviço não encontrado - mantido como \"0000\"; "
                  "classificar o serviço manualmente")
    return '0000'


# ---------------------------------------------------------------------------
# Entidades
# ---------------------------------------------------------------------------

def _entidade(papel: str, bloco: str, resolver, validar_doc: Callable[[str], bool],
              avisos: List[str]) -> Entidade:
    eh_prestador = papel == 'prestador'
    rot_razao = r'Raz[ãa]o\s+Social' if eh_prestador else r'Nome\s*/?\s*Raz[ãa]o\s+Social'
    razao = _rotulo_linha(bloco, rot_razao) or ''
    if not razao:
        razao = 'Prestador Não Identificado' if eh_prestador else 'Tomador Não Identificado'
        avisos.append(f"Razão social do {papel} não encontrada - conferir na nota")

    doc = _SENTINELA_DOC
    m = re.search(r'CPF\s*/?\s*CNPJ[^:\n]{0,6}:[ \t]*(' + _DOC + r')', bloco, re.IGNORECASE)
    if m:
        doc = re.sub(r'\D', '', m.group(1))
        if not validar_doc(doc):
            avisos.append(f"CNPJ/CPF do {papel} ({doc}) não passa na validação do dígito "
                          "verificador - mantido como impresso; conferir na nota")
    else:
        avisos.append(f"CNPJ/CPF do {papel} não lido - mantido como sentinela {_SENTINELA_DOC}; "
                      "conferir na nota")

    im = None
    m = re.search(r'Inscri[çc][ãa]o\s+Municipal\s*:[ \t]*([0-9][0-9A-Za-z.\-/]*)', bloco, re.IGNORECASE)
    if m:
        im = re.sub(r'[^0-9A-Za-z]', '', m.group(1)) or None

    logradouro, numero, complemento, bairro, cep = separar_endereco(
        _rotulo_linha(bloco, r'Endere[çc]o'))

    municipio, uf = '', ''
    m = re.search(r'(?:Munic[íi]pio|Cidade)\s*:[ \t]*([^\n]*?)[ \t]+(?:UF|Estado)\s*:[ \t]*([A-Za-z]{2})\b',
                  bloco, re.IGNORECASE)
    if m:
        municipio, uf = _colapsa(m.group(1)), m.group(2).upper()
    else:
        municipio = re.sub(r'\s+(?:UF|Estado)\s*:.*$', '', _rotulo_linha(bloco, r'(?:Munic[íi]pio|Cidade)') or '')
        uf = ((_rotulo_linha(bloco, r'(?:UF|Estado)') or '')[:2]).upper()
    if eh_prestador and not municipio:
        # A prefeitura emissora é a de Natal: prestador sem município legível
        # é de Natal (mesmo racional da UF do prestador em Ribeirão Pires).
        municipio, uf = 'NATAL', 'RN'
        avisos.append("Município do prestador não lido - assumido Natal/RN (prefeitura emissora); "
                      "conferir na nota")
    if not re.fullmatch(r'[A-Z]{2}', uf or ''):
        uf = 'RN' if eh_prestador else ''
    codigo = ''
    if municipio and uf:
        codigo = resolver.extract_and_validate(municipio, uf, city_hint=municipio)
    elif not eh_prestador:
        avisos.append("Município/UF do tomador não lidos - conferir o código IBGE na nota")
        codigo = resolver.extract_and_validate(municipio or 'Não informado', uf or resolver.default_uf)
    if len(cep) != 8:
        cep = '00000000'

    return Entidade(
        cnpj_cpf=doc,
        inscricao_municipal=im,
        razao_social=razao,
        email=corrigir_email(_rotulo_linha(bloco, r'E-?\s?mail')),
        telefone=_telefone(_rotulo_linha(bloco, r'Telefone')),
        endereco=Endereco(
            logradouro=logradouro,
            numero=numero,
            complemento=complemento,
            bairro=bairro,
            codigo_municipio=codigo,
            municipio=municipio or None,
            uf=uf or resolver.default_uf,
            cep=cep,
        ),
    )


# ---------------------------------------------------------------------------
# Serviços e valores
# ---------------------------------------------------------------------------

_RE_ITEM = re.compile(
    r'^\s*(\d{1,3})\s+(.+?)\s+(' + _MOEDA + r')\s+(' + _MOEDA + r')\s+(' + _MOEDA + r')\s*$')


def _itens(texto: str) -> List[Tuple[str, float]]:
    """Linhas da grade "Item | Descrição | Quant. | Vlr. Unitário | Valor
    Total" -> [(descrição, valor total)]. Linha sem os 3 números é
    continuação da descrição do item anterior."""
    m = re.search(r'^[^\n]*\bDescri[çc][ãa]o\b[^\n]*Valor\s+Total[^\n]*\n([\s\S]*?)^[^\n]*Valor\s+Total\s+da\s+NFS',
                  texto, re.IGNORECASE | re.MULTILINE)
    if not m:
        return []
    itens: List[List] = []
    for linha in m.group(1).splitlines():
        if not linha.strip():
            continue
        mi = _RE_ITEM.match(linha)
        if mi:
            itens.append([_colapsa(mi.group(2)), _valor_br(mi.group(5))])
        elif itens:
            itens[-1][0] = f"{itens[-1][0]} {_colapsa(linha)}"
    return [(d, v) for d, v in itens]


def _linha_valores(trecho: str) -> List[Optional[float]]:
    """Células de uma linha de valores da grade, em ordem: número -> float,
    máscara "*,**" -> None."""
    celulas: List[Optional[float]] = []
    for m in re.finditer(r'(' + _MASCARA + r')|(' + _MOEDA + r')', trecho):
        celulas.append(None if m.group(1) else _valor_br(m.group(2)))
    return celulas


def _grade(texto: str, avisos: List[str]):
    """Lê as 2 linhas da grade de tributos. Devolve (linha1, linha2, mascarada),
    cada linha uma lista de 5 células (float, None = mascarada/ilegível) ou
    None quando a linha veio inteira em branco."""
    rot1 = re.search(r'^[^\n]*Dedu[çc][õo]es[^\n]*Base\s+C[áa]lculo[^\n]*\n', texto, re.IGNORECASE | re.MULTILINE)
    rot2 = re.search(r'^[^\n]*INSS[^\n]*COFINS[^\n]*\n', texto, re.IGNORECASE | re.MULTILINE)
    fim = re.search(r'Outras\s+Informa[çc][õo]es', texto, re.IGNORECASE)
    if not rot1:
        avisos.append("Grade \"Deduções / Base Cálculo / Alíquota / Valor do ISS\" não encontrada - "
                      "conferir os tributos na nota")
        return None, None, False
    ini2 = rot2.start() if rot2 and rot2.start() > rot1.end() else (fim.start() if fim else len(texto))
    trecho1 = texto[rot1.end():ini2]
    trecho2 = ''
    if rot2 and rot2.start() > rot1.end():
        trecho2 = texto[rot2.end():(fim.start() if fim and fim.start() > rot2.end() else len(texto))]
    mascarada = bool(re.search(_MASCARA, trecho1 + trecho2))

    linhas = []
    for nome, trecho in (('Deduções/Base/Alíquota/ISS/Outras Retenções', trecho1),
                         ('INSS/IRPJ/CSLL/COFINS/PIS', trecho2)):
        cel = _linha_valores(trecho)
        if not cel:
            linhas.append(None)
        elif len(cel) == 5:
            linhas.append(cel)
        else:
            # Alguma célula em branco no meio: sem posição confiável para
            # cada número, nada é mapeado (nunca deslocar valor de coluna).
            avisos.append(f"Grade \"{nome}\" com {len(cel)} de 5 valores legíveis - posição de cada "
                          "valor incerta, nenhum foi usado (mantidos 0,00); conferir na nota")
            linhas.append([None] * 5)
    return linhas[0], linhas[1], mascarada


def _valores(texto: str, itens: List[Tuple[str, float]], optante_simples: bool,
             avisos: List[str]) -> Valores:
    serv = None
    m = re.search(r'Valor\s+Total\s+da\s+NFS-?e\s*(?:R\s*\$)?\s*:?\s*(' + _MOEDA + r')', texto, re.IGNORECASE)
    if m:
        serv = _valor_br(m.group(1))
    soma_itens = round(sum(v for _, v in itens), 2) if itens else None
    if serv is None:
        if soma_itens:
            serv = soma_itens
            avisos.append(f"\"Valor Total da NFS-e\" não lido - usada a soma dos itens (R$ {_br(serv)}); "
                          "conferir na nota")
        else:
            serv = 0.0
            avisos.append("Valor dos serviços não lido (nem o \"Valor Total da NFS-e\" nem os itens) - "
                          "mantido 0,00; preencher conforme a nota")
    elif soma_itens is not None and abs(soma_itens - serv) > 0.011:
        avisos.append(f"Soma dos itens (R$ {_br(soma_itens)}) diverge do \"Valor Total da NFS-e\" "
                      f"(R$ {_br(serv)}) - mantido o total impresso; conferir na nota")

    lin1, lin2, mascarada = _grade(texto, avisos)
    lin1 = lin1 or [None] * 5
    deducoes, base, aliquota_pct, iss, outras = lin1
    inss, ir, csll, cofins, pis = lin2 or [None] * 5

    nao_lidos = [n for n, v in (('Deduções', deducoes), ('Base de Cálculo', base),
                                ('Alíquota', aliquota_pct), ('Valor do ISS', iss)) if v is None]
    if nao_lidos == ['Deduções']:
        nao_lidos = []  # só Deduções em branco: zero legítimo
    if nao_lidos:
        motivo = "mascarados (\"*,**\")" if mascarada else "em branco/mascarados"
        if optante_simples:
            avisos.append(
                f"Prestador optante do Simples Nacional: {', '.join(nao_lidos)} {motivo} na nota "
                "(ISS recolhido no DAS) - ValorIss e Alíquota mantidos 0,00 e Base de Cálculo = "
                "Valor dos Serviços - Deduções; nada derivado de Base x Alíquota")
        else:
            avisos.append(
                f"{', '.join(nao_lidos)} {motivo} na nota - ValorIss e Alíquota mantidos 0,00 e "
                "Base de Cálculo = Valor dos Serviços - Deduções; conferir o ISS na nota")
    deducoes = deducoes or 0.0
    if base is None:
        base = round(serv - deducoes, 2)
    aliquota = (aliquota_pct or 0.0) / 100
    if aliquota > 0.05 + 1e-9:
        avisos.append(f"Alíquota lida {_br(aliquota * 100)}% acima do teto legal de 5% "
                      "(LC 116/2003 art. 8º) - erro de leitura, mantida 0,00; conferir na nota")
        aliquota = 0.0
    iss = iss or 0.0
    if iss and aliquota and abs(round(base * aliquota, 2) - iss) > 0.011:
        avisos.append(f"Valor do ISS impresso (R$ {_br(iss)}) não fecha com Base x Alíquota "
                      f"(R$ {_br(base)} x {_br(aliquota * 100)}%) - mantido o impresso; conferir na nota")
    inss, ir, csll, cofins, pis, outras = (x or 0.0 for x in (inss, ir, csll, cofins, pis, outras))
    liquido = round(serv - (inss + ir + csll + cofins + pis + outras), 2)
    return Valores(
        valor_servicos=serv,
        valor_deducoes=deducoes,
        valor_pis=pis,
        valor_cofins=cofins,
        valor_inss=inss,
        valor_ir=ir,
        valor_csll=csll,
        outras_retencoes=outras,
        base_calculo=base,
        aliquota=aliquota,
        valor_iss=iss,
        # A nota não tem campo de ISS retido: sem indicação de retenção.
        iss_retido=False,
        valor_iss_retido=0.0,
        valor_liquido_nfse=liquido,
    )


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------

def _data(d: str, hora: Optional[str] = None) -> Optional[datetime]:
    try:
        dia, mes, ano = (int(x) for x in d.split('/'))
        h = mi = s = 0
        if hora:
            partes = [int(x) for x in hora.split(':')]
            h, mi = partes[0], partes[1]
            s = partes[2] if len(partes) > 2 else 0
        return datetime(ano, mes, dia, h, mi, s)
    except (ValueError, IndexError):
        return None


def _datas(texto: str, avisos: List[str]) -> Tuple[datetime, datetime]:
    emissao = None
    m = re.search(r'Data\s*/?\s*Hora\s+de\s+Emiss[ãa]o\s*:?\s*(\d{2}/\d{2}/\d{4})(?:\s*(?:[àa]s)?\s*(\d{2}:\d{2}(?::\d{2})?))?',
                  texto, re.IGNORECASE)
    if m:
        emissao = _data(m.group(1), m.group(2))
    if emissao is None:
        m = re.search(r'Data\s+Presta[çc][ãa]o\s+(?:de\s+)?Servi[çc]o\s*:?\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
        emissao = _data(m.group(1)) if m else None
        if emissao is not None:
            avisos.append("Data/Hora de Emissão não lida - usada a Data Prestação Serviço; conferir na nota")

    competencia = None
    m = re.search(r'Compet[êe]ncia\s*:?\s*([A-Za-zÇç]{3})[A-Za-zçÇ]*\s*/\s*(\d{4})', texto, re.IGNORECASE)
    if m and _sem_acento(m.group(1)).upper() in _MESES:
        competencia = datetime(int(m.group(2)), _MESES[_sem_acento(m.group(1)).upper()], 1)
    else:
        m = re.search(r'Compet[êe]ncia\s*:?\s*(\d{2})\s*/\s*(\d{4})', texto, re.IGNORECASE)
        if m and 1 <= int(m.group(1)) <= 12:
            competencia = datetime(int(m.group(2)), int(m.group(1)), 1)

    if emissao is None:
        emissao = competencia or datetime.now()
        avisos.append("Data de emissão não lida - usada a " + (
            "competência" if competencia else "data atual") + "; conferir na nota")
    if competencia is None:
        competencia = datetime(emissao.year, emissao.month, 1)
        avisos.append("Competência não lida - usado o mês da emissão; conferir na nota")
    return emissao, competencia


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

def extrair(texto: str, resolver, validar_doc: Callable[[str], bool]) -> NotaNatal:
    avisos: List[str] = []

    m_prest = re.search(r'Prestador\s+de\s+Servi[çc]os?', texto, re.IGNORECASE)
    m_tom = re.search(r'Tomador\s+de\s+Servi[çc]os?', texto, re.IGNORECASE)
    m_serv = re.search(r'^\s*Servi[çc]os\s*$', texto, re.IGNORECASE | re.MULTILINE)
    fim_tom = None
    if m_tom:
        for marca in (m_serv, re.search(r'^\s*Item\s+Descri', texto, re.IGNORECASE | re.MULTILINE)):
            if marca and marca.start() > m_tom.end():
                fim_tom = marca.start()
                break
    cabecalho = texto[:m_prest.start()] if m_prest else texto
    bloco_prest = texto[m_prest.end():m_tom.start()] if m_prest and m_tom and m_tom.start() > m_prest.end() else ''
    bloco_tom = texto[m_tom.end():fim_tom or len(texto)] if m_tom else ''

    m = re.search(r'N[ºo°.]{0,2}\s*da\s+Nota\s*:[ \t]*(\d{1,15})\b', cabecalho, re.IGNORECASE)
    if m:
        numero = m.group(1)
    else:
        numero = _SENTINELA_NUMERO
        avisos.append(f"Número da nota não lido - mantido como sentinela {_SENTINELA_NUMERO}; conferir na nota")
    m = re.search(r'Nota\s+Substitu[íi]da\s*:[ \t]*(\d+)', cabecalho, re.IGNORECASE)
    if m:
        avisos.append(f"Nota impressa como SUBSTITUTA da nº {m.group(1)} - conferir se a nota substituída "
                      "já foi escriturada")

    m = re.search(r'C[óo]digo\s+de\s+Verifica[çc][ãa]o\s*:[ \t]*([A-Za-z0-9]{4,20})\b', cabecalho, re.IGNORECASE)
    if m:
        codigo_verificacao = m.group(1)
    else:
        codigo_verificacao = _SENTINELA_CODIGO_VERIFICACAO
        avisos.append("Código de Verificação não lido - conferir na nota")

    emissao, competencia = _datas(cabecalho, avisos)

    optante_simples, regime = False, None
    if re.search(r'Microempreendedor\s+Individual|\bMEI\b', texto):
        optante_simples, regime = True, '5'
    elif re.search(r'optante\s+(?:pelo|do)\s+SIMPLES\s+NACIONAL', texto, re.IGNORECASE):
        optante_simples, regime = True, '6'

    prestador = _entidade('prestador', bloco_prest, resolver, validar_doc, avisos)
    tomador = _entidade('tomador', bloco_tom, resolver, validar_doc, avisos)

    corpo = texto[fim_tom:] if fim_tom else texto
    codigo_servico = _item_lc116(texto[m_tom.end():] if m_tom else texto, avisos)
    itens = _itens(corpo)
    descricoes = [d for d, _ in itens if d]
    if descricoes:
        discriminacao = ' | '.join(descricoes)
    else:
        discriminacao = _DISCRIMINACAO_PADRAO
        avisos.append("Descrição dos itens não lida - discriminação genérica; conferir na nota")

    valores = _valores(corpo, itens, optante_simples, avisos)

    return NotaNatal(
        numero=numero,
        codigo_verificacao=codigo_verificacao,
        data_emissao=emissao,
        competencia=competencia,
        prestador=prestador,
        tomador=tomador,
        discriminacao=discriminacao,
        codigo_servico=codigo_servico,
        valores=valores,
        optante_simples=optante_simples,
        regime_especial=regime,
        avisos=avisos,
    )


# ---------------------------------------------------------------------------
# Recorte OCR do endereço do prestador
# ---------------------------------------------------------------------------

def linha_endereco_prestador(texto: str) -> Optional[str]:
    """A linha "Endereço: ..." do bloco do prestador, como o OCR a leu."""
    m_prest = re.search(r'Prestador\s+de\s+Servi[çc]os?', texto, re.IGNORECASE)
    m_tom = re.search(r'Tomador\s+de\s+Servi[çc]os?', texto, re.IGNORECASE)
    if not (m_prest and m_tom and m_tom.start() > m_prest.end()):
        return None
    m = re.search(r'^[^\n]*Endere[çc]o\s*:[^\n]*$', texto[m_prest.end():m_tom.start()], re.IGNORECASE | re.MULTILINE)
    return m.group(0) if m else None


def aplicar_releitura_endereco(texto: str, original: Optional[str], relida: Optional[str]) -> str:
    """Troca a linha de endereço do prestador pela releitura SÓ quando as
    duas diferem apenas em espaços (achado real: "RALDO DE MELO FREIRE" na
    página a 3x, "R ALDO DE MELO FREIRE" no recorte a 6x - o espaço depois da
    abreviatura "R" some). Qualquer outra diferença (letra, dígito) mantém o
    texto original: o recorte não é fonte para trocar conteúdo."""
    if not original or not relida:
        return texto
    relida = _colapsa(relida)
    rel = re.search(r'Endere[çc]o\s*:.*$', relida, re.IGNORECASE)
    ori = re.search(r'Endere[çc]o\s*:.*$', original, re.IGNORECASE)
    if not rel or not ori:
        return texto
    if re.sub(r'\s', '', rel.group(0)) != re.sub(r'\s', '', ori.group(0)) or rel.group(0) == _colapsa(ori.group(0)):
        return texto
    nova = original[:ori.start()] + rel.group(0)
    return texto.replace(original, nova, 1)


def reler_linha_endereco(pdf_path: str, pagina: int) -> Optional[str]:
    """Relê, por recorte a 6x (PSM 7), a 1ª linha "Endereço:" da página (a do
    prestador). A linha é localizada dinamicamente via `image_to_data` a 3x,
    sem coordenada fixa. None se não achar ou se o OCR não estiver
    disponível."""
    import io
    import os

    import pymupdf
    import pytesseract
    from PIL import Image

    from ..utils.tesseract_config import configurar_pytesseract
    configurar_pytesseract(pytesseract)
    doc = pymupdf.open(pdf_path)
    try:
        if pagina >= len(doc):
            return None
        page = doc.load_page(pagina)
        z1, z2 = 3.0, 6.0
        img1 = Image.open(io.BytesIO(page.get_pixmap(matrix=pymupdf.Matrix(z1, z1)).tobytes('png')))
        dados = pytesseract.image_to_data(img1, lang='por', output_type=pytesseract.Output.DICT)
        alvo = None
        for i, palavra in enumerate(dados['text']):
            if re.match(r'^Endere[çc]o:?$', palavra or '', re.IGNORECASE):
                alvo = i
                break
        if alvo is None:
            return None
        topo, alt, esq = dados['top'][alvo], dados['height'][alvo], dados['left'][alvo]
        escala = z2 / z1
        img2 = Image.open(io.BytesIO(page.get_pixmap(matrix=pymupdf.Matrix(z2, z2)).tobytes('png')))
        caixa = (max(0, int((esq - 10) * escala)), max(0, int((topo - alt * 0.6) * escala)),
                 img2.size[0], min(img2.size[1], int((topo + alt * 1.6) * escala)))
        return pytesseract.image_to_string(img2.crop(caixa), lang='por', config='--psm 7').strip() or None
    finally:
        doc.close()
