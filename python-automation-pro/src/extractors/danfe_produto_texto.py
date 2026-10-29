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
    r'ENDERE[ÇC]O|BAIRRO\s*/\s*DISTRITO|CEP|MUNIC[ÍI]PIO|(?:TELE)?FONE\s*/\s*FAX|UF|'
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
        'telefone': valor_do_rotulo(sec, r'(?:TELE)?FONE\s*/\s*FAX', val_fone),
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
    # Valor com ou sem "R$ " ("R$ 11.645,00" - nota nº 35284).
    return [(m.group(1), m.group(2), m.group(3)) for m in re.finditer(
        r'(?m)^[ \t]*(\d[\w/\-]*)[ \t]*\n\s*(\d{2}/\d{2}/\d{4})[ \t]*\n\s*(?:R\$\s*)?(' + _MONEY + r')[ \t]*$', sec)]


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
    if r['frete_por_conta'] is None:
        # "9 - SEM FRETE" numa linha propria longe do rotulo (nota nº 44986).
        r['frete_por_conta'] = frete_por_extenso(sec)
    if not m_peso:
        # Pesos sem "kg", rotulos em ordem trocada (nota nº 946).
        r['peso_bruto'], r['peso_liquido'] = pesos_bruto_liquido(sec)
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


# ===========================================================================
# Ampliacao 2026-10-29 - notas nº 946 (MUNDIAL INDUSTRIA METALURGICA, Birigui/
# SP) e nº 44986 (COMERCIAL CASA DA LAVOURA, Extrema/MG), dois geradores de
# DANFE digital diferentes do Minerion e da GRAN COFFEE. Mesma filosofia:
# leitura pela ESTRUTURA do DANFE (rotulos padronizados, tipos, identidades
# aritmeticas impressas), nunca pelo nome do emitente; o que nao fecha vira
# None (o chamador avisa), nunca um valor plausivel porem errado.
# ===========================================================================

# Faixas de CEP por UF (Correios) - contraprova estrutural de CEP x UF lidos.
_CEP_FAIXAS = (
    ('SP', 1000, 19999), ('RJ', 20000, 28999), ('ES', 29000, 29999), ('MG', 30000, 39999),
    ('BA', 40000, 48999), ('SE', 49000, 49999), ('PE', 50000, 56999), ('AL', 57000, 57999),
    ('PB', 58000, 58999), ('RN', 59000, 59999), ('CE', 60000, 63999), ('PI', 64000, 64999),
    ('MA', 65000, 65999), ('PA', 66000, 68899), ('AP', 68900, 68999), ('AM', 69000, 69299),
    ('RR', 69300, 69399), ('AM', 69400, 69899), ('AC', 69900, 69999), ('DF', 70000, 72799),
    ('GO', 72800, 72999), ('DF', 73000, 73699), ('GO', 73700, 76799), ('RO', 76800, 76999),
    ('TO', 77000, 77999), ('MT', 78000, 78899), ('MS', 79000, 79999), ('PR', 80000, 87999),
    ('SC', 88000, 89999), ('RS', 90000, 99999),
)


def cep_confere_uf(cep: Optional[str], uf: Optional[str]) -> Optional[bool]:
    """True/False se o CEP (8 digitos) cai/nao cai na faixa dos Correios da UF;
    None quando falta um dos dois."""
    d = _digitos(cep)
    if len(d) != 8 or not uf:
        return None
    pref = int(d[:5])
    return any(u == uf.upper() and ini <= pref <= fim for u, ini, fim in _CEP_FAIXAS)


def nome_emitente_canhoto(t: str) -> Optional[str]:
    """Razao social do emitente pela frase padrao do canhoto "RECEBEMOS DE
    <EMITENTE> OS PRODUTOS ...". Usada quando o letterhead nao traz o nome
    como TEXTO (nota nº 946: o nome e desenhado, o pdfminer so ve o endereco)."""
    m = re.search(r'RECEBEMOS\s+DE\s+(.+?)\s*OS\s+PRODUTOS', t or '', re.IGNORECASE)
    if not m:
        return None
    nome = m.group(1).strip(' -,')
    return nome if val_texto(nome) else None


def _norm(s: Optional[str]) -> str:
    return re.sub(r'[^A-Z0-9]', '', (s or '').upper())


_TIPO_LOGRADOURO = re.compile(
    r'^(?:RUA|R\.|AV\.?|AVEN(?:IDA)?|ROD(?:OVIA)?\.?|ESTR(?:ADA)?\.?|AL(?:AMEDA)?\.?|TRAV(?:ESSA)?\.?|'
    r'PRA[ÇC]A|P[ÇC]A\.?|LARGO|VIA|BR|SP|MG|BA|LOTEAMENTO|QUADRA|SITIO|S[ÍI]TIO|FAZENDA)\b', re.IGNORECASE)


def _endereco_letterhead(linhas: List[str]) -> Optional[Tuple[str, Optional[str], Optional[str], Optional[str]]]:
    """Linhas de endereco do letterhead (entre o nome e "<MUNICIPIO>-<UF>") ->
    (logradouro, numero, complemento, bairro). A linha com ", <numero>" fecha
    o logradouro (linhas anteriores sao a quebra do proprio logradouro: "RUA
    RUA MANOEL SEGUNDO" / "CELICE, 540"); o que vem depois do numero na mesma
    linha, separado por " - ", e [complemento -] bairro; linha seguinte
    inteira e o bairro. Complemento NUNCA e juntado ao logradouro."""
    idx = next((i for i, l in enumerate(linhas)
                if re.search(r',\s+(?:\d+[A-Z]?|S\s*/?\s*N)\b', l, re.IGNORECASE)), None)
    if idx is None:
        return None
    m = re.match(r'^(.*?),\s+(\d+[A-Z]?|S\s*/?\s*N)\b(.*)$', linhas[idx], re.IGNORECASE)
    if not m:
        return None
    logradouro = re.sub(r'\s+', ' ', ' '.join(linhas[:idx] + [m.group(1)])).strip()
    if not val_texto(logradouro):
        return None
    numero = m.group(2).strip()
    cauda = m.group(3).strip().strip('-,').strip()
    partes = [p.strip() for p in re.split(r'\s+-\s+|,\s+', cauda) if p.strip()] if cauda else []
    resto = linhas[idx + 1:]
    complemento, bairro = None, None
    if resto:
        bairro = resto[0]
        complemento = ' - '.join(partes) or None
        if len(resto) > 1:
            return None  # linhas sobrando: estrutura nao reconhecida, sem chute
    elif partes:
        bairro = partes[-1]
        complemento = ' - '.join(partes[:-1]) or None
    return logradouro, numero, complemento, bairro


def _linha_municipio_uf(l: str) -> Optional[Tuple[str, str, str]]:
    """"BIRIGUI-SP" ou "EXTREMA - MG - 37640-000 - (35)3435-1586" ->
    (municipio, uf, resto)."""
    mm = re.fullmatch(r'(.+?)\s*[-/]\s*([A-Z]{2})(?:\s+-\s+(.*))?', l.strip())
    if mm and mm.group(2) in UFS and val_municipio(mm.group(1)):
        return mm.group(1).strip(), mm.group(2), (mm.group(3) or '').strip()
    return None


def emitente_letterhead_livre(t: str) -> Optional[Dict[str, Optional[str]]]:
    """Letterhead do emitente em dois formatos que `emitente_letterhead` nao
    cobre (canhoto no RODAPE, ou rotulo "IDENTIFICACAO DO EMITENTE"):

    - nota nº 44986: "IDENTIFICACAO DO EMITENTE" / nome / "<logr>, <nº> -
      <bairro> -" / "<MUNICIPIO> - <UF> - <CEP> - <fone>" / e-mail, ate "DANFE";
    - nota nº 946: o texto da pagina COMECA pelo letterhead e o nome do
      emitente nao existe como texto (desenhado) - so "<logr>" / "<logr>,
      <nº>" / "<bairro>" / "<MUNICIPIO>-<UF>" / "CEP: ..." / "Fone: ...". O
      nome vem do canhoto ("RECEBEMOS DE <EMITENTE> OS PRODUTOS").

    Devolve None se o bloco nao fechar a estrutura (municipio-UF reconhecido,
    linha de logradouro com numero) - sem chute."""
    t = t or ''
    nome_canhoto = nome_emitente_canhoto(t)
    m = re.search(r'IDENTIFICA[ÇC][ÃA]O\s+DO\s+EMITENTE\s*\n(.+?)\n\s*DANFE\s*\n', t, re.IGNORECASE | re.DOTALL)
    if m:
        linhas = [l.strip() for l in m.group(1).split('\n') if l.strip()]
        if not linhas:
            return None
        nome, corpo, origem = linhas[0], linhas[1:], 'letterhead'
    else:
        # Bloco no INICIO do texto, antes do 1o rotulo de caixa / "DANFE".
        linhas = []
        for l in t.split('\n'):
            s = l.strip()
            if not s:
                continue
            if eh_rotulo(s) or re.fullmatch(r'DANFE|NF-?e', s, re.IGNORECASE):
                break
            linhas.append(s)
        if not linhas or not nome_canhoto:
            return None
        n = _norm(nome_canhoto)
        # O nome pode estar (quebrado em ate 3 linhas) no topo do bloco ...
        k = next((k for k in range(1, min(3, len(linhas)) + 1) if _norm(''.join(linhas[:k])) == n), 0)
        if k:
            nome, corpo, origem = ' '.join(linhas[:k]), linhas[k:], 'letterhead'
        elif _TIPO_LOGRADOURO.match(linhas[0]):
            # ... ou ausente do texto: o bloco comeca pelo logradouro.
            nome, corpo, origem = nome_canhoto, linhas, 'canhoto'
        else:
            return None
    idx_mun, municipio, uf, cep, fone = None, None, None, None, None
    for i, l in enumerate(corpo):
        mu = _linha_municipio_uf(l) if idx_mun is None else None
        if mu:
            idx_mun, (municipio, uf, resto) = i, mu
            for parte in re.split(r'\s+-\s+', resto):
                if not cep and re.fullmatch(r'\d{2}\.?\d{3}-?\d{3}', parte.strip()):
                    cep = _digitos(parte)
                elif not fone and val_fone(parte.strip()):
                    fone = parte.strip()
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
    meio = [l for l in corpo[:idx_mun] if not re.match(r'(?:CEP|Tel|Fone|Telefone)\b', l, re.IGNORECASE)]
    end = _endereco_letterhead(meio)
    if not end:
        return None
    logradouro, numero, complemento, bairro = end
    return {
        'razao_social': nome, 'logradouro': logradouro, 'numero': numero,
        'complemento': complemento, 'bairro': bairro, 'municipio': municipio,
        'uf': uf, 'cep': cep, 'telefone': fone, 'origem_nome': origem,
    }


def data_apos_rotulo(t: str, rotulo: str, max_linhas: int = 6) -> Optional[str]:
    """1a data dd/mm/aaaa nas `max_linhas` linhas nao vazias seguintes ao
    rotulo (linha inteira) - para grades em que o pdfminer intercala o valor
    de uma caixa vizinha entre o rotulo e a data (nota nº 44986). O chamador
    confere a data lida (periodo da chave, ordem emissao <= saida)."""
    m = re.search(r'(?im)^[ \t]*(?:' + rotulo + r')[ \t]*$', t or '')
    if not m:
        return None
    for l in [l.strip() for l in t[m.end():].split('\n') if l.strip()][:max_linhas]:
        md = re.fullmatch(r'(\d{2}/\d{2}/\d{4})', l)
        if md:
            return md.group(1)
    return None


def data_emissao_canhoto(t: str) -> Optional[str]:
    """"EMISSAO: 29/06/2026 - DEST. / REM.: ..." impresso no canhoto."""
    m = re.search(r'\bEMISS[ÃA]O\s*:\s*(\d{2}/\d{2}/\d{4})', t or '', re.IGNORECASE)
    return m.group(1) if m else None


def valor_total_canhoto(t: str) -> Optional[float]:
    """"VALOR TOTAL: R$ 6.102,00" / "Valor:  1.498,00" do canhoto - so para
    CONFERIR o vNF lido na grade."""
    m = re.search(r'RECEBEMOS\s+DE[^\n]*\n(?:[^\n]*\n){0,6}?[^\n]*\bVALOR(?:\s+TOTAL)?\s*:\s*(?:R\$\s*)?(' + _MONEY + r')',
                  t or '', re.IGNORECASE)
    return num_br(m.group(1)) if m else None


def tipo_operacao_marcado(t: str) -> Optional[str]:
    """Digito marcado na caixa "0-ENTRADA / 1-SAIDA" quando o pdfminer o
    despeja algumas linhas depois da legenda (nº/serie/folha no meio)."""
    m = re.search(r'1\s*-\s*SA[ÍI]DA[ \t]*\n', t or '', re.IGNORECASE)
    if not m:
        return None
    for l in [l.strip() for l in t[m.end():].split('\n') if l.strip()][:5]:
        if re.fullmatch(r'[01]', l):
            return l
    return None


def uf_e_fone_mesma_linha(sec: str) -> Tuple[Optional[str], Optional[str]]:
    """Rotulos "UF" e "FONE / FAX" seguidos de UMA linha "<UF> <fone>"
    (nota nº 946: "UF\\nFONE / FAX\\nBA 14982237695")."""
    m = re.search(r'(?im)^\s*UF\s*\n\s*FONE\s*/\s*FAX\s*\n\s*([A-Z]{2})\s+([\d()\s.\-+]{8,}?)\s*$', sec or '')
    if m and m.group(1) in UFS and val_fone(m.group(2)):
        return m.group(1), m.group(2).strip()
    return None, None


def valor_tipado_apos_rotulo(sec: str, rotulo: str, validar: Callable[[str], bool], max_linhas: int = 6) -> Optional[str]:
    """1o valor que passa em `validar` nas `max_linhas` linhas nao vazias
    seguintes a 1a ocorrencia do rotulo, pulando rotulos e valores de outro
    tipo. Usado so para campos que a leitura adjacente (`valor_do_rotulo`) nao
    achou, com contraprova pelo chamador (CEP x UF)."""
    m = re.search(r'(?im)^[ \t]*(?:' + rotulo + r')[ \t]*$', sec or '')
    if not m:
        return None
    for l in [l.strip() for l in sec[m.end():].split('\n') if l.strip()][:max_linhas]:
        if not eh_rotulo(l) and validar(l):
            return l
    return None


def destinatario_por_tipo(t: str) -> Dict[str, Optional[str]]:
    """Bairro/CEP/UF/fone do destinatario quando o pdfminer despeja os valores
    da 2a e 3a linhas da grade longe dos rotulos, intercalados com os de
    outra caixa (nota nº 44986: "CEP\\n29/06/2026\\nDATA SAIDA...\\n
    42700-130"). Le na zona DESTINATARIO -> CALCULO DO IMPOSTO o 1o valor de
    cada TIPO depois do rotulo; a grade do destinatario vem antes da do local
    de retirada/entrega. CEP so e aceito se cair na faixa da UF lida."""
    sec = secao(t, _SEC_DEST_INI, _SEC_DEST_FIM)
    r = {
        'bairro': valor_tipado_apos_rotulo(sec, r'BAIRRO\s*/\s*DISTRITO', lambda v: val_texto(v) and not re.search(r'\d', v)),
        'cep': valor_tipado_apos_rotulo(sec, r'CEP', val_cep),
        'uf': valor_tipado_apos_rotulo(sec, r'UF', val_uf),
        'telefone': valor_tipado_apos_rotulo(sec, r'(?:TELE)?FONE\s*/\s*FAX', val_fone),
    }
    if r['cep']:
        r['cep'] = _digitos(r['cep'])
    if r['uf']:
        r['uf'] = r['uf'].upper()
    if r['cep'] and cep_confere_uf(r['cep'], r['uf']) is not True:
        r['cep'] = None
    return r


def cnpj_destinatario_por_exclusao(t: str, cnpj_emitente: str) -> Optional[str]:
    """CNPJ do destinatario quando o pdfminer o despeja longe do rotulo
    "CNPJ / CPF" (nota nº 44986: depois de "DATA DA EMISSAO"). Candidatos: CNPJ
    com DV conferido, em LINHA PROPRIA (valor de caixa, nao texto corrido), na
    zona DESTINATARIO -> CALCULO DO IMPOSTO, que nao seja o do emitente nem o
    da grade do local de retirada/entrega. So devolve se houver exatamente
    UM candidato - qualquer ambiguidade -> None."""
    zona = secao(t, _SEC_DEST_INI, _SEC_DEST_FIM)
    excluir = {cnpj_emitente}
    loc = secao(t, r'INFORMA[ÇC][ÕO]ES\s+DO\s+LOCAL|LOCAL\s+DE\s+(?:RETIRADA|ENTREGA)',
                r'(?m)^\s*(?:FATURA|DUPLICATAS)\s*$|' + _SEC_DEST_FIM)
    c_loc = valor_do_rotulo(loc, r'CNPJ\s*/\s*CPF', val_cnpj_cpf)
    if c_loc:
        excluir.add(_digitos(c_loc))
    cands: List[str] = []
    for m in re.finditer(r'(?m)^[ \t]*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})[ \t]*$', zona):
        d = _digitos(m.group(1))
        if _cnpj_dv_ok(d) and d not in excluir and all(_digitos(c) != d for c in cands):
            cands.append(m.group(1))
    return cands[0] if len(cands) == 1 else None


def ie_emitente_antes_destinatario(t: str) -> Optional[str]:
    """IE do emitente quando o pdfminer a despeja longe do rotulo, como ultima
    linha antes de "DESTINATARIO / REMETENTE" (nota nº 44986). So aceita se o
    MESMO valor aparecer em outro ponto colado a um rotulo "INSCRICAO
    ESTADUAL" (contraprova - na 44986, a grade do local de retirada)."""
    m = re.search(r'\n\s*([\d./-]{2,20})[ \t]*\n+\s*DESTINAT[ÁA]RIO\s*/?\s*REMETENTE', t or '', re.IGNORECASE)
    if not m or not val_ie(m.group(1)) or _cnpj_dv_ok(_digitos(m.group(1))):
        return None
    ie = _digitos(m.group(1))
    for mo in re.finditer(r'(?im)^\s*INSCRI[ÇC][ÃA]O\s+ESTADUAL\s*\n\s*([\d./-]+)\s*$', t):
        if _digitos(mo.group(1)) == ie:
            return ie
    return None


def fatura_inline(t: str) -> List[Tuple[str, str, str]]:
    """Duplicatas em texto corrido "N.:001 Vl.:R$ 9.328,20 Venc.:06/03/2026;
    ..." (nota nº 946) -> (numero, vencimento, valor)."""
    return [(m.group(1), m.group(3), m.group(2)) for m in re.finditer(
        r'\bN\.?\s*[º°]?\s*:\s*(\w[\w/\-]*)\s+V(?:l|alor)\.?\s*:\s*(?:R\$\s*)?(' + _MONEY + r')\s+Venc(?:\.|imento)?\s*:\s*(\d{2}/\d{2}/\d{4})',
        t or '', re.IGNORECASE)]


def duplicatas_colunas(t: str) -> List[Tuple[str, str, str]]:
    """Caixa "DUPLICATAS" com colunas "Nº DUPLICATA | VENC. | VALOR" (nota nº
    44986) -> (numero, vencimento, valor)."""
    sec = secao(t, r'(?m)^\s*DUPLICATAS\s*$', _SEC_DEST_FIM)
    if not re.search(r'(?im)^\s*VENC(?:\.|IMENTO)\s*$', sec):
        return []
    return [(m.group(1), m.group(2), m.group(3)) for m in re.finditer(
        r'(?m)^[ \t]*(\d[\w/\-]*)[ \t]*\n\s*(\d{2}/\d{2}/\d{4})[ \t]*\n\s*(' + _MONEY + r')[ \t]*$', sec)]


def informacoes_complementares_ate_canhoto(t: str) -> Optional[str]:
    """Texto de "INFORMACOES COMPLEMENTARES" quando o bloco nao termina em
    "RESERVADO AO FISCO" (nota nº 946: rotulos da caixa do ISSQN no meio e o
    canhoto "RECEBEMOS DE" logo depois)."""
    m = re.search(r'INFORMA[ÇC][ÕO]ES\s+COMPLEMENTARES[ \t]*\n(.+?)(?=\n[^\n]*RECEBEMOS\s+DE|RESERVADO\s+AO\s+FISCO|\x0c|$)',
                  t or '', re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    linhas = [l.strip() for l in m.group(1).split('\n') if l.strip() and not eh_rotulo(l.strip())]
    return '\n'.join(linhas) or None


def frete_por_extenso(sec: str) -> Optional[str]:
    """Modalidade do frete impressa por extenso numa linha propria, longe do
    rotulo ("9 - SEM FRETE", nota nº 44986). Codigo e texto precisam
    concordar (0 remetente/emitente, 1 destinatario, 2 terceiros, 3/4
    proprio, 9 sem frete); mais de uma linha candidata -> None."""
    sentido = {'0': r'REMET|EMIT|CIF', '1': r'DEST|FOB', '2': r'TERC', '3': r'PR[ÓO]PRI', '4': r'PR[ÓO]PRI',
               '9': r'SEM\s+(?:FRETE|OCORR|TRANSP)'}
    achados = []
    for m in re.finditer(r'(?im)^\s*([0-49])\s*-\s*([A-Za-zÀ-ÿ][^\n]*?)\s*$', sec or ''):
        if re.search(sentido[m.group(1)], m.group(2), re.IGNORECASE):
            achados.append(m.group(1))
    return achados[0] if len(set(achados)) == 1 else None


def pesos_bruto_liquido(sec: str) -> Tuple[Optional[str], Optional[str]]:
    """Rotulos "PESO LIQUIDO" e "PESO BRUTO" (em qualquer ordem) seguidos dos
    dois valores sem unidade (nota nº 946). A ordem dos valores no texto nao
    e confiavel; peso bruto >= peso liquido (fisico) decide."""
    m = re.search(r'(?im)^\s*PESO\s+(?:L[ÍI]QUIDO|BRUTO)[^\n]*\n\s*PESO\s+(?:L[ÍI]QUIDO|BRUTO)[^\n]*\n'
                  r'\s*(\d{1,3}(?:\.\d{3})*,\d{1,4})\s*(?:kg)?\s*\n\s*(\d{1,3}(?:\.\d{3})*,\d{1,4})\s*(?:kg)?\s*$', sec or '')
    if not m:
        return None, None
    a, b = m.group(1), m.group(2)
    return (a, b) if num_br(a) >= num_br(b) else (b, a)


# --- itens: tabela "DADOS DO PRODUTO / SERVICOS" com uma celula por linha ---

_CAB_ITEM = re.compile(
    r'^(?:C[ÓO]DIGO(?:\s+DO)?|PRODUTO|PROD\.?\s*/\s*SERV\.?|DESCRI[ÇC][ÃA]O.*|NCM\s*/?\s*SH|CST|CSOSN|'
    r'CFOP(?:\s+UNID\.?)?|UND\.?|UNID\.?|UN\.?|QNT\.?|QUANT\.?|QTD\.?|VALOR|UNIT[ÁA]RIO|TOTAL|DESCONTO|'
    r'B\.?\s*C[ÁA]LCULO|BASE|C[ÁA]LC\.?\s*ICMS|ICMS|IPI|I\.?C\.?M\.?S\.?|I\.?P\.?I\.?|AL[ÍI]Q\.?|AL[ÍI]QUOTAS)$',
    re.IGNORECASE)
_NUM_CEL = re.compile(r'^\d{1,3}(?:\.\d{3})*,\d{1,4}$|^\d+$')


def itens_colunas(t: str) -> Tuple[List[Dict[str, object]], List[str]]:
    """Itens da tabela "DADOS DO PRODUTO / SERVICOS" quando cada celula sai
    numa linha (NCM, CST, CFOP e UNID. em linhas proprias ou juntas), com a
    descricao possivelmente quebrada em varias linhas e o CODIGO despejado
    entre os rotulos do cabecalho (notas nº 946 e nº 44986).

    Colunas numericas, na ordem do cabecalho nacional: QUANT, V.UNIT, V.TOTAL,
    [DESCONTO - so se o cabecalho tiver a coluna], BC ICMS, V.ICMS, V.IPI e as
    duas aliquotas. A aliquota de ICMS e a que fecha BC x ALIQ = V.ICMS (o
    texto do cabecalho "ALIQUOTAS / IPI / ICMS" nao reflete a ordem visual).
    Cada item precisa fechar QUANT x V.UNIT = V.TOTAL e BC x ALIQ = V.ICMS;
    qualquer item que nao feche, ou numero de CODIGOS diferente do de itens,
    devolve lista VAZIA + motivos (o chamador avisa) - nunca um item chutado."""
    sec = secao(t, r'DADOS\s+DOS?\s+PRODUTOS?\s*/\s*SERVI[ÇC]OS?', r'C[ÁA]LCULO\s+DO\s+ISSQN|DADOS\s+ADICI')
    linhas = [l.strip() for l in sec.split('\n') if l.strip()]
    # Codigos: celulas entre o rotulo "CODIGO..." e o rotulo "DESCRICAO...".
    i_cod = next((i for i, l in enumerate(linhas) if re.match(r'C[ÓO]DIGO', l, re.IGNORECASE)), None)
    i_des = next((i for i, l in enumerate(linhas) if re.match(r'DESCRI[ÇC][ÃA]O', l, re.IGNORECASE)), None)
    if i_cod is None or i_des is None or i_des < i_cod:
        return [], []
    i_ncm = [i for i, l in enumerate(linhas) if i > i_des and re.match(r'^\d{8}\b', l)]
    if not i_ncm:
        return [], []
    cab = linhas[:i_ncm[0]]
    tem_desc = any(re.fullmatch(r'DESCONTO', l, re.IGNORECASE) for l in cab[i_des:])
    codigos = [l for l in cab[i_cod + 1:i_des] if not _CAB_ITEM.match(l)]
    ultimo_cab = max(i for i, l in enumerate(cab) if _CAB_ITEM.match(l) or i == i_des)
    n_num = 9 if tem_desc else 8
    itens: List[Dict[str, object]] = []
    motivos: List[str] = []
    inicio_desc = ultimo_cab + 1
    pos = i_ncm[0]
    while pos < len(linhas) and re.match(r'^\d{8}\b', linhas[pos]):
        descricao = ' '.join(re.sub(r'\s+', ' ', l) for l in linhas[inicio_desc:pos]).strip()
        tokens: List[str] = []
        fim = pos
        while fim < len(linhas) and len(tokens) < 4 + n_num:
            tokens.extend(linhas[fim].split())
            fim += 1
        if len(tokens) != 4 + n_num:
            return [], [f"item {len(itens) + 1}: células da linha da tabela não fecham com o cabeçalho"]
        ncm, cst, cfop, unid = tokens[:4]
        nums = tokens[4:]
        if not (re.fullmatch(r'\d{8}', ncm) and re.fullmatch(r'\d{2,3}', cst) and re.fullmatch(r'\d{4}', cfop)
                and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,5}\.?', unid) and all(_NUM_CEL.match(n) for n in nums)
                and val_texto(descricao)):
            return [], [f"item {len(itens) + 1}: NCM/CST/CFOP/UNID./valores fora do tipo esperado"]
        v = [num_br(n) for n in nums]
        if tem_desc:
            qtd, vun, vtot, vdesc, bc, vicms, vipi, a1, a2 = v
        else:
            (qtd, vun, vtot, bc, vicms, vipi, a1, a2), vdesc = v, 0.0
        if abs(qtd * vun - vtot) > max(0.01, vtot * 0.001):
            return [], [f"item {len(itens) + 1}: QUANT x VR.UNIT não fecha com o VALOR TOTAL impresso"]
        fecha = [a for a in (a1, a2) if abs(round(bc * a / 100, 2) - vicms) <= 0.01]
        if not fecha:
            return [], [f"item {len(itens) + 1}: BC ICMS x ALÍQ. não fecha com o V. ICMS impresso"]
        if len(fecha) == 2 and a1 != a2:
            return [], [f"item {len(itens) + 1}: alíquotas de ICMS e IPI não distinguíveis (BC ICMS zerada)"]
        aliq_icms = fecha[0]
        aliq_ipi = a2 if aliq_icms == a1 else a1
        if vipi and abs(round(vtot * aliq_ipi / 100, 2) - vipi) > 0.01:
            motivos.append(f"item {len(itens) + 1}: V.IPI não fecha com V.TOTAL x ALÍQ.IPI - conferir")
        itens.append({
            'descricao': descricao, 'ncm': ncm, 'cst': cst, 'cfop': cfop, 'unidade': unid.rstrip('.'),
            'quantidade': qtd, 'valor_unitario': vun, 'valor_total': vtot, 'valor_desconto': vdesc, 'bc_icms': bc,
            'valor_icms': vicms, 'aliquota_icms': aliq_icms, 'valor_ipi': vipi, 'aliquota_ipi': aliq_ipi,
        })
        inicio_desc = fim
        # proximo item: 1a linha de NCM depois desta
        prox = next((i for i in i_ncm if i >= fim), None)
        if prox is None:
            break
        pos = prox
    if len(codigos) != len(itens):
        return [], [f"{len(codigos)} código(s) de produto para {len(itens)} item(ns) - associação não confiável"]
    for it, cod in zip(itens, codigos):
        it['codigo'] = cod
    return itens, motivos


# --- grade CALCULO DO IMPOSTO pela identidade dos totais -------------------

_ROT_GRADE = (
    ('bc_st', r'BASE\s+(?:DE\s+)?C[ÁA]LC(?:ULO|\.)?\s+(?:DO\s+)?ICMS\s+(?:SUBST|S\.?\s*T).*'),
    ('bc', r'BASE\s+(?:DE\s+)?C[ÁA]LC(?:ULO|\.)?\s+(?:DO\s+)?ICMS'),
    ('st', r'VALOR\s+(?:DO\s+)?ICMS\s+(?:SUBST|S\.?\s*T).*'),
    ('icms', r'VALOR\s+(?:DO\s+)?ICMS'),
    ('trib', r'VALOR\s+APROX.*|V\.?\s*TOT\.?\s*TRIB.*|VALOR\s+TOTAL\s+(?:DOS\s+|APROX.*\s+)?TRIBUTOS.*'),
    ('prod', r'VALOR\s+TOTAL\s+DOS\s+PRODUTOS'),
    ('frete', r'VALOR\s+DO\s+FRETE'),
    ('seguro', r'VALOR\s+DO\s+SEGURO'),
    ('desc', r'DESCONTO'),
    ('outras', r'OUTRAS\s+DESP.*'),
    ('ipi', r'VALOR\s+(?:DO\s+)?IPI'),
    ('nf', r'VALOR\s+TOTAL\s+DA\s+NOTA'),
)


def grade_por_identidade(t: str, itens: List[Dict[str, object]]) -> Optional[Dict[str, float]]:
    """Grade "CALCULO DO IMPOSTO" quando o pdfminer despeja os valores numa
    ordem propria, misturada com a caixa do transportador (notas nº 946 e nº
    44986 - a ordem nao e a mesma nos dois geradores). Atribuicao por
    IDENTIDADES, nao por posicao: com itens ja conferidos, vProd = soma
    V.TOTAL, vBC = soma BC, vICMS = soma V.ICMS, vIPI = soma V.IPI (cada um
    precisa estar entre os valores impressos); vNF = vProd + vIPI precisa
    estar entre os restantes e todo o resto precisa ser zero - exceto um
    unico valor quando a grade tem a caixa "VALOR APROX. DOS TRIBUTOS" (fora
    da identidade do total). Qualquer outra situacao (frete, desconto, ST...
    com valor) e ambigua por ordem de texto -> None (chamador avisa)."""
    if not itens:
        return None
    sec = secao(t, r'C[ÁA]LCULO\s+D[OE]\s+IMPOSTO', r'DADOS\s+DOS?\s+PRODUTOS?\s*/\s*SERVI')
    rotulos = set()
    for l in sec.split('\n'):
        s = l.strip()
        for chave, pad in _ROT_GRADE:
            if re.fullmatch(pad, s, re.IGNORECASE):
                rotulos.add(chave)
                break
        else:
            if re.match(r'(?:V\.|VALOR|BASE)\b.*\b(?:FCP|PIS|COFINS|II|UF|DIFAL|PARTILHA|DESON)', s, re.IGNORECASE):
                return None  # caixa de tributo nao modelada: atribuicao insegura
    obrig = {'bc', 'icms', 'prod', 'nf'}
    if not obrig <= rotulos:
        return None
    vals = [round(num_br(v), 2) for v in re.findall(r'(?m)^[ \t]*(\d{1,3}(?:\.\d{3})*,\d{2})[ \t]*$', sec)]
    if len(vals) != len(rotulos):
        return None
    s = lambda k: round(sum(float(i[k]) for i in itens), 2)
    ancoras = {'prod': s('valor_total'), 'bc': s('bc_icms'), 'icms': s('valor_icms')}
    if 'ipi' in rotulos:
        ancoras['ipi'] = s('valor_ipi')
    resto = list(vals)
    for v in ancoras.values():
        if v not in resto:
            return None
        resto.remove(v)
    v_nf = round(ancoras['prod'] + ancoras.get('ipi', 0.0), 2)
    if v_nf not in resto:
        return None
    resto.remove(v_nf)
    nao_zero = [v for v in resto if v != 0]
    if nao_zero and not ('trib' in rotulos and len(nao_zero) == 1):
        return None
    return {
        'base_calculo_icms': ancoras['bc'], 'valor_icms': ancoras['icms'], 'base_calculo_icms_st': 0.0,
        'valor_icms_st': 0.0, 'valor_total_produtos': ancoras['prod'], 'valor_frete': 0.0,
        'valor_seguro': 0.0, 'desconto': 0.0, 'outras_despesas': 0.0,
        'valor_ipi': ancoras.get('ipi', 0.0), 'valor_total_nota': v_nf,
    }


# ===========================================================================
# Ampliacao 2026-10-29 - nota nº 35284 (DANFE digital com o letterhead em
# texto corrido quebrado em linhas e a tabela de itens despejada pelo pdfminer
# COLUNA A COLUNA: todos os codigos, depois todas as descricoes, todos os NCM,
# ...). Mesma filosofia: estrutura do DANFE + identidades aritmeticas; o que
# nao fecha vira None/lista vazia + motivo, nunca um valor chutado.
# ===========================================================================

def _linhas_pos_canhoto(t: str) -> Optional[List[str]]:
    """Linhas entre a ULTIMA "Serie <s>" do canhoto e o box "DANFE"."""
    m = re.search(r'ASSINATURA\s+DO\s+RECEBEDOR\s*\n(.+?)\n\s*DANFE\s*\n', t or '', re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    ultima = None
    for ms in re.finditer(r'(?im)^\s*S[ÉE]RIE\s*:?\s*\d{1,3}\s*$', m.group(1)):
        ultima = ms
    if ultima is None:
        return None
    return [l.strip() for l in m.group(1)[ultima.end():].split('\n') if l.strip()]


_FONE_LINHA = re.compile(r'(?:Tel|Fone|Telefone)\.?\s*:?\s*([\d()\s.\-+]{8,})', re.IGNORECASE)
_ENDERECO_CORRIDO = re.compile(
    r'^(?P<logr>.+?),\s+(?P<num>\d+[A-Z]?|S\s*/?\s*N)\s+-\s+(?P<bairro>.+?)\s+-\s+(?P<mun>[^-]+?)\s+-\s+'
    r'(?P<uf>[A-Z]{2})\s+-\s+CEP\s*:?\s*(?P<cep>\d{2}\.?\d{3}-?\d{3})$', re.IGNORECASE)


def emitente_letterhead_corrido(t: str) -> Optional[Dict[str, Optional[str]]]:
    """Letterhead do emitente depois do canhoto em que o endereco e UMA frase
    quebrada em linhas: "<logr>, <nº> -" / "<bairro> - <MUN> - <UF> - CEP:" /
    "<cep>" / "Fone: ..." (nota nº 35284). A razao social vem do canhoto
    "RECEBEMOS DE <EMITENTE> OS PRODUTOS" (preferido); a 1a linha do bloco so
    e tratada como nome se for IGUAL a ele. Aceito so se a frase inteira fechar
    a estrutura, com UF valida, municipio sem digitos e CEP na faixa da UF."""
    nome = nome_emitente_canhoto(t)
    linhas = _linhas_pos_canhoto(t)
    if not nome or not linhas:
        return None
    corpo = linhas[1:] if _norm(linhas[0]) == _norm(nome) else linhas
    fone = None
    resto = []
    for l in corpo:
        mf = _FONE_LINHA.fullmatch(l)
        if mf:
            fone = fone or mf.group(1).strip()
        else:
            resto.append(l)
    m = _ENDERECO_CORRIDO.match(re.sub(r'\s+', ' ', ' '.join(resto)).strip())
    if not m:
        return None
    uf, mun, cep = m.group('uf').upper(), m.group('mun').strip(), _digitos(m.group('cep'))
    if uf not in UFS or not val_municipio(mun) or not val_texto(m.group('logr')) or cep_confere_uf(cep, uf) is not True:
        return None
    partes = [p.strip() for p in re.split(r'\s+-\s+', m.group('bairro')) if p.strip()]
    return {
        'razao_social': nome, 'logradouro': m.group('logr').strip(), 'numero': m.group('num').strip(),
        'complemento': ' - '.join(partes[:-1]) or None, 'bairro': partes[-1] if partes else None,
        'municipio': mun, 'uf': uf, 'cep': cep, 'telefone': fone,
    }


def uf_antes_do_rotulo(sec: str, cep: Optional[str]) -> Optional[str]:
    """UF impressa ANTES do proprio rotulo ("BA\\n\\nUF" - nota nº 35284, o
    rotulo "UF" seguido de outro rotulo). Aceita so com o CEP lido do mesmo
    bloco caindo na faixa da UF (contraprova estrutural)."""
    m = re.search(r'(?m)^[ \t]*([A-Z]{2})[ \t]*\n\s*UF[ \t]*$', sec or '')
    if not m or m.group(1) not in UFS or cep_confere_uf(cep, m.group(1)) is not True:
        return None
    return m.group(1)


def _blocos_numericos(linhas: List[List[str]], n: int) -> Optional[List[List[List[List[str]]]]]:
    """Agrupa as linhas numericas da tabela em faixas de N linhas. Cada faixa
    com k>=2 valores por linha = k colunas lidas linha a linha. Uma sequencia
    de linhas com UM valor e ambigua: N linhas = 1 coluna, ou 2N linhas = 2
    colunas intercaladas linha a linha (o pdfminer junta caixas vizinhas -
    nota nº 35284, BC ICMS / V. ICMS). Devolve, por trecho, as alternativas
    de colunas; None se algum trecho nao for multiplo de N."""
    trechos: List[List[List[str]]] = []
    for toks in linhas:
        if trechos and len(trechos[-1][0]) == len(toks):
            trechos[-1].append(toks)
        else:
            trechos.append([toks])
    alternativas = []
    for tr in trechos:
        if len(tr) % n:
            return None
        k = len(tr[0])
        if k >= 2:
            cols = []
            for ini in range(0, len(tr), n):
                faixa = tr[ini:ini + n]
                cols.extend([[l[j] for l in faixa] for j in range(k)])
            alternativas.append([cols])
            continue
        vals = [l[0] for l in tr]
        m = len(vals) // n

        def compor(pos: int) -> List[List[List[str]]]:
            if pos == m:
                return [[]]
            saida = []
            for c in (1, 2):
                if pos + c > m:
                    continue
                bloco = vals[pos * n:(pos + c) * n]
                cols = [bloco] if c == 1 else [bloco[0::2], bloco[1::2]]
                saida.extend(cols + resto for resto in compor(pos + c))
            return saida

        alternativas.append(compor(0))
    return alternativas


def _fecha(a: float, b: float) -> bool:
    """Igualdade monetaria com tolerancia de 1 centavo (arredondamento do
    emissor: 6.019,98 x 18% = 1.083,5964 impresso 1.083,59)."""
    return abs(round(a, 2) - round(b, 2)) <= 0.0101


def itens_por_coluna(t: str) -> Tuple[List[Dict[str, object]], List[str]]:
    """Itens da tabela "DADOS DOS PRODUTOS / SERVICOS" quando o pdfminer a
    despeja COLUNA A COLUNA (nota nº 35284): N codigos entre "CODIGO" e
    "DESCRICAO", o cabecalho, N descricoes, N NCM, N CST, N "CFOP UNID." e
    depois as colunas numericas QUANT, V.UNIT, [V.DESC], V.TOTAL, BC ICMS,
    V.ICMS, V.IPI, ALIQ.ICMS, ALIQ.IPI - algumas juntas numa linha por item
    ("0,00 18,00 0,00") ou intercaladas (BC/V.ICMS).

    Remonta as N linhas e so aceita se TODAS fecharem: QUANT x V.UNIT =
    V.TOTAL (centavo), BC = V.TOTAL - V.DESC quando tributado, BC x ALIQ =
    V.ICMS, BC zerada -> V.ICMS zerado. Cada agrupamento possivel das colunas
    e testado; aceito so se exatamente UM resultado fechar. Os totais da grade
    (soma V.TOTAL/V.DESC/BC/V.ICMS) sao conferidos pelo chamador. Qualquer
    falha -> lista vazia + motivo."""
    sec = secao(t, r'DADOS\s+DOS?\s+PRODUTOS?\s*/\s*SERVI[ÇC]OS?', r'C[ÁA]LCULO\s+DO\s+ISSQN|DADOS\s+ADICI')
    linhas = [l.strip() for l in sec.split('\n') if l.strip()]
    i_cod = next((i for i, l in enumerate(linhas) if re.match(r'C[ÓO]DIGO', l, re.IGNORECASE)), None)
    i_des = next((i for i, l in enumerate(linhas) if re.match(r'DESCRI[ÇC][ÃA]O', l, re.IGNORECASE)), None)
    if i_cod is None or i_des is None or i_des < i_cod:
        return [], []
    codigos = [l for l in linhas[i_cod + 1:i_des] if not _CAB_ITEM.match(l)]
    n = len(codigos)
    if n < 1 or not all(re.fullmatch(r'[\w.\-/]+', c) for c in codigos):
        return [], []
    i_ncm = next((i for i, l in enumerate(linhas) if i > i_des and re.fullmatch(r'\d{8}', l)), None)
    if i_ncm is None or i_ncm - n <= i_des:
        return [], []
    # Formato coluna a coluna: N NCM em linhas proprias, seguidos.
    if not all(re.fullmatch(r'\d{8}', l) for l in linhas[i_ncm:i_ncm + n]):
        return [], []
    descricoes = linhas[i_ncm - n:i_ncm]
    cab = linhas[i_des:i_ncm - n]
    if not _CAB_ITEM.match(cab[-1]) or any(_CAB_ITEM.match(d) for d in descricoes) \
            or not all(val_texto(d) for d in descricoes):
        return [], [f"{n} código(s) de produto sem {n} descrição(ões) de uma linha antes dos NCM - "
                    "descrição quebrada ou cabeçalho não reconhecido"]
    tem_desc = any(re.fullmatch(r'DESCONTO', l, re.IGNORECASE) for l in cab)
    # Colunas de texto: NCM, CST, CFOP, UNID. em faixas de N linhas.
    pos, cats = i_ncm, []
    while len(cats) < 4:
        faixa = [l.split() for l in linhas[pos:pos + n]]
        if len(faixa) < n or len({len(f) for f in faixa}) != 1:
            return [], ["colunas NCM/CST/CFOP/UNID. não formam faixas de uma linha por item"]
        cats.extend([[f[j] for f in faixa] for j in range(len(faixa[0]))])
        pos += n
    if len(cats) != 4:
        return [], ["colunas NCM/CST/CFOP/UNID. não fecham com o cabeçalho"]
    ncms, csts, cfops, unids = cats
    if not (all(re.fullmatch(r'\d{8}', v) for v in ncms) and all(re.fullmatch(r'\d{2,4}', v) for v in csts)
            and all(re.fullmatch(r'\d{4}', v) for v in cfops)
            and all(re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,5}\.?', v) for v in unids)):
        return [], ["NCM/CST/CFOP/UNID. fora do tipo esperado"]
    nums = []
    for l in linhas[pos:]:
        toks = l.split()
        if not all(_NUM_CEL.match(x) for x in toks):
            break
        nums.append(toks)
    n_num = 9 if tem_desc else 8
    alternativas = _blocos_numericos(nums, n)
    if alternativas is None:
        return [], ["valores numéricos da tabela não formam faixas de uma linha por item"]
    combinacoes: List[List[List[str]]] = [[]]
    for alt in alternativas:
        combinacoes = [c + a for c in combinacoes for a in alt]
    resultados = []
    for cols in combinacoes:
        if len(cols) != n_num:
            continue
        itens = []
        for i in range(n):
            v = [num_br(c[i]) for c in cols]
            if tem_desc:
                qtd, vun, vdesc, vtot, bc, vicms, vipi, a1, a2 = v
            else:
                (qtd, vun, vtot, bc, vicms, vipi, a1, a2), vdesc = v, 0.0
            if not _fecha(qtd * vun, vtot) or vdesc > vtot:
                break
            if bc and not _fecha(bc, vtot - vdesc):
                break
            if not bc and vicms:
                break
            fecha = [a for a in (a1, a2) if _fecha(bc * a / 100, vicms)]
            if not fecha or (len(fecha) == 2 and a1 != a2):
                break
            aliq_icms = fecha[0]
            aliq_ipi = a2 if aliq_icms == a1 else a1
            if vipi and not _fecha(vtot * aliq_ipi / 100, vipi):
                break
            itens.append({
                'codigo': codigos[i], 'descricao': re.sub(r'\s+', ' ', descricoes[i]), 'ncm': ncms[i],
                'cst': csts[i], 'cfop': cfops[i], 'unidade': unids[i].rstrip('.'), 'quantidade': qtd,
                'valor_unitario': vun, 'valor_total': vtot, 'valor_desconto': vdesc, 'bc_icms': bc,
                'valor_icms': vicms, 'aliquota_icms': aliq_icms, 'valor_ipi': vipi, 'aliquota_ipi': aliq_ipi,
            })
        else:
            if itens not in resultados:
                resultados.append(itens)
    if not resultados:
        return [], [f"{n} item(ns) lidos coluna a coluna, mas nenhuma montagem das colunas numéricas fecha "
                    "QUANT x V.UNIT = V.TOTAL, BC = V.TOTAL - DESC. e BC x ALÍQ. = V.ICMS em todos os itens"]
    if len(resultados) > 1:
        return [], [f"{n} item(ns) lidos coluna a coluna com mais de uma montagem possível das colunas - "
                    "associação não confiável"]
    return resultados[0], []
