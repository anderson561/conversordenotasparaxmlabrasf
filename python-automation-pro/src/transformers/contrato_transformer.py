"""
Transformer para gerar XML ABRASF 2.01 a partir de Contratos de Locação.

Regras especiais:
  - Locador  → <Tomador>   no XML
  - Locatário → <Prestador> no XML
  - <Numero>  → ano corrente (ex: 2026)
  - <Acumulador> → 916
  - CodigoVerificacao → "CONTRATO"
"""
import xml.etree.ElementTree as ET
from datetime import datetime
from ..models.contrato_locacao_model import ContratoLocacao

NS_ABRASF = 'http://www.abrasf.org.br/nfse.xsd'
NS_XSI    = 'http://www.w3.org/2001/XMLSchema-instance'


class ContratoLocacaoTransformer:
    """Gera XML ABRASF 2.01 a partir de um ContratoLocacao."""

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _digits(value: str) -> str:
        return ''.join(ch for ch in (value or '') if ch.isdigit())

    def _append_cpf_cnpj(self, parent: ET.Element, raw_doc: str,
                          preferred: str = "cnpj") -> None:
        doc = self._digits(raw_doc)
        if len(doc) == 14:
            ET.SubElement(parent, 'Cnpj').text = doc
        elif len(doc) == 11:
            ET.SubElement(parent, 'Cpf').text = doc
        elif preferred == "cpf":
            ET.SubElement(parent, 'Cpf').text = doc[:11].zfill(11)
        else:
            ET.SubElement(parent, 'Cnpj').text = doc[:14].zfill(14)

    # ------------------------------------------------------------------ #
    # Ponto de entrada público
    # ------------------------------------------------------------------ #
    def transform(self, contrato: ContratoLocacao) -> str:
        ET.register_namespace('', NS_ABRASF)
        ET.register_namespace('xsi', NS_XSI)

        root = self._build_comp_nfse(contrato)
        ET.indent(root, space='  ')
        return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')

    # ------------------------------------------------------------------ #
    # Construção do XML
    # ------------------------------------------------------------------ #
    def _build_comp_nfse(self, c: ContratoLocacao) -> ET.Element:
        # Número = ano corrente
        numero = str(c.data_emissao.year)

        # Cálculos de valores
        valor_servicos = round(c.valor_mensal, 2)
        valor_iss      = round(valor_servicos * c.aliquota_iss, 2)
        valor_liquido  = round(valor_servicos - valor_iss, 2)

        # Código do serviço formatado (4 dígitos sem pontos)
        item_lista = c.servico_codigo.replace('.', '').zfill(4)

        # Código município (locador = tomador → usamos dados do locador)
        cod_mun = c.locador.codigo_municipio

        # ---- Raiz ----
        root = ET.Element('CompNfse')
        nfse_xml  = ET.SubElement(root, 'Nfse', versao="2.01")
        inf_nfse  = ET.SubElement(nfse_xml, 'InfNfse', Id=f"NFSe{numero}")

        ET.SubElement(inf_nfse, 'Numero').text            = numero
        ET.SubElement(inf_nfse, 'CodigoVerificacao').text = "CONTRATO"
        ET.SubElement(inf_nfse, 'DataEmissao').text       = c.data_emissao.strftime('%Y-%m-%dT%H:%M:%S')
        ET.SubElement(inf_nfse, 'Competencia').text       = c.data_emissao.strftime('%Y-%m-%d')
        ET.SubElement(inf_nfse, 'OutrasInformacoes').text = "Gerado a partir de Contrato de Locação - ABRASF 2.01"

        # ---- ValoresNfse ----
        valores_nfse = ET.SubElement(inf_nfse, 'ValoresNfse')
        ET.SubElement(valores_nfse, 'ValorServicos').text    = f"{valor_servicos:.2f}"
        ET.SubElement(valores_nfse, 'ValorDeducoes').text    = "0.00"
        ET.SubElement(valores_nfse, 'ValorPis').text         = "0.00"
        ET.SubElement(valores_nfse, 'ValorCofins').text      = "0.00"
        ET.SubElement(valores_nfse, 'ValorInss').text        = "0.00"
        ET.SubElement(valores_nfse, 'ValorIr').text          = "0.00"
        ET.SubElement(valores_nfse, 'ValorCsll').text        = "0.00"
        ET.SubElement(valores_nfse, 'OutrasRetencoes').text  = "0.00"
        ET.SubElement(valores_nfse, 'BaseCalculo').text      = f"{valor_servicos:.2f}"
        ET.SubElement(valores_nfse, 'Aliquota').text         = f"{c.aliquota_iss:.4f}"
        ET.SubElement(valores_nfse, 'ValorIss').text         = f"{valor_iss:.2f}"
        ET.SubElement(valores_nfse, 'ValorLiquidoNfse').text = f"{valor_liquido:.2f}"

        ET.SubElement(inf_nfse, 'ValorCredito').text = "0.00"

        # ---- PrestadorServico → Locatário ----
        prestador_servico  = ET.SubElement(inf_nfse, 'PrestadorServico')
        ident_prestador    = ET.SubElement(prestador_servico, 'IdentificacaoPrestador')
        self._append_cpf_cnpj(ident_prestador, c.locatario.cnpj_cpf)
        if c.locatario.inscricao_municipal:
            ET.SubElement(ident_prestador, 'InscricaoMunicipal').text = c.locatario.inscricao_municipal

        razao_prest = c.locatario.razao_social.strip() or "Locatário Não Identificado"
        ET.SubElement(prestador_servico, 'RazaoSocial').text = razao_prest

        end_prest = ET.SubElement(prestador_servico, 'Endereco')
        ET.SubElement(end_prest, 'Endereco').text         = c.locatario.logradouro
        ET.SubElement(end_prest, 'Numero').text           = c.locatario.numero
        ET.SubElement(end_prest, 'Bairro').text           = c.locatario.bairro
        ET.SubElement(end_prest, 'CodigoMunicipio').text  = c.locatario.codigo_municipio
        ET.SubElement(end_prest, 'Uf').text               = c.locatario.uf
        ET.SubElement(end_prest, 'Cep').text              = self._digits(c.locatario.cep).zfill(8)

        if c.locatario.email or c.locatario.telefone:
            contato_prest = ET.SubElement(prestador_servico, 'Contato')
            if c.locatario.telefone:
                ET.SubElement(contato_prest, 'Telefone').text = self._digits(c.locatario.telefone)[:11]
            if c.locatario.email:
                ET.SubElement(contato_prest, 'Email').text = c.locatario.email[:80]

        # ---- OrgaoGerador ----
        orgao = ET.SubElement(inf_nfse, 'OrgaoGerador')
        ET.SubElement(orgao, 'CodigoMunicipio').text = cod_mun
        ET.SubElement(orgao, 'Uf').text              = c.locador.uf

        # ---- DeclaracaoPrestacaoServico ----
        decl     = ET.SubElement(inf_nfse, 'DeclaracaoPrestacaoServico')
        inf_decl = ET.SubElement(decl, 'InfDeclaracaoPrestacaoServico')

        ET.SubElement(inf_decl, 'Competencia').text       = c.data_emissao.strftime('%Y-%m-%d')
        ET.SubElement(inf_decl, 'NaturezaOperacao').text  = "1"
        ET.SubElement(inf_decl, 'Acumulador').text        = "916"   # ← TAG ACUMULADOR

        # ---- Servico ----
        servico = ET.SubElement(inf_decl, 'Servico')
        valores = ET.SubElement(servico, 'Valores')
        ET.SubElement(valores, 'ValorServicos').text         = f"{valor_servicos:.2f}"
        ET.SubElement(valores, 'IssRetido').text             = "1" if c.iss_retido else "2"
        ET.SubElement(valores, 'ValorIss').text              = f"{valor_iss:.2f}"
        ET.SubElement(valores, 'BaseCalculo').text           = f"{valor_servicos:.2f}"
        ET.SubElement(valores, 'Aliquota').text              = f"{c.aliquota_iss:.4f}"
        ET.SubElement(valores, 'DescontoIncondicionado').text = "0.00"
        ET.SubElement(valores, 'DescontoCondicionado').text  = "0.00"

        ET.SubElement(servico, 'ItemListaServico').text          = item_lista
        ET.SubElement(servico, 'CodigoTributacaoMunicipio').text = item_lista
        ET.SubElement(servico, 'CodigoCnae').text                = "0000000"
        ET.SubElement(servico, 'Discriminacao').text             = c.discriminacao
        ET.SubElement(servico, 'CodigoMunicipio').text           = cod_mun
        ET.SubElement(servico, 'ExigibilidadeISS').text          = "1"
        ET.SubElement(servico, 'MunicipioIncidencia').text       = cod_mun

        # ---- Prestador (dentro da Declaração) → Locatário ----
        prestador_decl     = ET.SubElement(inf_decl, 'Prestador')
        cpf_cnpj_prest_decl = ET.SubElement(prestador_decl, 'CpfCnpj')
        self._append_cpf_cnpj(cpf_cnpj_prest_decl, c.locatario.cnpj_cpf)
        if c.locatario.inscricao_municipal:
            ET.SubElement(prestador_decl, 'InscricaoMunicipal').text = c.locatario.inscricao_municipal

        # ---- Tomador → Locador ----
        tomador      = ET.SubElement(inf_decl, 'Tomador')
        ident_tomador = ET.SubElement(tomador, 'IdentificacaoTomador')
        cpf_cnpj_tom  = ET.SubElement(ident_tomador, 'CpfCnpj')
        self._append_cpf_cnpj(cpf_cnpj_tom, c.locador.cnpj_cpf)
        if c.locador.inscricao_municipal:
            ET.SubElement(ident_tomador, 'InscricaoMunicipal').text = c.locador.inscricao_municipal

        razao_tomador = c.locador.razao_social.strip() or "Locador Não Identificado"
        ET.SubElement(tomador, 'RazaoSocial').text = razao_tomador

        end_tomador = ET.SubElement(tomador, 'Endereco')
        ET.SubElement(end_tomador, 'Endereco').text        = c.locador.logradouro
        ET.SubElement(end_tomador, 'Numero').text          = c.locador.numero
        ET.SubElement(end_tomador, 'Bairro').text          = c.locador.bairro
        ET.SubElement(end_tomador, 'CodigoMunicipio').text = c.locador.codigo_municipio
        ET.SubElement(end_tomador, 'Uf').text              = c.locador.uf
        ET.SubElement(end_tomador, 'Cep').text             = self._digits(c.locador.cep).zfill(8)

        if c.locador.email or c.locador.telefone:
            contato_tom = ET.SubElement(tomador, 'Contato')
            if c.locador.telefone:
                ET.SubElement(contato_tom, 'Telefone').text = self._digits(c.locador.telefone)[:11]
            if c.locador.email:
                ET.SubElement(contato_tom, 'Email').text = c.locador.email[:80]

        ET.SubElement(inf_decl, 'OptanteSimplesNacional').text = "1" if c.optante_simples_nacional else "2"
        ET.SubElement(inf_decl, 'IncentivoFiscal').text        = "2"

        return root
