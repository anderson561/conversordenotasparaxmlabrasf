# -*- coding: utf-8 -*-
"""Cuiabá/MT (ISSNet) escaneado — dígito espúrio isolado ENTRE o rótulo
"Número da Nota Fiscal" e o número real, no formato de rótulo limpo.

Achado real (PDF "NFS PRESTADORES MTI 03-2026", pág.10, RC CONSTRUÇÕES
ELÉTRICAS -> São Pedro, número real confirmado pela imagem: **205**): o OCR
intercala um dígito isolado numa linha própria entre o rótulo e o valor —
"Número da Nota Fiscal\n5\n205\n" — o "5" é ruído (glifo espúrio), "205" é o
número de verdade. O padrão antigo (rótulo seguido do primeiro grupo de dígitos)
pega o PRIMEIRO grupo de dígitos após o rótulo, ou seja, o "5" errado —
saía numero="5" com aviso nenhum (parecia um resultado válido).

Corrigido: captura até 3 grupos de dígitos logo após o rótulo (cada um
podendo estar em sua própria linha) e fica com o MAIS LONGO — um ruído de
1 dígito nunca vence o número real ao lado. Quando só há um candidato
(formato limpo normal, sem ruído), o comportamento não muda."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'Número da Nota Fiscal\n5\n205\n\nSérie do Documento\n\nPrefeitura Municipal de Cuiabá (|| Nota Fiscal de Servi\nSecretaria Municipal de Economia NOTA Eletrônica - NES\nFone: () - http:/Iwww.cuiaba.mt.gov.br/ CUIABANA\n\nDados do Prestador de Serviço " pe\nData de Geração da NFS-e\n01/04/2026 17:20:05\n\nRC CONSTRUCOES ELETRICAS LTDA\nRC CONSTRUCOES ELETRICAS\n\nRua Primeiro de Maio,40 SALA B - Vista Alegre\nCEP 78085-705 - Fone: (65)3628-1623 - Cuiabá/ MT\n\nData de Competência\n01/04/2026\nreinstalacoes (hotmail.com 09303F3E7\nInscrição Municipal 127131 - CPF/CNPJ 17.196.107/0001-50\n\nIdentificação da Nota Fiscal Eletrônica\nNúmero do RPS Série do RPS Data de Emissão do RPS\nDados do Tomador de Serviços\n\nCNPJ/CPF : 03.051.741/0001-90 IM : 1492591\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : 71)3272-0733 E-mail : sp(Dsaopedroconstrutora.com.br\n\nDados do Intermediário de Serviços\n\nInscrição Municipal Razão Social\n\nDescrição dos Serviços\n\nFornecimento de material e mão de obra\n\nespecializada para execução de extensão de rede de média tensão, para a obra: MTI\nCENTRO POLÍTICO ADMINISTRATIVO, CUIABÁ/MT RUA 3 QUADRA 11 SETOR A\nSC- 78049060, Cuiabá — MT\n\nValor referente a 3º Medição\nValor referente aos materiais (60%) = R$ 10.773,00\nValor referente a mão de obra (40%) = R$ 7.182,00\n\nDados Bancários\n\nFavorecida: RC Construções Elétricas LTDA\n\nCNPJ: 17.196.107/0001-50\n\nBanco: 748 - Banco Cooperativo Sicredi S.A. — Bansicredi\n\nAgência: 0810\n\nConta: 08768-5\n\nChave pix (email): re.construcoeseletricasitda(Dgmail.com\n\nDetalhamento dos Tributos\nAtividade do Município Aliquota [hem da LC116/2003\n4321500 - [4321-5/00] Instalação e manutenção elétrica - 702 101061100 | 4321500\nVI. Total dos Serviços [Desconto Incondicionado [Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\n\nR$ 17.955,00 R$ 0,00 R$ 10.773,00 R$ 7.182,00 R$ 330,37 | Não R$ 0,00\nPIS COFINS INSS IRRF CSLL Outras Retenções VI ISSQN Retido  |Vi. Líquido da Nota Fiscal\nR$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 | R$ 0,00 R$ 0,00 R$ 0,00 R$ 17.955,00\n\nConstrução Civil Cód. Obra : mi: A\n'


def test_numero_ignora_digito_espurio_entre_rotulo_e_valor(monkeypatch):
    dummy_path = "tests/dummy_cuiaba_numero_espurio.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "205"
        assert nfse.numero != "5"
        assert "Número da nota não encontrado" not in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
