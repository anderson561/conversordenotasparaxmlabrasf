# -*- coding: utf-8 -*-
r"""DANFSe v2.0 (LAYOUT_NACIONAL_REFORMA) DIGITAL, "Ambiente Gerador: Sistema
Próprio do Município" — Teresina/PI. Nota real nº 53, 3E ENGENHARIA LTDA
(49.421.315/0001-00, IM 822741, CEP 64057-310) -> SAO PEDRO CONSTRUTORA LTDA
(Lauro de Freitas/BA, IBGE 2919207, CEP 42708-720), R$ 800,00, ISS 5% não
retido ("NF 3E ENG.pdf", arquivo real do usuário).

`RAW_DIGITAL` é o retorno REAL e verbatim de `extract_text()` (pdfminer) no
PDF original, via `repr()`.

Defeitos do XML antes do fix:
1. Numero 47 (nNFSe da chave de acesso) em vez do impresso 53 — a chave
   deste gerador não casa com o impresso (nNFSe 47, cMun 2207801).
2. Prestador com CodigoMunicipio 2919207 e CEP 42708720 (os do TOMADOR): o
   pdfminer despeja "Telefone" / "Código IBGE / CEP" do prestador ANTES do
   cabeçalho "PRESTADOR / FORNECEDOR"; a única ocorrência depois dele era a
   do tomador, lida pelo ordinal 0 (prestador).
3. Tomador com CEP 00000000 (o ordinal 1 não existia).
4. Prestador sem InscricaoMunicipal (rótulo "Inscrição Municipal", sem
   "Indicador")."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA
from src.transformers.abrasf_transformer import Abrasf201Transformer

RAW_DIGITAL = 'DANFSe v2.0 \nDocumento Auxiliar da NFS-e \n\nMunicípio: TERESINA / PI \nAmbiente Gerador: Sistema Próprio do Município \n\nTipo de Ambiente:  Produção \n\nA autenticidade desta NFS-e pode ser \nverificada pela leitura deste código QR ou pela \nconsulta da chave no portal nacional. \n\nTelefone \n\nCódigo IBGE / CEP \n2211001 / 64057-310 \n\nCHAVE DE ACESSO DA NFS-E \n22078011249421315000100000000000004726100162176312 \n\nNÚMERO DA NFS-E \n53 \nNÚMERO DA DPS \n- \nEMITENTE DA NFS-e \nPrestador \n\nCOMPETÊNCIA DA NFS-E \n16/10/2026 \nSÉRIE DA DPS \n- \nSITUAÇÃO DA NFS-e \nNFS-e Gerada \n\nDATA E HORA DA EMISSÃO DA NFS-E \n16/10/2026 10:00:54 \nDATA E HORA DA EMISSÃO DA DPS \n16/10/2026 10:00:54 \nFINALIDADE \nNFS-e regular \n\nPRESTADOR / FORNECEDOR \n\nCPF / CNPJ / NIF \n49.421.315/0001-00 \n\nNome / Nome empresarial \n3E ENGENHARIA LTDA \n\nEndereço \nCASA B QUADRA 51 CONJ RENASCENCA II \n\nSimples Nacional na Data de Competência \nNão optante \n\nRegime de Apuração Tributária pelo SN \n- \n\nTOMADOR / ADQUIRENTE \n\nCPF / CNPJ / NIF \n03.051.741/0001-90 \n\nNome / Nome empresarial \nSAO PEDRO CONSTRUTORA LTDA \n\nInscrição Municipal \n822741 \n\nMunicípio / Sigla UF \nTERESINA / PI \n\nE-mail \n- \n\nInscrição Municipal \n- \n\nMunicípio / Sigla UF \nLAURO DE FREITAS / BA \n\nTelefone \n- \n\nCódigo IBGE / CEP \n2919207 / 42708-720 \n\nEndereço \nAVENIDA PRAIA DE PAJUSSARA, 554, VILAS DO ATLANTICO \n\nE-mail \n- \n\nO DESTINATÁRIO É O PRÓPRIO TOMADOR/ADQUIRENTE DA OPERAÇÃO \n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e \n\nSERVIÇO PRESTADO \n\nCódigo de Tributação Nacional / Municipal \n07.02.01 \n\nCódigo da NBS \n1011261000 \n\nLocal da Prestação / Sigla UF / País \nTERESINA / PI / BR \n\nINSTALAÇÃO E MANUTENÇÃO ELÉTRICA. \n\nDescrição do Serviço \nSERVIÇO DE INSTALAÇÃO E MANUTENÇÃO ELÉTRICA. \n\nTRIBUTAÇÃO MUNICIPAL (ISSQN) \n\nRegime Especial de Tributação do ISSQN \nNenhum \n\nTipo de Tributação do ISSQN \nOperação tributável \n\nTipo de Imunidade do ISSQN \n- \n\nMunicípio / Sigla UF / País de Incidência do ISSQN \nTERESINA / PI / BR \n\nSuspensão da Exigibilidade do ISSQN \nNão \n\nBenefício Municipal \n- \n\nBC ISSQN \nR$ 800,00 \n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS) \n\nCálculo do BM \n- \n\nAlíquota Aplicada \n5,00% \n\nIRRF \n- \n\nPIS - Débito Apuração Própria \n- \n\nTRIBUTAÇÃO IBS/CBS \n\nCOFINS - Débito Apuração Própria \n- \n\nCST / cClassTrib \n000 / 000001 \n\nTotal Deduções/Reduções \n- \n\nRetenção do ISSQN \nNão Retido \n\nContribuição Previdenciária - Retida \n- \n\nDescrição Contrib. Sociais - Retidas \n- \n\nNúmero Processo Suspensão \n- \n\nDesconto Incondicionado \n- \n\nISSQN Apurado \nR$ 40,00 \n\nContribuições Sociais - Retidas \n- \n\nIndicador de Operação / Código IBGE Incidência / Município de Incidência / Sigla UF \n100301 / 2211001 / TERESINA / PI \n\nExclusões e Reduções da Base de Cálculo \nR$ 40,00 \n\nBase de Cálculo Após Exclusões e Reduções \nR$ 760,00 \n\nRed. Alíquota IBS / Red. Alíquota CBS \n- / - / - \n\nAlíq. Efetiva Municipal - IBS \n0,00 % \n\nValor Total Apurado - IBS \nR$ 0,00 \n\nVALOR TOTAL DA NFS-E \n\nValor Apurado Municipal - IBS \nR$ 0,00 \n\nAlíquota - CBS \n0,0 % \n\nVALOR DA OPERAÇÃO / SERVIÇO \nR$ 800,00 \n\nTotal das Retenções (ISSQN / Federais) \nR$ 0,00 \n\nVALOR LÍQUIDO DA NFS-e \nR$ 800,00 \n\nINFORMAÇÕES COMPLEMENTARES \nDADOS PARA PAGAMENTO PIX : eng.alexfontenele@gmail.com \nCFF: 058.797.343-90  \nVALOR: 800,00  \nBANCO C6 \n\nAlíq. Efetiva Estadual - IBS \n0,0 % \n\nAlíquota Efetiva - CBS \n0,0 % \n\nDesconto Incondicionado \nR$ 0,00 \n\nTotal do IBS/CBS \nR$ 0,00 \n\nAlíquota - IBS UF / IBS Mun \n0,00 % / 0,00 % \n\nValor Apurado Estadual - IBS \nR$ 0,00 \n\nValor Total Apurado - CBS \nR$ 0,00 \n\nDesconto Condicionado \nR$ 0,00 \n\nVALOR LÍQUIDO DA NFS-E + IBS/CBS \nR$ 800,00 \n\n \n \n \n\x0c'


def _parse(monkeypatch, raw, nome="dummy_nf_3e_eng.pdf"):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: raw)
    try:
        notas = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    assert len(notas) == 1
    return notas[0]


def test_layout_detectado_e_reforma():
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = RAW_DIGITAL
    assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA


def test_numero_impresso_prevalece_sobre_chave_divergente(monkeypatch):
    nota = _parse(monkeypatch, RAW_DIGITAL)
    assert nota.numero == "53"
    # Código de verificação continua sendo a chave (convenção da DANFSe).
    assert nota.codigo_verificacao == "22078011249421315000100000000000004726100162176312"


def test_aviso_de_divergencia_da_chave(monkeypatch):
    nota = _parse(monkeypatch, RAW_DIGITAL)
    avisos = [a for a in nota.avisos if "Chave de acesso codifica" in a]
    assert len(avisos) == 1
    a = avisos[0]
    assert "nº 47" in a and "município 2207801" in a
    assert "nº 53" in a and "2211001" in a and "usado o número impresso" in a


def test_prestador_municipio_cep_e_inscricao(monkeypatch):
    p = _parse(monkeypatch, RAW_DIGITAL).prestador
    assert p.cnpj_cpf == "49421315000100"
    assert p.razao_social == "3E ENGENHARIA LTDA"
    assert p.inscricao_municipal == "822741"
    assert p.endereco.logradouro == "CASA B QUADRA 51 CONJ RENASCENCA II"
    assert p.endereco.codigo_municipio == "2211001"
    assert p.endereco.uf == "PI"
    assert p.endereco.cep == "64057310"


def test_tomador_municipio_cep_e_endereco(monkeypatch):
    tm = _parse(monkeypatch, RAW_DIGITAL).tomador
    assert tm.cnpj_cpf == "03051741000190"
    assert tm.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
    assert not tm.inscricao_municipal
    e = tm.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("AVENIDA PRAIA DE PAJUSSARA", "554", "VILAS DO ATLANTICO")
    assert e.codigo_municipio == "2919207"
    assert e.uf == "BA"
    assert e.cep == "42708720"


def test_xml_final(monkeypatch):
    nota = _parse(monkeypatch, RAW_DIGITAL)
    xml = Abrasf201Transformer().transform(nota)
    assert "<Numero>53</Numero>" in xml
    assert "<Cep>64057310</Cep>" in xml and "<Cep>42708720</Cep>" in xml
    assert "<Cep>00000000</Cep>" not in xml
    prest = xml.split("<PrestadorServico>")[1].split("</PrestadorServico>")[0]
    assert "<CodigoMunicipio>2211001</CodigoMunicipio>" in prest
    assert "2919207" not in prest
    assert "<ValorServicos>800.00</ValorServicos>" in xml
    assert "<ValorIss>40.00</ValorIss>" in xml
    assert "<IssRetido>2</IssRetido>" in xml
    assert "<Competencia>2026-10-16</Competencia>" in xml


def test_chave_concordante_nao_gera_aviso_nem_muda_numero(monkeypatch):
    # Mesmo texto com o impresso igual ao nNFSe da chave: segue a chave, sem aviso.
    raw = RAW_DIGITAL.replace("NÚMERO DA NFS-E \n53 \n", "NÚMERO DA NFS-E \n47 \n")
    assert raw != RAW_DIGITAL
    nota = _parse(monkeypatch, raw)
    assert nota.numero == "47"
    assert not [a for a in nota.avisos if "Chave de acesso codifica" in a]


def test_escaneada_mantem_chave(monkeypatch):
    # Em página de OCR o impresso não é confiável: a chave continua valendo.
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = RAW_DIGITAL
    ex.layout = LAYOUT_NACIONAL_REFORMA
    ex._pagina_veio_de_ocr = True
    chave = "22078011249421315000100000000000004726100162176312"
    assert ex._danfse_v2_numero_impresso_divergente(chave) is None
    ex._pagina_veio_de_ocr = False
    assert ex._danfse_v2_numero_impresso_divergente(chave) == "53"
