# -*- coding: utf-8 -*-
r"""WebISS / Prefeitura Municipal de Aracaju (achado real, nota 2026000000014,
LY5T-1DG5 - lote "Notas/072026"): mesma DANFSe Nacional (`LAYOUT_NACIONAL`),
mas com vocabulário PRÓPRIO desta plataforma - "Valor dos Serviços (R$)"
(plural, não "Valor do Serviço"), "Base de Cálculo ISS (R$)", "ISS (R$)",
"ISS Retido (R$)", "Alíquota ISS (%)", "PIS/COFINS/INSS/IR/CSLL (R$)" - e o
número da CÉLULA vem SEM o token "R$" (só o RÓTULO tem o sufixo "(R$)").

Antes deste fix, os padrões de `_extrair_valores()` para `LAYOUT_NACIONAL`
exigiam "R$ n,nn" logo após o rótulo (formato de outras plataformas, ex.:
Domínio Sistemas/Criciúma) - nenhum casava nesta nota, e Valor dos
Serviços/Valor Líquido/Base de Cálculo/Alíquota saíam todos zerados
("Valor dos serviços extraído como zero" no aviso), quando a nota real é de
R$ 4.000,00.

A própria prefeitura imprime "*****" (mascarado) no lugar de Base de
Cálculo ISS/ISS/ISS Retido (regime ME/EPP optante do Simples Nacional,
sem tributação municipal efetiva na nota) - não é falha de extração; o
valor correto é permanecer em 0.0 (nunca fabricar) e sinalizar via aviso
dedicado.

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original -
nunca digitado à mão.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT_ARACAJU = 'PREFEITURA MUNICIPAL DE ARACAJU\n\nSecretaria Municipal da Fazenda - SEMFAZ\nAdministração Tributária - Praça General Valadão, Nº 341 - Centro - CEP 49.010-520\n- Aracaju/SE Telefone: (79) 3179-1100\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e\n\nEmissão (Horário de Brasília)\n\n13/07/2026 17:32:45\n\nPeríodo de Competência\n\nMunicípio de Prestação do\n\n07/2026\n\nServiço\n\nSão Paulo - SP\n\nReg. Especial Tributação\n\nExigibilidade do ISS\n\nMicroempresário e Empresa de Pequeno Porte\n(ME EPP)\n\nExigível em\nAracaju\n\nPRESTADOR DE SERVIÇOS\nRazão Social\n\nLELIO FORTES NETO\n\nNome Fantasia\n\nLELIO FORTES ARQUITETURA\n\nEmail\n\nleliofortesarq@gmail.com\n\nCPF/CNPJ\n\nInscrição Municipal\n\nInscrição Estadual\n\nSimples Nacional\n\nIncentivador Cultural\n\nFone/Fax\n\n45.433.242/0001-07\n\n1357950\n\nSim\n\nNão\n\n(79) 99956-9987\n\nEndereço\n\nAVENIDA JORGE AMADO, 1565, SALA 04 e 06, Jardins - CEP: 49025-330 - Aracaju - SE\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social\n\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\nCPF/CNPJ\n\nInscrição Municipal\n\nInscrição Estadual\n\nFone/Fax\n\nE-mail\n\n16.699.869/0002-97\n\nEndereço\n\n(71) 3355-2526\n\nLORENA@NAUTICAMOVEIS.COM\n\nAlameda Gabriel Monteiro da Silva, 1480, CASA TERREA - Jardim América - CEP: 01442-001 - São Paulo - SP\n\nSERVIÇO PRESTADO\n0701 - Engenharia, agronomia, agrimensura, arquitetura, geologia, urbanismo, paisagismo e congêneres. CNAE: 7111100. NBS: 114021100.\n\nDESCRIÇÃO DOS SERVIÇOS\nPrestação de serviço de especificação em projeto.\n\nRETENÇÕES FEDERAIS\n\nPIS (R$)\n\n0,00\n\nCOFINS (R$)\n\n0,00\n\nINSS (R$)\n\n0,00\n\nIR (R$)\n\n0,00\n\nCSLL (R$)\n\n0,00\n\nVALORES\n\nDeduções (R$)\n\nDesc. Cond. (R$)\n\nDesc. Incond. (R$)\n\nBase de Cálculo ISS (R$)\n\nOutras Retenções (R$)\n\n0,00\n\nAlíquota ISS (%)\n\n5,0000\n\n0,00\n\nValor dos Serviços (R$)\n\n4.000,00\n\n0,00\n\nISS (R$)\n\n*****\n\n0,00\n\n*****\n\nISS Retido (R$)\n\nValor Líquido (R$)\n\nValor Total da Nota (R$)\n\n*****\n\n4.000,00\n\n4.000,00\n\nOUTRAS INFORMAÇÕES\nOptante do Simples Nacional.\nTrib. aprox. R$ 538,00 Federal e R$ 200,00 Municipal. Fonte: IBPT [92589A]\nChave de Acesso da NFS-e Nacional: 28003081245433242000107202600000001426071185813466\n\nVisualizado em: 13/07/2026 17:32:45 | Para validação desta NFSe acesse: http://aracajuse.webiss.com.br/externo/nfse/validar\nEsta NFS-e é autodeclaratória. Esta NFS-e foi emitida com respaldo no Decreto nº 3.393 de 14 de março de 2011.\n\n\x0c'


def test_danfse_nacional_aracaju_extrai_valor_dos_servicos_sem_token_rs(monkeypatch):
    """Nota real 2026000000014 (LELIO FORTES ARQUITETURA -> NAUTICA INDUSTRIA
    E COMERCIO DE MOVEIS, WebISS/Aracaju): Valor dos Serviços = R$ 4.000,00,
    Alíquota ISS = 5%. Antes do fix, `valor_servicos`/`valor_liquido_nfse`/
    `base_calculo`/`aliquota` saíam todos 0.0."""
    dummy_path = "tests/dummy_danfse_aracaju_webiss.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_ARACAJU)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        assert extractor.layout == "danfse_nacional"

        v = nfse.valores
        assert v.valor_servicos == pytest.approx(4000.00)
        assert v.valor_liquido_nfse == pytest.approx(4000.00)
        assert v.aliquota == pytest.approx(0.05)
        # Base de Cálculo ISS vem mascarada ("*****") no documento fonte -
        # sem número real para extrair, cai no fallback já estabelecido
        # (base_calculo = valor_servicos) em vez de fabricar um valor.
        assert v.base_calculo == pytest.approx(4000.00)
        # ISS e ISS Retido também mascarados ("*****") - nunca fabricar,
        # ficam em 0.0.
        assert v.valor_iss == pytest.approx(0.0)
        assert v.iss_retido is False
        # RETENÇÕES FEDERAIS (PIS/COFINS/INSS/IR/CSLL) e Deduções: 0,00 reais
        # nesta nota.
        assert v.valor_pis == pytest.approx(0.0)
        assert v.valor_cofins == pytest.approx(0.0)
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_ir == pytest.approx(0.0)
        assert v.valor_csll == pytest.approx(0.0)

        assert "Valor dos serviços extraído como zero" not in nfse.avisos
        assert any("mascara" in a for a in nfse.avisos)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
