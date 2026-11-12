"""NFS-e de Sao Paulo/SP escaneada: numero da nota pelo campo AUTOVERIFICAVEL.

A NFS-e paulistana imprime o "Identificador" (chave NFS-e Nacional de 50
digitos) no anexo "IMPOSTO E CONTRIBUICAO SOBRE BENS E SERVICOS (IBS E CBS)"
(pagina 2) e, em varias notas, tambem no cabecalho da pagina 1 ("Identificador
Nacional:"):

    cMun(7) | amb(1) | tpInsc(1) | CNPJ(14) | nNFSe(13) | AAMM(4) | cod+DV(10)

O ultimo digito e o DV modulo 11 (pesos 2..9 da direita para a esquerda) dos 49
anteriores - cobre os 13 digitos do numero da nota. Conferido contra 6 chaves
reais (todas com o DV certo e o nNFSe igual ao numero impresso). Por isso a
chave decodificada vence qualquer leitura por OCR da caixa "Numero da Nota",
que nestas fotos some ou vira a Inscricao Municipal do prestador.

Modulo puro (so `re`): nada aqui toca OCR nem imagem.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

COD_IBGE_SAO_PAULO = '3550308'

_RE_IDENTIFICADOR = re.compile(
    r'Identificador\s*(?:Nacional)?\s*:?\s*(\d(?:[ \t]?\d){49})(?!\d)', re.IGNORECASE)
_RE_CNPJ_PONTUADO = r'\d{2}\.?\d{3}\.?\d{3}\s*/\s*\d{4}\s*-?\s*\d{2}'


def cnpj_valido(doc: str) -> bool:
    d = re.sub(r'\D', '', doc or '')
    if len(d) != 14 or d == d[0] * 14:
        return False
    for i in (12, 13):
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if i == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        resto = sum(int(d[n]) * pesos[n] for n in range(i)) % 11
        dv = 0 if 11 - resto >= 10 else 11 - resto
        if dv != int(d[i]):
            return False
    return True


def dv_valido(chave: str) -> bool:
    """DV modulo 11 (pesos 2..9) do 50o digito sobre os 49 primeiros."""
    if len(chave) != 50 or not chave.isdigit():
        return False
    soma = sum(int(c) * (2 + i % 8) for i, c in enumerate(reversed(chave[:49])))
    dv = 0 if 11 - soma % 11 >= 10 else 11 - soma % 11
    return dv == int(chave[49])


def extrair_identificadores(texto: str) -> List[str]:
    """Chaves de 50 digitos que seguem o rotulo "Identificador[ Nacional]:"
    (tolera um espaco solto entre digitos, defeito comum do OCR)."""
    return [re.sub(r'\D', '', m.group(1)) for m in _RE_IDENTIFICADOR.finditer(texto or '')]


def eh_pagina_anexo_ibs_cbs(texto: str) -> bool:
    """Anexo IBS/CBS: tem o titulo "(IBS E CBS)" e NAO tem o bloco "PRESTADOR DE
    SERVICOS" de uma nota (a pagina de uma nota seguinte nunca e o anexo)."""
    return bool(re.search(r'IBS\s*E\s*CBS', texto or '', re.IGNORECASE)) and \
        not re.search(r'PRESTADOR\s*DE\s*SERVI', texto or '', re.IGNORECASE)


def cnpj_do_prestador(texto: str) -> Optional[str]:
    """1o CNPJ pontuado apos o cabecalho "PRESTADOR DE SERVICOS" (14 digitos)."""
    m = re.search(r'PRESTADOR\s*DE\s*SERVI[ÇC]OS.{0,300}?(' + _RE_CNPJ_PONTUADO + ')',
                  texto or '', re.IGNORECASE | re.DOTALL)
    return re.sub(r'\D', '', m.group(1)) if m else None


def aamm_da_emissao(texto: str) -> Optional[str]:
    """AAMM da 1a data+hora "dd/mm/aaaa hh:mm" (a do RPS nao tem hora)."""
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})\s+\d{2}:\d{2}', texto or '')
    return (m.group(3)[2:] + m.group(2)) if m else None


def decodificar(chave: str, cnpj_prestador: Optional[str],
                emissao_aamm: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Decodifica e VALIDA a chave. Exige: 50 digitos, cMun de Sao Paulo, DV
    modulo 11, CNPJ com checksum e IGUAL ao do prestador lido na pagina da nota
    (sem o CNPJ do prestador nao ha como saber que a chave e desta nota) e, se a
    emissao impressa for legivel, AAMM igual ao mes/ano dela."""
    chave = re.sub(r'\D', '', chave or '')
    if len(chave) != 50 or chave[:7] != COD_IBGE_SAO_PAULO or not dv_valido(chave):
        return None
    cnpj, nnfse, aamm = chave[9:23], chave[23:36], chave[36:40]
    if not cnpj_valido(cnpj) or not cnpj_prestador or cnpj != cnpj_prestador:
        return None
    if not 1 <= int(aamm[2:]) <= 12:
        return None
    if emissao_aamm and aamm != emissao_aamm:
        return None
    if not nnfse.strip('0'):
        return None
    return {'chave': chave, 'cnpj': cnpj, 'nnfse': nnfse, 'aamm': aamm}


def formatar_numero(nnfse: str) -> str:
    """Convencao do projeto para o numero da NFS-e de Sao Paulo: 8 digitos com
    zeros a esquerda, como a prefeitura imprime ("00028203")."""
    return str(int(nnfse)).zfill(8)


def valores_de_outros_campos(texto: str) -> Set[str]:
    """Digitos (sem zeros a esquerda) de valores que o PROPRIO documento rotula
    como outro campo - Inscricao Municipal, CPF/CNPJ, CEP. Um candidato a
    "numero da nota" igual a um deles e leitura da celula errada."""
    achados: Set[str] = set()
    padroes = (
        r'Inscri[çc][ãa]o\s+Municipal\s*:?[ \t]*([\d][\d.\-/ \t]*)',
        r'CPF\s*/\s*CNPJ\s*:?[ \t]*([\d][\d.\-/ \t]*)',
        r'\bCEP\s*:?[ \t]*([\d][\d.\-]*)',
    )
    for p in padroes:
        for m in re.finditer(p, texto or '', re.IGNORECASE):
            digitos = re.sub(r'\D', '', m.group(1))
            if len(digitos) >= 5:
                achados.add(digitos.lstrip('0'))
    return achados


# --- Codigo de verificacao: amarra o anexo IBS/CBS a SUA nota ---------------
#
# O anexo repete, logo abaixo do Identificador, a linha
# "CPF/CNPJ/NIF do Fornecedor | Numero da Nota | Codigo de Verificacao". A chave
# NAO carrega o codigo de verificacao, e duas notas do mesmo prestador emitidas
# no mesmo mes passam igualmente na validacao CNPJ+AAMM de `decodificar`: so o
# codigo de verificacao diz de QUAL nota o anexo e. Achado real (lote Pluxee,
# 2026-11): o PDF trazia os anexos trocados (pag. 10 = anexo da nota da pag. 11,
# pag. 12 = anexo da nota da pag. 9) e a nota da pag. 11 herdava o numero da
# pag. 9 pela "pagina seguinte".

_RE_CV = r'[A-Z0-9]{4}-[A-Z0-9]{4}'
# Confusoes classicas do OCR em codigo alfanumerico, para comparar leituras.
_CONFUSOES_OCR = str.maketrans('OQDILSBZG', '000115825')


def codigo_verificacao_anexo(texto: str) -> Optional[str]:
    """Codigo de verificacao impresso na linha de valores logo abaixo do
    cabecalho "... Numero da Nota  Codigo de Verificacao" do anexo IBS/CBS."""
    m = re.search(r'N[uú]mero\s+da\s+Nota\s+C[óo]digo\s+de\s+Verifica[çc][ãa]o[^\n]*\n[ \t]*([^\n]*)',
                  texto or '', re.IGNORECASE)
    if not m:
        return None
    cv = re.search(r'\b(' + _RE_CV + r')\b', m.group(1))
    return cv.group(1) if cv else None


def codigos_verificacao_nota(texto: str) -> Set[str]:
    """Codigos de verificacao lidos na pagina da nota: o 1o codigo "XXXX-XXXX"
    em ate 150 caracteres depois de cada rotulo "Codigo de Verificacao" (o
    cabecalho da NFS-e paulistana imprime o rotulo e o valor em linhas vizinhas,
    as vezes com o RPS no meio)."""
    achados: Set[str] = set()
    for m in re.finditer(r'C[óo]digo\s+de\s+Verifica[çc][ãa]o', texto or '', re.IGNORECASE):
        cv = re.search(r'\b(' + _RE_CV + r')\b', texto[m.end():m.end() + 150])
        if cv:
            achados.add(cv.group(1))
    return achados


def codigos_verificacao_divergem(a: Optional[str], b: Optional[str]) -> bool:
    """True so quando os DOIS codigos sao legiveis e diferem em 2+ posicoes
    depois de normalizar as confusoes do OCR (O/0, I/1, S/5...): uma letra
    trocada pelo OCR nao faz de uma nota outra nota."""
    if not a or not b:
        return False
    na = re.sub(r'[^A-Z0-9]', '', a.upper()).translate(_CONFUSOES_OCR)
    nb = re.sub(r'[^A-Z0-9]', '', b.upper()).translate(_CONFUSOES_OCR)
    if len(na) != len(nb):
        return True
    return sum(x != y for x, y in zip(na, nb)) >= 2


def anexo_e_de_outra_nota(cv_anexo: Optional[str], cvs_nota: Set[str]) -> bool:
    """O anexo traz um codigo de verificacao legivel que nao bate com NENHUM
    codigo lido na nota (que tambem precisa ter ao menos um legivel)."""
    return bool(cv_anexo and cvs_nota) and all(
        codigos_verificacao_divergem(cv_anexo, cv) for cv in cvs_nota)
