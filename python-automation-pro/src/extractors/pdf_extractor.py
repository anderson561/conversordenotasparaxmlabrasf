"""
Extrator de NFS-e em PDF — suporte a múltiplos layouts municipais.

Layouts detectados automaticamente:
  A — Cuiabá/MT (ISSNet):       "Data de Competência"
  B — Barreiras/BA:              "Data Fato Gerador"
  C — Camaçari/BA (CPqD):       "Data da prestação do serviço"
  D — NFS-e Nacional (DANFSe):  "Competência da NFS-e"
  E — Genérico/SP (ABRASF):     "Competência" MM/YYYY ou mês extenso
  ? — Imagem/Scan:               texto vazio → aviso de OCR necessário
"""

# pyrefly: ignore[missing-import]
from pdfminer.high_level import extract_text
import re
from typing import Optional, List
from ..models.nfse_models import Nfse, Entidade, Endereco, Valores
from ..utils.ibge_resolver import IBGEResolver
from datetime import datetime

_ibge_resolver = IBGEResolver()

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_MESES_PT = {
    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
    'abril': 4, 'maio': 5, 'junho': 6,
    'julho': 7, 'agosto': 8, 'setembro': 9,
    'outubro': 10, 'novembro': 11, 'dezembro': 12,
    'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
    'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
}

# Layouts detectáveis (ordem de prioridade)
LAYOUT_CUIABA    = 'cuiaba_issnet'    # Cuiabá/MT via ISSNet
LAYOUT_BARREIRAS = 'barreiras_ba'     # Barreiras/BA
LAYOUT_CAMACARI  = 'camacari_cpqd'    # Camaçari/BA via CPqD
LAYOUT_NACIONAL  = 'danfse_nacional'  # NFS-e Nacional / DANFSe v1.0
LAYOUT_SALVADOR  = 'salvador_ba'      # Salvador/BA
LAYOUT_FEIRA     = 'feira_de_santana' # Feira de Santana/BA
LAYOUT_RIO       = 'rio_de_janeiro'   # Rio de Janeiro/RJ (Nota Carioca)
LAYOUT_GENERICO  = 'generico'         # SP / ABRASF / outros
LAYOUT_LOCALIZA  = 'localiza_fatura'  # Localiza Rent A Car S/A (Fatura de Locação)
LAYOUT_SAO_PAULO = 'sao_paulo_sp'     # São Paulo/SP
LAYOUT_JOINVILLE = 'joinville_sc'     # Joinville/SC
LAYOUT_FORTALEZA = 'fortaleza_ce'     # Fortaleza/CE
LAYOUT_ISBET     = 'isbet_recibo'     # ISBET (Nota de Contribuição)
LAYOUT_SIMOES_FILHO = 'simoes_filho_ba'  # Simões Filho/BA
LAYOUT_RIBEIRAO_PIRES = 'ribeirao_pires_sp' # Ribeirão Pires/SP


# Etiquetas para Identificação de Entidades
_LABELS_PRESTADOR = [
    'Prestador', 'Emitente', 'Dados do Prestador', 'Dados do Emitente',
    'Identificação do Prestador', 'Prestador do Serviço', 'EMITENTE DA NFS-e',
    'PRESTADOR DE SERVIÇOS', 'Prestador de Serviço', 'Dados do Prestador de Serviço',
    'Prestador de Serviços',   # Portal Nacional / DANFSe (plural)
    'PRESTADOR DE SERVIÇO',    # Variante sem acento
    'Fornecedor',              # Portal Nacional / DANFSe usa 'Fornecedor'
]
_LABELS_TOMADOR = [
    'Tomador', 'Dados do Tomador', 'Identificação do Tomador',
    'Tomador do Serviço', 'Dados do Cliente', 'TOMADOR DO SERVIÇO',
    'TOMADOR DE SERVIÇOS', 'Tomador de Serviço', 'Dados do Tomador de Serviço',
    'Tomador de Serviços',     # Portal Nacional (plural)
    'Cliente',                 # Portal Nacional / DANFSe usa 'Cliente'
]
_LABELS_INTERMEDIARIO = [
    'Intermediário do Serviço', 'INTERMEDIÁRIO DO SERVIÇO', 'Intermediário',
    'Intermediario', 'Dados do Intermediário', 'INTERMEDIARIO'
]
_LABELS_CNPJ_CPF = [
    'CNPJ', 'CPF', 'CNPJ / CPF / NIF', 'CPF/CNPJ', 'Inscrição Federal', 'CPF/CNPJ:'
]


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class SPPdfExtractor:
    """
    Extrator de NFS-e com detecção automática de layout municipal.
    Suporta múltiplos formatos de prefeituras diferentes.
    """

    # Padrão de exclusão (páginas de lixo que acompanham a nota/comprovantes bancários)
    TRASH_PATTERN = r'Recibo\s+de\s+Transfer[êe]ncia|Comprovante\s+de\s+Transa[cç][aã]o\s+Banc[aá]ria|Fatura\s+-\s+C[aâ]mara\s+de\s+Dirigentes\s+Lojistas'

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.raw_text = ''
        self.layout: Optional[str] = None

    # ------------------------------------------------------------------
    # Extração de texto bruto
    # ------------------------------------------------------------------

    def extract_raw_text(self) -> str:
        
        full_text = extract_text(self.pdf_path)
        # O pdfminer costuma separar páginas com o caractere \x0c (form feed)
        pages = full_text.split('\x0c')
        filtered_pages = []
        for page in pages:
            # Skip pages matching trash patterns
            if re.search(self.TRASH_PATTERN, page, re.IGNORECASE):
                continue
            # Detect layout of the page
            layout = self._detect_layout_page(page)
            # Keep page only if layout is recognized (not generic)
            if layout != LAYOUT_GENERICO:
                filtered_pages.append(page)
        
        self.raw_text = '\n\x0c\n'.join(filtered_pages).strip()
        return self.raw_text

    # ------------------------------------------------------------------
    # Detecção de layout
    # ------------------------------------------------------------------

    def _detect_layout(self) -> str:
        """
        Identifica o layout da nota a partir de marcas textuais únicas.
        """
        t = self.raw_text
        if re.search(r'Prefeitura Municipal de Cuiab[aá]|ISSNet', t, re.IGNORECASE):
            return LAYOUT_CUIABA
        if re.search(r'Data\s+Fato\s+Gerador', t, re.IGNORECASE):
            return LAYOUT_BARREIRAS
        if re.search(r'CPqD\s*[-–]\s*Gest[aã]o\s+P[uú]blica', t, re.IGNORECASE):
            return LAYOUT_CAMACARI
        if re.search(r'DANFSe\s+v\d|Compet[eê]ncia\s+da\s+NFS-e|Data\s+de\s+Compet[eê]ncia|Chave\s+de\s+Acesso', t, re.IGNORECASE | re.DOTALL):
            return LAYOUT_NACIONAL
        if re.search(r'PREFEITURA.*SALVADOR|Xique-Xique', t, re.IGNORECASE):
            return LAYOUT_SALVADOR # Ou um layout genérico da BA
        if re.search(r'FEIRA DE SANTANA', t, re.IGNORECASE):
            return LAYOUT_FEIRA
        if re.search(r'RIO DE JANEIRO|NOTA CARIOCA', t, re.IGNORECASE):
            return LAYOUT_RIO
        if re.search(r'LOCALIZA RENT A CAR S/A|FATURA\s*/\s*DUPLICATA', t, re.IGNORECASE):
            return LAYOUT_LOCALIZA
        if re.search(r'PREFEITURA DO MUNIC[IÍ]PIO DE S[AÃ]O PAULO', t, re.IGNORECASE):
            return LAYOUT_SAO_PAULO
        if re.search(r'Prefeitura de Joinville|NF-em', t, re.IGNORECASE):
            return LAYOUT_JOINVILLE
        if re.search(r'PREFEITURA MUNICIPAL DE FORTALEZA', t, re.IGNORECASE):
            return LAYOUT_FORTALEZA
        if re.search(r'NOTA DE CONTRIBUIÇÃO SOLIDÁRIA|ISBET', t, re.IGNORECASE):
            return LAYOUT_ISBET
        if re.search(r'Sim[oõ]es Filho', t, re.IGNORECASE):
            return LAYOUT_SIMOES_FILHO
        if re.search(r'Ribeir[aã]o Pires', t, re.IGNORECASE):
            return LAYOUT_RIBEIRAO_PIRES
        return LAYOUT_GENERICO

    def _detect_layout_page(self, page_text: str) -> str:
        """Detect layout for a single page's text.
        Returns a layout constant or LAYOUT_GENERICO if none match.
        """
        t = page_text
        if re.search(r'Prefeitura Municipal de Cuiab[aá]|ISSNet', t, re.IGNORECASE):
            return LAYOUT_CUIABA
        if re.search(r'Data\s+Fato\s+Gerador|MUNICIPIO\s+DE\s+BARREIRAS', t, re.IGNORECASE):
            return LAYOUT_BARREIRAS
        if re.search(r'CPqD\s*[-–]\s*Gest[aã]o\s+P[uú]blica', t, re.IGNORECASE):
            return LAYOUT_CAMACARI
        if re.search(r'DANFSe\s+v\d|Compet[eê]ncia\s+da\s+NFS-e|Data\s+de\s+Compet[eê]ncia|Chave\s+de\s+Acesso', t, re.IGNORECASE | re.DOTALL):
            return LAYOUT_NACIONAL
        if re.search(r'PREFEITURA.*SALVADOR|Xique-Xique', t, re.IGNORECASE):
            return LAYOUT_SALVADOR
        if re.search(r'FEIRA DE SANTANA', t, re.IGNORECASE):
            return LAYOUT_FEIRA
        if re.search(r'RIO DE JANEIRO|NOTA CARIOCA', t, re.IGNORECASE):
            return LAYOUT_RIO
        if re.search(r'LOCALIZA RENT A CAR S/A|FATURA\s*/\s*DUPLICATA', t, re.IGNORECASE):
            return LAYOUT_LOCALIZA
        if re.search(r'PREFEITURA DO MUNIC[IÍ]PIO DE S[AÃ]O PAULO', t, re.IGNORECASE):
            return LAYOUT_SAO_PAULO
        if re.search(r'Prefeitura de Joinville|NF-em', t, re.IGNORECASE):
            return LAYOUT_JOINVILLE
        if re.search(r'PREFEITURA MUNICIPAL DE FORTALEZA', t, re.IGNORECASE):
            return LAYOUT_FORTALEZA
        if re.search(r'NOTA DE CONTRIBUIÇÃO SOLIDÁRIA|ISBET', t, re.IGNORECASE):
            return LAYOUT_ISBET
        if re.search(r'Sim[oõ]es Filho', t, re.IGNORECASE):
            return LAYOUT_SIMOES_FILHO
        if re.search(r'Ribeir[aã]o Pires', t, re.IGNORECASE):
            return LAYOUT_RIBEIRAO_PIRES
        return LAYOUT_GENERICO

    # ------------------------------------------------------------------
    # Extração de competência por layout
    # ------------------------------------------------------------------

    def _extrair_competencia(self, data_emissao: datetime) -> datetime:
        t = self.raw_text
        layout = self.layout or LAYOUT_GENERICO
        result: Optional[datetime] = None

        if layout == LAYOUT_CUIABA:
            m = re.search(r'Data\s+de\s+Compet[eê]ncia\s*\n\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_BARREIRAS:
            m = re.search(r'Data\s+Fato\s+Gerador\s*\n\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_CAMACARI:
            m = re.search(r'Data\s+da\s+presta[cç][aã]o\s+do\s+servi[cç]o\s*:\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_NACIONAL:
            # Captura o trecho logo após a label e busca a primeira data (DD/MM/YYYY ou MM/YYYY)
            m = re.search(r'Compet[eê]ncia\s+da\s+NFS-e', t, re.IGNORECASE)
            if m:
                snippet = t[m.end():m.end()+150]
                m_date = re.search(r'(\d{2}/\d{2}/\d{4}|\d{1,2}/\d{4})(?!\d)', snippet)
                if m_date:
                    val = m_date.group(1)
                    if len(val.split('/')) == 3:
                        result = _parse_dmy(val) or None
                    else:
                        try:
                            mes_str, ano_str = val.split('/')
                            result = datetime(int(ano_str), int(mes_str), 1)
                        except (ValueError, TypeError):
                            result = None
        elif layout == LAYOUT_SALVADOR:
            m = re.search(r'COMPET[EÊ]NCIA(?:\s*:\s*|\s+)(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res:
                    result = datetime(res.year, res.month, 1)
            else:
                m = re.search(r'COMPET[EÊ]NCIA(?:\s*:\s*|\s+)(\d{2}/\d{4})', t, re.IGNORECASE)
                if m:
                    mes, ano = m.group(1).split('/')
                    result = datetime(int(ano), int(mes), 1)
        elif layout == LAYOUT_FEIRA:
            m = re.search(r'Fato\s+Gerador\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_RIO:
            m = re.search(r'M[eê]s\s+de\s+Compet[eê]ncia[:\s\n]+(\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                mes, ano = m.group(1).split('/')
                result = datetime(int(ano), int(mes), 1)
        elif layout == LAYOUT_LOCALIZA:
            m = re.search(r'DATA DE EMISS[AÃ]O:\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_SAO_PAULO:
            m = re.search(r'Compe:\s*([A-Za-z]+/\d{4})', t, re.IGNORECASE)
            if m:
                try:
                    mes_str, ano_str = m.group(1).split('/')
                    mes = _MONTHS.get(mes_str.lower()[:3], 1)
                    result = datetime(int(ano_str), mes, 1)
                except: pass
        elif layout == LAYOUT_FORTALEZA:
            m = re.search(r'Compet[eê]ncia[\s\n]*(\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                try:
                    mes, ano = m.group(1).split('/')
                    result = datetime(int(ano), int(mes), 1)
                except: pass
        elif layout == LAYOUT_ISBET:
            m = re.search(r'Data\s+de\s+Emiss[aã]o:\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_JOINVILLE:
            m = re.search(r'Compet[eê]ncia[\s\n]*(\d{1,2}/\d{4})', t, re.IGNORECASE)
            if m:
                try:
                    mes_str, ano_str = m.group(1).split('/')
                    result = datetime(int(ano_str), int(mes_str), 1)
                except: pass

        if result is None: result = _extrair_competencia_generica(t)
        if result is None: result = datetime(data_emissao.year, data_emissao.month, 1)
        return result

    def _extrair_data_emissao(self) -> datetime:
        t = self.raw_text
        if self.layout == LAYOUT_LOCALIZA:
            m = re.search(r'DATA DE EMISS[AÃ]O:\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_NACIONAL:
            # Padrão específico para DANFSe Nacional
            m_nac = re.search(r'Compet[eê]ncia\s+da\s+NFS-e[\s\n]+Data\s+e\s+Hora\s+da\s+emiss[aã]o.*?[\r\n]+(?:\d+[\r\n\s]+)?(?:\d{2}/\d{2}/\d{4})[\r\n\s]+(\d{2}/\d{2}/\d{4})[\r\n\s]+(\d{2}:\d{2}(?::\d{2})?)', t, re.IGNORECASE | re.DOTALL)
            if m_nac:
                res = _parse_dmy(m_nac.group(1), m_nac.group(2))
                if res: return res

        # Padrões mais flexíveis (Rio, Salvador, etc.)
        # Adicionado padrão específico para Rio sem separador fixo após o label
        patterns = [
            r'Emitido\s+em\s+(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?',
            r'Data\s+e\s+Hora\s+d[ea]\s+Emiss[aã]o.*?(?::|\s|\n)+(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?',
            r'(?:Data\s+de\s+Gera[cç][aã]o|Data\s+e\s+Hora\s+da\s+emiss[aã]o).*?(?::|\s|\n)+(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?',
            r'Data\s+de\s+Emiss[aã]o.*?(?::|\s|\n)+(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?',
            r'Emiss[aã]o(?:\s*\(Hor[aá]rio\s+de\s+Bras[ií]lia\))?.*?(?::|\s|\n)+(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?',
        ]
        for pattern in patterns:
            m = re.search(pattern, t, re.IGNORECASE | re.DOTALL)
            if m:
                data_str = m.group(1)
                hora_str = m.group(2) if m.lastindex >= 2 else None
                resultado = _parse_dmy(data_str, hora_str)
                if resultado: return resultado
                
        # Fallback usando a Chave de Acesso Nacional (Mês/Ano) para casos de OCR severo
        m_chave = re.search(r'\b(?:\d\s*){44,52}\b', t)
        if m_chave:
            chave = re.sub(r'\D', '', m_chave.group(0))
            if len(chave) >= 50:
                yy_mm = chave[36:40]
                if yy_mm.isdigit():
                    ano = 2000 + int(yy_mm[:2])
                    mes = int(yy_mm[2:])
                    if 1 <= mes <= 12 and 2000 <= ano <= 2100:
                        # Extraímos dia 1 pois a chave só nos dá o mês/ano
                        return datetime(ano, mes, 1)

        return datetime.now()

    # ------------------------------------------------------------------
    # Extração de campos simples (Final Strike version)
    # ------------------------------------------------------------------

    def _validate_cnpj_cpf(self, doc: str) -> bool:
        """Validação básica de checksum para CNPJ e CPF."""
        d = re.sub(r'\D', '', doc)
        if len(d) == 11:
            # CPF
            if d == d[0] * 11: return False
            for i in range(9, 11):
                val = sum((int(d[num]) * ((i + 1) - num)) for num in range(i))
                rev = (val * 10) % 11
                if rev == 10: rev = 0
                if rev != int(d[i]): return False
            return True
        elif len(d) == 14:
            # CNPJ
            if d == d[0] * 14: return False
            for i in [12, 13]:
                weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if i == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
                val = sum(int(d[num]) * weights[num] for num in range(i))
                rev = 11 - (val % 11)
                if rev >= 10: rev = 0
                if rev != int(d[i]): return False
            return True
        return False

    def _scavenge_all_cnpjs(self) -> List[str]:
        t = self.raw_text
        # Encontra padrões de dígitos espalhados que pareçam CNPJ (11-14 dígitos purgados)
        candidates = re.findall(r'\d\s*[\d\.\s/\\-]{10,80}\d', t)
        purged = []
        for c in candidates:
            p = re.sub(r'\D', '', c)
            if len(p) in (11, 14) and self._validate_cnpj_cpf(p):
                purged.append(p)
        return list(dict.fromkeys(purged))

    def _extrair_numero(self) -> str:
        t = self.raw_text
        
        if self.layout == LAYOUT_LOCALIZA:
            m = re.search(r'N[ºo]:\s*([A-Z0-9\s-]+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()
            
        if self.layout == LAYOUT_SAO_PAULO:
            m = re.search(r'N[uú]mero\s+da\s+Nota[:\s\n]+(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()
            
        if self.layout == LAYOUT_JOINVILLE:
            m = re.search(r'N[uú]mero\s*/\s*S[eé]rie[\s\n]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()
            
        if self.layout == LAYOUT_FORTALEZA:
            m = re.search(r'N[uú]mero\s+da\s+NFS-e[\s\n]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()
            
        if self.layout == LAYOUT_ISBET:
            m = re.search(r'N[ºo]:\s*([A-Z0-9-]+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()
            
        if self.layout == LAYOUT_RIBEIRAO_PIRES:
            m = re.search(r'NFS-e[\s\n]+(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()
            
        # 1. Busca por proximidade do label (Alta prioridade para DANFSe v1.0)
        # Procura o rótulo e pega o primeiro número que aparece depois dele (até 100 caracteres de distância)
        label_patterns = [
            r'N[uú]mero\s+(?:da\s+)?NFS-e', 
            r'N[uú]mero\s+da\s+Nota\s+Fiscal', 
            r'N[ºo]\s+da\s+Nota\s+Fiscal',
            r'N[uú]mero\s+da\s+Nota'
        ]
        for lp in label_patterns:
            m_lab = re.search(lp, t, re.IGNORECASE)
            if m_lab:
                # Pega o texto após o label e busca o primeiro conjunto de dígitos
                pos = m_lab.end()
                pos_end = min(pos + 100, len(t))
                m_prox = re.search(r'(\d+)', t[pos:pos_end])
                if m_prox:
                    num = m_prox.group(1).strip()
                    # Evita pegar anos (2024, 2026) se o número for curto
                    if num not in ('2024', '2025', '2026') or len(num) > 4:
                        return num

        # 2. Chave de Acesso (DANFSe Nacional / Cuiabá) - 44, 48 ou 50 dígitos purgados de uma sequência contínua
        m_chave = re.search(r'\b(?:\d\s*){44,52}\b', t)
        if m_chave:
            chave = re.sub(r'\D', '', m_chave.group(0))
            if len(chave) == 44:
                n_nf = chave[25:34].lstrip('0')
            elif len(chave) == 48:
                n_nf = chave[23:38].lstrip('0')
            elif len(chave) >= 50:
                n_nf = chave[23:36].lstrip('0')
            else:
                n_nf = None
            if n_nf: return n_nf

        # 3. Padrões tradicionais (Regex direto)
        patterns = [
            r'N[uú]mero\s+da\s+Nota\s+Fiscal\s*[:\s\n]*(\d+)',
            r'N[ºo]\s+da\s+Nota\s+Fiscal\s*[:\s\n]*(\d+)',
            r'N[uú]mero\s+da\s+NFS-e\s*[:\s\n]*(\d+)',
            r'N[uú]mero\s+da\s+Nota\s*[:\s\n]*(\d+)',
            r'N[uú]mero[:\s]+(\d+)',
            r'NFS-e\s*n[uú]mero[:\s]+(\d+)',
            r'NFS-e\s*[:\s\n]*(\d+)',
            r'N[ºo]\s*[:\s\n]*(\d+)',
            r'Nota\s*n[ºo]\s*[:\s\n]*(\d+)',
        ]
        for p in patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m: return m.group(1).strip()
            
        # Fallback para Cuiabá (Número isolado após label sem dois pontos)
        m_cuiaba = re.search(r'N[uú]mero\s+da\s+Nota\s+Fiscal\s*\n\s*(\d+)', t, re.IGNORECASE)
        if m_cuiaba: return m_cuiaba.group(1).strip()

        # Fallback de último recurso: Tentar extrair do nome do arquivo (NFS 13954, NOTA 123, NF-123)
        if getattr(self, 'pdf_path', None):
            import os
            basename = os.path.basename(self.pdf_path)
            m_filename = re.search(r'(?:NFS?|NOTA|NF)\s*[-_]*\s*(\d+)', basename, re.IGNORECASE)
            if m_filename:
                return m_filename.group(1).strip()

        return '00000000'

    def _extrair_discriminacao(self) -> str:
        t = self.raw_text
        # Label common to multiple layouts but very specific in its start/end in Rio
        def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p
        
        start_labels = [
            relax("Discriminação dos Serviços"),
            relax("DISCRIMINAÇÃO DOS SERVIÇOS"),
            relax("Discriminação"),
        ]
        end_labels = [
            relax("VALOR TOTAL DA NOTA"),
            relax("Valor Total da Nota"),
            relax("Código do Serviço"),
            relax("Item da Lista de Serviços"),
            relax("Para uso da Secretaria da Fazenda"),
        ]
        
        pattern = rf'(?:{"|".join(start_labels)})[:\s\n]*(.*?)(?={"|".join(end_labels)}|$)'
        m = re.search(pattern, t, re.IGNORECASE | re.DOTALL)
        if m:
            res = m.group(1).strip()
            # Clean up extra whitespace and newlines
            res = re.sub(r'\s+', ' ', res)
            return res
        return "Serviços prestados conforme nota fiscal."

    def _extrair_codigo_servico(self) -> str:
        t = self.raw_text
        def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p

        patterns = [
            rf'{relax("Item da Lista de Serviços")}[:\s\n]*([\d\.]+)',
            rf'{relax("Código do Serviço")}[:\s\n]*([\d\.]+)',
            r'C[oó]digo\s+de\s+Servi[cç]o[:\s\n]*([\d\.]+)',
            r'C[oó]digo\s+de\s+Atividade\s+CNAE[:\s\n]*([\d\.]+)',
            r'Natureza\s+dos\s+servi[cç]os[:\s\n]*(.+)',
        ]
        for p in patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                # Se for o caso do ISBET (texto), tenta retornar um código genérico ou o primeiro número encontrado
                num_m = re.search(r'(\d+)', val)
                if num_m: return num_m.group(1).zfill(4)
                return "03115"
        
        return "03115" # Default fallback

    def _extrair_codigo_verificacao(self) -> str:
        t = self.raw_text
        def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p

        # Padrões com relax() forçado para capturar etiquetas ruidosas
        # Limitando o range para evitar engolir linhas seguintes (ruído)
        patterns = [
            rf'{relax("Código de Verificação")}.*?{relax("Autenticação")}\s*[: \n]*([A-Z0-9\- \t]+)',
            rf'{relax("Código de Verificação")}\s*[: \n]*([A-Z0-9\- \t]+)',
            rf'{relax("Autenticação")}\s*[: \n]*([A-Z0-9\- \t]+)',
            rf'{relax("Código de Autenticidade")}\s*[: \n]*([A-Z0-9\- \t]+)',
            rf'{relax("Cód. de Autenticidade")}\s*[: \n]*([A-Z0-9\- \t]+)',
            rf'{relax("Codigo da NFS-e")}\s*[: \n]*([A-Z0-9\- \t]+)',
            r'C[oó]digo [Vv]erifica[cç][aã]o[:\s\n]*([A-Z0-9\- \t]+)',
            # Específico para Salvador quando o OCR distorce "Código de Verificação"
            r'Nota Salvador.*?[\n\r]+([A-Z0-9\-]{4,15})[\n\r]+PRESTADOR',
        ]
        for p in patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m:
                # Remove espaços e qualquer caractere não-alfanumérico (ex: P-R-U-5 -> PRU5)
                raw_code = m.group(1).upper()
                res = re.sub(r'[^A-Z0-9]', '', raw_code).strip()
                print(f"DEBUG: CodVer match: '{raw_code}' -> '{res}'")
                if len(res) >= 4: return res
        
        return 'XXXX-XXXX'

    def _extrair_entidade(self, tipo: str) -> Optional[Entidade]:
        t = self.raw_text
        is_prestador = (tipo.lower() == 'prestador')
        is_intermediario = (tipo.lower() == 'intermediario')
        
        if self.layout == LAYOUT_LOCALIZA:
            if is_prestador:
                return Entidade(
                    cnpj_cpf="16670085091444",
                    razao_social="LOCALIZA RENT A CAR S/A",
                    endereco=Endereco(
                        endereco="ROD BR 324, 1084", bairro="CABULA",
                        municipio="SALVADOR", uf="BA", cep="41150170"
                    )
                )
            else:
                m_cli = re.search(r'CLIENTE:\s*(.+?)(?=\nENDEREÇO:|\nCÓDIGO:)', t, re.IGNORECASE | re.DOTALL)
                m_end = re.search(r'ENDEREÇO:\s*(.+?)\nCEP/CID/UF:\s*([\d-]+)\s*-\s*([A-Z\s]+)\s*-\s*([A-Z]{2})', t, re.IGNORECASE)
                m_cnpj = re.search(r'CNPJ:\s*([\d./-]+)', t, re.IGNORECASE)
                
                razao = m_cli.group(1).replace('\n', ' ').strip() if m_cli else ""
                cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else ""
                end_full = m_end.group(1).strip() if m_end else ""
                cep = re.sub(r'\D', '', m_end.group(2)) if m_end else ""
                mun = m_end.group(3).strip() if m_end else ""
                uf = m_end.group(4).strip() if m_end else ""
                
                return Entidade(
                    cnpj_cpf=cnpj or "00000000000000", razao_social=razao or "Não Identificado",
                    endereco=Endereco(endereco=end_full, municipio=mun, uf=uf, cep=cep)
                )

        def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p

        # 1. Bloco
        if is_intermediario:
            labels = sorted(_LABELS_INTERMEDIARIO, key=len, reverse=True)
            other_labels = _LABELS_PRESTADOR + _LABELS_TOMADOR
        else:
            labels = sorted(_LABELS_PRESTADOR if is_prestador else _LABELS_TOMADOR, key=len, reverse=True)
            other_labels = (_LABELS_TOMADOR if is_prestador else _LABELS_PRESTADOR) + _LABELS_INTERMEDIARIO

        pattern_labels = "|".join([relax(l) for l in labels])
        pattern_other_labels = "|".join([relax(l) for l in other_labels])
        delimiters = rf'{pattern_other_labels}|{relax("Discrimina")}|' + \
                     rf'{relax("VALOR TOTAL")}|{relax("DADOS COMPLEMENTARES")}|' + \
                     rf'{relax("OUTRAS INFORMAÇÕES")}|{relax("SERVIÇO PRESTADO")}|' + \
                     rf'{relax("Descrição do Serviço")}|$'
        
        pattern_bloco = rf'(?:{pattern_labels}).*?(?={delimiters})'
        m_bloco = re.search(pattern_bloco, t, re.IGNORECASE | re.DOTALL)
        
        if is_intermediario and not m_bloco:
            return None

        bloco = m_bloco.group(0) if m_bloco else t

        bloco_clean = bloco.replace('|', ' ').replace('!', ' ').replace('\n', ' ').strip()
        bloco_clean = re.sub(r'\s{2,}', ' ', bloco_clean)

        # 2. CNPJ
        cnpj = None
        # Tenta capturar CNPJ validando o checksum para evitar pegar datas ou números
        matches = re.findall(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})', bloco)
        for m in matches:
            pure = re.sub(r'\D', '', m)
            if self._validate_cnpj_cpf(pure):
                cnpj = pure
                break
        
        if not cnpj:
            all_cnpjs = self._scavenge_all_cnpjs()
            # No bloco da entidade, tentamos ver se algum desses CNPJs aparece
            for c in all_cnpjs:
                if c in re.sub(r'\D', '', bloco):
                    cnpj = c
                    break
            
            if not cnpj:
                if is_prestador and len(all_cnpjs) >= 1: cnpj = all_cnpjs[0]
                elif not is_prestador and not is_intermediario and len(all_cnpjs) >= 2:
                    if "NÃO IDENTIFICADO" not in bloco_clean.upper() and "NAO IDENTIFICADO" not in bloco_clean.upper():
                        cnpj = all_cnpjs[1]
        
        if not cnpj: cnpj = '00000000000100'

        # 3. Inscrição Municipal
        insc = None
        # Procura por número de 5 a 12 dígitos que esteja próximo ao label, ignorando o próprio CNPJ
        m_insc_label = re.search(rf'{relax("Inscrição Municipal")}|{relax("IM :")}', bloco_clean, re.IGNORECASE)
        if m_insc_label:
            pos = m_insc_label.end()
            contexto = bloco_clean[pos:pos+50]
            # Busca dígitos que não sejam o CNPJ já identificado
            digitos_contexto = re.findall(r'\d{5,15}', re.sub(r'[^\d\s]', '', contexto))
            for d in digitos_contexto:
                if d != cnpj:
                    insc = d
                    break

        # 4. Razão Social (com stop-patterns para evitar engolir campos seguintes)
        # ORDEM IMPORTA: labels mais específicos primeiro.
        p_extra = (
            relax("Nome/Razão Social") + "|" +
            relax("Nome / Razão Social") + "|" +
            relax("Nome/fazão Social") + "|" +
            relax("Nome / fazão Social") + "|" +
            relax("Nome/Nome Empresarial") + "|" +
            relax("Nome / Nome Empresarial") + "|" +
            relax("Nome/Nome Empresa") + "|" +
            relax("Nome / Nome Empresa") + "|" +
            relax("Razão Social") + "|" +
            relax("fazão Social") + "|" +
            relax("Nome Empresarial")
        )
        stop_patterns = (
            relax("Endereço") + "|" + relax("ndere") + "|" + relax("Município") + "|" + relax("Cidade/UF") + "|" + relax("CEP") + "|" +
            relax("Logradouro") + "|" + relax("Compl") + "|" +
            relax("CPF/CNPJ") + "|" + relax("CNPJ") + "|" + relax("CPF") + "|" +
            relax("Inscrição Municipal") + "|" + relax("IM :") + "|" + relax("Inscrição Estadual") + "|" +
            relax("Telefone") + "|" + relax("E-mail") + "|" + relax("Nome Fantasia") + "|" +
            relax("Fornecedor") + "|" + relax("Tomador") + "|" + relax("Cliente") + "|" +
            relax("Simples Nacional") + "|" + relax("Regime de Apura") + "|" + relax("Optante")
        )

        # Captura até encontrar um stop_pattern ou o fim do bloco
        pattern_razao = rf'(?:{p_extra})[:\s/]*((?:(?!{stop_patterns}).)+)'
        m_razao = re.search(pattern_razao, bloco_clean, re.IGNORECASE)
        razao = m_razao.group(1).strip() if m_razao else ''

        # Limpeza de ruídos de labels e pontuação inicial
        labels_limpeza = [
            relax("Nome / Razão Social"), relax("Nome/Razão Social"),
            relax("Nome / Nome Empresarial"), relax("Nome/Nome Empresarial"),
            relax("Nome / Nome Empresa"), relax("Nome/Nome Empresa"),
            relax("Razão Social"), relax("Nome Fantasia"), relax("Nome Empresarial"), relax("Nome"), relax("Emitente")
        ]
        for l in labels_limpeza:
            razao = re.sub(rf'^{l}\s*', '', razao, flags=re.I).strip()
            razao = re.sub(rf'^{l}\s*', '', razao, flags=re.I).strip()
        
        # Remove fragmentos de CNPJ no início (comum em layouts de grade)
        razao = re.sub(r'^\d{2}\.\d{3}\.\d{3}\s+', '', razao).strip()
        razao = re.sub(r'^\d{8,}\s+', '', razao).strip()
        razao = re.sub(r'^[\s/!|:.-]+', '', razao).strip()

        _NOISE_RAZAO = re.compile(
            r'\b(DA NFS-e|Prestador do Servi|Nota Fiscal|Documento Auxiliar|'
            r'DANFSe|Prefeitura|Secretaria|Inscri[cç]|CNPJ|CPF|Endere[cç])\b',
            re.IGNORECASE
        )
        
        _LABELS_NOISE = re.compile(
            r'^(E-mail|CNPJ|CPF|Inscri[cç]|Endere[cç]|Tel[eé]fone|Munic[ií]|'
            r'CEP|Simples|Regime|Bairro|Logradouro|Complemento|N[uú]mero|UF|'
            r'Fornecedor|Tomador|Cliente|Prestador|Emitente|Discrimina|'
            r'Valor|ISS|Aliq|Base|Código|C[oó]d\.?|Item|Competên|Data|NFS-e|Responsável|Autenticidade|Chave|Consulte|Fone)',
            re.IGNORECASE
        )

        def is_valid_razao(line: str) -> bool:
            line_clean = line.strip()
            # Clean emails (with OCR resilience for @ like Q, O or dot when followed by real domain)
            line_clean = re.sub(r'\b[a-zA-Z0-9._%+-]+(?:@|[qQoO]|\.)[a-zA-Z0-9.-]+\.(?:com|br|net|org|gov)\b', '', line_clean, flags=re.I).strip()
            # Clean CNPJs and other numbers
            line_clean = re.sub(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s*', '', line_clean).strip()
            line_clean = re.sub(r'^\d{2}\.\d{3}\.\d{3}\s*', '', line_clean).strip()
            line_clean = re.sub(r'^\d{8,}\s*', '', line_clean).strip()
            line_clean = re.sub(r'[\s/!|:.-]+$', '', line_clean).strip()
            
            if len(line_clean) < 3: return False
            if _LABELS_NOISE.match(line_clean): return False
            if _NOISE_RAZAO.search(line_clean): return False
            if re.match(r'^\d{2}/\d{2}/\d{4}', line_clean) or re.match(r'^\d{2}:\d{2}', line_clean): return False
            if re.match(r'^[0-9\.\s/\\:-]+$', line_clean): return False
            if re.search(r'Nome\s*/\s*Nome', line_clean, re.I): return False
            if re.match(r'^[A-Z0-9-]{6,15}$', line_clean, re.I): return False
            if '@' in line_clean.lower() or '.com' in line_clean.lower(): return False
            return True

        if is_valid_razao(razao):
            pass
        else:
            razao = ''

        # ---------------------------------------------------------------
        # Fallback linha-a-linha no bloco bruto (newlines preservadas)
        # ---------------------------------------------------------------
        if not razao:
            _label_pats = [
                r'Nome\s*/\s*Nome\s+Empresarial',
                r'Nome\s*/\s*Nome\s+Empresa',
                r'Nome\s*/\s*[Razfãzo]+\s+Social',
                r'[Razfãzo]+\s+Social',
                r'Nome\s+Empresarial',
            ]
            for lp in _label_pats:
                m_lbl = re.search(lp, bloco, re.IGNORECASE)
                if m_lbl:
                    after = bloco[m_lbl.end():]
                    linhas = [ln.strip() for ln in after.split('\n') if ln.strip()]
                    for linha in linhas[:10]:
                        if is_valid_razao(linha):
                            razao = linha
                            break
                if razao: break
            
            # TERCEIRO FALLBACK: Busca por padrão "Razão Social: XXX" em qualquer lugar do bloco
            if not razao:
                m_direct = re.search(r'[Razfãzo]+\s+Social\s*[:\-]*\s*(.+)', bloco, re.IGNORECASE)
                if m_direct:
                    line_candidate = m_direct.group(1).split('\n')[0].strip()
                    if is_valid_razao(line_candidate):
                        razao = line_candidate

        # SEGUNDO FALLBACK: Se ainda não achou (layout sem labels como Cuiabá)
        # Pega a primeira linha que não seja label de seção e não seja lixo
        if not razao:
            bloco_sem_header = re.sub(rf'^(?:{pattern_labels})[:\s\n]*', '', bloco, flags=re.I | re.DOTALL)
            linhas = [ln.strip() for ln in bloco_sem_header.split('\n') if ln.strip()]
            for linha in linhas[:15]: # Tenta as 15 primeiras linhas
                if is_valid_razao(linha):
                    razao = linha
                    break

        # Descarta/limpa captura lixo ou label
        if not is_valid_razao(razao):
            razao = ''
        else:
            # Limpeza final robusta:
            # 1. Remove e-mails (resiliente)
            razao = re.sub(r'\b[a-zA-Z0-9._%+-]+(?:@|[qQoO]|\.)[a-zA-Z0-9.-]+\.(?:com|br|net|org|gov)\b', '', razao, flags=re.I).strip()
            razao = re.sub(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '', razao).strip()
            # 2. Remove fragmentos de data/hora no final (como em Nota 7: PH COPIADORAS... 06/04/2026 18:51:03)
            razao = re.sub(r'\s*\d{2}/\d{2}/\d{4}.*$', '', razao).strip()
            # 3. Remove fragmentos de CNPJ/CPF/Inscrição no início ou fim
            razao = re.sub(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s*', '', razao).strip()
            razao = re.sub(r'^\d{2}\.\d{3}\.\d{3}\s*', '', razao).strip()
            razao = re.sub(r'^\d{8,}\s*', '', razao).strip()
            razao = re.sub(r'[\s/!|:.-]+$', '', razao).strip()
            
        if not razao:
            razao = f'{tipo} Não Identificado'

        # 5. Endereço e IBGE
        end_data = {
            'logradouro': 'Não informado', 'numero': 'S/N', 'bairro': 'Não informado',
            'municipio': 'Não informado',
            'codigo_municipio': _ibge_resolver.default_code, 'uf': _ibge_resolver.default_uf, 'cep': '00000-000',
        }

        # Tenta extrair E-mail
        email = None
        m_email = re.search(rf'{relax("E-mail")}\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})', bloco_clean, re.IGNORECASE)
        if m_email:
            email = m_email.group(1).strip()
        
        # Tenta extrair Telefone
        telefone = None
        # Padrão para telefone: (XX) XXXX-XXXX ou similar
        m_tel = re.search(rf'{relax("Telefone")}\s*([\(\)\d\s-]{8,20})', bloco_clean, re.IGNORECASE)
        if m_tel:
            telefone = m_tel.group(1).strip()

        # Tenta extrair CEP
        m_cep = re.search(rf'{relax("CEP")}\s*[:\- ]*\s*([\d\- ]+)', bloco_clean, re.IGNORECASE)
        if m_cep:
            end_data['cep'] = re.sub(r'\D', '', m_cep.group(1))

        # Tenta extrair Município e UF
        m_mun = re.search(rf'(?:{relax("Município")}|{relax("Cidade/UF")})\s*([^0-9]+?)(?={relax("CEP")}|{relax("Telefone")}|{relax("E-mail")}|$)', bloco_clean, re.IGNORECASE)
        if m_mun:
            mun_text = m_mun.group(1).strip()
            # Limpeza de possíveis sobras de labels
            mun_text = re.sub(r'^[:\s]+', '', mun_text)
            
            clean_mun = mun_text
            
            # Checa se existe "UF: BA" ou "UF BA" no texto de município
            m_uf_in_mun = re.search(r'\bUF\s*[:\s]\s*([A-Z]{2})', mun_text, re.IGNORECASE)
            if m_uf_in_mun:
                end_data['uf'] = m_uf_in_mun.group(1).upper()
                clean_mun = re.sub(r'\bUF\s*[:\s]\s*[A-Z]{2}', '', clean_mun, flags=re.IGNORECASE).strip()
            
            if ' - ' in clean_mun:
                parts = clean_mun.split(' - ')
                clean_mun = parts[0].strip()
                if len(parts) > 1:
                    end_data['uf'] = parts[-1].strip()[:2].upper()
            elif '/' in clean_mun:
                parts = clean_mun.split('/')
                clean_mun = parts[0].strip()
                if len(parts) > 1:
                    end_data['uf'] = parts[-1].strip()[:2].upper()
            
            # Remove pontuações e espaços extras residuais
            clean_mun = re.sub(r'^[\s/!|:.-]+|[\s/!|:.-]+$', '', clean_mun).strip()
            end_data['municipio'] = clean_mun

        # Tenta extrair Logradouro, Número e Bairro
        m_end = re.search(rf'{relax("Endereço")}\s*(.*?)(?={relax("Município")}|{relax("Municipio")}|{relax("CEP")}|{relax("Telefone")}|{relax("E-mail")}|$)', bloco_clean, re.IGNORECASE | re.DOTALL)
        if m_end:
            partes_end = m_end.group(1).strip()
            # Se houver vírgulas, tentamos quebrar em Logradouro, Número, Bairro
            if ',' in partes_end:
                bits = [b.strip() for b in partes_end.split(',')]
                if len(bits) >= 3:
                    end_data['logradouro'] = bits[0]
                    end_data['numero'] = bits[1]
                    end_data['bairro'] = bits[2]
                elif len(bits) == 2:
                    end_data['logradouro'] = bits[0]
                    end_data['numero'] = bits[1]
            elif ' - ' in partes_end:
                spl = partes_end.rsplit(' - ', 1)
                end_data['logradouro'], end_data['bairro'] = spl[0].strip(), spl[1].strip()
            else:
                end_data['logradouro'] = partes_end

        # Detectar UF com base no Layout ou Regex no endereço (Fallback/Refinamento)
        if not end_data.get('uf') or len(end_data['uf']) != 2:
            if self.layout == LAYOUT_RIO:
                end_data['uf'] = "RJ"
            elif self.layout in (LAYOUT_SALVADOR, LAYOUT_BARREIRAS, LAYOUT_FEIRA, LAYOUT_CAMACARI):
                end_data['uf'] = "BA"
            elif self.layout == LAYOUT_CUIABA:
                end_data['uf'] = "MT"
            else:
                end_data['uf'] = "SP"

        # Refinamento por regex
        UFS_BRASIL = r'AC|AL|AM|AP|BA|CE|DF|ES|GO|MA|MG|MS|MT|PA|PB|PE|PI|PR|RJ|RN|RO|RR|RS|SC|SE|SP|TO'
        m_uf = re.search(rf'\b({UFS_BRASIL})\b', bloco_clean)
        if m_uf and m_uf.group(1):
            end_data['uf'] = m_uf.group(1).upper()

        end_data['codigo_municipio'] = _ibge_resolver.extract_and_validate(
            bloco_clean, detected_uf=end_data['uf'], raw_doc_text=t
        )

        return Entidade(
            cnpj_cpf=cnpj, 
            inscricao_municipal=insc, 
            razao_social=razao, 
            endereco=Endereco(**end_data),
            email=email,
            telefone=telefone
        )

    def _extrair_valores(self) -> Valores:
        t = self.raw_text
        
        if self.layout == LAYOUT_LOCALIZA:
            m_val = re.search(r'VALOR TOTAL\s+R\$\s*([\d.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        val_serv, base, aliq, iss = 0.0, 0.0, 0.0, 0.0
        pis, cofins, inss, ir, csll, outras = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        _val_patterns = [
            r'V[LlIi]\.\s+do\s+Servi[cç]o\s*[:\s\n]*R?\$?\s*([\d\.,]+)',
            r'VALOR\s+TOTAL\s+DA\s+NOTA\s*[=:]\s*R\$?\s*([\d\.,]+)',
            r'VALOR\s+TOTAL\s+DO\s+SERVIÇO:?\s*R\$?\s*([\d\.,]+)',
            r'V[LlIi]\.\s+Total\s+dos\s+Servi[cç]os\s*[:\s\n]*R?\$?\s*([\d\.,]+)',
            r'VALOR\s+SERVIÇO\s*(?:\(R\$\))?[:\s\n]*([\d\.,]+)',
            r'Valor\s+total\s+da\s+Nota:?\s*R?\$?\s*([\d\.,]+)',
            r'VALOR\s+DA\s+NOTA\s*=\s*R?\$?\s*([\d\.,]+)',
            r'Valor\s+do\s+Servi[cç]o\s*R?\$?\s*([\d\.,]+)',
            r'Valor\s+L[ií]quido\s+da\s+NFS-e[:\s]*R?\$?\s*([\d\.,]+)',
            r'Valor\s+(?:Total\s+)?dos?\s+Servi[cç]os?(?:\s*\(R\$\))?(?:.*?\n)?[\s]*([\d\.,]+)',
            r'TOTAL\s+DO\s+SERVI[CÇ]O[:\s]*R?\$?\s*([\d\.,]+)',
            r'Valor\s+Total\s+\(R\$\)[:\s\n]*([\d\.,]+)',
            # Padrão para tabelas (Cuiabá/DANFSe/Barreiras) - Tenta pegar o primeiro valor R$ após o cabeçalho
            r'(?:V[LlIi]\.\s+Total\s+dos\s+Servi[cç]os|Valor\s+do\s+Servi[cç]o).*?\n\s*R?\$?\s*([\d\.,]+)',
            r'VALOR\s+SERVIÇO.*?\n\s*R?\$?\s*([\d\.,]+)',
            r'VALOR\s+TOTAL\s+DA\s+NFS-E.*?\n\s*Valor\s+do\s+Servi[cç]o.*?\n\s*R?\$?\s*([\d\.,]+)',
        ]
        for p in _val_patterns:
            m_val = re.search(p, t, re.IGNORECASE)
            if m_val:
                val_serv = self._parse_valor(m_val.group(1))
                break

        # Impostos e Retenções
        m_inss = re.search(r'(?:Valor\s+)?INSS\s*\(R\$\):?\s*([\d\.,]+)', t, re.IGNORECASE)
        if not m_inss:
            m_inss = re.search(r'Contribui[çc][ãa]o\s+Previdenci[áa]ria\s*[-–]\s*Retida\s*[\n\r\s]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
        if m_inss: inss = self._parse_valor(m_inss.group(1))
        
        m_pis = re.search(r'(?:Valor\s+)?PIS\s*\(R\$\):?\s*([\d\.,]+)', t, re.IGNORECASE)
        if m_pis: pis = self._parse_valor(m_pis.group(1))
        
        m_cofins = re.search(r'(?:Valor\s+)?COFINS\s*\(R\$\):?\s*([\d\.,]+)', t, re.IGNORECASE)
        if m_cofins: cofins = self._parse_valor(m_cofins.group(1))
        
        m_ir = re.search(r'(?:Valor\s+)?IR(?:RF)?\s*\(?R\$\)?\s*[=:]?\s*([\d\.,]+)', t, re.IGNORECASE)
        if not m_ir:
            m_ir = re.search(r'IRRF\s*[\n\r\s]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
        if m_ir: ir = self._parse_valor(m_ir.group(1))
        
        m_csll = re.search(r'(?:Valor\s+)?CSLL\s*\(R\$\):?\s*([\d\.,]+)', t, re.IGNORECASE)
        if not m_csll:
            # Captura 'Contribuições Sociais - Retidas' do DANFSe (Geralmente PIS/COFINS/CSLL juntos)
            m_soc = re.search(r'Contribui[çc][õo]es\s+Sociais\s*[-–]\s*Retidas\s*[\n\r\s]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            if m_soc: csll = self._parse_valor(m_soc.group(1))
        else:
            csll = self._parse_valor(m_csll.group(1))
        
        val_deducoes = 0.0
        m_ded = re.search(r'Dedu[çc][õo]es\s+Base\s+C[áa]lculo\s*[:\s\n]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
        if m_ded: val_deducoes = self._parse_valor(m_ded.group(1))
        
        m_outras = re.search(r'Outras\s+Reten[cç][õo]es\s*\(R\$\):?\s*([\d\.,]+)', t, re.IGNORECASE)
        if not m_outras:
            m_outras = re.search(r'Total\s+das\s+Reten[cç][õo]es\s+Federais\s*[\n\r\s]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            if m_outras:
                val_total_fed = self._parse_valor(m_outras.group(1))
                # Se capturamos o total mas PIS/COFINS/CSLL/IR estão vazios, podemos usar esse valor como outras_retencoes
                # ou apenas para validar. Por segurança, só somamos se for maior que a soma individual.
                if val_total_fed > (pis + cofins + inss + ir + csll):
                    outras = val_total_fed - (pis + cofins + inss + ir + csll)
        if m_outras and not outras:
             outras = self._parse_valor(m_outras.group(1)) if 'Total' not in m_outras.group(0) else outras

        m_base = re.search(r'B\.?C\.?\s+do\s+ISS\s*(?:\(R\$\))?(?:.*?\n)?[\s=:]*([\d\.,]+)', t, re.IGNORECASE)
        if not m_base:
            m_base = re.search(r'Base\s+de\s+C[aá]lculo\s*[=:R\$\s]+([\d\.,]+)', t, re.IGNORECASE)
        if m_base: base = self._parse_valor(m_base.group(1))

        m_aliq = re.search(r'Al[ií]quota\s*(?:ISS\s*)?(?:\(%\))?[=:]?\s*(?:.*?\n)?\s*([\d\.,]+)', t, re.IGNORECASE)
        if not m_aliq:
            # Tenta pegar valor pequeno (0-5) em tabelas que contenham 'Alíquota'
            m_aliq_tab = re.findall(r'\|\s*(\d[,\.]\d{1,2})\s*\|', t)
            if m_aliq_tab:
                aliq = self._parse_valor(m_aliq_tab[0]) / 100
        elif m_aliq:
            val_aliq = self._parse_valor(m_aliq.group(1))
            # Se a alíquota for absurdamente alta (como um código CNAE), descarta e tenta secundário
            if val_aliq > 100:
                m_aliq_sec = re.search(r'\|\s*(\d[,\.]\d{1,2})\s*\|', t)
                if m_aliq_sec: val_aliq = self._parse_valor(m_aliq_sec.group(1))
                else: val_aliq = 0.0
            aliq = val_aliq / 100

        m_iss = re.search(r'(?:Valor\s+do\s+|Total\s+do\s+)?ISS(?:QN)?\s*(?:\(R\$\))?[=:R\$\s]*(?:.*?\n)?\s*([\d\.,]+)', t, re.IGNORECASE)
        if m_iss: iss = self._parse_valor(m_iss.group(1))

        # Valor Líquido (Tenta capturar ou calcula)
        val_liq = 0.0
        m_liq = re.search(r'VALOR\s+L[IÍ]QUIDO\s*(?:\(R\$\))?[:\s\n]*([\d\.,]+)', t, re.IGNORECASE)
        if not m_liq:
            m_liq = re.search(r'Vl\.\s+L[ií]quido\s+da\s+Nota\s+Fiscal\s*[:\s\n]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
        if not m_liq:
            m_liq = re.search(r'Valor\s+L[ií]quido\s*(?:\(R\$\))?[:\s\n]*([\d\.,]+)', t, re.IGNORECASE)
        
        if m_liq: 
            val_liq = self._parse_valor(m_liq.group(1))
        else:
            val_liq = val_serv - (pis + cofins + inss + ir + csll + outras)

        # Identificação de ISS Retido
        iss_retido = False
        val_iss_ret = 0.0
        
        # Regra 1: Tipo de Recolhimento (Layout Barreiras e outros)
        m_tipo = re.search(r'Tipo\s+de\s+Recolhimento\s*[:\n\s]*([^\n]+)', t, re.IGNORECASE)
        if m_tipo:
            tipo = m_tipo.group(1).upper()
            if "RETIDO" in tipo:
                iss_retido = True
                val_iss_ret = iss # Usa o valor do campo ISS como retido conforme solicitado
        
        # Regra 2: Rótulo explícito de Retenção
        if not iss_retido:
            m_iss_ret = re.search(r'Reten[cç][ãa]o\s+do\s+ISSQN[:\s]*([\w\s]+)', t, re.IGNORECASE)
            if m_iss_ret:
                # Se contiver 'Retido' ou 'Sim' e NÃO contiver 'Não', marcamos como retido
                status_iss = m_iss_ret.group(1).lower()
                if ('sim' in status_iss or 'retido' in status_iss) and 'não' not in status_iss:
                    iss_retido = True
                    val_iss_ret = iss
        
        # Se o ISS for retido mas não tiver sido subtraído do val_liq calculado manualmente
        if iss_retido and not m_liq and val_liq == (val_serv - (pis + cofins + inss + ir + csll + outras)):
            val_liq -= iss

        return Valores(
            valor_servicos=val_serv,
            valor_deducoes=val_deducoes,
            valor_pis=pis,
            valor_cofins=cofins,
            valor_inss=inss,
            valor_ir=ir,
            valor_csll=csll,
            outras_retencoes=outras,
            iss_retido=iss_retido,
            valor_iss=iss,
            valor_iss_retido=val_iss_ret if iss_retido else 0.0,
            base_calculo=base if base else val_serv,
            aliquota=aliq,
            valor_liquido_nfse=val_liq
        )

    @staticmethod
    def _parse_valor(valor_str: str) -> float:
        try: return float(valor_str.replace('.', '').replace(',', '.'))
        except: return 0.0

    def _extract_via_ocr(self) -> str:
        """Tenta extrair o texto renderizando as páginas do PDF como imagens e passando pelo Tesseract."""
        try:
            import pymupdf  # PyMuPDF
            import pytesseract
            from PIL import Image
            import io
            
            import os
            # Configuração explícita para Windows (caso não esteja no PATH)
            tess_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tess_path):
                pytesseract.pytesseract.tesseract_cmd = tess_path
            
            print(f"[*] PDF '{self.pdf_path}' sem texto detectado. Iniciando extração via OCR (Tesseract)...")
            
            doc = pymupdf.open(self.pdf_path)
            full_ocr_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Aumenta a resolução para melhorar a precisão do OCR (zoom 2x)
                zoom = 2.0
                mat = pymupdf.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                # Requer que os dados do idioma português ('por') estejam instalados no Tesseract
                text = pytesseract.image_to_string(img, lang='por')
                full_ocr_text.append(text)
                
            return "\n\x0c\n".join(full_ocr_text)
        except ImportError:
            print("[AVISO] Bibliotecas de OCR (pymupdf, pytesseract, pillow) não instaladas.")
            return ""
        except Exception as e:
            print(f"[AVISO] Falha ao executar OCR (Tesseract instalado no Windows?): {e}")
            return ""

    def parse(self) -> Optional[Nfse]:
        if not self.raw_text: self.extract_raw_text()
        
        if len(self.raw_text.strip()) < 50: return None

        self.layout = self._detect_layout()
        numero = self._extrair_numero()
        codigo_verificacao = self._extrair_codigo_verificacao()
        data_emissao = self._extrair_data_emissao()
        competencia = self._extrair_competencia(data_emissao)

        prestador = self._extrair_entidade("Prestador")
        tomador   = self._extrair_entidade("Tomador")
        intermediario = self._extrair_entidade("Intermediario")
        valores   = self._extrair_valores()

        discriminacao = self._extrair_discriminacao()
        servico_codigo = self._extrair_codigo_servico()

        # Opções de regime e incentivo
        optante_simples = False
        regime_especial = None
        if re.search(r'Optante\s*[-–]?\s*Microempreendedor\s+Individual\s*\(MEI\)', self.raw_text, re.IGNORECASE):
            optante_simples = True
            regime_especial = "5" # MEI
        elif re.search(r'Optante\s*[-–]?\s*(?:Simples\s+Nacional|Microempresa|EPP|Empresa\s+de\s+Pequeno\s+Porte)', self.raw_text, re.IGNORECASE):
            optante_simples = True
            regime_especial = "6" # ME/EPP
        
        incentivador = False
        if re.search(r'Incentivador\s+Cultural\s*[:\s\n]*Sim', self.raw_text, re.IGNORECASE):
            incentivador = True

        return Nfse(
            numero=numero,
            codigo_verificacao=codigo_verificacao,
            data_emissao=data_emissao,
            competencia=competencia,
            prestador=prestador,
            tomador=tomador,
            intermediario=intermediario,
            discriminacao=discriminacao,
            servico_codigo=servico_codigo,
            valores=valores,
            optante_simples_nacional=optante_simples,
            regime_especial_tributacao=regime_especial,
            incentivador_cultural=incentivador
        )

    def parse_multiple(self) -> List[Nfse]:
        """Extrai múltiplas notas do mesmo PDF, fatiando blocos de texto por heurística de início de nota."""
        def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p
        
        full_text = extract_text(self.pdf_path)
        
        # Fallback para OCR: Se o texto for muito curto ou não contiver palavras-chave essenciais (indica PDF de imagem)
        keywords = ["PREFEITURA", "MUNICIPIO", "MUNICÍPIO", "CNPJ", "NOTA", "NFS-e", "PRESTADOR", "TOMADOR"]
        has_keywords = any(re.search(relax(k), full_text, re.IGNORECASE) for k in keywords)
        
        if len(full_text.strip()) < 200 or not has_keywords:
            full_text = self._extract_via_ocr()
        
        print(f"[*] Texto extraído ({len(full_text)} caracteres). Iniciando reconhecimento de padrões...")
        
        pages = full_text.split('\x0c')
        
        self.invalid_pages = []
        filtered_pages = []
        for idx, page in enumerate(pages, start=1):
            if re.search(self.TRASH_PATTERN, page, re.IGNORECASE):
                self.invalid_pages.append({"page": idx, "reason": "Lixo/Recibo detectado"})
                continue
            layout = self._detect_layout_page(page)
            if layout == LAYOUT_GENERICO and len(page.strip()) > 50:
                self.invalid_pages.append({"page": idx, "reason": "Layout não reconhecido"})
                continue
            if len(page.strip()) > 50:
                filtered_pages.append((page, idx))
                
        invoices_texts = []
        current_invoice = []
        
        def is_new_invoice(text: str, current_group_num: Optional[str] = None) -> bool:
            
            # Se o texto contém um divisor visual forte (muitos sublinhados/hífens)
            if re.search(r'_{20,}|={20,}|-{20,}', text):
                return True

            patterns = [
                relax("PREFEITURA"), relax("MUNICIPIO"), relax("MUNICÍPIO"), relax("NOTA CARIOCA"),
                relax("NFS-e"), relax("Nota Fiscal de Serviços"), relax("Nº da Nota Fiscal"),
                relax("DANFSe"), relax("PRESTADOR DE SERVIÇO"), relax("EMITENTE"),
                relax("DADOS DO PRESTADOR"), relax("Chave de Acesso"),
                relax("LOCALIZA RENT A CAR"), relax("FATURA / DUPLICATA"),
                relax("MUNICÍPIO DE SÃO PAULO"), relax("Prefeitura de Joinville"),
                relax("MUNICIPAL DE FORTALEZA"), relax("CONTRIBUIÇÃO SOLIDÁRIA")
            ]
            
            has_start_pattern = any(re.search(p, text, re.IGNORECASE) for p in patterns)
            
            # Se tem Número e CNPJ, é forte candidato a nova nota
            has_num_cnpj = (re.search(rf'{relax("Número")}', text, re.I) or re.search(r'N[ºo]\s+da\s+Nota', text, re.I)) and \
                           (re.search(rf'{relax("CNPJ")}', text, re.I) or re.search(rf'{relax("Prestador")}', text, re.I))
            
            # Se não tem o padrão de início, provavelmente é continuação
            if not has_start_pattern and not has_num_cnpj:
                return False

            # Prioridade: Se temos o número da nota atual e conseguimos extrair o número desta página, comparamos.
            # Se for o mesmo número, é continuação (mesmo tendo cabeçalho repetido).
            if current_group_num:
                m_prox = re.search(r'(?:N[uú]mero|N[ºo]).*?(\d+)', text, re.I)
                if m_prox and m_prox.group(1) == current_group_num:
                    return False

            return has_start_pattern or has_num_cnpj

        is_localiza = False
        current_num = None

        # Processamento granular: quebra páginas que contêm múltiplas notas (divisores internos ou novos cabeçalhos)
        granular_blocks = []
        for page_text, page_idx in filtered_pages:
            # 1. Quebra por divisores visuais (linhas horizontais de OCR)
            parts = re.split(r'(?=\n_{20,}|\n={20,}|\n-{20,})', page_text)
            
            # 2. Quebra por cabeçalhos conhecidos se aparecerem colados no texto
            # Usamos lookahead para não consumir o cabeçalho no split
            headers_regex = r'(?=\n\s*\bDANFSe\b)'
            
            final_parts = []
            for p in parts:
                sub_parts = re.split(headers_regex, p, flags=re.I)
                final_parts.extend([(sp, page_idx) for sp in sub_parts if len(sp.strip()) > 50])
            
            granular_blocks.extend(final_parts)

        for block_text, page_idx in granular_blocks:
            # Tenta identificar o número da nota no bloco atual (suporta Número e Nº)
            num_match = re.search(r'(?:N[uú]mero|N[ºo]).*?(\d+)', block_text, re.I)
            block_num = num_match.group(1) if num_match else None

            if is_new_invoice(block_text, current_num):
                if current_invoice:
                    invoices_texts.append(("\n\x0c\n".join([c[0] for c in current_invoice]), current_invoice[0][1]))
                    current_invoice = []
                current_invoice.append((block_text, page_idx))
                current_num = block_num
                # Verifica se a nota que acabou de iniciar é da Localiza
                is_localiza = bool(re.search(r'LOCALIZA RENT A CAR S/A|FATURA\s*/\s*DUPLICATA', block_text, re.IGNORECASE))
            else:
                if not is_localiza:
                    current_invoice.append((block_text, page_idx))
                    if block_num: current_num = block_num
                    
        if current_invoice:
            invoices_texts.append(("\n\x0c\n".join([c[0] for c in current_invoice]), current_invoice[0][1]))
            
        results = []
        seen_numbers = set()
        
        for text_block, page_idx in invoices_texts:
            if len(text_block.strip()) < 50: continue
            
            sub_ext = SPPdfExtractor(self.pdf_path)
            sub_ext.raw_text = text_block
            
            try:
                nfse = sub_ext.parse()
                if not nfse: continue
                
                # Trava contra Lixo Residual (Páginas processadas que não são notas)
                if nfse.numero == '00000000' and nfse.prestador.cnpj_cpf.startswith('00000000000'):
                    continue
                
                # Evita duplicidade se o fatiamento falhou e pegou a mesma nota duas vezes
                # ou se a nota tem múltiplas páginas e o fatiamento não as uniu
                key = f"{nfse.numero}_{nfse.prestador.cnpj_cpf}"
                if key in seen_numbers and nfse.numero != '00000000':
                    continue
                
                nfse.pagina_origem = page_idx
                seen_numbers.add(key)
                results.append(nfse)
            except Exception as e:
                print(f"[EXTRACTOR ERROR] Problema ao fatiar nota do lote: {e}")
                
        return results

# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _parse_dmy(data_str: str, hora_str: Optional[str] = None) -> Optional[datetime]:
    try:
        dia, mes, ano = data_str.strip().split('/')
        if hora_str:
            ph = hora_str.strip().split(':')
            h, m = int(ph[0]), int(ph[1])
            s = int(ph[2]) if len(ph) > 2 else 0
            return datetime(int(ano), int(mes), int(dia), h, m, s)
        return datetime(int(ano), int(mes), int(dia))
    except: return None

def _extrair_competencia_generica(texto: str) -> Optional[datetime]:
    # Prioridade 1: Data completa DD/MM/YYYY
    m = re.search(r'(?:Compet[eê]ncia|Refer[eê]ncia|Fato\s*Gerador)[:\s]+(\d{2}/\d{2}/\d{4})', texto, re.I)
    if m: return _parse_dmy(m.group(1))

    # Prioridade 2: MM/YYYY
    m = re.search(r'(?:Compet[eê]ncia|Refer[eê]ncia|Fato\s*Gerador)[:\s]+(\d{1,2})/(\d{4})', texto, re.I)
    if m: return datetime(int(m.group(2)), int(m.group(1)), 1)

    # Prioridade 3: Mês por extenso
    m = re.search(r'(?:Compet[eê]ncia|Refer[eê]ncia|Fato\s*Gerador)[:\s]+([a-záéíóúâêôãõç]+)(?:/|\s+de\s+)(\d{4})', texto, re.I)
    if m:
        mes = _MESES_PT.get(m.group(1).lower())
        if mes: return datetime(int(m.group(2)), mes, 1)
    return None
