# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — Código de Verificação não pode virar o título do
documento quando o valor real nunca sai legível em NENHUM ponto do texto.

Nota real nº 2419 (LUNITECK -> BONI TRANSPORTES, PDF de 2 páginas em que a
pág. 1 é esta NFS-e de Salvador/BA muito degradada — mesmo os recuts
dedicados do LAYOUT_SALVADOR, que já tentam recuperar exatamente esse tipo de
degradação, não acham nada de útil aqui). O rótulo "Verificação:" sai legível,
mas o valor real nunca aparece — o que sobra logo depois, a várias linhas de
distância, é o título "PREFEITURA MUNICIPAL DO SALVADOR". O regex antigo
(`erifica[çc][aã]o\\s*:?\\s*(?:S?ALVADOR\\s*)?([A-Z0-9]{3,5}-?[A-Z0-9]{2,6})`)
atravessava esse vão e capturava "PREFEITURA" como se fosse o próprio código
— mesmo bug de "ALVADOR"/"PRESTADOR"/"TOMADOR" (rótulos do documento sendo
capturados como código), aqui com o TÍTULO do documento no lugar do rótulo de
seção seguinte.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR_P1 = (
    'VALOR TOTAL DA NOTA = R$ 397,14\n'
    'RSS: - [| Númeroda Nata:\n'
    '- Data je Horade Emissão: E\n'
    'e ago Sé I a "Cóvigo- de Verificação:\n\n'
    'PREFEITURA MUNICIPAL. DO SALVADOR DbOUZaçd Nota:\n\n'
    'Data de Emissão\n'
    'SECRETARIA MUNICIPAL DA. FAZENDA Pata ond em o:\n\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador Sesipa ge Vericação:\n\n'
    'PRESTADOR DE SERVIÇOS\n\n'
    '"CPECNDE Inscrição Mithicipal:\n'
    ':07,295.620/0001:34 -D0:384-869/001-60\n\n'
    'TOMARIA BE: E SEAVGOS\n\n'
    'NoineiRarão Sogial:\n'
    'pia -PRANSPORTES, LOGISTICA E-COMERCIO LTDA.\n\n'
    'GRE\n\n'
    'pg CN\n'
    'o TELB. APÚG%. tabs, À. TLD GN: RS 23,83\n\n'
    "VALOR TOTAL DA NOTA = 'R$397/14\n"
    'MÃE?\n'
    '9541800 = Reparação emantitenção de "computadores: e-de-squipamentos periféricos\n\n'
    'Valor Toiaídas Deduções:\n\n'
    'Bliss de Cálculo (RO) Pagan Valor 0155 (Rar Crédito Nota Salvador (R$)\n'
    '. , . E o e 0, Do\n'
    'Nalor INSS (R$y; [a PIS (RSS: Valor coRnS (Re | Valarir (Rg) | vatarosuL (ag) Jour RHEições E vaisi Liquido (R$);\n'
    '| 0,00; 0,00: 900) g;0o 0,00: (0:00 397,14\n'
    'Ala Ãas Cor Valor ES (RE: Alquola TES (a, Valor CESTAS\n\n'
    'x x\n\n'
    'OUTRAS INFORMAÇÕES\n'
    '=Esta-Nota Selvad «foi ida com respaldo na Lei 7,1486/2006\n'
    'EPP aptante:peio Simples. Nagional:\n'
    'it\n\n'
    '= Gódigo de: Tributação o Municipio: 1402-004 - Assistência lêcnica:\n'
)


def test_salvador_codigo_verificacao_rejeita_titulo_prefeitura():
    dummy_path = "tests/dummy_salvador_luniteck_p1.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_OCR_P1
        extractor.layout = extractor._detect_layout()
        assert extractor.layout == 'salvador_ba'

        codigo = extractor._extrair_codigo_verificacao()

        # BUG CORRIGIDO — não pode ser o título do documento.
        assert codigo != "PREFEITURA"
        # Quando o valor real não sobrevive em lugar nenhum do texto, o
        # honesto é o sentinela genérico, não um valor fabricado.
        assert codigo == "XXXX-XXXX"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
