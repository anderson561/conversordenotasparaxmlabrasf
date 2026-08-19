"""
Módulo de resolução e validação de códigos IBGE municipais.

Utiliza uma lógica de "Cascata de Validação":
  1. Tenta extrair o código IBGE diretamente do texto do PDF
  2. Valida se o código encontrado é compatível com a UF detectada
  3. Aplica fallback dinâmico por UF caso nenhum código válido seja encontrado
"""

import re

class IBGEResolver:
    """
    Extrai e valida códigos IBGE de texto bruto de NFS-e.

    Previne erros de cross-check entre UF e código municipal
    (ex: código de Alagoas "27..." em nota da Bahia "BA").
    """

    # Mapeamento oficial dos prefixos IBGE por Estado
    UF_PREFIXES = {
        "AC": "12", "AL": "27", "AM": "13", "AP": "16", "BA": "29",
        "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
        "MG": "31", "MS": "50", "MT": "51", "PA": "15", "PB": "25",
        "PE": "26", "PI": "22", "PR": "41", "RJ": "33", "RN": "24",
        "RO": "11", "RR": "14", "RS": "43", "SC": "42", "SE": "28",
        "SP": "35", "TO": "17"
    }
    # Códigos IBGE válidos (capitais) usados como fallback seguro por UF.
    DEFAULT_CODES_BY_UF = {
        "AC": "1200401", "AL": "2704302", "AM": "1302603", "AP": "1600303",
        "BA": "2927408", "CE": "2304400", "DF": "5300108", "ES": "3205309",
        "GO": "5208707", "MA": "2111300", "MG": "3106200", "MS": "5002704",
        "MT": "5103403", "PA": "1501402", "PB": "2507507", "PE": "2611606",
        "PI": "2211001", "PR": "4106902", "RJ": "3304557", "RN": "2408102",
        "RO": "1100205", "RR": "1400100", "RS": "4314902", "SC": "4205407",
        "SE": "2800308", "SP": "3550308", "TO": "1721000",
    }

    KNOWN_CITIES = {
        "CAMACARI": "2905701", "CAMAÇARI": "2905701",
        "SIMOES FILHO": "2929206", "SIMÕES FILHO": "2929206",
        "LAURO DE FREITAS": "2919207",
        "FEIRA DE SANTANA": "2910800",
        "BARREIRAS": "2903201",
        "OSASCO": "3534401",
        "CUIABA": "5103403", "CUIABÁ": "5103403",
        "CAMPINA GRANDE": "2504009",
        "CAMPINAS": "3509502",
        "BRASILIA": "5300108", "BRASÍLIA": "5300108",
        "SALVADOR": "2927408",
        "SAO PAULO": "3550308", "SÃO PAULO": "3550308",
        "RIO DE JANEIRO": "3304557",
        "VARGEM GRANDE PAULISTA": "3556453",
        "POJUCA": "2925303",
        "IACU": "2912707", "IAÇU": "2912707",
        "MATA DE SAO JOAO": "2921005", "MATA DE SÃO JOÃO": "2921005",
        "ROSARIO DA LIMEIRA": "3156452", "ROSÁRIO DA LIMEIRA": "3156452",
        "BROTAS DE MACAUBAS": "2904506", "BROTAS DE MACAÚBAS": "2904506",
        "GUARULHOS": "3518800",
        "MONTE SANTO": "2921550",
        "SAO JOSE": "4216602", "SÃO JOSÉ": "4216602",  # São José/SC (Grande Florianópolis)
        "SANTOS": "3548500",
    }

    def __init__(self, default_uf: str = "BA", default_code: str = "2927408"):
        """
        Args:
            default_uf:   UF padrão para fallback quando a UF não for detectada.
            default_code: Código IBGE padrão (Salvador/BA = 2927408).
        """
        self.default_uf = default_uf.upper()
        self.default_code = default_code

    def extract_and_validate(self, text: str, detected_uf: str = "BA", city_hint: str = None, raw_doc_text: str = None) -> str:
        """
        Tenta extrair o código IBGE do texto e valida contra a UF detectada.
        """
        uf = detected_uf.upper()
        prefix_esperado = self.UF_PREFIXES.get(uf, self.UF_PREFIXES.get(self.default_uf, "29"))

        # 0. Lookup direto pelo nome do município (city_hint), antes de qualquer
        #    busca por padrão no texto — evita que "SALVADOR" no endereço do
        #    tomador retorne o código de Salvador para o prestador de Camaçari.
        if city_hint:
            hint_upper = re.sub(r'[^\w\s]', '', city_hint).strip().upper()
            if hint_upper in self.KNOWN_CITIES:
                return self.KNOWN_CITIES[hint_upper]

        # 1. Busca todos os números de 5 a 7 dígitos no bloco da entidade
        candidates = re.findall(r'\b\d{5,7}\b', text)
        for candidate in candidates:
            if candidate.startswith(prefix_esperado):
                if len(candidate) == 7:
                    return candidate
                elif len(candidate) in (5, 6):
                    return candidate.ljust(7, '0')

        # 2. Busca no texto completo do documento (códigos IBGE explícitos)
        if raw_doc_text:
            candidates_full = re.findall(r'\b\d{7}\b', raw_doc_text)
            for candidate in candidates_full:
                if candidate.startswith(prefix_esperado):
                    return candidate

        # 3. Fallback por nome de capital no bloco da entidade (NÃO no doc inteiro)
        nome_busca = (city_hint or "").upper() + text.upper()
        p_rio = rf'R\s*I\s*O\s*D\s*E\s*[\s\n]*J\s*A\s*N\s*E\s*I\s*R\s*O'
        p_sp = rf'S\s*[AÃ]\s*O\s*[\s\n]*P\s*A\s*U\s*L\s*O'
        p_ssa = rf'S\s*A\s*L\s*V\s*A\s*D\s*O\s*R'

        if uf == "RJ" and re.search(p_rio, nome_busca, re.I):
            return "3304557"
        if uf == "SP" and re.search(p_sp, nome_busca, re.I):
            return "3550308"
        if uf == "BA" and re.search(p_ssa, nome_busca, re.I):
            return "2927408"

        # 4. Fallback final por UF (capital do estado)
        return self.DEFAULT_CODES_BY_UF.get(uf, self.default_code)
