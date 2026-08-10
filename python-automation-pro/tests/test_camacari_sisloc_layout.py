# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CAMACARI_SISLOC

# Texto REAL reconstruído por coordenada (`_reconstruir_texto_por_coordenadas`)
# da NFS-e nº 24052 — FERIMPORTE SERVICE LTDA -> DELTALINE SERVICOS LTDA.,
# Prefeitura Municipal de Camaçari/BA, plataforma SISLOC / NFS-e Easy
# (Benefix). PDF totalmente digital cujo gerador desenha rótulo e valor como
# objetos de texto separados no fluxo do PDF — o `pdfminer.high_level.
# extract_text()` padrão agrupa tudo numa ordem física quebrada (todos os
# valores despejados no fim do documento, fora de ordem), por isso este
# layout usa uma reconstrução dedicada via coordenadas de caractere (LTChar)
# em vez do texto padrão.
MOCK_TEXT = 'PREFEITURA MUNICIPAL DE CAMAÇARI # NFS-e 24052\n  \nCódigo de Verificação:\nSECRETARIA MUNICIPAL DE FINANÇAS \nUB9X49JPT\nNota Fiscal de Serviço Eletrônica (NFS-e)\nEmissão: 31/07/2026\n# RPS 222117 Série RPS Competência:\n31/07/2026\nRazão Social: FERIMPORTE SERVICE LTDA Telefone: (71)3621-6420\nR\nO\nD Inscrição Estadual:\nCNPJ: 05.100.645/0001-10 57645238 Inscrição Municipal: 0012130001\nA\nT\nS\nE Endereço: AV. JORGE AMADO, 0 - NOVA VITORIA CEP: 42.802-373\nR\nP\nMunicípio: CAMAÇARI UF: BA E-mail:\nRazão Social: DELTALINE SERVICOS LTDA. Telefone: (71)98787-0963\nR\nO\nD CNPJ/CPF: 01.813.680/0001-25 Inscrição Estadual: ISENTO Inscrição Municipal:\nA\nM\nO Endereço: RUA CAMBORIU, 39, IAPI, CEP 40330533, País BRASIL - IAPI CEP: 40.330-533\nT\nMunicípio: SALVADOR UF: BA E-mail:\nDISCRIMINAÇÃO DOS SERVIÇOS\nLOCACAO DE MAQUINAS E EQUIPAMENTOS CONFORME BOLETIM DE MEDICAO NO PERIODO DE 21/07/2026 A 24/07/2026\nData de Vencimento:30/08/2026\nCódigo Tributação do Município: 9901\nCódigo do Item Lista de Serviço (LC 116):  9901 Código CNAE: 7739099\no o\nã ã\nçi çi\nr r\nc c\ns s\ne e\nD D\nCamaçari - Cód. de Município IBGE: 2905701 1 - Tributacao no municipio\nMunicípio de  Natureza de \nPrestação: Operação:\nCodigo de tributacao Nacional NFS-e\nSI\nPIS  R$ 0,00 Valor do Serviço  R$ 91,20\nA\nR\nDesc. Condicionado  R$ 0,00\nE COFINS  R$ 0,00 Deduções  R$ 0,00\nD S\nE E L\nF INSS  ISS Retido  R$ 0,00 Desc. Incondicionado\n  R$ 0,00 R A R$ 0,00\nS O T\nE L O\nÕ IR  R$ 0,00 A T Valor Base Cálculo  R$ 0,00\nValor Líquido  R$ 91,20\nÇ V\nN\nE CSLL  R$ 0,00 Alíquota  0,00%\nT\nE\nR OUTRAS  R$ 0,00 Valor do ISS  R$ 0,00\nEmitido pela SISLOC - http://www.sisloc.com\nNFS-e gerada com a tecnologia NFS-e Easy® da Benefix - http://www.webenefix.com.br (21)-2621-5063'


def test_detect_layout_camacari_sisloc():
    dummy_path = "tests/dummy_camacari_sisloc.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_CAMACARI_SISLOC
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_camacari_sisloc_nfse_24052(monkeypatch):
    """PDF digital cujo `extract_text()` padrão embaralha rótulo/valor (todos
    os valores caem no fim do documento, fora de ordem) — este layout usa
    `_reconstruir_texto_por_coordenadas` para reconstruir o texto na ordem
    visual correta antes de qualquer extração de campo."""
    dummy_path = "tests/dummy_camacari_sisloc_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)
    monkeypatch.setattr(SPPdfExtractor, "_reconstruir_texto_por_coordenadas", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "24052"
        assert nfse.codigo_verificacao == "UB9X49JPT"
        assert nfse.servico_codigo == "0000"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "31/07/2026"
        assert nfse.competencia.strftime("%d/%m/%Y") == "31/07/2026"
        assert "LOCACAO DE MAQUINAS" in nfse.discriminacao

        p = nfse.prestador
        assert p.cnpj_cpf == "05100645000110"
        assert p.razao_social == "FERIMPORTE SERVICE LTDA"
        assert p.inscricao_municipal == "0012130001"
        assert p.endereco.municipio == "CAMAÇARI"
        assert p.endereco.uf == "BA"
        assert p.endereco.cep == "42802373"
        assert p.endereco.codigo_municipio == "2905701"

        t = nfse.tomador
        assert t.cnpj_cpf == "01813680000125"
        assert t.cnpj_cpf != p.cnpj_cpf
        assert t.razao_social == "DELTALINE SERVICOS LTDA"
        assert t.endereco.municipio == "SALVADOR"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "40330533"

        v = nfse.valores
        assert v.valor_servicos == pytest.approx(91.20)
        assert v.valor_liquido_nfse == pytest.approx(91.20)
        assert v.base_calculo == pytest.approx(91.20)
        assert v.aliquota == pytest.approx(0.0)
        assert v.valor_iss == pytest.approx(0.0)
        assert v.iss_retido is False
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
