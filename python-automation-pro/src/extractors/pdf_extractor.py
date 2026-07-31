"""
Extrator de NFS-e em PDF — suporte a múltiplos layouts municipais.

Layouts detectados automaticamente:
  A — Cuiabá/MT (ISSNet):       "Data de Competência"
  B — Barreiras/BA:              "Data Fato Gerador"
  C — Camaçari/BA (CPqD):       "Data da prestação do serviço"
  D — NFS-e Nacional (DANFSe):  "Competência da NFS-e"
  E — Genérico/SP (ABRASF):     "Competência" MM/YYYY ou mês extenso
  ? — Imagem/Scan:               texto vazio → aviso de OCR necessário
  F — Telecom (NF-e mod. 22):    "NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA"
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
LAYOUT_BRASILIA  = 'brasilia_df'      # Brasília/DF (Governo do DF)
LAYOUT_ISBET     = 'isbet_recibo'     # ISBET (Nota de Contribuição)
LAYOUT_SIMOES_FILHO = 'simoes_filho_ba'  # Simões Filho/BA
LAYOUT_RIBEIRAO_PIRES = 'ribeirao_pires_sp' # Ribeirão Pires/SP
LAYOUT_CPE_LOCACAO = 'cpe_locacao'    # CPE Tecnologia (Fatura de Locação)
LAYOUT_GUINCHO_CIDADE = 'guincho_cidade' # Guincho Cidade Eireli (Fatura de Locação)
LAYOUT_BF_AMBIENTAIS = 'bf_ambientais' # B.F. Serviços Ambientais (Fatura de Locação)
LAYOUT_LMR_ENGENHARIA = 'lmr_engenharia' # LMR Engenharia e Construção (Fatura de Locação)
LAYOUT_GERACAO_ENERGIA = 'geracao_energia' # Geração & Energia (Fatura de Locação)
LAYOUT_LOCONTAINERS = 'locontainers' # Locontainers (Vidal Locação de Containers)
LAYOUT_TELECOM_COMUNICACAO = 'telecom_comunicacao' # NF-e Fatura de Serviço de Comunicação Eletrônica
LAYOUT_OSASCO_REPASSE = 'osasco_nfr_repasse' # Osasco/SP - Nota Fiscal Eletrônica de Repasse (NF-R), ex: iFood Benefícios
LAYOUT_CAMPINAS  = 'campinas_sp'      # Campinas/SP - "NFSe Campinas" (Secretaria Municipal de Finanças)
LAYOUT_LAURO_FREITAS = 'lauro_de_freitas_ba' # Lauro de Freitas/BA
LAYOUT_SULSEG_COBRANCA = 'sulseg_cobranca'  # SUL&SEG - Nota de Cobrança de Locação (não sujeita a ISS)
LAYOUT_PASSWORD_ENOTAS = 'password_enotas'  # PASSWORD Sistemas Eletronicos (NFS-e eNotas Gateway, Lauro de Freitas/BA)
LAYOUT_FATURA_LOCACAO_GENERICA = 'fatura_locacao_generica'  # Fatura de Locação genérica (locação de bens móveis, não sujeita a ISS) — locadora/locatário parseados do texto
LAYOUT_ARMAC_LOCACAO = 'armac_locacao'  # ARMAC Locação (CNPJ 00.242.184) - Fatura de Locação escaneada, tabela multi-item, OCR zoom4/PSM6
LAYOUT_IACU_NFSE = 'iacu_nfse'  # Prefeitura Municipal de Iaçu/BA (plataforma nfservico.com.br) - NFS-e tributada, escaneada; caixa de cabeçalho via recorte dedicado
LAYOUT_SAO_PAULO_2 = 'sao_paulo_sp_scan'  # São Paulo/SP ESCANEADO (JPG/foto -> OCR) - mesmo cabeçalho do LAYOUT_SAO_PAULO digital, mas via OCR ruidoso; caixa de cabeçalho via recorte dedicado
LAYOUT_CAMACARI_2 = 'camacari_ba_scan'  # Camaçari/BA ESCANEADO (foto/JPG -> OCR) - mesmo cabeçalho do LAYOUT_CAMACARI, gated por from_ocr; SUPERSET (herda os branches do CAMACARI como fallback) + tratamento próprio: re-OCR zoom4/PSM6, recorte de cabeçalho, grade com alíquota↔ISS trocados e ISS calculado, correção do 1º dígito do CNPJ do tomador
LAYOUT_MATA_SAO_JOAO = 'mata_sao_joao_ba'  # Mata de São João/BA (plataforma SAATRI - matadesaojoao.saatri.com.br) - NFS-e tributada, escaneada de boa qualidade (OCR zoom3 limpo, sem rotação); layout dedicado do município. Estrutura: blocos "Prestador/Tomador do(s) Serviço(s)" contíguos, grade de valores rótulo-em-cima/valor-embaixo, código de serviço "01.01.01" (item LC 116) -> 4 dígitos
LAYOUT_ROSARIO_LIMEIRA = 'rosario_da_limeira_mg'  # Rosário da Limeira/MG (plataforma FUTURIZE) - NFS-e tributada DIGITAL (pdfminer limpo, sem OCR); layout dedicado do município. Blocos "PRESTADOR/TOMADOR DE SERVIÇOS" com rótulos por linha; endereço em linha única "logradouro - [extras] - bairro - CEP - município - UF"; código "Trib. Nacional 09.01.04" (item LC 116) -> 4 dígitos. Nota "fora do município" (prestação em outra cidade) mantém município do prestador na incidência (decisão do usuário)
LAYOUT_CAMACARI_AVULSA = 'camacari_ba_avulsa'  # Camaçari/BA - NOTA FISCAL DE PRESTAÇÃO DE SERVIÇOS (AVULSA) Série "A", emitida pela própria Prefeitura, escaneada (OCR). Distinta das notas Camaçari via CPqD (LAYOUT_CAMACARI/CAMACARI_2): blocos "IDENTIFICAÇÃO DO PRESTADOR/TOMADOR" com rótulos "Nome / Razão", "CPF / CNPJ:", "CEP: ... Município: ... UF:", "Logradouro: ... Nº ...", "Bairro: ...". Valores CONFIÁVEIS vêm da camada DIGITAL (pdfminer): o OCR troca o 1º dígito do VALOR TRIBUTÁVEL (14.685->74.685) e deixa o VALOR LÍQUIDO em branco. Detecção casa AVULSA + CAMAÇARI (precede o bloco CPqD)
LAYOUT_FF_LOCACAO = 'ff_locacao'  # F&F Comércio e Serviços de Telecomunicações de Segurança Eletrônica LTDA (Fatura de Locação de CFTV), escaneada. Detecção por CNPJ do emissor (13.398.812/0001-89), não pela frase "FATURA DE LOCAÇÃO" - o layout de 2 colunas do OCR quebra essa frase (intercalada com o nome da empresa). Campo "VALOR TOTAL DA FATURA" da nota-fonte traz um placeholder de template não substituído ("#venda_valor_total#") - valor real vem da tabela de itens (coluna "Valor Liquido")


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
    'Dados do Intermediário de Serviços', 'Intermediário do Serviço',
    'INTERMEDIÁRIO DO SERVIÇO', 'Intermediário',
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
        # Sinaliza que _extrair_data_emissao não achou nenhuma data no
        # documento e caiu no fallback de "agora" — usado por parse() para
        # gerar um aviso de baixa confiança em vez de mascarar o problema.
        self._data_emissao_fallback = False
        # Sinaliza que o texto veio de OCR (PDF imagem/escaneado), não de texto
        # embutido (pdfminer). Usado para distinguir layouts que existem em duas
        # origens — ex.: SP digital (LAYOUT_SAO_PAULO) vs SP escaneado
        # (LAYOUT_SAO_PAULO_2) compartilham o mesmo cabeçalho, mas só o segundo
        # passa por OCR.
        self.from_ocr = False
        # Ângulo (0/90/180/270) escolhido pelo _ocr_page ao corrigir a rotação
        # de fotos/scans — reaproveitado por recortes dedicados (ex.: caixa de
        # cabeçalho do SP2) para renderizar a região na mesma orientação.
        self._ocr_rotation = 0

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
        if re.search(r'NOTA\s+DE\s+COBRAN[ÇC]A', t, re.IGNORECASE) and re.search(r'18\.?294\.?792', t):
            return LAYOUT_SULSEG_COBRANCA
        # PASSWORD/eNotas: detecção específica do emitente (CNPJ 04.021.023 ou
        # razão social), conforme decidido — não casar por marca genérica do
        # gateway "eNotas" para evitar colisão com futuras notas de outros
        # emitentes que usem o mesmo provedor.
        if re.search(r'04\.?021\.?023[./]?0001-?33|PASSWORD\s*[-–]\s*SISTEMAS\s+ELETR', t, re.IGNORECASE):
            return LAYOUT_PASSWORD_ENOTAS
        if re.search(r'00\.111\.704|00111704|VIDAL\s+LOCA|LOCONTAINERS', t, re.IGNORECASE):
            return LAYOUT_LOCONTAINERS
        if re.search(r'03\.292\.008/0001-67|03\.292\.008', t, re.IGNORECASE):
            return LAYOUT_GERACAO_ENERGIA
        if re.search(r'LMR\s+ENGENHARIA|LTR\s+ENGENHARIA|L\.M\.R\.\s+ENGENHARIA', t, re.IGNORECASE):
            return LAYOUT_LMR_ENGENHARIA
        # F&F Comércio (fatura de locação de CFTV) - detectado pelo CNPJ do
        # emissor, não pela frase "FATURA DE LOCAÇÃO": o layout de 2 colunas do
        # OCR quebra essa frase (intercalada com o nome da empresa em linhas
        # separadas), então a marca genérica de locação nunca casa nesta nota.
        if re.search(r'13\.?398\.?812[/.]?0001-?89', t, re.IGNORECASE):
            return LAYOUT_FF_LOCACAO
        if re.search(r'CPE BAHIA|cpe tecnologia', t, re.IGNORECASE):
            return LAYOUT_CPE_LOCACAO
        if re.search(r'GUINCHO CIDADE', t, re.IGNORECASE):
            return LAYOUT_GUINCHO_CIDADE
        if re.search(r'B\.F\.\s*SERVICOS\s*AMBIENTAIS|B\.F\.\s*SERVIÇOS\s*AMBIENTAIS', t, re.IGNORECASE):
            return LAYOUT_BF_AMBIENTAIS
        if re.search(r'Prefeitura Municipal de Cuiab[aá]|ISSNet', t, re.IGNORECASE):
            return LAYOUT_CUIABA
        if re.search(r'Data\s+Fato\s+Gerador', t, re.IGNORECASE):
            return LAYOUT_BARREIRAS
        # Camaçari/BA - NOTA FISCAL DE PRESTAÇÃO DE SERVIÇOS (AVULSA), emitida
        # pela própria Prefeitura (Série "A"), escaneada. PRECEDE o bloco Camaçari
        # CPqD porque compartilha "CAMAÇARI" no cabeçalho, mas a estrutura (blocos
        # IDENTIFICAÇÃO DO PRESTADOR/TOMADOR, grade de valores própria) é distinta.
        # O OCR quebra "PREFEITURA MUNICIPAL DE" e "CAMAÇARI" em linhas separadas,
        # por isso casamos "AVULSA" + "CAMAÇARI" (a marca AVULSA não aparece nas
        # notas CPqD digitais/escaneadas, então não há falso positivo com elas).
        if re.search(r'\bAVULSA\b', t, re.IGNORECASE) and re.search(r'CAMA[CÇ]ARI', t, re.IGNORECASE):
            return LAYOUT_CAMACARI_AVULSA
        if re.search(r'CPqD\s*[-–]\s*Gest[aã]o\s+P[uú]blica|PREFEITURA\s+MUNICIPAL\s+DE\s+CAMA[CÇ]ARI', t, re.IGNORECASE):
            # Mesmo cabeçalho para o Camaçari digital (texto embutido) e o
            # escaneado (foto/JPG -> OCR). Diferente do SP2, o LAYOUT_CAMACARI
            # já tratava notas escaneadas; por isso o LAYOUT_CAMACARI_2 é um
            # SUPERSET (herda os branches do CAMACARI como fallback) e só é
            # roteado quando o texto veio de OCR — o digital continua intocado.
            return LAYOUT_CAMACARI_2 if getattr(self, 'from_ocr', False) else LAYOUT_CAMACARI
        if re.search(r'PREFEITURA.*SALVADOR|Xique-Xique', t, re.IGNORECASE):
            return LAYOUT_SALVADOR # Ou um layout genérico da BA
        if re.search(r'FEIRA DE SANTANA', t, re.IGNORECASE):
            return LAYOUT_FEIRA
        if re.search(r'MUNIC[IÍ]PIO\s+DE\s+LAURO\s+DE\s+FREITAS|laurodefreitas\.ba\.gov\.br', t, re.IGNORECASE):
            return LAYOUT_LAURO_FREITAS
        # Mata de São João/BA (plataforma SAATRI) — específico do município
        # (decidido com o usuário: NÃO casar só por "saatri.com.br" para evitar
        # rotear outras prefeituras SAATRI ainda não testadas). O "ã" pode sair
        # corrompido no OCR, por isso toleramos [ãa]. Precede layouts genéricos.
        if re.search(r'Mata\s+de\s+S[ãa]o\s+Jo[ãa]o', t, re.IGNORECASE) or re.search(r'matadesaojoao\.saatri', t, re.IGNORECASE):
            return LAYOUT_MATA_SAO_JOAO
        # Rosário da Limeira/MG (plataforma FUTURIZE) — específico do município
        # (decidido com o usuário: NÃO casar por "FUTURIZE" para não rotear
        # outras prefeituras da mesma plataforma ainda não testadas).
        if re.search(r'ROS[ÁA]RIO\s+DA\s+LIMEIRA', t, re.IGNORECASE):
            return LAYOUT_ROSARIO_LIMEIRA
        if re.search(r'RIO DE JANEIRO|NOTA CARIOCA', t, re.IGNORECASE):
            return LAYOUT_RIO
        if re.search(r'LOCALIZA RENT A CAR S/A|FATURA\s*/\s*DUPLICATA', t, re.IGNORECASE):
            return LAYOUT_LOCALIZA
        if re.search(r'PREFEITURA DO MUNIC[IÍ]PIO DE S[AÃ]O PAULO', t, re.IGNORECASE):
            # Mesmo cabeçalho para o SP digital (texto embutido) e o SP
            # escaneado (JPG/foto -> OCR). Só o escaneado passa por OCR, e sua
            # estrutura textual (2 colunas ruidosas, caixa de cabeçalho densa)
            # exige regras próprias — roteia para LAYOUT_SAO_PAULO_2 sem tocar
            # no layout digital, que continua 100% intacto.
            return LAYOUT_SAO_PAULO_2 if getattr(self, 'from_ocr', False) else LAYOUT_SAO_PAULO
        if re.search(r'Prefeitura de Joinville|NF-em', t, re.IGNORECASE):
            return LAYOUT_JOINVILLE
        if re.search(r'PREFEITURA MUNICIPAL DE FORTALEZA', t, re.IGNORECASE):
            return LAYOUT_FORTALEZA
        if re.search(r'Governo do Distrito Federal|Secretária de Estado de Economia do Distrito Federal|Coordenação do ISS', t, re.IGNORECASE):
            return LAYOUT_BRASILIA
        if re.search(r'NOTA DE CONTRIBUIÇÃO SOLIDÁRIA|ISBET', t, re.IGNORECASE):
            return LAYOUT_ISBET
        if re.search(r'Sim[oõ]es Filho', t, re.IGNORECASE):
            return LAYOUT_SIMOES_FILHO
        if re.search(r'Ribeir[aã]o Pires', t, re.IGNORECASE):
            return LAYOUT_RIBEIRAO_PIRES
        if re.search(r'NOTA\s+FISCAL\s+DE\s+FATURA\s+DE\s+SERVI[CÇ]O\s+DE\s+COMUNICA[CÇ][AÃ]O', t, re.IGNORECASE):
            return LAYOUT_TELECOM_COMUNICACAO
        if re.search(r'Nota\s+Fiscal\s+Eletr[oô]nica\s+de\s+(?:Servi[cç]os\s+)?Repasse|nfe\.osasco\.(?:sp\.)?gov\.br', t, re.IGNORECASE):
            return LAYOUT_OSASCO_REPASSE
        if re.search(r'NFSe\s+Campinas|Prefeitura\s+Municipal\s+Campinas|Nota\s+Fiscal\s+de\s+Servi[cç]os\s+eletr[oôó0]nica\s+de\s+Campinas', t, re.IGNORECASE):
            return LAYOUT_CAMPINAS
        if re.search(r'DANFSe\s+v\d|Compet[eê]ncia\s+da\s+NFS-e|Data\s+de\s+Compet[eê]ncia|Chave\s+de\s+Acesso', t, re.IGNORECASE | re.DOTALL):
            return LAYOUT_NACIONAL
        # Iaçu/BA (plataforma nfservico.com.br) — específico do município (decidido
        # com o usuário: NÃO casar por marca genérica da plataforma para evitar
        # colisão com outros municípios do mesmo SaaS). O "ç" de IAÇU pode sair
        # corrompido no OCR ("IA?U"), então toleramos até 2 chars entre "IA" e "U".
        if re.search(r'PREFEITURA\s+MUNICIPAL\s+DE\s+IA.{0,2}U\b', t, re.IGNORECASE) or re.search(r'nfservico\.com\.br\S*iacu', t, re.IGNORECASE):
            return LAYOUT_IACU_NFSE
        # ARMAC (locadora específica, fatura escaneada) — precede o genérico de
        # locação por ter estrutura própria (blocos "Dados do Locador/Tomador",
        # tabela multi-item) que exige extração dedicada + re-OCR em zoom alto.
        if re.search(r'00\.?242\.?184', t) or (re.search(r'\bARMAC\b', t, re.IGNORECASE) and re.search(r'FATURA\s+DE\s+LOCA[ÇC][ÃA]O', t, re.IGNORECASE)):
            return LAYOUT_ARMAC_LOCACAO
        # Fatura de Locação genérica: DEVE ficar por último, depois de todos os
        # emitentes específicos de locação (CPE, Guincho, BF, LMR, Geração,
        # Locontainers, SUL&SEG, ARMAC) e de todos os layouts municipais — cada
        # um desses ganha por marca própria; só cai aqui uma fatura de locação de
        # locadora ainda não catalogada (ex.: LOC BAHIA). Ver gotcha Forma A
        # (ordem da cadeia de detecção).
        if re.search(r'FATURA\s+DE\s+LOCA[ÇC][ÃA]O', t, re.IGNORECASE):
            return LAYOUT_FATURA_LOCACAO_GENERICA
        return LAYOUT_GENERICO

    def _detect_layout_page(self, page_text: str) -> str:
        """Detect layout for a single page's text.
        Returns a layout constant or LAYOUT_GENERICO if none match.
        """
        t = page_text
        if re.search(r'NOTA\s+DE\s+COBRAN[ÇC]A', t, re.IGNORECASE) and re.search(r'18\.?294\.?792', t):
            return LAYOUT_SULSEG_COBRANCA
        if re.search(r'04\.?021\.?023[./]?0001-?33|PASSWORD\s*[-–]\s*SISTEMAS\s+ELETR', t, re.IGNORECASE):
            return LAYOUT_PASSWORD_ENOTAS
        if re.search(r'00\.111\.704|00111704|VIDAL\s+LOCA|LOCONTAINERS', t, re.IGNORECASE):
            return LAYOUT_LOCONTAINERS
        if re.search(r'03\.292\.008/0001-67|03\.292\.008', t, re.IGNORECASE):
            return LAYOUT_GERACAO_ENERGIA
        if re.search(r'LMR\s+ENGENHARIA|LTR\s+ENGENHARIA|L\.M\.R\.\s+ENGENHARIA', t, re.IGNORECASE):
            return LAYOUT_LMR_ENGENHARIA
        # F&F Comércio (fatura de locação de CFTV) - detectado pelo CNPJ do
        # emissor, não pela frase "FATURA DE LOCAÇÃO": o layout de 2 colunas do
        # OCR quebra essa frase (intercalada com o nome da empresa em linhas
        # separadas), então a marca genérica de locação nunca casa nesta nota.
        if re.search(r'13\.?398\.?812[/.]?0001-?89', t, re.IGNORECASE):
            return LAYOUT_FF_LOCACAO
        if re.search(r'CPE BAHIA|cpe tecnologia', t, re.IGNORECASE):
            return LAYOUT_CPE_LOCACAO
        if re.search(r'GUINCHO CIDADE', t, re.IGNORECASE):
            return LAYOUT_GUINCHO_CIDADE
        if re.search(r'B\.F\.\s*SERVICOS\s*AMBIENTAIS|B\.F\.\s*SERVIÇOS\s*AMBIENTAIS', t, re.IGNORECASE):
            return LAYOUT_BF_AMBIENTAIS
        if re.search(r'Prefeitura Municipal de Cuiab[aá]|ISSNet', t, re.IGNORECASE):
            return LAYOUT_CUIABA
        if re.search(r'Data\s+Fato\s+Gerador|MUNICIPIO\s+DE\s+BARREIRAS', t, re.IGNORECASE):
            return LAYOUT_BARREIRAS
        # Camaçari/BA - NOTA FISCAL DE PRESTAÇÃO DE SERVIÇOS (AVULSA), emitida
        # pela própria Prefeitura (Série "A"), escaneada. PRECEDE o bloco Camaçari
        # CPqD porque compartilha "CAMAÇARI" no cabeçalho, mas a estrutura (blocos
        # IDENTIFICAÇÃO DO PRESTADOR/TOMADOR, grade de valores própria) é distinta.
        # O OCR quebra "PREFEITURA MUNICIPAL DE" e "CAMAÇARI" em linhas separadas,
        # por isso casamos "AVULSA" + "CAMAÇARI" (a marca AVULSA não aparece nas
        # notas CPqD digitais/escaneadas, então não há falso positivo com elas).
        if re.search(r'\bAVULSA\b', t, re.IGNORECASE) and re.search(r'CAMA[CÇ]ARI', t, re.IGNORECASE):
            return LAYOUT_CAMACARI_AVULSA
        if re.search(r'CPqD\s*[-–]\s*Gest[aã]o\s+P[uú]blica|PREFEITURA\s+MUNICIPAL\s+DE\s+CAMA[CÇ]ARI', t, re.IGNORECASE):
            # Mesmo cabeçalho para o Camaçari digital (texto embutido) e o
            # escaneado (foto/JPG -> OCR). Diferente do SP2, o LAYOUT_CAMACARI
            # já tratava notas escaneadas; por isso o LAYOUT_CAMACARI_2 é um
            # SUPERSET (herda os branches do CAMACARI como fallback) e só é
            # roteado quando o texto veio de OCR — o digital continua intocado.
            return LAYOUT_CAMACARI_2 if getattr(self, 'from_ocr', False) else LAYOUT_CAMACARI
        if re.search(r'PREFEITURA.*SALVADOR|Xique-Xique', t, re.IGNORECASE):
            return LAYOUT_SALVADOR
        if re.search(r'FEIRA DE SANTANA', t, re.IGNORECASE):
            return LAYOUT_FEIRA
        if re.search(r'MUNIC[IÍ]PIO\s+DE\s+LAURO\s+DE\s+FREITAS|laurodefreitas\.ba\.gov\.br', t, re.IGNORECASE):
            return LAYOUT_LAURO_FREITAS
        # Mata de São João/BA (plataforma SAATRI) — específico do município.
        if re.search(r'Mata\s+de\s+S[ãa]o\s+Jo[ãa]o', t, re.IGNORECASE) or re.search(r'matadesaojoao\.saatri', t, re.IGNORECASE):
            return LAYOUT_MATA_SAO_JOAO
        # Rosário da Limeira/MG (plataforma FUTURIZE) — específico do município
        # (decidido com o usuário: NÃO casar por "FUTURIZE" para não rotear
        # outras prefeituras da mesma plataforma ainda não testadas).
        if re.search(r'ROS[ÁA]RIO\s+DA\s+LIMEIRA', t, re.IGNORECASE):
            return LAYOUT_ROSARIO_LIMEIRA
        if re.search(r'RIO DE JANEIRO|NOTA CARIOCA', t, re.IGNORECASE):
            return LAYOUT_RIO
        if re.search(r'LOCALIZA RENT A CAR S/A|FATURA\s*/\s*DUPLICATA', t, re.IGNORECASE):
            return LAYOUT_LOCALIZA
        if re.search(r'PREFEITURA DO MUNIC[IÍ]PIO DE S[AÃ]O PAULO', t, re.IGNORECASE):
            # Mesmo cabeçalho para o SP digital (texto embutido) e o SP
            # escaneado (JPG/foto -> OCR). Só o escaneado passa por OCR, e sua
            # estrutura textual (2 colunas ruidosas, caixa de cabeçalho densa)
            # exige regras próprias — roteia para LAYOUT_SAO_PAULO_2 sem tocar
            # no layout digital, que continua 100% intacto.
            return LAYOUT_SAO_PAULO_2 if getattr(self, 'from_ocr', False) else LAYOUT_SAO_PAULO
        if re.search(r'Prefeitura de Joinville|NF-em', t, re.IGNORECASE):
            return LAYOUT_JOINVILLE
        if re.search(r'PREFEITURA MUNICIPAL DE FORTALEZA', t, re.IGNORECASE):
            return LAYOUT_FORTALEZA
        if re.search(r'Governo do Distrito Federal|Secretária de Estado de Economia do Distrito Federal|Coordenação do ISS', t, re.IGNORECASE):
            return LAYOUT_BRASILIA
        if re.search(r'NOTA DE CONTRIBUIÇÃO SOLIDÁRIA|ISBET', t, re.IGNORECASE):
            return LAYOUT_ISBET
        if re.search(r'Sim[oõ]es Filho', t, re.IGNORECASE):
            return LAYOUT_SIMOES_FILHO
        if re.search(r'Ribeir[aã]o Pires', t, re.IGNORECASE):
            return LAYOUT_RIBEIRAO_PIRES
        if re.search(r'NOTA\s+FISCAL\s+DE\s+FATURA\s+DE\s+SERVI[CÇ]O\s+DE\s+COMUNICA[CÇ][AÃ]O', t, re.IGNORECASE):
            return LAYOUT_TELECOM_COMUNICACAO
        if re.search(r'Nota\s+Fiscal\s+Eletr[oô]nica\s+de\s+(?:Servi[cç]os\s+)?Repasse|nfe\.osasco\.(?:sp\.)?gov\.br', t, re.IGNORECASE):
            return LAYOUT_OSASCO_REPASSE
        if re.search(r'NFSe\s+Campinas|Prefeitura\s+Municipal\s+Campinas|Nota\s+Fiscal\s+de\s+Servi[cç]os\s+eletr[oôó0]nica\s+de\s+Campinas', t, re.IGNORECASE):
            return LAYOUT_CAMPINAS
        if re.search(r'DANFSe\s+v\d|Compet[eê]ncia\s+da\s+NFS-e|Data\s+de\s+Compet[eê]ncia|Chave\s+de\s+Acesso', t, re.IGNORECASE | re.DOTALL):
            return LAYOUT_NACIONAL
        if re.search(r'PREFEITURA\s+MUNICIPAL\s+DE\s+IA.{0,2}U\b', t, re.IGNORECASE) or re.search(r'nfservico\.com\.br\S*iacu', t, re.IGNORECASE):
            return LAYOUT_IACU_NFSE
        if re.search(r'00\.?242\.?184', t) or (re.search(r'\bARMAC\b', t, re.IGNORECASE) and re.search(r'FATURA\s+DE\s+LOCA[ÇC][ÃA]O', t, re.IGNORECASE)):
            return LAYOUT_ARMAC_LOCACAO
        if re.search(r'FATURA\s+DE\s+LOCA[ÇC][ÃA]O', t, re.IGNORECASE):
            return LAYOUT_FATURA_LOCACAO_GENERICA
        return LAYOUT_GENERICO

    # ------------------------------------------------------------------
    # Extração de competência por layout
    # ------------------------------------------------------------------

    def _extrair_competencia(self, data_emissao: datetime) -> datetime:
        t = self.raw_text
        layout = self.layout or LAYOUT_GENERICO
        result: Optional[datetime] = None

        if layout == LAYOUT_CPE_LOCACAO:
            m = re.search(r'Data\s+de\s*(?:Incri[cç][aã]o|Inscri[cç][aã]o|[:\s\n])*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_GUINCHO_CIDADE:
            m = re.search(r'Emiss[aã]o\s*[:\s\n]*(\d{2}[./]\d{2}[./]\d{4})', t, re.IGNORECASE)
            if m:
                clean_date = m.group(1).replace('.', '/')
                result = _parse_dmy(clean_date) or None
        elif layout == LAYOUT_BF_AMBIENTAIS:
            m = re.search(r'Emiss[aã]o\s*[:\s\n]*.*?(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if not m:
                m = re.search(r'Salvador\s*\(BA\),\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})', t, re.IGNORECASE)
            if m:
                parsed_dt = self._parse_data_extenso(m.group(1)) if 'de' in m.group(1) else _parse_dmy(m.group(1))
                if parsed_dt: result = parsed_dt
        elif layout == LAYOUT_LMR_ENGENHARIA:
            m = re.search(r'DATA\s+DA\s+EMISS[AÃ]O\s*[:\s\n]*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_GERACAO_ENERGIA:
            m = re.search(r'(\d{2}/\d{2}/\d{4})', t)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_LOCONTAINERS:
            m = re.search(r'DATA\s+DA\s+EMISS[AÃÕO]*\s*[\n\r\s]+(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_CUIABA:
            m = re.search(r'Data\s+de\s+Compet[eê]ncia\s*\n\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_BARREIRAS:
            m = re.search(r'Data\s+Fato\s+Gerador\s*\n\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_CAMACARI:
            m = re.search(r'Data\s+da\s+presta[cç][aã]o\s+do\s+servi[cç]o\s*:\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m: result = _parse_dmy(m.group(1)) or None
        elif layout == LAYOUT_MATA_SAO_JOAO:
            # "Data do Fato Gerador\n25/05/2026" — a competência é o mês do fato gerador.
            m = re.search(r'Data\s+do\s+Fato\s+Gerador\s*\n\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: result = datetime(res.year, res.month, 1)
        elif layout == LAYOUT_ROSARIO_LIMEIRA:
            # "Período de Competência: 06/2026" (mês/ano).
            m = re.search(r'Per[ií]odo\s+de\s+Compet[eê]ncia\s*:\s*(\d{2})/(\d{4})', t, re.IGNORECASE)
            if m:
                try:
                    result = datetime(int(m.group(2)), int(m.group(1)), 1)
                except ValueError:
                    result = None
        elif layout == LAYOUT_CAMACARI_AVULSA:
            # Não há campo de competência próprio; usamos o mês da data de
            # prestação (data_emissao já resolvida a partir de "DATA DE PRESTAÇÃO").
            result = datetime(data_emissao.year, data_emissao.month, 1)
        elif layout == LAYOUT_TELECOM_COMUNICACAO:
            # Campo "REFERÊNCIA (ANO/MÊS): 2026/06" ou "REFERÊNCIA: 2026/06"
            m = re.search(r'REFER[EÊ]NCIA\s*(?:\([^)]*\))?\s*[:\s]+(\d{4})/(\d{2})', t, re.IGNORECASE)
            if m:
                try:
                    result = datetime(int(m.group(1)), int(m.group(2)), 1)
                except ValueError:
                    result = None
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
        elif layout == LAYOUT_IACU_NFSE:
            # "- COMPETÊNCIA: 07/2026 (mês/ano)"
            m = re.search(r'COMPET[EÊ]NCIA\s*:?\s*(\d{2})/(\d{4})', t, re.IGNORECASE)
            if m:
                try:
                    result = datetime(int(m.group(2)), int(m.group(1)), 1)
                except ValueError:
                    result = None
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
                    mes = _MESES_PT.get(mes_str.lower()[:3], 1)
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
        elif layout == LAYOUT_OSASCO_REPASSE:
            # "Ref. Fiscal 06/2026" (cabeçalho) — rótulo não reconhecido pelo
            # fallback genérico, que só busca "Competência"/"Referência"/"Fato Gerador".
            m = re.search(r'Ref\.?\s*Fiscal\s*:?\s*(\d{1,2})/(\d{4})', t, re.IGNORECASE)
            if m:
                try:
                    result = datetime(int(m.group(2)), int(m.group(1)), 1)
                except ValueError:
                    result = None

        if result is None: result = _extrair_competencia_generica(t)
        if result is None: result = datetime(data_emissao.year, data_emissao.month, 1)
        return result

    def _extrair_data_emissao(self) -> datetime:
        t = self.raw_text
        self._data_emissao_fallback = False
        if self.layout == LAYOUT_ARMAC_LOCACAO:
            # "Data Documento: | 10.07.2026" (datas com ponto no OCR da ARMAC).
            m = re.search(r'Data\s+Documento\s*:?\s*\|?\s*(\d{2}[./]\d{2}[./]\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1).replace('.', '/'))
                if res: return res

        if self.layout == LAYOUT_IACU_NFSE:
            # "Data e hora de Emissão:\n\n10/07/2026 16:37:22" (recorte do cabeçalho).
            m = re.search(r'Data\s+e\s+hora\s+de\s+Emiss[aã]o\s*:?\s*[\n\s]*(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1), m.group(2))
                if res: return res

        if self.layout == LAYOUT_MATA_SAO_JOAO:
            # "Data e Hora de Emissão\n\nRaros\n\n25/05/2026 12:23:13" — pode haver
            # ruído de OCR entre o rótulo e a data, por isso toleramos até 40 chars.
            m = re.search(r'Data\s+e\s+Hora\s+de\s+Emiss[ãa]o[\s\S]{0,40}?(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1), m.group(2))
                if res: return res

        if self.layout == LAYOUT_ROSARIO_LIMEIRA:
            # "Data da Nota Fiscal:  26/06/2026" (sem hora).
            m = re.search(r'Data\s+da\s+Nota\s+Fiscal\s*:\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_CAMACARI_AVULSA:
            # "DATA DE PRESTAÇÃO: 12.06.2026" — datas com ponto neste layout. Não
            # há rótulo "Data de Emissão"; a data da prestação é a referência.
            m = re.search(r'DATA\s+DE\s+PRESTA[ÇC][ÃA]O\s*:?\s*(\d{2})[./](\d{2})[./](\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(f"{m.group(1)}/{m.group(2)}/{m.group(3)}")
                if res: return res

        if self.layout == LAYOUT_CPE_LOCACAO:
            m = re.search(r'Data\s+de\s*(?:Incri[cç][aã]o|Inscri[cç][aã]o|[:\s\n])*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_GUINCHO_CIDADE:
            m = re.search(r'Emiss[aã]o\s*[:\s\n]*(\d{2}[./]\d{2}[./]\d{4})', t, re.IGNORECASE)
            if m:
                clean_date = m.group(1).replace('.', '/')
                res = _parse_dmy(clean_date)
                if res: return res

        if self.layout == LAYOUT_BF_AMBIENTAIS:
            m = re.search(r'Emiss[aã]o\s*[:\s\n]*.*?(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if not m:
                m = re.search(r'Salvador\s*\(BA\),\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})', t, re.IGNORECASE)
            if m:
                parsed_dt = self._parse_data_extenso(m.group(1)) if 'de' in m.group(1) else _parse_dmy(m.group(1))
                if parsed_dt: return parsed_dt

        if self.layout == LAYOUT_LMR_ENGENHARIA:
            m = re.search(r'DATA\s+DA\s+EMISS[AÃ]O\s*[:\s\n]*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_FF_LOCACAO:
            m = re.search(r'Emiss[ãa]o\s*:?\s*[\n\s]*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_GERACAO_ENERGIA:
            m = re.search(r'(\d{2}/\d{2}/\d{4})', t)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_LOCONTAINERS:
            m = re.search(r'DATA\s+DA\s+EMISS[AÃÕO]*\s*[\n\r\s]+(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_LOCALIZA:
            m = re.search(r'DATA DE EMISS[AÃ]O:\s*(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_TELECOM_COMUNICACAO:
            # "DATA DE EMISSÃO: 16/06/2026" ou variações com espaços
            m = re.search(r'DATA\s+DE\s+EMISS[AÃ]O\s*[:\s]+(\d{2}/\d{2}/\d{4})', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1))
                if res: return res

        if self.layout == LAYOUT_CAMACARI_2:
            # No Camaçari escaneado a caixa de cabeçalho (recorte dedicado) traz
            # "Data de Emissão : |\n— 28/05/2026 16:22" com hora — preferimos ela
            # à "Data da prestação" (só data). O "—"/"|" são ruído de borda.
            m = re.search(r'Data\s+de\s+Emiss[ãa]o\s*:?\s*\|?\s*[\n\s—-]*(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1), m.group(2))
                if res: return res

        if self.layout in (LAYOUT_CAMACARI, LAYOUT_CAMACARI_2):
            # Este layout não traz um rótulo "Data de Emissão" — usamos "Data da
            # prestação do serviço" (mesmo rótulo já usado por _extrair_competencia)
            # e, como reforço, "Data Impressão". Sem isso, cai no fallback genérico
            # abaixo, que não reconhece nenhum dos dois e retorna datetime.now().
            m = re.search(r'Data\s+da\s+presta[cç][aã]o\s+do\s+servi[cç]o\s*:\s*(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1), m.group(2))
                if res: return res
            m = re.search(r'Data\s+Impress[aã]o\s*:?\s*(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}))?', t, re.IGNORECASE)
            if m:
                res = _parse_dmy(m.group(1), m.group(2))
                if res: return res

        if self.layout == LAYOUT_NACIONAL:
            # Padrão específico para DANFSe Nacional
            m_nac = re.search(r'Compet[eê]ncia\s+da\s+NFS-e[\s\n]+Data\s+e\s+Hora\s+da\s+emiss[aã]o.*?[\r\n]+(?:\d+[\r\n\s]+)?(?:\d{2}/\d{2}/\d{4})[\r\n\s]+(\d{2}/\d{2}/\d{4})[\r\n\s]+(\d{2}:\d{2}(?::\d{2})?)', t, re.IGNORECASE | re.DOTALL)
            if m_nac:
                res = _parse_dmy(m_nac.group(1), m_nac.group(2))
                if res: return res

        # Lista de campos/rótulos mapeados para a data de emissão
        data_emissao_labels = [
            r'Emitido\s+em',
            r'Data\s+e\s+Hora\s+d[ea]\s+Emiss[aã]o',
            r'Data\s+de\s+Gera[cç][aã]o',
            r'Data\s+e\s+Hora\s+da\s+emiss[aã]o',
            r'Data\s+de\s+Emiss[aã]o',
            r'Data\s+de',
            r'Emiss[aã]o(?:\s*\(Hor[aá]rio\s+de\s+Bras[ií]lia\))?',
        ]
        
        patterns = []
        for label in data_emissao_labels:
            if label == r'Emitido\s+em':
                patterns.append(r'Emitido\s+em\s+(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}(?::\d{2})?))?')
            elif label == r'Data\s+de':
                # CPE e similares podem ter Incrição/Inscrição no meio
                patterns.append(rf'{label}\s*(?:Incri[cç][aã]o|Inscri[cç][aã]o|[:\s\n])*(\d{{2}}/\d{{2}}/\d{{4}})(?:\s+(\d{{2}}:\d{{2}}(?::\d{{2}})?))?')
            else:
                patterns.append(rf'{label}.*?(?::|\s|\n)+(\d{{2}}/\d{{2}}/\d{{4}})(?:\s+(\d{{2}}:\d{{2}}(?::\d{{2}})?))?')
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

        self._data_emissao_fallback = True
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

        if self.layout == LAYOUT_ARMAC_LOCACAO:
            # "Fatura de Locação Número Fatura: | 90109539" (o "|" é ruído de
            # borda de célula do OCR).
            m = re.search(r'N[úu]mero\s+Fatura\s*:?\s*\|?\s*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_IACU_NFSE:
            # "Número da nota:\n\n2" — vindo do recorte dedicado do cabeçalho
            # (_ocr_header_box_iacu), prependido ao texto. Ancorado no rótulo
            # próprio; o valor pode ser um único dígito.
            m = re.search(r'N[úu]mero\s+da\s+nota\s*:?\s*[\n\s]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_FATURA_LOCACAO_GENERICA:
            # "NÚMERO:\n\n788" — ancorado no rótulo próprio, evitando casar com
            # "CONTRATO: 702" (número do contrato, não da fatura).
            m = re.search(r'N[ÚU]MERO\s*:\s*[\n\s]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_PASSWORD_ENOTAS:
            # "NÚMERO DA NOTA\n\n202600000038558" — ancorado no rótulo próprio
            # para não casar com o "RPS 38591" do cabeçalho nem com a inscrição
            # municipal (14 dígitos) mais abaixo.
            m = re.search(r'N[ÚU]MERO\s+DA\s+NOTA\s*[\n\s]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_MATA_SAO_JOAO:
            # "Número da Nota [ruído]\n\n00000018" — ancorado no rótulo próprio;
            # o valor vem zero-preenchido (8 dígitos), então removemos os zeros
            # à esquerda ("00000018" -> "18").
            m = re.search(r'N[úu]mero\s+da\s+Nota.*?\n+\s*0*(\d+)', t, re.IGNORECASE | re.DOTALL)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_ROSARIO_LIMEIRA:
            # "Nº da Nota\n72/2026" — o número é a parte antes da "/" (o resto é o
            # ano). Ancorado no rótulo próprio para não pegar o "Nº Integral"
            # (202600000000072) nem o "Nº da RPS".
            m = re.search(r'N[ºo°]\s*da\s*Nota\s*\n\s*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_CAMACARI_AVULSA:
            # "...DE SERVIÇOS (AVULSA) 00000088462" — número zero-preenchido (11
            # dígitos) na linha do cabeçalho. Removemos os zeros à esquerda
            # (int() -> "88462"). Ancorado em "AVULSA" para não casar com o
            # "Código Pessoa: 0000630812" do prestador.
            m = re.search(r'AVULSA\s*\)?\s*(\d{5,})', t, re.IGNORECASE)
            if m: return str(int(m.group(1)))

        if self.layout == LAYOUT_LOCALIZA:
            # "FATURA / DUPLICATA Nº: ACPIT - 311630" -> só o número (o "código
            # da filial" antes do traço, ex. ACPIT/AAREC/AASSA/ACBUL, não é
            # numérico). Capturar o valor alfanumérico inteiro quebrava a
            # importação no ERP contábil ("Número da NFS-e não é do tipo
            # numérico") em TODAS as notas Localiza reais testadas. Além disso,
            # em ao menos uma nota real (YUI/ACBUL) o rótulo seguinte ("CLIENTE")
            # vinha colado sem espaço logo após o número — `\d+` já para no
            # primeiro caractere não numérico, então essa colagem não vaza mais.
            m = re.search(r'N[ºo]:\s*[A-Z]*\s*-?\s*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_SAO_PAULO:
            m = re.search(r'N[uú]mero\s+da\s+Nota[:\s\n]+(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_SAO_PAULO_2:
            # "Número da Nota\n00331020" vindo do recorte dedicado do cabeçalho
            # (_ocr_header_box_sao_paulo), prependido ao texto. Na página inteira
            # o valor sai corrompido (vira "5"), então priorizamos a linha limpa
            # do recorte, que é a 1ª ocorrência do rótulo no texto.
            m = re.search(r'N[uú]mero\s+da\s+Nota\s*:?\s*[\n\s]*(\d{3,})', t, re.IGNORECASE)
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
            
        if self.layout == LAYOUT_CPE_LOCACAO:
            m = re.search(r'N[úu]mero\s+da\s+Nota\s+de\s+Loca[cç][aã]o\s*[:\s]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()
            m_top = re.search(r'N[ºo]\s*(\d+)', t, re.IGNORECASE)
            if m_top: return m_top.group(1).strip()

        if self.layout == LAYOUT_SULSEG_COBRANCA:
            # "NOTA DE COBRANÇA Nº\n\n20260000012366" — evita casar com o campo
            # "DADOS DO DOCUMENTO / NÚMERO" mais abaixo, que é o número de
            # cadastro do cliente na SUL&SEG, não o número da nota.
            m = re.search(r'NOTA\s+DE\s+COBRAN[ÇC]A\s+N[ºo]\s*[\n\s]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_GUINCHO_CIDADE:
            m = re.search(r'FATURA\s+DE\s+LOCA[CÇ][AÃ]O\s*[\n\s]*N[ºo]\s*[:\s]*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_OSASCO_REPASSE:
            # Ordem invertida do padrão usual ("Número da Nota"): "Nota No.: 2440738"
            # ou "Nota Nº: 02479318" (variações vistas em documentos reais).
            m = re.search(r'Nota\s+N[º°o]\.?\s*:?\s*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_BF_AMBIENTAIS:
            m = re.search(r'FATURA\s+n[ºo°]\s*[:\s\n]*(\d+)', t, re.IGNORECASE)
            if m: return str(int(m.group(1))) # remove leading zeros

        if self.layout == LAYOUT_LMR_ENGENHARIA:
            m = re.search(r'FATURA/DUPLICATA\s+N[ºo°]\s*[:\s\n]*(\d+)', t, re.IGNORECASE)
            if m: return str(int(m.group(1))) # remove leading zeros

        if self.layout == LAYOUT_FF_LOCACAO:
            # "FATURA DE LOCAÇÃO ... Nº: 520366" - rótulo próprio do cabeçalho
            # (também repetido no rodapé de assinatura, mesmo valor).
            m = re.search(r'N[º°o]\s*:?\s*(\d{4,})', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_GERACAO_ENERGIA:
            m = re.search(r'03\.292\.008.*?LOCA.*?BENS.*?\s+(\d+)', t, re.IGNORECASE | re.DOTALL)
            if m: return str(int(m.group(1)))

        if self.layout == LAYOUT_LOCONTAINERS:
            m = re.search(r'Nota\s+Fatura\s+N[ºo°]?\s*[\n\r\s]+(\d+)', t, re.IGNORECASE)
            if m: return str(int(m.group(1)))

        if self.layout == LAYOUT_TELECOM_COMUNICACAO:
            # "NOTA FISCAL Nº 27528 - SÉRIE: 1" ou "NOTA FISCAL Nº 27528"
            m = re.search(r'NOTA\s+FISCAL\s+N[ºo°]\s*(\d+)', t, re.IGNORECASE)
            if m: return m.group(1).strip()

        if self.layout == LAYOUT_SALVADOR:
            # A caixa de cabeçalho ("Número da Nota:") é reforçada por um recorte
            # dedicado em zoom alto (ver _ocr_header_box_salvador), prependido ao
            # texto — mas o valor pode vir separado do rótulo por texto de outra
            # coluna (ex.: "Número da Nota:\n\nPREFEITURA MUNICIPAL DO SALVADOR
            # 00004852") ou com um caractere solto colado ("R 00004852"). Por
            # isso buscamos o primeiro número plausível numa janela após o rótulo,
            # em vez de exigir adjacência imediata.
            m_lab = re.search(r'N[uú]mero\s+da\s+Nota', t, re.IGNORECASE)
            if m_lab:
                janela = t[m_lab.end(): m_lab.end() + 80]
                for m_num in re.finditer(r'\b(\d{4,10})\b', janela):
                    return m_num.group(1)

        if self.layout in (LAYOUT_CAMACARI, LAYOUT_CAMACARI_2):
            # Rótulo "Número da Nota" — o OCR deste layout às vezes troca o "ú" por "i"
            # ("Nimero da Nota") e, por ser um documento em duas colunas, o valor real
            # nem sempre fica colado ao rótulo (pode vir depois de texto de outra coluna,
            # ex: "Número da Nota\nPREFEITURA MUNICIPAL DE CAMAÇARI 961"). Por isso
            # buscamos o rótulo e pegamos o primeiro número dentro de uma janela após
            # ele, em vez de exigir adjacência imediata.
            m_lab = re.search(r'N[uiú]mero\s+da\s+Nota', t, re.IGNORECASE)
            if m_lab:
                janela = t[m_lab.end(): m_lab.end() + 80]
                # Em PDFs gerados digitalmente (não OCR), o marcador de página
                # ("Pagina 1/1") pode cair dentro dessa janela, antes do valor
                # real — removê-lo evita capturar o "1" da paginação.
                janela = re.sub(r'P[áa]gina\s*\d+\s*/\s*\d+', ' ', janela, flags=re.IGNORECASE)
                for m_num in re.finditer(r'\b(\d+)\b', janela):
                    num = m_num.group(1)
                    # Descarta números de 1 dígito (paginação residual) e o ano
                    # isolado (que também pode aparecer perto do rótulo).
                    if len(num) < 2:
                        continue
                    if num in ('2024', '2025', '2026') and len(num) <= 4:
                        continue
                    return num

        if self.layout == LAYOUT_CAMPINAS:
            # Grade "Número / Série" cujo valor vem em outra linha, no formato
            # "1712/E" (número da nota + letra da série). O rótulo "Número / Série"
            # divide a linha de cabeçalho com outros campos, então ancoramos no
            # próprio valor: dígitos seguidos de "/" e uma única letra de série.
            # "06/2026" (competência) não casa porque exige letra após a barra;
            # "5920-1/00-00" (CNAE) também não casa.
            m = re.search(r'\b(\d{2,7})\s*/\s*[A-Za-z]\b', t)
            if m:
                return m.group(1).strip()

        if self.layout == LAYOUT_CUIABA:
            # ISSNet Cuiabá em dois formatos de OCR:
            # (1) rótulo limpo (digital/scan bom): "Número da Nota Fiscal: 205".
            # Às vezes o OCR intercala um dígito espúrio ISOLADO numa linha
            # própria ENTRE o rótulo e o valor real (ex.: nota real pág.10 do
            # MTI 03-2026, "RC CONSTRUÇÕES ELÉTRICAS": "Número da Nota
            # Fiscal\n5\n205\n" — o "5" é ruído, "205" é o número de
            # verdade). Por isso capturamos TODOS os grupos de dígitos logo
            # após o rótulo (até 3, cada um em sua própria linha) e ficamos
            # com o MAIS LONGO — um ruído de 1 dígito nunca vence o número
            # real ao lado, e quando só há um candidato (formato limpo
            # normal) o comportamento não muda.
            m = re.search(
                r'N[uú]mero\s+da\s+Nota\s+Fiscal\s*:?\s*((?:\d+\s*\n?\s*){1,3})',
                t, re.IGNORECASE
            )
            if m:
                candidatos = re.findall(r'\d+', m.group(1))
                if candidatos:
                    return max(candidatos, key=len)
            # (2) scan degradado (consolidado MTI): a caixa do número sai garbleada,
            # mas o número vem IMEDIATAMENTE antes de "Dados do Prestador de Serviço".
            # Evita o genérico pescar o "Número: 554" do ENDEREÇO do tomador
            # ("Avenida Praia de Pajussara Número: 554").
            m = re.search(r'\b(\d{2,6})\s*\n\s*Dados\s+do\s+Prestador', t, re.IGNORECASE)
            if m:
                return m.group(1)
            # Nenhuma das duas âncoras casou (scan gravemente degradado, ex.: nota
            # ANDERSON FAUSTINO/FA TELAS — testado com re-OCR em zoom até 10x sem
            # recuperar o número no cabeçalho). NÃO cai nos padrões genéricos
            # abaixo: o padrão bare "Número[:\s]+(\d+)" pescaria o mesmo
            # "Número: 554" do endereço do tomador (mesma armadilha). Vai direto
            # para o fallback honesto (nome do arquivo / placeholder + aviso) —
            # não fabricar um número plausível-porém-errado.
            if getattr(self, 'pdf_path', None):
                import os
                m_fn = re.search(r'(?:NFS?|NOTA|NF)\s*[-_]*\s*(\d+)', os.path.basename(self.pdf_path), re.IGNORECASE)
                if m_fn:
                    return m_fn.group(1).strip()
            return '00000000'

        if self.layout == LAYOUT_NACIONAL:
            # DANFSe Nacional: o número da NFS-e vem codificado na Chave de Acesso
            # de 50 dígitos (posições 24-36, zero-preenchidas) — fonte de verdade
            # imune ao OCR, que costuma comer dígitos do valor impresso ao lado do
            # rótulo "Número da NFS-e" (ex.: "21" sai "2"). Por isso priorizamos o
            # decode da chave sobre a proximidade do rótulo (usada mais abaixo).
            m_chave = re.search(r'\b(?:\d\s*){44,60}\b', t)
            if m_chave:
                chave = re.sub(r'\D', '', m_chave.group(0))
                if len(chave) >= 50:
                    n_nf = chave[23:36].lstrip('0')
                    if n_nf:
                        return n_nf

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
        if self.layout == LAYOUT_MATA_SAO_JOAO:
            # "Discriminação do(s) Serviço(s)\n\nSERVIÇOS DE MARKETING DIGITAL\n\n
            # Classificação do Serviço (LEI 116/2003)..." — bloco entre o rótulo
            # e a Classificação do Serviço (próxima seção). OCR limpo neste layout.
            m = re.search(
                r'Discrimina[çc][ãa]o\s+do\(s\)\s+Servi[çc]o\(s\)(.*?)'
                r'Classifica[çc][ãa]o\s+do\s+Servi[çc]o',
                t, re.IGNORECASE | re.DOTALL)
            if m:
                disc = re.sub(r'\s+', ' ', m.group(1)).strip()
                if disc:
                    return disc

        if self.layout == LAYOUT_ROSARIO_LIMEIRA:
            # O texto real da discriminação ("HOSPEDAGEM") é entregue pelo pdfminer
            # ENTRE o rótulo "ART:" e o cabeçalho "DISCRIMINAÇÃO DOS SERVIÇOS"
            # (a grade de valores vem logo após o cabeçalho, sem a descrição).
            m = re.search(r'\bART:\s*\n\s*(.+?)\s*\n\s*DISCRIMINA[ÇC][ÃA]O', t, re.IGNORECASE | re.DOTALL)
            if m:
                disc = re.sub(r'\s+', ' ', m.group(1)).strip()
                if disc:
                    return disc

        if self.layout == LAYOUT_CAMACARI_AVULSA:
            # A descrição real do serviço é a linha do item, logo após o cabeçalho
            # da tabela ("...Preço Unitário, Preço Total"), no formato
            # "1 TRANSPORTE E DESTINAÇÃO FINAL DE RESIDUO CLASSE II B 16.500,00! 16.500,00".
            # Removemos a quantidade inicial ("1 ") e os dois valores finais (o "!"
            # é ruído de borda do OCR).
            m = re.search(
                r'Pre[çc]o\s+Tota[l]?[^\n]*\n\s*\d+\s+(.+?)\s+[\d.,]+[!|]*\s+[\d.,]+',
                t, re.IGNORECASE)
            if m:
                disc = re.sub(r'\s+', ' ', m.group(1)).strip()
                if disc:
                    return disc

        if self.layout == LAYOUT_SAO_PAULO_2:
            # Bloco entre "DISCRIMINAÇÃO DE SERVIÇOS" e "ALÍQUOTAS DOS TRIBUTOS"
            # (ou "VALOR TOTAL DO SERVIÇO"), no OCR de 2 colunas ruidoso. A
            # descrição real ("IMC - PLANO ZAP+ (ZAP+VIVA+OLX)") vem misturada
            # com rótulos vazados (Inscrição Municipal, Valor Bruto) e o texto da
            # Lei 12.741/PIS/COFINS — filtramos essas linhas de ruído.
            m = re.search(
                r'DISCRIMINA[ÇC][ÃA]O\s+D[EO]S?\s+SERVI[ÇC]OS(.*?)'
                r'(?:AL[IÍ]QUOTAS\s+DOS\s+TRIBUTOS|VALOR\s+TOTAL\s+DO\s+SERVI[ÇC]O)',
                t, re.IGNORECASE | re.DOTALL)
            if m:
                linhas = []
                for ln in m.group(1).split('\n'):
                    ln = ln.strip().lstrip('|').strip()
                    if not ln:
                        continue
                    if re.search(r'Inscri[çc][ãa]o\s+Municipal|Valor\s+Bruto|REF\.?\s*A\s*LEI|PERC\.|VALOR\s+(?:PIS|COFINS)|^R\$|12\.?741', ln, re.IGNORECASE):
                        continue
                    linhas.append(ln)
                disc = ' '.join(linhas).strip()
                if disc:
                    return disc

        if self.layout == LAYOUT_CAMACARI_2:
            # Bloco entre "DISCRIMINAÇÃO DOS SERVIÇOS" e "Retenções (R$)", no OCR
            # de grade ruidoso. As linhas úteis (descrição do serviço + "OPTANTE
            # PELO SIMPLES NACIONAL") vêm misturadas com a linha de cabeçalho da
            # tabela (QTD / VALOR UNIT / VALOR TOTAL), com um rótulo "DESCRIÇÃO"
            # corrompido ("ESCaurCiio") e com colunas numéricas soltas
            # (quantidade/valores). Filtramos essas linhas de ruído e removemos os
            # números de coluna coladas ao fim das linhas de descrição.
            m = re.search(
                r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS(.*?)Reten[çc][õo]es\s*\(R\$\)',
                t, re.IGNORECASE | re.DOTALL)
            if m:
                linhas = []
                for ln in m.group(1).split('\n'):
                    ln = ln.strip().lstrip('|').strip(' .')
                    if not ln:
                        continue
                    # Linha de cabeçalho da tabela (QTD/VALOR UNIT/VALOR TOTAL).
                    if re.search(r'\b(?:QTD|STD)\b|VALOR\s+UNIT|VALOR\s+TOTAL', ln, re.IGNORECASE):
                        continue
                    # Remove as colunas numéricas (qtd/valor unit/valor total)
                    # que o OCR cola ao fim da linha de descrição.
                    ln = re.sub(r'\s+\d{1,3}(?:\.\d{3})*,\d{2,4}(?:\s+\d{1,3}(?:\.\d{3})*,\d{2})*\s*$', '', ln).strip()
                    # O texto real do serviço é impresso em CAIXA ALTA; só mantemos
                    # linhas com um bloco de 4+ maiúsculas seguidas. Isso descarta o
                    # rótulo "DESCRIÇÃO" corrompido pelo OCR (ex.: "ESCaurCiio",
                    # caixa mista) e linhas de valores puras, preservando a
                    # descrição ("...DESINSETIZAÇÃO PARA TRAÇAS") e "OPTANTE PELO
                    # SIMPLES NACIONAL". O 1º caractere de cada linha pode ter sido
                    # comido pela borda da grade ("SERVIÇO"->"ERVIÇO").
                    if not re.search(r'[A-ZÀ-Ú]{4,}', ln):
                        continue
                    linhas.append(ln)
                disc = ' '.join(linhas).strip()
                if disc:
                    return disc

        if self.layout == LAYOUT_IACU_NFSE:
            # Bloco entre "DISCRIMINAÇÃO DOS SERVIÇOS" e "LOCAL DE PRESTAÇÃO DOS
            # SERVIÇOS", em várias linhas; normalizamos os espaços numa linha só.
            m = re.search(r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS(.*?)LOCAL\s+DE\s+PRESTA[ÇC][ÃA]O', t, re.IGNORECASE | re.DOTALL)
            if m:
                disc = re.sub(r'\s+', ' ', m.group(1)).strip()
                if disc: return disc

        if self.layout == LAYOUT_SALVADOR:
            # O rótulo "DISCRIMINAÇÃO DOS SERVIÇOS" sai truncado/corrompido no
            # OCR (ex.: "DISCRIMINA! IÇoS"), então ancoramos só no prefixo
            # "DISCRIMINA" + o sufixo "...IÇ[OÕ]S" tolerante a ruído entre eles.
            # O texto termina antes de uma linha "IR (" (nota de retenção que
            # aparece logo depois na mesma caixa) ou dos dados bancários.
            m = re.search(
                r'DISCRIMINA[\s\S]{0,25}?I[ÇC][OÕ]S\s*\n+(.*?)'
                r'(?=\n\s*IR\s*\(|BANCO\s+BRADESCO|VALOR\s+TOTAL\s+DA\s+NOTA|$)',
                t, re.IGNORECASE | re.DOTALL)
            if m:
                linhas = [ln.strip() for ln in m.group(1).split('\n') if ln.strip()]
                if linhas:
                    return " ".join(linhas)

        if self.layout == LAYOUT_LAURO_FREITAS:
            # O texto do serviço vem colado, na mesma linha, à nota de
            # transparência fiscal do IBPT ("Valor aproximado dos tributos R$
            # X Fonte IBPT") — removida por não fazer parte da discriminação
            # real do serviço prestado.
            m = re.search(
                r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS\s*\n+(.*?)(?=\n\s*VALOR\s+TOTAL\s+DA\s+NOTA|$)',
                t, re.IGNORECASE | re.DOTALL)
            if m:
                texto = re.sub(r'\s+', ' ', m.group(1)).strip()
                texto = re.sub(r'\s*Valor\s+aproximado\s+dos\s+tributos.*$', '', texto, flags=re.IGNORECASE).strip()
                if texto:
                    return texto

        if self.layout == LAYOUT_SULSEG_COBRANCA:
            # A descrição do item ("LOCAÇÃO DO EQUIPAMENTO DE ALARME") sai, no
            # texto do pdfminer, ANTES do cabeçalho da tabela ("DESCRIÇÃO
            # QUANTIDADE VALOR UNITÁRIO VALOR TOTAL") — mesma inversão de ordem
            # de outros layouts em grade. Ancoramos em "ISENTO" (Inscrição
            # Estadual do tomador, que sempre precede o item nesta nota) e
            # paramos antes da quantidade + valor unitário que seguem.
            m = re.search(r'ISENTO\s*\n+(.+?)\n+\d+\s*\n+R\$', t, re.IGNORECASE | re.DOTALL)
            if m:
                texto = re.sub(r'\s+', ' ', m.group(1)).strip()
                if texto:
                    return texto

        if self.layout == LAYOUT_PASSWORD_ENOTAS:
            # Bloco entre "DISCRIMINAÇÃO DOS SERVIÇOS" e "CÓDIGO DO SERVIÇO".
            # O item vem como "1 Locação do Sistema de Alarme. 214,44" (número
            # do item + descrição + valor colados na mesma linha), seguido da
            # descrição detalhada e do "Cód. 2172" (código interno do item) —
            # removemos os três ruídos (item nº, valor solto, código interno)
            # para manter só o texto descritivo do serviço.
            m = re.search(
                r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS\s*\n+(.*?)(?=\n\s*C[ÓO]DIGO\s+DO\s+SERVI[ÇC]O|$)',
                t, re.IGNORECASE | re.DOTALL)
            if m:
                texto = re.sub(r'\s+', ' ', m.group(1)).strip()
                texto = re.sub(r'\s*C[óo]d\.\s*\d+\s*$', '', texto).strip()
                texto = re.sub(r'^\d+\s+', '', texto)
                texto = re.sub(r'(\.)\s*[\d\.]+,\d{2}\s+', r'\1 ', texto).strip()
                if texto:
                    return texto

        if self.layout == LAYOUT_FATURA_LOCACAO_GENERICA:
            # "1 - CGB-0001   CORTADOR DE GRAMA A BATERIA" — nº do item, código
            # interno do produto e descrição colados na mesma linha, logo após
            # o cabeçalho da tabela ("QTDE - DESCRIÇÃO ... VALOR").
            m = re.search(r'\n\s*\d+\s*-\s*([A-Z0-9][A-Z0-9\-]*)\s+([^\n]+)', t)
            if m:
                codigo, desc = m.group(1).strip(), m.group(2).strip()
                texto = f"{codigo} {desc}".strip()
                if texto:
                    return texto

        if self.layout == LAYOUT_ARMAC_LOCACAO:
            # Tabela multi-item: cada linha começa com um código de item
            # (ex.: "ES01501", "RC00824", "MO00199") seguido da descrição do
            # equipamento e das datas de locação. Capturamos só a descrição
            # (entre o código e a 1ª data), deduplicando itens repetidos.
            itens = []
            for ln in t.split('\n'):
                m = re.match(r'^[A-Za-z][A-Za-z0-9]{4,}\s+(.+?)\s+\d{2}[.\s]\d{2}[.\s/]*\d{4}', ln.strip())
                if m:
                    desc = re.sub(r'\s+', ' ', m.group(1)).strip()
                    if desc and desc not in itens:
                        itens.append(desc)
            if itens:
                return " | ".join(itens)

        if self.layout == LAYOUT_CAMPINAS:
            # Bloco "DESCRIÇÃO DO SERVIÇO PRESTADO (...)" até o próximo marcador
            # (dados bancários / documento / tributação).
            m = re.search(
                r'DESCRI[ÇC][AÃ]O\s+DO\s+SERVI[ÇC]O\s+PRESTADO.*?\)\s*(.*?)'
                r'(?=DADOS\s+BANC|DOCUMENTO\s+EMITIDO|TRIBUTA[ÇC][AÃ]O\s+MUNICIPAL|C[ÁA]LCULO\s+DO\s+ISSQN|$)',
                t, re.IGNORECASE | re.DOTALL)
            if m:
                linhas = [ln.strip() for ln in m.group(1).split('\n') if ln.strip()]
                if linhas:
                    return " ".join(linhas)

        if self.layout == LAYOUT_CPE_LOCACAO:
            m = re.search(r'C[oó]digo\s+e\s+Descri[cç][aã]o.*?\n(.*)', t, re.IGNORECASE | re.DOTALL)
            if m:
                linhas = m.group(1).split('\n')
                items = []
                for l in linhas:
                    l_clean = l.strip()
                    if not l_clean: continue
                    if re.search(r'Endereço|Dados\s+do|Vencimento|Valor:', l_clean, re.IGNORECASE):
                        break
                    items.append(l_clean)
                return " | ".join(items)

        if self.layout == LAYOUT_GUINCHO_CIDADE:
            m = re.search(r'DESCRIMINA[CÇ][AÃ]O\s*[:\s\n]*(.*?)(?=OBSERVA[ÇC][ÕO]ES|OBSERVA[ÇC]O|PAGAMENTO|VALOR\s+TOTAL|$)', t, re.IGNORECASE | re.DOTALL)
            if m:
                res = m.group(1).strip()
                res = re.sub(r'\s+', ' ', res)
                return res

        if self.layout == LAYOUT_BF_AMBIENTAIS:
            m = re.search(r'Objeto\s*:\s*Descri[cç][aã]o\s*\n*(.*?)(?=Valor\s+Total|Total\s+Bruto|$)', t, re.IGNORECASE | re.DOTALL)
            if m:
                res = m.group(1).strip()
                res = re.sub(r'\s+', ' ', res)
                return res

        if self.layout == LAYOUT_LMR_ENGENHARIA:
            m = re.search(r'DESCRI[CÇ]I?[ÃA]?O\s*\n*(.*?)(?=DADOS\s+DA\s+CONTA|VENCIMENTO|VALOR\s+TOTAL|$)', t, re.IGNORECASE | re.DOTALL)
            if m:
                lines = m.group(1).strip().split('\n')
                items = []
                for l in lines:
                    l_clean = l.strip()
                    if not l_clean: continue
                    if l_clean.upper() == "VALOR":
                        continue
                    if re.search(r'R\$\s*\d+', l_clean, re.IGNORECASE):
                        break
                    items.append(l_clean)
                res = " | ".join(items)
                res = re.sub(r'\s+', ' ', res)
                return res

        if self.layout == LAYOUT_GERACAO_ENERGIA:
            pos = t.find("JOSE AUGUSTO SANTOS")
            bloco_disc = t[pos + len("JOSE AUGUSTO SANTOS"):] if pos != -1 else t
            lines = bloco_disc.strip().split('\n')
            items = []
            for l in lines:
                l_clean = l.strip()
                if not l_clean: continue
                if re.match(r'^\d+$', l_clean): continue
                if re.search(r'\b\d{1,3}(?:\.\d{3})*(?:,\d{2})\b', l_clean):
                    break
                items.append(l_clean)
            res = " | ".join(items)
            res = re.sub(r'\s+', ' ', res)
            return res

        if self.layout == LAYOUT_TELECOM_COMUNICACAO:
            # Coleta os itens da tabela "ITENS DA FATURA" até "TOTAL A PAGAR"
            m = re.search(
                r'ITENS\s+DA\s+FATURA.*?\n(.*?)(?=TOTAL\s+A\s+PAGAR|VENCIMENTO|$)',
                t, re.IGNORECASE | re.DOTALL
            )
            if m:
                linhas = [
                    l.strip() for l in m.group(1).split('\n')
                    if l.strip() and not re.match(r'^[\d\.,\s]+$', l.strip())
                    and not re.match(r'^(UN|cClass|QUANT|VALOR|DESC|PIS|BC|AL[IÍ]Q)', l.strip(), re.IGNORECASE)
                ]
                if linhas:
                    return ' | '.join(linhas[:15])
            return 'Serviços de telecomunicação conforme nota fiscal.'

        if self.layout == LAYOUT_LOCONTAINERS:
            m_start = re.search(r'QUANT\.\s*DESCRI[CÇCçIíiÃãOõoAaSs]*', t, re.IGNORECASE)
            m_end = re.search(r'VALOR\s+UNIT[AÁAáIíiOõoRRsS]*', t, re.IGNORECASE)
            if m_start and m_end:
                block = t[m_start.end():m_end.start()]
                lines = block.split('\n')
                items = []
                for l in lines:
                    l_clean = l.strip()
                    if not l_clean:
                        continue
                    if l_clean in ["BAIRRO / DISTRITO", "IAPI", "CNPJ / CPF", "01.813.680/0001-25", "CEP", "40330533", "FONE / FAX", "7132441400", "U.F.", "INSCRIÇÃO MUNICIPAL", "INSCRIÇÃO ESTADUAL", "BA", "INSCRIO MUNICIPAL", "INSCRIO ESTADUAL"]:
                        continue
                    if re.match(r'^\d+$', l_clean):
                        continue
                    items.append(l_clean)
                res = " | ".join(items)
                res = re.sub(r'\s+', ' ', res)
                return res

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
        if self.layout in (LAYOUT_CPE_LOCACAO, LAYOUT_GUINCHO_CIDADE, LAYOUT_BF_AMBIENTAIS, LAYOUT_LMR_ENGENHARIA, LAYOUT_GERACAO_ENERGIA, LAYOUT_LOCONTAINERS, LAYOUT_TELECOM_COMUNICACAO, LAYOUT_SULSEG_COBRANCA, LAYOUT_FATURA_LOCACAO_GENERICA, LAYOUT_ARMAC_LOCACAO, LAYOUT_FF_LOCACAO):
            return "0601"

        if self.layout == LAYOUT_MATA_SAO_JOAO:
            # "Classificação do Serviço (LEI 116/2003) + Desdobro\n\n01.01.01 -
            # Análise e desenvolvimento de sistemas." — o item da LC 116 vem como
            # "XX.XX.XX" (o 3º par é o desdobro municipal). O código ABRASF são os
            # 2 primeiros pares -> "0101". Ancorado no rótulo próprio para não
            # casar com o NBS ("115021000") logo abaixo.
            m = re.search(r'Classifica[çc][ãa]o\s+do\s+Servi[çc]o.*?\n+\s*(\d{2})\.(\d{2})\.\d{2}', t, re.IGNORECASE | re.DOTALL)
            if m:
                return m.group(1) + m.group(2)

        if self.layout == LAYOUT_ROSARIO_LIMEIRA:
            # "Código de Trib. Nacional: 09.01.04 - HOSPEDAGEM ..." — item da LC 116
            # como "XX.XX.XX" (o 3º par é o desdobro). Usamos os 2 primeiros pares
            # (09.01 -> 0901). Ancorado no rótulo para não casar com o NBS
            # ("1.0303.11.00") logo abaixo.
            m = re.search(r'C[óo]digo\s+de\s+Trib\.?\s*Nacional\s*:\s*(\d{2})\.(\d{2})\.\d{2}', t, re.IGNORECASE)
            if m:
                return m.group(1) + m.group(2)

        if self.layout == LAYOUT_CAMACARI_AVULSA:
            # "PE 000709 - VARRIÇÃO, COLETA, REMOÇÃO..." — código da atividade em 6
            # dígitos zero-preenchidos (000709 = item 7.09 da LC 116). Usamos os 4
            # dígitos significativos -> "0709". Ancorado no traço que separa código
            # e descrição (o número da nota "00000088462" não é seguido de traço).
            m = re.search(r'\b0*(\d{4})\s*[-–]\s*[A-Za-zÀ-ú]', t)
            if m:
                return m.group(1)

        if self.layout == LAYOUT_SAO_PAULO_2:
            # "Código do Serviço a ” ;\n02498 - Inserção de textos..." — código
            # de 5 dígitos do cadastro paulistano. O OCR insere ruído entre o
            # rótulo e o valor, então buscamos, numa janela após o rótulo, o
            # padrão "NNNNN - <letra>" (código seguido de descrição).
            m_lab = re.search(r'C[oó]digo\s+do\s+Servi[çc]o', t, re.IGNORECASE)
            if m_lab:
                janela = t[m_lab.end(): m_lab.end() + 120]
                m_cod = re.search(r'(\d{4,5})\s*-\s*[A-Za-zÀ-ú]', janela)
                if m_cod:
                    return m_cod.group(1)

        if self.layout == LAYOUT_CAMACARI_2:
            # "Serviço: 000713 - DEDETIZAÇÃO, DESINFECÇÃO, ..." — item da lista
            # em 6 dígitos com zeros à esquerda (000713 = 07.13). Ancoramos em
            # exatamente 6 dígitos iniciados por "0" para não casar com o
            # "Município da prestação do serviço: 2905701" (código IBGE, 7
            # dígitos, na mesma família de rótulos "... serviço:"). Retornamos os
            # 4 dígitos significativos (0713), padrão dos demais layouts.
            m = re.search(r'Servi[çc]o\s*:\s*(0\d{5})\b', t)
            if m:
                return m.group(1)[-4:]

        if self.layout == LAYOUT_CAMPINAS:
            # Seção "Serviço" traz o item da LC 116/03 no formato "13.02 - FONOGRAFIA...".
            # O CNAE ("5920-1/00-00") aparece antes, mas tem formato distinto (\d{4}-\d)
            # e não casa com \d{2}\.\d{2}.
            m = re.search(r'\b(\d{2})\.(\d{2})\s*-\s*[A-Za-zÀ-ú]', t)
            if m:
                return (m.group(1) + m.group(2))

        if self.layout == LAYOUT_IACU_NFSE:
            # "Item da lista de serviços:\n7.02 - Execução..." — código LC116 no
            # formato N.NN; normalizamos para 4 dígitos (0702), como os demais.
            m = re.search(r'Item\s+da\s+lista\s+de\s+servi[çc]os\s*:?\s*\n?\s*(\d{1,2})\.(\d{2})', t, re.IGNORECASE)
            if m:
                return m.group(1).zfill(2) + m.group(2)

        if self.layout == LAYOUT_SALVADOR:
            # "Item da Lista de Serviços:\n01714 - Advocacia." — a nota traz um
            # zero de preenchimento à esquerda do código LC 116 (17.14); removemos
            # para manter o padrão de 4 dígitos usado pelos demais layouts.
            m = re.search(r'Item\s+da\s+Lista\s+de\s+Servi[çc]os\s*:?\s*\n?\s*0?(\d{3,4})', t, re.IGNORECASE)
            if m:
                return m.group(1)

        if self.layout == LAYOUT_PASSWORD_ENOTAS:
            # "CÓDIGO DO SERVIÇO\n\n15.03 / 1503 - Locação e manutenção..." — a
            # nota traz o código LC116 em dois formatos (com e sem ponto); usamos
            # os 4 dígitos sem ponto (1503) para manter o padrão dos demais layouts.
            m = re.search(r'(\d{2})\.(\d{2})\s*/\s*(\d{4})\s*-', t)
            if m:
                return m.group(3)

        if self.layout == LAYOUT_LAURO_FREITAS:
            # "ITEM DA LISTA DE SERVIÇOS:\n\n( Lei Municipal 1572/2015 )\n\n110201 -
            # Vigilância..." — entre o rótulo e o valor há a referência da lei
            # municipal (que também contém dígitos, ex.: "1572/2015"), então não
            # basta pegar o primeiro número após o rótulo. Ancoramos no padrão
            # "dígitos - Texto" (só o código real vem seguido de um hífen e uma
            # descrição). O código de 6 dígitos é "item.subitem LC116 + subitem
            # municipal" (ex.: 11.02.01); usamos só os 4 primeiros (11.02) para
            # manter o padrão LC 116 dos demais layouts.
            m_lab = re.search(r'ITEM\s+DA\s+LISTA\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
            if m_lab:
                janela = t[m_lab.end(): m_lab.end() + 150]
                m_cod = re.search(r'\b(\d{4,6})\s*-\s*[A-ZÀ-Ú]', janela)
                if m_cod:
                    return m_cod.group(1)[:4]

        if self.layout == LAYOUT_CUIABA:
            # ISSNet Cuiabá: na grade de detalhamento a linha da atividade traz
            # "...Serviços de engenharia - 5,00 | 701 114031000 | 7112000" —
            # colunas Atividade / Alíquota / item LC116 / NBS / CNAE. O item da LC
            # 116 (701 = 7.01) são os 3-4 dígitos após a alíquota e antes do NBS de
            # 9 dígitos. Normalizamos para 4 dígitos (0701).
            m = re.search(r'\d{1,2},\d{2}\s*\|?\s*(\d{3,4})\s+\d{9}', t)
            if m:
                return m.group(1).zfill(4)

        if self.layout == LAYOUT_NACIONAL:
            # DANFSe: "Código de Tributação Nacional ... 16.02.01 - Outros serviços
            # de transporte..." — item da LC 116 no formato "XX.XX.XX" (o 3º par é o
            # desdobro). Usamos os 2 primeiros pares (16.02 -> 1602). Ancorado no
            # rótulo próprio; entre ele e o código há os rótulos vizinhos da grade
            # ("Código de Tributação Municipal Local da Prestação..."), então
            # pulamos até o primeiro "XX.XX.XX". Sem este ramo, cai no default
            # genérico "03115".
            m = re.search(r'C[óo]digo\s+de\s+Tributa[çc][ãa]o\s+Nacional[\s\S]{0,100}?(\d{2})\.(\d{2})\.\d{2}', t, re.IGNORECASE)
            if m:
                return m.group(1) + m.group(2)

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
        if self.layout in (LAYOUT_CPE_LOCACAO, LAYOUT_GUINCHO_CIDADE, LAYOUT_BF_AMBIENTAIS, LAYOUT_LMR_ENGENHARIA, LAYOUT_GERACAO_ENERGIA, LAYOUT_LOCONTAINERS, LAYOUT_SULSEG_COBRANCA, LAYOUT_FATURA_LOCACAO_GENERICA, LAYOUT_ARMAC_LOCACAO, LAYOUT_LOCALIZA, LAYOUT_FF_LOCACAO):
            return "FATURA"

        if self.layout == LAYOUT_SAO_PAULO_2:
            # "RPS Nº 320839 Série NF, emitido em 25/06/2026 PQHZ-BYVT" — o
            # código de verificação (formato XXXX-XXXX) vem no FIM da linha do
            # RPS. O padrão genérico casaria "RPS Nº" → "RPSN"; aqui ancoramos
            # em "emitido em <data>" e pegamos o token XXXX-XXXX seguinte.
            m = re.search(r'emitido\s+em\s+\d{2}/\d{2}/\d{4}\s+([A-Z0-9]{4}-[A-Z0-9]{4})', t, re.IGNORECASE)
            if not m:
                m = re.search(r'\b([A-Z0-9]{4}-[A-Z0-9]{4})\b', t)
            if m:
                return m.group(1).upper()

        if self.layout == LAYOUT_OSASCO_REPASSE:
            # "Cód. de Autenticidade: VCWSRSCV" costuma vir na mesma linha/célula
            # de tabela que o campo seguinte ("Valor do Repasse"), sem quebra de
            # linha entre eles — usamos [A-Z0-9]+ (sem espaço) para não engolir
            # o próximo rótulo, diferente do padrão genérico mais abaixo.
            m = re.search(r'C[oó]d\.?\s+de\s+Autenticidade\s*:?\s*([A-Z0-9]+)', t, re.IGNORECASE)
            if m:
                return m.group(1).upper()

        if self.layout == LAYOUT_TELECOM_COMUNICACAO:
            # Extrai a chave de acesso de 44 dígitos após o rótulo "CHAVE DE ACESSO"
            m = re.search(r'CHAVE\s+DE\s+ACESSO\s*[:\s]*([\d\s]{44,60})', t, re.IGNORECASE)
            if m:
                chave = re.sub(r'\D', '', m.group(1))
                if len(chave) == 44:
                    return chave
            # Fallback: sequência no formato impresso "XXXX XXXX ... XXXX" (11 grupos de 4)
            m2 = re.search(r'\b(?:\d{4}\s+){10}\d{4}\b', t)
            if m2:
                chave = re.sub(r'\D', '', m2.group(0))
                if len(chave) == 44:
                    return chave
            return 'TELECOM'

        if self.layout == LAYOUT_PASSWORD_ENOTAS:
            # "CÓDIGO DE VERIFICAÇÃO\n\n043BE7B2F" — valor alfanumérico logo após
            # o rótulo próprio (o rótulo genérico abaixo também casaria, mas
            # ancoramos aqui para evitar depender da ordem das seções).
            m = re.search(r'C[ÓO]DIGO\s+DE\s+VERIFICA[ÇC][ÃA]O\s*[\n\s]*([A-Z0-9]+)', t, re.IGNORECASE)
            if m:
                return m.group(1).strip().upper()

        if self.layout == LAYOUT_IACU_NFSE:
            # "Código de Verificação:\n\nc5cae3fd79" (recorte do cabeçalho). É um
            # hash alfanumérico minúsculo — preservamos exatamente como impresso
            # (sem uppercase), pois é a chave de consulta de autenticidade.
            m = re.search(r'C[óo]digo\s+de\s+Verifica[çc][ãa]o\s*:?\s*[\n\s]*([A-Za-z0-9]{6,})', t, re.IGNORECASE)
            if m:
                return m.group(1).strip()

        # Brasília/DF: Extração específica do Código de Autenticidade (DPS)
        if self.layout == LAYOUT_BRASILIA:
            return self._extrair_codigo_autenticidade_brasilia()

        if self.layout == LAYOUT_LAURO_FREITAS:
            # O valor real ("579312F9A") não fica colado ao rótulo "Código de
            # Verificação" — entre os dois há um parágrafo inteiro de aviso de
            # autenticidade ("A autenticidade desta Nota... QR Code."), então os
            # padrões genéricos abaixo (que exigem proximidade) não capturam
            # nada útil. Buscamos, na janela entre o rótulo e o cabeçalho
            # "PRESTADOR DE SERVIÇOS" seguinte, o único token que mistura
            # letras e dígitos (o parágrafo de aviso é só texto corrido).
            m_lab = re.search(r'C[oó]digo\s+de\s+Verifica[çc][aã]o', t, re.IGNORECASE)
            m_prest = re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
            if m_lab and m_prest and m_prest.start() > m_lab.end():
                janela = t[m_lab.end():m_prest.start()]
                for m_cod in re.finditer(r'\b([A-Z0-9]{6,15})\b', janela):
                    candidato = m_cod.group(1)
                    if re.search(r'\d', candidato) and re.search(r'[A-Z]', candidato):
                        return candidato

        if self.layout == LAYOUT_SALVADOR:
            # O rótulo "Código de Verificação" quase sempre sai truncado/corrompido
            # no OCR (ex.: "césigo de Verificação", "aésigo de Verificação"), mas a
            # palavra "Verificação" em si e o valor logo abaixo saem legíveis de
            # forma consistente (ver _ocr_header_box_salvador). Ancoramos só em
            # "erificação" e exigimos que o candidato misture letras e dígitos —
            # uma palavra só-letras que caia na janela (ex.: fragmento de rótulo
            # como "ador") nunca é o código real.
            m = re.search(r'erifica[çc][aã]o\s*:?[\s\S]{0,20}?([A-Z0-9]{3,5}-?[A-Z0-9]{2,6})', t, re.IGNORECASE)
            if m:
                candidato = re.sub(r'[^A-Z0-9]', '', m.group(1).upper())
                if len(candidato) >= 6 and re.search(r'\d', candidato) and re.search(r'[A-Z]', candidato):
                    return candidato

        if self.layout == LAYOUT_CUIABA:
            # ISSNet Cuiabá: o código de autenticidade (ex.: "3B3DC3576") aparece
            # no cabeçalho, sem rótulo estável no OCR. É o primeiro token de 7-10
            # caracteres que MISTURA letra maiúscula e dígito — CNPJ/CEP/telefone/
            # NBS são só dígitos (não casam) e o restante do texto é palavra pura.
            for m in re.finditer(r'\b([0-9A-Z]{7,10})\b', t):
                cand = m.group(1)
                if re.search(r'[A-Z]', cand) and re.search(r'\d', cand):
                    return cand

        if self.layout == LAYOUT_NACIONAL:
            # DANFSe Nacional não tem "Código de Verificação" — sua identidade e
            # autenticidade são a Chave de Acesso de 50 dígitos ("Chave de Acesso
            # da NFS-e"), que também é a chave de consulta no portal nacional.
            # Preenche o <CodigoVerificacao> do XML (decisão do usuário). É a única
            # sequência contígua de 50 dígitos do documento (CNPJ tem 14).
            m = re.search(r'\b(?:\d\s*){50,60}\b', t)
            if m:
                chave = re.sub(r'\D', '', m.group(0))
                if len(chave) >= 50:
                    return chave[:50]

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
                if len(res) >= 4: return res
        
        return 'XXXX-XXXX'
    
    def _extrair_codigo_autenticidade_brasilia(self) -> str:
        """
        Extrai o Código de Autenticidade específico do layout Brasília/DF.
        
        O código aparece na seção "Código de Autenticidade" ou "Data Emissão da DPS"
        como uma sequência numérica contínua (ex: 530001081224929857000159000000000118226051779414799)
        """
        t = self.raw_text

        # Padrão 1: Após "Código de Autenticidade" ou "Cód. de Autenticidade".
        # O código real costuma vir em dois grupos numéricos separados por
        # espaço (ex: "...517794 14799") que devem ser concatenados — por
        # isso é tratado à parte da lista genérica abaixo, que só usa o
        # maior grupo (semântica diferente, ver Padrão 2).
        m_auth = re.search(
            r'C[oó]d(?:igo)?\s+de\s+Autenticidade\s*[:\s\n]*(\d{20,})(?:\s+(\d+))?',
            t, re.IGNORECASE
        )
        if m_auth:
            code = m_auth.group(1) + (m_auth.group(2) or '')
            code_clean = re.sub(r'[^0-9]', '', code).strip()
            if len(code_clean) >= 20:
                print(f"DEBUG: Brasília CodAut match: '{code_clean}'")
                return code_clean

        patterns = [
            # Padrão 2: Na seção de "Data Emissão da DPS" (sequência numérica longa)
            r'Data\s+Emiss[aã]o\s+da\s+DPS\s*[:\s\n]*(\d{10,20})\s+(\d{20,})',
            # Padrão 3: Genérico - série da DPS (número longo após identificadores)
            r'S[eé]rie\s+da\s+DPS\s*[:\s\n]*(\d{20,})',
            # Padrão 4: Sequência numérica longa isolada (fallback)
            r'(\d{44,})',  # Código de autenticidade típico tem 44 dígitos
        ]
        
        for p in patterns:
            m = re.search(p, t, re.IGNORECASE)
            if m:
                # Se houver múltiplos grupos, pega o maior (código de autenticidade)
                groups = [g for g in m.groups() if g and isinstance(g, str)]
                if groups:
                    code = max(groups, key=len) if len(groups) > 1 else groups[0]
                    code_clean = re.sub(r'[^0-9]', '', code).strip()
                    if len(code_clean) >= 20:  # Código de autenticidade deve ter pelo menos 20 dígitos
                        print(f"DEBUG: Brasília CodAut match: '{code_clean}'")
                        return code_clean
        
        print(f"DEBUG: Brasília - Código de Autenticidade não encontrado, retornando fallback")
        return 'XXXX-XXXX'

    def _extrair_entidade(self, tipo: str) -> Optional[Entidade]:
        t = self.raw_text
        is_prestador = (tipo.lower() == 'prestador')
        is_intermediario = (tipo.lower() == 'intermediario')

        if self.layout == LAYOUT_TELECOM_COMUNICACAO:
            if is_intermediario:
                return None
            if is_prestador:
                return self._extrair_prestador_telecom(t)
            else:
                return self._extrair_tomador_telecom(t)

        # São Paulo/SP digital: em algumas notas reais (ex. AMIL/TEMIS,
        # 2026-07-31) o pdfminer extrai o texto numa ordem física diferente da
        # visual — os cabeçalhos "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS"
        # ficam DESLOCADOS no meio dos próprios dados da entidade (o CNPJ do
        # prestador chega a vazar sozinho, antes de qualquer cabeçalho). O
        # extrator genérico delimita bloco por cabeçalho de seção e erra o
        # alvo nesse caso (CNPJ do prestador vira o do tomador; razão social
        # do tomador vira o bairro dele). Gateado pelo rótulo "Bairro:" —
        # marca específica deste template de campos, ausente no mock sintético
        # mais simples que já cobre o caminho genérico (test_sao_paulo_layout).
        if self.layout == LAYOUT_SAO_PAULO and not is_intermediario and re.search(r'Bairro\s*:', t, re.IGNORECASE):
            return self._extrair_entidade_sao_paulo(is_prestador)

        if self.layout == LAYOUT_OSASCO_REPASSE:
            if is_intermediario:
                return None
            return self._extrair_entidade_osasco_repasse(is_prestador)

        if self.layout == LAYOUT_CAMPINAS:
            if is_intermediario:
                return None
            # Duas estruturas de texto possíveis para o MESMO layout:
            #  - PDF imagem/escaneado (OCR): grade com vários campos por linha
            #    ("CPF/CNPJ NIF Inscrição Municipal Telefone" numa linha só).
            #  - PDF digital (pdfminer): tabela de 2 colunas extraída campo a campo,
            #    com rótulo e valor em linhas próprias e as colunas intercaladas.
            if re.search(r'CPF\s*/?\s*CNPJ\s*/?\s*NIF[ \t]+(?:Inscri|Telefone)', t, re.IGNORECASE):
                return self._extrair_entidade_campinas(is_prestador)
            return self._extrair_entidade_campinas_digital(is_prestador)

        if self.layout == LAYOUT_FATURA_LOCACAO_GENERICA:
            if is_intermediario:
                return None
            return self._extrair_entidade_fatura_locacao_generica(is_prestador)

        if self.layout == LAYOUT_ARMAC_LOCACAO:
            if is_intermediario:
                return None
            return self._extrair_entidade_armac(is_prestador)

        if self.layout == LAYOUT_IACU_NFSE:
            if is_intermediario:
                return None
            return self._extrair_entidade_iacu(is_prestador)

        if self.layout == LAYOUT_MATA_SAO_JOAO:
            if is_intermediario:
                return None
            return self._extrair_entidade_mata_sao_joao(is_prestador)

        if self.layout == LAYOUT_ROSARIO_LIMEIRA:
            if is_intermediario:
                return None
            return self._extrair_entidade_rosario_limeira(is_prestador)

        if self.layout == LAYOUT_CAMACARI_AVULSA:
            if is_intermediario:
                return None
            return self._extrair_entidade_camacari_avulsa(is_prestador)

        if self.layout == LAYOUT_CAMACARI_2:
            if is_intermediario:
                return None
            ent = self._extrair_entidade_camacari2(is_prestador)
            if ent is not None:
                return ent
            # fall-through: cai no extrator genérico (superset) se o dedicado
            # não conseguir montar a entidade.

        if self.layout == LAYOUT_SULSEG_COBRANCA:
            if is_intermediario:
                return None
            if is_prestador:
                # Emitente fixo (mesma empresa/IM/IBGE já validados no layout
                # de NFS-e da SUL&SEG — a nota de cobrança traz Inscrição
                # Estadual em vez da Municipal, então reaproveitamos a IM
                # já confirmada). Endereço conforme impresso nesta nota.
                mun_cod = _ibge_resolver.extract_and_validate("Lauro de Freitas", "BA", city_hint="Lauro de Freitas")
                return Entidade(
                    cnpj_cpf="18294792000110",
                    razao_social="SUL&SEG SERVICOS DE MANUT ELET EIRELI - ME",
                    inscricao_municipal="0010030574",
                    endereco=Endereco(
                        logradouro="AV. BRIGADEIRO ALBERTO COSTA MATOS",
                        numero="103",
                        bairro="Aracuí",
                        codigo_municipio=mun_cod,
                        municipio="Lauro de Freitas",
                        uf="BA",
                        cep="42702010",
                    ),
                )
            else:
                m_label = re.search(r'C\.N\.P\.J\.?\s*/\s*C\.P\.F\.', t, re.IGNORECASE)
                janela = t[m_label.end(): m_label.end() + 400] if m_label else t

                m_raz = re.search(r'\d+\s*\n+([A-Z][A-Z0-9 .,&-]+?)\s*\n', janela)
                razao = m_raz.group(1).strip() if m_raz else "Tomador Não Identificado"

                m_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', janela)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "00000000000000"

                m_end = re.search(r'ENDERE[CÇ]O\s*\n+(.+?)\n+MUNIC[IÍ]PIO', janela, re.IGNORECASE | re.DOTALL)
                linhas_end = [ln.strip() for ln in m_end.group(1).split('\n') if ln.strip()] if m_end else []
                logradouro = linhas_end[0] if linhas_end else "Não informado"
                complemento = None
                if len(linhas_end) > 1:
                    complemento = ', '.join(linhas_end[1:]).strip() or None

                m_mun = re.search(r'MUNIC[IÍ]PIO\s*\n+(.+?)\n', janela, re.IGNORECASE)
                municipio = m_mun.group(1).strip() if m_mun else "Não informado"

                m_bairro = re.search(r'BAIRRO\s*\n+(.+?)\n', janela, re.IGNORECASE)
                bairro = m_bairro.group(1).strip() if m_bairro else "Não informado"

                m_cep = re.search(r'CEP\s*\n+([\d-]+)', janela, re.IGNORECASE)
                cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else "00000000"

                m_uf = re.search(r'\bUF\s*\n+([A-Z]{2})', janela, re.IGNORECASE)
                uf = m_uf.group(1).strip() if m_uf else "BA"

                mun_cod = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio, raw_doc_text=t)

                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao,
                    endereco=Endereco(
                        logradouro=logradouro,
                        numero="S/N",
                        complemento=complemento,
                        bairro=bairro,
                        codigo_municipio=mun_cod,
                        municipio=municipio,
                        uf=uf,
                        cep=cep,
                    ),
                )

        if self.layout == LAYOUT_PASSWORD_ENOTAS:
            if is_intermediario:
                return None
            return self._extrair_entidade_password_enotas(is_prestador)

        if self.layout == LAYOUT_CPE_LOCACAO:
            if is_prestador:
                mun_cod = _ibge_resolver.extract_and_validate("Lauro de Freitas", "BA")
                return Entidade(
                    cnpj_cpf="07712781000196",
                    razao_social="CPE BAHIA COM DE APARELHOS TOP",
                    inscricao_municipal="001001798011",
                    endereco=Endereco(
                        logradouro="RUA A, COND. EMPRESARIAL LIT.NORTE CELNOR, GP-13B",
                        numero="GP-13B",
                        bairro="ITINGA",
                        codigo_municipio=mun_cod,
                        municipio="Lauro de Freitas",
                        uf="BA",
                        cep="42700000"
                    )
                )
            elif is_intermediario:
                return None
            else:
                m_cli_label = re.search(r'Dados\s+do\s+Cl[ie]nte', t, re.IGNORECASE)
                pos_cli = m_cli_label.start() if m_cli_label else t.find("Dados do Cliente")
                bloco_cli = t[pos_cli:] if pos_cli != -1 else t
                
                m_cnpj = re.search(r'CNPJ\s*/\s*CPF\s*[:\s]*([\d./-]+)', bloco_cli, re.IGNORECASE)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "00000000000000"
                
                m_raz = re.search(r'Nome\s*/\s*Raz[aã]o\s+Social\s*[:\s]*(.+)', bloco_cli, re.IGNORECASE)
                razao = m_raz.group(1).split('\n')[0].strip() if m_raz else ""
                
                m_end = re.search(r'Endere[cç]o\s*[:\s]*(.+)', bloco_cli, re.IGNORECASE)
                endereco_rua = m_end.group(1).split('\n')[0].strip() if m_end else ""
                
                m_bairro = re.search(r'Bairro\s*[:\s]*(.+)', bloco_cli, re.IGNORECASE)
                bairro = m_bairro.group(1).split('\n')[0].strip() if m_bairro else ""
                
                m_cep = re.search(r'Cep\s*[:\s]*(\d+)', bloco_cli, re.IGNORECASE)
                cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else "00000000"
                
                m_mun = re.search(r'Munic[ií]pio\s*[:\s]*(.+)', bloco_cli, re.IGNORECASE)
                mun = m_mun.group(1).split('\n')[0].strip() if m_mun else ""
                
                m_uf = re.search(r'U\.F\.\s*[:\s]*([A-Z]{2})', bloco_cli, re.IGNORECASE)
                uf = m_uf.group(1).strip() if m_uf else "BA"
                
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf)
                
                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao or "Cliente Não Identificado",
                    endereco=Endereco(
                        logradouro=endereco_rua or "Não informado",
                        numero="S/N",
                        bairro=bairro or "Não informado",
                        codigo_municipio=mun_cod,
                        municipio=mun or "Não informado",
                        uf=uf,
                        cep=cep or "00000000"
                    )
                )

        if self.layout == LAYOUT_GUINCHO_CIDADE:
            if is_prestador:
                mun_cod = _ibge_resolver.extract_and_validate("Feira de Santana", "BA")
                return Entidade(
                    cnpj_cpf="14318419000109",
                    razao_social="GUINCHO CIDADE EIRELI",
                    endereco=Endereco(
                        logradouro="RUA PORTO DA VITORIA",
                        numero="18",
                        bairro="NOVO HORIZONTE",
                        codigo_municipio=mun_cod,
                        municipio="Feira de Santana",
                        uf="BA",
                        cep="44000000"
                    )
                )
            elif is_intermediario:
                return None
            else:
                pos_cli = t.find("DESTINATÁRIO")
                bloco_cli = t[pos_cli:] if pos_cli != -1 else t
                
                m_cnpj = re.search(r'CNPJ\s*[:\s]*([\d./-]+)', bloco_cli, re.IGNORECASE)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "00000000000000"
                
                m_raz = re.search(r'RAZAO\s+SOCIAL\s*[:\s]*([^C\n]+)', bloco_cli, re.IGNORECASE)
                razao = m_raz.group(1).strip() if m_raz else ""
                
                m_end = re.search(r'Endere[cç]o\s*[:\s]*(.+)', bloco_cli, re.IGNORECASE)
                endereco_full = m_end.group(1).split('\n')[0].strip() if m_end else ""
                
                m_num = re.search(r'N[ºo°]\s*(\d+)', endereco_full, re.IGNORECASE)
                numero = m_num.group(1).strip() if m_num else "S/N"
                logradouro = re.sub(r'N[ºo°]\s*\d+', '', endereco_full).strip()
                
                m_bairro = re.search(r'Bairro\s*[:\s]*([^\nC]+)', bloco_cli, re.IGNORECASE)
                bairro = m_bairro.group(1).strip() if m_bairro else ""
                if not bairro or "cidade" in bairro.lower():
                    bairro = "IAPI"
                
                m_cep = re.search(r'CEP\s*[:\s]*([\d.-]+)', bloco_cli, re.IGNORECASE)
                cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else "00000000"
                
                m_mun = re.search(r'Cidade\s*[:\s]*([^U\n]+)', bloco_cli, re.IGNORECASE)
                mun = m_mun.group(1).strip() if m_mun else "SALVADOR"
                
                m_uf = re.search(r'UF\s*[:\s]*([A-Z]{2})', bloco_cli, re.IGNORECASE)
                uf = m_uf.group(1).strip() if m_uf else "BA"
                
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf)
                
                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao or "Cliente Não Identificado",
                    endereco=Endereco(
                        logradouro=logradouro or "Não informado",
                        numero=numero,
                        bairro=bairro or "Não informado",
                        codigo_municipio=mun_cod,
                        municipio=mun or "Não informado",
                        uf=uf,
                        cep=cep or "00000000"
                    )
                )

        if self.layout == LAYOUT_BF_AMBIENTAIS:
            if is_prestador:
                mun_cod = _ibge_resolver.extract_and_validate("Salvador", "BA")
                return Entidade(
                    cnpj_cpf="34425389000139",
                    razao_social="B.F. SERVICOS AMBIENTAIS EIRELI",
                    inscricao_municipal="7745600150",
                    endereco=Endereco(
                        logradouro="R CARIPARE (LOT GJAS R P VARGAS)",
                        numero="S/N",
                        bairro="GRANJAS RURAIS PRESIDENTE VARGAS",
                        codigo_municipio=mun_cod,
                        municipio="Salvador",
                        uf="BA",
                        cep="41230075"
                    ),
                    telefone="7132393501"
                )
            elif is_intermediario:
                return None
            else:
                pos_cli = t.find("Cliente:")
                bloco_cli = t[pos_cli:] if pos_cli != -1 else t
                
                m_cnpj = re.search(r'CNPJ\s*[:\s]*([\d./-]+)', bloco_cli, re.IGNORECASE)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "00000000000000"
                
                m_raz = re.search(r'Cliente\s*:\s*\n*\s*(.+)', bloco_cli, re.IGNORECASE)
                razao = m_raz.group(1).split('\n')[0].strip() if m_raz else ""
                
                m_end = re.search(r'RUA\s+CAMBORIU.*', bloco_cli, re.IGNORECASE)
                endereco_line = m_end.group(0).split('\n')[0].strip() if m_end else ""
                
                logradouro = "RUA CAMBORIU"
                numero = "39"
                bairro = "IAPI"
                if " - " in endereco_line:
                    left, right = endereco_line.split(" - ")
                    bairro = right.strip()
                    if "," in left:
                        logradouro, numero = [x.strip() for x in left.split(",")]
                
                m_cep = re.search(r'CEP\s*[:\s]*([\d.-]+)', bloco_cli, re.IGNORECASE)
                cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else "40330533"
                
                m_mun = re.search(r'Salvador\s*-\s*BA', bloco_cli, re.IGNORECASE)
                mun = "Salvador" if m_mun else "Salvador"
                uf = "BA"
                
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf)
                
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', bloco_cli)
                email_tomador = ",".join(emails) if emails else None
                
                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao or "DELTALINE SERVICOS LTDA.",
                    endereco=Endereco(
                        logradouro=logradouro,
                        numero=numero,
                        bairro=bairro,
                        codigo_municipio=mun_cod,
                        municipio=mun,
                        uf=uf,
                        cep=cep
                    ),
                    email=email_tomador
                )

        if self.layout == LAYOUT_LMR_ENGENHARIA:
            if is_prestador:
                mun_cod = _ibge_resolver.extract_and_validate("CAMPINA GRANDE", "PB")
                return Entidade(
                    cnpj_cpf="25177534000208",
                    razao_social="LMR ENGENHARIA E CONSTRUÇÃO EIRELI",
                    endereco=Endereco(
                        logradouro="RUA JOSÉ ERMÍRIO DE MORAES",
                        numero="310",
                        bairro="DISTRITO INDUSTRIAL",
                        codigo_municipio=mun_cod,
                        municipio="CAMPINA GRANDE",
                        uf="PB",
                        cep="58411570"
                    ),
                    telefone="8321547188"
                )
            elif is_intermediario:
                return None
            else:
                pos_cli = t.find("Cliente:")
                bloco_cli = t[pos_cli:] if pos_cli != -1 else t
                
                m_cnpj = re.search(r'CNPJ\s*[:\s]*([\d./-]+)', bloco_cli, re.IGNORECASE)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "01813680000125"
                
                m_raz = re.search(r'Cliente\s*:\s*(.+)', bloco_cli, re.IGNORECASE)
                razao = m_raz.group(1).split('\n')[0].strip() if m_raz else "DELTALINE SERVIÇOS LTDA"
                
                m_end = re.search(r'Endere[cç]o\s*[:\s]*(.+)', bloco_cli, re.IGNORECASE)
                endereco_line = m_end.group(1).split('\n')[0].strip() if m_end else "Rua Camboriu, 39 - IAPI - SALVADOR-BA"
                
                endereco_line = endereco_line.replace('–', '-').replace('—', '-').replace('', '-')
                logradouro = "Rua Camboriu"
                numero = "39"
                bairro = "IAPI"
                mun = "SALVADOR"
                uf = "BA"
                cep = "40330533"
                
                parts = [p.strip() for p in endereco_line.split('-')]
                if len(parts) >= 1:
                    left = parts[0]
                    if ',' in left:
                        logradouro, numero = [x.strip() for x in left.split(',')]
                if len(parts) >= 2:
                    bairro = parts[1]
                if len(parts) >= 3:
                    mun_uf = parts[2]
                    if ',' in mun_uf:
                        mun, uf = [x.strip() for x in mun_uf.split(',')]
                    elif ' ' in mun_uf:
                        mun = mun_uf.strip()[:-2].strip()
                        uf = mun_uf.strip()[-2:].strip()
                    else:
                        mun = mun_uf
                
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf)
                
                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao,
                    endereco=Endereco(
                        logradouro=logradouro,
                        numero=numero,
                        bairro=bairro,
                        codigo_municipio=mun_cod,
                        municipio=mun,
                        uf=uf,
                        cep=cep
                    )
                )

        if self.layout == LAYOUT_GERACAO_ENERGIA:
            if is_prestador:
                mun_cod = _ibge_resolver.extract_and_validate("Salvador", "BA")
                return Entidade(
                    cnpj_cpf="03292008000167",
                    razao_social="GERAÇÃO E ENERGIA SERVIÇOS E COMÉRCIO LTDA",
                    inscricao_municipal="ISENTO",
                    endereco=Endereco(
                        logradouro="Rua Gonçalo Coelho",
                        numero="77",
                        bairro="Pituaçu",
                        codigo_municipio=mun_cod,
                        municipio="Salvador",
                        uf="BA",
                        cep="41741120"
                    ),
                    telefone="7132323999"
                )
            elif is_intermediario:
                return None
            else:
                pos_cli = t.find("USUÁRIO FINAL OU DESTINATÁRIO")
                if pos_cli == -1:
                    pos_cli = t.find("DELTALINE")
                bloco_cli = t[pos_cli:] if pos_cli != -1 else t
                
                m_cnpj = re.search(r'CNPJ\s*/\s*CPF\s*[:\s]*([\d./-]+)', bloco_cli, re.IGNORECASE)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "01813680000125"
                
                m_raz = re.search(r'NOME\s*:\s*(.+)', bloco_cli, re.IGNORECASE)
                razao = m_raz.group(1).split('\n')[0].strip() if m_raz else "DELTALINE SERVICOS LTDA."
                
                m_end = re.search(r'ENDERE[CÇ]O\s*:\s*(.+)', bloco_cli, re.IGNORECASE)
                endereco_line = m_end.group(1).split('\n')[0].strip() if m_end else "RUA CAMBORIÚ, 39"
                
                logradouro = "RUA CAMBORIÚ"
                numero = "39"
                if ',' in endereco_line:
                    logradouro, numero = [x.strip() for x in endereco_line.split(',')]
                
                m_bairro = re.search(r'BAIRRO\s*:\s*(.+)', bloco_cli, re.IGNORECASE)
                bairro = m_bairro.group(1).split('\n')[0].strip() if m_bairro else "IAPI"
                
                m_cep = re.search(r'CEP\s*:\s*([\d.-]+)', bloco_cli, re.IGNORECASE)
                cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else "40330533"
                
                m_mun = re.search(r'MUNIC[IÍ]PIO\s*:\s*(.+)', bloco_cli, re.IGNORECASE)
                mun = m_mun.group(1).split('\n')[0].strip() if m_mun else "SALVADOR"
                
                m_uf = re.search(r'ESTADO\s*:\s*([A-Z]{2})', bloco_cli, re.IGNORECASE)
                uf = m_uf.group(1).strip() if m_uf else "BA"
                
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf)
                
                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao,
                    endereco=Endereco(
                        logradouro=logradouro,
                        numero=numero,
                        bairro=bairro,
                        codigo_municipio=mun_cod,
                        municipio=mun,
                        uf=uf,
                        cep=cep
                    )
                )

        if self.layout == LAYOUT_LOCONTAINERS:
            if is_prestador:
                mun_cod = _ibge_resolver.extract_and_validate("Salvador", "BA")
                return Entidade(
                    cnpj_cpf="00111704000131",
                    razao_social="VIDAL LOCAÇÃO E COMÉRCIO DE CONTAINERS LTDA",
                    inscricao_municipal="37776300172",
                    endereco=Endereco(
                        logradouro="AVENIDA PAULO VI",
                        numero="1984",
                        bairro="PITUBA",
                        codigo_municipio=mun_cod,
                        municipio="Salvador",
                        uf="BA",
                        cep="41810001"
                    ),
                    telefone="7133550157"
                )
            elif is_intermediario:
                return None
            else:
                pos_cli = t.find("DADOS DO CLIENTE")
                bloco_cli = t[pos_cli:] if pos_cli != -1 else t
                
                m_cnpj = re.search(r'CNPJ\s*/\s*CPF\s*[\n\r\s]+([\d\./-]+)', bloco_cli, re.IGNORECASE)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "01813680000125"
                
                m_raz = re.search(r'NOME\s*/\s*RAZ[AÃÕO\s]+/s*SOCIAL\s*[\n\r\s]+([^\n\r]+)', bloco_cli, re.IGNORECASE)
                if not m_raz:
                    m_raz = re.search(r'NOME\s*/\s*RAZ[AÃÕO]*\s+SOCIAL\s*[\n\r\s]+([^\n\r]+)', bloco_cli, re.IGNORECASE)
                razao = m_raz.group(1).strip() if m_raz else "DELTALINE SERVICOS LTDA"
                
                m_end = re.search(r'ENDERE[CÇ]O\s*[\n\r\s]+([^\n\r]+)', bloco_cli, re.IGNORECASE)
                endereco_line = m_end.group(1).strip() if m_end else "RUA CAMBORIU"
                
                logradouro = endereco_line
                numero = ""
                if ',' in endereco_line:
                    logradouro, numero = [x.strip() for x in endereco_line.split(',')]
                
                m_bairro = re.search(r'BAIRRO\s*/\s*DISTRITO\s*[\n\r\s]+([^\n\r]+)', bloco_cli, re.IGNORECASE)
                bairro = m_bairro.group(1).strip() if m_bairro else "IAPI"
                
                m_cep = re.search(r'CEP\s*[\n\r\s]+([\d\.-]+)', bloco_cli, re.IGNORECASE)
                cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else "40330533"
                
                m_mun = re.search(r'MUNICIPIO\s*[\n\r\s]+([^\n\r]+)', bloco_cli, re.IGNORECASE)
                mun = m_mun.group(1).strip() if m_mun else "SALVADOR"
                
                m_uf = re.search(r'U\.F\.\s*[\n\r\s]+([A-Z]{2})', bloco_cli, re.IGNORECASE)
                uf = m_uf.group(1).strip() if m_uf else "BA"
                
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf)
                
                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao,
                    endereco=Endereco(
                        logradouro=logradouro,
                        numero=numero,
                        bairro=bairro,
                        codigo_municipio=mun_cod,
                        municipio=mun,
                        uf=uf,
                        cep=cep
                    )
                )

        if self.layout == LAYOUT_FF_LOCACAO:
            if is_prestador:
                mun_cod = _ibge_resolver.extract_and_validate("Camaçari", "BA", city_hint="Camaçari")
                return Entidade(
                    cnpj_cpf="13398812000189",
                    razao_social="F&F COMÉRCIO E SERVIÇOS DE TELECOMUNICAÇÕES DE SEGURANÇA ELETRÔNICA LTDA",
                    endereco=Endereco(
                        logradouro="Rua Senhor do Bomfim",
                        numero="544",
                        complemento="Loja 02",
                        bairro="Monte Gordo",
                        codigo_municipio=mun_cod,
                        municipio="Camaçari",
                        uf="BA",
                        cep="42839852"
                    ),
                    telefone="40628609"
                )
            elif is_intermediario:
                return None
            else:
                # Bloco do tomador delimitado pelo marcador "DESTINATARIO" -
                # sem isso, os rótulos abaixo casariam primeiro com os dados
                # do prestador (que usa os mesmos rótulos ENDEREÇO/CEP/CNPJ).
                pos_dest = t.find("DESTINATARIO")
                bloco_dest = t[pos_dest:] if pos_dest != -1 else t

                # "RAZÃO 7396 - Boutique Guarajuba PH Gestão\nSOCIAL" - rótulo
                # de 2 linhas ("RAZÃO"/"SOCIAL") quebrado pelo OCR em torno do
                # valor de uma linha só. Mantém o código de cliente ("7396 -")
                # colado, tal como impresso - não fabricar uma separação que a
                # nota não delimita.
                m_raz = re.search(r'RAZ[ÃA]O\s+(.+?)\s*\n\s*SOCIAL', bloco_dest, re.IGNORECASE)
                razao = re.sub(r'\s+', ' ', m_raz.group(1)).strip() if m_raz else "Tomador Não Identificado"

                m_cnpj = re.search(r'CNPJ\s*/\s*CPF\s*:?\s*([\d./-]+)', bloco_dest, re.IGNORECASE)
                cnpj_tomador = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "00000000000000"

                # "ENDEREÇO: GUARAJUBA, 0 Pousada Boutique Guarajuba - CNPJ/CPF: ..."
                # - o rótulo "CNPJ/CPF" da coluna vizinha cola direto no fim do
                # endereço (mesmo efeito de colunas intercaladas já visto em
                # Localiza/São Paulo). O endereço aqui é o nome do próprio
                # estabelecimento, não rua+número tradicional - extrai como
                # está, sem inventar uma estrutura que a nota não tem.
                m_end = re.search(r'ENDERE[ÇC]O\s*:\s*(.+?)\s*-\s*CNPJ', bloco_dest, re.IGNORECASE | re.DOTALL)
                logradouro = "Não informado"
                if m_end:
                    logradouro = re.sub(r'\s+', ' ', m_end.group(1)).strip()
                    # "GUARAJUBA, 0 Pousada..." - "0" isolado logo após a
                    # vírgula é ruído do OCR (não há número de rua nesta nota).
                    logradouro = re.sub(r',\s*[0O]\s+', ', ', logradouro)

                # Continuação do endereço (bairro/distrito), empurrada para a
                # linha seguinte pela mesma intercalação de colunas.
                m_bairro = re.search(r'CNPJ\s*/\s*CPF\s*:?\s*[\d./-]+\s*\n\s*([^\n]+?)\s*\n\s*CIDADE', bloco_dest, re.IGNORECASE)
                bairro = m_bairro.group(1).strip() if m_bairro else "Não informado"

                m_mun = re.search(r'CIDADE\s*:\s*(.+?)\s*CEP', bloco_dest, re.IGNORECASE)
                municipio = m_mun.group(1).strip() if m_mun else "Camaçari"

                m_cep = re.search(r'CEP\s*:\s*([\d-]+)\s*UF', bloco_dest, re.IGNORECASE)
                cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else ""

                m_uf = re.search(r'UF\s*:\s*([A-Z]{2})', bloco_dest, re.IGNORECASE)
                uf = m_uf.group(1).strip() if m_uf else "BA"

                mun_cod = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio)

                return Entidade(
                    cnpj_cpf=cnpj_tomador,
                    razao_social=razao,
                    endereco=Endereco(
                        logradouro=logradouro,
                        numero="S/N",
                        bairro=bairro,
                        codigo_municipio=mun_cod,
                        municipio=municipio,
                        uf=uf,
                        cep=cep or "00000000"
                    )
                )

        if self.layout == LAYOUT_LAURO_FREITAS:
            if is_intermediario:
                return None
            return self._extrair_entidade_lauro_freitas(is_prestador)

        if self.layout == LAYOUT_LOCALIZA:
            # Notas Localiza reais chegam em pelo menos 2 formatos de texto BEM
            # diferentes, dependendo da nota (mesmo formato de PDF): (a) via OCR
            # (fonte do PDF ilegível para o pdfminer) — texto quebrado em linhas,
            # mas com a ORDEM de "CNPJ -"/"Localiza"/"FATURA / DUPLICATA" e dos
            # campos do tomador variando de nota pra nota; (b) via texto digital
            # do pdfminer (quando a fonte do PDF é legível) — tudo n uma ÚNICA
            # linha corrida, sem quebras, e com a ordem dos campos do tomador
            # diferente da variante OCR. Os regex abaixo evitam depender de "\n"
            # ou de uma ordem fixa entre rótulos — usam âncoras estáveis em
            # QUALQUER um dos formatos (validado contra 4 notas reais de
            # filiais/formatos distintos: Trade Center Pituba, AG Aeroporto
            # Recife, Agência Aeroporto Salvador, Agência Centro Cabula).
            def _split_endereco_localiza(raw_addr: str):
                """"AV TANCREDO NEVES, 1632 - CAMINHO ARVORES" -> logradouro/
                número/bairro/complemento. O bairro é sempre o ÚLTIMO segmento
                separado por hífen (ex.: "RUA TERRITORIO DO AMAPA, 146 CS 2 -
                PITUBA" -> bairro "PITUBA", complemento "CS 2")."""
                m_num = re.search(r',\s*(\d+)', raw_addr)
                if m_num:
                    logradouro = raw_addr[:m_num.start()].strip()
                    numero = m_num.group(1)
                    resto = raw_addr[m_num.end():].strip()
                else:
                    logradouro, numero, resto = raw_addr.strip(), "S/N", ""
                bairro, complemento = "Não informado", None
                if resto:
                    partes = [p.strip() for p in resto.split('-') if p.strip()]
                    if partes:
                        bairro = partes[-1]
                        if len(partes) > 1:
                            complemento = " - ".join(partes[:-1]) or None
                return logradouro or "Não informado", numero, bairro, complemento

            def _strip_texto_colado(raw: str) -> str:
                """Corta um trecho maiúsculo de endereço no 1º pedaço colado sem
                espaço (e-mail do OCR sem "@" legível, parênteses, etc.), sem
                depender de reconhecer o que veio grudado."""
                m = re.match(r'([A-ZÀ-Ú0-9][A-ZÀ-Ú0-9.,\-\s]*?)(?:\s+[a-z(][^\n]*)?\s*$', raw)
                return m.group(1).strip() if m else raw.strip()

            if is_prestador:
                # Bloco do cabeçalho da filial emissora: tudo antes de "FATURA /
                # DUPLICATA" (ou, quando esse rótulo vem colado ao número sem
                # espaço, antes do próprio "Nº: <código> - <dígitos>").
                m_fatura = re.search(r'FATURA\s*/\s*DUPLICATA|N[ºo]\.?\s*:\s*[A-Z]+\s*-?\s*\d+', t, re.IGNORECASE)
                bloco_prest = t[:m_fatura.start()] if m_fatura else t

                # CNPJ e CEP/Município/UF da filial: pega a ÚLTIMA ocorrência
                # antes da fatura — a ordem relativa de "CNPJ -" x "Localiza"
                # (logotipo) varia entre notas, então não fixamos qual vem antes.
                cnpjs = list(re.finditer(r'CNPJ\s*-?\s*:?\s*([\d./-]{14,20})', bloco_prest, re.IGNORECASE))
                m_cnpj_prest = cnpjs[-1] if cnpjs else None
                ceps = list(re.finditer(r'(\d{5}-?\d{3})\s*-\s*([A-Z\s]+?)\s*-\s*([A-Z]{2})\b', bloco_prest, re.IGNORECASE))
                m_cep_prest = ceps[-1] if ceps else None

                logradouro_raw = ""
                if m_cep_prest:
                    antes_cep = bloco_prest[:m_cep_prest.start()]
                    # Endereço sempre começa por um logradouro brasileiro comum
                    # (AV/ROD/RUA/TV/...) — âncora estável tanto se o texto tem
                    # quebras de linha quanto se está tudo numa linha só.
                    m_addr = re.search(
                        r'\b((?:AV|R|ROD|TV|AL|PC|ESTRADA|PRA[ÇC]A|ALAMEDA|TRAVESSA)\.?\s[^\n]*)',
                        antes_cep, re.IGNORECASE)
                    if m_addr:
                        logradouro_raw = _strip_texto_colado(m_addr.group(1))

                cnpj = re.sub(r'\D', '', m_cnpj_prest.group(1)) if m_cnpj_prest else ""
                mun = m_cep_prest.group(2).strip() if m_cep_prest else "SALVADOR"
                uf = m_cep_prest.group(3).strip() if m_cep_prest else "BA"
                cep = re.sub(r'\D', '', m_cep_prest.group(1)) if m_cep_prest else ""
                logradouro, numero, bairro, complemento = _split_endereco_localiza(logradouro_raw)
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf)

                return Entidade(
                    cnpj_cpf=cnpj or "00000000000000",
                    razao_social="LOCALIZA RENT A CAR S/A",
                    endereco=Endereco(
                        logradouro=logradouro, numero=numero, complemento=complemento,
                        bairro=bairro, codigo_municipio=mun_cod, municipio=mun, uf=uf, cep=cep
                    )
                )
            else:
                m_end = re.search(
                    r'ENDERE[ÇC]O:\s*(.+?)\s*CEP/CID/UF:\s*([\d-]+)\s*-\s*([A-Z\s]+?)\s*-\s*([A-Z]{2})',
                    t, re.IGNORECASE | re.DOTALL)

                # A razão social do tomador aparece em 2 formatos: (a) quebrada em
                # 2 fragmentos por colunas intercaladas do OCR — o nome (sem
                # sufixo) fica ANTES do rótulo "CÓDIGO:", e só o sufixo ("LTDA")
                # vem DEPOIS do rótulo "CLIENTE:" (ex.: "...SUSTENTABILIDADE
                # CÓDIGO: 02640209\nCLIENTE: LTDA"); (b) já completa logo após
                # "CLIENTE:" no texto digital sem quebras, só faltando o espaço
                # antes do sufixo societário colado (ex.: "CLIENTE: TEMIS...
                # SUSTENTABILIDADELTDA"). Distinguimos pela ORDEM entre os 2
                # rótulos: se "CLIENTE:" vem ANTES de "CÓDIGO:", é o formato (b).
                m_cliente_label = re.search(r'CLIENTE:', t, re.IGNORECASE)
                m_codigo_label = re.search(r'C[ÓO]DIGO:\s*\d+', t, re.IGNORECASE)
                if m_cliente_label and m_codigo_label and m_cliente_label.start() < m_codigo_label.start():
                    m_full = re.search(r'CLIENTE:\s*(.+?)\s*ENDERE[ÇC]O:', t, re.IGNORECASE | re.DOTALL)
                    razao = re.sub(r'\s+', ' ', m_full.group(1)).strip() if m_full else ""
                    razao = re.sub(r'([A-ZÀ-Ú])\s*(LTDA|EIRELI|S\.A\.?|ME|EPP)\s*$', r'\1 \2', razao, flags=re.IGNORECASE)
                else:
                    nome1 = ""
                    if m_codigo_label:
                        janela = t[max(0, m_codigo_label.start() - 80): m_codigo_label.start()]
                        m_nome1 = re.search(r'([A-ZÀ-Ú][A-ZÀ-Ú0-9.,&\s]*?)\s*$', janela)
                        nome1 = m_nome1.group(1).strip(' .—-') if m_nome1 else ""
                    m_nome2 = re.search(
                        r'CLIENTE:\s*(.+?)(?=\s*ENDERE[ÇC]O:|\s*C[ÓO]DIGO:|\s*INSC)', t, re.IGNORECASE | re.DOTALL)
                    nome2 = re.sub(r'\s+', ' ', m_nome2.group(1)).strip() if m_nome2 else ""
                    if nome1 and nome2 and nome2.upper() not in nome1.upper():
                        razao = f"{nome1} {nome2}".strip()
                    else:
                        razao = nome2 or nome1

                # O CNPJ do tomador só é buscado DEPOIS do endereço (janela
                # restrita) — buscar no texto inteiro pegava o 1º "CNPJ:" do
                # documento, que é o do PRESTADOR (Localiza), não o do cliente.
                cnpj = ""
                if m_end:
                    m_cnpj = re.search(r'CNPJ:\s*([\d./-]+)', t[m_end.end():], re.IGNORECASE)
                    cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else ""

                logradouro_raw = m_end.group(1).strip() if m_end else ""
                logradouro, numero, bairro, complemento = _split_endereco_localiza(logradouro_raw)
                cep = re.sub(r'\D', '', m_end.group(2)) if m_end else ""
                mun = m_end.group(3).strip() if m_end else ""
                uf = m_end.group(4).strip() if m_end else ""
                mun_cod = _ibge_resolver.extract_and_validate(mun, uf) if mun else _ibge_resolver.default_code

                return Entidade(
                    cnpj_cpf=cnpj or "00000000000000", razao_social=razao or "Não Identificado",
                    endereco=Endereco(
                        logradouro=logradouro, numero=numero, complemento=complemento,
                        bairro=bairro, codigo_municipio=mun_cod, municipio=mun or None, uf=uf or _ibge_resolver.default_uf,
                        cep=cep or "00000000"
                    )
                )

        def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p

        # Salvador escaneado (OCR): esta variante NÃO traz cabeçalho "TOMADOR".
        # Prestador e tomador são dois blocos consecutivos delimitados apenas
        # pelos rótulos "Nome/Razão Social" — o prestador sob "PRESTADOR DE
        # SERVIÇOS" (ordem CPF/CNPJ → Nome → Endereço) e o tomador logo abaixo,
        # SEM rótulo próprio (ordem invertida: Nome → CPF/CNPJ → Endereço). Sem
        # este recorte, a busca genérica pelo rótulo "TOMADOR" falha, o bloco
        # vira o texto inteiro e o tomador acaba herdando o 1º CNPJ/nome/endereço
        # (os do prestador). Só ativa quando NÃO há rótulo de tomador — a variante
        # digital rotulada ("TOMADOR DE SERVIÇOS" + "Município:/UF:") segue no
        # caminho genérico já testado, sem risco de regressão.
        bloco_sv = None
        if self.layout == LAYOUT_SALVADOR and not is_intermediario:
            tem_label_tomador = re.search(
                "|".join(relax(l) for l in _LABELS_TOMADOR), t, re.IGNORECASE)
            nomes = list(re.finditer(r'Nome\s*/?\s*Raz[ãa]o\s+Social', t, re.IGNORECASE))
            if not tem_label_tomador and len(nomes) >= 2:
                m_disc = re.search(r'DISCRIMINA[ÇC][ÃA]O', t, re.IGNORECASE)
                disc_pos = m_disc.start() if m_disc else len(t)
                if is_prestador:
                    m_prest = re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]O', t, re.IGNORECASE)
                    ini = m_prest.start() if m_prest else 0
                    bloco_sv = t[ini: nomes[1].start()]
                else:
                    bloco_sv = t[nomes[1].start(): disc_pos]

        # Cuiabá/ISSNet escaneado: em scans degradados o cabeçalho "Dados do
        # Tomador de Serviços" às vezes some por completo do OCR (nota real
        # ANDERSON FAUSTINO/FA TELAS -> São Pedro), fazendo o bloco do PRESTADOR
        # (delimitado genericamente até o próximo rótulo reconhecido) engolir
        # também o CNPJ/Razão/Endereço do TOMADOR até "Dados do Intermediário" —
        # CNPJ sai certo (1º a validar), mas razão/endereço/município saem do
        # TOMADOR. Assinatura estável do layout, presente em ambos os formatos
        # (limpo e degradado): o prestador usa "CPF/CNPJ" (CPF antes do CNPJ),
        # o tomador usa "CNPJ/CPF" ou "CNPJICPF" (CNPJ antes do CPF, a barra
        # vira "I" no OCR) — usamos essa INVERSÃO de ordem como âncora do início
        # do bloco do tomador, independente do rótulo de cabeçalho estar legível.
        bloco_cuiaba = None
        if self.layout == LAYOUT_CUIABA and not is_intermediario:
            m_prest_lab = re.search(r'Dados\s+do\s+Prestador', t, re.IGNORECASE)
            m_tom_anchor = re.search(r'CNPJ\s*[/I]\s*CPF', t, re.IGNORECASE)
            if not m_tom_anchor:
                # Degradação ainda maior (nota real GMS FLATS HOTEL -> São Pedro):
                # nem o rótulo "CNPJ/CPF" sobrevive — o CNPJ do tomador vem NU,
                # seguido na linha seguinte por "Razão Social:". Validado que essa
                # combinação só ocorre no bloco do tomador (nunca no do prestador,
                # que usa CPF/CNPJ com rótulo, mesmo quando o próprio CNPJ sai
                # com pontuação corrompida por vírgula).
                m_tom_anchor = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s*\n\s*Raz[ãa]o\s+Social', t, re.IGNORECASE)
            if m_prest_lab and m_tom_anchor and m_tom_anchor.start() > m_prest_lab.start():
                m_interm_lab = re.search(r'Dados\s+do\s+Intermedi[áa]rio', t, re.IGNORECASE)
                if is_prestador:
                    bloco_normal = t[m_prest_lab.start(): m_tom_anchor.start()]
                    if re.search(r'CPF\s*[/I]\s*CNPJ', bloco_normal, re.IGNORECASE):
                        bloco_cuiaba = bloco_normal
                    elif m_interm_lab:
                        # Prestador REAL deslocado (nota real DR3 TERCEIRIZAÇÃO,
                        # pág.3 do PDF "NFS PRESTADORES ANALISE..."): o cabeçalho
                        # "Dados do Prestador" aparece sem os dados reais logo
                        # em seguida (ali só vem, sem rótulo próprio, o CNPJ do
                        # TOMADOR) — os dados REAIS do prestador (nome/CNPJ)
                        # aparecem mais adiante, sob o cabeçalho "Dados do
                        # Intermediário de Serviços" (a ordem física do OCR
                        # embaralhou os blocos). Só assume esse deslocamento
                        # quando o trecho ali REALMENTE tem a assinatura do
                        # prestador (CPF/CNPJ, CPF antes) — senão mantém o
                        # bloco normal (vazio nas notas sem esse problema),
                        # preservando o comportamento já validado.
                        m_fim = re.search(r'Descri[çc][ãa]o\s+dos?\s+Servi[çc]os?', t[m_interm_lab.start():], re.IGNORECASE)
                        fim_abs = m_interm_lab.start() + m_fim.start() if m_fim else len(t)
                        candidato = t[m_interm_lab.start(): fim_abs]
                        if re.search(r'CPF\s*[/I]\s*CNPJ', candidato, re.IGNORECASE):
                            # Remove o cabeçalho da seção + a linha (vazia) de
                            # colunas da grade do intermediário ("CNPJ/CPF
                            # Inscrição Municipal Razão Social", sem dado real
                            # nenhum) — sem isso, a extração genérica de razão
                            # social bate nesse "Razão Social" de cabeçalho e
                            # engole as linhas seguintes (nome fantasia +
                            # endereço) até o próximo stop-word.
                            candidato_sem_header = re.sub(
                                r'^.*?Raz[ãa]o\s+Social\s*\n*', '', candidato,
                                count=1, flags=re.IGNORECASE | re.DOTALL
                            )
                            bloco_cuiaba = candidato_sem_header if candidato_sem_header.strip() else candidato
                        else:
                            bloco_cuiaba = bloco_normal
                    else:
                        bloco_cuiaba = bloco_normal
                else:
                    fim = m_interm_lab.start() if (m_interm_lab and m_interm_lab.start() > m_tom_anchor.start()) else len(t)
                    bloco_cuiaba = t[m_tom_anchor.start(): fim]

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
                     rf'{relax("Descrição do Serviço")}|{relax("Descrição dos Serviços")}|$'
        
        pattern_bloco = rf'(?:{pattern_labels}).*?(?={delimiters})'
        m_bloco = re.search(pattern_bloco, t, re.IGNORECASE | re.DOTALL)
        
        if is_intermediario and not m_bloco:
            return None

        # Cuiabá/ISSNet: quando o bloco do "Intermediário" carrega a assinatura
        # do PRESTADOR (rótulo "CPF/CNPJ", CPF antes do CNPJ), não é um
        # intermediário de verdade — são os dados REAIS do prestador que a
        # ordem física do OCR deslocou para depois desse cabeçalho (nota real
        # DR3 TERCEIRIZAÇÃO, pág.3 do PDF "NFS PRESTADORES ANALISE..."). Sem
        # este guard, o intermediário "roubaria" o CNPJ/razão do prestador em
        # vez de ficar vazio (None).
        if self.layout == LAYOUT_CUIABA and is_intermediario and m_bloco and \
                re.search(r'CPF\s*[/I]\s*CNPJ', m_bloco.group(0), re.IGNORECASE):
            return None

        if bloco_sv is not None:
            bloco = bloco_sv
        elif bloco_cuiaba is not None:
            bloco = bloco_cuiaba
        else:
            bloco = m_bloco.group(0) if m_bloco else t

        bloco_clean = bloco.replace('|', ' ').replace('!', ' ').replace('\n', ' ').strip()
        bloco_clean = re.sub(r'\s{2,}', ' ', bloco_clean)

        # 2. CNPJ
        cnpj = None
        # Tenta capturar CNPJ validando o checksum para evitar pegar datas ou números
        # Os separadores aceitam espaço em volta: o OCR intercala espaço espúrio
        # antes do dígito verificador ("48.310.477/0001 -08") e o número era descartado.
        matches = re.findall(
            r'(\d{2}\.\d{3}\.\d{3}[ \t]*/[ \t]*\d{4}[ \t]*-[ \t]*\d{2}'
            r'|\d{3}\.\d{3}\.\d{3}[ \t]*-[ \t]*\d{2})',
            bloco
        )
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
                # `d in cnpj` descarta pedaços do próprio CNPJ: quando a pontuação
                # cai, "48.310.477/0001" vira um blob de 12 dígitos que passaria por IM.
                if d != cnpj and d not in cnpj:
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
        # Letra minúscula solta antes do nome: é o ":" do rótulo lido como letra
        # ("Nome/Razão Social:" -> "...Social e"). Só minúscula, para não comer
        # um "E"/"A" legítimo de razão social em caixa alta.
        razao = re.sub(r'^[a-zà-ÿ]\s+(?=[A-ZÀ-Ý])', '', razao).strip()

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
            # Só rejeita como "código" (ex.: verificação/autenticidade) se houver dígito
            # misturado às letras; nomes curtos só-letras (ex.: "CETREL") são razões sociais válidas.
            if re.match(r'^(?=[A-Z0-9-]{6,15}$)(?=.*\d)[A-Z0-9-]+$', line_clean, re.I): return False
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
        m_cep = re.search(rf'{relax("CEP")}\s*[:\- ]*\s*([\d.\- ]+)', bloco_clean, re.IGNORECASE)
        if m_cep:
            end_data['cep'] = re.sub(r'\D', '', m_cep.group(1))

        # Tenta extrair Município e UF
        m_mun = re.search(rf'(?:{relax("Município")}|{relax("Cidade/UF")})\s*([^0-9]+?)(?={relax("CEP")}|{relax("Telefone")}|{relax("E-mail")}|$)', bloco_clean, re.IGNORECASE)
        if m_mun:
            mun_text = m_mun.group(1).strip()
            # Limpeza de possíveis sobras de labels
            mun_text = re.sub(r'^[:\s]+', '', mun_text)
            
            clean_mun = mun_text
            
            # Checa se existe "Estado/Prov./Reg." no texto (Padrão Cuiabá/ISSNet)
            m_estado_prov = re.search(r'Estado/Prov\./Reg\.?\s*[:\s]\s*([A-Z]{2})', mun_text, re.IGNORECASE)
            if m_estado_prov:
                end_data['uf'] = m_estado_prov.group(1).upper()
                clean_mun = re.sub(r'Estado/Prov\./Reg\.?\s*[:\s]\s*[A-Z]{2}', '', clean_mun, flags=re.IGNORECASE).strip()
            
            # Checa se existe "UF: BA" ou "UF BA" no texto de município
            m_uf_in_mun = re.search(r'\bUF\s*[:\s]\s*([A-Z]{2})', mun_text, re.IGNORECASE)
            if m_uf_in_mun:
                end_data['uf'] = m_uf_in_mun.group(1).upper()
                # Descarta tudo a partir do "UF:" (inclusive o que vier depois do código
                # da UF) — texto de outra coluna que "estourou" para essa linha não deve
                # grudar no nome do município.
                clean_mun = clean_mun[:m_uf_in_mun.start()].strip()

            
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
        m_end = re.search(rf'(?:{relax("Endereço")}|{relax("Logradouro")})[:\s]*(.*?)(?={relax("Município")}|{relax("Municipio")}|{relax("CEP")}|{relax("Telefone")}|{relax("E-mail")}|{relax("Bairro")}|{relax("Complemento")}|$)', bloco_clean, re.IGNORECASE | re.DOTALL)
        if m_end:
            partes_end = m_end.group(1).strip().lstrip(':').strip()
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
            elif partes_end:
                end_data['logradouro'] = partes_end

        # Rótulo "Bairro" separado (não embutido na linha de Endereço/Logradouro),
        # comum em layouts de grade (ex.: Camaçari) onde cada campo tem sua própria linha.
        m_bairro_label = re.search(rf'{relax("Bairro")}\s*[:\s]*(.*?)(?={relax("Município")}|{relax("Municipio")}|{relax("CEP")}|{relax("Telefone")}|{relax("E-mail")}|{relax("UF")}|$)', bloco_clean, re.IGNORECASE | re.DOTALL)
        if m_bairro_label:
            bairro_val = m_bairro_label.group(1).strip(' :-')
            if bairro_val:
                end_data['bairro'] = bairro_val

        # Fallback: o rótulo "Bairro:" veio vazio, mas o valor "estourou" para uma
        # linha isolada logo após a linha de UF (renderização em grade/colunas onde
        # o valor não fica na mesma linha do rótulo — mesma classe de problema já
        # visto no "Número da Nota" do Camaçari).
        if end_data.get('bairro') in (None, '', 'Não informado'):
            m_overflow = re.search(
                r'\bUF\s*[:\s]*[A-Z]{2}\s*\n\s*([A-ZÀ-Ú][A-ZÀ-Úa-zà-ú]{2,29})\s*(?:\n|$)',
                bloco, re.IGNORECASE
            )
            if m_overflow:
                candidato = m_overflow.group(1).strip()
                if candidato and not _LABELS_NOISE.match(candidato) and not _NOISE_RAZAO.search(candidato):
                    end_data['bairro'] = candidato

        # Detectar UF com base no Layout ou Regex no endereço (Fallback/Refinamento)
        if not end_data.get('uf') or len(end_data['uf']) != 2 or end_data['uf'] == 'EX':
            if self.layout == LAYOUT_RIO:
                end_data['uf'] = "RJ"
            elif self.layout in (LAYOUT_SALVADOR, LAYOUT_BARREIRAS, LAYOUT_FEIRA, LAYOUT_CAMACARI, LAYOUT_CAMACARI_2, LAYOUT_MATA_SAO_JOAO):
                end_data['uf'] = "BA"
            elif self.layout == LAYOUT_CUIABA:
                end_data['uf'] = "MT"
            else:
                end_data['uf'] = "SP"

        # Refinamento por regex
        UFS_BRASIL = r'AC|AL|AM|AP|BA|CE|DF|ES|GO|MA|MG|MS|MT|PA|PB|PE|PI|PR|RJ|RN|RO|RR|RS|SC|SE|SP|TO'
        m_uf = re.search(rf'\b({UFS_BRASIL})\b', bloco_clean)
        # Se encontrou um UF válido, e o atual está vazio ou é 'EX', atualiza.
        # (Isso impede que um UF EX(exterior) prevaleça se houver MT na string)
        if m_uf and m_uf.group(1):
            if not end_data.get('uf') or end_data['uf'] == 'EX':
                end_data['uf'] = m_uf.group(1).upper()
        
        # Garante MT no layout Cuiabá para Prestador (Emitente) se falhar completamente
        if self.layout == LAYOUT_CUIABA and is_prestador and end_data.get('uf') == 'EX':
            end_data['uf'] = 'MT'

        if self.layout == LAYOUT_SALVADOR:
            # O campo "Endereço" desta nota é texto livre no formato
            # "<logradouro/complemento> - [<bairro> -] <município> - CEP: ...",
            # sem rótulos próprios de Bairro/Município. A lógica genérica acima
            # assume que o único "-" separa logradouro de BAIRRO, então jogava o
            # nome do MUNICÍPIO (ex.: "Feira de Santana") dentro do campo bairro
            # — e o IBGE resolver caía no fallback de Salvador (capital) mesmo
            # para tomadores em outra cidade. Aqui isolamos a linha de Endereço
            # e tratamos o(s) segmento(s) entre logradouro e "CEP:" como
            # [bairro,] município (o penúltimo segmento é bairro só quando há 3+).
            m_end_sv = re.search(r'Endere[çc]o\s*:?\s*\n?\s*(.+?)(?=CEP\s*:|\n\s*E-mail|$)', bloco, re.IGNORECASE | re.DOTALL)
            if m_end_sv:
                end_raw = re.sub(r'\s+', ' ', m_end_sv.group(1)).strip(' -,')
                segs = [s.strip() for s in end_raw.split(' - ') if s.strip()]
                if len(segs) >= 2:
                    end_data['logradouro'] = segs[0]
                    end_data['municipio'] = segs[-1]
                    if len(segs) >= 3:
                        end_data['bairro'] = segs[-2]

        if self.layout == LAYOUT_CUIABA and (not end_data.get('municipio') or end_data.get('municipio') in ('Não informado', '')):
            # ISSNet Cuiabá: o município do prestador vem como "- Cuiabá! MT" (o
            # "!"/"|" é ruído de OCR); o do tomador vem explícito em
            # "Cidade/UF: <cidade>/ <UF>". Sem extrair o município, o resolver caía
            # num IBGE errado (pescava os dígitos da Inscrição Municipal, ex.:
            # "295033" → 2950330, em vez de Cuiabá 5103403).
            m_cid = re.search(r'Cidade\s*/\s*UF\s*:?\s*([A-Za-zÀ-ú ]+?)\s*/\s*([A-Z]{2})', bloco, re.IGNORECASE)
            if m_cid:
                end_data['municipio'] = m_cid.group(1).strip()
                end_data['uf'] = m_cid.group(2).strip().upper()
            else:
                m_mun = re.search(r'[-–]\s*([A-Za-zÀ-ú]+(?:\s+[A-Za-zÀ-ú]+){0,2}?)\s*[!|/]?\s*\bMT\b', bloco)
                if m_mun:
                    end_data['municipio'] = m_mun.group(1).strip()
                    end_data['uf'] = 'MT'

        end_data['codigo_municipio'] = _ibge_resolver.extract_and_validate(
            bloco_clean, detected_uf=end_data['uf'],
            city_hint=end_data.get('municipio'), raw_doc_text=t
        )

        # Intermediário é uma entidade OPCIONAL (ao contrário de prestador/
        # tomador, que sempre aparecem, ainda que "Não Identificado"). Quando
        # nada de fato foi encontrado (CNPJ caiu no sentinela E a razão ficou
        # no default genérico) devolvemos None em vez de fabricar um
        # intermediário fantasma — visto em Cuiabá/ISSNet (pág. 14): a tabela
        # "Dados do Intermediário de Serviços" vem vazia (só o cabeçalho da
        # grade), mas o bloco genérico, sem o delimitador correto, engolia o
        # texto de "Descrição dos Serviços" seguinte e pescava o CNPJ do
        # PRESTADOR (linha do pix) como se fosse do intermediário.
        if is_intermediario and cnpj == '00000000000100' and razao == f'{tipo} Não Identificado':
            return None

        return Entidade(
            cnpj_cpf=cnpj,
            inscricao_municipal=insc,
            razao_social=razao,
            endereco=Endereco(**end_data),
            email=email,
            telefone=telefone
        )

    def _extrair_prestador_telecom(self, t: str) -> Entidade:
        """Extrai o emitente (prestador) de uma NF-e de serviço de comunicação.

        O CNPJ do emitente está codificado na chave de acesso de 44 dígitos nas
        posições 8-21 (0-indexed). O nome da empresa aparece nas primeiras linhas
        do texto antes do primeiro CNPJ formatado.
        """
        cnpj_prest = ""
        # Estratégia 1: extrai CNPJ das posições 8-21 da chave de acesso
        m_chave = re.search(r'\b(?:\d{4}\s+){10}\d{4}\b', t)
        if not m_chave:
            m_chave = re.search(r'CHAVE\s+DE\s+ACESSO\s*[:\s]*([\d\s]{44,60})', t, re.IGNORECASE)
        if m_chave:
            chave = re.sub(r'\D', '', m_chave.group(0) if not m_chave.lastindex else m_chave.group(1))
            if len(chave) == 44:
                cnpj_prest = chave[6:20]  # posições 6-19 = CNPJ emitente na chave NF-e mod22

        # Estratégia 2: primeiro CNPJ formatado no texto
        if not cnpj_prest:
            m_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', t)
            if m_cnpj:
                cnpj_prest = re.sub(r'\D', '', m_cnpj.group(1))

        # Nome: primeiras linhas não-vazias antes do primeiro CNPJ/telefone/CEP,
        # pulando o título fixo "DOCUMENTO AUXILIAR..." do cabeçalho deste layout
        # (senão o loop parava nele por engano, achando que era o nome do prestador).
        linhas = [l.strip() for l in t.split('\n') if l.strip()]
        nome_prest = linhas[0] if linhas else "Prestador de Telecomunicação"
        for l in linhas:
            if re.match(r'DOCUMENTO\s+AUXILIAR', l, re.IGNORECASE):
                continue
            if re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\(\d{2}\)\s*\d{4}', l):
                break
            if re.search(r'[A-Za-zÀ-ú]', l) and len(l) > 3:
                nome_prest = l
                break

        # Endereço: linha que contém CEP de 8 dígitos ou padrão "Rua/Av"
        logradouro, numero, bairro, municipio, uf, cep = ("Não informado", "S/N", "Não informado", "Não informado", "BA", "00000000")
        m_end = re.search(
            r'((?:Rua|Av(?:enida)?|Alameda|Rod(?:ovia)?|Estrada|Trav(?:essa)?)[^,\n]+),?\s*(\d+[^\n,]*?)[\n,]',
            t, re.IGNORECASE
        )
        if m_end:
            logradouro = m_end.group(1).strip()
            numero = m_end.group(2).strip() or "S/N"

        m_cep = re.search(r'(\d{5}[-\s]?\d{3})', t)
        if m_cep:
            cep = re.sub(r'\D', '', m_cep.group(1))

        m_mun = re.search(r'(\w[\w\s]+)\s*[-–]\s*([A-Z]{2})\b', t)
        if m_mun:
            municipio = m_mun.group(1).strip()
            uf = m_mun.group(2).strip()

        mun_cod = _ibge_resolver.extract_and_validate(municipio, uf)

        return Entidade(
            cnpj_cpf=cnpj_prest or "00000000000000",
            razao_social=nome_prest,
            endereco=Endereco(
                logradouro=logradouro,
                numero=numero,
                bairro=bairro,
                codigo_municipio=mun_cod,
                municipio=municipio,
                uf=uf,
                cep=cep,
            ),
        )

    def _extrair_tomador_telecom(self, t: str) -> Entidade:
        """Extrai o destinatário (tomador) de uma NF-e de serviço de comunicação.

        O tomador é identificado pelo rótulo 'CNPJ/CPF' que aparece no bloco
        do destinatário à esquerda do documento.

        O OCR deste layout costuma confundir a barra "/" do rótulo com a
        letra "I" (ex: "CNPJ/CPF:" vira "CNPJICPF:"), então o separador é
        tratado como opcional e tolerante a essa variação.
        """
        m_cnpj = re.search(r'CNPJ\s*[/Il|]?\s*CPF\s*[:\s]*([\d./-]+)', t, re.IGNORECASE)
        cnpj_tom = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else "00000000000000"

        # Nome: primeira linha "de nome" encontrada subindo a partir do bloco
        # com "CNPJ/CPF", pulando linhas de endereço (contêm dígitos, ex:
        # número/CEP) ou no padrão "Município - UF".
        nome_tom = "Tomador Não Identificado"
        if m_cnpj:
            bloco_antes = t[:m_cnpj.start()]
            linhas_antes = [l.strip() for l in bloco_antes.split('\n') if l.strip()]
            if linhas_antes:
                for l in reversed(linhas_antes):
                    if re.search(r'\d', l):
                        continue
                    if re.fullmatch(r'.+\s[-–]\s*[A-Z]{2}', l):
                        continue
                    if re.search(r'[A-Za-zÀ-ú]', l) and len(l) > 3:
                        nome_tom = l
                        break

        # Endereço: extrai CEP, município e UF do bloco ao redor do CNPJ/CPF
        pos_cnpj = m_cnpj.start() if m_cnpj else 0
        bloco_tom = t[max(0, pos_cnpj - 400): pos_cnpj + 400]

        logradouro, numero, bairro = "Não informado", "S/N", "Não informado"
        m_end = re.search(
            r'((?:Rua|Av(?:enida)?|Alameda|Rod(?:ovia)?|Estrada|Trav(?:essa)?)[^,\n]+),?\s*(\d+[^\n,]*?)[\n,]',
            bloco_tom, re.IGNORECASE
        )
        if m_end:
            logradouro = m_end.group(1).strip()
            numero = m_end.group(2).strip() or "S/N"

        cep = "00000000"
        m_cep = re.search(r'(\d{5}[-\s]?\d{3})', bloco_tom)
        if m_cep:
            cep = re.sub(r'\D', '', m_cep.group(1))

        municipio, uf = "Não informado", "BA"
        m_mun = re.search(r'(\w[\w\s]+)\s*[-–]\s*([A-Z]{2})\b', bloco_tom)
        if m_mun:
            municipio = m_mun.group(1).strip()
            uf = m_mun.group(2).strip()

        mun_cod = _ibge_resolver.extract_and_validate(municipio, uf)

        return Entidade(
            cnpj_cpf=cnpj_tom,
            razao_social=nome_tom,
            endereco=Endereco(
                logradouro=logradouro,
                numero=numero,
                bairro=bairro,
                codigo_municipio=mun_cod,
                municipio=municipio,
                uf=uf,
                cep=cep,
            ),
        )

    _LABEL_TOKEN_SAO_PAULO = re.compile(
        r'^(CPF\s*/\s*CNPJ|Nome\s*/\s*Raz[ãa]o(?:\s+Social)?|Endere[çc]o|'
        r'CNPJ|CPF|TOMADOR\s+DE\s+SERVI[ÇC]OS|PRESTADOR\s+DE\s+SERVI[ÇC]OS)\s*:?$',
        re.IGNORECASE
    )

    @classmethod
    def _primeiro_conteudo_sao_paulo(cls, bloco_texto: str, n: int = 1) -> List[str]:
        """Devolve as N primeiras linhas não-vazias de `bloco_texto` que NÃO são
        um rótulo solto (sem valor colado) — usado para pular os cabeçalhos/
        rótulos decorativos que o pdfminer intercala entre os campos reais."""
        linhas = [l.strip() for l in bloco_texto.split('\n') if l.strip()]
        conteudo = [l for l in linhas if not cls._LABEL_TOKEN_SAO_PAULO.match(l)]
        return conteudo[:n]

    def _extrair_entidade_sao_paulo(self, is_prestador: bool) -> Entidade:
        """Extrai prestador/tomador do layout São Paulo/SP quando o pdfminer
        desloca os cabeçalhos "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS"
        para o MEIO dos próprios dados da entidade (nota real AMIL/TEMIS,
        2026-07-31): o CNPJ do prestador chega a vazar sozinho antes de
        qualquer cabeçalho, e o rótulo "TOMADOR DE SERVIÇOS" só aparece DEPOIS
        de Nome/Razão + CPF/CNPJ + Endereço do tomador já terem passado. Um
        bloco delimitado por cabeçalho de seção erra o alvo nesse caso — em
        vez disso, ancoramos cada campo pelo PRÓPRIO rótulo mais próximo (ou,
        para o CNPJ, pela ordem de aparição no documento inteiro), pulando
        rótulos "soltos" (decorativos, sem valor colado) via
        `_primeiro_conteudo_sao_paulo`."""
        t = self.raw_text

        # CNPJ: 1ª ocorrência de checksum válido no documento = prestador, 2ª =
        # tomador. Mais robusto aqui que delimitar por cabeçalho, já que o CNPJ
        # do prestador pode vazar para ANTES de "PRESTADOR DE SERVIÇOS".
        all_cnpjs = self._scavenge_all_cnpjs()
        if is_prestador:
            cnpj = all_cnpjs[0] if len(all_cnpjs) >= 1 else "00000000000000"
        else:
            cnpj = all_cnpjs[1] if len(all_cnpjs) >= 2 else "00000000000000"

        nomes_razao = list(re.finditer(r'Nome\s*/\s*Raz[ãa]o(?:\s+Social)?\s*:?', t, re.IGNORECASE))
        m_prest_header = re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)

        razao, logradouro_raw, insc, bloco_campos = "", "", None, t

        if is_prestador:
            # A razão social/endereço REAIS do prestador vêm logo após
            # "Inscrição municipal:" + seu valor — o rótulo "Nome/Razão" que
            # existiria normalmente aqui vazou/virou um trio decorativo sem
            # valor ("CPF/CNPJ / Nome/Razão / Endereço" em sequência, sem
            # conteúdo colado). Delimita até o 1º "Nome/Razão" (início dos
            # dados do tomador) para nunca vazar pro bloco do tomador.
            # A busca já consome o PRÓPRIO valor da inscrição municipal (não só
            # o rótulo) — senão o dígito vira a "1ª linha de conteúdo" e desloca
            # razão/endereço uma posição (razão vira o nº da IM, endereço vira
            # a razão real).
            m_im = re.search(r'Inscri[çc][ãa]o\s+municipal\s*:?\s*\n*\s*(\d+)', t, re.IGNORECASE)
            insc = m_im.group(1) if m_im else None
            inicio = m_im.end() if m_im else (m_prest_header.end() if m_prest_header else 0)
            fim = nomes_razao[0].start() if nomes_razao else len(t)
            bloco_nome_end = t[inicio:fim]
            conteudo = self._primeiro_conteudo_sao_paulo(bloco_nome_end, n=2)
            razao = conteudo[0] if len(conteudo) >= 1 else ""
            logradouro_raw = conteudo[1] if len(conteudo) >= 2 else ""

            # Bairro/Município/UF/CEP do prestador ficam ENTRE a 1ª ocorrência
            # de "Nome/Razão" (o trio decorativo, sem valor) e a 2ª (a real,
            # já do tomador) — cortar em nomes_razao[0] os deixaria de fora.
            fim_campos = nomes_razao[1].start() if len(nomes_razao) >= 2 \
                else (nomes_razao[0].start() if nomes_razao else len(t))
            bloco_campos = t[m_prest_header.end(): fim_campos] if m_prest_header else t
        else:
            # A razão social real do tomador é a 2ª ocorrência do rótulo
            # "Nome/Razão" (a 1ª, junto ao prestador, é o trio decorativo sem
            # valor). O cabeçalho "TOMADOR DE SERVIÇOS" some DEPOIS desses
            # campos, então não serve como início de bloco.
            if len(nomes_razao) >= 2:
                bloco_tomador = t[nomes_razao[1].end():]
                conteudo = self._primeiro_conteudo_sao_paulo(bloco_tomador, n=1)
                razao = conteudo[0] if conteudo else ""

                m_end_lbl = re.search(r'Endere[çc]o\s*:?', bloco_tomador, re.IGNORECASE)
                if m_end_lbl:
                    conteudo_end = self._primeiro_conteudo_sao_paulo(bloco_tomador[m_end_lbl.end():], n=1)
                    logradouro_raw = conteudo_end[0] if conteudo_end else ""

                bloco_campos = bloco_tomador

        if not razao:
            razao = f"{'Prestador' if is_prestador else 'Tomador'} Não Identificado"

        # Bairro/Município/UF/CEP: já vêm corretamente ordenados dentro do
        # `bloco_campos` de cada entidade (o deslocamento afeta só a posição
        # do CABEÇALHO de seção, não a ordem relativa desses 4 campos entre
        # si) — mesma técnica de "rótulo -> 1ª linha de conteúdo real".
        bairro = "Não informado"
        m_bairro = re.search(r'Bairro\s*:?\s*', bloco_campos, re.IGNORECASE)
        if m_bairro:
            cont = self._primeiro_conteudo_sao_paulo(bloco_campos[m_bairro.end():], n=1)
            if cont: bairro = cont[0]

        municipio = "SAO PAULO"
        m_mun = re.search(r'Munic[íi]pio\s*:?\s*', bloco_campos, re.IGNORECASE)
        if m_mun:
            cont = self._primeiro_conteudo_sao_paulo(bloco_campos[m_mun.end():], n=1)
            if cont: municipio = cont[0]

        uf = "SP"
        m_uf = re.search(r'\bUF\s*:?\s*', bloco_campos, re.IGNORECASE)
        if m_uf:
            cont = self._primeiro_conteudo_sao_paulo(bloco_campos[m_uf.end():], n=1)
            if cont and len(cont[0]) <= 3:
                uf = cont[0][:2].upper()

        cep = ""
        m_cep = re.search(r'\bCEP\s*:?\s*', bloco_campos, re.IGNORECASE)
        if m_cep:
            cont = self._primeiro_conteudo_sao_paulo(bloco_campos[m_cep.end():], n=1)
            if cont: cep = re.sub(r'\D', '', cont[0])

        email = None
        m_email = re.search(r'E-?mail\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', bloco_campos, re.IGNORECASE)
        if m_email:
            email = m_email.group(1).strip()

        mun_cod = _ibge_resolver.extract_and_validate(municipio, uf)

        return Entidade(
            cnpj_cpf=cnpj,
            inscricao_municipal=insc,
            razao_social=razao,
            endereco=Endereco(
                logradouro=logradouro_raw or "Não informado",
                numero="S/N",
                bairro=bairro,
                codigo_municipio=mun_cod,
                municipio=municipio,
                uf=uf,
                cep=cep or "00000000",
            ),
            email=email,
        )

    def _extrair_entidade_lauro_freitas(self, is_prestador: bool) -> Entidade:
        """Extrai prestador/tomador do layout Lauro de Freitas/BA.

        Duas variantes de documento usam a mesma marca de layout:

        1) NFS-e regular (ex. nota Macedo/Sul&Seg): cabeçalho "PRESTADOR DE
           SERVIÇOS" vem ANTES de "TOMADOR DE SERVIÇOS". O pdfminer extrai
           os campos Município/UF/Email do PRESTADOR fora de ordem: eles
           saem DEPOIS do cabeçalho do tomador, mas ANTES do "Nome/Razão" do
           tomador (a linha correspondente do prestador "vaza" para a caixa
           seguinte).
        2) NFTS (Nota Fiscal Eletrônica do TOMADOR de Serviços, ex. nota
           2026302 BDP LOGISTICA→BONI TRANSPORTES): cabeçalho "TOMADOR DE
           SERVIÇOS" vem ANTES de "PRESTADOR DE SERVIÇOS", e cada bloco sai
           completo/autocontido, sem vazamento nenhum. Assumir a ordem fixa
           da variante 1 aqui faz `bloco_prestador` virar um slice com
           início depois do fim (string vazia) — todo o prestador some.

        O texto se divide em até 3 blocos, delimitados pelos cabeçalhos de
        seção (na ordem em que realmente aparecem) e pelo 1º "Nome/Razão"
        que sobra depois do cabeçalho do tomador:
          - bloco_prestador: CNPJ/Inscrição/Nome/Endereço/Bairro/CEP do
            PRESTADOR, e (só na variante 2) também Município/UF/Email.
          - bloco_vazado: CNPJ do TOMADOR + (só na variante 1) Município/UF/
            Email VAZADOS do PRESTADOR.
          - bloco_tomador: Nome/Endereço/Bairro/Município/UF/CEP/Email do
            TOMADOR (corretos, na ordem esperada, nas duas variantes).
        """
        t = self.raw_text

        m_prest_header = re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
        m_tom_header = re.search(r'TOMADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)

        if m_prest_header and (not m_tom_header or m_tom_header.start() > m_prest_header.start()):
            # Variante 1 (NFS-e regular): PRESTADOR antes de TOMADOR.
            bloco_prestador = t[m_prest_header.end():m_tom_header.start()] if m_tom_header else t[m_prest_header.end():]
        elif m_prest_header:
            # Variante 2 (NFTS): TOMADOR antes de PRESTADOR — bloco do
            # prestador vai do seu próprio cabeçalho até a próxima seção
            # conhecida (discriminação dos serviços) ou o fim do texto.
            resto_prest = t[m_prest_header.end():]
            m_fim_prest = re.search(r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS', resto_prest, re.IGNORECASE)
            bloco_prestador = resto_prest[:m_fim_prest.start()] if m_fim_prest else resto_prest
        else:
            bloco_prestador = t

        resto = t[m_tom_header.end():] if m_tom_header else t

        m_nome_tomador = re.search(r'Nome\s*/\s*Raz[ãa]o', resto, re.IGNORECASE)
        bloco_vazado = resto[:m_nome_tomador.start()] if m_nome_tomador else ''
        bloco_tomador = resto[m_nome_tomador.start():] if m_nome_tomador else resto

        def _campo(pattern: str, bloco: str) -> Optional[str]:
            m = re.search(pattern, bloco, re.IGNORECASE)
            return m.group(1).strip() if m else None

        def _cnpj_cpf(bloco: str) -> str:
            m = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})', bloco)
            return re.sub(r'\D', '', m.group(1)) if m else '00000000000000'

        if is_prestador:
            cnpj = _cnpj_cpf(bloco_prestador)
            insc = _campo(r'Inscri[çc][aã]o\s*\n+\s*(\d+)', bloco_prestador)
            razao = _campo(r'Nome\s*/\s*Raz[ãa]o\s*\n+\s*(.+)', bloco_prestador) or 'Prestador Não Identificado'
            endereco_raw = _campo(r'Endere[çc]o\s*:?\s*\n+\s*(.+)', bloco_prestador) or 'Não informado'
            bairro = _campo(r'Bairro\s*:?\s*\n*\s*([^\n]+)', bloco_prestador) or 'Não informado'
            cep_raw = _campo(r'CEP\s*:?\s*\n*\s*([\d-]+)', bloco_prestador)
            municipio = (_campo(r'Munic[íi]pio\s*:\s*([^\n]+)', bloco_prestador)
                         or _campo(r'Munic[íi]pio\s*:\s*([^\n]+)', bloco_vazado)
                         or 'LAURO DE FREITAS')
            uf = (_campo(r'\bUF\s*:\s*([A-Z]{2})', bloco_prestador)
                  or _campo(r'\bUF\s*:\s*([A-Z]{2})', bloco_vazado)
                  or 'BA')
            email_pat = r'Email\s*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            email = _campo(email_pat, bloco_prestador) or _campo(email_pat, bloco_vazado)
        else:
            cnpj = _cnpj_cpf(bloco_vazado)
            insc = None
            razao = _campo(r'Nome\s*/\s*Raz[ãa]o\s*\n+\s*(.+)', bloco_tomador) or 'Tomador Não Identificado'
            endereco_raw = _campo(r'Endere[çc]o\s*:?\s*\n+\s*(.+)', bloco_tomador) or 'Não informado'
            bairro = _campo(r'Bairro\s*:?\s*\n*\s*([^\n]+)', bloco_tomador) or 'Não informado'
            cep_raw = _campo(r'CEP\s*:?\s*\n*\s*([\d-]+)', bloco_tomador)
            municipio = _campo(r'Munic[íi]pio\s*:\s*([^\n]+)', bloco_tomador) or 'Não informado'
            uf = _campo(r'\bUF\s*:\s*([A-Z]{2})', bloco_tomador) or 'BA'
            email = _campo(r'Email\s*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', bloco_tomador)

        cep = re.sub(r'\D', '', cep_raw) if cep_raw else '00000000'

        # Endereço vem em texto livre com vírgulas ("Rua X, 1184, CENTRO"). O
        # 3º segmento (quando existe) é complemento/referência solto — o
        # bairro oficial vem do rótulo "Bairro:" à parte, não deste segmento.
        partes_end = [p.strip() for p in endereco_raw.split(',')]
        logradouro = partes_end[0] if partes_end else 'Não informado'
        numero = partes_end[1] if len(partes_end) >= 2 and partes_end[1] else 'S/N'
        complemento = None
        if len(partes_end) >= 3:
            complemento = ', '.join(partes_end[2:]).strip() or None

        mun_cod = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio, raw_doc_text=t)

        return Entidade(
            cnpj_cpf=cnpj,
            inscricao_municipal=insc,
            razao_social=razao,
            endereco=Endereco(
                logradouro=logradouro,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                codigo_municipio=mun_cod,
                municipio=municipio,
                uf=uf,
                cep=cep,
            ),
            email=email,
        )

    def _extrair_entidade_password_enotas(self, is_prestador: bool) -> Entidade:
        """Extrai prestador/tomador do layout PASSWORD/eNotas (Lauro de Freitas/BA).

        O texto do pdfminer vem limpo e em ordem. O PRESTADOR fica no topo, em
        formato livre (razão social, endereço, "BAIRRO - Município - UF - CEP",
        telefone, e-mail, CNPJ, IM). O TOMADOR fica na seção "DADOS DO TOMADOR",
        em grade rótulo-em-cima/valor-embaixo (Nome, Endereço, E-mail, Telefone,
        Bairro, CEP, Município, UF, País, CPF/CNPJ).
        """
        t = self.raw_text

        m_tom = re.search(r'DADOS\s+DO\s+TOMADOR', t, re.IGNORECASE)
        m_discrim = re.search(r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS', t, re.IGNORECASE)
        bloco_prest = t[:m_tom.start()] if m_tom else t
        fim_tom = m_discrim.start() if m_discrim else len(t)
        bloco_tom = t[m_tom.end():fim_tom] if m_tom else t

        def _split_endereco(raw: str):
            """'EVERALDINA B DA PAZ, 400' -> (logradouro, numero, complemento)."""
            partes = [p.strip() for p in raw.split(',')]
            logradouro = partes[0] if partes and partes[0] else 'Não informado'
            numero = 'S/N'
            complemento = None
            if len(partes) >= 2:
                m_num = re.match(r'(\d+)\s*(.*)', partes[1])
                if m_num:
                    numero = m_num.group(1)
                    resto = m_num.group(2).strip()
                    extras = ([resto] if resto else []) + partes[2:]
                    complemento = ', '.join([e for e in extras if e]).strip() or None
                else:
                    complemento = ', '.join(partes[1:]).strip() or None
            return logradouro, numero, complemento

        if is_prestador:
            b = bloco_prest
            m_cnpj = re.search(r'CNPJ\s*:?\s*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', b, re.IGNORECASE)
            cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'
            m_im = re.search(r'INSCRI[ÇC][ÃA]O\s+MUNICIPAL\s*:?\s*(\d+)', b, re.IGNORECASE)
            insc = m_im.group(1) if m_im else None
            m_email = re.search(r'EMAIL\s*:?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', b, re.IGNORECASE)
            email = m_email.group(1) if m_email else None
            m_tel = re.search(r'TELEFONE\s*:?\s*(\d+)', b, re.IGNORECASE)
            telefone = m_tel.group(1) if m_tel else None

            # Razão social: primeira linha de conteúdo após o cabeçalho "emitido em".
            m_raz = re.search(r'emitido\s+em\s*:?\s*\d{2}/\d{2}/\d{4}\s*\n+\s*(.+)', b, re.IGNORECASE)
            razao = m_raz.group(1).strip() if m_raz else 'Prestador Não Identificado'

            # Endereço: linha logo após a razão social.
            endereco_raw = 'Não informado'
            if m_raz:
                resto = b[m_raz.end():]
                m_end = re.search(r'\s*([^\n]+)', resto)
                if m_end:
                    endereco_raw = m_end.group(1).strip()

            # "ITINGA - Lauro de Freitas - BA - 42738495"
            bairro, municipio, uf, cep = 'Não informado', 'Lauro de Freitas', 'BA', '00000000'
            m_loc = re.search(r'\n\s*([^\n]+?)\s*-\s*([^\n]+?)\s*-\s*([A-Z]{2})\s*-\s*(\d{8})', b)
            if m_loc:
                bairro = m_loc.group(1).strip()
                municipio = m_loc.group(2).strip()
                uf = m_loc.group(3).strip()
                cep = re.sub(r'\D', '', m_loc.group(4))

            logradouro, numero, complemento = _split_endereco(endereco_raw)
            mun_cod = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio, raw_doc_text=t)

            return Entidade(
                cnpj_cpf=cnpj,
                inscricao_municipal=insc,
                razao_social=razao,
                endereco=Endereco(
                    logradouro=logradouro,
                    numero=numero,
                    complemento=complemento,
                    bairro=bairro,
                    codigo_municipio=mun_cod,
                    municipio=municipio,
                    uf=uf,
                    cep=cep,
                ),
                email=email,
                telefone=telefone,
            )

        # Tomador — grade rótulo/valor.
        b = bloco_tom

        def _campo(rotulo: str) -> Optional[str]:
            m = re.search(rotulo + r'\s*\n+\s*([^\n]+)', b, re.IGNORECASE)
            return m.group(1).strip() if m else None

        razao = _campo(r'NOME\s*/\s*RAZ[ÃA]O\s+SOCIAL') or 'Tomador Não Identificado'
        endereco_raw = _campo(r'ENDERE[ÇC]O') or 'Não informado'
        m_email = re.search(r'E-?MAIL\s*\n+\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', b, re.IGNORECASE)
        email = m_email.group(1) if m_email else None
        bairro = _campo(r'BAIRRO\s*/\s*DISTRITO') or _campo(r'BAIRRO') or 'Não informado'
        municipio = _campo(r'MUNIC[ÍI]PIO') or 'Não informado'
        m_uf = re.search(r'\bUF\s*\n+\s*([A-Z]{2})\b', b, re.IGNORECASE)
        uf = m_uf.group(1).strip() if m_uf else 'BA'
        m_cep = re.search(r'\bCEP\s*\n+\s*(\d{5}-?\d{3}|\d{8})', b, re.IGNORECASE)
        cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else '00000000'
        m_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})', b)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        logradouro, numero, complemento = _split_endereco(endereco_raw)
        mun_cod = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio, raw_doc_text=t)

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao,
            endereco=Endereco(
                logradouro=logradouro,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                codigo_municipio=mun_cod,
                municipio=municipio,
                uf=uf,
                cep=cep,
            ),
            email=email,
        )

    def _extrair_entidade_fatura_locacao_generica(self, is_prestador: bool) -> Entidade:
        """Extrai locadora/locatário do layout de Fatura de Locação genérico
        (qualquer locadora ainda não catalogada com detecção própria — ver
        LAYOUT_FATURA_LOCACAO_GENERICA).

        Estrutura de texto (pdfminer, PDF digital, sem OCR): dois blocos com o
        mesmo vocabulário de rótulos ("Razão Social"/"Nome/Razão Social",
        "Endereço", "Cidade", "Telefone", "E-mail", "CNPJ", "Estado"),
        delimitados pelos cabeçalhos "LOCADORA"/"LOCATÁRIO" e pelo início da
        tabela de itens ("QTDE - DESCRIÇÃO"). Quando um campo (Telefone,
        Estado) não tem valor logo após o rótulo na mesma linha, o pdfminer
        empurra o valor para depois do próximo rótulo vazio (ex.: "Estado:\\n
        \\nE-mail:\\n\\nBA" — o "BA" é o valor de Estado, deslocado) — mesmo
        padrão de vazamento de campo já visto no layout Lauro de Freitas
        (Forma E do gotcha de colisão de layout).
        """
        t = self.raw_text

        m_locadora = re.search(r'\bLOCADORA\b', t, re.IGNORECASE)
        m_locatario = re.search(r'\bLOCAT[ÁA]RIO\b', t, re.IGNORECASE)
        m_tabela = re.search(r'QTDE\s*-\s*DESCRI[ÇC][ÃA]O', t, re.IGNORECASE)

        fim_locadora = m_locatario.start() if m_locatario else len(t)
        bloco_locadora = t[m_locadora.end():fim_locadora] if m_locadora else ''
        inicio_locatario = m_locatario.end() if m_locatario else 0
        fim_locatario = m_tabela.start() if m_tabela else len(t)
        bloco_locatario = t[inicio_locatario:fim_locatario] if m_locatario else t

        bloco = bloco_locadora if is_prestador else bloco_locatario
        placeholder = 'Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'

        def _campo(rotulo: str) -> str:
            m = re.search(rotulo + r'\s*:\s*([^\n]+)', bloco, re.IGNORECASE)
            return m.group(1).strip() if m else ''

        razao = _campo(r'Nome\s*/\s*Raz[ãa]o\s+Social') or _campo(r'Raz[ãa]o\s+Social') or placeholder

        endereco_raw = _campo(r'Endere[çc]o')
        cep = ''
        m_cep = re.search(r'CEP\s*:\s*([\d-]+)', endereco_raw, re.IGNORECASE)
        if m_cep:
            cep = re.sub(r'\D', '', m_cep.group(1))
            endereco_raw = endereco_raw[:m_cep.start()].strip()

        logradouro, numero, bairro, complemento = endereco_raw or 'Não informado', 'S/N', 'Não informado', None
        m_num = re.search(r'N[ºo°]\s*(\d+)\s*(.*)$', endereco_raw, re.IGNORECASE)
        if m_num:
            logradouro = endereco_raw[:m_num.start()].strip() or 'Não informado'
            numero = m_num.group(1)
            resto_words = m_num.group(2).strip().split()
            # Primeiro segmento após o número costuma ser um qualificador de
            # unidade (galpão/sala/loja/...), não o bairro propriamente dito —
            # confirmado com a mesma tomadora (FOLHAS URBANAS) no layout
            # PASSWORD/eNotas, onde "GALPAO" é complemento e "PITANGUEIRAS" é
            # o bairro real.
            complemento_keywords = {
                'GALPAO', 'GALPÃO', 'SALA', 'LOJA', 'APTO', 'APARTAMENTO',
                'BLOCO', 'CASA', 'ANDAR', 'TERREO', 'TÉRREO', 'FUNDOS', 'COBERTURA',
            }
            if resto_words and resto_words[0].upper() in complemento_keywords and len(resto_words) > 1:
                complemento = resto_words[0]
                bairro = ' '.join(resto_words[1:])
            elif resto_words:
                bairro = ' '.join(resto_words)

        cidade = _campo(r'Cidade') or 'Não informado'

        uf = ''
        m_uf_inline = re.search(r'Estado\s*:\s*([A-Z]{2})\b', bloco, re.IGNORECASE)
        if m_uf_inline:
            uf = m_uf_inline.group(1).upper()
        else:
            m_uf_orfao = re.search(r'\n\s*([A-Z]{2})\s*\n', bloco)
            uf = m_uf_orfao.group(1) if m_uf_orfao else 'BA'

        m_cnpj = re.search(r'CNPJ\s*:\s*([\d./-]+)', bloco, re.IGNORECASE)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        m_tel = re.search(r'Telefone\s*:?\s*\n*\s*(\(\d{2}\)\s*\d{4,5}-\d{4})', bloco, re.IGNORECASE)
        telefone = m_tel.group(1) if m_tel else None

        mun_cod = _ibge_resolver.extract_and_validate(cidade, uf, city_hint=cidade, raw_doc_text=t)

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao,
            endereco=Endereco(
                logradouro=logradouro,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                codigo_municipio=mun_cod,
                municipio=cidade,
                uf=uf,
                cep=cep or '00000000',
            ),
            telefone=telefone,
        )

    def _extrair_entidade_armac(self, is_prestador: bool) -> Entidade:
        """Extrai locador/tomador da Fatura de Locação da ARMAC (OCR zoom4/PSM6).

        Estrutura: blocos "Dados do Locador" e "Dados do Tomador", cada um com
        "Razão Social:", "CNPJ[/CPF]:" e duas linhas "Endereço:" — a 1ª é
        logradouro+número[+complemento], a 2ª é "CEP Cidade - UF". O OCR insere
        ruído de borda de célula ("|", "*", "e", "Es:") logo após os rótulos,
        que limpamos; o CNPJ do locador vem com máscara e o do tomador cru
        (14 dígitos). A nota ARMAC não traz bairro em campo próprio.
        """
        t = self.raw_text

        m_loc = re.search(r'Dados\s+do\s+Locador', t, re.IGNORECASE)
        m_tom = re.search(r'Dados\s+do\s+Tomador', t, re.IGNORECASE)
        fim_loc = m_tom.start() if m_tom else len(t)
        bloco_loc = t[m_loc.end():fim_loc] if m_loc else t
        resto = t[m_tom.end():] if m_tom else t
        # Fim do bloco do tomador: início da tabela de itens ou das observações.
        m_fim = re.search(
            r'\n[A-Za-z][A-Za-z0-9]{4,}\s+.+\d{2}[.\s]\d{2}[.\s/]*\d{4}|Observa[çc][õo]es|Consultor|Total\s+antes',
            resto, re.IGNORECASE)
        bloco_tom = resto[:m_fim.start()] if m_fim else resto

        bloco = bloco_loc if is_prestador else bloco_tom
        placeholder = 'Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'

        def _limpa(v: str) -> str:
            return re.sub(r'^[^0-9A-Za-zÀ-Úà-ú]+', '', v).strip()

        m_raz = re.search(r'Raz[ãa]o\s+Social\s*:?\s*(.+)', bloco, re.IGNORECASE)
        razao = _limpa(m_raz.group(1)) if m_raz else ''
        razao = razao or placeholder

        m_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', bloco) or re.search(r'\b(\d{14})\b', bloco)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        enderecos = [_limpa(e) for e in re.findall(r'Endere[çc]o\s*:?\s*(.+)', bloco, re.IGNORECASE)]
        street_raw, cep, cidade, uf = '', '', 'Não informado', 'BA'
        for e in enderecos:
            m_cml = re.search(r'(\d{5}-?\d{3})\s+(.+?)\s*-\s*([A-Z]{2})\b', e)
            if m_cml:
                cep = re.sub(r'\D', '', m_cml.group(1))
                cidade = m_cml.group(2).strip()
                uf = m_cml.group(3).upper()
            else:
                street_raw = e

        # Corta ruído de OCR antes do início real do logradouro (ex.: "Es: - RUA
        # ...") ancorando num tipo de logradouro conhecido.
        m_st = re.search(
            r'\b(RUA|R\.|AV|AVENIDA|ESTRADA|EST\.|TRAVESSA|TRV|ALAMEDA|AL\.|PRA[CÇ]A|ROD|RODOVIA)\b.*',
            street_raw, re.IGNORECASE)
        if m_st:
            street_raw = m_st.group(0).strip()

        logradouro, numero, complemento = street_raw or 'Não informado', 'S/N', None
        partes = [p.strip() for p in street_raw.split(',')]
        if partes and partes[0]:
            m_num = re.search(r'(.+?)\s+(\d+)\s*$', partes[0])
            if m_num:
                logradouro = m_num.group(1).strip()
                numero = m_num.group(2)
            else:
                logradouro = partes[0]
            if len(partes) > 1:
                complemento = ', '.join(partes[1:]).strip() or None

        mun_cod = _ibge_resolver.extract_and_validate(cidade, uf, city_hint=cidade, raw_doc_text=t)

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao,
            endereco=Endereco(
                logradouro=logradouro or 'Não informado',
                numero=numero,
                complemento=complemento,
                bairro='Não informado',
                codigo_municipio=mun_cod,
                municipio=cidade,
                uf=uf,
                cep=cep or '00000000',
            ),
        )

    @staticmethod
    def _cnpj_valido(digitos: str) -> bool:
        """Valida os dois dígitos verificadores de um CNPJ (14 dígitos)."""
        c = re.sub(r'\D', '', digitos or '')
        if len(c) != 14 or c == c[0] * 14:
            return False

        def _dv(nums: str) -> str:
            pesos = list(range(2, 10)) * 2
            soma = sum(int(n) * p for n, p in zip(reversed(nums), pesos))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)

        return c[12] == _dv(c[:12]) and c[13] == _dv(c[:13])

    @classmethod
    def _corrige_cnpj_primeiro_digito(cls, digitos: str) -> str:
        """Corrige o artefato de OCR mais comum em fotos de baixa qualidade: o
        PRIMEIRO dígito do CNPJ lido errado (ex.: "1" -> "4", gerando
        "49477725000101" no lugar de "19477725000101"). Só age quando o CNPJ
        original é inválido; testa apenas as 10 variações do 1º dígito e só
        aceita a correção quando EXATAMENTE uma delas passa na validação (foi
        verificado que, para o caso real, a correção é única — corrigir qualquer
        dígito daria múltiplos candidatos e seria ambíguo). Conservador: se nada
        (ou mais de um) validar, devolve os dígitos originais."""
        c = re.sub(r'\D', '', digitos or '')
        if len(c) != 14 or cls._cnpj_valido(c):
            return c
        candidatos = [d + c[1:] for d in '0123456789' if cls._cnpj_valido(d + c[1:])]
        return candidatos[0] if len(candidatos) == 1 else c

    def _extrair_entidade_camacari2(self, is_prestador: bool) -> Optional[Entidade]:
        """Extrai prestador/tomador da NFS-e de Camaçari/BA ESCANEADA (foto/JPG
        -> OCR). Estrutura: blocos "PRESTADOR DE SERVIÇOS" e "TOMADOR DE
        SERVIÇOS" com rótulos "Nome/Razão Social:", "CPF/CNPJ:", "Inscrição
        Municipal:", "Logradouro:/Nº:", "Compl.:/Bairro:", "CEP:/MUNICÍPIO:/UF:".

        Cuidados específicos deste scan (validados contra a nota real nº 1050):
        - O CNPJ do TOMADOR sai com o 1º dígito trocado ("49..."→ deveria "19...")
          — corrigido por _corrige_cnpj_primeiro_digito (validação do DV).
        - O MUNICÍPIO do PRESTADOR some no OCR ("CEP: MUNICÍPIO: ."); como toda
          NFS-e municipal de Camaçari é emitida por prestador inscrito no próprio
          município, assumimos Camaçari/BA quando o campo vem vazio.
        - Nomes de bairro/complemento podem sair corrompidos (não são críticos
          para o XML nem para a resolução de IBGE).
        Devolve None se não conseguir isolar o bloco da entidade (o dispatch
        então cai no extrator genérico — superset)."""
        t = self.raw_text
        m_prest = re.search(r'PRESTADOR\s*DE\s*SERVI[ÇC]OS', t, re.IGNORECASE)
        m_tom = re.search(r'TOMADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
        m_disc = re.search(r'DISCRIMINA[ÇC][ÃA]O', t, re.IGNORECASE)

        if is_prestador:
            if not (m_prest and m_tom):
                return None
            bloco = t[m_prest.end():m_tom.start()]
            municipio_default, uf_default = 'CAMACARI', 'BA'
        else:
            if not m_tom:
                return None
            fim = m_disc.start() if (m_disc and m_disc.start() > m_tom.end()) else len(t)
            bloco = t[m_tom.end():fim]
            municipio_default, uf_default = '', 'BA'

        def _campo(pat: str) -> str:
            m = re.search(pat, bloco, re.IGNORECASE)
            return m.group(1).strip(' .:|') if m else ''

        razao = _campo(r'Nome/Raz[ãa]o\s+Social\s*:?\s*(.+)')
        razao = re.sub(r'\s{2,}.*$', '', razao).strip()  # corta ruído após 2+ espaços

        m_cnpj = re.search(r'CPF/CNPJ\s*:?\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})', bloco, re.IGNORECASE)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else ''
        if not is_prestador and cnpj:
            cnpj = self._corrige_cnpj_primeiro_digito(cnpj)
        if not cnpj:
            cnpj = '00000000000000'

        inscricao = _campo(r'Inscri[çc][ãa]o\s+Municipal\s*:?\s*(\d+)')

        logradouro = _campo(r'Logradouro\s*:?\s*(.+?)\s*(?:N[ºo°]\s*:|$)')
        numero = _campo(r'N[ºo°]\s*:?\s*([A-Za-z0-9]+)')
        complemento = _campo(r'Compl\.?\s*:?\s*(.+?)\s*(?:B[ai]{1,2}r{1,2}o|Beira|$)')

        cep = ''
        m_cep = re.search(r'CEP\s*:?\s*(\d{2}\.?\d{3}-?\d{3})', bloco, re.IGNORECASE)
        if m_cep:
            cep = re.sub(r'\D', '', m_cep.group(1))

        m_mun = re.search(r'MUNIC[IÍ]PIO\s*:?\s*([A-Za-zÀ-ú][A-Za-zÀ-ú\s]+?)\s*(?:EaMiisia|UF|$)', bloco, re.IGNORECASE)
        municipio = m_mun.group(1).strip() if m_mun else ''
        # Descarta capturas degeneradas (só pontuação/1 letra) e usa o default.
        if len(re.sub(r'[^A-Za-zÀ-ú]', '', municipio)) < 3:
            municipio = municipio_default

        m_uf = re.search(r'UF\s*:?\s*(BAHIA|[A-Z]{2})\b', bloco, re.IGNORECASE)
        uf = m_uf.group(1).upper() if m_uf else uf_default
        if uf == 'BAHIA':
            uf = 'BA'

        cod_mun = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio) if municipio else ''

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao or ('Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'),
            inscricao_municipal=inscricao,
            endereco=Endereco(
                logradouro=logradouro or 'Não informado',
                numero=numero or 'S/N',
                complemento=complemento,
                bairro='Não informado',
                codigo_municipio=cod_mun,
                municipio=municipio or municipio_default,
                uf=uf,
                cep=cep or '00000000',
            ),
        )

    def _extrair_entidade_mata_sao_joao(self, is_prestador: bool) -> Entidade:
        """Extrai prestador/tomador da NFS-e de Mata de São João/BA (plataforma
        SAATRI). Estrutura (OCR limpo, sem rótulos por linha): blocos
        "Prestador do(s) Serviço(s)" e "Tomador do(s) Serviço(s)" com as linhas
        na ordem: Razão Social / Nome Fantasia / Logradouro (+ nº/compl.) /
        "Bairro - MUNICÍPIO/UF CEP: NNNNN-NNN" / "CNPJ Insc. Municipal: NNN".

        Os rótulos "Nome/Razão Social:", "CPF/CNPJ:" etc. aparecem dumpados em
        bloco separado no fim da nota (coluna de labels do PDF) e são ignorados.
        O município é resolvido pelo IBGEResolver a partir do "MUNICÍPIO/UF" da
        linha de endereço (Mata de São João -> 2921005; sem essa entrada o
        resolver cairia no default Salvador/2927408)."""
        t = self.raw_text
        m_prest = re.search(r'Prestador\s+do\(s\)\s+Servi[çc]o\(s\)', t, re.IGNORECASE)
        m_tom = re.search(r'Tomador\s+do\(s\)\s+Servi[çc]o\(s\)', t, re.IGNORECASE)
        m_exig = re.search(r'Exigibilidade\s+do\s+ISS', t, re.IGNORECASE)

        if is_prestador:
            if not (m_prest and m_tom):
                bloco = ''
            else:
                bloco = t[m_prest.end():m_tom.start()]
        else:
            if not m_tom:
                bloco = ''
            else:
                fim = m_exig.start() if (m_exig and m_exig.start() > m_tom.end()) else len(t)
                bloco = t[m_tom.end():fim]

        linhas = [ln.strip() for ln in bloco.split('\n') if ln.strip()]

        razao = linhas[0] if linhas else ''

        m_cnpj = re.search(r'(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})', bloco)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        m_im = re.search(r'Insc\.?\s*Municipal:?\s*(\d+)', bloco, re.IGNORECASE)
        inscricao = m_im.group(1) if m_im else ''

        # A linha de localização é "Bairro - MUNICÍPIO/UF CEP: NNNNN-NNN".
        # Isolamos essa linha (não a regex sobre o bloco inteiro, senão o "\s"
        # cruzaria quebras e o bairro capturaria a linha anterior).
        mun_idx = -1
        bairro, municipio, uf = 'Não informado', '', 'BA'
        for i, ln in enumerate(linhas):
            m_loc = re.search(r'^(.*?)\s*-\s*([A-Za-zÀ-ú][A-Za-zÀ-ú\s]+?)/([A-Z]{2})\s+CEP', ln)
            if m_loc:
                mun_idx = i
                bairro = m_loc.group(1).strip() or 'Não informado'
                municipio = m_loc.group(2).strip()
                uf = m_loc.group(3).upper()
                break

        m_cep = re.search(r'CEP:?\s*(\d{5}-?\d{3})', bloco, re.IGNORECASE)
        cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else '00000000'

        # Logradouro: a linha imediatamente anterior à linha de município/CEP
        # (ordem SAATRI: razão / [fantasia] / logradouro / bairro-município-CEP).
        logradouro = ''
        if mun_idx > 0 and linhas[mun_idx - 1] != razao:
            logradouro = linhas[mun_idx - 1]

        cod_mun = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio) if municipio else ''

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao or ('Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'),
            inscricao_municipal=inscricao,
            endereco=Endereco(
                logradouro=logradouro or 'Não informado',
                numero='S/N',
                bairro=bairro or 'Não informado',
                codigo_municipio=cod_mun,
                municipio=municipio or 'Não informado',
                uf=uf,
                cep=cep,
            ),
        )

    def _extrair_entidade_rosario_limeira(self, is_prestador: bool) -> Entidade:
        """Extrai prestador/tomador da NFS-e de Rosário da Limeira/MG (plataforma
        FUTURIZE, PDF digital). Blocos "PRESTADOR DE SERVIÇOS" / "TOMADOR DE
        SERVIÇOS" com rótulos por linha ("Razão Social:"/"Nome:", "CPF/CNPJ:",
        "Inscrição Municipal:", "Endereço:").

        O endereço vem numa linha única no formato
        "logradouro, nº - [complemento/extras] - bairro - CEP - MUNICÍPIO - UF".
        Parseamos de trás pra frente (UF = último segmento, município = penúltimo,
        CEP = o segmento que casa NNNNN-NNN, bairro = o segmento antes do CEP) —
        robusto ao número variável de segmentos intermediários (ex.: o tomador
        tem um "SC" extra entre logradouro e bairro).

        Quirk do pdfminer: bairros com letra-espaçada saem como
        "F R A N C I S C O B E R T O N I" (letter-spacing do PDF, TODAS as letras
        com espaço simples — sem como recuperar o limite de palavra); colapsamos
        as letras isoladas (-> "FRANCISCOBERTONI") sem inventar espaços, e só
        quando o segmento é de fato uma sequência de caracteres únicos (não toca
        bairros normais como "IAPI" nem "JARDIM AMERICA")."""
        t = self.raw_text
        m_prest = re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
        m_tom = re.search(r'TOMADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
        m_cnae = re.search(r'\bCNAE\b|DADOS\s+COMPLEMENTARES', t, re.IGNORECASE)

        if is_prestador:
            bloco = t[m_prest.end():m_tom.start()] if (m_prest and m_tom) else ''
            rotulo_razao = r'Raz[ãa]o\s+Social\s*:'
        else:
            if m_tom:
                fim = m_cnae.start() if (m_cnae and m_cnae.start() > m_tom.end()) else len(t)
                bloco = t[m_tom.end():fim]
            else:
                bloco = ''
            # "Nome:" (com ":" logo após) — não casa "Nome Fantasia:".
            rotulo_razao = r'Nome\s*:'

        def _collapse_spaced(s: str) -> str:
            tokens = s.split(' ')
            if len(tokens) >= 3 and all(len(tk) == 1 for tk in tokens if tk):
                return ''.join(tokens)
            return s

        m_razao = re.search(rotulo_razao + r'\s*(.+)', bloco, re.IGNORECASE)
        razao = m_razao.group(1).strip() if m_razao else ''

        m_cnpj = re.search(r'CPF/CNPJ\s*:\s*([\d./-]+)', bloco, re.IGNORECASE)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        m_im = re.search(r'Inscri[çc][ãa]o\s+Municipal\s*:\s*(\d+)', bloco, re.IGNORECASE)
        inscricao = m_im.group(1) if m_im else ''

        m_end = re.search(r'Endere[çc]o\s*:\s*(.+)', bloco, re.IGNORECASE)
        logradouro = numero = bairro = municipio = cep = ''
        uf = 'MG'
        if m_end:
            segs = [s.strip() for s in m_end.group(1).split(' - ') if s.strip()]
            if len(segs) >= 3:
                uf = segs[-1].upper()[:2]
                municipio = segs[-2]
                cep_idx = next((i for i, s in enumerate(segs) if re.match(r'\d{2}\.?\d{3}-?\d{3}$', s)), None)
                if cep_idx is not None:
                    cep = re.sub(r'\D', '', segs[cep_idx])
                    if cep_idx - 1 >= 1:
                        bairro = _collapse_spaced(segs[cep_idx - 1])
                logradouro = segs[0]
                # número no fim do logradouro ("RUA X, 194").
                m_num = re.search(r',\s*([0-9]+[A-Za-z]?)\s*$', logradouro)
                if m_num:
                    numero = m_num.group(1)
                    logradouro = logradouro[:m_num.start()].strip().rstrip(',').strip()

        cod_mun = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio) if municipio else ''

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao or ('Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'),
            inscricao_municipal=inscricao,
            endereco=Endereco(
                logradouro=logradouro or 'Não informado',
                numero=numero or 'S/N',
                bairro=bairro or 'Não informado',
                codigo_municipio=cod_mun,
                municipio=municipio or 'Não informado',
                uf=uf,
                cep=cep or '00000000',
            ),
        )

    def _extrair_entidade_camacari_avulsa(self, is_prestador: bool) -> Entidade:
        """Extrai prestador/tomador da NOTA FISCAL DE PRESTAÇÃO DE SERVIÇOS (AVULSA)
        da Prefeitura de Camaçari/BA (escaneada -> OCR). Blocos "IDENTIFICAÇÃO DO
        PRESTADOR" / "IDENTIFICAÇÃO DO TOMADOR", com rótulos numa estrutura fixa:
            Nome / Razão <razão>
            CPF / CNPJ: <cnpj>  Código Pessoa / Inscrição Municipal: ...
            CEP: <cep>  Município: <município>  UF: <uf>
            Logradouro: <logradouro>  Nº <número>
            [Complemento ...]  Bairro: <bairro>
        """
        t = self.raw_text
        m_prest = re.search(r'IDENTIFICA[ÇC][ÃA]O\s+DO\s+PRESTADOR', t, re.IGNORECASE)
        m_tom = re.search(r'IDENTIFICA[ÇC][ÃA]O\s+DO\s+TOMADOR', t, re.IGNORECASE)
        m_nat = re.search(r'NATUREZA\s+DA\s+OPERA[ÇC][ÃA]O', t, re.IGNORECASE)

        if is_prestador:
            bloco = t[m_prest.end():m_tom.start()] if (m_prest and m_tom) else ''
        else:
            if m_tom:
                fim = m_nat.start() if (m_nat and m_nat.start() > m_tom.end()) else len(t)
                bloco = t[m_tom.end():fim]
            else:
                bloco = ''

        # "Nome / Razão ECO COLETA TUDO ... LTDA" (sem ":" após "Razão").
        m_razao = re.search(r'Nome\s*/\s*Raz[ãa]o\s*:?\s*(.+)', bloco, re.IGNORECASE)
        razao = m_razao.group(1).strip() if m_razao else ''

        # "CPF / CNPJ: 17.095.195/0001-01" (para o resto da linha há "Código Pessoa"
        # ou "Inscrição Municipal", que o [\d./-]+ não captura).
        m_cnpj = re.search(r'CPF\s*/\s*CNPJ\s*:?\s*([\d./-]+)', bloco, re.IGNORECASE)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        m_im = re.search(r'Inscri[çc][ãa]o\s+Municipal\s*:?\s*(\d+)', bloco, re.IGNORECASE)
        inscricao = m_im.group(1) if m_im else ''

        # "CEP: 42802580 Município: CAMACARI UF: BA" — CEP (8 díg.), município e UF.
        m_cep = re.search(r'CEP\s*:?\s*(\d{5}-?\d{3}|\d{8})', bloco, re.IGNORECASE)
        cep = re.sub(r'\D', '', m_cep.group(1)) if m_cep else '00000000'

        m_mun = re.search(r'Munic[íi]pio\s*:?\s*(.+?)\s+UF\s*:?\s*([A-Z]{2})', bloco, re.IGNORECASE)
        municipio = m_mun.group(1).strip() if m_mun else ''
        uf = m_mun.group(2).strip().upper() if m_mun else 'BA'

        # "Logradouro: RUA A3 Nº. SN" / "Logradouro: R CAMBORIU Nº: 39".
        m_log = re.search(r'Logradouro\s*:?\s*(.+?)\s+N[ºo°]\.?\s*:?\s*([\w-]+)', bloco, re.IGNORECASE)
        logradouro = m_log.group(1).strip() if m_log else ''
        numero = m_log.group(2).strip() if m_log else 'S/N'

        m_bairro = re.search(r'Bairro\s*:?\s*(.+)', bloco, re.IGNORECASE)
        bairro = m_bairro.group(1).strip() if m_bairro else ''

        cod_mun = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio) if municipio else ''

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao or ('Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'),
            inscricao_municipal=inscricao,
            endereco=Endereco(
                logradouro=logradouro or 'Não informado',
                numero=numero or 'S/N',
                bairro=bairro or 'Não informado',
                codigo_municipio=cod_mun,
                municipio=municipio or 'Não informado',
                uf=uf,
                cep=cep or '00000000',
            ),
        )

    def _extrair_entidade_iacu(self, is_prestador: bool) -> Entidade:
        """Extrai prestador/tomador da NFS-e de Iaçu/BA (plataforma nfservico.com.br).

        Estrutura: blocos "PRESTADOR DE SERVIÇOS" e "TOMADOR DE SERVIÇOS", cada
        um com "Nome/Razão Social:", "CPF/CNPJ:"/"Inscrição Municipal:" e um
        "Endereço:" em linha única no formato "RUA X N, - BAIRRO - CEP: NNNNNNNN
        - CIDADE - UF". O bloco do tomador vem contaminado com o texto de um
        carimbo de recebimento (nome/cargo de quem recebeu); o parsing ancora em
        rótulos e no formato fixo do endereço, ignorando esse ruído.
        """
        t = self.raw_text
        m_prest = re.search(r'PRESTADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
        m_tom = re.search(r'TOMADOR\s+DE\s+SERVI[ÇC]OS', t, re.IGNORECASE)
        m_disc = re.search(r'DISCRIMINA[ÇC][ÃA]O\s+DOS\s+SERVI[ÇC]OS', t, re.IGNORECASE)

        if is_prestador:
            ini = m_prest.end() if m_prest else 0
            fim = m_tom.start() if m_tom else len(t)
        else:
            ini = m_tom.end() if m_tom else 0
            fim = m_disc.start() if m_disc else len(t)
        bloco = t[ini:fim]
        placeholder = 'Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'

        m_raz = re.search(r'Nome\s*/?\s*Raz[ãa]o\s+Social\s*:?\s*[\n\s]*(.+)', bloco, re.IGNORECASE)
        razao = m_raz.group(1).strip() if m_raz else placeholder
        razao = razao or placeholder

        m_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', bloco) or re.search(r'\b(\d{14})\b', bloco)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        logradouro, numero, bairro = 'Não informado', 'S/N', 'Não informado'
        cep, municipio, uf = '00000000', 'Não informado', 'BA'
        # "RUA JUVENTINO MEDRADO 94, - BOIADEIRA - CEP: 46860000 - IACU - BA"
        # (o logradouro não cruza linha: char class sem \n).
        m_end = re.search(
            r'([A-Za-zÀ-Úà-ú][A-Za-zÀ-Úà-ú0-9 .\']+?)\s+(\d+|S/?N),?\s*-\s*'
            r'([^\n-]+?)\s*-\s*CEP\s*:?\s*(\d{5}-?\d{3})\s*-\s*([^\n-]+?)\s*-\s*([A-Z]{2})\b',
            bloco, re.IGNORECASE)
        if m_end:
            logradouro = m_end.group(1).strip()
            numero = m_end.group(2).strip()
            bairro = m_end.group(3).strip()
            cep = re.sub(r'\D', '', m_end.group(4))
            municipio = m_end.group(5).strip()
            uf = m_end.group(6).upper()

        mun_cod = _ibge_resolver.extract_and_validate(municipio, uf, city_hint=municipio, raw_doc_text=t)

        return Entidade(
            cnpj_cpf=cnpj,
            razao_social=razao,
            endereco=Endereco(
                logradouro=logradouro or 'Não informado',
                numero=numero,
                bairro=bairro,
                codigo_municipio=mun_cod,
                municipio=municipio,
                uf=uf,
                cep=cep or '00000000',
            ),
        )

    @staticmethod
    def _parse_endereco_livre_osasco(raw: str) -> dict:
        """Quebra um endereço em linha única e formato livre (separado por
        vírgulas, sem rótulos de logradouro/número/bairro) em seus componentes.
        Usado pelo layout Osasco/NF-R, cujo campo "Endereço" vem como uma
        única string livre (ex: "AV. dos Autonomistas, 1496-BLOCO-B,3º
        ANDAR,PARTE-Vila Yara-06020012" ou "A AL HUMAITA, 0 - GUARAJUBA
        ,42840-562")."""
        raw = raw.strip().rstrip('.').strip()
        cep = ''
        m_cep = re.search(r'(\d{5}-?\d{3})\s*$', raw)
        if m_cep:
            cep = re.sub(r'\D', '', m_cep.group(1))
            raw = raw[:m_cep.start()].strip().rstrip(',- ').strip()

        bits = [b.strip() for b in raw.split(',') if b.strip()]
        logradouro = bits[0] if bits else 'Não informado'
        numero = 'S/N'
        bairro = 'Não informado'

        resto = bits[1:]
        if resto:
            m_num = re.match(r'\s*(\d+)\s*[-–]?\s*(.*)', resto[0])
            if m_num:
                numero = m_num.group(1)
                sobra = m_num.group(2).strip(' -')
                if sobra:
                    bairro = sobra
            extra = ' '.join(resto[1:]).strip()
            if extra:
                bairro = f"{bairro} {extra}".strip() if bairro != 'Não informado' else extra

        return {'logradouro': logradouro, 'numero': numero, 'bairro': bairro, 'cep': cep}

    def _extrair_entidade_campinas(self, is_prestador: bool) -> Entidade:
        """Extrai EMITENTE PRESTADOR / TOMADOR do layout Campinas/SP.

        A NFSe de Campinas é uma grade em que os rótulos ficam numa linha e os
        valores na linha seguinte, com vários campos por linha:

            CPF / CNPJ/ NIF   Inscrição Municipal   Telefone
            10.983.367/0001-26  00.165.107-2  (19) 9818-9401
            Nome / Nome Empresarial   E-mail
            PRESTO COMUNICACAO E SOM LTDA - ME  gabrielduarte2007 @gmail.com
            Endereço   Município   CEP
            AVENIDA CARLOS GRIMALDI 1171 D 22 JARDIM CONCEIÇÃO CAMPINAS / SP BRASIL 13091-000

        O parser genérico (baseado em "rótulo: valor" na mesma linha) não decodifica
        essa grade, por isso o tratamento dedicado.
        """
        t = self.raw_text

        if is_prestador:
            m_bloco = re.search(
                r'EMITENTE\s+PRESTADOR\s+DO\s+SERVI[CÇ]O(.*?)(?=TOMADOR\s+DO\s+SERVI[CÇ]O|$)',
                t, re.IGNORECASE | re.DOTALL)
        else:
            m_bloco = re.search(
                r'TOMADOR\s+DO\s+SERVI[CÇ]O(.*?)(?=SERVI[CÇ]O\s+PRESTADO|CNAE\s*/\s*CBO|$)',
                t, re.IGNORECASE | re.DOTALL)

        bloco = m_bloco.group(1) if m_bloco else ''
        linhas = [ln.strip() for ln in bloco.split('\n')]

        _HEADER_RE = re.compile(
            r'(CPF\s*/?\s*CNPJ|Inscri[cç][aã]o\s+Municipal|Telefone|'
            r'Nome\s*/\s*Nome|E-?mail|Endere[cç]o|Munic[ií]pio|CEP)',
            re.IGNORECASE)

        def valor_apos(header_re: str) -> str:
            """Primeira linha não-vazia após o rótulo que não seja outro cabeçalho."""
            for i, ln in enumerate(linhas):
                if re.search(header_re, ln, re.IGNORECASE):
                    for j in range(i + 1, len(linhas)):
                        cand = linhas[j].strip()
                        if not cand:
                            continue
                        if _HEADER_RE.search(cand):
                            return ''
                        return cand
                    return ''
            return ''

        # 1. CNPJ/CPF, Inscrição Municipal e Telefone (linha "doc  IM  telefone")
        linha_doc = valor_apos(r'CPF\s*/?\s*CNPJ')
        cnpj = '00000000000000'
        m_doc = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})', linha_doc)
        if m_doc:
            pure = re.sub(r'\D', '', m_doc.group(1))
            if self._validate_cnpj_cpf(pure):
                cnpj = pure

        insc = None
        telefone = None
        if m_doc:
            resto = linha_doc[m_doc.end():].strip()
            # Inscrição Municipal: próximo token com dígitos (ex: "00.165.107-2");
            # "-" isolado (tomador sem IM) é ignorado.
            m_im = re.search(r'([\d][\d.\-/]{3,})', resto)
            if m_im:
                insc_dig = re.sub(r'\D', '', m_im.group(1))
                if insc_dig:
                    insc = insc_dig
                    resto = resto[m_im.end():].strip()
            # Telefone: primeiro trecho que pareça um telefone (com DDD).
            m_tel = re.search(r'\(?\d{2}\)?\s*[\d.\-\s]{7,}', resto)
            if m_tel:
                tel_dig = re.sub(r'\D', '', m_tel.group(0))
                if 8 <= len(tel_dig) <= 13:
                    telefone = tel_dig

        # 2. Razão social + e-mail (linha após "Nome / Nome Empresarial")
        linha_nome = valor_apos(r'Nome\s*/\s*Nome')
        razao = ''
        email = None
        if linha_nome:
            tokens = linha_nome.split()
            # Detecta o token de domínio (o OCR costuma mesclar "@gmail.com" em
            # algo como "GQgmail.com"); o token anterior é o local-part.
            dom_idx = None
            for k, tok in enumerate(tokens):
                if re.search(r'(?i)(@|gmail|hotmail|outlook|yahoo|\.com|\.br|\.net|\.org)', tok):
                    dom_idx = k
                    break
            if dom_idx is not None:
                local_idx = dom_idx - 1 if dom_idx - 1 >= 0 else dom_idx
                razao = ' '.join(tokens[:local_idx]).strip()
                dom_tok = tokens[dom_idx]
                # Provedores conhecidos: o OCR costuma prefixar lixo ("GQgmail.com"),
                # então extraímos o provedor + TLD de dentro do token.
                m_known = re.search(r'(gmail|hotmail|outlook|yahoo|live|icloud|bol|uol|terra)\.com(?:\.br)?', dom_tok, re.IGNORECASE)
                if m_known:
                    dominio = m_known.group(0).lower()
                else:
                    m_any = re.search(r'[\w-]+\.(?:com(?:\.br)?|br|net|org|gov(?:\.br)?)', dom_tok, re.IGNORECASE)
                    dominio = (m_any.group(0) if m_any else dom_tok).lstrip('.')
                local = tokens[local_idx] if local_idx < dom_idx else ''
                local = re.sub(r'[^\w.%+-]', '', local)
                if local:
                    email = f'{local}@{dominio}'
            else:
                razao = linha_nome.strip()
            razao = re.sub(r'[\s/!|:.-]+$', '', razao).strip()

        if not razao:
            razao = 'Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'

        # 3. Endereço (linha após o cabeçalho "Endereço ... Município ... CEP")
        linha_end = valor_apos(r'Endere[cç]o')
        end_data = {
            'logradouro': 'Não informado', 'numero': 'S/N', 'bairro': 'Não informado',
            'municipio': 'Não informado',
            'codigo_municipio': _ibge_resolver.default_code,
            'uf': _ibge_resolver.default_uf, 'cep': '00000000',
        }
        if linha_end:
            raw_end = linha_end

            # CEP no fim da linha (ex: "13091-000")
            m_cep = re.search(r'(\d{5}-?\d{3})\s*$', raw_end)
            if m_cep:
                end_data['cep'] = re.sub(r'\D', '', m_cep.group(1))
                raw_end = raw_end[:m_cep.start()].strip()

            # País "BRASIL" antes do CEP
            raw_end = re.sub(r'\bBRASIL\b\s*$', '', raw_end, flags=re.IGNORECASE).strip()

            # Município / UF: "<MUNICIPIO> / SP" ou "<MUNICIPIO> | BA" (o OCR troca
            # a barra por pipe). Captura até 3 palavras antes do separador como
            # candidato a município (o IBGE resolver valida o nome real).
            m_mun = re.search(
                r'([A-Za-zÀ-ú]+(?:\s+[A-Za-zÀ-ú]+){0,2})\s*[/|]\s*([A-Z]{2})\b',
                raw_end)
            municipio_hint = None
            if m_mun:
                municipio_hint = m_mun.group(1).strip()
                end_data['uf'] = m_mun.group(2).strip().upper()
                # O que sobra antes do município é o logradouro/numero/bairro
                raw_end = raw_end[:m_mun.start()].strip()

            # Município final + bairro que "vazou" para o hint. O regex de município
            # capta até 3 palavras antes do separador (ex: "JARDIM CONCEIÇÃO
            # CAMPINAS"); a cidade real é o maior sufixo conhecido ("CAMPINAS") e
            # as palavras que sobram na frente são, na verdade, o bairro.
            municipio_final = municipio_hint or ''
            bairro_do_hint = ''
            if municipio_hint:
                palavras = municipio_hint.split()
                for start in range(len(palavras)):
                    cand = ' '.join(palavras[start:])
                    if re.sub(r'[^\w\s]', '', cand).strip().upper() in _ibge_resolver.KNOWN_CITIES:
                        municipio_final = cand
                        bairro_do_hint = ' '.join(palavras[:start]).strip()
                        break
                else:
                    municipio_final = palavras[-1]
                    bairro_do_hint = ' '.join(palavras[:-1]).strip()
            end_data['municipio'] = municipio_final or 'Não informado'
            if bairro_do_hint:
                end_data['bairro'] = bairro_do_hint

            # Divisão best-effort de logradouro / número / complemento na parte
            # restante (o que vem antes do bairro/município).
            if raw_end:
                # Ignora ordinais no nome da via (ex: "5º AVENIDA") ao procurar o
                # número do imóvel; prefere um número de 2+ dígitos.
                m_num = None
                for cand in re.finditer(r'\b(\d{1,6})\b(?![º°ªo])', raw_end):
                    m_num = cand
                    if len(cand.group(1)) >= 2:
                        break
                if m_num:
                    end_data['logradouro'] = raw_end[:m_num.start()].strip(' ,.-') or 'Não informado'
                    end_data['numero'] = m_num.group(1)
                    complemento = raw_end[m_num.end():].strip(' ,.-;')
                    if complemento:
                        end_data['complemento'] = complemento
                        if not bairro_do_hint:
                            end_data['bairro'] = complemento
                            end_data.pop('complemento', None)
                else:
                    end_data['logradouro'] = raw_end.strip(' ,.-')

            end_data['codigo_municipio'] = _ibge_resolver.extract_and_validate(
                raw_end, detected_uf=end_data['uf'],
                city_hint=end_data['municipio'], raw_doc_text=None
            )

        return Entidade(
            cnpj_cpf=cnpj,
            inscricao_municipal=insc,
            razao_social=razao,
            endereco=Endereco(**end_data),
            email=email,
            telefone=telefone,
        )

    @staticmethod
    def _split_endereco_campinas(raw_end: str) -> dict:
        """Quebra a linha de endereço do Campinas (sem município, já removido) em
        logradouro / número / complemento / bairro. Ex.:
          "AVENIDA CARLOS GRIMALDI 1171 D 22 JARDIM CONCEIÇÃO"
          "5ª AVENIDA ALTO DO SALDANHA 2671 SALA:1202;   BROTAS"
        """
        out = {'logradouro': 'Não informado', 'numero': 'S/N',
               'complemento': None, 'bairro': 'Não informado'}
        raw_end = raw_end.strip()
        if not raw_end:
            return out

        # Número do imóvel: primeiro número que NÃO seja ordinal ("5ª AVENIDA");
        # prefere 2+ dígitos.
        m_num = None
        for cand in re.finditer(r'\b(\d{1,6})\b(?![º°ªo])', raw_end):
            m_num = cand
            if len(cand.group(1)) >= 2:
                break
        if not m_num:
            out['logradouro'] = raw_end.strip(' ,.-')
            return out

        out['logradouro'] = raw_end[:m_num.start()].strip(' ,.-') or 'Não informado'
        out['numero'] = m_num.group(1)
        resto = raw_end[m_num.end():].strip(' ,.-;')
        if not resto:
            return out

        # Complemento/bairro: separador ";" quando presente; senão, um complemento
        # curto do tipo "D 22"/"SALA 1202" no início e o restante como bairro.
        if ';' in resto:
            comp, _, bairro = resto.partition(';')
            out['complemento'] = comp.strip(' ,.-') or None
            out['bairro'] = bairro.strip(' ,.-;') or 'Não informado'
        else:
            m_comp = re.match(r'([A-Za-z]{1,4}\.?\s*\d{1,5}[A-Za-z]?)\s+(.+)', resto)
            if m_comp:
                out['complemento'] = m_comp.group(1).strip()
                out['bairro'] = m_comp.group(2).strip(' ,.-')
            else:
                out['bairro'] = resto.strip(' ,.-')
        return out

    def _extrair_entidade_campinas_digital(self, is_prestador: bool) -> Entidade:
        """Extrai PRESTADOR/TOMADOR da NFSe Campinas em PDF digital (camada de
        texto). O pdfminer extrai a tabela de 2 colunas campo a campo, deixando
        CNPJ/Nome/Endereço contíguos por entidade, mas espalhando os demais
        campos (Inscrição Municipal, E-mail, Município, Telefone, CEP) num bloco
        posterior com as colunas intercaladas. A regra estável: a N-ésima
        ocorrência de cada rótulo pertence à N-ésima entidade (1ª = prestador,
        2ª = tomador).
        """
        t = self.raw_text
        lines = t.split('\n')
        idx = 0 if is_prestador else 1

        def ocorrencias(label_re: str):
            """Valores (1ª linha não-vazia seguinte) de cada linha == rótulo exato."""
            vals = []
            for i, l in enumerate(lines):
                if re.fullmatch(label_re, l.strip(), re.IGNORECASE):
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip():
                            vals.append(lines[j].strip())
                            break
            return vals

        def pick(label_re: str) -> str:
            vals = ocorrencias(label_re)
            return vals[idx].strip() if len(vals) > idx else ''

        # Bloco contíguo da entidade (CNPJ, Nome, Endereço)
        if is_prestador:
            m_bloco = re.search(
                r'EMITENTE\s+PRESTADOR\s+DO\s+SERVI[CÇ]O(.*?)(?=TOMADOR\s+DO\s+SERVI[CÇ]O|$)',
                t, re.IGNORECASE | re.DOTALL)
        else:
            m_bloco = re.search(
                r'TOMADOR\s+DO\s+SERVI[CÇ]O(.*?)(?=A\s+autenticidade|Inscri[cç][aã]o\s+Municipal|SERVI[CÇ]O\s+PRESTADO|$)',
                t, re.IGNORECASE | re.DOTALL)
        bl = [x.strip() for x in (m_bloco.group(1) if m_bloco else '').split('\n')]

        def apos(lst, label_re: str) -> str:
            for i, l in enumerate(lst):
                if re.search(label_re, l, re.IGNORECASE):
                    for j in range(i + 1, len(lst)):
                        cand = lst[j].strip()
                        if cand and not re.search(r'Nome\s*/\s*Nome|Endere[cç]o|CPF\s*/', cand, re.IGNORECASE):
                            return cand
            return ''

        # CNPJ/CPF
        cnpj = '00000000000000'
        m_doc = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})',
                          m_bloco.group(1) if m_bloco else '')
        if m_doc:
            pure = re.sub(r'\D', '', m_doc.group(1))
            if self._validate_cnpj_cpf(pure):
                cnpj = pure

        razao = apos(bl, r'Nome\s*/\s*Nome')
        razao = re.sub(r'[\s/!|:.-]+$', '', razao).strip()
        if not razao or re.search(r'Endere[cç]o|CPF', razao, re.IGNORECASE):
            razao = ''
        if not razao:
            razao = 'Prestador Não Identificado' if is_prestador else 'Tomador Não Identificado'

        # Campos espalhados (por índice de ocorrência)
        im_raw = pick(r'Inscri[cç][aã]o\s+Municipal')
        insc = re.sub(r'\D', '', im_raw) if im_raw else ''
        insc = insc or None

        email_raw = pick(r'E-?mail')
        email = email_raw if (email_raw and '@' in email_raw) else None

        tel_raw = pick(r'Telefone')
        tel_dig = re.sub(r'\D', '', tel_raw) if tel_raw else ''
        telefone = tel_dig if (8 <= len(tel_dig) <= 13) else None

        cep_raw = pick(r'CEP')
        cep = re.sub(r'\D', '', cep_raw) if cep_raw else ''
        cep = cep or '00000000'

        # Município / UF (ex.: "CAMPINAS / SP BRASIL")
        mun_raw = pick(r'Munic[ií]pio')
        municipio = 'Não informado'
        uf = 'SP'
        if mun_raw:
            m_mun = re.search(r'(.+?)\s*[/|]\s*([A-Z]{2})\b', mun_raw)
            if m_mun:
                municipio = m_mun.group(1).strip()
                uf = m_mun.group(2).strip().upper()
            else:
                municipio = re.sub(r'\bBRASIL\b', '', mun_raw, flags=re.IGNORECASE).strip()

        # Endereço (logradouro/numero/complemento/bairro) — município não vem aqui
        end_line = apos(bl, r'Endere[cç]o')
        end_line = re.sub(r'\bBRASIL\b\s*$', '', end_line, flags=re.IGNORECASE).strip()
        end_parts = self._split_endereco_campinas(end_line)

        cod_mun = _ibge_resolver.extract_and_validate(
            mun_raw or municipio, detected_uf=uf, city_hint=municipio, raw_doc_text=None)

        return Entidade(
            cnpj_cpf=cnpj,
            inscricao_municipal=insc,
            razao_social=razao,
            endereco=Endereco(
                logradouro=end_parts['logradouro'],
                numero=end_parts['numero'],
                complemento=end_parts['complemento'],
                bairro=end_parts['bairro'],
                municipio=municipio,
                uf=uf,
                codigo_municipio=cod_mun,
                cep=cep,
            ),
            email=email,
            telefone=telefone,
        )

    def _extrair_entidade_osasco_repasse(self, is_prestador: bool) -> Entidade:
        """Extrai EMITENTE/RECEPTOR do layout Osasco/SP (Nota Fiscal Eletrônica
        de Repasse - NF-R, ex: iFood Benefícios e Serviços Ltda). Campos em
        formato "Rótulo: valor", distintos dos rótulos "Prestador"/"Tomador"
        usados pela maioria dos outros layouts.
        """
        t = self.raw_text
        tipo_label = "Prestador" if is_prestador else "Tomador"

        if is_prestador:
            m_bloco = re.search(r'EMITENTE(.*?)(?=RECEPTOR|$)', t, re.IGNORECASE | re.DOTALL)
        else:
            m_bloco = re.search(r'RECEPTOR(.*?)(?=DISCRIMINA[CÇ][AÃ]O|IMPOSTOS\s+ADICIONAIS|$)', t, re.IGNORECASE | re.DOTALL)
        bloco = m_bloco.group(1) if m_bloco else t

        # "Razão Social:" ou "Razão Social/Nome:" (variações vistas em documentos reais)
        m_razao = re.search(r'Raz[ãa]o\s+Social\s*(?:/\s*Nome)?\s*:\s*(.+)', bloco, re.IGNORECASE)
        razao = m_razao.group(1).split('\n')[0].strip() if m_razao else f'{tipo_label} Não Identificado'

        # "CNPJ/CPF:" ou "CPF/CNPJ:" — ordem varia entre documentos
        m_cnpj = re.search(r'(?:CNPJ\s*/\s*CPF|CPF\s*/\s*CNPJ)\s*:\s*([\d./-]+)', bloco, re.IGNORECASE)
        cnpj = re.sub(r'\D', '', m_cnpj.group(1)) if m_cnpj else '00000000000000'

        m_im = re.search(r'Inscri[cç][aã]o\s+Municipal\s*:\s*(\d+)', bloco, re.IGNORECASE)
        insc = m_im.group(1).strip() if m_im else None

        # O ":" após "Município"/"UF" nem sempre aparece no texto extraído da
        # tabela (varia até dentro do mesmo documento, entre EMITENTE/RECEPTOR).
        m_end = re.search(r'Endere[cç]o\s*:\s*(.+?)(?=Munic[ií]pio\s*:?|\n\s*UF\b|$)', bloco, re.IGNORECASE | re.DOTALL)
        end_data = self._parse_endereco_livre_osasco(m_end.group(1)) if m_end else {
            'logradouro': 'Não informado', 'numero': 'S/N', 'bairro': 'Não informado', 'cep': '00000000'
        }

        m_mun = re.search(r'Munic[ií]pio\s*:\s*([^\n]+?)(?=\s*UF\b|\n|$)', bloco, re.IGNORECASE)
        municipio = m_mun.group(1).strip() if m_mun else 'Não informado'

        m_uf = re.search(r'\bUF\s*:?\s*([A-Z]{2})\b', bloco, re.IGNORECASE)
        uf = m_uf.group(1).upper() if m_uf else 'SP'

        # "E-mail:" ou "Email:"
        m_email = re.search(r'E-?mail\s*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', bloco, re.IGNORECASE)
        email = m_email.group(1).strip() if m_email else None

        # "Telefone:" ou "Fone:"
        m_fone = re.search(r'(?:Telefone|Fone)\s*:\s*([\(\)\d\s-]{6,20})', bloco, re.IGNORECASE)
        telefone = m_fone.group(1).strip() if m_fone else None

        mun_cod = _ibge_resolver.extract_and_validate(municipio, uf)

        return Entidade(
            cnpj_cpf=cnpj,
            inscricao_municipal=insc,
            razao_social=razao,
            endereco=Endereco(
                logradouro=end_data['logradouro'],
                numero=end_data['numero'],
                bairro=end_data['bairro'],
                codigo_municipio=mun_cod,
                municipio=municipio,
                uf=uf,
                cep=end_data['cep'] or '00000000',
            ),
            email=email,
            telefone=telefone,
        )

    def _extrair_valores(self) -> Valores:
        t = self.raw_text

        if self.layout == LAYOUT_CUIABA:
            # Só intercepta o FORMATO EM GRADE (scan degradado, consolidado MTI):
            # cabeçalho "Vl./Vi. Total dos Serviços ... | ... | Total do ISSQN |
            # ISSQN Retido | ..." seguido, na PRÓXIMA linha, de uma linha de VALORES
            # com vários "R$" (o OCR troca "Vl."→"Vi."). Pegamos os R$ por POSIÇÃO:
            # [0]=serviços, [3]=base de cálculo, [4]=Total do ISSQN. O formato com
            # rótulo limpo ("Vl. Total dos Serviços: R$ ...") NÃO casa (o ":" corta
            # antes da quebra) e cai no extrator genérico abaixo, que já o tratava.
            m_row = re.search(r'V[il]\.?\s*Total\s+dos\s+Servi[çc]os[^\n:]*\n\s*(R\$[^\n]*R\$[^\n]*)', t, re.IGNORECASE)
            if m_row:
                row = m_row.group(1)
                vals = [self._parse_valor(x) for x in re.findall(r'R\$\s*([\d.,]+)', row)]
                serv = base = iss = 0.0
                if len(vals) >= 5:
                    serv, base, iss = vals[0], vals[3], vals[4]
                elif vals:
                    serv = vals[0]; base = serv
                iss_retido = bool(re.search(r'\bSim\b', row))
                # Alíquota: coluna da grade de atividade ("... - 5,00 | 701 <NBS 9díg>").
                aliq = 0.0
                m_al = re.search(r'(\d{1,2},\d{2})\s*\|?\s*\d{3,4}\s+\d{9}', t)
                if m_al:
                    aliq = self._parse_valor(m_al.group(1)) / 100
                # Cross-check fiel à face: ISS impresso = base×alíquota (560×5%=28,00);
                # se a grade não devolveu o ISS, computa.
                if not iss and base and aliq:
                    iss = round(base * aliq, 2)
                # Líquido: 2ª grade ("... VI. Líquido da Nota Fiscal" → último R$ da linha).
                liquido = serv or base
                m_liq = re.search(r'L[íi]quido\s+da\s+Nota\s+Fiscal\s*\n\s*(R\$[^\n]*)', t, re.IGNORECASE)
                if m_liq:
                    rs = re.findall(r'R\$\s*([\d.,]+)', m_liq.group(1))
                    if rs:
                        liquido = self._parse_valor(rs[-1])
                return Valores(
                    valor_servicos=serv, valor_deducoes=0.0, base_calculo=base or serv,
                    aliquota=aliq, valor_iss=iss, iss_retido=iss_retido,
                    valor_iss_retido=iss if iss_retido else 0.0,
                    valor_liquido_nfse=liquido or serv,
                )

        if self.layout == LAYOUT_NACIONAL:
            # DANFSe Nacional: grade "rótulo(s) em cima / valores embaixo", com
            # campos vazios marcados por "-" e linhas em branco entre rótulo e
            # valor. Os padrões genéricos não casam essa estrutura (chegam a pescar
            # o número da nota como ISS), então extraímos por proximidade de cada
            # rótulo próprio, pegando o primeiro "R$ n,nn" após ele.
            def _rs_apos(label, janela=200):
                m = re.search(label, t, re.IGNORECASE)
                if not m:
                    return 0.0
                trecho = t[m.end(): m.end() + janela]
                m_v = re.search(r'R\$\s*([\d.]+,\d{2})', trecho)
                return self._parse_valor(m_v.group(1)) if m_v else 0.0

            serv = _rs_apos(r'Valor\s+do\s+Servi[çc]o')
            liquido = _rs_apos(r'Valor\s+L[íi]quido\s+da\s+NFS')
            if not serv:
                serv = liquido
            if not liquido:
                liquido = serv

            # BC/ISS/alíquota só têm valor em notas com tributação efetiva; em MEI
            # ("Optante - Microempreendedor Individual") saem em branco ("-").
            def _num_rotulo(label, janela=40):
                m = re.search(label + r'[\s\S]{0,' + str(janela) + r'}?R\$\s*([\d.]+,\d{2})', t, re.IGNORECASE)
                return self._parse_valor(m.group(1)) if m else 0.0

            base = _num_rotulo(r'BC\s+ISSQN')
            iss = _num_rotulo(r'ISSQN\s+Apurado')
            iss_retido = bool(re.search(r'ISSQN\s+Retido[\s\S]{0,40}?\bSim\b', t, re.IGNORECASE))

            return Valores(
                valor_servicos=serv,
                valor_deducoes=0.0,
                base_calculo=base or serv,
                aliquota=0.0,
                valor_iss=iss,
                iss_retido=iss_retido,
                valor_iss_retido=iss if iss_retido else 0.0,
                valor_liquido_nfse=liquido or serv,
            )

        if self.layout == LAYOUT_MATA_SAO_JOAO:
            # Duas grades "rótulo-em-cima / valores-embaixo" (padrão SAATRI):
            #  1) "Valor do(s) Serviço(s) | Valor Dedução | Desconto Incondicionado |
            #     Base de Cálculo ISS"  ->  "10.000,00 0,00 0,00 10.000,00"
            #     (serviços, dedução, desconto incondicionado, base de cálculo)
            #  2) "Alíquota ISS (%) | Valor do ISS | Valor ISS Retido | Desconto
            #     Condicionado"  ->  "0,00 0,00 0,00 0,00"
            #  E o total em "Total do(s) Serviço(s) | Total Líquido" -> "10.000,00 10.000,00".
            serv = base = 0.0
            deducoes = desc_incond = 0.0
            aliquota = iss = iss_retido_val = desc_cond = 0.0
            liquido = 0.0

            m1 = re.search(
                r'Valor\s+do\(s\)\s+Servi[çc]o\(s\).*?Base\s+de\s+C[áa]lculo\s+ISS\s*\n\s*'
                r'([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
                t, re.IGNORECASE)
            if m1:
                serv = self._parse_valor(m1.group(1))
                deducoes = self._parse_valor(m1.group(2))
                desc_incond = self._parse_valor(m1.group(3))
                base = self._parse_valor(m1.group(4))

            m2 = re.search(
                r'Al[íi]quota\s+ISS\s*\(%\).*?Desconto\s+Condicionado\s*\n\s*'
                r'([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)',
                t, re.IGNORECASE)
            if m2:
                aliquota = self._parse_valor(m2.group(1)) / 100
                iss = self._parse_valor(m2.group(2))
                iss_retido_val = self._parse_valor(m2.group(3))
                desc_cond = self._parse_valor(m2.group(4))

            m_tot = re.search(
                r'Total\s+do\(s\)\s+Servi[çc]o\(s\)\s+Total\s+L[íi]quido\s*\n[-\s]*([\d.,]+)\s+([\d.,]+)',
                t, re.IGNORECASE)
            liquido = self._parse_valor(m_tot.group(2)) if m_tot else (serv or base)

            return Valores(
                valor_servicos=serv,
                valor_deducoes=deducoes,
                base_calculo=base or serv,
                aliquota=aliquota,
                valor_iss=iss,
                iss_retido=iss_retido_val > 0,
                valor_iss_retido=iss_retido_val,
                desconto_incondicionado=desc_incond,
                desconto_condicionado=desc_cond,
                valor_liquido_nfse=liquido or serv,
            )

        if self.layout == LAYOUT_ROSARIO_LIMEIRA:
            # Layout FUTURIZE (rótulo-em-cima / valor-na-linha-de-baixo). O total
            # vem de "VALOR TOTAL DE SERVIÇOS = R$ 158,40" (na mesma linha).
            def _num_apos(label):
                m = re.search(label + r'\s*\n\s*([\d.,]+)', t, re.IGNORECASE)
                return self._parse_valor(m.group(1)) if m else 0.0

            m_serv = re.search(r'VALOR\s+TOTAL\s+DE\s+SERVI[ÇC]OS\s*=\s*R\$\s*([\d.,]+)', t, re.IGNORECASE)
            serv = self._parse_valor(m_serv.group(1)) if m_serv else 0.0
            base = _num_apos(r'Base\s+de\s+C[áa]lculo\s*\(R\$\)')
            aliquota = _num_apos(r'Al[íi]quota\s*\(%\)') / 100
            iss = _num_apos(r'Valor\s+do\s+ISS\s*\(R\$\)')
            iss_retido_val = _num_apos(r'ISS\s+Retido\s*\(R\$\)')
            liquido = _num_apos(r'Valor\s+L[íi]quido\s*\(R\$\)')
            pis = _num_apos(r'PIS\s*\(R\$\)')
            cofins = _num_apos(r'COFINS\s*\(R\$\)')
            inss = _num_apos(r'INSS\s*\(R\$\)')
            ir = _num_apos(r'IR\s*\(R\$\)')
            csll = _num_apos(r'CSLL\s*\(R\$\)')
            outras = _num_apos(r'Outras\s+Reten[çc][õo]es\s*\(R\$\)')

            return Valores(
                valor_servicos=serv,
                valor_deducoes=0.0,
                valor_pis=pis, valor_cofins=cofins, valor_inss=inss,
                valor_ir=ir, valor_csll=csll, outras_retencoes=outras,
                base_calculo=base or serv,
                aliquota=aliquota,
                valor_iss=iss,
                iss_retido=iss_retido_val > 0,
                valor_iss_retido=iss_retido_val,
                valor_liquido_nfse=liquido or serv,
            )

        if self.layout == LAYOUT_CAMACARI_AVULSA:
            # Nota avulsa ISENTA (alíquota 0 / ISS 0 / sem retenção — a própria nota
            # diz "NÃO CABE RETENÇÃO NA FONTE"). O rótulo "TOTAL SERVIÇOS 16.500,00"
            # sai limpo no OCR (bruto). Já o "VALOR TRIBUTÁVEL" tem o 1º dígito
            # trocado pelo OCR (14.685 -> 74.685) e o "VALOR LÍQUIDO" fica em branco,
            # então tiramos base/líquido da CAMADA DIGITAL (pdfminer), que traz os
            # valores exatos. Decisão do usuário: ValorServicos = total bruto,
            # BaseCalculo = valor tributável.
            m_serv = re.search(r'TOTAL\s+SERVI[ÇC]OS[^\d\n]*([\d.]+,\d{2})', t, re.IGNORECASE)
            serv = self._parse_valor(m_serv.group(1)) if m_serv else 0.0

            dig = ''
            try:
                dig = extract_text(self.pdf_path) or ''
            except Exception:
                dig = ''
            dig_vals = sorted({self._parse_valor(x) for x in re.findall(r'\d[\d.]*,\d{2}', dig)})
            # Sem retenção -> base == líquido == valor tributável. Ele é o valor
            # digital diferente do total de serviços; se só houver um valor
            # (nota totalmente tributável), base = serv.
            if not serv and dig_vals:
                serv = max(dig_vals)
            base = next((v for v in dig_vals if abs(v - serv) > 0.001), serv) if dig_vals else serv

            return Valores(
                valor_servicos=serv,
                valor_deducoes=0.0,
                base_calculo=base or serv,
                aliquota=0.0,
                valor_iss=0.0,
                iss_retido=False,
                valor_iss_retido=0.0,
                valor_liquido_nfse=base or serv,
            )

        if self.layout == LAYOUT_SAO_PAULO_2:
            # NFS-e tributada de São Paulo (escaneada). A grade oficial
            # "Valor Total das Deduções | Base de Cálculo | Alíquota (%) |
            # Valor do ISS | crédito" traz os 5 valores numa linha só, na ordem.
            # É a fonte confiável do ISS — o corpo do texto tem valores-isca
            # (ex.: "PERC. ISS 2.90% Valor ISS: 137,06", que na verdade é o
            # COFINS de 7,60%). O total vem de "VALOR TOTAL DO SERVIÇO = R$ ...".
            m_val = re.search(r'VALOR\s+TOTAL\s+DO\s+SERVI[ÇC]O\s*=?\s*R\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            val_serv = self._parse_valor(m_val.group(1)) if m_val else 0.0

            NUM = r'([\d\.]*,\d{2})'
            m_grid = re.search(
                r'Valor\s+Total\s+das\s+Dedu[çc][õo]es.*?Base\s+de\s+C[áa]lculo.*?'
                r'Al[íi]quota.*?Valor\s+do\s+ISS.*?\n\s*'
                + NUM + r'\s+' + NUM + r'\s+' + NUM + r'%?\s+' + NUM,
                t, re.IGNORECASE | re.DOTALL)
            if m_grid:
                deducoes = self._parse_valor(m_grid.group(1))
                base = self._parse_valor(m_grid.group(2))
                aliquota = self._parse_valor(m_grid.group(3)) / 100
                iss = self._parse_valor(m_grid.group(4))
            else:
                deducoes, base, aliquota, iss = 0.0, val_serv, 0.0, 0.0

            return Valores(
                valor_servicos=val_serv,
                valor_deducoes=deducoes,
                base_calculo=base,
                aliquota=aliquota,
                valor_iss=iss,
                iss_retido=False,
                valor_liquido_nfse=val_serv,
            )

        if self.layout == LAYOUT_SALVADOR:
            m_val = re.search(r'VALOR\s+TOTAL\s+DA\s+NOTA\s*[=:]\s*R\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            val_serv = self._parse_valor(m_val.group(1)) if m_val else 0.0

            # Grade "Valor INSS / PIS / COFINS / IR / CSLL / Outras Retenções /
            # Valor Líquido": rótulos numa linha, os 7 valores na linha
            # seguinte na mesma ordem — mesmo padrão de "grade rótulo-em-cima/
            # valor-embaixo" já visto em Camaçari/Campinas. Tolera um "]" solto
            # entre valores (ruído de borda de tabela capturado pelo OCR).
            NUM = r'(\d{1,3}(?:\.\d{3})*,\d{2})'
            SEP = r'\s*\]?\s*'
            m_grid = re.search(
                r'Valor\s+INSS.*?Valor\s+L[ií]quido\s*\(R\$\)\s*:?\s*\n\s*'
                + NUM + SEP + NUM + SEP + NUM + SEP + NUM + SEP + NUM + SEP + NUM + SEP + NUM,
                t, re.IGNORECASE
            )
            if m_grid:
                inss, pis, cofins, ir, csll, outras, liquido = (self._parse_valor(g) for g in m_grid.groups())
            else:
                inss = pis = cofins = ir = csll = outras = 0.0
                liquido = val_serv

            # Sociedade de Uniprofissionais com "ISS RECOLHIDO POR QUOTA
            # PROFISSIONAL ALÍQUOTA FIXA": a própria nota deixa Base de
            # Cálculo/Alíquota/Valor do ISS em branco ("*") porque o ISS é pago
            # por quota fixa mensal, não por percentual sobre o serviço —
            # gravamos 0 nesses três campos em vez de inferir a partir do
            # Valor dos Serviços (decisão confirmada com o usuário).
            if re.search(r'RECOLHIDO\s+POR\s+QUOTA\s+PROFISSIONAL', t, re.IGNORECASE):
                base, aliq, iss = 0.0, 0.0, 0.0
            else:
                m_base = re.search(r'Base\s+de\s+C[aá]lculo\s*\(R\$\)\D*?([\d\.,]+)', t, re.IGNORECASE)
                base = self._parse_valor(m_base.group(1)) if m_base else val_serv
                m_aliq = re.search(r'Al[ií]quota\s*\(%\)\D*?(\d{1,2},\d{1,2})', t, re.IGNORECASE)
                aliq = (self._parse_valor(m_aliq.group(1)) / 100) if m_aliq else 0.0
                m_iss = re.search(r'Valor\s+do\s+ISS\s*\(R\$\)\D*?([\d\.,]+)', t, re.IGNORECASE)
                iss = self._parse_valor(m_iss.group(1)) if m_iss else 0.0

            return Valores(
                valor_servicos=val_serv,
                valor_deducoes=0.0,
                valor_pis=pis, valor_cofins=cofins, valor_inss=inss,
                valor_ir=ir, valor_csll=csll, outras_retencoes=outras,
                base_calculo=base, aliquota=aliq, valor_iss=iss,
                valor_liquido_nfse=liquido,
            )

        if self.layout == LAYOUT_LAURO_FREITAS:
            # Grade "Valor Total Deduções / Base de Cálculo / Alíquota (%) /
            # Valor do ISS / ISSQN Retido": rótulos numa linha, os 5 valores
            # na sequência seguinte, na mesma ordem. O prefixo "R$" antes dos
            # 2 primeiros valores nem sempre sai no texto (ex. nota NFTS
            # 2026302, BDP LOGISTICA) — tolerado como opcional.
            m_row = re.search(
                r'Valor\s+Total\s+Dedu[çc][õo]es\s*\(R\$\)\s*Base\s+de\s+C[áa]lculo\s*\(R\$\)\s*'
                r'Al[íi]quota\s*\(%\)\s*Valor\s+do\s+ISS\s*\(R\$\)\s*ISSQN\s+Retido\s*\(R\$\)\s*'
                r'(?:R\$\s*)?([\d\.,]+)\s*(?:R\$\s*)?([\d\.,]+)\s*([\d\.,]+)\s*([\d\.,]+)\s*(Sim|N[ãa]o)',
                t, re.IGNORECASE
            )
            if m_row:
                deducoes = self._parse_valor(m_row.group(1))
                base = self._parse_valor(m_row.group(2))
                aliquota = self._parse_valor(m_row.group(3)) / 100
                iss = self._parse_valor(m_row.group(4))
                iss_retido = m_row.group(5).strip().lower() == 'sim'
            else:
                deducoes = base = aliquota = iss = 0.0
                iss_retido = False

            m_val_total = re.search(r'VALOR\s+TOTAL\s+DA\s+NOTA\s+FISCAL\s*:?\s*R\$\s*([\d\.,]+)', t, re.IGNORECASE)
            val_serv = self._parse_valor(m_val_total.group(1)) if m_val_total else base

            # Grade "RETENÇÃO DE IMPOSTOS": rótulos PIS/COFINS/INSS/IRRF/CSLL/
            # Outras Retenções seguidos dos valores na mesma ordem, mas o
            # número de valores impressos pode ser menor que o de rótulos
            # (coluna em branco) — completamos com 0,00 os que faltarem.
            def _nums(regiao: str):
                return [self._parse_valor(x) for x in re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', regiao)]

            m_ret_block = re.search(
                r'RETEN[ÇC][ÃA]O\s+DE\s+IMPOSTOS(.*?)VALOR\s+L[ÍI]QUIDO\s+DA\s+NOTA\s+FISCAL',
                t, re.IGNORECASE | re.DOTALL
            )
            ret_nums = (_nums(m_ret_block.group(1)) if m_ret_block else []) + [0.0] * 6
            pis, cofins, inss, ir, csll, outras = ret_nums[:6]

            m_liq = re.search(r'VALOR\s+L[ÍI]QUIDO\s+DA\s+NOTA\s+FISCAL\s*:?\s*R\$\s*([\d\.,]+)', t, re.IGNORECASE)
            liquido = self._parse_valor(m_liq.group(1)) if m_liq else val_serv

            return Valores(
                valor_servicos=val_serv,
                valor_deducoes=deducoes,
                valor_pis=pis, valor_cofins=cofins, valor_inss=inss,
                valor_ir=ir, valor_csll=csll, outras_retencoes=outras,
                base_calculo=base, aliquota=aliquota, valor_iss=iss,
                iss_retido=iss_retido,
                valor_liquido_nfse=liquido,
            )

        if self.layout == LAYOUT_IACU_NFSE:
            # NFS-e tributada (Prefeitura de Iaçu/BA). Grade "Valor total das
            # deduções / Base de cálculo / Alíquota (%) / Valor do ISS / Crédito":
            # os rótulos numa linha e os 5 valores na linha seguinte, na mesma
            # ordem. Diferente da família de locação, aqui há ISS real (3%),
            # então espelhamos a face (base/alíquota/ISS preenchidos).
            m_val = re.search(r'VALOR\s+TOTAL\s+DA\s+NOTA\s*=?\s*R\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            val_serv = self._parse_valor(m_val.group(1)) if m_val else 0.0

            NUM = r'([\d\.]*,\d{2})'
            m_grid = re.search(
                r'Valor\s+total\s+das\s+dedu[çc][õo]es.*?Cr[ée]dito\s*\(R\$\)\s*:?\s*\n\s*'
                + NUM + r'\s+' + NUM + r'\s+' + NUM + r'\s+' + NUM + r'\s+' + NUM,
                t, re.IGNORECASE | re.DOTALL)
            if m_grid:
                deducoes = self._parse_valor(m_grid.group(1))
                base = self._parse_valor(m_grid.group(2))
                aliquota = self._parse_valor(m_grid.group(3)) / 100
                iss = self._parse_valor(m_grid.group(4))
            else:
                deducoes, base, aliquota, iss = 0.0, val_serv, 0.0, 0.0

            m_liq = re.search(r'Valor\s+l[íi]quido\s*\(R\$\)\s*:?\s*\n\s*([\d\.,]+)', t, re.IGNORECASE)
            liquido = self._parse_valor(m_liq.group(1)) if m_liq else val_serv

            return Valores(
                valor_servicos=val_serv,
                valor_deducoes=deducoes,
                base_calculo=base,
                aliquota=aliquota,
                valor_iss=iss,
                iss_retido=False,
                valor_liquido_nfse=liquido,
            )

        if self.layout == LAYOUT_PASSWORD_ENOTAS:
            # NFS-e tributada (ISS 3%, Simples Nacional). Cada valor tem rótulo
            # próprio com o valor na linha seguinte. O "VALOR DO ISS" é
            # renderizado como "-" (não destacado, recolhido via DAS do Simples),
            # então espelhamos a face: base e alíquota preenchidas, ISS = 0,00.
            def _val_apos(rotulo: str) -> float:
                m = re.search(rotulo + r'\s*:?\s*\n+\s*R\$?\s*([\d\.,]+)', t, re.IGNORECASE)
                return self._parse_valor(m.group(1)) if m else 0.0

            val_serv = _val_apos(r'VALOR\s+DOS\s+SERVI[ÇC]OS')
            base = _val_apos(r'BASE\s+DE\s+C[ÁA]LCULO')
            deducoes = _val_apos(r'\(-\)\s*DEDU[ÇC][ÕO]ES')
            liquido = _val_apos(r'VALOR\s+L[ÍI]QUIDO')

            m_aliq = re.search(r'AL[ÍI]QUOTA\s*:?\s*\n+\s*(\d{1,2},\d{1,2})\s*%', t, re.IGNORECASE)
            aliquota = (self._parse_valor(m_aliq.group(1)) / 100) if m_aliq else 0.0

            return Valores(
                valor_servicos=val_serv,
                valor_deducoes=deducoes,
                base_calculo=base,
                aliquota=aliquota,
                valor_iss=0.0,
                iss_retido=False,
                valor_liquido_nfse=liquido if liquido else val_serv,
            )

        if self.layout == LAYOUT_ARMAC_LOCACAO:
            # Fatura de locação de bens móveis (não sujeita a ISS). O "Valor
            # total" (ex.: "Valortotal: 103.640,00", às vezes colado no OCR) é o
            # total já com seguro/acréscimos, que é o valor faturado.
            m = re.search(r'Valor\s*total\s*:?\s*\|?\s*R?\$?\s*([\d.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m.group(1)) if m else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_SULSEG_COBRANCA:
            # Nota de cobrança de locação de bens móveis — "OPERAÇÃO NÃO SUJEITA
            # AO I.S.S. DE ACORDO COM A LEI COMPLEMENTAR 116/03." (base/ISS/
            # alíquota zerados, como nos demais layouts de locação).
            m_val = re.search(r'VALOR\s+L[IÍ]QUIDO\s+DA\s+NOTA\s+DE\s+COBRAN[ÇC]A\s*[\n\s]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_FATURA_LOCACAO_GENERICA:
            # "Não é fato gerador do ISSQN a locação de bens móveis..." — mesmo
            # tratamento da família de locação (base/alíquota/ISS zerados).
            # "TOTAL: R$ 69,00" já é líquido (desconto/acréscimo aplicados).
            m_val = re.search(r'TOTAL\s*:\s*R\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_CPE_LOCACAO:
            m_val = re.search(r'\bValor\b\s*[:\s\n]+([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_GUINCHO_CIDADE:
            m_val = re.search(r'VALOR\s+TOTAL\s+DA\s+FATURA\s*[:\s\n]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_OSASCO_REPASSE:
            # NF-R de repasse: não discrimina Base de Cálculo/Alíquota/ISS (regime
            # especial — o próprio documento diz que a apuração do ISS "quando
            # aplicável" fica a cargo do emitente). Nem todo documento traz
            # "Valor da Nota" explícito — alguns só mostram "Valor do Repasse",
            # que na prática sai com o mesmo valor.
            m_val = re.search(r'Valor\s+da\s+Nota\s*:\s*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            if not m_val:
                m_val = re.search(r'Valor\s+do\s+Repasse\s*:?\s*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_CAMPINAS:
            # Duas grades rótulo-em-cima / valores-embaixo:
            #  CÁLCULO DO ISSQN: [Valor total, Deduções, Desc. incond., Base de
            #                     cálculo, Alíquota (%), Valor do ISSQN]
            #  VALOR TOTAL:      [Base de cálculo, Retenções, Desc. incond.,
            #                     Desc. condicionado, Valor Líquido]
            # O OCR às vezes perde o dígito inicial do "Valor total" (700,00 -> 00,00)
            # e mistura as colunas de alíquota/ISS. A "Base de cálculo do ISSQN"
            # é o valor que sai limpo de forma consistente, então a usamos como
            # âncora (para Simples Nacional, base == valor dos serviços).
            def _nums(regiao: str):
                return [self._parse_valor(x) for x in re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', regiao)]

            # CÁLCULO termina em RETENÇÕES — NÃO em "VALOR TOTAL", pois o próprio
            # rótulo desta grade começa com "Valor total da NFSe Campinas".
            m_calc = re.search(r'C[ÁA]LCULO\s+DO\s+ISSQN(.*?)(?:RETEN[ÇC][ÕO]ES|$)', t, re.IGNORECASE | re.DOTALL)
            nums_calc = _nums(m_calc.group(1)) if m_calc else []

            # Grade "VALOR TOTAL" (âncora de fim de documento). O OCR às vezes
            # trunca as últimas colunas desta linha, então ela é usada só como reforço.
            m_tot = re.search(r'VALOR\s+TOTAL\s*\n(.*?)(?:INFORMA[ÇC][ÕO]ES|$)', t, re.IGNORECASE | re.DOTALL)
            nums_tot = _nums(m_tot.group(1)) if m_tot else []

            # Colunas da grade CÁLCULO: [valor_total, deduções, desc_incond, base,
            # alíquota, valor_iss]. A "Base de cálculo do ISSQN" (4ª coluna) sai
            # limpa de forma consistente; o "Valor total" (1ª) às vezes perde o
            # dígito inicial no OCR. Por isso a base é a âncora.
            valor_total = nums_calc[0] if nums_calc else 0.0
            deducoes = nums_calc[1] if len(nums_calc) >= 2 else 0.0
            desc_incond = nums_calc[2] if len(nums_calc) >= 3 else 0.0
            base = nums_calc[3] if len(nums_calc) >= 4 else 0.0
            aliq = (nums_calc[4] / 100.0) if len(nums_calc) >= 5 else 0.0
            iss = nums_calc[5] if len(nums_calc) >= 6 else 0.0
            if base == 0.0 and nums_calc:
                base = max(nums_calc)

            # Valor dos serviços: usa o "Valor total" se saiu íntegro; senão a base.
            val_serv = valor_total if valor_total > 0 else base
            if val_serv == 0.0:
                val_serv = max(nums_tot) if nums_tot else 0.0
            if base == 0.0:
                base = val_serv

            # Colunas da grade VALOR TOTAL: [base, retenções, desc_incond,
            # desc_cond, líquido]. Como o OCR pode truncar as últimas, derivamos
            # o líquido por cálculo quando a coluna não veio íntegra.
            retencoes_tot = nums_tot[1] if len(nums_tot) >= 2 else 0.0
            desc_cond = nums_tot[3] if len(nums_tot) >= 4 else 0.0
            liquido_grid = nums_tot[4] if len(nums_tot) >= 5 else 0.0
            if liquido_grid > 0:
                liquido = liquido_grid
            else:
                liquido = val_serv - deducoes - desc_incond - desc_cond - retencoes_tot
            if liquido <= 0.0:
                liquido = val_serv

            return Valores(
                valor_servicos=val_serv,
                valor_deducoes=deducoes,
                base_calculo=base,
                aliquota=aliq,
                valor_iss=iss,
                valor_liquido_nfse=liquido,
                desconto_incondicionado=desc_incond,
                desconto_condicionado=desc_cond,
                outras_retencoes=retencoes_tot,
            )

        if self.layout == LAYOUT_BF_AMBIENTAIS:
            m_val = re.search(r'Total\s+Bruto\s*[\n\r\s]*Descontos\s*[\n\r\s]*Total\s+L[ií]quido\s*[\n\r\s]*([\d\.,]+)', t, re.IGNORECASE)
            if not m_val:
                m_val = re.search(r'Total\s+Bruto\s*[\s\n\r]*.*?\n\s*([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_LMR_ENGENHARIA:
            m_val = re.search(r'VALOR\s+TOTAL\s*[\n\r\s]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_FF_LOCACAO:
            # "VALOR TOTAL DA FATURA" costuma trazer um placeholder de
            # template NÃO SUBSTITUÍDO pela própria nota-fonte ("R$
            # #venda_valor_total#" - bug do sistema de faturamento do
            # emissor, confirmado na imagem renderizada, não é erro de OCR).
            # Quando isso acontece o regex de dígitos não casa e caímos no
            # fallback da tabela de itens; se uma nota futura vier com esse
            # campo devidamente preenchido, ele é usado primeiro.
            m_val = re.search(r'VALOR\s+TOTAL\s+DA\s+FATURA\s*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            if m_val:
                v = self._parse_valor(m_val.group(1))
            else:
                # Tabela "Descrição | Contrato | Valor Unitário | Qtde. |
                # Valor Liquido": cada linha de item traz 2 valores "R$"
                # (unitário e líquido, nessa ordem) - somamos só os líquidos
                # (índices ímpares), robusto a mais de 1 item.
                m_ini = re.search(r'Valor\s+L[ií]quido', t, re.IGNORECASE)
                m_fim = re.search(r'VALOR\s+TOTAL\s+DA\s+FATURA', t, re.IGNORECASE)
                bloco_itens = t
                if m_ini:
                    bloco_itens = t[m_ini.end():m_fim.start()] if m_fim else t[m_ini.end():]
                valores_rs = re.findall(r'R\$\s*([\d\.,]+)', bloco_itens)
                liquidos = valores_rs[1::2] if len(valores_rs) >= 2 else valores_rs
                v = sum(self._parse_valor(x) for x in liquidos)
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_GERACAO_ENERGIA:
            m_val = re.search(r'(\d{2}/\d{2}/\d{4})\s+([\d\.,]+)\s+([\d\.,]+)', t)
            v = self._parse_valor(m_val.group(3)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_LOCONTAINERS:
            m_val = re.search(r'TOTAL\s+DESTA\s+NOTA\s*[\n\r\s]+([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_LOCALIZA:
            # "VALOR TOTAL" e o "R$ valor" nem sempre ficam colados: no OCR da
            # grade de vencimento/condição de pagamento, o rótulo e o valor saem
            # em linhas separadas por outros campos ("VALOR TOTAL\n15/04/2026 A
            # PRAZO\n\nR$ 3.168,70"), então o valor real caía no fallback 0.0.
            # Aceita qualquer coisa entre o rótulo e o próximo "R$" (limite curto
            # para não pular para um valor de linha seguinte não relacionado).
            # Sem \b depois de "TOTAL": no texto digital sem espaços de uma nota
            # real (YUI/ACBUL) o rótulo cola direto na data ("TOTAL04/05/2026"),
            # e letra->dígito não é fronteira de palavra para o regex.
            m_val = re.search(r'VALOR\s+TOTAL[\s\S]{0,80}?R\$\s*([\d.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_val.group(1)) if m_val else 0.0
            return Valores(
                valor_servicos=v, valor_liquido_nfse=v,
                base_calculo=0.0, valor_iss=0.0, aliquota=0.0
            )

        if self.layout == LAYOUT_TELECOM_COMUNICACAO:
            # "TOTAL A PAGAR: R$ 129,90" ou "TOTAL A PAGAR R$ 129,90"
            m_total = re.search(r'TOTAL\s+A\s+PAGAR\s*[:\s]*R?\$?\s*([\d\.,]+)', t, re.IGNORECASE)
            v = self._parse_valor(m_total.group(1)) if m_total else 0.0

            # BC ICMS e alíquota (campos presentes no documento, mapeados para base_calculo/aliquota)
            m_bc = re.search(r'BC\s+ICMS\s+([\d\.,]+)', t, re.IGNORECASE)
            bc = self._parse_valor(m_bc.group(1)) if m_bc else v

            m_aliq = re.search(r'AL[IÍ]Q\s*(?:\(%\))?\s*([\d\.,]+)', t, re.IGNORECASE)
            aliq = (self._parse_valor(m_aliq.group(1)) / 100.0) if m_aliq else 0.0

            # PIS/COFINS declarados na tabela de itens
            m_pis = re.search(r'PIS/COFINS\s+([\d\.,]+)', t, re.IGNORECASE)
            pis = self._parse_valor(m_pis.group(1)) if m_pis else 0.0

            return Valores(
                valor_servicos=v,
                valor_liquido_nfse=v,
                base_calculo=bc,
                aliquota=aliq,
                valor_iss=0.0,
                valor_pis=pis,
            )

        if self.layout == LAYOUT_CAMACARI_2:
            # Grade "Retenções (R$) x Totais (R$)" do Camaçari ESCANEADO. Além do
            # ruído de OCR nos rótulos ("Nalor"->Valor, "Basa"->Base), os valores
            # da Alíquota e do ISS saem TROCADOS de linha: a nota lê
            # "Aliquota (%) 35,75" e "Valor do ISS (R$) 6,5%", mas o real é
            # alíquota 6,5% e ISS 35,75 (6,5% × 550 = 35,75, confere com a face).
            # Regra imune à troca: a alíquota é o ÚNICO token seguido de "%"; o ISS
            # é derivado de base × alíquota. Só assume o layout se achar Valor dos
            # Serviços E a alíquota; senão devolve o controle ao parser CAMACARI
            # base (superset) via fall-through.
            def _num(mm):
                return self._parse_valor(mm.group(1)) if mm else 0.0
            m_val = re.search(r'[NV]a?lor\s+dos\s+Servi[cç]os\s*\(R\$\)\s*([\d\.,]+)', t, re.IGNORECASE)
            m_base = re.search(r'Bas[ae]\s+de\s+C[aá]lculo\s*\(=\)\s*([\d\.,]+)', t, re.IGNORECASE)
            m_liq = re.search(r'[NV]a?lor\s+L[ií]quido\s+da\s+Nota\s*\(=\)\s*([\d\.,]+)', t, re.IGNORECASE)
            m_ded = re.search(r'Dedu[çc][õo]es\s*\(?[-=]?\)?\s*([\d\.,]+)', t, re.IGNORECASE)
            m_pct = re.search(r'(\d{1,2}[,.]\d{1,2})\s*%', t)
            if m_val and m_pct:
                val_serv = _num(m_val)
                deducoes = _num(m_ded)
                base = _num(m_base) if m_base else max(val_serv - deducoes, 0.0)
                aliquota = self._parse_valor(m_pct.group(1)) / 100.0
                iss = round(base * aliquota, 2)
                liquido = _num(m_liq) if m_liq else val_serv
                return Valores(
                    valor_servicos=val_serv,
                    valor_deducoes=deducoes,
                    base_calculo=base,
                    aliquota=aliquota,
                    valor_iss=iss,
                    iss_retido=False,
                    valor_liquido_nfse=liquido,
                )

        if self.layout in (LAYOUT_CAMACARI, LAYOUT_CAMACARI_2):
            def _parse_valor_camacari(raw: str) -> float:
                # O OCR deste layout costuma ler corretamente rótulos como
                # "Aliquota (%)", mas perde toda a pontuação (separador de
                # milhar/decimal) especificamente nos valores da coluna
                # "Totais (R$)" (ex: "5.115,41" vira "511541"). Quando o valor
                # capturado é uma sequência de dígitos sem nenhum separador,
                # tratamos os 2 últimos dígitos como centavos.
                digits = raw.strip()
                if re.fullmatch(r'\d{3,}', digits):
                    return int(digits) / 100
                return self._parse_valor(digits)

            m_val = re.search(r'Valor\s+dos\s+Servi[cç]os\s*(?:\(R\$\)|\(=\))?\s*([\d\.,]+)', t, re.IGNORECASE)
            m_base = re.search(r'Base\s+de\s+C[aá]lculo\s*\(=\)\s*([\d\.,]+)', t, re.IGNORECASE)
            # "Al.?quota" tolera o "í" de "Alíquota" ser lido pelo OCR como "i" comum
            # ou até como o caractere de substituição Unicode "�" (falha total de
            # reconhecimento daquele glifo específico).
            # Exige separador decimal (vírgula) no valor capturado: em notas
            # fotografadas (ex.: Botelho/Camaçari) o OCR embaralha a grade
            # "Retenções x Totais" e faz esse rótulo colar num número de outra
            # linha/coluna sem vírgula (ex.: "27" em vez de "2,79") — uma
            # alíquota de ISS sem casas decimais é sempre sinal de captura
            # errada, nunca um valor real (diferente do Valor dos Serviços/ISS,
            # que legitimamente podem chegar sem nenhuma pontuação quando o
            # OCR só perde o separador de milhar/decimal — ver `_parse_valor_camacari`).
            m_aliq = re.search(r'Al.?quota\s*\(%\)\s*(\d{1,2},\d{1,2})', t, re.IGNORECASE)
            m_iss = re.search(r'Valor\s+(?:do\s+)?ISS\s*\(R\$\)\s*([\d\.,]+)', t, re.IGNORECASE)
            m_liq = re.search(r'Valor\s+L[ií]quido\s+da\s+Nota\s*\(=\)\s*([\d\.,]+)', t, re.IGNORECASE)
            m_ded = re.search(r'Dedu[cç][oõ]es\s*\(-\)\s*([\d\.,]+)', t, re.IGNORECASE)

            val_serv = _parse_valor_camacari(m_val.group(1)) if m_val else 0.0
            base = _parse_valor_camacari(m_base.group(1)) if m_base else 0.0
            aliq = (self._parse_valor(m_aliq.group(1)) / 100) if m_aliq else 0.0
            iss = _parse_valor_camacari(m_iss.group(1)) if m_iss else 0.0
            liquido = _parse_valor_camacari(m_liq.group(1)) if m_liq else val_serv
            deducoes = _parse_valor_camacari(m_ded.group(1)) if m_ded else 0.0
            # Base de cálculo = Valor dos Serviços - Deduções quando o rótulo
            # "Base de Cálculo" não foi capturado (mesma causa do m_aliq acima).
            if base == 0.0 and val_serv > 0.0:
                base = val_serv - deducoes
            # Alíquota derivada de ISS/Base quando o rótulo da alíquota falhou
            # mas o valor do ISS foi lido com confiança (formato de moeda).
            if aliq == 0.0 and iss > 0.0 and base > 0.0:
                aliq = iss / base
            pis, cofins, inss, ir, csll, outras = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

            # Fallback: em PDFs deste layout gerados digitalmente (não escaneados/OCR),
            # o pdfminer costuma extrair a tabela em dois blocos separados — primeiro
            # TODOS os rótulos das colunas "Retenções (R$)" e "Totais (R$)", e só
            # depois TODOS os valores numéricos correspondentes, na mesma ordem
            # relativa (efeito comum de extração de tabelas em grade). Nesse caso,
            # os regexes acima (que exigem o valor logo após o rótulo) não casam com
            # nada (exceto, por acaso, o último rótulo, que fica adjacente ao
            # primeiro valor do bloco seguinte — daí a checagem por val_serv == 0
            # em vez de confiar em "algum regex casou").
            if val_serv == 0.0 and re.search(r'Reten[çc][õo]es\s*\(R\$\)', t, re.IGNORECASE) and re.search(r'Totais\s*\(R\$\)', t, re.IGNORECASE):
                label_defs = [
                    ('pis', r'\bPIS\s*:?'),
                    ('cofins', r'\bCOFINS\s*:?'),
                    ('inss', r'\bINSS\s*:?'),
                    ('ir', r'\bIR\s*:?'),
                    ('csll', r'\bCSLL\s*:?'),
                    ('outras', r'\bOutras\s*:?'),
                    ('total_retencoes', r'Total\s+de\s+Reten[çc][õo]es\s*:?'),
                    ('val_serv', r'Valor\s+dos\s+Servi[cç]os\s*\(R\$\)'),
                    ('deducoes', r'Dedu[çc][oõ]es\s*\(-\)'),
                    ('base', r'Base\s+de\s+C[aá]lculo\s*\(=\)'),
                    ('aliq', r'Al.?quota\s*\(%\)'),
                    ('iss', r'Valor\s+(?:do\s+)?ISS\s*\(R\$\)'),
                    ('liquido', r'Valor\s+L[ií]quido\s+da\s+Nota\s*\(=\)'),
                ]
                matches = [(nome, re.search(pat, t, re.IGNORECASE)) for nome, pat in label_defs]
                encontrados = [(m.start(), nome) for nome, m in matches if m]
                encontrados.sort(key=lambda x: x[0])
                fim_labels = max((m.end() for _, m in matches if m), default=0)

                if encontrados and fim_labels:
                    trecho_valores = t[fim_labels:]
                    m_corte = re.search(r'Tipo\s+de\s+tributa[çc][aã]o', trecho_valores, re.IGNORECASE)
                    if m_corte:
                        trecho_valores = trecho_valores[:m_corte.start()]

                    numeros = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', trecho_valores)
                    if len(numeros) >= len(encontrados):
                        por_nome = dict(zip([nome for _, nome in encontrados], numeros))

                        def _v(nome):
                            raw = por_nome.get(nome)
                            return _parse_valor_camacari(raw) if raw else 0.0

                        val_serv = _v('val_serv')
                        deducoes = _v('deducoes')
                        base = _v('base')
                        aliq = _v('aliq') / 100
                        iss = _v('iss')
                        liquido = _v('liquido')
                        pis, cofins, inss, ir, csll, outras = (
                            _v('pis'), _v('cofins'), _v('inss'), _v('ir'), _v('csll'), _v('outras')
                        )

            return Valores(
                valor_servicos=val_serv, base_calculo=base, aliquota=aliq,
                valor_iss=iss, valor_liquido_nfse=liquido, valor_deducoes=deducoes,
                valor_pis=pis, valor_cofins=cofins, valor_inss=inss,
                valor_ir=ir, valor_csll=csll, outras_retencoes=outras,
            )

        val_serv, base, aliq, iss = 0.0, 0.0, 0.0, 0.0
        pis, cofins, inss, ir, csll, outras = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        _val_patterns = [
            # "Valor Serviço: R$ 27.796,65" (ex: layout Brasília/DF) — sem "do/dos"
            # antes de "Serviço" e com "R$" logo após os dois-pontos.
            r'Valor\s+Servi[cç]o\s*:\s*R?\$?\s*([\d\.,]+)',
            r'V[LlIi]\.\s+do\s+Servi[cç]o\s*[:\s\n]*R?\$?\s*([\d\.,]+)',
            r'VALOR\s+TOTAL\s+DA\s+NOTA\s*[=:]\s*R\$?\s*([\d\.,]+)',
            r'VALOR\s+TOTAL\s+DO\s+SERVIÇO\s*[:=]?\s*R\$?\s*([\d\.,]+)',
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

        # Prioriza um rótulo explícito de valor ("Valor (do) ISS" / "Total (do) ISS")
        # para não casar com "Alíquota ISS: 5,00%", que também contém a palavra
        # "ISS" mas antecede o rótulo de valor real no texto.
        m_iss = re.search(r'(?:Valor\s+(?:do\s+)?|Total\s+(?:do\s+)?)ISS(?:QN)?\s*(?:\(R\$\))?[=:R\$\s]*(?:.*?\n)?\s*([\d\.,]+)', t, re.IGNORECASE)
        if not m_iss:
            m_iss = re.search(r'ISS(?:QN)?\s*(?:\(R\$\))?[=:R\$\s]*(?:.*?\n)?\s*([\d\.,]+)', t, re.IGNORECASE)
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

        # São Paulo/SP digital: em algumas notas reais (AMIL/TEMIS, 2026-07-31)
        # a grade "Valor Total das Deduções / Desconto Incond. / Base de
        # Cálculo / Alíquota (%) / Valor ISS / Crédito p/ Abatimento do IPTU"
        # vem em DOIS blocos separados no pdfminer — todos os rótulos primeiro,
        # todos os valores depois, na mesma ordem relativa (mesmo efeito já
        # tratado em LAYOUT_CAMACARI_2). Os regexes acima (que exigem o valor
        # logo após o rótulo) não casam com nada útil, ou casam com o valor
        # ERRADO (ex.: "Valor ISS" casando com o "0,00" do rótulo seguinte,
        # "Crédito p/ Abatimento do IPTU"). Gateado pela presença de "Valor
        # Total das Deduções" — marca específica desta grade, ausente do mock
        # sintético mais simples que já cobre o caminho genérico.
        if self.layout == LAYOUT_SAO_PAULO and re.search(r'Valor\s+Total\s+das\s+Dedu[çc][õo]es', t, re.IGNORECASE):
            label_defs_sp = [
                ('deducoes', r'Valor\s+Total\s+das\s+Dedu[çc][õo]es'),
                ('desconto_incond', r'Desconto\s+Incond\.?'),
                ('base', r'Base\s+de\s+C[áa]lculo'),
                ('aliq', r'Al[íi]quota\s*\(%\)'),
                ('iss', r'Valor\s+ISS\b'),
            ]
            matches_sp = [(nome, re.search(pat, t, re.IGNORECASE)) for nome, pat in label_defs_sp]
            encontrados_sp = sorted(
                ((m.start(), nome) for nome, m in matches_sp if m), key=lambda x: x[0]
            )
            fim_labels_sp = max((m.end() for _, m in matches_sp if m), default=0)
            if encontrados_sp and fim_labels_sp:
                trecho_sp = t[fim_labels_sp:]
                m_corte_sp = re.search(r'Esta\s+NFS-e\s+foi\s+emitida', trecho_sp, re.IGNORECASE)
                if m_corte_sp:
                    trecho_sp = trecho_sp[:m_corte_sp.start()]
                numeros_sp = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', trecho_sp)
                if len(numeros_sp) >= len(encontrados_sp):
                    por_nome_sp = dict(zip([nome for _, nome in encontrados_sp], numeros_sp))
                    if 'base' in por_nome_sp:
                        base = self._parse_valor(por_nome_sp['base'])
                    if 'aliq' in por_nome_sp:
                        aliq = self._parse_valor(por_nome_sp['aliq']) / 100
                    if 'iss' in por_nome_sp:
                        iss = self._parse_valor(por_nome_sp['iss'])
                    if 'deducoes' in por_nome_sp:
                        val_deducoes = self._parse_valor(por_nome_sp['deducoes'])

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

    def _parse_data_extenso(self, data_str: str) -> Optional[datetime]:
        try:
            m = re.search(r'(\d{1,2})\s+de\s+([a-zA-Záéíóúãõç]+)\s+de\s+(\d{4})', data_str, re.IGNORECASE)
            if m:
                dia = int(m.group(1))
                mes_nome = m.group(2).lower()
                ano = int(m.group(3))
                mes = _MESES_PT.get(mes_nome)
                if mes:
                    return datetime(ano, mes, dia)
        except:
            pass
        return None

    @staticmethod
    def _parse_valor(valor_str: str) -> float:
        try: return float(valor_str.replace('.', '').replace(',', '.'))
        except: return 0.0

    # Termos esperados em qualquer NFS-e/DANFE, usados para pontuar a
    # qualidade do texto reconhecido em cada tentativa de rotação.
    _OCR_QUALITY_KEYWORDS = (
        "PREFEITURA", "MUNICIPAL", "MUNICIPIO", "MUNICÍPIO", "SECRETARIA",
        "NOTA", "FISCAL", "SERVIC", "SERVIÇ", "PRESTADOR", "TOMADOR",
        "CNPJ", "CPF", "VALOR", "CEP", "DISCRIMINA", "EMISSAO", "EMISSÃO",
    )

    @classmethod
    def _score_ocr_text(cls, text: str) -> int:
        """Pontua a qualidade de um texto OCR pela presença de termos fiscais
        esperados. Uma orientação errada (imagem de cabeça para baixo/rotacionada)
        produz texto embaralhado que praticamente nunca bate com essas palavras,
        enquanto a orientação correta reconhece várias delas — ver gotcha da
        rotação de OCR (nota Botelho/Camaçari, PDF originado de foto/JPG).
        Números em formato de moeda brasileira (ex.: "270,00") pesam mais,
        pois indicam que a tabela de valores foi reconhecida corretamente."""
        if not text:
            return 0
        upper = text.upper()
        score = sum(upper.count(kw) for kw in cls._OCR_QUALITY_KEYWORDS)
        score += 2 * len(re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', text))
        return score

    def _ocr_page(self, page_num: int) -> str:
        """Renderiza uma única página do PDF (0-indexed) como imagem e extrai o
        texto via Tesseract, testando as 4 rotações (0/90/180/270°) quando a
        leitura na orientação original sai com baixa qualidade — fotos/JPGs
        convertidos em PDF frequentemente chegam de cabeça para baixo ou de
        lado, e o OSD do Tesseract (image_to_osd) se mostrou pouco confiável
        para detectar isso nesses documentos."""
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

            doc = pymupdf.open(self.pdf_path)
            try:
                if page_num >= len(doc):
                    return ""
                page = doc.load_page(page_num)
                # Aumenta a resolução para melhorar a precisão do OCR. Subido de 2x
                # para 3x após validar contra uma nota real de Salvador/BA: em 2x o
                # CNPJ do tomador perdia a barra ("628/0001"→"62810001", quebrando o
                # regex de CNPJ e causando um bug grave de troca de CNPJ entre
                # entidades), o nome de município saía corrompido ("Feira"→"Fora") e
                # a grade de retenções/valor líquido não era reconhecida. Zoom 5x
                # recupera ainda mais campos, mas introduz uma regressão nova
                # (quebra a discriminação do serviço em dois fragmentos
                # desconectados) — 3x é o ponto de melhor custo-benefício validado.
                zoom = 3.0
                mat = pymupdf.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                img = Image.open(io.BytesIO(pix.tobytes("png")))
                # Requer que os dados do idioma português ('por') estejam instalados no Tesseract
                best_text = pytesseract.image_to_string(img, lang='por')
                best_score = self._score_ocr_text(best_text)
                best_angle = 0

                # Só vale a pena testar outras rotações se a leitura em 0°
                # não pareceu um documento fiscal de verdade.
                if best_score == 0:
                    for angle in (180, 90, 270):
                        rotated = img.rotate(-angle, expand=True)
                        candidate = pytesseract.image_to_string(rotated, lang='por')
                        score = self._score_ocr_text(candidate)
                        if score > best_score:
                            best_score = score
                            best_text = candidate
                            best_angle = angle
                        if best_score > 0:
                            break

                # Guarda o ângulo vencedor para recortes dedicados (ex.: caixa de
                # cabeçalho do SP2) renderizarem a região na mesma orientação.
                self._ocr_rotation = best_angle

                # Layout Salvador/BA tem uma caixa de cabeçalho densa e pequena
                # (Número da Nota / Data e Hora de Emissão / Código de Verificação)
                # que sai ilegível mesmo em zoom 3x/5x na página inteira — em
                # ambos os testes contra uma nota real (GABINO 4852) o valor do
                # código de verificação some ou aparece corrompido junto ao título
                # do documento. Um recorte dedicado dessa região (canto superior
                # direito) em zoom mais alto recupera o valor corretamente
                # ("AF7P-SGPS"), mesmo quando o rótulo "Código" continua truncado
                # pelo OCR. Prependemos ao texto principal para que os regexes
                # encontrem esta versão limpa antes de qualquer ocorrência
                # ambígua no restante do documento.
                if re.search(r'PREFEITURA\s+MUNICIPAL\s+DO\s+SALVADOR|Nota\s+Salvador', best_text, re.IGNORECASE):
                    header_text = self._ocr_header_box_salvador(page)
                    if header_text.strip():
                        best_text = f"{header_text}\n{best_text}"
                    # Recut do bloco do TOMADOR em zoom alto SÓ quando ele sai sem
                    # um CNPJ bem-formado no zoom 3 (scans de baixa qualidade
                    # corrompem CNPJ/razão do tomador — ex.: nota nº 46). Notas
                    # cujo tomador já sai limpo pulam o custo extra e não correm
                    # risco de regressão. O recorte limpo é prependado, então a
                    # extração genérica do tomador acha o CNPJ/razão corretos primeiro.
                    m_tom = re.search(r'TOMADOR\s+DE\s+SERVI[ÇC]OS(.*?)(?=DISCRIMINA|PRESTADOR|$)',
                                      best_text, re.IGNORECASE | re.DOTALL)
                    if m_tom and not re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', m_tom.group(1)):
                        tomador_text = self._ocr_tomador_salvador(page, best_angle)
                        if tomador_text.strip():
                            best_text = f"{tomador_text}\n{best_text}"

                # ARMAC (Fatura de Locação escaneada): a leitura padrão (3x, PSM
                # automático) embaralha a grade multi-item e perde a linha
                # "Valor total" e os blocos de entidade. Reprocessar a página
                # inteira em zoom 4x com PSM 6 (bloco único) recupera tudo de
                # forma limpa (validado contra a nota real 90109539) — trocamos o
                # texto inteiro, pois é estritamente melhor para esta página.
                if re.search(r'00\.?242\.?184', best_text) or (re.search(r'\bARMAC\b', best_text, re.IGNORECASE) and re.search(r'FATURA\s+DE\s+LOCA', best_text, re.IGNORECASE)):
                    armac_text = self._ocr_armac(page)
                    if armac_text.strip():
                        best_text = armac_text

                # Iaçu/BA (plataforma nfservico.com.br): a caixa do canto superior
                # direito (Número da nota / Data e hora de Emissão / Código de
                # Verificação) fica vazia na leitura de página inteira — é pequena
                # e divide espaço com um QR Code. Um recorte dedicado em zoom alto
                # recupera esses três campos; prependemos ao texto principal.
                if re.search(r'PREFEITURA\s+MUNICIPAL\s+DE\s+IA.{0,2}U', best_text, re.IGNORECASE) or re.search(r'nfservico\.com\.br', best_text, re.IGNORECASE):
                    header_iacu = self._ocr_header_box_iacu(page)
                    if header_iacu.strip():
                        best_text = f"{header_iacu}\n{best_text}"

                # São Paulo/SP escaneado (JPG/foto -> OCR): a caixa "Número da
                # Nota" do canto superior direito sai ilegível na página inteira
                # (o número "00331020" chega a virar "5"). Recorte dedicado na
                # mesma orientação já corrigida (best_angle) recupera o número.
                if re.search(r'PREFEITURA\s+DO\s+MUNIC[IÍ]PIO\s+DE\s+S[AÃ]O\s+PAULO', best_text, re.IGNORECASE):
                    header_sp = self._ocr_header_box_sao_paulo(page, best_angle)
                    if header_sp.strip():
                        best_text = f"{header_sp}\n{best_text}"

                # Cuiabá/MT (ISSNet) escaneado: a grade "Detalhamento dos
                # Tributos" (Vl. Total dos Serviços | ... | Total do ISSQN |
                # ISSQN Retido | ...) às vezes sai truncada no zoom 3 padrão —
                # seja quebrando a linha de valores no meio (ex.: "R$443,80 |
                # R$000" numa linha, "R$ 0,00" isolado bem abaixo — pág. 14 do
                # MTI 03-2026), seja perdendo uma coluna inteira sem quebrar a
                # linha (ex.: "R$ 22.709,56 R$ 0,00 R$ 0,00 R$ 454,19 | Não R$
                # 0,00" — só 5 tokens numa linha só, pág. 3 do PDF "ANALISE" —
                # a Base de Cálculo duplicada simplesmente não sai). Uma linha
                # completa desta grade sempre tem 6 tokens "R$" (serviços,
                # desconto incond., deduções, base, ISS, desconto cond.) —
                # confirmado nas notas já corretas (nº 134, pág. 14 após
                # recut). Um recut em zoom 5 + PSM 6 (página inteira) recompõe
                # a linha inteira de forma consistente (validado nos zooms
                # 4/5/6/8). Só reprocessa quando a linha sai com MENOS de 6
                # tokens "R$" — notas já limpas no zoom 3 pulam o custo extra
                # e não correm risco de regressão.
                if re.search(r'Prefeitura\s+Municipal\s+de\s+Cuiab[áa]', best_text, re.IGNORECASE):
                    m_row_chk = re.search(
                        r'V[il]\.?\s*Total\s+dos\s+Servi[çc]os[^\n:]*\n\s*(R\$[^\n]*)',
                        best_text, re.IGNORECASE)
                    row_chk = m_row_chk.group(1) if m_row_chk else ''
                    if len(re.findall(r'R\$', row_chk)) < 6:
                        valores_cuiaba = self._ocr_valores_cuiaba(page)
                        if valores_cuiaba.strip():
                            # Remove a própria leitura de "Número da Nota Fiscal"
                            # deste recut antes de prependar: é um re-OCR de
                            # página inteira em outro zoom, feito para consertar
                            # a GRADE DE VALORES — sua leitura do número (que
                            # ninguém validou) pode ser DIFERENTE e pior que a do
                            # zoom 3 (ex.: nota real GMS FLATS pág. 17: zoom 3 lê
                            # "9699", este recut lê outra coisa; nenhum dos dois
                            # bate com o real "5639"). O número tem seu próprio
                            # recorte dedicado e validado (`_ocr_numero_box_cuiaba`,
                            # logo abaixo) — não deixamos este recut "vazar" um
                            # 2º palpite não confirmado para a extração de número.
                            valores_cuiaba = re.sub(
                                r'N[uú]mero\s+da\s+Nota\s+Fiscal\s*:?\s*\d+\s*',
                                '', valores_cuiaba, flags=re.IGNORECASE
                            )
                            best_text = f"{valores_cuiaba}\n{best_text}"

                    # Número: SEMPRE faz o recorte dedicado da caixa "Número da
                    # Nota Fiscal" (canto superior direito, ao lado do logo/QR)
                    # em 3 zooms (6/8/10) x 2 PSM, com whitelist de dígitos, e
                    # PREPENDA quando há consenso (≥2 dos 6 concordam) — mesmo
                    # quando o rótulo limpo já "casou" na leitura padrão (zoom
                    # 3). Isso não é redundante: a leitura de página inteira do
                    # zoom 3 pode ler o dígito ERRADO com total confiança, sem
                    # nenhum sinal de ambiguidade (ex.: nota real GMS FLATS
                    # pág. 17 — zoom 3 lê "9699" de forma limpa, mas o número
                    # real, confirmado pela imagem, é "5639"). Como o recorte
                    # dedicado já exige consenso entre zooms/PSM antes de
                    # aceitar um valor, ele é MAIS confiável que a leitura de
                    # página inteira para este campo especificamente — por
                    # isso tem prioridade (é prependado, e a extração usa a 1ª
                    # ocorrência). Sem consenso no recorte (ex.: mesma nota GMS
                    # FLATS, que não tem número recuperável em nenhuma
                    # combinação testada), `_ocr_numero_box_cuiaba` devolve
                    # vazio e a leitura padrão (ou o fallback honesto) segue
                    # valendo — nunca piora o que já funcionava.
                    numero_box = self._ocr_numero_box_cuiaba(page)
                    if numero_box.strip():
                        best_text = f"{numero_box}\n{best_text}"

                # Camaçari/BA escaneado (foto/JPG -> OCR): a leitura padrão
                # (zoom 3) desta família de fotos de baixa qualidade descarta a
                # metade inferior inteira da nota (grade "Retenções x Totais",
                # tipo de tributação e item de serviço). Reprocessar a página em
                # zoom 4 + PSM 6 recupera todo o corpo (grade/serviço/entidades),
                # e um recorte dedicado do canto superior direito recupera o
                # número e a data de emissão (a caixa some no zoom 3). Ambos na
                # mesma orientação já corrigida (best_angle). Só dispara para
                # notas de Camaçari que passaram por OCR — o digital nunca chega
                # aqui (tem texto embutido). Validado contra a nota real nº 1050
                # (PEREIRA SANTOS -> AMANE AGUIAR, JPG rotacionado 180°).
                if re.search(r'PREFEITURA\s+MUNICIPAL\s+DE\s+CAMA[CÇ]ARI', best_text, re.IGNORECASE) or re.search(r'Data\s+da\s+presta[cç][aã]o\s+do\s+servi[cç]o', best_text, re.IGNORECASE):
                    body_cam = self._ocr_camacari_scan(page, best_angle)
                    if body_cam.strip():
                        best_text = body_cam
                    header_cam = self._ocr_header_box_camacari(page, best_angle)
                    if header_cam.strip():
                        best_text = f"{header_cam}\n{best_text}"

                # F&F Comércio (fatura de locação de CFTV): achado real — para
                # ESTA nota específica, o MESMO pixmap (zoom 3x) produz um
                # texto muito mais completo (1016 vs 558 caracteres — recupera
                # o rótulo "RAZÃO SOCIAL", o bloco "ENDEREÇO"/"CNPJ/CPF" do
                # tomador e a tabela de itens inteira) quando passado ao
                # Tesseract por CAMINHO DE ARQUIVO em vez de objeto PIL em
                # memória (provável diferença de metadado de DPI mudando o
                # pré-processamento interno). Não mexemos no `_ocr_page`
                # global — os outros ~35 layouts já validados usam o caminho
                # por objeto sem problema — só refazemos a leitura quando o
                # CNPJ da F&F já foi reconhecido no texto (mesmo degradado), e
                # só trocamos se o resultado for estritamente mais completo.
                if re.search(r'13\.?398\.?812[/.]?0001-?89', best_text, re.IGNORECASE):
                    recut_ff = self._ocr_recut_ff_locacao(page)
                    if len(recut_ff.strip()) > len(best_text.strip()):
                        best_text = recut_ff

                return best_text
            finally:
                doc.close()
        except ImportError:
            print("[AVISO] Bibliotecas de OCR (pymupdf, pytesseract, pillow) não instaladas.")
            return ""
        except Exception as e:
            print(f"[AVISO] Falha ao executar OCR na página {page_num + 1}: {e}")
            return ""

    @staticmethod
    def _ocr_armac(page) -> str:
        """Reprocessa a página inteira da Fatura de Locação da ARMAC em zoom 4x
        com PSM 6 (assume um único bloco uniforme de texto). A leitura padrão
        (3x, PSM automático) trata a grade multi-item de equipamentos como
        colunas soltas e embaralha os valores, além de perder a linha
        "Valor total" e colar os blocos "Dados do Locador/Tomador". Validado
        contra a nota real 90109539: recupera "Valor total: 103.640,00", as
        datas, os dois CNPJs e os endereços de forma consistente."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(4.0, 4.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            return pytesseract.image_to_string(img, lang='por', config='--psm 6')
        except Exception:
            return ""

    @staticmethod
    def _ocr_recut_ff_locacao(page) -> str:
        """Re-OCR da página inteira (mesmo zoom 3x do `_ocr_page` padrão), mas
        entregando a imagem ao Tesseract por CAMINHO DE ARQUIVO em vez de
        objeto PIL em memória. Achado real (nota F&F Comércio): o MESMO
        pixmap rende 558 caracteres pelo caminho normal (objeto em memória) e
        1016 caracteres por este caminho (arquivo) — a diferença recupera
        campos inteiros que a leitura padrão simplesmente omite (rótulo
        "RAZÃO SOCIAL", bloco "ENDEREÇO"/"CNPJ/CPF" do tomador, a tabela de
        itens). Isolado como recut de layout específico (não altera o
        `_ocr_page` para os demais ~35 layouts já validados)."""
        try:
            import pymupdf
            import pytesseract
            import tempfile
            import os

            pix = page.get_pixmap(matrix=pymupdf.Matrix(3.0, 3.0))
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name
                pix.save(tmp_path)
                return pytesseract.image_to_string(tmp_path, lang='por')
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception:
            return ""

    @staticmethod
    def _ocr_header_box_salvador(page) -> str:
        """Recorta e reprocessa em zoom alto (4.5x) o canto superior direito da
        nota Salvador/BA (caixa "Número da Nota" / "Data e Hora de Emissão" /
        "Código de Verificação"), usando PSM 6 (bloco único de texto) — a região
        inteira da página não recupera esses campos de forma confiável em
        nenhum zoom testado. Validado contra nota real: recupera "00004852" e
        "AF7P-SGPS" mesmo quando o rótulo "Código" continua truncado."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(4.5, 4.5))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            w, h = img.size
            crop = img.crop((int(w * 0.60), 0, w, int(h * 0.11)))
            return pytesseract.image_to_string(crop, lang='por', config='--psm 6')
        except Exception:
            return ""

    @staticmethod
    def _ocr_tomador_salvador(page, angle: int = 0) -> str:
        """Re-OCR da página inteira do Salvador/BA em zoom ALTO (5x), devolvendo
        SÓ o recorte do bloco do TOMADOR ("TOMADOR DE SERVIÇOS" até
        "DISCRIMINAÇÃO"). Em scans de baixa qualidade o zoom 3 padrão corrompe o
        CNPJ e a razão do tomador (ex.: "03.051.741/0001-90" vira
        "05051.74110001.00"; "SÃO PEDRO" vira "es EO"), fazendo o CNPJ cair no
        sentinela de "não identificado". O zoom 5 recupera ambos limpos —
        validado contra a nota real nº 46 (BALUARTE -> SÃO PEDRO CONSTRUTORA).
        Devolve só o recorte para PREPENDER ao texto base (não troca a página
        inteira: em zoom 5 a discriminação do serviço se fragmenta). Aplica a
        mesma rotação (`angle`) já detectada pelo _ocr_page."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(5.0, 5.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            if angle:
                img = img.rotate(-angle, expand=True)
            txt = pytesseract.image_to_string(img, lang='por')
            m = re.search(r'TOMADOR\s+DE\s+SERVI[ÇC]OS.*?(?=DISCRIMINA|$)', txt, re.IGNORECASE | re.DOTALL)
            return m.group(0) if m else ""
        except Exception:
            return ""

    @staticmethod
    def _ocr_header_box_iacu(page) -> str:
        """Recorta e reprocessa em zoom alto (5x) o canto superior direito da
        NFS-e de Iaçu/BA (plataforma nfservico.com.br): a caixa "Número da nota"
        / "Data e hora de Emissão" / "Código de Verificação". Esses três campos
        saem vazios na leitura de página inteira (a caixa é pequena e tem um QR
        Code logo abaixo). Usa PSM 6 (bloco único). Validado contra a nota real
        N'S ASSUNÇÃO nº 2: recupera "2", "10/07/2026 16:37:22" e "c5cae3fd79"."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(5.0, 5.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            w, h = img.size
            crop = img.crop((int(w * 0.65), int(h * 0.08), w, int(h * 0.26)))
            return pytesseract.image_to_string(crop, lang='por', config='--psm 6')
        except Exception:
            return ""

    @staticmethod
    def _ocr_header_box_sao_paulo(page, angle: int = 0) -> str:
        """Recorta e reprocessa em zoom alto (6x) a caixa "Número da Nota" do
        canto superior direito da NFS-e de São Paulo ESCANEADA (JPG/foto). O
        número (ex.: "00331020", dígitos em negrito) sai ilegível na leitura de
        página inteira — chega a virar "5". Aplica a MESMA rotação (`angle`) que
        o _ocr_page usou para deixar a página na vertical e lê a célula do número
        com PSM 6 + whitelist de dígitos. Retorna uma linha sintética limpa
        ("Número da Nota\\n<n>") para a branch de número casar sem depender do
        resto da caixa. Validado contra a nota real (BOM NEGOCIO nº 00331020,
        JPG rotacionado 180°)."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(6.0, 6.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            if angle:
                img = img.rotate(-angle, expand=True)
            w, h = img.size
            crop = img.crop((int(w * 0.67), int(h * 0.098), int(w * 0.98), int(h * 0.126))).convert('L')
            num = pytesseract.image_to_string(
                crop, lang='por',
                config='--psm 6 -c tessedit_char_whitelist=0123456789'
            )
            num = re.sub(r'\D', '', num)
            return f"Número da Nota\n{num}\n" if num else ""
        except Exception:
            return ""

    @staticmethod
    def _ocr_numero_box_cuiaba(page) -> str:
        """Recorta e reprocessa em zoom alto a caixa "Número da Nota Fiscal" do
        canto superior direito da NFS-e de Cuiabá/MT (ISSNet) escaneada — só o
        dígito (exclui o logo/QR "NOTA CUIABANA" ao lado, que confunde o OCR e
        faz o dígito variar entre zooms, ex.: "16" virando "18"). Whitelist de
        dígitos, mas nem PSM 6 (bloco) nem PSM 7 (linha única) é confiável
        sozinho — o recorte tem DUAS linhas (rótulo + número), e qual PSM lida
        melhor com isso varia por nota: na nota pág. 14 (MTI) só o PSM 7 lê
        "16" (PSM 6 vem vazio); na nota nº 10 (DR3 Terceirização, PDF
        "ANALISE") só o PSM 6 lê "10" de forma estável (PSM 7 varia entre
        "10"/"1"/vazio conforme o zoom). Por isso vota com AMBOS os PSM em 3
        zooms (6/8/10 — 6 tentativas) e só aceita quando ao menos 2 concordam
        no mesmo valor — sem consenso, devolve vazio em vez de arriscar um
        dígito errado (ex.: nota GMS FLATS pág. 17, sem número recuperável em
        nenhuma combinação testada). Faixa vertical do recorte calibrada
        (0.065-0.098 da altura da página) contra 3 notas reais com números de
        tamanhos diferentes (205, 16, 10) — uma faixa mais estreita (usada
        antes) cortava a linha do dígito ao meio em notas cujo número de 3
        dígitos (ex.: "205") ocupa mais espaço vertical, devolvendo vazio."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io
            from collections import Counter

            votos = []
            for zoom in (6.0, 8.0, 10.0):
                pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                w, h = img.size
                crop = img.crop((int(w * 0.80), int(h * 0.065), int(w * 0.98), int(h * 0.098)))
                for psm in (6, 7):
                    texto = pytesseract.image_to_string(
                        crop, lang='por', config=f'--psm {psm} -c tessedit_char_whitelist=0123456789'
                    ).strip()
                    if texto:
                        votos.append(texto)
            if not votos:
                return ""
            numero, contagem = Counter(votos).most_common(1)[0]
            if contagem < 2:
                return ""
            return f"Número da Nota Fiscal\n{numero}\n"
        except Exception:
            return ""

    @staticmethod
    def _ocr_valores_cuiaba(page) -> str:
        """Reprocessa a página inteira da NFS-e de Cuiabá/MT (ISSNet) escaneada
        em zoom alto (5x) com PSM 6 (bloco único). No zoom 3 padrão a grade
        "Detalhamento dos Tributos" às vezes quebra a linha de valores no meio
        (o "Total do ISSQN" e parte da "Base de Cálculo" somem para uma linha
        separada, fora do alcance do regex de captura por linha). Zoom 5 + PSM
        6 recompõe a linha inteira num único bloco, junto com a alíquota
        (item da LC116) — validado contra a nota real pág. 14: zoom 6 também
        recompõe a grade de valores, mas nesse zoom específico a alíquota
        "2,00" cai do texto; zoom 5 preserva ambos."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(5.0, 5.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            return pytesseract.image_to_string(img, lang='por', config='--psm 6')
        except Exception:
            return ""

    @staticmethod
    def _ocr_camacari_scan(page, angle: int = 0) -> str:
        """Reprocessa a página inteira da NFS-e de Camaçari/BA ESCANEADA em zoom
        4x com PSM 6 (bloco único), na mesma orientação já corrigida (`angle`).
        A leitura padrão (zoom 3, PSM automático) desta família de fotos de
        baixa qualidade descarta a metade inferior da nota — a grade
        "Retenções (R$) x Totais (R$)", o "Tipo de tributação" e o item de
        serviço nunca aparecem. Zoom 4 + PSM 6 recupera o corpo inteiro de forma
        consistente (validado contra a nota real nº 1050): grade de totais,
        "Serviço: 000713 - ...", entidades e "Data da prestação do serviço"."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(4.0, 4.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            if angle:
                img = img.rotate(-angle, expand=True)
            return pytesseract.image_to_string(img, lang='por', config='--psm 6')
        except Exception:
            return ""

    @staticmethod
    def _ocr_header_box_camacari(page, angle: int = 0) -> str:
        """Recorta e reprocessa em zoom alto (6x) a caixa do canto superior
        direito da NFS-e de Camaçari/BA ESCANEADA ("Número da Nota" / "Data de
        Emissão" / "Código de autenticidade"), na mesma orientação já corrigida
        (`angle`), com PSM 6. Na leitura de página inteira essa caixa some. O
        recorte recupera o número (ex.: "1050") e a data/hora de emissão; o
        valor do código de autenticidade é impresso em fonte muito fraca e
        costuma sair ilegível mesmo aqui (fica então sinalizado em `avisos`).
        Validado contra a nota real nº 1050."""
        try:
            import pymupdf
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(matrix=pymupdf.Matrix(6.0, 6.0))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            if angle:
                img = img.rotate(-angle, expand=True)
            w, h = img.size
            crop = img.crop((int(w * 0.72), int(h * 0.045), w, int(h * 0.16)))
            return pytesseract.image_to_string(crop, lang='por', config='--psm 6')
        except Exception:
            return ""

    def _extract_via_ocr(self) -> str:
        """Tenta extrair o texto de TODAS as páginas do PDF renderizando-as como imagens e passando pelo Tesseract."""
        try:
            import pymupdf  # PyMuPDF
            doc = pymupdf.open(self.pdf_path)
            n_pages = len(doc)
            doc.close()
        except ImportError:
            print("[AVISO] Bibliotecas de OCR (pymupdf, pytesseract, pillow) não instaladas.")
            return ""
        except Exception as e:
            print(f"[AVISO] Falha ao abrir PDF para OCR: {e}")
            return ""

        print(f"[*] PDF '{self.pdf_path}' sem texto detectado. Iniciando extração via OCR (Tesseract)...")
        return "\n\x0c\n".join(self._ocr_page(i) for i in range(n_pages))

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
        elif re.search(
                r'OPTANTE\s+(?:PELO|DO)\s+SIMPLES\s+NACIONAL|EPP\s+OPTANTE|'
                r'perante\s+o\s+Simples\s+Nacional[\s\S]{0,40}?OPTANTE',
                self.raw_text, re.IGNORECASE):
            # "OPTANTE" e "SIMPLES NACIONAL" costumam ficar separados por "PELO"
            # (ex.: Campinas em OCR/imagem, ou o texto corrido "Documento emitido
            # por ME ou EPP optante pelo simples nacional" do layout PASSWORD/
            # eNotas) ou em linhas distintas de grade (PDF digital), fugindo do
            # padrão adjacente do elif anterior. Deixamos de restringir a
            # LAYOUT_CAMPINAS pois a frase em si já é específica o suficiente.
            optante_simples = True
            regime_especial = "6" # ME/EPP
        elif re.search(r'Simples\s+Nac(?:ional)?\s*/\s*MEI\s*/\s*Outros\s*:\s*Simples\s+Nacional', self.raw_text, re.IGNORECASE):
            # Layout FUTURIZE (Rosário da Limeira/MG): campo "Simples Nac/MEI/Outros:
            # Simples Nacional". O campo "Reg. Especial Tributação:" vem vazio nesta
            # nota, então marcamos apenas o optante (regime especial fica ausente).
            optante_simples = True

        incentivador = False
        if re.search(r'Incentivador\s+Cultural\s*[:\s\n]*Sim', self.raw_text, re.IGNORECASE):
            incentivador = True

        # Avisos de baixa confiança: sinaliza quando um campo caiu em valor de
        # fallback (número zerado, CNPJ zerado, data de hoje etc.) em vez de
        # mascarar silenciosamente o problema — foi assim que os bugs de
        # Camaçari/telecom desta sessão passaram despercebidos até revisão manual.
        avisos: List[str] = []
        if numero == '00000000':
            avisos.append("Número da nota não encontrado")
        if codigo_verificacao in ('XXXX-XXXX',):
            avisos.append("Código de verificação/autenticidade não encontrado")
        if self._data_emissao_fallback:
            avisos.append("Data de emissão não encontrada (usando a data atual como fallback)")
        # Alguns extratores de entidade usam '00000000000100' como sentinela de
        # "CNPJ não encontrado" (em vez de todo-zeros) — comparamos por prefixo
        # de 11 zeros para cobrir ambos os casos (mesmo critério da trava
        # antilixo em parse_multiple).
        if prestador and (prestador.cnpj_cpf.startswith('00000000000') or prestador.cnpj_cpf == ''):
            avisos.append("Dados do prestador não identificados")
        if tomador and (tomador.cnpj_cpf.startswith('00000000000') or tomador.cnpj_cpf == '' or tomador.razao_social == 'Tomador Não Identificado'):
            avisos.append("Dados do tomador não identificados")
        if valores.valor_servicos == 0.0:
            avisos.append("Valor dos serviços extraído como zero")

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
            incentivador_cultural=incentivador,
            avisos=avisos
        )

    def parse_multiple(self) -> List[Nfse]:
        """Extrai múltiplas notas do mesmo PDF, fatiando blocos de texto por heurística de início de nota."""
        def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p

        def _numero_heuristico_bloco(text: str) -> Optional[str]:
            """Extrai um "número da nota" aproximado de um BLOCO de texto, usado
            só para decidir se um trecho é uma nota nova ou continuação da
            anterior (não é o número final do XML — esse vem de `_extrair_numero`
            por layout). O padrão genérico antigo (Número/Nº seguido do 1º dígito) pegava
            o PRIMEIRO "Número" do texto, que muitas vezes é o número do
            ENDEREÇO do tomador ("Endereço : Avenida Praia de Pajussara Número:
            554"), não o da nota. Como o mesmo tomador (endereço fixo) se repete
            em várias notas de um PDF consolidado, isso fazia páginas de notas
            DIFERENTES compartilharem o mesmo "número" aparente e serem tratadas
            como continuação uma da outra — a nota seguinte nunca vira um XML
            próprio, fica silenciosamente engolida na anterior (achado real:
            PDF "NFS PRESTADORES ANALISE...", pág. 3, nota nº 10 sumia assim).
            Tenta primeiro rótulos específicos de "número da nota"; só cai no
            genérico como último recurso, e mesmo assim pula ocorrências cuja
            linha contém "Endereço" (a armadilha conhecida)."""
            especificos = [
                r'N[uú]mero\s+da\s+Nota\s+Fiscal\s*:?\s*(\d+)',
                r'N[ºo]\.?\s*da\s+Nota\s+Fiscal\s*:?\s*(\d+)',
                r'N[uú]mero\s+da\s+Nota\s*:?\s*(\d+)',
                r'N[ºo]\.?\s*da\s+Nota\s*:?\s*(\d+)',
            ]
            for p in especificos:
                m = re.search(p, text, re.IGNORECASE)
                if m:
                    return m.group(1)
            for m in re.finditer(r'(?:N[uú]mero|N[ºo])\.?\s*:?.*?(\d+)', text, re.IGNORECASE):
                inicio_linha = text.rfind('\n', 0, m.start()) + 1
                linha_ate_match = text[inicio_linha: m.start()]
                if re.search(r'Endere[çc]o', linha_ate_match, re.IGNORECASE):
                    continue
                return m.group(1)
            return None
        
        full_text = extract_text(self.pdf_path)
        
        # Fallback para OCR: Se o texto for muito curto ou não contiver palavras-chave essenciais (indica PDF de imagem)
        keywords = ["PREFEITURA", "MUNICIPIO", "MUNICÍPIO", "CNPJ", "NOTA", "NFS-e", "PRESTADOR", "TOMADOR"]
        has_keywords = any(re.search(relax(k), full_text, re.IGNORECASE) for k in keywords)
        
        if len(full_text.strip()) < 200 or not has_keywords:
            full_text = self._extract_via_ocr()
            self.from_ocr = True

        print(f"[*] Texto extraído ({len(full_text)} caracteres). Iniciando reconhecimento de padrões...")

        pages = full_text.split('\x0c')

        # Fallback de OCR por página: em PDFs mistos (algumas páginas com texto
        # extraível diretamente, outras sendo imagem/scan), o texto do documento
        # inteiro já "parece" válido o suficiente para pular o OCR global acima,
        # deixando as páginas escaneadas sem nenhum texto e, portanto, ignoradas
        # mais adiante. Aqui tentamos OCR pontual apenas nas páginas que renderizaram
        # pouco ou nenhum texto, sem reprocessar o documento inteiro.
        OCR_MIN_CHARS = 50
        try:
            import pymupdf  # PyMuPDF
            doc = pymupdf.open(self.pdf_path)
            n_pages_real = len(doc)
            doc.close()
        except Exception:
            n_pages_real = len(pages)

        if n_pages_real > len(pages):
            pages.extend([''] * (n_pages_real - len(pages)))

        for idx in range(min(n_pages_real, len(pages))):
            if len(pages[idx].strip()) < OCR_MIN_CHARS:
                ocr_text = self._ocr_page(idx)
                if len(ocr_text.strip()) >= OCR_MIN_CHARS:
                    print(f"[*] Página {idx + 1} sem texto extraível — usando OCR.")
                    pages[idx] = ocr_text
                    self.from_ocr = True

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

            # Localiza: a fatura (pág. com "FATURA / DUPLICATA Nº:") normalmente
            # vem seguida de um boleto/Pix que repete "LOCALIZA RENT A CAR S/A"
            # só como nome do beneficiário do pagamento — não é uma fatura nova.
            # Sem este caso, a heurística genérica de número diverge entre as
            # duas páginas (a do boleto não tem "Nº:", então pega um dígito
            # solto de outro campo, ex. uma data) e a mesma fatura vira 2 XMLs.
            if is_localiza and re.search(r'LOCALIZA RENT A CAR S/A', text, re.IGNORECASE) \
                    and not re.search(r'FATURA\s*/\s*DUPLICATA\s*N[ºo]', text, re.IGNORECASE):
                return False

            patterns = [
                relax("PREFEITURA"), relax("MUNICIPIO"), relax("MUNICÍPIO"), relax("NOTA CARIOCA"),
                relax("NFS-e"), relax("Nota Fiscal de Serviços"), relax("Nº da Nota Fiscal"),
                relax("DANFSe"), relax("PRESTADOR DE SERVIÇO"), relax("EMITENTE"),
                relax("DADOS DO PRESTADOR"), relax("Chave de Acesso"),
                relax("LOCALIZA RENT A CAR"), relax("FATURA / DUPLICATA"),
                relax("MUNICÍPIO DE SÃO PAULO"), relax("Prefeitura de Joinville"),
                relax("MUNICIPAL DE FORTALEZA"), relax("CONTRIBUIÇÃO SOLIDÁRIA"),
                relax("CPE BAHIA"), relax("cpe tecnologia"), relax("FATURA DE LOCAÇÃO"),
                relax("GUINCHO CIDADE"), relax("B.F. SERVICOS AMBIENTAIS"),
                relax("B.F. SERVIÇOS AMBIENTAIS"), relax("LMR ENGENHARIA"),
                relax("LTR ENGENHARIA"), relax("03.292.008"), relax("GERACAO E ENERGIA"),
                relax("LOCONTAINERS"), relax("VIDAL LOCACAO"), relax("NOTA DE COBRANÇA"),
                relax("NOTA FISCAL DE FATURA DE SERVICO DE COMUNICACAO"),
                relax("NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO"),
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
                num_prox = _numero_heuristico_bloco(text)
                if num_prox and num_prox == current_group_num:
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
            block_num = _numero_heuristico_bloco(block_text)

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
            # Propaga a origem (OCR vs texto embutido) para a detecção de layout
            # do bloco distinguir SP escaneado (LAYOUT_SAO_PAULO_2) do SP digital.
            sub_ext.from_ocr = self.from_ocr

            try:
                nfse = sub_ext.parse()
                if not nfse: continue
                
                # Trava contra Lixo Residual (Páginas processadas que não são notas).
                # Fotos/JPGs de baixa qualidade (ex.: nota Botelho/Camaçari) podem
                # perder número e CNPJ no OCR mas ainda ter nomes de prestador/tomador
                # legíveis — nesse caso é uma nota real e degradada, não lixo, então
                # só descartamos quando NENHUM nome de entidade foi reconhecido.
                if nfse.numero == '00000000' and nfse.prestador.cnpj_cpf.startswith('00000000000'):
                    placeholders_razao = {
                        'Não Identificado', 'Prestador Não Identificado',
                        'Tomador Não Identificado', 'Cliente Não Identificado',
                    }
                    tem_nome_prestador = nfse.prestador.razao_social not in placeholders_razao and len(nfse.prestador.razao_social.strip()) > 5
                    tem_nome_tomador = nfse.tomador and nfse.tomador.razao_social not in placeholders_razao and len(nfse.tomador.razao_social.strip()) > 5
                    if not (tem_nome_prestador or tem_nome_tomador):
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
