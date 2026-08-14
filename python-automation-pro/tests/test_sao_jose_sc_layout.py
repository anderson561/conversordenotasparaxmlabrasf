# -*- coding: utf-8 -*-
r"""São José/SC (`sao_jose_sc`) - achado no pedido do usuário para criar o
layout depois que a nota real nº 348301 (INTELBRAS S/A - IND DE TEL ELET BRA,
CNPJ 82.901.000/0001-27, matriz em São José/SC -> SINDICATO DOS DELEGADOS DE
POLICIA, Salvador/BA, R$ 178,80) não tinha nenhum layout dedicado ainda.

Texto REAL extraído por pdfminer (`extract_text`) - PDF DIGITAL, sem OCR.
Preservado verbatim, incluindo 3 quirks que travam regressão:

1. **Canhoto/recibo do destinatário ANTES do conteúdo da nota, separado por
   uma linha de 200+ hifens**: sem tratamento, o `parse_multiple` fatiava
   esse preâmbulo ("Identificação e assinatura... do recebedor") como uma
   "nota" fantasma própria (nº 00000000, razão social = o próprio texto do
   canhoto) - corrigido descartando blocos de preâmbulo sem NENHUM sinal de
   nota quando `current_invoice` ainda está vazio.
2. **Blocos "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS" com reordenação
   própria**: razão social + nome fantasia vêm ANTES do bloco de 7 rótulos
   (Nome Fantasia/Nome-Razão Social/CPF-CNPJ/Endereço/Complemento/Município/
   E-mail); dos 5 valores restantes, o Município vem REALOCADO para o
   INÍCIO da sequência (ordem real: Município, CPF/CNPJ, Endereço[+
   Complemento], E-mail).
3. **CEP/UF do PRESTADOR saem deslocados para a janela logo após o
   cabeçalho "TOMADOR DE SERVIÇOS"** (artefato de leitura em 2 colunas do
   pdfminer) - sem isolar essa janela, o parser do tomador capturaria o
   CEP/UF do PRESTADOR como se fossem próprios.

Grade de valores também com ordem invertida (valores ANTES dos rótulos
"Quantidade/Valor Unitário/..."), ancorada no rótulo ESTÁVEL "Quantidade".
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_JOSE_SC

MOCK_TEXT = 'Data\n\nIdentificação e assinatura (eletrônica ou física) do recebedor:\n\n----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n\nPREFEITURA MUNICIAL DE SÃO JOSÉ\nSECRETARIA MUNICIPAL DA RECEITA\nNota Fiscal Eletrônica de Prestação de Serviços - NFES-e\n\nIdentificador\n83271301261209292908\n\nNúmero da Nota\n\n348301\n\nNúmero de RPS\n\n951524\n\nData de Emissão da Nota \n\n13/01/2026\n\nData do Fato Gerador\n\n13/01/2026\n\nCódigo de Verificação\n\n83271301261209292908\n\nPRESTADOR DE SERVIÇOS\n\nINTELBRAS S/A - IND DE TEL ELET BRA\n\nIntelbras Matriz\n\nNome Fantasia:\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nComplemento:\nMunicípio:\nE-mail:\n\nSão José\n\n82.901.000/0001-27\n\nRodovia BR 101\nKM 210\n\nsuporte@intelbras.com.br\n\nNúmero:\n\nSN\n\nBairro:\n\nDistrito Industrial\n\nTOMADOR DE SERVIÇOS\n\nCEP:\nUF:\n\n88104-800\nSC\n\nSINDICATO DOS DELEGADOS DE POLICIA\n\nSINDICATO DOS DELEGADOS DE POLICIA\n\nNome Fantasia:\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nComplemento:\nMunicípio:\nE-mail:\n\nSALVADOR\n\n73.393.696/0001-37\n\nR DIREITA DA PIEDADE\n\nadministrativo@adpeb.com.br\n\nNúmero:\n\n11\n\nBairro:\n\nBARRIS\n\nCEP:\n\n40070-190\n\nPaís:\nUF:\n\nBR\nBA\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nInscrição Municipal:\nInscrição Estadual:\nTelefone:\n\n(48) 3281-9500\n\n29454\n250082764\n\nInscrição Estadual:\nInscrição Municipal:\nTelefone:\n\n71999121315\n\nISENTO\n\nLIC SOFT CLOUD-STANDARD 36X\n\n12\n\n14,9\n\n178,80\n\n178,80\n\n2,00\n\n3,58\n\nQuantidade\n\nValor Unitário\n\nValor do Serviço\n\nBase de Cálculo\n\n( % )\n\nISS\n\nPIS/PASEP\n\n0\n\nCOFINS\n\n0\n\nRETENÇÕES FEDERAIS\nINSS\n\nIR\n\n0\n\n0\n\nValor bruto = R$ 178,8\n\nValor líquido = R$ 178,8\n\nCSLL\n\n0\n\nOutras Retenções\n\n0\n\n1.05 - Licenciamento ou cessão de direito de uso de programas de computação.\n\nDesc. Condicionado (R$)\n\nDesc. Incondicional (R$)\n\nDeduções (R$)\n\nBase de Cálculo\n\nValor ISS (R$)\n\n178,8\n\n3,58\n\nInformações Genéricas\n\nPedido: 00039421\n\nINFORMAÇÕES COMPLEMENTARES\n\nOUTRAS INFORMAÇÕES\n\n Valor aproximado dos tributos: Federal R$21.48 (12.00), Estadual R$0.00  (0.00),  Municipal R$0.00 (0.00), com base NA Lei \n12.741/2012 e NO Decreto 8.264/2014 - FONTE IBPT.   DATA de vencimento: 30/01/2026.  \nWIDE CLOUD 36 MESES  - SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA WIDE CLOUD 36 MESES  - SINDICATO \nDOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA ADPEB SINDICATO - 659255\n\nCódigo de verificação de Autenticidade\n\n8327130126120929290829010002026017634583\n\n\x0c'


def test_detect_layout_sao_jose_sc():
    dummy_path = "tests/dummy_sao_jose_sc.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_SAO_JOSE_SC
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_sao_jose_sc_nfse_348301(monkeypatch):
    """Antes: sem layout dedicado, a nota caía no genérico e o canhoto virava
    uma 2ª nota fantasma (nº 00000000). Depois: 1 nota só, todos os campos
    corretos, município do prestador resolvido para São José/SC (não o
    fallback de capital de SC, Florianópolis)."""
    dummy_path = "tests/dummy_sao_jose_sc_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        # Antes: 2 notas (canhoto fantasma + a real).
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "348301"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "13/01/2026"
        assert nfse.competencia.strftime("%d/%m/%Y") == "01/01/2026"
        assert nfse.codigo_verificacao == "83271301261209292908"
        assert nfse.servico_codigo == "0105"
        assert nfse.discriminacao == "LIC SOFT CLOUD-STANDARD 36X"
        assert nfse.avisos == []

        p = nfse.prestador
        assert p.cnpj_cpf == "82901000000127"
        assert p.razao_social == "INTELBRAS S/A - IND DE TEL ELET BRA"
        assert p.endereco.logradouro == "Rodovia BR 101"
        assert p.endereco.numero == "SN"
        assert p.endereco.bairro == "Distrito Industrial"
        # Antes do fix de city_hint: caía no fallback de capital de SC
        # (Florianópolis, 4205407) em vez de São José (4216602).
        assert p.endereco.codigo_municipio == "4216602"
        assert p.endereco.uf == "SC"
        assert p.endereco.cep == "88104800"

        t = nfse.tomador
        assert t.cnpj_cpf == "73393696000137"
        assert t.razao_social == "SINDICATO DOS DELEGADOS DE POLICIA"
        assert t.endereco.logradouro == "R DIREITA DA PIEDADE"
        assert t.endereco.numero == "11"
        assert t.endereco.bairro == "BARRIS"
        assert t.endereco.codigo_municipio == "2927408"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "40070190"

        v = nfse.valores
        assert v.valor_servicos == 178.8
        assert v.base_calculo == 178.8
        assert v.aliquota == 0.02
        assert v.valor_iss == 3.58
        assert v.valor_liquido_nfse == 178.8
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
