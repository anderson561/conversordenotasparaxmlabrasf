# -*- coding: utf-8 -*-
"""Cuiabá/MT (ISSNet) escaneado — nota inteira sumindo do resultado por causa
de uma heurística compartilhada (`parse_multiple`/`is_new_invoice`, usada por
TODOS os layouts, não só Cuiabá).

Achado real (PDF "NFS PRESTADORES ANALISE DE NFS-iss e inss retido", págs.
1-3): a heurística que decide se um bloco de texto é uma nota nova ou
continuação da anterior usava a regex genérica `(?:Número|Nº).*?(\\d+)` para
comparar "números" entre blocos. Quando a caixa real "Número da Nota Fiscal"
sai ilegível no OCR (nota nº 10, pág. 3), essa regex cai no PRÓXIMO "Número"
do texto — o do ENDEREÇO do tomador ("Avenida Praia de Pajussara Número:
554"), que é o MESMO em toda nota que vai para o mesmo tomador (São Pedro
Construtora, endereço fixo). Como as págs. 2 e 3 batem nesse "554" repetido,
eram tratadas como CONTINUAÇÃO da nota da pág. 1 em vez de notas novas — a
nota nº 10 nunca virava um XML próprio, ficava silenciosamente engolida.

Corrigido com `_numero_heuristico_bloco`: tenta primeiro rótulos específicos
de "número da nota" e, no fallback genérico, pula ocorrências de "Número"
cuja linha contém "Endereço" (a armadilha). Este teste usa o OCR REAL das
3 primeiras páginas do PDF (nota 3641 -> nota 284 -> nota nº 10/DR3
Terceirização) para confirmar que as 3 viram notas SEPARADAS."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

PAGINA_1 = 'Série do Documento\nvil) Nota Fiscal de Serviço\nEletrônica - NFS-e\n\nNúmero da Nota Fiscal\n3641\n\nData de Geração da NFS-e\n06/04/2026 10:07:09\nData de Competência\n06/04/2026\nCód. de Autenticidade\nD29A7D2C0\n\nResponsável pela Retenção\n\nPrefeitura Municipal de Cuiabá\nSecretaria Municipal de Economia\n\nFone: () - http:/Awww.cuiaba.mt.gov.br/\n\nDados do Prestador de Serviço\n\nD.A.S. MALDONADO ME\nESTRUTEC ENGENHARIA\nAvenida Fernando Correa da Costa,8100 FUNDOS B - São José\nCEP 78080-535 - Fone: (65)3023-9382 - Cuiabá/ MT\narielDestrutecmt.com.br\n\nInscrição Municipal 133315 - CPF/CNPJ 19.645.093/0001-30\n\nIdentificação da Nota Fiscal Eletrônica\nNatureza da Operação Número do RPS Série do RPS\nEE\nLocal dos Serviços Município Incidência\n\nCuiabá - Mao Grosso\n\nDados do Tomador de Serviços\n\nCNPJICPF:  03.051.741/0001-90 IM: 1492591\n\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : (71)3272-0733 E-mail : sp(Qsaopedroconstrutora.com.br\n\nData de Emissão do RPS\n\nDados do Intermediário de Serviços\nCNPJICPF Inscrição Municipal Razão Social\n\nDescrição dos Serviços\n60 Moldagem de corpo e prova 10 x 20 cm em HORA NORMAL: das 07:00h às 18:00h.: R$ 780,00\n\n48 Ensaio de Compressão Axial de Corpo de Prova de Concreto: R$ 528,00\n04 Mobilização e Coletas de Cps : R$ 320,00\n\nDetalhamento dos Tributos\nAtividade do Município\n\n7112000 - [7112-0/00] Serviços de engenharia -\n\nCod. CNAE\n7112000\n\nAlíquota [itemdaLC116/2003 [Cód NES\n5,00 | 1709 114044200\n\nVI. Total dos Serviços | Desconto Incondicionado [Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\nR$ 1.628,00 R$ 0,00 R$ 976,80 R$ 651,20 R$ 32,56 | Não R$ 0,00\nPIS Outras Retenções Vi. ISSQN Retido [VI. Líquido da Nota Fiscal\n\nR$ 1.556,37\n\nR$ 0,00 R$ 0,00\n\nCOFINS INSS IRRF SIL\nR$ 0,00 R$71,63] R$0,00 | R$0,00\n\nConstrução Civil Cód. Obra :\n'

PAGINA_2 = 'Prefeitura Municipal de Cuiabá\nSecretaria Municipal de Economia\nFone: () - http:/Awww.cuiaba.mt.gov.br/\n\n284\n\nDados do Prestador de Serviço\n\nData de Geração da NFS-e\n\n04/04/2026 14:31:56\n\nData de Competência\n04/04/2026\n\nCód. de Autenticidade\n816B55321\n\nResponsável pela Retenção\n\nISRAEL DE OLIVEIRA FILHO & CIA LTDA\nPERFIL | ENGENHARIA DE ESTRUTURAS\n\nRua D,0 QUADRACOM.2/2 LOTE 05A12/23A34 - Distrito Industrial\nCEP 78098-300 - Fone: (65)8109-5900 - Cuiabá/ MT\n\nfinanceiroDperfilicom.br\nInscrição Municipal 197851 - CPF/CNPJ 36.693.198/0001-83\n\nIdentificação da Nota Fiscal Eletrônica\n\nNatureza da Operação Número do RPS Série do RPS\nExigível\n\nLocal dos Serviços\nCuiabá - Mato Grosso\n\nData de Emissão do RPS\n\nMunicípio Incidência\nCuiabá - Mato Grosso\n\nDados do Tomador de Serviços\n\nCNPJ/CPF : 03.051.741/0001-90 IM : 1492591\n\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : (71)3272-0733 E-mail : sp(saopedroconstrutora.com.br\nDados do Intermediário de Serviços\n\nCNPJ/CPF Inscrição Municipal Razão Social\n\nDescrição dos Serviços\n\nMão de obra de fabricação e montagem de estruturas\nReferente a medição 12 de 01/04/2026\nCNO 90.018.32011/78\n\nDados Bancários: Favorecido: Israel de Oliveira Filho & Cia Ltda - 756 - Banco Sicoob - Agência: 3325 - Conta:106.743-5 - CNPJ/PIX: 36.693.198/0001-83\n\nDetalhamento dos Tributos\nMeo Tem da LC716/2003  [Cód. NBS Cód. CNAE\n2542000 - [2542-0/00] Fabricação de artigos de serralheria, e... 5,00 | 1413 101075000 | 2542000\nVI. Total dos Serviços |Desconto Incondicionado  |Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado 7]\nR$ 1.275,86 | Não R$ 0,00\n\nVI. Líquido da Nota Fiscal\n\nR$ 25.517,16 |\n\nVI. ISSQN Retido\nR$ 0,00\n\nR$ 25.517,16 R$ 0,00\nPIS COFINS\n\nR$ 0,00 R$ 0,00\nConstrução Civil\n\nOutras Retenções\nR$ 0,00\nArt.:\n'

PAGINA_3 = 'Série do Documento\nNota Fiscal de Serviço\nEletrônica - NFS-e\n\nPrefeitura Municipal de Cuiabá\nSecretaria Municipal de Economia\nFone: () - http:/Awww.cuiaba.mt.gov.br/\n\nDados do Prestador de Serviço\n\nData de Geração da NFS-e\n\n06/04/2026 19:49:51\n\nData de Competência\n06/04/2026\n\nCód. de Autenticidade\n\nE320F124C\n\nResponsável pela Retenção\n\nNatureza da Operação Número do RPS Série do RPS Data de Emissão do RPS\n\nEE ER E E RO\nLocal dos Serviços Município Incidência\n\nCNPJICPF:  03.051.741/0001-90 IM: 1492591\n\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : OD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : (71)3272-0733 E-mail : sp(Osaopedroconstrutora.com.br\n\nDados do Intermediário de Serviços\n\nCNPJICPF Inscrição Municipal Razão Social\n\nDR3 TERCEIRIZACAO LTDA\n\nDR3 TERCEIRIZACAO\n\nRua Brigadeiro Eduardo Gomes,86 SALA: 105; - Goiabeira\nCEP 78032-030 - Fone: (65)99206-9540 - Cuiabá/ MT\n\ngenesisassessoria26(Ogmail.com\nInscrição Municipal 321599 - CPF/CNPJ 62.981.187/0001-09\n\nDescrição dos Serviços\nREJUNTAMENTO EXTERNO RAMPA DE ACESSO, ESPELHO D\'ÁGUA,FACHADA ,LIMPEZA INTERNA: REVESTIMENTOS (inclusão de banheiros e piso)\nDADOS BANCARIOS\n\nNome: DR3 TERCEIRIZAÇÃO\n\nRenata Lourenço do Nascimento\n\nBanco: C6 Chave Pix CNPJ 62981187000109\n\nDetalhamento dos Tributos\n\nAtividade do Município Cód. CNAE\n\n8121400 - [8121-4/00] Limpeza em prédios e em domicílios - 2,00 118031000 | 8121400\nVI. Total dos Serviços | Desconto Incondicionado  |Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\nR$ 22.709,56 R$ 0,00 R$ 0,00 R$ 454,19 | Não R$ 0,00\nPIS COFINS INSS IRRF CSLL Outras Retenções (Vi. ISSQN Retido [VI. Líquido da Nota Fiscal\nRs 0,00 R$ 000 RS 22.709,56\nConstrução Civil Cód. Obra : Art:\n'

MOCK_OCR = PAGINA_1 + "\n\x0c\n" + PAGINA_2 + "\n\x0c\n" + PAGINA_3


def test_paginas_nao_ficam_grudadas_pelo_endereco_do_tomador(monkeypatch):
    dummy_path = "tests/dummy_cuiaba_invoice_split.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()

        # Antes do fix: as 3 páginas viravam 1 nota só (2 e 3 engolidas pela
        # 1, todas com "Número: 554" do endereço do tomador em comum).
        assert len(nfse_list) == 3

        numeros = {nf.numero for nf in nfse_list}
        assert "3641" in numeros
        assert "284" in numeros

        # A nota da página 3 (DR3 Terceirização) tem que existir como
        # entrada própria, mesmo sem número recuperável.
        pagina3 = next(nf for nf in nfse_list if nf.pagina_origem == 3)
        assert pagina3.prestador.cnpj_cpf == "62981187000109"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
