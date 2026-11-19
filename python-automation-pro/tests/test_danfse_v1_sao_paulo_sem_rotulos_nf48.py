# -*- coding: utf-8 -*-
"""DANFSe v1.0 DIGITAL com camada de texto SÓ DE VALORES (rótulos em curvas).

Achado real 2026-11-19: `Nova pasta/05-Mai-2026_NF_48_RAIMUNDA.pdf`, DANFSe
v1.0 emitida pela Prefeitura de São Paulo (RAIMUNDA REGIS ALMEIDA DE SOUZA,
MEI -> NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA, R$ 2.950,00).
O pdfminer devolve só os valores, nenhum rótulo ("Valor do Serviço", "Nome /
Nome Empresarial", "EMITENTE DA NFS-e"... estão desenhados como curvas). A
nota caía no LAYOUT_NACIONAL pelo fallback "chave de acesso" e saía com
ValorServicos 0,00, RazaoSocial do prestador e do tomador = "(11) 6343-0429",
endereços "Não informado", DataEmissao 2026-05-01 e um `<Intermediario>`
lixo ("NÃO IDENTIFICADO NA NFS-e").

Correção: `_danfse_texto_sem_rotulos` detecta a página e
`danfse_rotulos_imagem.ler_pagina` monta o texto com os RÓTULOS do OCR e os
VALORES da camada digital, juntados pela posição na página.
"""
import os

import pytest

from src.extractors import danfse_rotulos_imagem as dri
from src.extractors.pdf_extractor import LAYOUT_NACIONAL, SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer

PDF_REAL = r'L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\Nova pasta\05-Mai-2026_NF_48_RAIMUNDA.pdf'

# Texto REAL do `pdfminer.high_level.extract_text()` desta nota, verbatim:
# só valores, nenhum rótulo.
TEXTO_DIGITAL_NF48 = "35503082248134937000186000000000004826057173219569\n\n48\n\n11\n\n15/05/2026\n\n70000\n\n15/05/2026 14:36:30\n\n15/05/2026 14:36:30\n\nPrefeitura da Cidade de São Paulo\nSecretaria Municipal da Fazenda\n(11)156\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nPrestador do Serviço\n\n48.134.937/0001-86\n\n-\n\n(11) 6343-0429\n\n48.134.937 RAIMUNDA REGIS ALMEIDA DE SOUZA\n\nALVES_E_ALMEIDA@HOTMAIL.COM\n\nRUA SANT'ANA, 404, VILA SAO PEDRO\n\nSão Paulo - SP\n\n4676110\n\nOptante - Microempreendedor Individual (MEI)\n\n16.699.869/0002-97\n\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\n-\n\n-\n\n-\n\n-\n\nGABRIEL MONTEIRO DA SILVA, 1480, CASA TERREA, JARDIM AMERICA São Paulo - SP\n\n01442-001\n\nINTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\n\n-\n\n-\n\nNão\n\n-\n\n-\n\n-\n\n-\n\n-\n\n-\n\n16.02.01 - Outros serviços de\ntransporte de natureza municipal.\n\nSERVIÇO DE FRETE\n\nOperação Tributável\n\n-\n\nR$ 2.950,00\n\n-\n\n-\n\n-\n\nR$ 2.950,00\n\n-\n\n-\n\n105011210\n\nSão Paulo - SP\n\n-\n\nSão Paulo - SP\n\nNenhum\n\n-\n\n-\n\nNão Retido\n\n-\n\n-\n\n-\n\n-\n\n-\n\n-\n\n-\n\n-\n\n-\n\n\x0c"

# Texto REAL de `danfse_rotulos_imagem.ler_pagina` (página 1 desta nota):
# rótulos do OCR (Tesseract 'por', zoom 3x) + valores da camada digital,
# agrupados por linha visual. Os únicos resíduos de OCR ("NFSe", "ss:",
# "CIDADE DE") são do logotipo/brasão, fora de qualquer campo.
TEXTO_MESCLADO_NF48 = "Prefeitura da Cidade de São Paulo\nNFSe DANFSe v1.0 Secretaria Municipal da Fazenda\nss: Documento Auxiliar da NFS-e CIDADE DE (11)156\nChave de Acesso da NFS-e\n35503082248134937000186000000000004826057173219569\nNúmero da NFS-e Competência da NFS-e Data e Hora da emissão da NFS-e\n48 15/05/2026 15/05/2026 14:36:30\nNúmero da DPS Série da DPS Data e Hora da emissão da DPS\n11 70000 15/05/2026 14:36:30 A autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\nEMITENTE DA NFS-e CNPJ/CPF /NIF Inscrição Municipal Telefone\nPrestador do Serviço 48.134.937/0001-86 - (11) 6343-0429\nNome / Nome Empresarial E-mail\n48.134.937 RAIMUNDA REGIS ALMEIDA DE SOUZA ALVES_E_ALMEIDA@HOTMAIL.COM\nEndereço Município CEP\nRUA SANT'ANA, 404, VILA SAO PEDRO São Paulo - SP 4676110\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\nOptante - Microempreendedor Individual (MEI) -\nTOMADOR DO SERVIÇO CNPJ/CPF / NIF Inscrição Municipal Telefone\n16.699.869/0002-97 - -\nNome / Nome Empresarial E-mail\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA -\nEndereço Município CEP\nGABRIEL MONTEIRO DA SILVA, 1480, CASA TERREA, JARDIM AMERICA São Paulo - SP 01442-001\nINTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\nSERVIÇO PRESTADO\nCódigo de Tributação Nacional Código de Tributação Municipal Local da Prestação País da Prestação\n16.02.01 - Outros serviços de - São Paulo - SP -\ntransporte de natureza municipal.\nDescrição do Serviço\nSERVIÇO DE FRETE\nTRIBUTAÇÃO MUNICIPAL\nTributação do ISSQN País Resultado da Prestação do Serviço Município de Incidência do ISSQN Regime Especial de Tributação\nOperação Tributável - São Paulo - SP Nenhum\nTipo de Imunidade Suspensão da Exigibilidade do ISSQN Número Processo Suspensão Benefício Municipal\n- Não - -\nValor do Serviço Desconto Incondicionado Total Deduções/Reduções Cálculo do BM\nR$ 2.950,00 - - -\nBC ISSQN Alíquota Aplicada Retenção do ISSQN ISSQN Apurado\n- - Não Retido -\nTRIBUTAÇÃO FEDERAL\nIRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas Descrição Contrib. Sociais - Retidas\n- - - -\nPIS - Débito Apuração Própria COFINS - Débito Apuração Própria\n- -\nVALOR TOTAL DA NFS-E\nValor do Serviço Desconto Condicionado Desconto Incondicionado ISSQN Retido\nR$ 2.950,00 - - -\nTotal das Retenções Federais PIS/COFINS - Débito Apur. Própria Valor Líquido da NFS-e\n- - R$ 2.950,00\nTOTAIS APROXIMADOS DOS TRIBUTOS\nFederais Estaduais Municipais\n- - -\nINFORMAÇÕES COMPLEMENTARES\nNBS: 105011210"

CHAVE = '35503082248134937000186000000000004826057173219569'


@pytest.fixture
def dummy_pdf(tmp_path):
    p = tmp_path / 'nf48.pdf'
    p.write_bytes(b'%PDF-1.4')
    return str(p)


def _parse(monkeypatch, dummy_pdf, mesclado=TEXTO_MESCLADO_NF48, ocr=None):
    chamadas = {'mescla': 0, 'ocr': 0}

    def _ler(pdf_path, page_idx):
        chamadas['mescla'] += 1
        return mesclado

    def _ocr(self, page_num):
        chamadas['ocr'] += 1
        return ocr or ''

    monkeypatch.setattr('src.extractors.pdf_extractor.extract_text', lambda path: TEXTO_DIGITAL_NF48.rstrip('\x0c'))  # PDF de 1 página: sem o form feed final
    monkeypatch.setattr(dri, 'ler_pagina', _ler)
    monkeypatch.setattr(SPPdfExtractor, '_ocr_page', _ocr)
    notas = SPPdfExtractor(dummy_pdf).parse_multiple()
    return notas, chamadas


# --- detecção da patologia --------------------------------------------------

def test_texto_digital_real_sem_rotulos_e_detectado():
    assert SPPdfExtractor._danfse_texto_sem_rotulos(TEXTO_DIGITAL_NF48)


def test_texto_mesclado_tem_rotulos():
    assert not SPPdfExtractor._danfse_texto_sem_rotulos(TEXTO_MESCLADO_NF48)


@pytest.mark.parametrize('modulo, var', [
    ('test_danfse_nacional_layout', 'MOCK_OCR'),
    ('test_danfse_intermediario_vira_tomador', 'MOCK_TEXT'),
    ('test_danfse_nacional_razao_social_email_colado', 'MOCK_TEXT'),
    ('test_danfse_nacional_pagina_unica_sem_fantasma', 'MOCK_TEXT_PAGINA3'),
])
def test_danfse_com_rotulos_nao_dispara(modulo, var):
    """DANFSe v1.0 normais (texto real de OCR já coberto) têm rótulos."""
    import importlib
    texto = getattr(importlib.import_module(f'tests.{modulo}'), var)
    assert not SPPdfExtractor._danfse_texto_sem_rotulos(texto)


def test_sem_marca_de_danfse_nao_dispara():
    # Mesmo texto sem a frase do QR Code e sem a chave sozinha na linha.
    texto = TEXTO_DIGITAL_NF48.replace('portal nacional da NFS-e', 'portal').replace(CHAVE, 'X')
    assert not SPPdfExtractor._danfse_texto_sem_rotulos(texto)


def test_outro_modelo_com_chave_nacional_nao_dispara():
    """Regressão do corpus: NFS-e de Salvador/BA ("NOTA FISCAL SP
    EMPREENDIMENTO (AVENA).pdf") cita o portal nacional e não tem rótulo da
    DANFSe v1.0, mas tem os rótulos "<campo> :" do próprio modelo."""
    texto = TEXTO_DIGITAL_NF48.replace(
        'Prestador do Serviço', 'CNPJ/CPF :\n\nRazão Social :\n\nEndereço :\n\nPrestador do Serviço')
    assert not SPPdfExtractor._danfse_texto_sem_rotulos(texto)


def test_endereco_em_linha_limpa_ruido_de_ocr(dummy_pdf):
    """Regressão do corpus ("nfs 03.11.pdf" pág. 3, DANFSe v1.0 escaneada)."""
    ext = SPPdfExtractor(dummy_pdf)
    end = {'logradouro': 'Não informado', 'numero': 'S/N', 'bairro': 'Não informado',
           'municipio': 'Não informado', 'uf': 'BA', 'cep': '00000-000'}
    ext._danfse_v1_endereco_em_linha(
        'Endereço Município CEP\nPRAIA DE PAJUSSARA, 554, VILAS DO ATLANTICO = Lauro de Freitas - BA 42708-720\n',
        end, 'Tomador')
    assert (end['logradouro'], end['numero'], end['bairro']) == ('PRAIA DE PAJUSSARA', '554', 'VILAS DO ATLANTICO')
    assert (end['municipio'], end['uf'], end['cep']) == ('Lauro de Freitas', 'BA', '42708720')


def test_texto_curto_nao_dispara():
    assert not SPPdfExtractor._danfse_texto_sem_rotulos(CHAVE + '\nportal nacional da NFS-e')


# --- nota completa ------------------------------------------------------------

def test_nf48_nota_completa(monkeypatch, dummy_pdf):
    notas, chamadas = _parse(monkeypatch, dummy_pdf)
    assert chamadas == {'mescla': 1, 'ocr': 0}
    assert len(notas) == 1
    n = notas[0]
    assert n.numero == '48'
    assert n.codigo_verificacao == CHAVE
    assert n.data_emissao.strftime('%Y-%m-%d %H:%M:%S') == '2026-05-15 14:36:30'
    assert n.competencia.strftime('%Y-%m-%d') == '2026-05-15'

    v = n.valores
    assert v.valor_servicos == pytest.approx(2950.00)
    assert v.valor_liquido_nfse == pytest.approx(2950.00)
    assert v.valor_deducoes == 0.0
    assert (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir, v.valor_csll) == (0, 0, 0, 0, 0)
    # MEI, BC/alíquota/ISS impressos "-": mesma convenção das demais DANFSe
    # v1.0 de MEI (base = valor do serviço, alíquota e ISS 0), não retido.
    assert v.base_calculo == pytest.approx(2950.00)
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0
    assert v.iss_retido is False

    assert n.optante_simples_nacional is True
    assert n.regime_especial_tributacao == '5'  # MEI
    assert n.servico_codigo == '1602'
    assert n.discriminacao == 'SERVIÇO DE FRETE'

    p = n.prestador
    assert p.cnpj_cpf == '48134937000186'
    assert p.razao_social == 'RAIMUNDA REGIS ALMEIDA DE SOUZA'
    e = p.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("RUA SANT'ANA", '404', 'VILA SAO PEDRO')
    assert (e.codigo_municipio, e.uf) == ('3550308', 'SP')
    assert e.cep == '04676110'

    t = n.tomador
    assert t.cnpj_cpf == '16699869000297'
    assert t.razao_social == 'NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA'
    e = t.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro) == (
        'GABRIEL MONTEIRO DA SILVA', '1480', 'CASA TERREA', 'JARDIM AMERICA')
    assert (e.codigo_municipio, e.uf, e.cep) == ('3550308', 'SP', '01442001')

    assert n.intermediario is None
    assert n.avisos == [
        'CEP do prestador impresso com 7 dígitos (4676110) - completado com o zero à '
        'esquerda (04676110); confira']


def test_nf48_xml(monkeypatch, dummy_pdf):
    notas, _ = _parse(monkeypatch, dummy_pdf)
    xml = Abrasf201Transformer().transform(notas[0])
    assert '<ValorServicos>2950.00</ValorServicos>' in xml
    assert '<ValorLiquidoNfse>2950.00</ValorLiquidoNfse>' in xml
    assert '<IssRetido>2</IssRetido>' in xml
    assert '<DataEmissao>2026-05-15T14:36:30</DataEmissao>' in xml
    assert '<ItemListaServico>1602</ItemListaServico>' in xml
    assert '<Intermediario>' not in xml
    assert '(11) 6343-0429' not in xml
    assert 'Não informado' not in xml


def test_mescla_indisponivel_cai_no_ocr_puro(monkeypatch, dummy_pdf):
    """Sem Tesseract/PDF ilegível a mescla devolve None: a página vai para o
    OCR puro (antes desta correção nem isso acontecia)."""
    notas, chamadas = _parse(monkeypatch, dummy_pdf, mesclado=None, ocr=TEXTO_MESCLADO_NF48)
    assert chamadas == {'mescla': 1, 'ocr': 1}
    assert notas[0].valores.valor_servicos == pytest.approx(2950.00)


# --- mescla pura (sem PDF nem Tesseract) -------------------------------------

def test_palavras_digitais_separa_por_lacuna_e_espaco():
    # (topo, base, x0, x1, ch): "R$ 2,0" numa linha e "X" noutra.
    chars = [(10, 18, 0, 4, 'R'), (10, 18, 4, 8, '$'), (10, 18, 8, 10, ' '),
             (10, 18, 10, 14, '2'), (10, 18, 14, 16, ','), (10, 18, 16, 20, '0'),
             (30, 38, 0, 4, 'X')]
    assert [w[4] for w in dri.palavras_digitais(chars)] == ['R$', '2,0', 'X']


def test_mesclar_poe_rotulo_em_cima_e_descarta_ocr_sobre_valor():
    digitais = [(20, 28, 10, 60, 'R$ 2.950,00')]
    ocr = [
        (10, 17, 10, 30, 'Valor'), (10, 17, 32, 40, 'do'), (10, 17, 42, 70, 'Serviço'),
        # leitura do OCR EM CIMA do valor digital: descartada (o digital vale)
        (20, 28, 10, 60, 'R$2.950,O0'),
        (10, 17, 150, 200, 'Desconto'),
    ]
    digitais.append((20, 28, 150, 155, '-'))
    assert dri.mesclar(digitais, ocr) == 'Valor do Serviço Desconto\nR$ 2.950,00 -'


# --- endereço/discriminação/intermediário da DANFSe v1.0 em linha ------------

def test_endereco_em_linha_sem_numero_nao_adivinha(dummy_pdf):
    ext = SPPdfExtractor(dummy_pdf)
    end = {'logradouro': 'Não informado', 'numero': 'S/N', 'bairro': 'Não informado',
           'municipio': 'Não informado', 'uf': 'BA', 'cep': '00000-000'}
    ext._danfse_v1_endereco_em_linha(
        'Endereço Município CEP\nRODOVIA BA 099 KM 12 Camaçari - BA 42840-000\n', end, 'Tomador')
    assert end['logradouro'] == 'RODOVIA BA 099 KM 12'
    assert (end['numero'], end['bairro']) == ('S/N', 'Não informado')
    assert (end['municipio'], end['uf'], end['cep']) == ('Camaçari', 'BA', '42840000')
    assert not getattr(ext, '_danfse_v1_avisos', [])


def test_endereco_em_linha_nao_sobrescreve_extraido(dummy_pdf):
    ext = SPPdfExtractor(dummy_pdf)
    end = {'logradouro': 'AV X', 'numero': '1', 'bairro': 'CENTRO',
           'municipio': 'Salvador', 'uf': 'BA', 'cep': '40000000'}
    ext._danfse_v1_endereco_em_linha(
        'Endereço Município CEP\nRUA Y, 2, BAIRRO Z Camaçari - BA 42840-000\n', end, 'Tomador')
    assert end == {'logradouro': 'AV X', 'numero': '1', 'bairro': 'CENTRO',
                   'municipio': 'Salvador', 'uf': 'BA', 'cep': '40000000'}


def test_discriminacao_com_rotulo_vazado_fica_no_padrao(dummy_pdf):
    """Texto embaralhado por coluna (OCR de scan): rótulo de outra célula no
    meio da descrição -> mantém o texto padrão em vez de misturar."""
    ext = SPPdfExtractor(dummy_pdf)
    ext.layout = LAYOUT_NACIONAL
    ext.raw_text = ('Descrição do Serviço\n\nCódigo de Tributação Municipal\n\nSERVIÇO X\n\n'
                    'TRIBUTAÇÃO MUNICIPAL\n')
    assert ext._extrair_discriminacao() == 'Serviços prestados conforme nota fiscal.'


@pytest.mark.skipif(not os.path.exists(PDF_REAL), reason='PDF real fora do corpus local')
def test_pdf_real_nf48():
    pytest.importorskip('pytesseract')
    notas = SPPdfExtractor(PDF_REAL).parse_multiple()
    assert len(notas) == 1
    n = notas[0]
    assert n.valores.valor_servicos == pytest.approx(2950.00)
    assert n.prestador.razao_social == 'RAIMUNDA REGIS ALMEIDA DE SOUZA'
    assert n.tomador.endereco.cep == '01442001'
    assert n.intermediario is None
