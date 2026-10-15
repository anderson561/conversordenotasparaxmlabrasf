"""Helpers dos templates da "NFS-e de Saubara/BA" (plataforma Link3 Tecnologia).

Dois templates distintos, ambos PDF DIGITAL (texto embutido, sem OCR), ambos
com o cabeçalho "ESTADO DA BAHIA / MUNICIPIO DE SAUBARA / Secretaria Municipal
de Administração..." e o CNPJ da PREFEITURA (13.040.233/0001-60 - nunca o do
prestador nem o do tomador) logo abaixo:

* Variante 1 (`LAYOUT_SAUBARA`)   - "Nota Fiscal Eletrônica de Serviços",
  blocos "DADOS DO EMITENTE" / "DADOS DO DESTINATÁRIO", grade de valores no
  rodapé com rótulo e valor em linhas vizinhas ("Valor ISS:" / "48,00").
  Não imprime CEP, Inscrição Municipal nem competência. Achado real
  2026-09-14, nota 202600000000351 (ASSOCIAÇÃO RELIOGIOSA E CULTURAL BABÁ OKÉ
  -> TEMIS Projetos de Meio Ambiente e Sustentabilidade, R$ 1.600,00).
* Variante 2 (`LAYOUT_SAUBARA_2`) - "NOTA FISCAL ELETRÔNICA DE SERVIÇOS -
  NFS-e", blocos "PRESTADOR DE SERVIÇOS" / "TOMADOR DE SERVIÇOS", código
  IBGE impresso ao lado de "CIDADE -", CNAE/NBS/item LC 116, regime especial
  e grade de tributos em 2 linhas (12 colunas). Achado real 2026-09-14, nota
  202600000000080 (VIVA COMUNICAÇAO E SERVIÇOS LTDA -> TEMIS, R$ 120,00).

Em ambas o `pdfminer.extract_text()` despeja os blocos de rótulo/valor numa
ordem que depende da geometria da caixa (ex.: na variante 2 as colunas da
direita do prestador saem DEPOIS do cabeçalho "TOMADOR DE SERVIÇOS"), então
cada rótulo é lido por OCORRÊNCIA (1ª = prestador/emitente, 2ª = tomador/
destinatário) e o valor é o da própria linha seguinte, nunca da posição
absoluta no texto. Onde a ordem não bate o esperado, o campo vira sentinela +
aviso (princípio de integridade fiscal do projeto: dado ausente é
recuperável por um humano, dado errado é escriturado).

Tudo aqui é função pura sobre texto (testável sem PDF nem OCR).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from ..models.nfse_models import Endereco, Entidade, Valores

# Código IBGE de Saubara/BA, conferido na API oficial do IBGE
# (servicodados.ibge.gov.br/api/v1/localidades/municipios/2929750 -> "Saubara",
# UF BA) e impresso na própria nota da variante 2 ("COD. MUNICIPIO GERADOR
# 2929750BA", "CIDADE - 2929750 Saubara").
COD_IBGE_SAUBARA = '2929750'
MUNICIPIO_SAUBARA = 'Saubara'
UF_SAUBARA = 'BA'

VARIANTE_1 = 1
VARIANTE_2 = 2

_SENTINELA_DOC = '00000000000000'
_SENTINELA_NUMERO = '00000000'
_SENTINELA_CODIGO_VERIFICACAO = 'XXXX-XXXX'

# O cabeçalho da prefeitura precisa aparecer logo no início do texto da nota:
# um "MUNICIPIO DE SAUBARA" lá no meio é endereço/município citado por uma
# nota de OUTRA cidade, nunca o cabeçalho.
_JANELA_CABECALHO = 600

_UF_POR_NOME = {
    'ACRE': 'AC', 'ALAGOAS': 'AL', 'AMAPA': 'AP', 'AMAZONAS': 'AM', 'BAHIA': 'BA',
    'CEARA': 'CE', 'DISTRITO FEDERAL': 'DF', 'ESPIRITO SANTO': 'ES', 'GOIAS': 'GO',
    'MARANHAO': 'MA', 'MATO GROSSO': 'MT', 'MATO GROSSO DO SUL': 'MS',
    'MINAS GERAIS': 'MG', 'PARA': 'PA', 'PARAIBA': 'PB', 'PARANA': 'PR',
    'PERNAMBUCO': 'PE', 'PIAUI': 'PI', 'RIO DE JANEIRO': 'RJ',
    'RIO GRANDE DO NORTE': 'RN', 'RIO GRANDE DO SUL': 'RS', 'RONDONIA': 'RO',
    'RORAIMA': 'RR', 'SANTA CATARINA': 'SC', 'SAO PAULO': 'SP', 'SERGIPE': 'SE',
    'TOCANTINS': 'TO',
}

# Regime especial de tributação impresso -> código da tabela ABRASF 2.01.
_REGIME_ESPECIAL = (
    (r'Microempresa\s+Municipal', '1'),
    (r'Estimativa', '2'),
    (r'Sociedade\s+de\s+Profissionais', '3'),
    (r'Cooperativa', '4'),
    (r'Microempreendedor\s+Individual|\bMEI\b', '5'),
    (r'Microempres[aá]rio\s+e\s+Empresa\s+de\s+Pequeno\s+Porte|\bME\s*/?\s*EPP\b', '6'),
)

_ROTULOS_V2_GRADE = (
    'PIS', 'COFINS', 'INSS', 'IR', 'CSLL', 'Dedu[çc][õo]es', 'Base\\s+C[áa]lculo',
    'Al[íi]quota', 'ISS', 'Reten[çc][ãa]o\\s+ISS', 'Outras\\s+Reten[çc][õo]es',
    'Valor\\s+L[íi]quido',
)


@dataclass
class NotaSaubara:
    """Campos extraídos de uma NFS-e de Saubara (uma das 2 variantes)."""
    variante: int
    numero: str
    codigo_verificacao: str
    data_emissao: Optional[datetime]
    discriminacao: str
    codigo_servico: str
    codigo_cnae: Optional[str]
    prestador: Entidade
    tomador: Entidade
    valores: Valores
    optante_simples: bool = False
    regime_especial: Optional[str] = None
    avisos: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def variante(texto: str) -> Optional[int]:
    """Variante (1 ou 2) do template de Saubara, ou None se não for Saubara.

    Gate ESTREITO por 3 âncoras do documento de Saubara, todas exigidas (a
    palavra "Saubara" solta é marca compartilhada com prestadores/tomadores de
    outras cidades e NUNCA basta):
      1. o cabeçalho em linhas PRÓPRIAS - "ESTADO DA BAHIA" e, logo abaixo,
         "MUNICIPIO DE SAUBARA" - nos primeiros caracteres do texto (o nome
         do município no meio de uma frase ou de um endereço não é cabeçalho);
      2. a identidade da prefeitura: o CNPJ dela (13.040.233/0001-60) OU uma
         linha "Secretaria Municipal de Administração...";
      3. o título "Nota Fiscal Eletrônica de Serviços" em linha própria.
    A variante vem do rótulo de bloco exclusivo de cada template. Cabeçalho
    de Saubara sem nenhum dos dois blocos (template novo) devolve None: um
    "Layout não reconhecido" ruidoso é preferível a ler campos pelo template
    errado."""
    if not texto:
        return None
    cabecalho = texto.lstrip()[:_JANELA_CABECALHO]
    if not re.search(r'(?im)^[ \t]*ESTADO\s+DA\s+BAHIA[ \t]*\n+[ \t]*MUNIC[ÍI]PIO\s+DE\s+SAUBARA[ \t]*$', cabecalho):
        return None
    if not (re.search(r'13\.?040\.?233\s*/?\s*0001-?60', texto)
            or re.search(r'(?im)^[ \t]*Secretaria\s+Municipal\s+de\s+Administra', texto)):
        return None
    if not re.search(r'(?im)^[ \t]*Nota\s+Fiscal\s+Eletr[ôo]nica\s+de\s+Servi[çc]os\b', texto):
        return None
    if re.search(r'DADOS\s+DO\s+EMITENTE', texto, re.IGNORECASE):
        return VARIANTE_1
    if re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]OS', texto, re.IGNORECASE):
        return VARIANTE_2
    return None


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _sem_acento(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _colapsa(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def _valor_br(s: str) -> float:
    """"1.600,00" -> 1600.0; "48,00" -> 48.0."""
    return float(s.replace('.', '').replace(',', '.'))


def _pct(s: str) -> float:
    """Percentual impresso ("3", "2,00", "3,5", "3.5") -> número (3.0, 2.0, 3.5, 3.5)."""
    s = s.strip()
    return _valor_br(s) if ',' in s else float(s)


_NUM_MONETARIO = r'\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}'

# Número e código de verificação: o valor tem de ocupar a linha INTEIRA logo
# abaixo do rótulo. Rótulo com o campo em branco seguido de outra linha de
# texto ("Código de Verificação:" + "Nota Fiscal Eletrônica de Serviços") não
# pode render "Nota" como código.
_RE_NUMERO = re.compile(r'N[ÚU]MERO\s+DA\s+NOTA[ \t]*\n+[ \t]*(\d{1,15})[ \t]*(?:\n|$)', re.IGNORECASE)
_RE_CODIGO_VERIFICACAO = re.compile(
    r'C[ÓO]DIGO\s+DE\s+VERIFICA[ÇC][ÃA]O[ \t]*:?[ \t]*\n+[ \t]*([A-Za-z0-9]{4,20})[ \t]*(?:\n|$)', re.IGNORECASE)


def _rotulo_valor(t: str, rotulo: str, valor: str = _NUM_MONETARIO) -> Optional[str]:
    """Valor na linha SEGUINTE ao rótulo (com ou sem ":"), None se ausente.

    A exigência de que o valor comece logo após a quebra de linha evita
    capturar o rótulo vizinho quando o campo veio em branco."""
    m = re.search(rotulo + r'\s*:?\s*\n+\s*(' + valor + r')\s*(?:\n|$)', t, re.IGNORECASE)
    return m.group(1) if m else None


def _uf_de(estado: str) -> str:
    est = _sem_acento(_colapsa(estado)).upper()
    if len(est) == 2 and est.isalpha():
        return est
    return _UF_POR_NOME.get(est, '')


def _telefone(ddd: str, numero: str) -> Optional[str]:
    """DDD + número impressos em 2 células ("071" "981235905") -> 11 dígitos.

    O zero à esquerda do DDD ("071") é prefixo de discagem, não parte do
    número; fora disso o valor só é aceito se tiver 10/11 dígitos."""
    digitos = re.sub(r'\D', '', (ddd or '') + (numero or ''))
    if len(digitos) == 12 and digitos.startswith('0'):
        digitos = digitos[1:]
    return digitos if len(digitos) in (10, 11) else None


_NUM_ENDERECO = r'S\s*/?\s*N|\d+[A-Za-z]?(?:-[A-Za-z0-9]+)?'


def separar_endereco(raw: str) -> Tuple[str, str, Optional[str]]:
    """Divide a linha livre de endereço em (logradouro, número, complemento).

    Formatos reais: "RUA DA PAZ  33,  ENTIDADE RELIGIOSA" (número colado ao
    logradouro, complemento depois da vírgula), "RUA Território do Amapá, 146"
    e "RUA SANTO  ANTONIO , 14-A" (vírgula antes do número). Sem número
    legível, o número vira "S/N" e o texto inteiro fica no logradouro."""
    norm = _colapsa(raw).replace(' ,', ',').strip(' ,')
    if not norm:
        return 'Não informado', 'S/N', None
    partes = [p.strip() for p in norm.split(',') if p.strip()]
    primeira = partes[0]
    resto = partes[1:]
    if resto:
        m = re.match(r'^(' + _NUM_ENDERECO + r')\b\s*(.*)$', resto[0], re.IGNORECASE)
        if m:
            comp = ', '.join(([m.group(2)] if m.group(2) else []) + resto[1:])
            return primeira, re.sub(r'\s+', '', m.group(1)).upper(), comp or None
    m = re.match(r'^(.+?)\s+(' + _NUM_ENDERECO + r')$', primeira, re.IGNORECASE)
    if m:
        return m.group(1).strip(), re.sub(r'\s+', '', m.group(2)).upper(), ', '.join(resto) or None
    return primeira, 'S/N', ', '.join(resto) or None


def _montar_entidade(papel: str, *, razao: Optional[str], doc_raw: Optional[str],
                     endereco_raw: Optional[str], bairro: Optional[str],
                     municipio: Optional[str], uf: Optional[str], cep: Optional[str],
                     im: Optional[str], email: Optional[str], telefone: Optional[str],
                     cod_ibge_impresso: Optional[str], resolver,
                     validar_doc: Callable[[str], bool], avisos: List[str]) -> Entidade:
    """Monta a `Entidade` do prestador/tomador, com sentinela + aviso para
    tudo que a nota não entregou de forma confiável."""
    rotulo = 'prestador' if papel == 'prestador' else 'tomador'
    razao = _colapsa(razao or '')
    if not razao:
        razao = 'Prestador Não Identificado' if papel == 'prestador' else 'Tomador Não Identificado'
        avisos.append(f"Razão social do {rotulo} não encontrada - conferir na nota")

    doc = re.sub(r'\D', '', doc_raw or '')
    if len(doc) not in (11, 14):
        if doc:
            avisos.append(f"CNPJ/CPF do {rotulo} ({doc_raw.strip()}) com tamanho inválido - "
                          "mantido como sentinela; conferir na nota")
        doc = _SENTINELA_DOC
    elif not validar_doc(doc):
        avisos.append(f"CNPJ/CPF do {rotulo} ({doc}) impresso na nota não passa na validação "
                      "do dígito verificador - mantido como impresso; conferir na nota")

    logradouro, numero, complemento = separar_endereco(endereco_raw or '')
    municipio = _colapsa(municipio or '')
    uf = (uf or '').strip().upper()

    cod_mun = ''
    if cod_ibge_impresso and re.fullmatch(r'\d{7}', cod_ibge_impresso) \
            and cod_ibge_impresso.startswith(resolver.UF_PREFIXES.get(uf, '\0')):
        cod_mun = cod_ibge_impresso
    elif municipio:
        cod_mun = resolver.extract_and_validate(municipio, uf or UF_SAUBARA, city_hint=municipio)

    cep_d = re.sub(r'\D', '', cep or '')
    if len(cep_d) != 8:
        cep_d = '00000000'

    return Entidade(
        cnpj_cpf=doc,
        razao_social=razao,
        inscricao_municipal=(im or '').strip() or None,
        email=(email or '').strip() or None,
        telefone=telefone,
        endereco=Endereco(
            logradouro=logradouro,
            numero=numero,
            complemento=complemento,
            bairro=_colapsa(bairro or '') or 'Não informado',
            codigo_municipio=cod_mun,
            municipio=municipio,
            uf=uf,
            cep=cep_d,
        ),
    )


def _checar_valores(v: Valores, avisos: List[str]) -> None:
    """Coerência aritmética dos valores IMPRESSOS: divergência vira aviso,
    nunca arredondamento silencioso nem correção do número da nota."""
    tol = 0.011
    esperado_base = round(v.valor_servicos - v.valor_deducoes, 2)
    if abs(v.base_calculo - esperado_base) > tol:
        avisos.append(f"Base de cálculo impressa ({v.base_calculo:.2f}) diverge de Valor dos serviços - "
                      f"Deduções ({esperado_base:.2f}) - conferir na nota")
    esperado_iss = round(v.base_calculo * v.aliquota, 2)
    if abs(v.valor_iss - esperado_iss) > tol:
        avisos.append(f"ISS impresso ({v.valor_iss:.2f}) diverge de Base x Alíquota "
                      f"({esperado_iss:.2f}) - conferir na nota")
    retencoes = (v.valor_ir + v.valor_inss + v.valor_pis + v.valor_cofins + v.valor_csll
                 + v.outras_retencoes + (v.valor_iss if v.iss_retido else 0.0))
    esperado_liq = round(v.valor_servicos - retencoes, 2)
    if abs(v.valor_liquido_nfse - esperado_liq) > tol:
        avisos.append(f"Valor líquido impresso ({v.valor_liquido_nfse:.2f}) diverge de Valor dos serviços - "
                      f"retenções ({esperado_liq:.2f}) - conferir na nota")


def _item_lc116(codigo: Optional[str], avisos: List[str]) -> str:
    """Item da lista de serviço em 4 dígitos. Código que não existe na LC 116
    (ex.: "99.99 Outros Serviços", código municipal genérico) vira "0000", a
    convenção do projeto para "sem item LC 116 válido" (mesmo tratamento do
    "9901" de Camaçari/SISLOC), com aviso citando o código impresso."""
    if codigo:
        nn, mm = codigo.split('.')
        if 1 <= int(nn) <= 40:
            return nn.zfill(2) + mm
        avisos.append(f"Item de serviço impresso ({codigo}) não existe na lista da LC 116/2003 - "
                      "mantido como \"0000\" (sem item válido); classificar o serviço manualmente")
        return '0000'
    avisos.append("Item da lista de serviço não encontrado - mantido como \"0000\"; "
                  "classificar o serviço manualmente")
    return '0000'


def _data(texto: Optional[str], hora: Optional[str] = None) -> Optional[datetime]:
    if not texto:
        return None
    try:
        dia, mes, ano = texto.split('/')
        h = m = s = 0
        if hora:
            partes = hora.split(':')
            h, m = int(partes[0]), int(partes[1])
            s = int(partes[2]) if len(partes) > 2 else 0
        return datetime(int(ano), int(mes), int(dia), h, m, s)
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Variante 1 - "DADOS DO EMITENTE" / "DADOS DO DESTINATÁRIO"
# ---------------------------------------------------------------------------

_ROTULOS_V1 = frozenset({
    'nome', 'endereco', 'natureza da operacao', 'bairro', 'municipio', 'estado',
    'cnpj/cpf', 'rg', 'data emissao', 'dados do emitente', 'dados do destinatario',
    'itens dos servicos', 'cod', 'descricao', 'un', 'qtd', 'valor', 'valor total',
})


def _rotulo_v1(linha: str) -> Optional[str]:
    chave = _sem_acento(_colapsa(linha)).lower().rstrip(':').strip()
    chave = re.sub(r'\s*/\s*', '/', chave)
    return chave if chave in _ROTULOS_V1 else None


def _ocorrencias_v1(t: str) -> Dict[str, List[str]]:
    """Valor de cada rótulo por ordem de ocorrência: o valor é a linha
    seguinte não vazia, se ela própria não for outro rótulo (campo em branco
    fica ""). A 1ª ocorrência é do emitente, a 2ª do destinatário."""
    m_ini = re.search(r'DADOS\s+DO\s+EMITENTE', t, re.IGNORECASE)
    m_fim = re.search(r'Valor\s+Total\s+da\s+Nota', t, re.IGNORECASE)
    ini = m_ini.end() if m_ini else 0
    fim = m_fim.start() if m_fim and m_fim.start() > ini else len(t)
    linhas = [ln.strip() for ln in t[ini:fim].split('\n') if ln.strip()]
    occ: Dict[str, List[str]] = {}
    for i, linha in enumerate(linhas):
        rot = _rotulo_v1(linha)
        if rot is None or rot in ('dados do emitente', 'dados do destinatario', 'itens dos servicos'):
            continue
        prox = linhas[i + 1] if i + 1 < len(linhas) else ''
        valor = '' if (not prox or _rotulo_v1(prox)) else prox
        occ.setdefault(rot, []).append(valor)
    return occ


def _parse_v1(t: str, resolver, validar_doc, avisos: List[str]) -> NotaSaubara:
    occ = _ocorrencias_v1(t)

    def campo(rot: str, idx: int) -> Optional[str]:
        lst = occ.get(rot, [])
        return lst[idx] if idx < len(lst) else None

    for rot in ('nome', 'endereco', 'municipio', 'cnpj/cpf', 'bairro', 'estado'):
        if len(occ.get(rot, [])) < 2:
            avisos.append(
                f"Rótulo \"{rot}\" encontrado {len(occ.get(rot, []))}x (esperado 2: emitente e "
                "destinatário) - ordem de leitura do PDF inesperada; conferir prestador e tomador na nota")

    prestador = _montar_entidade(
        'prestador', razao=campo('nome', 0), doc_raw=campo('cnpj/cpf', 0),
        endereco_raw=campo('endereco', 0), bairro=campo('bairro', 0),
        municipio=campo('municipio', 0), uf=_uf_de(campo('estado', 0) or ''), cep=None,
        im=None, email=None, telefone=None, cod_ibge_impresso=None,
        resolver=resolver, validar_doc=validar_doc, avisos=avisos)
    tomador = _montar_entidade(
        'tomador', razao=campo('nome', 1), doc_raw=campo('cnpj/cpf', 1),
        endereco_raw=campo('endereco', 1), bairro=campo('bairro', 1),
        municipio=campo('municipio', 1), uf=_uf_de(campo('estado', 1) or ''), cep=None,
        im=None, email=None, telefone=None, cod_ibge_impresso=None,
        resolver=resolver, validar_doc=validar_doc, avisos=avisos)
    avisos.append("CEP do prestador e do tomador não são impressos neste template da NFS-e de "
                  "Saubara - mantidos zerados por não haver valor real para extrair")

    m_num = _RE_NUMERO.search(t)
    m_cod = _RE_CODIGO_VERIFICACAO.search(t)
    m_data = re.search(r'Data\s+Emiss[ãa]o\s*\n+\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)

    # Item(ns) da lista: rótulo "Cod" e, na linha seguinte, "99.99 Outros
    # Serviços" (código e descrição na mesma linha).
    # Região só entre o rótulo "Cod" e "Valor Total da Nota": a discriminação
    # livre, depois dela, pode ter linhas começando por "NN.NN ...".
    m_cod_rot = re.search(r'(?m)^\s*Cod\s*$', t)
    m_tot = re.search(r'Valor\s+Total\s+da\s+Nota', t, re.IGNORECASE)
    regiao_itens = t[m_cod_rot.end():m_tot.start()] if (
        m_cod_rot and m_tot and m_tot.start() > m_cod_rot.end()) else ''
    itens = re.findall(r'(?m)^\s*(\d{1,2}\.\d{2})\s+[A-Za-zÀ-ú]', regiao_itens)
    codigos_distintos = list(dict.fromkeys(itens))
    if len(codigos_distintos) > 1:
        avisos.append("Nota com mais de um item de serviço de códigos diferentes ("
                      + ', '.join(codigos_distintos) + ") - usado o primeiro; conferir classificação")
    codigo_servico = _item_lc116(codigos_distintos[0] if codigos_distintos else None, avisos)

    discriminacao = ''
    m_disc = re.search(
        r'Valor\s+L[íi]quido\s+da\s+Nota\s*\(R\$\)\s*:?\s*\n+\s*[\d.,]+\s*\n+(.*?)(?:\n\s*Link3\s+Tecnologia|\Z)',
        t, re.IGNORECASE | re.DOTALL)
    if m_disc:
        discriminacao = _colapsa(m_disc.group(1))
    if not discriminacao:
        m_desc = re.search(r'(?m)^\s*\d{1,2}\.\d{2}\s+(.+)$', regiao_itens)
        discriminacao = _colapsa(m_desc.group(1)) if m_desc else ''
        avisos.append("Discriminação do serviço não encontrada - usada a descrição do item "
                      "da lista; conferir na nota")

    valores = _valores_v1(t, avisos)

    return NotaSaubara(
        variante=VARIANTE_1,
        numero=m_num.group(1) if m_num else _SENTINELA_NUMERO,
        codigo_verificacao=m_cod.group(1) if m_cod else _SENTINELA_CODIGO_VERIFICACAO,
        data_emissao=_data(m_data.group(1)) if m_data else None,
        discriminacao=discriminacao,
        codigo_servico=codigo_servico,
        codigo_cnae=None,
        prestador=prestador,
        tomador=tomador,
        valores=valores,
        avisos=avisos,
    )


def _valores_v1(t: str, avisos: List[str]) -> Valores:
    ausentes: List[str] = []

    def num(rotulo: str, nome: str) -> float:
        bruto = _rotulo_valor(t, rotulo)
        if bruto is None:
            ausentes.append(nome)
            return 0.0
        return _valor_br(bruto)

    total = num(r'Valor\s+Total\s+da\s+Nota\s*\(R\$\)', 'Valor Total da Nota')
    base = num(r'Base\s+de\s+C[áa]lculo\s+da\s+Nota', 'Base de Cálculo')
    deducoes = num(r'Dedu[çc][õo]es', 'Deduções')
    iss = num(r'valor\s+ISS', 'valor ISS')
    irrf = num(r'Valor\s+IRRF', 'IRRF')
    inss = num(r'Valor\s+INSS', 'INSS')
    liquido_bruto = _rotulo_valor(t, r'Valor\s+L[íi]quido\s+da\s+Nota\s*\(R\$\)')
    m_ret = re.search(r'ISS\s+Retido\s*:?\s*\n+\s*(Sim|N[ãa]o)\b', t, re.IGNORECASE)
    m_aliq = re.search(r'Aliq\.?\s*Iss\s*:?\s*\n+\s*(\d+(?:[.,]\d+)?)\s*(?:\n+\s*)?%', t, re.IGNORECASE)

    if m_ret is None:
        ausentes.append('ISS Retido')
    if m_aliq is None:
        ausentes.append('Aliq. Iss')
    if liquido_bruto is None:
        ausentes.append('Valor Líquido da Nota')
    if ausentes:
        avisos.append("Campos da grade de valores não encontrados (mantidos zerados/\"Não\"): "
                      + ', '.join(ausentes) + " - conferir na nota")

    iss_retido = bool(m_ret and m_ret.group(1).lower().startswith('s'))
    aliquota = _pct(m_aliq.group(1)) / 100 if m_aliq else 0.0
    liquido = _valor_br(liquido_bruto) if liquido_bruto is not None else total

    v = Valores(
        valor_servicos=total,
        valor_deducoes=deducoes,
        valor_inss=inss,
        valor_ir=irrf,
        iss_retido=iss_retido,
        valor_iss=iss,
        valor_iss_retido=iss if iss_retido else 0.0,
        base_calculo=base,
        aliquota=aliquota,
        valor_liquido_nfse=liquido,
    )
    if not ausentes:
        _checar_valores(v, avisos)
    return v


# ---------------------------------------------------------------------------
# Variante 2 - "PRESTADOR DE SERVIÇOS" / "TOMADOR DE SERVIÇOS"
# ---------------------------------------------------------------------------

_ROTULOS_V2 = frozenset({
    'NOME/RAZAO SOCIAL', 'NOME FANTASIA', 'CNPJ/CPF', 'ENDERECO', 'COMPLEMENTO', 'E-MAIL',
    'TELEFONE', 'UF', 'CIDADE -', 'CIDADE', 'BAIRRO', 'CEP', 'INSC. ESTADUAL',
    'INSCRICAO MUNICIPAL', 'PRESTADOR DE SERVICOS', 'TOMADOR DE SERVICOS',
})


def _eh_rotulo_v2(linha: str) -> bool:
    chave = _sem_acento(_colapsa(linha)).upper().rstrip(':').strip()
    return re.sub(r'\s*/\s*', '/', chave) in _ROTULOS_V2


def _ocorrencias_campo_v2(t: str, rotulo: str) -> List[Optional[str]]:
    """Valor (linha seguinte) de cada ocorrência de um rótulo, em ordem; None
    quando o campo está em branco, isto é, a linha seguinte é outro rótulo."""
    saida: List[Optional[str]] = []
    for m in re.finditer(rotulo + r'[ \t]*\n+[ \t]*([^\n]*)', t):
        v = m.group(1).strip()
        saida.append(None if (not v or _eh_rotulo_v2(v)) else v)
    return saida


def _parse_v2(t: str, resolver, validar_doc, avisos: List[str]) -> NotaSaubara:
    # Região dos blocos de entidade: do "PRESTADOR DE SERVIÇOS" até a
    # discriminação. Fora dela há outros "CNPJ/CPF"/"UF"... só se a nota mudar.
    m_ini = re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
    m_fim = re.search(r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS', t, re.IGNORECASE)
    ini = m_ini.end() if m_ini else 0
    fim = m_fim.start() if m_fim and m_fim.start() > ini else len(t)
    r = t[ini:fim]

    def pares(rotulo: str) -> List[Optional[str]]:
        return _ocorrencias_campo_v2(r, rotulo)

    nomes = pares(r'NOME\s*/\s*RAZ[ÃA]O\s+SOCIAL')
    docs = pares(r'CNPJ\s*/\s*CPF')
    enderecos = pares(r'ENDERE[ÇC]O')
    emails = pares(r'E-?MAIL')
    ufs = pares(r'\bUF')
    bairros = pares(r'BAIRRO')
    ceps = pares(r'\bCEP')
    cidades = [(m.group(1), m.group(2).strip()) for m in
               re.finditer(r'CIDADE\s*-\s*(\d{7})\s+([^\n]+)', r)]
    telefones: List[Optional[str]] = []
    for m_tel in re.finditer(r'TELEFONE[ \t]*\n+', r):
        resto = r[m_tel.end():]
        mt = re.match(r'\s*(\d{2,3})\s+(\d{7,9})\b', resto) or re.match(r'\s*(\d{10,12})()\b', resto)
        telefones.append(_telefone(mt.group(1), mt.group(2)) if mt else None)
    m_im = re.search(r'INSCRI[ÇC][ÃA]O\s+MUNICIPAL[ \t]*\n+[ \t]*(\d+)[ \t]*(?:\n|$)', r, re.IGNORECASE)

    contagens = {'NOME/RAZÃO SOCIAL': nomes, 'CNPJ/CPF': docs, 'ENDEREÇO': enderecos,
                 'UF': ufs, 'BAIRRO': bairros, 'CEP': ceps, 'CIDADE': cidades}
    for nome, lst in contagens.items():
        if len(lst) < 2:
            avisos.append(
                f"Rótulo \"{nome}\" encontrado {len(lst)}x (esperado 2: prestador e tomador) - "
                "ordem de leitura do PDF inesperada; conferir prestador e tomador na nota")

    def pega(lst, idx):
        return lst[idx] if idx < len(lst) else None

    def entidade(papel: str, idx: int, im: Optional[str]) -> Entidade:
        cidade = pega(cidades, idx)
        return _montar_entidade(
            papel, razao=pega(nomes, idx), doc_raw=pega(docs, idx),
            endereco_raw=pega(enderecos, idx), bairro=pega(bairros, idx),
            municipio=cidade[1] if cidade else None, uf=pega(ufs, idx), cep=pega(ceps, idx),
            im=im, email=pega(emails, idx), telefone=pega(telefones, idx),
            cod_ibge_impresso=cidade[0] if cidade else None,
            resolver=resolver, validar_doc=validar_doc, avisos=avisos)

    prestador = entidade('prestador', 0, m_im.group(1) if m_im else None)
    tomador = entidade('tomador', 1, None)

    # Auto-verificação da ordem de leitura: o rodapé repete a razão social do
    # prestador ("Operador da Empresa: ..."); divergência denuncia prestador e
    # tomador trocados pela ordem do texto.
    m_op = re.search(r'Operador\s+da\s+Empresa\s*:\s*([^\n]+)', t, re.IGNORECASE)
    if m_op and _sem_acento(_colapsa(m_op.group(1))).upper() != _sem_acento(prestador.razao_social).upper():
        avisos.append(f"Razão social do prestador lida ({prestador.razao_social}) difere do rodapé "
                      f"\"Operador da Empresa\" ({_colapsa(m_op.group(1))}) - possível inversão "
                      "prestador/tomador pela ordem de leitura do PDF; conferir na nota")

    m_gerador = re.search(r'COD\.?\s+MUNICIPIO\s+GERADOR\s*\n+\s*(\d{7})', t, re.IGNORECASE)
    if m_gerador and m_gerador.group(1) != COD_IBGE_SAUBARA:
        avisos.append(f"Código do município gerador impresso ({m_gerador.group(1)}) difere do de "
                      f"Saubara ({COD_IBGE_SAUBARA}) - conferir na nota")
    if prestador.endereco.codigo_municipio and prestador.endereco.codigo_municipio != COD_IBGE_SAUBARA:
        avisos.append(f"Prestador sediado fora de Saubara ({prestador.endereco.municipio}/"
                      f"{prestador.endereco.uf}): OrgaoGerador/MunicipioIncidencia do XML seguem o "
                      "município do prestador - conferir na nota")
    m_trib = re.search(r'Tributa[çc][ãa]o\s*:\s*\n+\s*Iss\s+Devido\s+n[oa]\s+Munic[ií]pio\s+de\s+([^\n]+)',
                       t, re.IGNORECASE)
    if m_trib and _sem_acento(_colapsa(m_trib.group(1))).upper() != 'SAUBARA':
        avisos.append(f"ISS devido em outro município ({_colapsa(m_trib.group(1))}) - a incidência "
                      "do XML NÃO foi alterada; conferir na nota")

    m_num = _RE_NUMERO.search(t)
    m_cod = _RE_CODIGO_VERIFICACAO.search(t)
    m_data = re.search(
        r'DATA\s+E\s+HORA\s+DA\s+EMISS[ÃA]O\s*\n+\s*(\d{2}/\d{2}/\d{4})(?:[ \t]+(\d{2}:\d{2}(?::\d{2})?))?',
        t, re.IGNORECASE)

    m_item = re.search(r'LC\s*116/2003\s*\n+\s*(\d{1,2})\.(\d{2})\b', t, re.IGNORECASE)
    codigo_servico = _item_lc116(f"{m_item.group(1)}.{m_item.group(2)}" if m_item else None, avisos)
    m_cnae = re.search(r'C[ÓO]DIGO\s+CNAE\s*\n+\s*(\d{7})\b', t, re.IGNORECASE)

    m_disc = re.search(r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS\s*\n+(.*?)\n\s*C[ÓO]DIGO\s+CNAE',
                       t, re.IGNORECASE | re.DOTALL)
    discriminacao = _colapsa(m_disc.group(1)) if m_disc else ''
    if not discriminacao:
        avisos.append("Discriminação do serviço não encontrada - conferir na nota")

    regime = None
    m_reg = re.search(r'Regime\s+Tributa[çc][ãa]o\s+Especial\s*\n+\s*([^\n]+)', t, re.IGNORECASE)
    if m_reg:
        for padrao, codigo in _REGIME_ESPECIAL:
            if re.search(padrao, m_reg.group(1), re.IGNORECASE):
                regime = codigo
                break
        if regime is None:
            avisos.append(f"Regime de tributação especial impresso (\"{_colapsa(m_reg.group(1))}\") "
                          "não reconhecido - RegimeEspecialTributacao do XML não preenchido")
    optante = bool(re.search(r'EMPRESA\s+OPTANTE\s+DO\s+SIMPLES', t, re.IGNORECASE))

    return NotaSaubara(
        variante=VARIANTE_2,
        numero=m_num.group(1) if m_num else _SENTINELA_NUMERO,
        codigo_verificacao=m_cod.group(1) if m_cod else _SENTINELA_CODIGO_VERIFICACAO,
        data_emissao=_data(m_data.group(1), m_data.group(2)) if m_data else None,
        discriminacao=discriminacao,
        codigo_servico=codigo_servico,
        codigo_cnae=m_cnae.group(1) if m_cnae else None,
        prestador=prestador,
        tomador=tomador,
        valores=_valores_v2(t, avisos),
        optante_simples=optante,
        regime_especial=regime,
        avisos=avisos,
    )


def _valores_v2(t: str, avisos: List[str]) -> Valores:
    """Grade de valores da variante 2.

    O texto traz o total ("VALOR TOTAL DO(S) SERVIÇO(S) (R$)\\n\\n120,00") e
    depois os 12 rótulos (PIS, COFINS, INSS, IR, CSLL / Deduções, Base,
    Alíquota, ISS, Retenção ISS, Outras Retenções, Valor Líquido) e os 12
    valores, cada fluxo na ordem do template. A atribuição é POSICIONAL e só
    é aceita quando os 12 rótulos aparecem na ordem esperada E há exatamente
    12 valores; a coerência aritmética (base = total - deduções, ISS = base x
    alíquota, líquido = total - retenções) é então conferida contra o
    impresso. Estrutura diferente do esperado => só o total é aproveitado e o
    resto fica zerado + aviso."""
    m_total_titulo = re.search(r'VALOR\s+TOTAL\s+DO\(S\)\s+SERVI[ÇC]O\(S\)\s*\(R\$\)', t, re.IGNORECASE)
    m_fim = re.search(r'INFORMA[ÇC][ÕO]ES\s+FISCAIS|Tributa[çc][ãa]o\s*:', t, re.IGNORECASE)
    regiao = ''
    if m_total_titulo:
        fim = m_fim.start() if m_fim and m_fim.start() > m_total_titulo.end() else len(t)
        regiao = t[m_total_titulo.end():fim]
    linhas = [ln.strip() for ln in regiao.split('\n') if ln.strip()]

    padrao_num = re.compile(r'^\d[\d.]*(?:,\d+)?$')
    padrao_sn = re.compile(r'^(Sim|N[ãa]o)$', re.IGNORECASE)
    numeros = [ln for ln in linhas if padrao_num.match(ln) or padrao_sn.match(ln)]
    rotulos_linhas = [ln for ln in linhas if not (padrao_num.match(ln) or padrao_sn.match(ln))]

    total = _valor_br(numeros[0]) if numeros and padrao_num.match(numeros[0]) else 0.0
    grade = numeros[1:]

    # Rótulos presentes, em ordem, exatamente como o template (cada um numa
    # linha própria, com o "(R$)"/"(%)" opcional).
    ordem_ok = False
    if len(rotulos_linhas) == len(_ROTULOS_V2_GRADE):
        ordem_ok = all(
            re.fullmatch(rot + r'\s*(?:\((?:R\$|%)\))?', ln, re.IGNORECASE)
            for rot, ln in zip(_ROTULOS_V2_GRADE, rotulos_linhas))

    if not (ordem_ok and len(grade) == len(_ROTULOS_V2_GRADE)
            and padrao_sn.match(grade[9]) and all(padrao_num.match(g) for i, g in enumerate(grade) if i != 9)):
        avisos.append("Grade de tributos (PIS/COFINS/INSS/IR/CSLL, deduções, base, alíquota, ISS, "
                      "retenção, líquido) não pôde ser lida com segurança - só o valor total foi "
                      "aproveitado; demais valores mantidos zerados, conferir na nota")
        return Valores(valor_servicos=total, base_calculo=total, aliquota=0.0, valor_liquido_nfse=total)

    pis, cofins, inss, ir, csll, deducoes, base, aliq, iss, ret, outras, liquido = grade
    iss_retido = ret.lower().startswith('s')
    v = Valores(
        valor_servicos=total,
        valor_deducoes=_valor_br(deducoes),
        valor_pis=_valor_br(pis),
        valor_cofins=_valor_br(cofins),
        valor_inss=_valor_br(inss),
        valor_ir=_valor_br(ir),
        valor_csll=_valor_br(csll),
        iss_retido=iss_retido,
        valor_iss=_valor_br(iss),
        valor_iss_retido=_valor_br(iss) if iss_retido else 0.0,
        outras_retencoes=_valor_br(outras),
        base_calculo=_valor_br(base),
        aliquota=_valor_br(aliq) / 100,
        valor_liquido_nfse=_valor_br(liquido),
    )
    _checar_valores(v, avisos)
    return v


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def extrair(texto: str, var: int, resolver, validar_doc: Callable[[str], bool]) -> NotaSaubara:
    """Extrai todos os campos de uma nota de Saubara da variante `var`.

    `resolver` é o `IBGEResolver` compartilhado do extrator (para o aviso de
    município fora da tabela continuar funcionando) e `validar_doc` valida o
    dígito verificador de CNPJ/CPF."""
    avisos: List[str] = []
    if var == VARIANTE_1:
        return _parse_v1(texto, resolver, validar_doc, avisos)
    return _parse_v2(texto, resolver, validar_doc, avisos)
