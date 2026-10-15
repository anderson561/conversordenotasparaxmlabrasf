# -*- coding: utf-8 -*-
r"""São Paulo/SP digital (LAYOUT_SAO_PAULO) - template com a ordem de texto do
pdfminer DESLOCADA (rótulos e valores em ordens diferentes por nota) e o
endereço impresso em UMA linha. Seis defeitos de uma mesma família, achados
nas notas reais FLASH nº 05710445/05710815 (FLASH TECNOLOGIA -> TEMIS) e na
nota nº 01223660 (cartório -> NAUTICA), todos conferidos contra a imagem
renderizada das páginas:

 1. Tomador `RazaoSocial` saía "Salvador" (o município) / "São Paulo";
 2. endereço de Prestador e Tomador saía "Não informado"/S/N (só o CEP);
 3. Prestador saía UF=BA/2927408 (Salvador) mesmo imprimindo "São Paulo/SP";
 4. Alíquota impressa 2,00% saía 0.00 e, na nota 01223660, Deduções/Base/ISS
    saíam trocados (Deduções=367,40, Base=2,00, ISS=2,00; o impresso é
    193,65 / 367,40 / 7,34);
 5. Competência = mês da emissão (02/10/2026) embora o RPS e a "Data da
    Compra" sejam de 30/09/2026;
 6. Discriminação começava com "DE SERVIÇOS" (o cabeçalho "DISCRIMINAÇÃO DE
    SERVIÇOS" cortado pela metade).

Os textos são o retorno REAL e verbatim de `pdfminer.high_level.extract_text()`
nos PDFs reais (já com o `\x0c` entre as 2 páginas; a 2ª é o anexo IBS/CBS).
Na nota 01223660 o CPF do prestador e o e-mail do tomador foram trocados por
valores sintéticos (dados pessoais); o resto é verbatim.
"""
import os
from datetime import datetime

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO

NOTA_FLASH_05710445 = 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\nRPS Nº 4159843 Série NFSE2, emitido em 30/09/2026\n\nNúmero da Nota\n\n05710445\nData e Hora de Emissão\n02/10/2026 04:25:42\nCódigo de Verificação\nGZCS-2BDP\n\nIdentificador Nacional: 35503081232223020000118000000571044526101399600678\n\n20261002u32223020000118\n\nPRESTADOR DE SERVIÇOS\n\nInscrição Municipal:\n\n6.141.672-0\n\n32.223.020/0001-18\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nMunicípio: São Paulo\n\nFLASH TECNOLOGIA E  INSTITUICAO DE PAGAMENTO LTDA\n\nR EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000\nUF: SP\n\nTOMADOR DE SERVIÇOS\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nMunicípio:\n\n07.345.543/0001-90\n\nR T R TERRITORIO DO AMAPA 146, Casa 2 - PITUBA - CEP: 41830-540\nSalvador\n\nE-mail:\n\nUF:\n\nBA\n\nfinanceiro@temis-es.com.br\n\nInscrição Municipal:\n\n----\n\nCPF/CNPJ:\n\n----\n\nNome/Razão Social:\n\n----\n\nINTERMEDIÁRIO DE SERVIÇOS\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nValor Total - R$ 1.113,00\nCompra de Créditos na Plataforma Flash - R$ 1.113,00\nValor total de serviços Flash - R$ 0,00\nData da Compra: 30/09/2026\n\nCompra de benefícios - Auxilio Alimentação e Refeição: R$ 877,00 (1 depósito)\nCompra de benefícios - Auxilio Mobilidade: R$ 236,00 (1 depósito)\n\nContrato 5y6p1Uko4RlaWv1h0qrTg\n\nAutorização de Regime especial - SEI 6017.2019/0041453-7\nO ISS incide apenas sobre o valor de serviços Flash indicado acima\nLocal da prestação de serviços: São Paulo - SP\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\nVALOR TOTAL RECEBIDO = R$ 1.113,00\n\nContribuição Previdenciária - Retida (R$)\n\nIRRF (R$)\n\nCOFINS (R$)\n\nPIS/PASEP (R$)\n\nIPI (R$)\n\nContribuições Sociais - Retidas (R$)\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nDescrição Contribuições Sociais - Retidas\n\n0 - PIS/COFINS/CSLL Não Retidos.\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$)\n0,00\n\nMunicípio de Prestação do Serviço\n-\n\n0,00\n\n2,00%\n\nNúmero Inscrição da Obra\n-\n\nBase de Cálculo (R$)\n\nAlíquota (%)\n\nValor do ISS (R$)\n\nCrédito Programa da NFP (R$)\n0,00\n\n0,00\n\nValor Aproximado dos Tributos / Fonte\n-\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 4159843 Série NFSE2, emitido em 30/09/2026; (3) O\nISS relativo a esta NFS-e deverá ser recolhido de acordo com as regras da DES-IF, mediante o envio da declaração e a posterior emissão da respectiva\nguia de pagamento por meio do sistema da DES-IF.;\n\nPágina 1 de 2\n\n\x0cIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081232223020000118000000571044526101399600678\n\nCPF/CNPJ/NIF do Fornecedor\n32.223.020/0001-18\n\nNÃO INFORMADO\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\n----\n\n----\n\n----\n\nE-mail:\n\n----\n\nNúmero da Nota\n05710445\n\nDESTINATÁRIO\n\nNIF:\n\n----\n\nNº:\n\n----\n\nCompl.:\n\n--\n\nCódigo de Verificação\nGZCS-2BDP\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nADQUIRENTE\n\nNIF:\n\nMunicípio:\n\n----\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\n07.345.543/0001-90\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\nPITUBA\n\nR T R TERRITORIO DO AMAPA\n\nMunicípio:\n\n2927408 - Salvador - BA\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nE-mail:\n\nNº:\nfinanceiro@temis-es.com.br\n\n146\n\nCompl.:\n\nCasa 2\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nSERVIÇO PRESTADO\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nCEP:\n\n41830-540\n\nCEP:\n\n----\n\nLocal de prestação:\n\n2927408 - Salvador - BA\n\nCódigo indicador da operação:\n\n100301\n\nLocalidade de incidência:\n\n2927408 - Salvador - BA\n\nTipo de operação:\n\n5-Fornecimento e recebimento do pagamento concomitantes.\n\nOperação de uso:\n\nNão\n\nSituação tributária:\n\n000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nOUTRAS CLASSIFICAÇÕES\n\nNBS:\n\n114012100 - Serviços de gestão em processos de negócios \n\nNCM:\n\n----\n\nValor da multa (R$)\n-\n\nValor do juros (R$)\n-\n\nValor das Deduções\n\nBase de Cálculo do\n\nAlíquota Estadual do\n\nAlíquota Municipal\n\nRedução de Alíquota\n\nAlíquota Efetiva do\n\nValor Diferido do IBS\n\nValor do IBS (R$)\n\nde IBS e CBS (R$)\n\nIBS e CBS (R$)\n\nIBS (%)\n0,10%\n\ndo IBS (%)\n0,00%\n\ndo IBS (%)\n0,00%\n\nIBS (%)\n0,10%\n\n(R$)\n-\n\n0,00\n\n1.113,00\n\n0,00\n\nAlíquota da CBS (%)\n\nRedução de Alíquota\n\nAlíquota Efetiva da\n\nValor Diferido da\n\nValor da CBS (R$)\n\n0,90%\n\nda CBS (%)\n0,00%\n\nCBS (%)\n0,90%\n\nCBS (R$)\n0,00\n\n0,00\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nVALOR TOTAL COBRADO =  R$ 1.113,00\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n\n\x0c'

NOTA_FLASH_05710815 = 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\nRPS Nº 4160219 Série NFSE2, emitido em 30/09/2026\n\nNúmero da Nota\n\n05710815\nData e Hora de Emissão\n02/10/2026 04:29:30\nCódigo de Verificação\nWNUW-RAQE\n\nIdentificador Nacional: 35503081232223020000118000000571081526100060387227\n\n20261002u32223020000118\n\nPRESTADOR DE SERVIÇOS\n\nInscrição Municipal:\n\n6.141.672-0\n\n32.223.020/0001-18\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nMunicípio: São Paulo\n\nFLASH TECNOLOGIA E  INSTITUICAO DE PAGAMENTO LTDA\n\nR EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000\nUF: SP\n\nTOMADOR DE SERVIÇOS\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nMunicípio:\n\n07.345.543/0001-90\n\nR T R TERRITORIO DO AMAPA 146, Casa 2 - PITUBA - CEP: 41830-540\nSalvador\n\nE-mail:\n\nUF:\n\nBA\n\nfinanceiro@temis-es.com.br\n\nInscrição Municipal:\n\n----\n\nCPF/CNPJ:\n\n----\n\nNome/Razão Social:\n\n----\n\nINTERMEDIÁRIO DE SERVIÇOS\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nValor Total - R$ 20.853,30\nCompra de Créditos na Plataforma Flash - R$ 20.853,30\nValor total de serviços Flash - R$ 0,00\nData da Compra: 30/09/2026\n\nCompra de benefícios - Auxilio Mobilidade: R$ 4.979,60 (22 depósitos)\nCompra de benefícios - Auxilio Alimentação e Refeição: R$ 15.873,70 (19 depósitos)\n\nContrato BOUbrnWLrYv6uMUQ90MV5\n\nAutorização de Regime especial - SEI 6017.2019/0041453-7\nO ISS incide apenas sobre o valor de serviços Flash indicado acima\nLocal da prestação de serviços: São Paulo - SP\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\nVALOR TOTAL RECEBIDO = R$ 20.853,30\n\nContribuição Previdenciária - Retida (R$)\n\nIRRF (R$)\n\nCOFINS (R$)\n\nPIS/PASEP (R$)\n\nIPI (R$)\n\nContribuições Sociais - Retidas (R$)\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nDescrição Contribuições Sociais - Retidas\n\n0 - PIS/COFINS/CSLL Não Retidos.\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$)\n0,00\n\nMunicípio de Prestação do Serviço\n-\n\n0,00\n\n2,00%\n\nNúmero Inscrição da Obra\n-\n\nBase de Cálculo (R$)\n\nAlíquota (%)\n\nValor do ISS (R$)\n\nCrédito Programa da NFP (R$)\n0,00\n\n0,00\n\nValor Aproximado dos Tributos / Fonte\n-\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 4160219 Série NFSE2, emitido em 30/09/2026; (3) O\nISS relativo a esta NFS-e deverá ser recolhido de acordo com as regras da DES-IF, mediante o envio da declaração e a posterior emissão da respectiva\nguia de pagamento por meio do sistema da DES-IF.;\n\nPágina 1 de 2\n\n\x0cIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081232223020000118000000571081526100060387227\n\nCPF/CNPJ/NIF do Fornecedor\n32.223.020/0001-18\n\nNÃO INFORMADO\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\n----\n\n----\n\n----\n\nE-mail:\n\n----\n\nNúmero da Nota\n05710815\n\nDESTINATÁRIO\n\nNIF:\n\n----\n\nNº:\n\n----\n\nCompl.:\n\n--\n\nCódigo de Verificação\nWNUW-RAQE\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nADQUIRENTE\n\nNIF:\n\nMunicípio:\n\n----\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\n07.345.543/0001-90\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\nPITUBA\n\nR T R TERRITORIO DO AMAPA\n\nMunicípio:\n\n2927408 - Salvador - BA\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nE-mail:\n\nNº:\nfinanceiro@temis-es.com.br\n\n146\n\nCompl.:\n\nCasa 2\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nSERVIÇO PRESTADO\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nCEP:\n\n41830-540\n\nCEP:\n\n----\n\nLocal de prestação:\n\n2927408 - Salvador - BA\n\nCódigo indicador da operação:\n\n100301\n\nLocalidade de incidência:\n\n2927408 - Salvador - BA\n\nTipo de operação:\n\n5-Fornecimento e recebimento do pagamento concomitantes.\n\nOperação de uso:\n\nNão\n\nSituação tributária:\n\n000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nOUTRAS CLASSIFICAÇÕES\n\nNBS:\n\n114012100 - Serviços de gestão em processos de negócios \n\nNCM:\n\n----\n\nValor da multa (R$)\n-\n\nValor do juros (R$)\n-\n\nValor das Deduções\n\nBase de Cálculo do\n\nAlíquota Estadual do\n\nAlíquota Municipal\n\nRedução de Alíquota\n\nAlíquota Efetiva do\n\nValor Diferido do IBS\n\nValor do IBS (R$)\n\nde IBS e CBS (R$)\n\nIBS e CBS (R$)\n\nIBS (%)\n0,10%\n\ndo IBS (%)\n0,00%\n\ndo IBS (%)\n0,00%\n\nIBS (%)\n0,10%\n\n(R$)\n-\n\n0,00\n\n20.853,30\n\n0,00\n\nAlíquota da CBS (%)\n\nRedução de Alíquota\n\nAlíquota Efetiva da\n\nValor Diferido da\n\nValor da CBS (R$)\n\n0,90%\n\nda CBS (%)\n0,00%\n\nCBS (%)\n0,90%\n\nCBS (R$)\n0,00\n\n0,00\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nVALOR TOTAL COBRADO =  R$ 20.853,30\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n\n\x0c'

NOTA_CARTORIO_01223660 = 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\nRPS Nº 6001296 Série PT, emitido em 03/09/2026\n\nNúmero da Nota\n\n01223660\nData e Hora de Emissão\n09/09/2026 11:01:24\nCódigo de Verificação\nMEJW-RXMS\n\n20261014u02399587723\n\nIdentificador Nacional: 35503081102399587723000000122366026095177728055\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nMunicípio: São Paulo\n\n111.444.777-35\n\nInscrição Municipal:\nRICARDO RAGE FERRO - 6 TABELIAO DE PROTESTO DE LETRAS E TITUL\n\n7.898.196-4\n\nR SILVIA 110, ANDAR 6 - BELA VISTA - CEP: 01331-902\n\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nMunicípio:\n\n16.699.869/0002-97\n\nAL GABRIEL MONTEIRO DA SILVA 1480, CASA  TERREA - JARDIM AMERICA - CEP: 01442-001\ncontato@exemplo.com.br\nSão Paulo\n\nE-mail:\n\nUF:\n\nSP\n\nUF: SP\n\nInscrição Municipal:\n\n7.187.046-6\n\nCPF/CNPJ:\n\n----\n\nNome/Razão Social:\n\n----\n\nINTERMEDIÁRIO DE SERVIÇOS\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nO valor desta nota refere-se aos emolumentos e contribuições (Taxa - STF - Representação 1094-5 SP e ADIN\n1444-7 PR),calculados de acordo com a Lei Estadual nº 11.331/02, art. 19, com a redação pela Lei nº\n15.600/2014, Lei nº 15.855/2015 e Lei nº 16.346/2016, RECEBIDOS pelo(s) seguinte(s) ato(s) praticado(s) por\nRICARDO RAGE FERRO 6º TABELIÃO DE PROTESTO DE SÃO PAULO - CNPJ: 52.751.994/0001-81:\n\n1 PAGAMENTO Protocolo nº 3378 - 31/08/2026\n\nDiscriminação dos valores RECEBIDOS:\nEmolumentos: R$ 317,47\nSecretaria Da Fazenda: R$ 61,75\nEstado: R$ 90,23\nSinoreg (Custeio Atos Gratuitos do Registro Civil): R$ 16,71\nFundo Especial Despesas Tribunal Justiça: R$ 21,79\nContribuição Santa Casa de Misericórdia: R$ 3,17\nImposto Municipal: R$ 7,34\nMinistério Público R$ 15,24\nIntimação: R$ 27,35\nValor Total PAGO: R$ 561,05\n\nATENÇÃO: Conforme consulta nº 21 de 21/01/2014, da Coordenação-Geral de Tributação (Cosit) da SRF, OS VALORES\nDESCRITOS NESTA NOTA NÃO ESTÃO SUJEITOS AS RETENÇÕES de 11% prevista no art. 4º da Lei nº 10.666/2003, com a\nredação dada pela Lei nº 11.933/2009 e 20% de contribuições previdenciárias ao INSS, inciso III do art. 22 da\nLei nº 8.212/91.\n\nVALOR TOTAL DO SERVIÇO = R$ 561,05\n\nContribuição Previdenciária - Retida (R$)\n\nIRRF (R$)\n\nCOFINS (R$)\n\nPIS/PASEP (R$)\n\nIPI (R$)\n\nContribuições Sociais - Retidas (R$)\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nDescrição Contribuições Sociais - Retidas\n-\n\nCódigo do Serviço\n03877 - Serv Registros Públicos/Cartorários/Notariais exceto autent documentos, reconhec firmas e prest inf\n\nValor Total das Deduções (R$)\n193,65\n\nBase de Cálculo (R$)\n\nAlíquota (%)\n\nValor do ISS (R$)\n\n367,40\n\n2,00%\n\nCrédito Programa da NFP (R$)\n0,00\n\n7,34\n\nMunicípio de Prestação do Serviço\n-\n\nNúmero Inscrição da Obra\n-\n\nValor Aproximado dos Tributos / Fonte\n-\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e não gera crédito no Programa da Nota Fiscal Paulistana; (3) Esta NFS-e\nsubstitui o RPS Nº 6001296 Série PT, emitido em 03/09/2026; (4) NFS-e quitada em 07/10/2026;\n\nPágina 1 de 2\n\n\x0cIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081102399587723000000122366026095177728055\n\nCPF/CNPJ/NIF do Fornecedor\n111.444.777-35\n\nNÃO INFORMADO\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\n----\n\n----\n\n----\n\nE-mail:\n\n----\n\nNúmero da Nota\n01223660\n\nDESTINATÁRIO\n\nNIF:\n\n----\n\nNº:\n\n----\n\nCompl.:\n\n--\n\nCódigo de Verificação\nMEJW-RXMS\n\nMunicípio:\n\n----\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\n16.699.869/0002-97\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\nJARDIM AMERICA\n\nAL GABRIEL MONTEIRO DA SILVA, 1480\n\nNAUTICA IND E COM DE MOVEIS E SERV LTDA\n\nADQUIRENTE\n\nNIF:\n\nNº:\n\nCompl.:\n\nMunicípio:\n\n3550308 - São Paulo - SP\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nE-mail:\n\n----\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nSERVIÇO PRESTADO\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nCEP:\n\n01442-001\n\nCEP:\n\n----\n\nLocal de prestação:\n\n3550308 - São Paulo - SP\n\nCódigo indicador da operação:\n\n100301\n\nLocalidade de incidência:\n\n3550308 - São Paulo - SP\n\nTipo de operação:\n\n-----\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nOperação de uso:\n\nNão\n\nSituação tributária:\n\n000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nOUTRAS CLASSIFICAÇÕES\n\nNBS:\n\n113040000 - Serviços notariais e de registro\n\nNCM:\n\n----\n\nValor da multa (R$)\n-\n\nValor do juros (R$)\n-\n\nValor das Deduções\n\nBase de Cálculo do\n\nAlíquota Estadual do\n\nAlíquota Municipal\n\nRedução de Alíquota\n\nAlíquota Efetiva do\n\nValor Diferido do IBS\n\nValor do IBS (R$)\n\nde IBS e CBS (R$)\n\nIBS e CBS (R$)\n\nIBS (%)\n0,10%\n\ndo IBS (%)\n0,00%\n\ndo IBS (%)\n0,00%\n\nIBS (%)\n0,10%\n\n(R$)\n-\n\n0,55\n\n0,00\n\n553,70\n\nAlíquota da CBS (%)\n\nRedução de Alíquota\n\nAlíquota Efetiva da\n\nValor Diferido da\n\nValor da CBS (R$)\n\n0,90%\n\nda CBS (%)\n0,00%\n\nCBS (%)\n0,90%\n\nCBS (R$)\n0,00\n\n4,98\n\nVALOR TOTAL COBRADO =  R$ 561,05\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n\n\x0c'

PAGINA_FLASH_1 = NOTA_FLASH_05710445.split("\x0c")[0]
PRESTADOR_FLASH = "R EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000"
TOMADOR_FLASH = "R T R TERRITORIO DO AMAPA 146, Casa 2 - PITUBA - CEP: 41830-540"
RAZAO_TEMIS = "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"


def _parse(monkeypatch, texto_digital):
    caminho = "tests/dummy_sp_template_deslocado.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto_digital)
    try:
        notas = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    assert len(notas) == 1
    return notas[0]


# --- 1, 2, 3: entidades -------------------------------------------------------

def test_flash_tomador_razao_social_e_endereco(monkeypatch):
    t = _parse(monkeypatch, NOTA_FLASH_05710445).tomador
    assert t.razao_social == RAZAO_TEMIS
    assert t.cnpj_cpf == "07345543000190"
    e = t.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro, e.cep) == (
        "R T R TERRITORIO DO AMAPA", "146", "Casa 2", "PITUBA", "41830540")
    # o município impresso do tomador É Salvador/BA (lido por rótulo, não fallback)
    assert (e.municipio, e.uf, e.codigo_municipio) == ("Salvador", "BA", "2927408")


def test_flash_prestador_endereco_e_municipio_sao_paulo(monkeypatch):
    p = _parse(monkeypatch, NOTA_FLASH_05710445).prestador
    assert p.cnpj_cpf == "32223020000118" and p.inscricao_municipal == "61416720"
    e = p.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro, e.cep) == (
        "R EUGENIO DE MEDEIROS", "242", "ANDAR 4", "PINHEIROS", "05425000")
    # imprime "Município: São Paulo / UF: SP" -> SP/3550308, nunca o fallback BA/Salvador
    assert (e.municipio, e.uf, e.codigo_municipio) == ("São Paulo", "SP", "3550308")


def test_segunda_nota_flash_tambem_corrigida(monkeypatch):
    nfse = _parse(monkeypatch, NOTA_FLASH_05710815)
    assert nfse.tomador.razao_social == RAZAO_TEMIS
    assert nfse.prestador.endereco.uf == "SP" and nfse.prestador.endereco.codigo_municipio == "3550308"
    assert nfse.tomador.endereco.logradouro == "R T R TERRITORIO DO AMAPA"
    assert nfse.valores.aliquota == 0.02


def test_cartorio_razao_do_tomador_deslocada_para_antes_do_cabecalho(monkeypatch):
    # nota 01223660: a razão do tomador vem ANTES do cabeçalho "TOMADOR DE
    # SERVIÇOS" (no fim do bloco do prestador) e o genérico lia "São Paulo".
    nfse = _parse(monkeypatch, NOTA_CARTORIO_01223660)
    assert nfse.tomador.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA"
    assert nfse.prestador.razao_social == "RICARDO RAGE FERRO - 6 TABELIAO DE PROTESTO DE LETRAS E TITUL"
    e = nfse.tomador.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro, e.cep) == (
        "AL GABRIEL MONTEIRO DA SILVA", "1480", "CASA  TERREA", "JARDIM AMERICA", "01442001")
    assert (e.uf, e.codigo_municipio) == ("SP", "3550308")
    p = nfse.prestador.endereco
    assert (p.logradouro, p.numero, p.complemento, p.bairro, p.uf, p.codigo_municipio) == (
        "R SILVIA", "110", "ANDAR 6", "BELA VISTA", "SP", "3550308")


def test_sem_cep_no_endereco_preserva_o_comportamento_atual(monkeypatch):
    # sem o âncora "- CEP: NNNNN-NNN" nada é refinado: continua "Não informado"
    # (o CEP vem de outro campo do extrator genérico), sem endereço inventado.
    texto = (NOTA_FLASH_05710445
             .replace(" - CEP: 05425-000", "").replace(" - CEP: 41830-540", ""))
    nfse = _parse(monkeypatch, texto)
    for ent in (nfse.prestador, nfse.tomador):
        assert ent.endereco.logradouro == "Não informado"
        assert ent.endereco.numero == "S/N"
        assert ent.endereco.bairro == "Não informado"


def test_municipio_fora_da_tabela_usa_fallback_com_aviso(monkeypatch):
    texto = NOTA_FLASH_05710445.replace("\nSalvador\n", "\nCidade Ficticia do Norte\n")
    assert "Cidade Ficticia do Norte" in texto
    nfse = _parse(monkeypatch, texto)
    e = nfse.tomador.endereco
    assert (e.municipio, e.uf) == ("Cidade Ficticia do Norte", "BA")
    assert e.codigo_municipio == "2927408"  # capital da UF: fallback, NÃO confiável
    assert any("Cidade Ficticia do Norte" in a and "fallback" in a for a in nfse.avisos)


# --- 4: grade de valores (alíquota) -------------------------------------------

def test_flash_aliquota_impressa_2_por_cento_e_valores_flash_inalterados(monkeypatch):
    v = _parse(monkeypatch, NOTA_FLASH_05710445).valores
    assert v.aliquota == pytest.approx(0.02)          # mesma representação dos demais layouts
    assert v.base_calculo == 0.0 and v.valor_iss == 0.0  # como impresso
    assert v.valor_deducoes == 0.0
    assert v.valor_servicos == 1113.00 and v.valor_liquido_nfse == 1113.00  # regra Flash intacta


def test_cartorio_grade_deducoes_base_aliquota_iss_pela_estrutura(monkeypatch):
    # impresso: Deduções 193,65 | Base 367,40 | Alíquota 2,00% | ISS 7,34 | Crédito 0,00
    # (o pdfminer entrega "193,65 | 367,40 2,00% | 0,00 7,34": Crédito antes do ISS)
    v = _parse(monkeypatch, NOTA_CARTORIO_01223660).valores
    assert (v.valor_deducoes, v.base_calculo, v.aliquota, v.valor_iss) == (193.65, 367.40, 0.02, 7.34)
    assert v.valor_servicos == 561.05
    assert 367.40 * 0.02 == pytest.approx(v.valor_iss, abs=0.02)


def test_sem_aliquota_legivel_nao_inventa(monkeypatch):
    # sem o "2,00%" não há estrutura Dedução/Base/Alíquota: mantém a leitura anterior (0.00)
    texto = NOTA_FLASH_05710445.replace("2,00%", "")
    v = _parse(monkeypatch, texto).valores
    assert v.aliquota == 0.0


@pytest.mark.parametrize("grade, esperado", [
    # rótulos primeiro, valores depois, na ordem (AMIL / nota 05299158)
    ("Valor Total das Deduções\nBase de Cálculo\nAlíquota (%)\nValor ISS\n0,00\n40,18\n5,00%\n2,00\n0,00\nOUTRAS INFORMAÇÕES",
     (0.0, 40.18, 0.05, 2.00)),
    # Crédito antes do ISS
    ("Valor Total das Deduções (R$)\n193,65\n367,40\n2,00%\n0,00\n7,34\nOUTRAS INFORMAÇÕES",
     (193.65, 367.40, 0.02, 7.34)),
    # Base e Alíquota presentes, ISS zero impresso (aritmética não fecha) -> não adivinha
    ("Valor Total das Deduções (R$)\n0,00\n100,00\n2,00%\n0,00\n0,00\nOUTRAS INFORMAÇÕES", None),
    # sem percentual na 3ª posição -> None
    ("Valor Total das Deduções (R$)\n0,00\n100,00\n2,00\n0,00\n0,00\nOUTRAS INFORMAÇÕES", None),
    # sem a grade
    ("nada aqui", None),
])
def test_grade_por_estrutura_unidade(grade, esperado):
    assert SPPdfExtractor._sp_grade_valores_por_estrutura(grade) == esperado


# --- 5: competência -----------------------------------------------------------

def test_competencia_usa_mes_do_rps_quando_a_nota_nao_imprime(monkeypatch):
    # emissão 02/10/2026, RPS e "Data da Compra" 30/09/2026 -> 09/2026
    nfse = _parse(monkeypatch, NOTA_FLASH_05710445)
    assert nfse.data_emissao == datetime(2026, 10, 2, 4, 25, 42)
    assert nfse.competencia == datetime(2026, 9, 1)


def test_competencia_sem_rps_usa_data_da_compra(monkeypatch):
    texto = NOTA_FLASH_05710445.replace("RPS Nº 4159843 Série NFSE2, emitido em 30/09/2026", "")
    assert _parse(monkeypatch, texto).competencia == datetime(2026, 9, 1)


def test_competencia_sem_rps_nem_data_da_compra_cai_no_mes_da_emissao(monkeypatch):
    texto = (NOTA_FLASH_05710445.replace("RPS Nº 4159843 Série NFSE2, emitido em 30/09/2026", "")
             .replace("Data da Compra: 30/09/2026", ""))
    assert _parse(monkeypatch, texto).competencia == datetime(2026, 10, 1)


def test_competencia_rps_posterior_a_emissao_ou_antiga_demais_e_ignorada(monkeypatch):
    # RPS depois da emissão (impossível) e RPS de 2 anos antes: nenhum vale
    for rps in ("05/10/2026", "30/09/2024"):
        texto = (NOTA_FLASH_05710445.replace("emitido em 30/09/2026", f"emitido em {rps}")
                 .replace("Data da Compra: 30/09/2026", ""))
        assert _parse(monkeypatch, texto).competencia == datetime(2026, 10, 1), rps


def test_competencia_impressa_vence_o_rps(monkeypatch):
    texto = NOTA_FLASH_05710445.replace("Número da Nota", "Compe: Nov/2026\nNúmero da Nota", 1)
    assert _parse(monkeypatch, texto).competencia == datetime(2026, 11, 1)


def test_competencia_nota_do_mesmo_mes_nao_muda(monkeypatch):
    # nota 01223660: RPS 03/09 e emissão 09/09 -> 09/2026 (igual ao mês da emissão)
    assert _parse(monkeypatch, NOTA_CARTORIO_01223660).competencia == datetime(2026, 9, 1)


# --- 6: discriminação ---------------------------------------------------------

def test_discriminacao_nao_comeca_com_o_resto_do_cabecalho(monkeypatch):
    d = _parse(monkeypatch, NOTA_FLASH_05710445).discriminacao
    assert d.startswith("Valor Total - R$ 1.113,00 Compra de Créditos na Plataforma Flash - R$ 1.113,00")
    assert not d.startswith("DE SERVIÇOS")
    assert d.rstrip().endswith("0 - PIS/COFINS/CSLL Não Retidos.")


def test_discriminacao_cartorio(monkeypatch):
    d = _parse(monkeypatch, NOTA_CARTORIO_01223660).discriminacao
    assert d.startswith("O valor desta nota refere-se aos emolumentos")


# --- unidade: parser do endereço de linha única -------------------------------

@pytest.mark.parametrize("linha, esperado", [
    (PRESTADOR_FLASH, ("R EUGENIO DE MEDEIROS", "242", "ANDAR 4", "PINHEIROS", "05425000")),
    (TOMADOR_FLASH, ("R T R TERRITORIO DO AMAPA", "146", "Casa 2", "PITUBA", "41830540")),
    ("R FREI CANECA 1355 - CONSOLACAO - CEP: 01307-001", ("R FREI CANECA", "1355", None, "CONSOLACAO", "01307001")),
    ("AV PAULISTA, 1000, SALA 5 - BELA VISTA - CEP: 01310-100", ("AV PAULISTA", "1000", "SALA 5", "BELA VISTA", "01310100")),
    ("Endereço: R X S/N - CENTRO - CEP: 01000-000", ("R X", "S/N", None, "CENTRO", "01000000")),
    ("R X 10 - PARQUE BELA VISTA - SALAS 203 E 204 - CEP: 40279-435", ("R X", "10", "SALAS 203 E 204", "PARQUE BELA VISTA", "40279435")),
    ("R EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS", None),   # sem CEP
    ("R EUGENIO DE MEDEIROS 242 - CEP: 05425-000", None),        # sem bairro
])
def test_endereco_linha_unica(linha, esperado):
    assert SPPdfExtractor._sp_endereco_linha_unica(linha) == esperado
