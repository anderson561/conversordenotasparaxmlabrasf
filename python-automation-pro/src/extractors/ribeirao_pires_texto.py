"""Helpers de texto da NFS-e de Ribeirão Pires/SP (`LAYOUT_RIBEIRAO_PIRES`).

Modelo Ginfes com reforma tributária (mesma família visual do
`LAYOUT_SANTOS`): seções "Prestador de Serviço", "Tomador de Serviço",
"Atividade Econômica", "Discriminação do Serviço", "Tributos Federais (R$)",
"Identificação Prestação de Serviços" e "Detalhamento de Valores (R$)" (com
IBS/CBS). Achado real 2026-11-19: notas nº 20831 e 22716, AMBAR INOVACOES SPE
LTDA -> STAUMMAQ, R$ 1.000,00, PDF DIGITAL.

O `extract_text()` padrão do pdfminer despeja os rótulos das duas grades de
baixo e só DEPOIS os valores, e um campo em branco ("Outras Retenções") some
da lista sem deixar marca — mapear por posição desloca todos os valores
seguintes (Deduções viraria a Base de Cálculo). Por isso tudo aqui é lido do
texto RECONSTRUÍDO POR COORDENADA (`_reconstruir_texto_por_coordenadas`), em
que cada linha visual traz "rótulo valor" lado a lado; um campo em branco
fica com o rótulo sem valor, nunca empresta o valor do vizinho.

Função pura sobre texto (testável sem PDF). Onde a leitura não fecha, devolve
None no campo e registra aviso em `avisos` — nunca fabrica valor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_MOEDA = r'\d{1,3}(?:\.\d{3})*,\d{2,4}'

# Rótulos das linhas de entidade. "Inscrição" e "Endereço" do PRESTADOR saem
# sem dois-pontos; os demais sempre com. Exigir ":" nos outros evita cortar
# um valor que contenha a palavra (ex.: logradouro "Rua do Bairro Alto").
_ROTULOS_ENTIDADE = re.compile(
    r'(?:(?<=\s)|^)(?:'
    r'(?P<cnpj>CPF/CNPJ)\s*:'
    r'|(?P<im>Inscri[çc][ãa]o(?:\s+Municipal)?)\s*:?'
    r'|(?P<nif>NIF)\s*:'
    r'|(?P<nome>Nome/Raz[ãa]o\s+Social)\s*:'
    r'|(?P<endereco>Endere[çc]o)\s*:?'
    r'|(?P<numero>N[úu]mero)\s*:'
    r'|(?P<complemento>Complemento)\s*:'
    r'|(?P<bairro>Bairro)\s*:'
    r'|(?P<cep>CEP)\s*:'
    r'|(?P<municipio>Munic[íi]pio)\s*:'
    r'|(?P<uf>UF)\s*:'
    r'|(?P<pais>Pa[íi]s)\s*:'
    r'|(?P<email>E-?mail)\s*:'
    r'|(?P<telefone>Telefone)\s*:'
    r')',
    re.IGNORECASE | re.MULTILINE)


@dataclass
class EntidadeRP:
    cnpj_cpf: str = ''
    inscricao_municipal: str = ''
    razao_social: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    municipio: str = ''
    uf: str = ''
    email: str = ''
    telefone: str = ''


@dataclass
class CamposRP:
    prestador: EntidadeRP
    tomador: EntidadeRP
    item_lc116: Optional[str] = None          # "1722"
    discriminacao: str = ''
    competencia: Optional[str] = None         # "10/2026"
    municipio_incidencia: Optional[str] = None
    uf_incidencia: Optional[str] = None
    simples_nacional: Optional[bool] = None
    iss_retido: Optional[bool] = None
    exigibilidade: Optional[str] = None       # "1"
    # Tributos Federais: {'PIS': (valor, tipo), 'COFINS': (valor, tipo),
    # 'INSS': valor, 'IR': valor, 'CSLL': valor}
    tributos_federais: Dict[str, object] = field(default_factory=dict)
    # Detalhamento de Valores: rótulo canônico -> float (ausente = em branco)
    valores: Dict[str, float] = field(default_factory=dict)
    avisos: List[str] = field(default_factory=list)


def eh_modelo_ginfes(texto: str) -> bool:
    """O texto (reconstruído por coordenada) é do modelo com as seções acima?"""
    return bool(
        re.search(r'Prestador\s+de\s+Servi[çc]o', texto, re.IGNORECASE)
        and re.search(r'Tomador\s+de\s+Servi[çc]o', texto, re.IGNORECASE)
        and re.search(r'Detalhamento\s+de\s+Valores', texto, re.IGNORECASE)
        and re.search(r'^\s*Valor\s+L[íi]quido\b', texto, re.IGNORECASE | re.MULTILINE))


def _num(s: str) -> float:
    return float(s.replace('.', '').replace(',', '.'))


def _ler_entidade(bloco: str) -> EntidadeRP:
    ent = EntidadeRP()
    for linha in bloco.splitlines():
        marcas = list(_ROTULOS_ENTIDADE.finditer(linha))
        for i, m in enumerate(marcas):
            fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(linha)
            valor = re.sub(r'\s+', ' ', linha[m.end():fim]).strip()
            chave = m.lastgroup
            if chave in ('nif', 'pais') or not valor:
                continue
            if chave == 'im':
                chave = 'inscricao_municipal'
            elif chave == 'nome':
                chave = 'razao_social'
            elif chave == 'endereco':
                chave = 'logradouro'
            elif chave == 'cnpj':
                chave = 'cnpj_cpf'
            if not getattr(ent, chave):
                setattr(ent, chave, valor)
    ent.cnpj_cpf = re.sub(r'\D', '', ent.cnpj_cpf)
    ent.cep = re.sub(r'\D', '', ent.cep)
    ent.uf = ent.uf.upper()[:2] if re.match(r'^[A-Za-z]{2}\b', ent.uf) else ''
    return ent


def _caixa(rotulo: str, texto: str) -> Optional[bool]:
    """Caixa "( ) Sim (X) Não" na MESMA linha do rótulo; None se ilegível
    ou marcada nas duas/nenhuma opção."""
    m = re.search(rotulo + r'\s*\(\s*(X?)\s*\)\s*Sim\s*\(\s*(X?)\s*\)\s*N[ãa]o',
                  texto, re.IGNORECASE)
    if not m or bool(m.group(1)) == bool(m.group(2)):
        return None
    return bool(m.group(1))


# Rótulos da grade "Detalhamento de Valores (R$)" — coluna DIREITA, então o
# valor (quando impresso) é o último token da linha.
_ROTULOS_VALORES = {
    'servico': r'Valor\s+do\s+Servi[çc]o',
    'desconto_incondicionado': r'Desconto\s+Incondicionado',
    'desconto_condicionado': r'Desconto\s+Condicionado',
    'retencoes_federais': r'Reten[çc][õo]es\s+Federais',
    'pis_cofins_apuracao_propria': r'PIS/COFINS\s*-\s*Apura[çc][ãa]o\s+Pr[óo]pria',
    'outras_retencoes': r'Outras\s+Reten[çc][õo]es',
    'deducoes': r'Dedu[çc][õo]es\s+Previstas\s+em\s+Lei',
    'base_calculo': r'Base\s+de\s+C[áa]lculo',
    'aliquota': r'Al[íi]quota',
    'issqn': r'ISSQN',
    'ibs': r'IBS',
    'cbs': r'CBS',
    'contribuicoes_sociais_retidas': r'Contribui[çc][õo]es\s+Sociais\s*-\s*Retidas',
    'liquido': r'Valor\s+L[íi]quido',
}


def ler_campos(texto: str) -> Optional[CamposRP]:
    """Lê os campos do modelo a partir do texto reconstruído por coordenada.
    None quando o texto não é deste modelo (o chamador mantém o caminho
    antigo do layout)."""
    if not texto or not eh_modelo_ginfes(texto):
        return None
    avisos: List[str] = []

    m_prest = re.search(r'^\s*Prestador\s+de\s+Servi[çc]o\s*$', texto, re.IGNORECASE | re.MULTILINE)
    m_tom = re.search(r'^\s*Tomador\s+de\s+Servi[çc]o\s*$', texto, re.IGNORECASE | re.MULTILINE)
    m_ativ = re.search(r'^\s*Atividade\s+Econ[ôo]mica\s*$', texto, re.IGNORECASE | re.MULTILINE)
    if not (m_prest and m_tom and m_ativ and m_prest.end() < m_tom.start() < m_ativ.start()):
        return None
    prestador = _ler_entidade(texto[m_prest.end():m_tom.start()])
    tomador = _ler_entidade(texto[m_tom.end():m_ativ.start()])

    campos = CamposRP(prestador=prestador, tomador=tomador, avisos=avisos)

    # Atividade Econômica: "17.22 / 8.1722 - Cobrança Em Geral." -> "1722".
    # O código após a barra é a atividade MUNICIPAL, não CNAE.
    m = re.search(r'Atividade\s+Econ[ôo]mica\s*\n\s*(\d{1,2})\.(\d{2})\s*/', texto, re.IGNORECASE)
    if m:
        campos.item_lc116 = m.group(1).zfill(2) + m.group(2)

    m = re.search(r'Discrimina[çc][ãa]o\s+do\s+Servi[çc]o\s*\n([\s\S]*?)\n\s*Tributos\s+Federais',
                  texto, re.IGNORECASE)
    if m:
        campos.discriminacao = re.sub(r'\s+', ' ', m.group(1)).strip()

    # Tributos Federais: linha de rótulos e, logo abaixo, a de valores
    # ("6,50 Apuração Própria 30,00 Apuração Própria 0,00 0,00 0,00 - ...").
    m = re.search(
        r'^\s*PIS\s+Tipo\s+PIS\s+COFINS\s+Tipo\s+COFINS\s+INSS\s+IR\s+CSLL\b[^\n]*\n'
        r'\s*(' + _MOEDA + r')\s+(.*?)\s+(' + _MOEDA + r')\s+(.*?)\s+'
        r'(' + _MOEDA + r')\s+(' + _MOEDA + r')\s+(' + _MOEDA + r')(?=\s|$)',
        texto, re.IGNORECASE | re.MULTILINE)
    if m:
        campos.tributos_federais = {
            'PIS': (_num(m.group(1)), m.group(2).strip()),
            'COFINS': (_num(m.group(3)), m.group(4).strip()),
            'INSS': _num(m.group(5)), 'IR': _num(m.group(6)), 'CSLL': _num(m.group(7)),
        }
    else:
        avisos.append("Grade \"Tributos Federais (R$)\" não lida - PIS/COFINS/INSS/IR/CSLL "
                      "mantidos zerados; confira na nota")

    m = re.search(r'Compet[êe]ncia\s+(\d{2}/\d{4})\b', texto, re.IGNORECASE)
    if m:
        campos.competencia = m.group(1)
    m = re.search(r'Mun[íi]c[íi]pio\s+Incid[êe]ncia\s+([A-Za-zÀ-ú][A-Za-zÀ-ú\s.\'-]*?)\s+-\s+([A-Z]{2})\b',
                  texto, re.IGNORECASE)
    if m:
        campos.municipio_incidencia = re.sub(r'\s+', ' ', m.group(1)).strip()
        campos.uf_incidencia = m.group(2).upper()
    m = re.search(r'Exigibilidade\s+ISSQN\s+(\d)\s*-', texto, re.IGNORECASE)
    if m:
        campos.exigibilidade = m.group(1)
    campos.simples_nacional = _caixa(r'Simples\s+Nacional', texto)
    campos.iss_retido = _caixa(r'ISSQN\s+a\s+Reter', texto)

    for chave, rotulo in _ROTULOS_VALORES.items():
        m = re.search(r'(?:^|\s)' + rotulo + r'[ \t]+(' + _MOEDA + r')[ \t]*$',
                      texto, re.IGNORECASE | re.MULTILINE)
        if m:
            campos.valores[chave] = _num(m.group(1))
    return campos
