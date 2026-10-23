# -*- coding: utf-8 -*-
r"""NFS-e de Camaçari/BA ESCANEADA (`LAYOUT_CAMACARI_3`, CPqD) — lote real
"Scan2026-10-16_110738.pdf" (STAUMMAQ, 16/10/2026), páginas 2, 5 e 9.

Defeitos corrigidos (conferidos contra a imagem renderizada das páginas):

1. ALÍQUOTA (notas nº 4584 e 4571, impressa "3,78"): o extrator já guardava
   0.0378, mas o `Abrasf201Transformer` formatava a alíquota com `:.2f` e o
   XML saía `0.04`. Agora sai com até 4 casas (`tsAliquota` admite 4) e no
   mínimo 2 — alíquota inteira continua idêntica ("0.05").
2. METADE DE CIMA DA NOTA nº 4571 (pág. 5): a leitura zoom 4 + PSM 6 de
   `_ocr_camacari_scan` segmentou mal o topo deste scan limpo — prestador sem
   Inscrição Municipal e sem logradouro, município "CAMAÇARI ida" (caía no
   default Salvador/2927408), tomador sem CPF/CNPJ (sentinela "Tomador Não
   Identificado") e discriminação lixo. A grade de valores da mesma leitura
   saiu perfeita. `_camacari_reparar_metade_superior` relê em zoom 5 + PSM 6
   só quando faltam os 2 documentos válidos e troca só o topo.
3. MUNICÍPIO com sujeira minúscula ("CAMAÇARI ida"): cortada quando o nome
   lido inteiro não é município conhecido e o cortado é.
4. NOTA nº 5084 (pág. 9, GUINCHOS BEIRA RIO LTDA): Número "S" -> "S/N" (a
   captura parava na barra) e Bairro "RIO LTDA" -> "SANTO ANTONIO" (a grafia
   OCR "Beira" aceita como rótulo de bairro casava o "BEIRA" da razão social;
   agora só vale seguida de ":"/".").

Os textos abaixo são o OCR REAL (Tesseract) das páginas, verbatim.
"""
import io

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer

# Pág. 2, nota nº 4584 — texto final de `_ocr_page` (inalterado por este fix).
OCR_P2_4584 = (
    'Número da Nota\n'
    '4584\n'
    'Data de Emissão\n'
    '01/10/2026 10:18\n'
    'Código de autenticidade\n'
    'K6IH7CGAV\n'
    '021674001\n'
    'Nº: SN\n'
    'rr\n'
    '\n'
    'mero da Nota\n'
    '4584\n'
    'ta de Emissão\n'
    '01/10/2026 10:18\n'
    'digo de autenticidade\n'
    'K6IH7CGAV\n'
    '1\n'
    'Nº: SN\n'
    'UF: BA\n'
    '\n'
    'o) Número da Nota\n'
    'Ns PREFEITURA MUNICIPAL DE CAMAÇARI 4584\n'
    '” id : Data de Emissão\n'
    'CEE Secretaria da Fazenda pr\n'
    'Ea NOTA FISCAL DE SERVIÇOS ELETRÔNICA\n'
    'K6IH7CGAV\n'
    'PRESTADOR DE SERVIÇOS\n'
    '> Nome/Razão Social: ROSANA JULIAO CARDOSO & CIA LTDA - ME\n'
    'SEMIIL CPF/CNPJ: 11.289.382/0001-31 Inscrição Municipal: 0021674001\n'
    'Logradouro: BA 522 - VIA CASCALHEIRA Nº: SN\n'
    'Compl.: SALA 04 Bairro:  CASCALHEIRA (ABRANTES)\n'
    'CEP: 42820512 Município: CAMAÇARI UF: BA\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA\n'
    'CPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal:\n'
    'Logradouro: VIA URBANA Nº: 01\n'
    'Compl.: Bairro: CIA SUL\n'
    'CEP: 43700000 Município: SIMÕES FILHO UF: BA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\n'
    'MANUTENÇÃO PREVENTIVA DE TRANSFORMADORES ATRAVÉS DOS TESTES EM ÓLEO 1,0000 1.687,03 1.687,03\n'
    'ISOLANTE CONFORME PROPOSTA SEMIL 367/2026\n'
    'DOC EMITIDO POR EP NÃO GERA DIREITO A CREDITO FISCAL DE ICMS, ISS E 0,0000 0,00 0,00\n'
    'IPI. EMPRESA OPTANTE DO SIMPLES NACIONAL. SERVIÇO REALIZADO NA\n'
    'SEMIL\n'
    'VENCIMENTO: 10/10/2026 ATRAVÉS DE BOLETO BANCÁRIO EMITIDO PELO 0,0000 0,00 0,00\n'
    'BANCO ITAU\n'
    'a A\n'
    '[=] ita [m] 1) [lã E ai [m]\n'
    'EEAda XML PDF [npitide\n'
    'Retenções (R$) ótais (R$)\n'
    'PIS: O 9,00 | Valor dos Serviços (R$) 1.687,03\n'
    'COFINS: ( (q 0,00 [Deduções (- 0,00\n'
    'INSS: 747 0,00 | Base de Cálculo (=) 1.687,03\n'
    'IR: 3, jo 0,00 | Alíquota (%) 3,78\n'
    'CSLL: CAIL 0,00 | Valor do ISS (R$) 63,76\n'
    'Outras: m ) If) 0,00 |Valor Líquido da Nota (=) 1.687,03\n'
    'Total de Retenções: o) 0,00\n'
    'Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 01/10/2026\n'
    'Município da prestação do serviço: 2905701 - CAMACARI\n'
    'Município da tributação: 2905701 - CAMACARI\n'
    "CNAE: '\n"
    'Serviço: 001401 - LUBRIFICAÇÃO, LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RESTAURAÇÃO, BLINDAGEM,\n'
    'MANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, VEÍCULOS, APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE\n'
    'QUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS).\n'
    'LO [>>>\n'
    'CPqD - Gestão Pública Data Impressão: 01/10/2026 10:18\n'
)

# Pág. 9, nota nº 5084 — texto final de `_ocr_page` (inalterado por este fix).
OCR_P9_5084 = (
    'Número da Nota\n'
    '5084\n'
    'Data de Emissão\n'
    '- 25/09/2026 15:30\n'
    'Código de autenticidade\n'
    'S9042P0SP\n'
    '041217001\n'
    'Nº; S/N\n'
    '\n'
    'mero da Nota\n'
    '5084\n'
    'ta de Emissão\n'
    '- 25/09/2026 15:30\n'
    'digo de autenticidade\n'
    'S9042P0SP\n'
    '1\n'
    'Nº; S/N\n'
    'UF: BA\n'
    '\n'
    'ei ad aa Número da Nota\n'
    'ti PREFEITURA MUNICIPAL DE CAMAÇARI\n'
    'bd NOTA FISCAL DE SERVIÇOS ELETRÔNICA\n'
    'S9042P0SP\n'
    'PRESTADOR DE SERVIÇOS\n'
    'Nome/Razão Social: GUINCHOS BEIRA RIO LTDA\n'
    'CPF/CNPJ: 36.751.976/0001-43 Inscrição Municipal: 0041217001\n'
    'Logradouro: | RODOVIA BA-522 - VIA COPEC Nº: S/N\n'
    'Compl.: Bairro: SANTO ANTONIO\n'
    'CEP: 42805830 Município: CAMAÇARI UF: BA\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA\n'
    'CPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal:\n'
    'Logradouro: VIA URBANA Nº: 01\n'
    'Compl.: Bairro: CIA SUL\n'
    'CEP: 43700000 Município: SIMÕES FILHO UF: BA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\n'
    '22/09/26 TRANSPORTE DE 01 MOTOR DA DOW QUIMICA PARA STAUMMO 1,0000 1.000,00 1.000,00\n'
    'DADOS PARA PAGAMENTO: BANCO ITAÚ AGÊNCIA: 0501 CONTA CORRENTE: 0,0000 0,00 0,00\n'
    '49395 -1 BENEFICIARIO GUINCHOS BEIRA RIO LTDA CNPJ: 36.751.976/0001\n'
    '-43 PAGAMENTO PARA 10/10/26 PIX 71 99168-2175\n'
    'Be | Rn\n'
    'leao XML PDF alpes\n'
    'Retenções (R$) Totais (R$)\n'
    'PIS: eo 0,00 |Valor dos Serviços (R$) 1.000,00\n'
    'COFINS: e 0,00 | Deduções (-) 0,00\n'
    'INSS: 7 A0)) 0,00 | Base de Cálculo (=) 1.000,00\n'
    'IR: C$ No 0,00 | Alíquota (%) 5,00\n'
    'CSLL: ”“ GC AGA 0,00 | Valor do ISS (R$) 50,00\n'
    'Outras: Gnifo 0,00 |Valor Líquido da Nota (=) 1.000,00\n'
    'Total de Retenções: 0,00\n'
    'Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 25/09/2026\n'
    'Município da prestação do serviço: 2905701 - CAMACARI\n'
    'Município da tributação: 2905701 - CAMACARI\n'
    'CNAE:\n'
    'Serviço: 001602 - OUTROS SERVIÇOS DE TRANSPORTE DE NATUREZA MUNICIPAL.\n'
    'PD GesdoPúblca Datalmpressão: 250920261530\n'
)

# Pág. 5, nota nº 4571 — texto final de `_ocr_page` COM o reparo da metade
# superior (cabeçalho recortado + topo do zoom 5 + grade do zoom 4).
OCR_P5_4571 = (
    'Número da Nota\n'
    '4571\n'
    'Data de Emissão\n'
    '18/09/2026 11:18\n'
    'Código de autenticidade\n'
    '0QYQQFR54\n'
    '021674001\n'
    'Nº: SN\n'
    '\n'
    'E\n'
    '\n'
    'mero da Nota\n'
    '4571\n'
    'a de Emissão\n'
    '18/09/2026 11:18\n'
    'ligo de autenticidade\n'
    'OQYQQFR54\n'
    '|\n'
    'Nº: SN\n'
    'UF: BA\n'
    '\n'
    'Número da Nota\n'
    'Data de Emissão\n'
    'Código de autenticidade\n'
    '1674001\n'
    'Nº: SN\n'
    '-S)\n'
    '\n'
    'oo Número da Nota\n'
    'e PREFEITURA MUNICIPAL DE CAMAÇARI\n'
    'RR Secretaria da Fazenda\n'
    ': , 18/09/2026 11:18\n'
    'Da NOTA FISCAL DE SERVIÇOS ELETRÔNICA Código de autenticidade\n'
    'É É OQYQAFR54\n'
    'PRESTADOR DE SERVIÇOS\n'
    'El Nome/Razão Social: ROSANA JULIAO CARDOSO & CIA LTDA - ME\n'
    'SEMIL CPF/CNPJ: 11.289.382/0001-31 Inscrição Municipal: 0021674001\n'
    'Logradouro: BA 522 - VIA CASCALHEIRA Nº: SN\n'
    'Compl.: SALA 04 Bairro: — CASCALHEIRA (ABRANTES)\n'
    'CEP: 42820512 Município: CAMAÇARI UF: BA\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA\n'
    'CPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal:\n'
    'Logradouro: VIA URBANA Nº: 01\n'
    'Compl.: Bairro: CIA SUL\n'
    'CEP: 43700000 Município: SIMÕES FILHO UF: BA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\n'
    'MANUTENÇÃO PREVENTIVA DE TRANSFORMADORES ATRAVÉS DOS TESTES EM ÓLEO 1,0000 953,54 953,54\n'
    'ISOLANTE CONFORME PROPOSTA SEMIL 364/2026\n'
    'DOC EMITIDO POR EP NÃO GERA DIREITO A CREDITO FISCAL DE ICMS, ISS E 0,0000 0,00 0,00\n'
    'IPI. EMPRESA OPTANTE DO SIMPLES NACIONAL. SERVIÇO REALIZADO NA\n'
    'SEMIL\n'
    'VENCIMENTO: 30/09/2026 ATRAVÉS DE BOLETO BANCÁRIO EMITIDO PELO 0,0000 0,00 0,00\n'
    'BANCO ITAU\n'
    'Eliane ERR\n'
    'ER por Ejs\n'
    'ele XML\n'
    '\n'
    'Retenções (R$) Totais (R$)\n'
    'PIS: q VA 0,00 | Valor dos Serviços (R$) 953,54\n'
    'COFINS: ) 0,00 | Deduções (-) 0,00\n'
    'INSS: TUA , 0,00 | Base de Cálculo (=) 953,54\n'
    'IR: Ato 0,00 |Aliquota (%) 3,78\n'
    'CSLL: 0,00 | Valor do ISS (R$) 36,04\n'
    'Outras: GuDO 0,00 | Valor Líquido da Nota (=) 953,54\n'
    'Total de Retenções: ) 0,00\n'
    'Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 18/09/2026\n'
    'Município da prestação do serviço: 2905701 - CAMACARI\n'
    'Município da tributação: 2905701 - CAMACARI\n'
    'CNAE: . . . .\n'
    'Serviço: 001401 - LUBRIFICAÇÃO, LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RESTAURAÇÃO, BLINDAGEM,\n'
    'MANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, VEÍCULOS, APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE\n'
    'QUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS).\n'
    'LOW\n'
    'CPqD - Gestão Pública Data Impressão: 18/09/2026 11:18\n'
)

# Pág. 5 — o recorte do cabeçalho (prependado) e o corpo zoom 4 + PSM 6
# ANTES do reparo (o que a main entregava ao extrator).
OCR_P5_CABECALHO = (
    'Número da Nota\n'
    '4571\n'
    'Data de Emissão\n'
    '18/09/2026 11:18\n'
    'Código de autenticidade\n'
    '0QYQQFR54\n'
    '021674001\n'
    'Nº: SN\n'
    '\n'
    'E\n'
    '\n'
    'mero da Nota\n'
    '4571\n'
    'a de Emissão\n'
    '18/09/2026 11:18\n'
    'ligo de autenticidade\n'
    'OQYQQFR54\n'
    '|\n'
    'Nº: SN\n'
    'UF: BA\n'
    '\n'
    'Número da Nota\n'
    'Data de Emissão\n'
    'Código de autenticidade\n'
    '1674001\n'
    'Nº: SN\n'
    '-S)\n'
    '\n'
)
OCR_P5_CORPO_Z4_RUIM = (
    'Ass PREFEITURA MUNICIPAL DE CAMAÇARI\n'
    'RR Secretaria da Fazenda E io | vas\n'
    'E] A 18/09/2026 11:18\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA\n'
    '0QYQQFR54\n'
    ', : PRESTADOR DE SERVIÇOS\n'
    'ea Nome/Razão Social: ROSANA JULIAO CARDOSO & CIA LTDA - ME\n'
    'SE MIL CPF/CNP): 11.289.382/0001-31 irã ;\n'
    'In ipal:\n'
    'Logradouro: BA 522 - VIA CASCALHEIRA Ep O\n'
    'Compl.: SALA 04 , Nº: SN\n'
    'Bairro:  CASCALHEIRA\n'
    'CEP: 42820512 Município: CAMAÇARI ida UF\n'
    ': BA\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razã jal:\n'
    'nr Social tee RR TECNICOS AUTOMACA MOTORES E MAQ LTDA\n'
    'Logradouro: VIA URBANA Inarigeão anos\n'
    'Compl.: , Nº: 01\n'
    '. Bairro: CIA SUL\n'
    'CEP: 43700000 Município: SIMÕES FILHO UF: BA\n'
    'º DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'DESCRIÇÃO ma E Ni\n'
    'MANUTENÇÃO PREVENTIVA DE TRANSFORMADO É dr VALOR TOTAL (R$)\n'
    'ISOLANTE CONFORME PROPOSTA SEMIL PP dd a naaao Ss Sa 953,54\n'
    'DOC EMITIDO POR EP NÃO GERA DIREITO A CREDITO FIS\n'
    'IPI. EMPRESA OPTANTE DO SIMPLES NACIONAL. a i sa Si 20 BO\n'
    'SEMIL\n'
    'VENCIMENTO: 30/09/2026 A É Á\n'
    'Dias TRAVÉS DE BOLETO BANCÁRIO EMITIDO PELO 0,0000 0,00 ando\n'
    '[alastra XML PDF [n] Sima\n'
    'Retenções (R$) Totais (R$)\n'
    'PIS: q VA 0,00 | Valor dos Serviços (R$) 953,54\n'
    'COFINS: ) 0,00 | Deduções (-) 0,00\n'
    'INSS: TUA , 0,00 | Base de Cálculo (=) 953,54\n'
    'IR: Ato 0,00 |Aliquota (%) 3,78\n'
    'CSLL: 0,00 | Valor do ISS (R$) 36,04\n'
    'Outras: GuDO 0,00 | Valor Líquido da Nota (=) 953,54\n'
    'Total de Retenções: ) 0,00\n'
    'Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 18/09/2026\n'
    'Município da prestação do serviço: 2905701 - CAMACARI\n'
    'Município da tributação: 2905701 - CAMACARI\n'
    'CNAE: . . . .\n'
    'Serviço: 001401 - LUBRIFICAÇÃO, LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RESTAURAÇÃO, BLINDAGEM,\n'
    'MANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, VEÍCULOS, APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE\n'
    'QUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS).\n'
    'LOW\n'
    'CPqD - Gestão Pública Data Impressão: 18/09/2026 11:18\n'
)

# Pág. 5 — a releitura zoom 5 + PSM 6 da página inteira (topo bom, grade ruim).
OCR_P5_CORPO_Z5 = (
    'oo Número da Nota\n'
    'e PREFEITURA MUNICIPAL DE CAMAÇARI\n'
    'RR Secretaria da Fazenda\n'
    ': , 18/09/2026 11:18\n'
    'Da NOTA FISCAL DE SERVIÇOS ELETRÔNICA Código de autenticidade\n'
    'É É OQYQAFR54\n'
    'PRESTADOR DE SERVIÇOS\n'
    'El Nome/Razão Social: ROSANA JULIAO CARDOSO & CIA LTDA - ME\n'
    'SEMIL CPF/CNPJ: 11.289.382/0001-31 Inscrição Municipal: 0021674001\n'
    'Logradouro: BA 522 - VIA CASCALHEIRA Nº: SN\n'
    'Compl.: SALA 04 Bairro: — CASCALHEIRA (ABRANTES)\n'
    'CEP: 42820512 Município: CAMAÇARI UF: BA\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA\n'
    'CPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal:\n'
    'Logradouro: VIA URBANA Nº: 01\n'
    'Compl.: Bairro: CIA SUL\n'
    'CEP: 43700000 Município: SIMÕES FILHO UF: BA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\n'
    'MANUTENÇÃO PREVENTIVA DE TRANSFORMADORES ATRAVÉS DOS TESTES EM ÓLEO 1,0000 953,54 953,54\n'
    'ISOLANTE CONFORME PROPOSTA SEMIL 364/2026\n'
    'DOC EMITIDO POR EP NÃO GERA DIREITO A CREDITO FISCAL DE ICMS, ISS E 0,0000 0,00 0,00\n'
    'IPI. EMPRESA OPTANTE DO SIMPLES NACIONAL. SERVIÇO REALIZADO NA\n'
    'SEMIL\n'
    'VENCIMENTO: 30/09/2026 ATRAVÉS DE BOLETO BANCÁRIO EMITIDO PELO 0,0000 0,00 0,00\n'
    'BANCO ITAU\n'
    'Eliane ERR\n'
    'ER por Ejs\n'
    'ele XML\n'
    'Retenções (R$) vena (RS: 953,54\n'
    'PIS: MA 0,00 | Valor dos Serviços (R$) ,\n'
    'INTER 0,00 | Deduções (-) 0,00\n'
    'COFINS: » 953,54\n'
    'RE: AV 0,00 |Base de Cálculo (=) ra\n'
    'no / 0,00 | Alíquota (%) ,\n'
    'IR: y\n'
    'o (K to 0,00 | Valor do ISS (R$) Ee\n'
    'Outras: NIDA 0,00 | Valor Líquido da Nota (=) É\n'
    'Total de Retenções: 0,00 = co: 18/09/2026\n'
    'Tipo de tributação: A RECOLHER PELO PRESTADOR Deita Aa presmtiaçõa Onionnioas\n'
    'Município da prestação do serviço: 2905701 - CAMACARI\n'
    'Município da tributação: 2905701 - CAMACARI\n'
    'CNAE: ” z Ã STAURAÇÃO, BLINDAGEM\n'
    'Go: E PEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RE , ,\n'
    'MANTER O E GONHERNS dO DE MÁQUINAS, VEICULOS: APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE\n'
    'QUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS).\n'
    'CPqD - Gestão Pública En\n'
)


def _parse(monkeypatch, tmp_path, mock, numero):
    caminho = tmp_path / ("Scan2026-10-16_110738 - NF %s.pdf" % numero)
    caminho.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock)
    extractor = SPPdfExtractor(str(caminho))
    notas = extractor.parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.mark.parametrize("mock, numero", [
    ("OCR_P2_4584", "4584"), ("OCR_P5_4571", "4571"), ("OCR_P9_5084", "5084")])
def test_as_tres_paginas_usam_o_extrator_do_camacari_escaneado(
        monkeypatch, tmp_path, mock, numero):
    vistos = []
    original = SPPdfExtractor._extrair_entidade_camacari3

    def espiao(self, is_prestador):
        vistos.append(self.layout)
        return original(self, is_prestador)

    monkeypatch.setattr(SPPdfExtractor, "_extrair_entidade_camacari3", espiao)
    _parse(monkeypatch, tmp_path, globals()[mock], numero)
    assert vistos and set(vistos) == {"camacari_ba_scan_v3"}


@pytest.fixture
def nota_4584(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, OCR_P2_4584, "4584")


@pytest.fixture
def nota_4571(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, OCR_P5_4571, "4571")


@pytest.fixture
def nota_5084(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, OCR_P9_5084, "5084")


# ------------------------------------------------------------ 1. ALÍQUOTA

@pytest.mark.parametrize("valor, esperado", [
    (0.05, "0.05"), (0.02, "0.02"), (0.0, "0.00"), (1.0, "1.00"),
    (0.0378, "0.0378"), (0.0201, "0.0201"), (0.035, "0.035"),
    (0.037799999999, "0.0378"), (0.04999999, "0.05"),
])
def test_format_aliquota(valor, esperado):
    assert Abrasf201Transformer._format_aliquota(valor) == esperado


def test_aliquota_3_78_da_4584_vai_inteira_para_o_xml(nota_4584):
    assert nota_4584.valores.aliquota == pytest.approx(0.0378)
    xml = Abrasf201Transformer().transform(nota_4584)
    assert xml.count("<Aliquota>0.0378</Aliquota>") == 2
    assert "<Aliquota>0.04</Aliquota>" not in xml


def test_aliquota_inteira_continua_com_duas_casas(nota_5084):
    xml = Abrasf201Transformer().transform(nota_5084)
    assert xml.count("<Aliquota>0.05</Aliquota>") == 2


def test_4584_nao_regride(nota_4584):
    n = nota_4584
    assert n.numero == "4584"
    assert n.codigo_verificacao == "K6IH7CGAV"
    assert n.valores.valor_servicos == pytest.approx(1687.03)
    assert n.valores.base_calculo == pytest.approx(1687.03)
    assert n.valores.valor_iss == pytest.approx(63.76)
    assert n.valores.valor_liquido_nfse == pytest.approx(1687.03)
    p = n.prestador
    assert p.cnpj_cpf == "11289382000131"
    assert p.inscricao_municipal == "0021674001"
    assert p.endereco.logradouro == "BA 522 - VIA CASCALHEIRA"
    assert p.endereco.numero == "SN"
    assert p.endereco.bairro == "CASCALHEIRA (ABRANTES)"
    assert p.endereco.codigo_municipio == "2905701"
    t = n.tomador
    assert t.cnpj_cpf == "02370080000100"
    assert t.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA"
    assert t.endereco.codigo_municipio == "2930709"


# ------------------------------------------- 2. METADE DE CIMA DA 4571

def test_4571_prestador_completo(nota_4571):
    p = nota_4571.prestador
    assert p.cnpj_cpf == "11289382000131"
    assert p.inscricao_municipal == "0021674001"
    assert p.endereco.logradouro == "BA 522 - VIA CASCALHEIRA"
    assert p.endereco.bairro == "CASCALHEIRA (ABRANTES)"
    assert p.endereco.cep == "42820512"
    assert p.endereco.codigo_municipio == "2905701"


def test_4571_tomador_identificado(nota_4571):
    t = nota_4571.tomador
    assert t.cnpj_cpf == "02370080000100"
    assert t.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA"
    assert t.endereco.logradouro == "VIA URBANA"
    assert t.endereco.numero == "01"
    assert t.endereco.bairro == "CIA SUL"
    assert t.endereco.cep == "43700000"
    assert t.endereco.codigo_municipio == "2930709"


def test_4571_discriminacao_fiel_e_valores(nota_4571):
    n = nota_4571
    assert n.numero == "4571"
    assert n.codigo_verificacao == "0QYQQFR54"
    assert n.discriminacao.startswith(
        "MANUTENÇÃO PREVENTIVA DE TRANSFORMADORES ATRAVÉS DOS TESTES EM ÓLEO "
        "ISOLANTE CONFORME PROPOSTA SEMIL 364/2026")
    assert "VENCIMENTO: 30/09/2026" in n.discriminacao
    assert "naaao" not in n.discriminacao
    assert n.valores.valor_servicos == pytest.approx(953.54)
    assert n.valores.aliquota == pytest.approx(0.0378)
    assert n.valores.valor_iss == pytest.approx(36.04)
    assert n.valores.valor_liquido_nfse == pytest.approx(953.54)


class _Pix:
    def tobytes(self, fmt):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (4, 4), "white").save(buf, format="PNG")
        return buf.getvalue()


class _Pagina:
    def get_pixmap(self, matrix=None):
        return _Pix()


def test_reparo_troca_so_o_topo_e_preserva_a_grade(monkeypatch, tmp_path):
    import pytesseract
    chamadas = []

    def fake(img, lang=None, config=None):
        chamadas.append(config)
        return OCR_P5_CORPO_Z5
    monkeypatch.setattr(pytesseract, "image_to_string", fake)
    caminho = tmp_path / "x.pdf"
    caminho.write_bytes(b"%PDF-1.4")
    ext = SPPdfExtractor(str(caminho))

    assert ext._camacari_docs_entidades(OCR_P5_CORPO_Z4_RUIM) == 1
    reparado = ext._camacari_reparar_metade_superior(_Pagina(), 0, OCR_P5_CORPO_Z4_RUIM)
    assert chamadas == ["--psm 6"]
    assert ext._camacari_docs_entidades(reparado) == 2
    topo, grade = reparado.split("Retenções (R$)", 1)
    assert "02.370.080/0001-00" in topo
    assert "SEMIL 364/2026" in topo
    # a grade vem da leitura zoom 4 (no zoom 5 ela se desmonta)
    assert "Aliquota (%) 3,78" in grade
    assert "Valor dos Serviços (R$) 953,54" in grade


def test_reparo_nao_mexe_em_leitura_sa(monkeypatch, tmp_path):
    import pytesseract

    def proibido(*a, **k):
        raise AssertionError("não deveria reler a página")
    monkeypatch.setattr(pytesseract, "image_to_string", proibido)
    caminho = tmp_path / "x.pdf"
    caminho.write_bytes(b"%PDF-1.4")
    ext = SPPdfExtractor(str(caminho))
    assert ext._camacari_reparar_metade_superior(_Pagina(), 0, OCR_P2_4584) is OCR_P2_4584


def test_reparo_sem_ganho_devolve_o_original(monkeypatch, tmp_path):
    import pytesseract
    monkeypatch.setattr(pytesseract, "image_to_string",
                        lambda *a, **k: OCR_P5_CORPO_Z4_RUIM)
    caminho = tmp_path / "x.pdf"
    caminho.write_bytes(b"%PDF-1.4")
    ext = SPPdfExtractor(str(caminho))
    assert ext._camacari_reparar_metade_superior(
        _Pagina(), 0, OCR_P5_CORPO_Z4_RUIM) is OCR_P5_CORPO_Z4_RUIM


# ---------------------------------- 3. MUNICÍPIO COM SUJEIRA MINÚSCULA

def test_municipio_com_sujeira_nao_cai_em_salvador(monkeypatch, tmp_path):
    """Mesmo com a leitura RUIM (sem o reparo), o "CAMAÇARI ida" do
    prestador resolve Camaçari em vez do default Salvador. O tomador segue
    sem documento nessa leitura — sentinela honesto, não inventado."""
    n = _parse(monkeypatch, tmp_path, OCR_P5_CABECALHO + OCR_P5_CORPO_Z4_RUIM, "4571")
    assert n.prestador.endereco.codigo_municipio == "2905701"
    assert n.prestador.endereco.codigo_municipio != "2927408"
    assert n.tomador.cnpj_cpf == "00000000000000"


# ----------------------------------------------------- 4. NOTA 5084

def test_5084_numero_s_barra_n(nota_5084):
    assert nota_5084.prestador.endereco.numero == "S/N"


def test_5084_bairro_nao_vaza_da_razao_social(nota_5084):
    p = nota_5084.prestador
    assert p.razao_social == "GUINCHOS BEIRA RIO LTDA"
    assert p.endereco.bairro == "SANTO ANTONIO"


def test_5084_resto_nao_regride(nota_5084):
    n = nota_5084
    assert n.numero == "5084"
    assert n.codigo_verificacao == "S9042P0SP"
    p = n.prestador
    assert p.cnpj_cpf == "36751976000143"
    assert p.inscricao_municipal == "0041217001"
    assert p.endereco.logradouro == "RODOVIA BA-522 - VIA COPEC"
    assert p.endereco.cep == "42805830"
    assert p.endereco.codigo_municipio == "2905701"
    assert n.tomador.cnpj_cpf == "02370080000100"
    assert n.tomador.endereco.numero == "01"
    assert n.tomador.endereco.bairro == "CIA SUL"
    assert n.valores.valor_servicos == pytest.approx(1000.00)
    assert n.valores.aliquota == pytest.approx(0.05)
    assert n.valores.valor_iss == pytest.approx(50.00)
