"""Leitura por ROTULO do DANFE (NF-e Modelo 55) DIGITAL em que o texto do PDF
sai como "rotulo\\nvalor" de caixa em caixa, mas com a ordem das caixas
diferente da que `_parse_danfe_produto` (regex escritas para a nota nº 52.136,
GRAN COFFEE) espera.

Achado real 2026-10-28, nota nº 478012 (STONE BUILDING SA INDUSTRIA E
COMERCIO, Braganca Paulista/SP -> H. Z. PATRIMONIAL LTDA., Lauro de
Freitas/BA, R$1.498,00, DANFE emitido pelo sistema "Minerion"): a nota era
detectada corretamente como LAYOUT_DANFE_PRODUTO, mas quase todo campo caia no
sentinela - numero impresso "Nº 0478012" (nao "N. 52.136"), chave de acesso
impressa com PONTOS ("35.2607.03918238000199.55...") e longe do rotulo, data
"21/07/2026" (nao "15-01-2026"), protocolo com " em " entre numero e data,
letterhead do emitente depois do nome do MOTORISTA no canhoto ("Mot.:ALCINO
APARECIDO RAMOS" virava a razao social do emitente), destinatario/transporte
em caixas rotulo\\nvalor numa ordem diferente, grade "CALCULO DO IMPOSTO" com
valores despejados numa ordem propria e a tabela de itens com
"NCM CST CFOP" numa linha so.

Tudo aqui sao funcoes PURAS sobre texto, usadas por `_parse_danfe_produto`
apenas como FALLBACK quando a regex original do campo nao casa - a nota da
GRAN COFFEE continua lida exatamente como antes. Cada valor lido por rotulo
passa por um validador do TIPO esperado (UF valida, CEP de 8 digitos,
CNPJ/CPF com digito verificador...) - um rotulo seguido de outro rotulo, ou de
um valor de outro tipo (caixa vizinha), devolve None em vez de um valor
plausivel porem errado.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Tuple

UFS = frozenset(
    "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()
)

# Linhas que sao ROTULO de caixa do DANFE (padrao nacional), nunca valor.
_ROTULO_LINHA = re.compile(
    r'^\s*(?:'
    r'NOME\s*/?\s*RAZ[ÃA]O\s+SOCIAL|RAZ[ÃA]O\s+SOCIAL|CNPJ(?:\s*/\s*CPF)?|CPF|'
    r'ENDERE[ÇC]O|BAIRRO\s*/\s*DISTRITO|CEP|MUNIC[ÍI]PIO|FONE\s*/\s*FAX|UF|'
    r'INSCRI[ÇC][ÃA]O\s+ESTADUAL.*|INSC\.\s.*|DATA\s+D[AEO]\s+.*|DATA\s+EMISS[ÃA]O|'
    r'HORA\s+D[AEO]\s+.*|FATURA.*|N[ÚU]MERO|VENCIMENTO|VENC\.?|VALOR(?:\s.*)?|'
    r'PROTOCOLO\s.*|NATUREZA\s.*|QUANTIDADE|ESP[ÉE]CIE|MARCA|NUMERA[ÇC][ÃA]O|'
    r'PESO\s+.*|PLACA.*|C[ÓO]DIGO.*|FRETE\s+POR\s+CONTA|DADOS\s+.*|C[ÁA]LCULO\s.*|'
    r'TRANSPORTADOR.*|DESTINAT[ÁA]RIO.*|BASE\s+DE\s+C[ÁA]LCULO.*|DESCONTO|'
    r'OUTRAS\s+DESPESAS.*|RESERVADO\s+AO\s+FISCO|INFORMA[ÇC][ÕO]ES\s+COMPLEMENTARES'
    r')\s*$',
    re.IGNORECASE)

_MONEY = r'\d{1,3}(?:\.\d{3})*,\d{2,4}'


def eh_rotulo(linha: str) -> bool:
    return bool(_ROTULO_LINHA.match(linha or ''))


def num_br(s: Optional[str]) -> float:
    if not s:
        return 0.0
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0


def _digitos(s: Optional[str]) -> str:
    return re.sub(r'\D', '', s or '')


# --- validadores de tipo -------------------------------------------------

def _cnpj_dv_ok(c: str) -> bool:
    if len(c) != 14 or c == c[0] * 14:
        return False

    def _dv(nums: str) -> str:
        pesos = list(range(2, 10)) * 2
        soma = sum(int(n) * p for n, p in zip(reversed(nums), pesos))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    return c[12] == _dv(c[:12]) and c[13] == _dv(c[:13])


def val_cnpj_cpf(v: str) -> bool:
    if not re.fullmatch(r'[\d./\-\s]+', v or ''):
        return False
    d = _digitos(v)
    return _cnpj_dv_ok(d) or len(d) == 11


def val_cep(v: str) -> bool:
    return bool(re.fullmatch(r'\d{2}\.?\d{3}-?\d{3}', (v or '').strip()))


def val_uf(v: str) -> bool:
    return (v or '').strip().upper() in UFS


def val_texto(v: str) -> bool:
    """Texto livre (nome, logradouro, bairro, municipio): precisa ter letras."""
    return len(re.sub(r'[^A-Za-zÀ-ÿ]', '', v or '')) >= 2


def val_municipio(v: str) -> bool:
    return val_texto(v) and not re.search(r'\d', v or '')


def val_fone(v: str) -> bool:
    return bool(re.fullmatch(r'[\d()\s.\-+]+', v or '')) and len(_digitos(v)) >= 8


def val_ie(v: str) -> bool:
    v = (v or '').strip()
    return v.upper() == 'ISENTO' or (bool(re.fullmatch(r'[\d./\-]+', v)) and len(_digitos(v)) >= 2)


# --- leitura rotulo -> valor ---------------------------------------------

def valor_do_rotulo(sec: str, rotulo: str, validar: Optional[Callable[[str], bool]] = None) -> Optional[str]:
    """Valor da 1a ocorrencia de `rotulo` (regex de LINHA INTEIRA) cuja proxima
    linha nao vazia e um valor valido (nao e outro rotulo e passa em
    `validar`)."""
    for m in re.finditer(r'(?im)^[ \t]*(?:' + rotulo + r')[ \t]*$', sec or ''):
        resto = sec[m.end():]
        prox = next((l.strip() for l in resto.split('\n') if l.strip()), None)
        if prox is None or eh_rotulo(prox):
            continue
        if validar is not None and not validar(prox):
            continue
        return prox
    return None


def secao(t: str, inicio: str, fim: str) -> str:
    m = re.search(inicio, t or '', re.IGNORECASE)
    if not m:
        return ''
    resto = t[m.end():]
    mf = re.search(fim, resto, re.IGNORECASE)
    return resto[:mf.start()] if mf else resto


# --- campos ----------------------------------------------------------------

def localizar_chave_nfe55(t: str, dv_fn: Callable[[str], str]) -> str:
    """Chave de acesso de 44 digitos do Modelo 55 em qualquer linha do texto,
    com quaisquer separadores (espacos em grupos de 4, PONTOS - "35.2607.0391
    ...55.000.000478012.1.00759350.0"). So aceita janela com modelo 55 nas
    posicoes 20:22 E digito verificador mod-11 correto (`dv_fn`) - validacao
    ESTRUTURAL: uma leitura com digito trocado e recusada."""
    for linha in (t or '').split('\n'):
        digitos = _digitos(linha)
        for i in range(max(0, len(digitos) - 43)):
            cand = digitos[i:i + 44]
            if cand[20:22] == '55' and dv_fn(cand[:43]) == cand[43]:
                return cand
    return ''


def separar_logradouro(linha: str) -> Tuple[str, Optional[str], Optional[str]]:
    """"AV LUIZ TARQUINIO PONTES, 2580, SALA 311 EDF VILLAS" ->
    (logradouro, numero, complemento); "ROD FERNAO DIAS, KM 13,5, SN" ->
    ("ROD FERNAO DIAS, KM 13,5", "SN", None). Sem numero reconhecivel devolve
    a linha inteira como logradouro e numero None."""
    linha = (linha or '').strip().rstrip(',').strip()
    # numero (digitos ou S/N) seguido opcionalmente de ", complemento"
    # separador = virgula SEGUIDA de espaco ("KM 13,5" e decimal, nao separa)
    m = re.match(r'^(.*?),\s+(\d+[A-Z]?|S\s*/?\s*N)(?:(?:,\s+|\s{2,}|\s+-\s+)(.+))?$', linha, re.IGNORECASE)
    if m and val_texto(m.group(1)):
        return m.group(1).strip(), m.group(2).strip(), (m.group(3) or '').strip() or None
    return linha, None, None


def emitente_letterhead(t: str) -> Optional[Dict[str, Optional[str]]]:
    """Letterhead do emitente: bloco livre entre o canhoto e o box "DANFE".

    O canhoto (assinatura do recebedor, "Mot.:<motorista>", codigo de barras,
    "NF-e / Nº <n> / Serie <s>") vem ANTES no texto - o letterhead comeca
    depois da ULTIMA linha "Serie <s>" do canhoto. Linhas reconhecidas por
    estrutura: "<MUNICIPIO>-<UF>", "CEP: <8 digitos>", "Tel:/Fone: ...";
    entre o nome e o municipio, 1a linha = logradouro+numero, 2a = bairro.
    Devolve None se o municipio-UF nao for reconhecido (sem chute)."""
    m = re.search(r'ASSINATURA\s+DO\s+RECEBEDOR\s*\n(.+?)\n\s*DANFE\s*\n', t or '', re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    bloco = m.group(1)
    ultima = None
    for ms in re.finditer(r'(?im)^\s*S[ÉE]RIE\s*:?\s*\d{1,3}\s*$', bloco):
        ultima = ms
    if ultima is None:
        return None
    linhas = [l.strip() for l in bloco[ultima.end():].split('\n') if l.strip()]
    if len(linhas) < 3:
        return None
    nome = linhas[0]
    idx_mun, municipio, uf, cep, fone = None, None, None, None, None
    for i, l in enumerate(linhas[1:], start=1):
        mm = re.fullmatch(r'(.+?)\s*[-/]\s*([A-Z]{2})', l)
        if idx_mun is None and mm and mm.group(2) in UFS and val_municipio(mm.group(1)):
            idx_mun, municipio, uf = i, mm.group(1).strip(), mm.group(2)
            continue
        mc = re.fullmatch(r'CEP\s*:?\s*(\d{2}\.?\d{3}-?\d{3})', l, re.IGNORECASE)
        if mc:
            cep = _digitos(mc.group(1))
            continue
        mf = re.fullmatch(r'(?:Tel|Fone|Telefone)\.?\s*:?\s*([\d()\s.\-+]{8,})', l, re.IGNORECASE)
        if mf:
            fone = mf.group(1).strip()
    if idx_mun is None or not val_texto(nome):
        return None
    meio = [l for l in linhas[1:idx_mun]
            if not re.match(r'(?:CEP|Tel|Fone|Telefone)\b', l, re.IGNORECASE)]
    if not meio:
        return None
    logradouro, numero, complemento = separar_logradouro(meio[0])
    bairro = meio[1] if len(meio) > 1 else None
    return {
        'razao_social': nome, 'logradouro': logradouro, 'numero': numero,
        'complemento': complemento, 'bairro': bairro, 'municipio': municipio,
        'uf': uf, 'cep': cep, 'telefone': fone,
    }


def nome_confere_canhoto(t: str, nome: str) -> Optional[bool]:
    """O canhoto traz "RECEBEMOS DE <EMITENTE> ..." - contraprova barata de que o
    letterhead lido e o do emitente. None quando o canhoto nao tem a frase."""
    m = re.search(r'RECEBEMOS\s+DE\s+([^\n]+)', t or '', re.IGNORECASE)
    if not m:
        return None
    norm = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())
    return norm(m.group(1)).startswith(norm(nome))


_SEC_DEST_INI = r'DESTINAT[ÁA]RIO\s*/?\s*REMETENTE'
_SEC_DEST_FIM = r'C[ÁA]LCULO\s+D[OE]\s+IMPOSTO'
# A grade do destinatario termina antes de um bloco "LOCAL DE RETIRADA /
# ENTREGA" (rotulos iguais - NOME, CNPJ, MUNICIPIO... - mas de OUTRA entidade).
_SEC_DEST_FIM_ENTIDADE = r'INFORMA[ÇC][ÕO]ES\s+DO\s+LOCAL|LOCAL\s+DE\s+(?:RETIRADA|ENTREGA)|' + _SEC_DEST_FIM


def destinatario_por_rotulos(t: str) -> Dict[str, Optional[str]]:
    sec = secao(t, _SEC_DEST_INI, _SEC_DEST_FIM_ENTIDADE)
    r = {
        'razao_social': valor_do_rotulo(sec, r'NOME\s*/?\s*RAZ[ÃA]O\s+SOCIAL', val_texto),
        'cnpj_cpf': valor_do_rotulo(sec, r'CNPJ\s*/\s*CPF', val_cnpj_cpf),
        'endereco': valor_do_rotulo(sec, r'ENDERE[ÇC]O', val_texto),
        'bairro': valor_do_rotulo(sec, r'BAIRRO\s*/\s*DISTRITO', val_texto),
        'cep': valor_do_rotulo(sec, r'CEP', val_cep),
        'municipio': valor_do_rotulo(sec, r'MUNIC[ÍI]PIO', val_municipio),
        'uf': valor_do_rotulo(sec, r'UF', val_uf),
        'telefone': valor_do_rotulo(sec, r'FONE\s*/\s*FAX', val_fone),
        'inscricao_estadual': valor_do_rotulo(sec, r'INSCRI[ÇC][ÃA]O\s+ESTADUAL', val_ie),
    }
    if r['cep']:
        r['cep'] = _digitos(r['cep'])
    if r['uf']:
        r['uf'] = r['uf'].upper()
    return r


def fatura_por_rotulos(t: str) -> List[Tuple[str, str, str]]:
    """Duplicatas da caixa "FATURA" (NUMERO | VENCIMENTO | VALOR, repetidas):
    triplas (numero, vencimento dd/mm/aaaa, valor) na ordem impressa."""
    sec = secao(t, r'(?m)^\s*FATURA\s*$', _SEC_DEST_FIM)
    if not re.search(r'(?im)^\s*VENCIMENTO\s*$', sec):
        return []
    return [(m.group(1), m.group(2), m.group(3)) for m in re.finditer(
        r'(?m)^[ \t]*(\d[\w/\-]*)[ \t]*\n\s*(\d{2}/\d{2}/\d{4})[ \t]*\n\s*(' + _MONEY + r')[ \t]*$', sec)]


def grade_calculo_por_ordem(t: str) -> Optional[List[float]]:
    """Os 11 valores da grade "CALCULO DO IMPOSTO" na ordem em que o texto os
    despeja (rotulos ignorados). Devolve None se nao forem exatamente 11."""
    sec = secao(t, r'C[ÁA]LCULO\s+D[OE]\s+IMPOSTO', r'TRANSPORTADOR\s*/\s*VOLUMES')
    vals = re.findall(r'(?m)^[ \t]*(' + _MONEY + r')[ \t]*$', sec)
    if len(vals) != 11:
        return None
    return [num_br(v) for v in vals]


def itens_ncm_cst_cfop(t: str) -> List[Dict[str, str]]:
    """Linhas da tabela "DADOS DOS PRODUTOS/SERVICOS" no formato em que o texto
    traz, uma celula por linha: CODIGO / DESCRICAO / "NCM CST CFOP" / UNID /
    QUANT / VR.UNIT / VALOR / BC.ICMS / V.ICMS / ALIQ.ICMS (V.IPI e ALIQ.IPI
    vazios). Item com IPI preenchido nao casa (fica de fora e o chamador avisa)."""
    sec = secao(t, r'DESCRI[ÇC][ÃA]O\s+DOS?\s+PRODUTOS?', r'DADOS\s+ADICI|INFORMA[ÇC][ÕO]ES\s+COMPLEMENTARES|C[ÁA]LCULO\s+DO\s+ISSQN')
    pat = re.compile(
        r'(?m)^[ \t]*(\S+)[ \t]*\n\s*([^\n]+?)[ \t]*\n\s*(\d{8})\s+(\d{2,3})\s+(\d{4})[ \t]*\n\s*([A-Za-z]{1,6})[ \t]*\n'
        r'\s*(' + _MONEY + r')[ \t]*\n\s*(' + _MONEY + r')[ \t]*\n\s*(' + _MONEY + r')[ \t]*\n\s*(' + _MONEY + r')[ \t]*\n'
        r'\s*(' + _MONEY + r')[ \t]*\n\s*(\d{1,2}(?:,\d{1,4})?)[ \t]*$')
    chaves = ('codigo', 'descricao', 'ncm', 'cst', 'cfop', 'unidade', 'quantidade', 'valor_unitario',
              'valor_total', 'bc_icms', 'valor_icms', 'aliquota_icms')
    return [dict(zip(chaves, m.groups())) for m in pat.finditer(sec)]


def transportador_por_rotulos(t: str) -> Optional[Dict[str, Optional[str]]]:
    sec = secao(t, r'TRANSPORTADOR\s*/\s*VOLUMES\s+TRANSPORTADOS',
                r'C[ÓO]D(?:IGO|\.)\s*(?:PROD\.?)?\s*\n+\s*DESCRI[ÇC][ÃA]O|NCM\s*/\s*SH')
    if not sec:
        return None
    # Legenda de opcoes ("0-EMITENTE / 1-DEST/REM / ...") seguida do codigo
    # marcado (nota nº 478012) ...
    m_frete = re.search(r'FRETE\s+POR\s+CONTA[ \t]*\n((?:\s*\d\s*-[^\n]*\n)+)\s*(\d)[ \t]*$', sec, re.IGNORECASE | re.MULTILINE)
    if not m_frete:
        # ... ou so a opcao escolhida, por extenso ("0-Remetente (CIF)").
        m_frete = re.search(r'FRETE\s+POR\s+CONTA[ \t]*\n()\s*(\d)\s*-\s*[A-Za-z][^\n]*\n(?!\s*\d\s*-)',
                            sec, re.IGNORECASE)
    m_peso = re.search(r'PESO\s+L[ÍI]QUIDO[^\n]*\n\s*([\d.,]+)\s*kg[ \t]*\n\s*([\d.,]+)\s*kg', sec, re.IGNORECASE)
    r = {
        'razao_social': valor_do_rotulo(sec, r'RAZ[ÃA]O\s+SOCIAL', val_texto),
        'cnpj_cpf': valor_do_rotulo(sec, r'CNPJ\s*/\s*CPF', val_cnpj_cpf),
        'inscricao_estadual': valor_do_rotulo(sec, r'INSCRI[ÇC][ÃA]O\s+ESTADUAL', val_ie),
        'frete_por_conta': m_frete.group(2) if m_frete and m_frete.group(2) in '012349' else None,
        'placa_veiculo': valor_do_rotulo(sec, r'PLACA(?:\s+DO\s+VE[ÍI]CULO)?',
                                         lambda v: bool(re.fullmatch(r'[A-Z]{3}-?\d[A-Z0-9]\d{2}', v))),
        'especie': valor_do_rotulo(sec, r'ESP[ÉE]CIE', val_texto),
        'peso_bruto': m_peso.group(1) if m_peso else None,
        'peso_liquido': m_peso.group(2) if m_peso else None,
    }
    if not any(r.values()):
        return None
    return r


def dados_adicionais_sem_rotulo(t: str) -> Optional[str]:
    """Texto de "DADOS ADICIONAIS" quando o gerador nao imprime o rotulo
    "INFORMACOES COMPLEMENTARES": vem depois de "DADOS ADICIONAIS" /
    "RESERVADO AO FISCO" (a nota nº 478012 imprime o rotulo com o erro de
    digitacao "DADOS ADICIOINAIS")."""
    m = re.search(r'DADOS\s+ADICI\w*\s*\n\s*RESERVADO\s+AO\s+FISCO[ \t]*\n(.+?)(?:\x0c|$)', t or '',
                  re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    linhas = [l.strip() for l in m.group(1).split('\n') if l.strip()]
    return '\n'.join(linhas) or None
