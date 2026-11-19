"""NFS-e de Eldorado do Sul/RS (portal "nfseeldoradodosul.govbr.cloud").

Template "Nota Fiscal de Serviços Eletrônica (DANFSE)" do portal municipal
govbr.cloud: cabeçalho do PRESTADOR à esquerda, caixa "Número da NFS-e" /
"Data do Serviço" / "Código Verificador" à direita; faixa "MUNICÍPIO DE
ELDORADO DO SUL/RS - Secretaria da Fazenda" com "Dt. de Emissão",
"Exigibilidade ISS" e "Tributado no Município"; blocos TOMADOR e
INTERMEDIÁRIO (rótulo pequeno em cima, valor embaixo); tabela "DESCRIÇÃO DOS
SERVIÇOS | VALOR TOTAL | ALIQ. | VALOR IMPOSTO | RETIDO"; "Código do Serviço"
(item LC 116); grade de tributos federais (só informativa - CIDE, COFINS,
ICMS, IOF, IPI, PIS...) e grade do ISSQN (próprio/retido/total/deduções);
código de barras no rodapé cujo texto é NÚMERO + CÓDIGO VERIFICADOR + CNPJ
DO PRESTADOR concatenados.

Achado real 2026-11-19: DELL_NF2955797.pdf (DELL COMPUTADORES DO BRASIL LTDA
-> NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA, R$ 151,52, ISS 2%
não retido), PDF sem camada de texto (só imagem). Sem este módulo a página
caía em LAYOUT_GENERICO -> "Layout não reconhecido" -> nenhum XML.

A leitura de página inteira do Tesseract perde por completo a caixa do
número e a do "Dt. de Emissão", embaralha o CNPJ do tomador ("16.665
B69/0002.97") e lê o '@' do e-mail como "O". Por isso `ler_recortes` faz
leituras dedicadas por região (a caixa do cabeçalho, a faixa da emissão e,
ancoradas nos rótulos achados por `image_to_data`, as linhas do CNPJ e do
e-mail do tomador), e `extrair` (função PURA sobre texto, testável sem PDF)
só aceita o que é confirmado: CNPJ por dígito verificador, número/código
verificador conferidos com o texto do código de barras, valores conferidos
pela aritmética do próprio documento. O que não fecha vira sentinela + aviso
(princípio de integridade fiscal do projeto).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from ..models.nfse_models import Endereco, Entidade, Valores
from .sp_identificador import cnpj_valido

# Código IBGE de Eldorado do Sul/RS, conferido na API oficial do IBGE
# (servicodados.ibge.gov.br/api/v1/localidades/municipios/4306767 ->
# "Eldorado do Sul", UF RS).
COD_IBGE_ELDORADO_DO_SUL = '4306767'

SENTINELA_NUMERO = '00000000'
SENTINELA_CODIGO_VERIFICACAO = 'XXXX-XXXX'
SENTINELA_DOC = '00000000000000'

_UFS = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
    'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
}

_RE_VALOR = r'\d{1,3}(?:\.\d{3})*,\d{2}'
_RE_CNPJ = r'\d{2}\.?\d{3}\.?\d{3}\s*/\s*\d{4}\s*-?\s*\d{2}'
_RE_DATA = r'\d{2}/\d{2}/\d{4}'
# Código Verificador: token alfanumérico curto (na nota real, 9 caracteres
# hexadecimais minúsculos, "830e3b7ff").
_RE_CV = r'[0-9a-zA-Z]{6,12}'

# Complemento colado no fim do logradouro pelo portal ("AL GABRIEL MONTEIRO
# DA SILVA C TERREA,1480"): só separa diante de uma palavra-chave típica de
# complemento; sem ela, tudo fica no logradouro (nunca adivinha).
_RE_COMPLEMENTO = re.compile(
    r'\s+((?:C\s+TERRE[AO]|CASA|APTO?\.?|AP\.?|APARTAMENTO|SALA|SL\.?|LOJA|LJ\.?|'
    r'BLOCO|BL\.?|ANDAR|CONJ(?:UNTO)?\.?|CJ\.?|FUNDOS|T[ÉE]RRE[OA]|GALP[ÃA]O|BOX|'
    r'QUADRA|QD\.?|LOTE|LT\.?)\b.*)$',
    re.IGNORECASE)


@dataclass
class NotaEldorado:
    numero: str
    codigo_verificacao: str
    data_emissao: datetime
    data_emissao_fallback: bool
    competencia: datetime
    prestador: Entidade
    tomador: Entidade
    discriminacao: str
    servico_codigo: str
    valores: Valores
    municipio_tributacao: Optional[Tuple[str, str]]  # (nome, UF) impresso
    avisos: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def eh_template(texto: str) -> bool:
    """Gate ESTREITO: título "(DANFSE)" do portal + marca do município de
    Eldorado do Sul (URL do portal "nfseeldoradodosul.govbr.cloud" OU o
    cabeçalho "MUNICÍPIO DE ELDORADO DO SUL") + um rótulo estrutural do
    template ("Código Verificador"/"Exigibilidade"/"Tributado no Município").
    "Eldorado do Sul" solto (endereço de prestador/tomador de outra nota)
    nunca basta."""
    t = texto or ''
    titulo = re.search(r'Servi[çc]os\s+Eletr[ôo]nica\s*\(\s*DANFSE\s*\)', t, re.IGNORECASE)
    municipio = re.search(r'nfse\s*eldoradodosul\s*\.\s*govbr\s*\.\s*cloud', t, re.IGNORECASE) \
        or re.search(r'MUNIC[ÍI]PIO\s+DE\s+ELDORADO\s+DO\s+SUL', t, re.IGNORECASE)
    estrutura = re.search(
        r'C[óo]digo\s+Verificador|Exigibilidade|Tributado\s+no\s+Munic[íi]pio', t, re.IGNORECASE)
    return bool(titulo and municipio and estrutura)


# ---------------------------------------------------------------------------
# Recortes dedicados (OCR) - só para página escaneada
# ---------------------------------------------------------------------------

# Regiões em fração da página (x0, y0, x1, y1), com folga em volta da caixa.
_REGIAO_CABECALHO = (0.735, 0.03, 1.0, 0.13)   # Número / Data do Serviço / Código Verificador
_REGIAO_EMISSAO = (0.50, 0.12, 1.0, 0.21)     # Dt. de Emissão / Exigibilidade / Tributado no Município
_REGIAO_PRESTADOR = (0.0, 0.02, 0.62, 0.14)   # letterhead do prestador (e-mail/fone)


def ler_recortes(pdf_path: str, page_idx: int) -> Dict[str, List[str]]:
    """Leituras dedicadas por região (várias por campo, para votação).
    Devolve {} em qualquer falha (sem Tesseract, página inexistente...) - o
    `extrair` segue só com o texto de página inteira e avisa o que faltar."""
    try:
        import io
        import os
        import pymupdf
        import pytesseract
        from PIL import Image

        tess = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tess):
            pytesseract.pytesseract.tesseract_cmd = tess

        doc = pymupdf.open(pdf_path)
        try:
            if page_idx < 0 or page_idx >= len(doc):
                return {}
            page = doc.load_page(page_idx)
            imagens = {}
            for z in (3, 4):
                pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z))
                imagens[z] = Image.open(io.BytesIO(pix.tobytes('png'))).convert('L')
        finally:
            doc.close()

        def _crop(im, reg):
            w, h = im.size
            return im.crop((int(reg[0] * w), int(reg[1] * h), int(reg[2] * w), int(reg[3] * h)))

        out: Dict[str, List[str]] = {'cabecalho': [], 'emissao': [], 'prestador': [],
                                     'cnpj_tomador': [], 'email_tomador': []}
        for z, im in imagens.items():
            out['cabecalho'].append(pytesseract.image_to_string(_crop(im, _REGIAO_CABECALHO), lang='por', config='--psm 6'))
            out['emissao'].append(pytesseract.image_to_string(_crop(im, _REGIAO_EMISSAO), lang='por', config='--psm 6'))
            # 'eng' lê o '@' que o 'por' troca por "O"/"Q"/"G".
            out['prestador'].append(pytesseract.image_to_string(_crop(im, _REGIAO_PRESTADOR), lang='eng', config='--psm 6'))

        # Linhas do CNPJ e do e-mail do TOMADOR: ancoradas nos rótulos
        # "CNPJ"/"E-mail" que vêm DEPOIS de "TOMADOR" (posição pelo
        # image_to_data da imagem 3x, reescalada para as outras).
        im3 = imagens[3]
        dados = pytesseract.image_to_data(im3, lang='por', output_type=pytesseract.Output.DICT)
        palavras = [(dados['text'][i] or '', dados['left'][i], dados['top'][i], dados['height'][i])
                    for i in range(len(dados['text']))]
        topo_tomador = next((t for (w, l, t, h) in palavras if re.match(r'TOMADOR', w, re.IGNORECASE)), None)
        topo_interm = next((t for (w, l, t, h) in palavras if re.match(r'INTERMEDI', w, re.IGNORECASE)), None)
        if topo_tomador is not None:
            def _rotulo(padrao):
                for (w, l, t, h) in palavras:
                    if t > topo_tomador and (topo_interm is None or t < topo_interm) and re.match(padrao, w, re.IGNORECASE):
                        return l, t, h
                return None
            for chave, padrao, lang in (('cnpj_tomador', r'CNPJ', 'por'), ('email_tomador', r'E-?mail', 'eng')):
                r = _rotulo(padrao)
                if not r:
                    continue
                l, t, h = r
                for z, im in imagens.items():
                    f = z / 3.0
                    w_img = im.size[0]
                    caixa = (int(max(0, l - 6) * f), int((t + h) * f), int(0.68 * w_img), int((t + h + 3.2 * h) * f))
                    out[chave].append(pytesseract.image_to_string(im.crop(caixa), lang=lang, config='--psm 7'))
        return out
    except Exception:  # noqa: BLE001 - recorte é só reforço; falha = sem recorte
        return {}


# ---------------------------------------------------------------------------
# Helpers de texto
# ---------------------------------------------------------------------------

def _valor(s: str) -> float:
    return float(s.replace('.', '').replace(',', '.'))


def _linhas(t: str) -> List[str]:
    return [ln.strip() for ln in t.splitlines()]


def _limpa(s: str) -> str:
    """Tira molduras de célula que o OCR lê como caracteres ("[", "|")."""
    return re.sub(r'^[\[\]|(){}_;:,.\s]+|[\[\]|{}_;\s]+$', '', s or '').strip()


def _linha_apos(t: str, rotulo: str, inicio: int = 0, fim: Optional[int] = None) -> Optional[str]:
    """Primeira linha não vazia depois da linha que casa `rotulo` (dentro de
    t[inicio:fim])."""
    trecho = t[inicio:fim] if fim is not None else t[inicio:]
    m = re.search(rotulo, trecho, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    resto = trecho[trecho.find('\n', m.end()) + 1:] if '\n' in trecho[m.end():] else ''
    for ln in resto.splitlines():
        if ln.strip():
            return ln.strip()
    return None


def _votar(candidatos: Iterable[str]) -> Tuple[Optional[str], int, int]:
    """(mais votado, votos dele, nº de valores distintos)."""
    c = Counter(x for x in candidatos if x)
    if not c:
        return None, 0, 0
    valor, votos = c.most_common(1)[0]
    return valor, votos, len(c)


def _cnpjs_validos(texto: str) -> List[str]:
    achados = []
    for m in re.finditer(_RE_CNPJ, texto or ''):
        d = re.sub(r'\D', '', m.group(0))
        if cnpj_valido(d):
            achados.append(d)
    return achados


def _fmt(v: float) -> str:
    return f"{v:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')


# ---------------------------------------------------------------------------
# Extração
# ---------------------------------------------------------------------------

def extrair(texto: str, recortes: Optional[Dict[str, List[str]]] = None,
            resolver_ibge: Optional[Callable[[str, str], str]] = None) -> NotaEldorado:
    """Campos da NFS-e a partir do texto de página inteira (`texto`) e das
    leituras dedicadas (`recortes`, ver `ler_recortes`; vazio para PDF
    digital/teste). `resolver_ibge(municipio, uf) -> código IBGE`."""
    t = texto or ''
    rec = recortes or {}
    avisos: List[str] = []
    resolver = resolver_ibge or (lambda nome, uf: COD_IBGE_ELDORADO_DO_SUL)

    prestador, cnpj_prest_impresso = _prestador(t, rec, resolver, avisos)
    numero, cv = _numero_e_codigo(t, rec, prestador.cnpj_cpf, avisos)
    data_servico, data_emissao, emissao_fallback = _datas(t, rec, avisos)
    competencia = datetime((data_servico or data_emissao).year, (data_servico or data_emissao).month, 1)
    tomador = _tomador(t, rec, resolver, avisos)
    valores = _valores(t, avisos)
    discriminacao = _discriminacao(t, avisos)
    servico_codigo = _codigo_servico(t, avisos)
    mun_trib = _municipio_tributacao(t, rec)
    _exigibilidade(t, rec, avisos)

    return NotaEldorado(
        numero=numero, codigo_verificacao=cv, data_emissao=data_emissao,
        data_emissao_fallback=emissao_fallback, competencia=competencia,
        prestador=prestador, tomador=tomador, discriminacao=discriminacao,
        servico_codigo=servico_codigo, valores=valores,
        municipio_tributacao=mun_trib, avisos=avisos)


def _prestador(t: str, rec, resolver, avisos) -> Tuple[Entidade, Optional[str]]:
    lns = _linhas(t)
    razao = 'Prestador Não Identificado'
    logradouro, numero, complemento = 'Não informado', 'S/N', None
    idx_titulo = next((i for i, ln in enumerate(lns) if re.search(r'\(\s*DANFSE\s*\)', ln, re.IGNORECASE)), None)
    idx_cep = next((i for i, ln in enumerate(lns) if re.search(r'^CEP\s*:', ln, re.IGNORECASE)), None)
    if idx_titulo is not None and idx_cep is not None and idx_cep > idx_titulo:
        bloco = [ln for ln in lns[idx_titulo + 1: idx_cep] if ln]
        if len(bloco) >= 2:
            razao = _limpa(bloco[0]) or razao
            logradouro, numero, complemento = _endereco_prestador(bloco[1])
        elif len(bloco) == 1:
            razao = _limpa(bloco[0]) or razao
    if razao == 'Prestador Não Identificado':
        avisos.append("Razão social do prestador não lida no cabeçalho - conferir na nota")

    cep, bairro = '00000000', 'Não informado'
    m = re.search(r'CEP\s*:\s*(\d{5})\s*-?\s*(\d{3})\s*-?\s*(?:Bairro\s*:\s*([^\n\[|]+))?', t, re.IGNORECASE)
    if m:
        cep = m.group(1) + m.group(2)
        if m.group(3) and _limpa(m.group(3)):
            bairro = _limpa(m.group(3))
    else:
        avisos.append("CEP do prestador não lido - mantido zerado, conferir na nota")

    municipio, uf = 'Eldorado do Sul', 'RS'
    m = re.search(r'Munic[íi]pio\s*:\s*([^\n]+?)\s*-\s*([A-Z]{2})\b', t)
    if m and m.group(2) in _UFS:
        municipio, uf = _limpa(m.group(1)), m.group(2)
    else:
        avisos.append("Município do prestador não lido no cabeçalho - assumido Eldorado do Sul/RS "
                      "(município emissor da nota), conferir na nota")
    codigo_mun = resolver(municipio, uf)

    # CNPJ / IE / IM: linha de valores logo abaixo dos rótulos do prestador.
    cnpj_impresso, im = None, None
    m = re.search(r'CNPJ\s*/?\s*CPF[^\n]*Inscri[çc][ãa]o\s+Municipal[^\n]*\n((?:[^\n]*\n){0,3})', t, re.IGNORECASE)
    if m:
        m2 = re.search(r'(' + _RE_CNPJ + r')(?:\s+(\d{3,20}))?(?:\s+(\d{1,20}))?', m.group(1))
        if m2:
            d = re.sub(r'\D', '', m2.group(1))
            if cnpj_valido(d):
                cnpj_impresso = d
                if m2.group(3):
                    im = m2.group(3)
                elif m2.group(2):
                    # Só um número após o CNPJ: não dá para saber se é IE ou IM.
                    im = None
    cnpj_barra = _cnpj_do_codigo_barras(t)
    if cnpj_impresso and cnpj_barra and cnpj_impresso != cnpj_barra:
        avisos.append(f"CNPJ do prestador impresso ({cnpj_impresso}) diverge do código de barras "
                      f"({cnpj_barra}) - usado o impresso, conferir na nota")
    cnpj = cnpj_impresso or cnpj_barra
    if not cnpj:
        cnpj = SENTINELA_DOC
        avisos.append("CNPJ do prestador ilegível (nenhuma leitura com dígito verificador válido) - conferir na nota")
    if im is None:
        avisos.append("Inscrição Municipal do prestador não lida - conferir na nota")

    email, telefone = _contato_prestador(t, rec)
    ent = Entidade(
        cnpj_cpf=cnpj, inscricao_municipal=im, razao_social=razao,
        endereco=Endereco(logradouro=logradouro, numero=numero, complemento=complemento,
                          bairro=bairro, codigo_municipio=codigo_mun, municipio=municipio,
                          uf=uf, cep=cep),
        email=email, telefone=telefone)
    return ent, cnpj_impresso


def _endereco_prestador(linha: str) -> Tuple[str, str, Optional[str]]:
    """"AV INDUSTRIAL BELGRAF, 400 - -" -> (logradouro, número, complemento)."""
    linha = _limpa(linha)
    m = re.match(r'^(.+?),\s*(\d+[A-Za-z]?|S/?N)\b\s*(.*)$', linha, re.IGNORECASE)
    if not m:
        return linha or 'Não informado', 'S/N', None
    comp = re.sub(r'^[\s\-–]+|[\s\-–]+$', '', m.group(3))
    comp = re.sub(r'(?:\s*-\s*)+$', '', comp).strip()
    return m.group(1).strip(), m.group(2).upper(), (comp or None)


def _contato_prestador(t: str, rec) -> Tuple[Optional[str], Optional[str]]:
    emails, fones = [], []
    for fonte in list(rec.get('prestador', [])):
        for m in re.finditer(r'E-?mail\s*:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', fonte, re.IGNORECASE):
            emails.append(m.group(1).upper())
    for fonte in list(rec.get('prestador', [])) + [t]:
        m = re.search(r'Fone\s*:\s*(\(\s*\d{1,3}\s*\)\s*\d{4,5}\s*-\s*\d{4})', fonte, re.IGNORECASE)
        if m:
            fones.append(re.sub(r'\s+', '', m.group(1)))
    email, votos_e, distintos_e = _votar(emails)
    fone, votos_f, distintos_f = _votar(fones)
    # Contato não é dado fiscal, mas também não se inventa: só entra com 2+
    # leituras concordando e nenhuma divergente.
    email = email if votos_e >= 2 and distintos_e == 1 else None
    fone = fone if votos_f >= 2 and distintos_f == 1 else None
    return email, fone


def _cnpj_do_codigo_barras(t: str) -> Optional[str]:
    tok = _token_codigo_barras(t)
    if tok and cnpj_valido(tok[-14:]):
        return tok[-14:]
    return None


def _token_codigo_barras(t: str) -> Optional[str]:
    """Texto impresso sob o código de barras: NÚMERO + CÓDIGO VERIFICADOR +
    CNPJ DO PRESTADOR, numa linha só, sem espaços (o OCR às vezes intercala
    espaços - são removidos)."""
    for ln in reversed(_linhas(t)):
        compacto = re.sub(r'\s+', '', ln)
        if re.fullmatch(r'\d{6,}[0-9a-zA-Z]+\d{14}', compacto) and len(compacto) >= 30:
            return compacto
    return None


def _numero_e_codigo(t: str, rec, cnpj_prestador: str, avisos) -> Tuple[str, str]:
    fontes = list(rec.get('cabecalho', [])) + [t]
    numeros, cvs = [], []
    for f in fontes:
        m = re.search(r'da\s+NFS-?e\s*\n+\W*(\d{8,20})\b', f, re.IGNORECASE)
        if m:
            numeros.append(m.group(1))
        m = re.search(r'C[óo]digo\s+Verificador\s*\n+[^\n]*?' + _RE_DATA + r'\s*[|\]\[]?\s*(' + _RE_CV + r')\b', f, re.IGNORECASE)
        if not m:
            # Página inteira: a linha dos valores sai fundida com a dos
            # rótulos do prestador ("... Inscrição Municipal E E 10/02/2026 830e3b7ff").
            m = re.search(r'Inscri[çc][ãa]o\s+Municipal[^\n]*?' + _RE_DATA + r'\s*[|\]\[]?\s*(' + _RE_CV + r')\s*$', f, re.IGNORECASE | re.MULTILINE)
        if m and re.search(r'\d', m.group(1)) and re.search(r'[A-Za-z]', m.group(1)):
            cvs.append(m.group(1))

    numero, _, dist_n = _votar(numeros)
    cv, _, dist_cv = _votar(cvs)
    if dist_n > 1:
        avisos.append(f"Leituras divergentes do Número da NFS-e ({', '.join(sorted(set(numeros)))}) - "
                      "usada a mais votada, conferir na nota")
    if dist_cv > 1:
        avisos.append(f"Leituras divergentes do Código Verificador ({', '.join(sorted(set(cvs)))}) - "
                      "usada a mais votada, conferir na nota")

    # Conferência com o texto do código de barras (número + CV + CNPJ do prestador).
    tok = _token_codigo_barras(t)
    if tok and tok[-14:] == cnpj_prestador:
        corpo = tok[:-14]
        if numero and cv:
            if corpo != numero + cv:
                avisos.append(f"Número/Código Verificador lidos ({numero} / {cv}) não conferem com o texto "
                              f"do código de barras ({tok}) - conferir na nota")
        elif numero and corpo.startswith(numero) and len(corpo) > len(numero):
            cv = corpo[len(numero):]
        elif cv and corpo.endswith(cv) and len(corpo) > len(cv):
            numero = corpo[:-len(cv)]
    if not numero:
        numero = SENTINELA_NUMERO
        avisos.append("Número da NFS-e ilegível (caixa do cabeçalho e código de barras) - conferir na nota")
    if not cv:
        cv = SENTINELA_CODIGO_VERIFICACAO
        avisos.append("Código Verificador ilegível - conferir na nota")
    return numero, cv


def _datas(t: str, rec, avisos) -> Tuple[Optional[datetime], datetime, bool]:
    def _dt(s):
        try:
            return datetime.strptime(s, '%d/%m/%Y')
        except ValueError:
            return None

    servicos = []
    for f in list(rec.get('cabecalho', [])) + [t]:
        m = re.search(r'Data\s+do\s+Servi[çc]o[^\n]*\n+[^\n]*?(' + _RE_DATA + r')', f, re.IGNORECASE)
        if not m:
            m = re.search(r'Inscri[çc][ãa]o\s+Municipal[^\n]*?(' + _RE_DATA + r')\s*[|\]\[]?\s*' + _RE_CV + r'\s*$', f, re.IGNORECASE | re.MULTILINE)
        if m and _dt(m.group(1)):
            servicos.append(m.group(1))
    emissoes = []
    for f in list(rec.get('emissao', [])) + [t]:
        m = re.search(r'Dt\.?\s*de\s+Emiss[ãa]o[^\n]*\n+\W*(' + _RE_DATA + r')', f, re.IGNORECASE)
        if m and _dt(m.group(1)):
            emissoes.append(m.group(1))
    servico, _, dist_s = _votar(servicos)
    emissao, _, dist_e = _votar(emissoes)
    if dist_s > 1 or dist_e > 1:
        avisos.append("Leituras divergentes de Data do Serviço/Dt. de Emissão - usada a mais votada, conferir na nota")
    d_serv = _dt(servico) if servico else None
    if emissao:
        return d_serv, _dt(emissao), False
    if d_serv:
        avisos.append("Dt. de Emissão ilegível - usada a Data do Serviço impressa como data de emissão, conferir na nota")
        return d_serv, d_serv, False
    avisos.append("Data de emissão não encontrada (usando a data atual como fallback)")
    hoje = datetime.now()
    return None, hoje, True


def _tomador(t: str, rec, resolver, avisos) -> Entidade:
    ini_m = re.search(r'TOMADOR\s+DO\s+SERVI', t, re.IGNORECASE)
    fim_m = re.search(r'INTERMEDI[ÁA]RIO\s+DO\s+SERVI', t, re.IGNORECASE)
    ini = ini_m.end() if ini_m else 0
    fim = fim_m.start() if (fim_m and fim_m.start() > ini) else None
    bloco = t[ini:fim] if fim else t[ini:]

    razao = _linha_apos(bloco, r'Nome\s*/\s*Raz[ãa]o\s+Social')
    if razao:
        razao = _limpa(razao)
        # A coluna "Município de Prestação do Serviço" sai colada no fim da
        # linha da razão social ("... LTDA Eldorado do Sul/RS").
        razao = re.sub(r'\s+[A-ZÀ-Ú][a-zà-ÿ]+(?:\s+(?:d[aeo]s?|[A-ZÀ-Ú][a-zà-ÿ]+))*\s*/\s*[A-Z]{2}\s*$', '', razao).strip()
    if not razao:
        razao = 'Tomador Não Identificado'
        avisos.append("Razão social do tomador não lida - conferir na nota")

    logradouro, numero, complemento = 'Não informado', 'S/N', None
    linha_end = _linha_apos(bloco, r'^\W*Endere[çc]o\s*$')
    if linha_end:
        linha_end = _limpa(linha_end)
        m = re.match(r'^(.+?)\s*,\s*(\d+[A-Za-z]?|S/?N)\s*(.*)$', linha_end, re.IGNORECASE)
        if m:
            logradouro, numero = m.group(1).strip(), m.group(2).upper()
            resto = _limpa(re.sub(r'^[\s\-–,]+', '', m.group(3)))
            mc = _RE_COMPLEMENTO.search(logradouro)
            if mc and mc.start() > 0:
                complemento = mc.group(1).strip()
                logradouro = logradouro[:mc.start()].strip()
            if resto:
                complemento = f"{complemento} {resto}".strip() if complemento else resto
        else:
            logradouro = linha_end
    else:
        avisos.append("Endereço do tomador não lido - conferir na nota")

    municipio, uf, cep, telefone = None, None, '00000000', None
    linha_cid = _linha_apos(bloco, r'Cidade\s+UF')
    if linha_cid:
        m = re.match(r'^\W*(.+?)\s+([A-Za-z]{2})\b\s*(.*?)(\d{5})\s*-?\s*(\d{3})\s*$', linha_cid)
        if m and m.group(2).upper() in _UFS:
            municipio, uf = _limpa(m.group(1)), m.group(2).upper()
            cep = m.group(4) + m.group(5)
            mf = re.search(r'\(?\s*(\d{1,3})\s*\)\s*(\d{4,5})\s*-\s*(\d{4})', m.group(3))
            if mf:
                telefone = f"({mf.group(1)}) {mf.group(2)}-{mf.group(3)}"
    if not municipio:
        municipio, uf = 'Não informado', 'RS'
        avisos.append("Cidade/UF/CEP do tomador ilegíveis - conferir na nota")
    codigo_mun = resolver(municipio, uf)

    bairro = _limpa(_linha_apos(bloco, r'^\W*Bairro\s*$') or '') or 'Não informado'

    # CNPJ: leituras dedicadas da linha (votação + dígito verificador); o
    # texto de página inteira só entra se também passar no DV.
    candidatos = []
    for f in rec.get('cnpj_tomador', []):
        candidatos.extend(_cnpjs_validos(f))
    m_rot = re.search(r'CNPJ\s*/?\s*7?\s*CPF[^\n]*\n((?:[^\n]*\n){0,2})', bloco, re.IGNORECASE)
    if m_rot:
        candidatos.extend(_cnpjs_validos(m_rot.group(1)))
    cnpj, votos, distintos = _votar(candidatos)
    if not cnpj:
        cnpj = SENTINELA_DOC
        avisos.append("CNPJ/CPF do tomador ilegível (nenhuma leitura com dígito verificador válido) - conferir na nota")
    elif distintos > 1:
        avisos.append(f"Leituras divergentes do CNPJ do tomador ({', '.join(sorted(set(candidatos)))}) - "
                      "usado o mais votado, conferir na nota")

    emails = []
    for f in rec.get('email_tomador', []):
        m = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,3})', f)
        if m:
            emails.append(m.group(1).upper())
    email, votos_e, dist_e = _votar(emails)
    email = email if votos_e >= 2 and dist_e == 1 else None

    return Entidade(
        cnpj_cpf=cnpj, inscricao_municipal=None, razao_social=razao,
        endereco=Endereco(logradouro=logradouro, numero=numero, complemento=complemento,
                          bairro=bairro, codigo_municipio=codigo_mun, municipio=municipio,
                          uf=uf, cep=cep),
        email=email, telefone=telefone)


def _valores(t: str, avisos) -> Valores:
    total = aliq = imposto = None
    retido = None
    m = re.search(r'(' + _RE_VALOR + r')\s+(\d{1,2},\d{1,4})\s+(' + _RE_VALOR + r')\s+(Sim|N[ãa]o)\b', t, re.IGNORECASE)
    if m:
        total, aliq, imposto = _valor(m.group(1)), _valor(m.group(2)) / 100.0, _valor(m.group(3))
        retido = m.group(4).lower().startswith('s')

    # Grade do ISSQN: 6 valores na linha abaixo dos rótulos.
    base = iss_proprio = base_ret = iss_ret = iss_total = deducoes = None
    m = re.search(r'Base\s+C[áa]lculo\s+ISSQN\s+Pr[óo]prio[^\n]*Dedu[çc][ãa]o[^\n]*\n+\s*((?:[\[|]?\s*' + _RE_VALOR + r'\s*){6})', t, re.IGNORECASE)
    if m:
        vs = [_valor(v) for v in re.findall(_RE_VALOR, m.group(1))]
        base, iss_proprio, base_ret, iss_ret, iss_total, deducoes = vs[:6]

    liquido = None
    m = re.search(r'Valor\s+L[íi]quido\s+da\s+NFS-?e\W*(' + _RE_VALOR + r')', t, re.IGNORECASE)
    if m:
        liquido = _valor(m.group(1))
    total_nota = None
    m = re.search(r'Valor\s+Total\s+da\s+NFS-?e\W*(' + _RE_VALOR + r')', t, re.IGNORECASE)
    if m:
        total_nota = _valor(m.group(1))

    servicos = total if total is not None else total_nota
    if servicos is None:
        avisos.append("Valor total dos serviços ilegível - zerado, conferir na nota")
        servicos = 0.0
    elif total is not None and total_nota is not None and abs(total - total_nota) > 0.005:
        avisos.append(f"Valor total da descrição (R$ {_fmt(total)}) diverge do Valor Total da NFS-e "
                      f"(R$ {_fmt(total_nota)}) - usado o da descrição, conferir na nota")

    if retido is None:
        avisos.append("Coluna RETIDO ilegível - ISS tratado como não retido, conferir na nota")
        retido = False
    if deducoes is None:
        deducoes = 0.0
    if base is None:
        base = round(servicos - deducoes, 2) if servicos else 0.0
        if servicos:
            avisos.append("Grade do ISSQN ilegível - Base de Cálculo assumida = valor dos serviços, conferir na nota")
    if aliq is None:
        aliq = 0.0
        avisos.append("Alíquota do ISS ilegível - zerada, conferir na nota")
    valor_iss = imposto if imposto is not None else (iss_total if iss_total is not None else 0.0)
    if imposto is not None and iss_total is not None and abs(imposto - iss_total) > 0.005:
        avisos.append(f"Valor do imposto da descrição (R$ {_fmt(imposto)}) diverge do Valor Total do ISSQN "
                      f"(R$ {_fmt(iss_total)}) - conferir na nota")
    if aliq > 0.05 + 1e-9:
        avisos.append(f"Alíquota lida {aliq * 100:.2f}% ".replace('.', ',') + "acima do teto legal de 5% "
                      "(LC 116/2003 art. 8º) — erro de leitura, conferir na nota")
        aliq = 0.0
    elif aliq and base and abs(round(base * aliq, 2) - valor_iss) > 0.011:
        avisos.append(f"Base de Cálculo × Alíquota não confere com o Valor do ISS lido "
                      f"({base:.2f} × {aliq * 100:.2f}% ≠ {valor_iss:.2f}) — valores mantidos como lidos, conferir na nota")
    if abs((servicos - deducoes) - base) > 0.005:
        avisos.append(f"Base de Cálculo (R$ {_fmt(base)}) ≠ valor dos serviços − deduções "
                      f"(R$ {_fmt(servicos - deducoes)}) - conferir na nota")

    valor_iss_retido = 0.0
    if retido:
        valor_iss_retido = iss_ret if iss_ret else valor_iss
    if liquido is None:
        # Sem retenção federal impressa neste template: líquido = serviços −
        # ISS retido (ABRASF). Nunca abaixo de zero.
        liquido = round(max(servicos - valor_iss_retido, 0.0), 2)

    # Grade federal (CIDE/COFINS/ICMS/IOF/IPI/PIS) é informativa neste
    # template, não é retenção: nunca vai para ValorPis/ValorCofins. Valor
    # não zero impresso nela merece conferência humana.
    m = re.search(r'\bCIDE\b[^\n]*\n+\s*([^\n]+)', t)
    if m and any(_valor(v) > 0 for v in re.findall(_RE_VALOR, m.group(1))):
        avisos.append("Grade de tributos federais (CIDE/COFINS/PIS/ICMS/IOF/IPI) traz valor não zero - "
                      "não importado como retenção, conferir na nota")

    return Valores(
        valor_servicos=servicos, valor_deducoes=deducoes, iss_retido=retido,
        valor_iss=valor_iss, valor_iss_retido=valor_iss_retido, base_calculo=base,
        aliquota=aliq, valor_liquido_nfse=liquido)


def _discriminacao(t: str, avisos) -> str:
    m = re.search(r'DESCRI[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS[^\n]*\n([\s\S]+?)\n\s*C[óo]digo\s+do\s+Servi[çc]o', t, re.IGNORECASE)
    if not m:
        avisos.append("Descrição dos serviços não lida - conferir na nota")
        return 'Serviço conforme nota fiscal'
    texto = m.group(1)
    # Valores da 1ª linha (VALOR TOTAL / ALIQ. / VALOR IMPOSTO / RETIDO).
    texto = re.sub(r'\s+' + _RE_VALOR + r'\s+\d{1,2},\d{1,4}\s+' + _RE_VALOR + r'\s+(?:Sim|N[ãa]o)\b', '', texto, count=1, flags=re.IGNORECASE)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto or 'Serviço conforme nota fiscal'


def _codigo_servico(t: str, avisos) -> str:
    m = re.search(r'C[óo]digo\s+do\s+Servi[çc]o[^\n]*\n+\s*(\d{1,2})\s*\.\s*(\d{2})\b', t, re.IGNORECASE)
    if m:
        return f"{int(m.group(1)):02d}{m.group(2)}"
    avisos.append("Código do Serviço (item LC 116) não lido - mantido \"0000\", classificar o serviço manualmente")
    return '0000'


def _municipio_tributacao(t: str, rec) -> Optional[Tuple[str, str]]:
    """"Tributado no Município" impresso (nome, UF)."""
    for f in list(rec.get('emissao', [])) + [t]:
        m = re.search(r'Tributado\s+no\s+Munic[íi]pio[\s\S]{0,200}?([A-ZÀ-Ú][\wÀ-ÿ\' ]+?)\s*/\s*([A-Z]{2})\b', f)
        if m and m.group(2) in _UFS:
            return m.group(1).strip(), m.group(2)
    return None


def _exigibilidade(t: str, rec, avisos) -> None:
    texto = '\n'.join(list(rec.get('emissao', [])) + [t])
    if re.search(r'Exigibilidade', texto, re.IGNORECASE) and not re.search(r'\bExig[íi]vel\b', texto, re.IGNORECASE):
        avisos.append("Exigibilidade do ISS diferente de \"Exigível\" (ou ilegível) - XML sai como "
                      "exigível, conferir na nota")
