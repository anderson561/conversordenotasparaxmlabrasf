# -*- coding: utf-8 -*-
"""Guarajuba Shopping Ltda (CNPJ real 24.890.395/0001-03, confirmado pelo
usuário) é tomadora recorrente num lote de 30 notas em municípios/layouts
diferentes. Achado real, nota Salvador/BA nº 00054394: o OCR deste scan lê
consistentemente "24.890.396/0001-03" (o "5" de ".395" sai "6"), quebrando o
dígito verificador — sem nenhum outro CNPJ válido sobrando no documento para
o fallback de "scavenge" usar, o tomador caía no sentinela
`00000000000100`. Mesmo princípio já usado para BONI TRANSPORTES: só
substitui quando o checksum JÁ reprovou e a razão social bate com esta
contraparte conhecida, nunca mascarando um CNPJ genuinamente diferente de
outra empresa."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'PREFEITURA MUNICIPAL DO SALVADOR\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social:\n'
    'GUARAJUBA SHOPPING LTDA\n'
    'CPF/CNPJ:\n'
    '24.890.396/0001-03\n'
    'Endereço:\n'
    'AL MONTE DAS DUNAS SN GUARAJUBA - Camaçari - CEP: 42827-000/BA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'Locação de máquinas e equipamentos\n'
    'VALOR TOTAL DA NOTA = R$391,57\n'
)


def _novo_extrator(texto):
    dummy_path = "tests/dummy_guarajuba_shopping_cnpj.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_cnpj_de_guarajuba_shopping_corrigido_quando_digito_ilegivel():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT)
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == "24890395000103"
    finally:
        os.remove(dummy_path)


def test_correcao_nao_sobrescreve_cnpj_ja_valido():
    # Guard não deve disparar quando o CNPJ já é válido (nunca sobrescreve
    # um valor que já passou no checksum).
    texto = MOCK_TEXT.replace('24.890.396/0001-03', '24.890.395/0001-03')
    extractor, dummy_path = _novo_extrator(texto)
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == "24890395000103"
    finally:
        os.remove(dummy_path)


def test_correcao_nao_dispara_para_empresa_diferente_com_cnpj_invalido():
    # Guard é ancorado na razão social exata "GUARAJUBA SHOPPING" — um CNPJ
    # inválido de outra empresa qualquer não deve ser mascarado por este
    # valor fixo.
    texto = MOCK_TEXT.replace('GUARAJUBA SHOPPING LTDA', 'OUTRA EMPRESA QUALQUER LTDA')
    extractor, dummy_path = _novo_extrator(texto)
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf != "24890395000103"
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
