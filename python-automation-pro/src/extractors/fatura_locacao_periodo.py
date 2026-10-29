"""Helpers da "FATURA DE LOCAÇÃO Nº <id>" com grade "PERÍODO DE REFERÊNCIA"
(locação de bens móveis, NÃO é NFS-e).

Achado real 2026-10-28 (`LOCACAO OBRA - 18 DE AGOSTO.pdf` e `LOCACAO OBRA - 19
DE AGOSTO.pdf`): EXTREMA LOCACAO DE EQUIPAMENTOS LTDA (marca "MEGA LOCAÇÃO",
CNPJ 15.756.706/0001-55, Extrema/MG) -> H. Z. PATRIMONIAL LTDA. (Lauro de
Freitas/BA), faturas ND-025919 (R$ 350,00) e ND-025924 (R$ 400,00). Antes deste
módulo as páginas caíam em LAYOUT_FATURA_LOCACAO_GENERICA (só pela frase
"FATURA DE LOCAÇÃO"), cujos extratores são calibrados no template da LOC BAHIA:
Numero "09" (a "Carteira" do boleto), prestador/tomador não identificados,
valor 0,00 e a linha digitável do boleto como discriminação.

Estrutura do impresso (PDF DIGITAL de sistema de gestão de locadora, com o
boleto embaixo na mesma página):
  * letterhead do locador (razão social / endereço / "<BAIRRO> - CEP:" /
    "FONE: ... - <CIDADE> - <UF>" / "CNPJ (MF):" / "INSC. ESTADUAL:" /
    "E-MAIL:") e a caixa "FATURA DE LOCAÇÃO Nº <id>";
  * grade com rótulos fixos "PERÍODO DE REFERÊNCIA", "NATUREZA DA OPERAÇÃO",
    "DATA DE EMISSÃO", "TOMADOR - RAZÃO SOCIAL", "C.N.P.J / CPF", "ENDEREÇO",
    "ENTREGA" (endereço de entrega - nunca o do tomador), "INSC ESTADUAL / RG";
  * tabela "Quantidade | Unidade | Discriminação | Valor Unitário | Valor
    Total", "Observações", "Contrato", "Parcelas" (Vencimento <data> R$ <v>) e
    "VALOR TOTAL";
  * boleto (Beneficiário/Pagador/linha digitável/Nosso Número) - nada dele é
    dado da fatura; só confere o identificador ("Número do Documento").

O `pdfminer.extract_text()` despeja a tabela de itens POR COLUNA (todas as
quantidades, depois as unidades, as descrições, os unitários e os totais),
intercalada com os blocos Observações/Contrato/Parcelas e em ordem diferente
conforme o número de itens. `_itens` reconstrói as linhas pela contagem de cada
coluna e só aceita o resultado quando as colunas fecham (N quantidades, N
unidades, N descrições, 2N valores); senão a discriminação leva só as
descrições, com aviso. Detecção ESTRUTURAL (título + rótulos fixos), nunca
pelo nome/CNPJ da locadora. `extrair` é função pura sobre o texto.
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional, Tuple

from datetime import datetime

from ..models.nfse_models import Endereco, Entidade, Valores
from .nota_locacao import (
    ITEM_LOCACAO, CODIGO_VERIFICACAO, ItemLocacao, NotaLocacao,
    _RE_RAZAO, _colapsa, _valor_br, separar_endereco,
)

__all__ = ['ITEM_LOCACAO', 'CODIGO_VERIFICACAO', 'eh_fatura_locacao_periodo', 'extrair']

_SENTINELA_DOC = '00000000000000'
_SENTINELA_NUMERO = '00000000'

_MONEY = r'\d{1,3}(?:\.\d{3})*,\d{2}'
_RE_TITULO = re.compile(
    r'FATURA\s+DE\s+LOCA[ÇC][ÃA]O\s+N\s*[º°oO.]{1,2}\s*(?P<ident>(?:[A-Z]{1,4}\s*-\s*)?(?P<num>\d{1,12}))\b',
    re.IGNORECASE)
_ROTULOS = (
    r'PER[ÍI]ODO\s+DE\s+REFER[ÊE]NCIA',
    r'NATUREZA\s+DA\s+OPERA[ÇC][ÃA]O',
    r'DATA\s+DE\s+EMISS[ÃA]O',
    r'TOMADOR\s*-\s*RAZ[ÃA]O\s+SOCIAL',
    r'Discrimina[çc][ãa]o',
    r'Valor\s+Unit[áa]rio',
    r'Parcelas',
)
_RE_CNPJ = re.compile(r'\d{2}\.?\d{3}\.?\d{3}\s*/\s*\d{4}\s*-?\s*\d{2}')
_RE_CPF = re.compile(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}')
_RE_CEP = re.compile(r'^\d{5}-?\d{3}$|^\d{2}\.\d{3}-?\d{3}$')
_RE_PLACEHOLDER_OBS = re.compile(r'^\[[^\]]*\(observa[çc][ãa]o\)\]$', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def eh_fatura_locacao_periodo(texto: str) -> bool:
    """True para este modelo de "FATURA DE LOCAÇÃO".

    Exige o título "FATURA DE LOCAÇÃO Nº <id>" E todos os rótulos fixos da
    grade (PERÍODO DE REFERÊNCIA, NATUREZA DA OPERAÇÃO, DATA DE EMISSÃO,
    TOMADOR - RAZÃO SOCIAL, Discriminação, Valor Unitário, Parcelas). Outras
    faturas de locação (LOC BAHIA/genérica, NEO-TAGUS, ARMAC, CPE...) não
    imprimem essa combinação; NFS-e/nota fiscal eletrônica fica fora."""
    if not texto or not _RE_TITULO.search(texto):
        return False
    if not all(re.search(r, texto, re.IGNORECASE) for r in _ROTULOS):
        return False
    if re.search(r'\bNFS-?e\b|Nota\s+Fiscal\s+(?:Eletr|de\s+Servi)|DANFS', texto, re.IGNORECASE):
        return False
    return True


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _apos_rotulo(texto: str, rotulo: str) -> Optional[str]:
    """1ª linha não vazia logo depois do rótulo (sozinho na sua linha)."""
    m = re.search(r'^[ \t]*' + rotulo + r'[ \t]*\n\s*([^\n]+)', texto, re.IGNORECASE | re.MULTILINE)
    return _colapsa(m.group(1)) if m else None


def _cabecalho(texto: str) -> str:
    """Letterhead do locador: tudo antes do 1º rótulo da grade."""
    fim = len(texto)
    for r in (r'NATUREZA\s+DA\s+OPERA', r'PER[ÍI]ODO\s+DE\s+REFER', r'TOMADOR\s*-\s*RAZ',
              r'FATURA\s+DE\s+LOCA'):
        m = re.search(r, texto, re.IGNORECASE)
        if m:
            fim = min(fim, m.start())
    return texto[:fim]


def _data(s: Optional[str]) -> Optional[datetime]:
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', s or '')
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Entidades
# ---------------------------------------------------------------------------

def _prestador(texto: str, resolver, validar_doc, cnpj_tomador: str, avisos: List[str]) -> Entidade:
    cab = _cabecalho(texto)

    doc = None
    for m in _RE_CNPJ.finditer(cab):
        d = re.sub(r'\D', '', m.group(0))
        if d != cnpj_tomador and validar_doc(d):
            doc = d
            break
    if not doc:
        avisos.append("CNPJ do locador (prestador) não encontrado no cabeçalho com dígito verificador "
                      "válido - mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC

    m_razao = _RE_RAZAO.search(cab)
    razao = _colapsa(m_razao.group(1)) if m_razao else ''
    if not razao:
        avisos.append("Razão social do locador (prestador) não encontrada no cabeçalho - conferir no documento")
        razao = 'Prestador Não Identificado'

    endereco_raw = ''
    for linha in cab.splitlines():
        linha = _colapsa(linha)
        if re.match(r'(?:FONE|TEL|CNPJ|INSC|E-?MAIL)', linha, re.IGNORECASE) or re.search(r'\bCEP\b', linha, re.IGNORECASE):
            continue
        if re.search(r',\s*(?:\d{1,6}|S/?N)\b', linha, re.IGNORECASE):
            endereco_raw = linha
            break
    logradouro, numero, compl = separar_endereco(endereco_raw)
    if not endereco_raw:
        avisos.append("Endereço do locador (prestador) não encontrado no cabeçalho - conferir no documento")

    bairro = cep = ''
    m_cep = re.search(r'^[ \t]*(?P<bairro>[^\n]*?)[ \t-]*CEP\s*:?\s*(?P<cep>\d{2}\.?\d{3}-?\d{3})', cab,
                      re.IGNORECASE | re.MULTILINE)
    if m_cep:
        bairro = _colapsa(m_cep.group('bairro')).strip(' -')
        cep = re.sub(r'\D', '', m_cep.group('cep'))

    municipio = uf = cod_mun = ''
    m_cid = re.search(r'^[ \t]*FONE[^\n]*?-\s*(?P<cidade>[A-ZÀ-Ú][A-ZÀ-Ú\' .]+?)\s*-\s*(?P<uf>[A-Z]{2})[ \t]*$',
                      cab, re.MULTILINE)
    if m_cid:
        municipio = _colapsa(m_cid.group('cidade'))
        uf = m_cid.group('uf')
        cod_mun = resolver.extract_and_validate(municipio, uf, city_hint=municipio)
    else:
        avisos.append("Município/UF do locador (prestador) não encontrados no cabeçalho - conferir no documento")

    m_tel = re.search(r'FONE\s*:?\s*\(?(\d{2})\)?\s*(\d{4,5})\s*-?\s*(\d{4})', cab, re.IGNORECASE)
    m_mail = re.search(r'E-?MAIL\s*:?\s*([\w.+-]+@[\w-]+(?:\.[\w-]+)+)', cab, re.IGNORECASE)

    return Entidade(
        cnpj_cpf=doc, razao_social=razao,
        telefone=''.join(m_tel.groups()) if m_tel else None,
        email=m_mail.group(1) if m_mail else None,
        endereco=Endereco(
            logradouro=logradouro, numero=numero, complemento=compl,
            bairro=bairro or 'Não informado', codigo_municipio=cod_mun,
            municipio=municipio or None, uf=uf, cep=cep if len(cep) == 8 else '00000000'),
    )


def _endereco_tomador_bruto(texto: str) -> str:
    """Linhas não vazias logo depois do rótulo "ENDEREÇO" (até a linha em
    branco), coladas numa linha só: o pdfminer preserva o espaço final da
    linha quebrada ("... LAURO \\nDE FREITAS"), que vira o separador; sem
    ele, entra um espaço."""
    m = re.search(r'^[ \t]*ENDERE[ÇC]O[ \t]*\n(?:[ \t]*\n)*((?:[^\n]*\S[^\n]*(?:\n|$))+)', texto, re.MULTILINE)
    if not m:
        return ''
    return _colapsa(''.join(l.rstrip('\r\n') if l.endswith(' ') else l + ' '
                            for l in m.group(1).splitlines(keepends=False)))


def separar_endereco_tomador(raw: str) -> Optional[Tuple[str, str, Optional[str], str, str, str, str]]:
    """"LOGRADOURO, NUM - COMPL... - BAIRRO - CIDADE - UF - CEP" ->
    (logradouro, numero, complemento, bairro, cidade, uf, cep8). None se a
    linha não fecha com "... - <CIDADE> - <UF> - <CEP>"."""
    partes = [p.strip() for p in re.split(r'\s+-\s+', raw or '') if p.strip()]
    if len(partes) < 5 or not _RE_CEP.match(partes[-1]) or not re.fullmatch(r'[A-Z]{2}', partes[-2]):
        return None
    cep = re.sub(r'\D', '', partes[-1])
    uf, cidade, bairro = partes[-2], partes[-3], partes[-4]
    logradouro, numero, resto = separar_endereco(partes[0])
    compl = ' - '.join(([resto] if resto else []) + partes[1:-4]) or None
    return logradouro, numero, compl, bairro, cidade, uf, cep


def _tomador(texto: str, resolver, validar_doc, avisos: List[str]) -> Entidade:
    razao = _apos_rotulo(texto, r'TOMADOR\s*-\s*RAZ[ÃA]O\s+SOCIAL') or ''
    if not razao:
        avisos.append("Razão social do tomador não encontrada - conferir no documento")
        razao = 'Tomador Não Identificado'

    doc_raw = _apos_rotulo(texto, r'C\.?\s*N\.?\s*P\.?\s*J\.?\s*/\s*CPF') or ''
    m_doc = _RE_CNPJ.search(doc_raw) or _RE_CPF.search(doc_raw)
    doc = re.sub(r'\D', '', m_doc.group(0)) if m_doc else ''
    if len(doc) not in (11, 14):
        avisos.append("CNPJ/CPF do tomador não encontrado - mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC
    elif not validar_doc(doc):
        avisos.append(f"CNPJ/CPF do tomador ({doc}) não passa na validação do dígito verificador - "
                      "mantido como lido; conferir no documento")

    raw = _endereco_tomador_bruto(texto)
    partes = separar_endereco_tomador(raw)
    if partes:
        logradouro, numero, compl, bairro, municipio, uf, cep = partes
        cod_mun = resolver.extract_and_validate(municipio, uf, city_hint=municipio)
    else:
        if raw:
            avisos.append("Endereço do tomador fora do padrão \"... - BAIRRO - CIDADE - UF - CEP\" - "
                          "gravado inteiro no logradouro; conferir bairro/município/CEP no documento")
        else:
            avisos.append("Endereço do tomador não encontrado - conferir no documento")
        logradouro, numero, compl = (raw or 'Não informado'), 'S/N', None
        bairro = municipio = uf = cep = cod_mun = ''

    return Entidade(
        cnpj_cpf=doc, razao_social=razao,
        endereco=Endereco(
            logradouro=logradouro, numero=numero, complemento=compl,
            bairro=bairro or 'Não informado', codigo_municipio=cod_mun,
            municipio=municipio or None, uf=uf, cep=cep if len(cep) == 8 else '00000000'),
    )


# ---------------------------------------------------------------------------
# Itens, totais e discriminação
# ---------------------------------------------------------------------------

_ROTULOS_GRADE = re.compile(
    r'^(?:Quantidade(?:\s+Unidade)?|Unidade|Discrimina[çc][ãa]o|Valor\s+Unit[áa]rio|Valor\s+Total)$')


def _regiao_itens(texto: str) -> str:
    m_ini = re.search(r'^[ \t]*Quantidade\b', texto, re.MULTILINE)
    m_fim = re.search(r'^[ \t]*VALOR TOTAL[ \t]*$', texto, re.MULTILINE)  # caixa alta: o total da fatura
    if not (m_ini and m_fim and m_fim.start() > m_ini.start()):
        return ''
    regiao = texto[m_ini.start():m_fim.start()] + '\n'
    # Blocos que o pdfminer intercala com as colunas da tabela.
    regiao = re.sub(r'^[ \t]*Observa[çc][õo]es[ \t]*\n(?:[^\n]*\S[^\n]*\n)*', '', regiao, flags=re.MULTILINE | re.IGNORECASE)
    regiao = re.sub(r'^[ \t]*Contrato[ \t]*\n[^\n]*\n', '', regiao, flags=re.MULTILINE | re.IGNORECASE)
    regiao = re.sub(r'^[ \t]*Parcelas[ \t]*\n(?:[^\n]*\S[^\n]*\n)*', '', regiao, flags=re.MULTILINE | re.IGNORECASE)
    return regiao


def _itens(texto: str, avisos: List[str]) -> Tuple[List[Tuple[str, str, ItemLocacao, str]], List[str]]:
    """((qtd impressa, unidade, item, total impresso), descrições). A lista de itens só vem
    preenchida quando as colunas fecham; senão vem vazia (+ aviso) e o
    chamador usa só as descrições."""
    qtds: List[str] = []
    unids: List[str] = []
    descs: List[str] = []
    valores: List[str] = []
    for linha in _regiao_itens(texto).splitlines():
        linha = _colapsa(linha)
        if not linha or _ROTULOS_GRADE.match(linha):
            continue
        if re.fullmatch(_MONEY, linha):
            valores.append(linha)
        elif re.fullmatch(r'\d{1,6}', linha):
            qtds.append(linha)
        elif re.fullmatch(r'[A-ZÇ]{1,3}\d?', linha):
            unids.append(linha)
        else:
            descs.append(linha)
    n = len(descs)
    if not n:
        return [], []
    if not (len(qtds) == n and len(unids) == n and len(valores) == 2 * n):
        avisos.append(f"Tabela de itens da fatura não reconstruída com segurança ({n} descrições, "
                      f"{len(qtds)} quantidades, {len(unids)} unidades, {len(valores)} valores) - "
                      "discriminação leva só as descrições; conferir valores no documento")
        return [], descs
    itens = []
    for i in range(n):
        item = ItemLocacao(descricao=descs[i], quantidade=float(qtds[i]),
                           valor_unitario=_valor_br(valores[i]), valor_total=_valor_br(valores[n + i]))
        if abs(item.quantidade * item.valor_unitario - item.valor_total) > 0.011:
            avisos.append(f"Item \"{item.descricao[:40]}\": quantidade x unitário "
                          f"({item.quantidade * item.valor_unitario:.2f}) diverge do total impresso "
                          f"({item.valor_total:.2f}) - conferir no documento")
        itens.append((qtds[i], unids[i], item, valores[n + i]))
    return itens, descs


def _observacoes(texto: str) -> str:
    m = re.search(r'^[ \t]*Observa[çc][õo]es[ \t]*\n((?:[^\n]*\S[^\n]*\n?)*)', texto, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ''
    linhas = [_colapsa(l) for l in m.group(1).splitlines()]
    return ' '.join(l for l in linhas if l and not _RE_PLACEHOLDER_OBS.match(l))


def extrair(texto: str, resolver, validar_doc: Callable[[str], bool]) -> NotaLocacao:
    """Extrai a fatura. `resolver` é o `IBGEResolver` compartilhado do
    extrator; `validar_doc` valida o DV de CNPJ/CPF."""
    avisos: List[str] = []
    texto = texto or ''

    m_tit = _RE_TITULO.search(texto)
    ident = re.sub(r'\s+', '', m_tit.group('ident')) if m_tit else ''
    if m_tit and m_tit.group('num').strip('0'):
        numero = str(int(m_tit.group('num')))
    else:
        avisos.append("Número da fatura de locação não encontrado - mantido sentinela; conferir no documento")
        numero = _SENTINELA_NUMERO
    num_doc = _apos_rotulo(texto, r'N[úu]mero\s+do\s+Documento')
    if ident and num_doc and re.sub(r'\s+', '', num_doc) != ident:
        avisos.append(f"Número da fatura ({ident}) difere do \"Número do Documento\" do boleto ({num_doc}) - "
                      "conferir no documento")

    data = _data(_apos_rotulo(texto, r'DATA\s+DE\s+EMISS[ÃA]O'))

    tomador = _tomador(texto, resolver, validar_doc, avisos)
    prestador = _prestador(texto, resolver, validar_doc, tomador.cnpj_cpf, avisos)

    linhas_itens, descs = _itens(texto, avisos)
    if linhas_itens:
        itens_txt = '; '.join(f"{q} {u} {it.descricao} R$ {v}" for q, u, it, v in linhas_itens)
    else:
        itens_txt = '; '.join(descs)
    periodo = _apos_rotulo(texto, r'PER[ÍI]ODO\s+DE\s+REFER[ÊE]NCIA')
    contrato = _apos_rotulo(texto, r'Contrato')
    parcelas = re.findall(r'Vencimento\s+(\d{2}/\d{2}/\d{4})\s+R\$\s*(' + _MONEY + r')', texto)
    obs = _observacoes(texto)

    partes = [f"FATURA DE LOCAÇÃO Nº {ident}" if ident else "FATURA DE LOCAÇÃO"]
    if itens_txt:
        partes.append(f"ITENS: {itens_txt}")
    else:
        avisos.append("Itens da fatura de locação não encontrados - conferir no documento")
    if periodo:
        partes.append(f"PERÍODO: {periodo}")
    if contrato:
        partes.append(f"CONTRATO: {contrato}")
    if parcelas:
        partes.append("VENCIMENTO: " + '; '.join(f"{d} R$ {v}" for d, v in parcelas))
    if obs:
        partes.append(f"OBS: {obs}")
    discriminacao = ' | '.join(partes)

    m_total = re.search(r'^[ \t]*VALOR TOTAL[ \t]*\n\s*R\$\s*(' + _MONEY + r')', texto, re.MULTILINE)
    total = _valor_br(m_total.group(1)) if m_total else None
    soma_itens = round(sum(it.valor_total for _q, _u, it, _v in linhas_itens), 2) if linhas_itens else None
    soma_parcelas = round(sum(_valor_br(v) for _d, v in parcelas), 2) if parcelas else None
    if total is None:
        total = soma_itens
        if total is not None:
            avisos.append("\"VALOR TOTAL\" da fatura não encontrado - valor tomado da soma dos itens; "
                          "conferir no documento")
        else:
            avisos.append("\"VALOR TOTAL\" da fatura não encontrado - valor zerado; conferir no documento")
    for nome, soma in (('soma dos itens', soma_itens), ('soma das parcelas', soma_parcelas)):
        if total is not None and soma is not None and abs(total - soma) > 0.011:
            avisos.append(f"Valor total da fatura ({total:.2f}) diverge da {nome} ({soma:.2f}) - "
                          "mantido o total impresso; conferir no documento")
    valor = total or 0.0
    valores = Valores(valor_servicos=valor, valor_liquido_nfse=valor,
                      base_calculo=0.0, aliquota=0.0, valor_iss=0.0)

    optante = bool(re.search(r'OPTANTE\s+(?:PELO|DO)\s+SIMPLES\s+NACIONAL', texto, re.IGNORECASE))

    avisos.append(
        "Documento é FATURA DE LOCAÇÃO de bem móvel (não é NFS-e): locação de bens móveis fica fora "
        "do campo de incidência do ISS (LC 116/2003). XML gerado na convenção das faturas de locação: "
        "ISS/base/alíquota zerados, item 0601 e código de verificação \"FATURA\"; conferir o "
        "lançamento no Domínio antes de importar")

    return NotaLocacao(
        numero=numero, data_emissao=data, discriminacao=discriminacao,
        prestador=prestador, tomador=tomador, valores=valores,
        itens=[it for _q, _u, it, _v in linhas_itens], optante_simples=optante, avisos=avisos,
    )
