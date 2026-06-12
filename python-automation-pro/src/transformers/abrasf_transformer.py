import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List
from ..models.nfse_models import Nfse

NS_ABRASF = 'http://www.abrasf.org.br/nfse.xsd'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'

class Abrasf201Transformer:
    """Transformador para gerar XML no padrão ABRASF 2.01."""
    @staticmethod
    def _digits(value: str) -> str:
        return ''.join(ch for ch in (value or '') if ch.isdigit())

    def _append_cpf_cnpj(self, parent, raw_doc: str, preferred: str = "cnpj"):
        """
        Garante geração consistente de CPF/CNPJ para evitar
        'Tipo de Inscrição não identificado' no importador.
        """
        doc = self._digits(raw_doc)
        if len(doc) == 14:
            ET.SubElement(parent, 'Cnpj').text = doc
            return
        if len(doc) == 11:
            ET.SubElement(parent, 'Cpf').text = doc
            return
        # Fallback seguro quando OCR/extrator não trouxe documento limpo.
        if preferred == "cpf":
            ET.SubElement(parent, 'Cpf').text = doc[:11].zfill(11)
        else:
            ET.SubElement(parent, 'Cnpj').text = doc[:14].zfill(14)

    @staticmethod
    def _format_competencia(nfse: Nfse) -> str:
        comp = getattr(nfse, "competencia", None) or nfse.data_emissao
        return comp.strftime('%Y-%m-%d')

    def transform(self, nfse: Nfse) -> str:
        # Registra namespaces (ajuda em alguns casos de tostring)
        ET.register_namespace('', NS_ABRASF)
        ET.register_namespace('xsi', NS_XSI)

        root = self._build_comp_nfse(nfse)
        
        ET.indent(root, space='  ')
        return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')

    def transform_batch(self, nfse_list: List[Nfse]) -> str:
        """Gera um arquivo XML contendo múltiplas CompNfse envoltas em um elemento raiz."""
        ET.register_namespace('', NS_ABRASF)
        ET.register_namespace('xsi', NS_XSI)
        
        # Elemento raiz para o lote (padrão comum para importação de múltiplas notas)
        root = ET.Element('ListaNfse')
        root.set('xmlns', NS_ABRASF)
        
        for nfse in nfse_list:
            comp_nfse = self._build_comp_nfse(nfse)
            root.append(comp_nfse)
            
        ET.indent(root, space='  ')
        return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8')

    def _build_comp_nfse(self, nfse: Nfse) -> ET.Element:
        # Root element in the ABRASF namespace (usando tags simples e xmlns explícito)
        root = ET.Element('CompNfse')
        # root.set('xmlns', NS_ABRASF) # O namespace já é gerenciado pelo register_namespace e root do lote
        
        nfse_xml = ET.SubElement(root, 'Nfse', versao="2.01")
        inf_nfse = ET.SubElement(nfse_xml, 'InfNfse', Id=f"NFSe{nfse.numero}")
        
        ET.SubElement(inf_nfse, 'Numero').text = nfse.numero
        
        codigo_ver = getattr(nfse, 'codigo_verificacao', getattr(nfse, 'codigoVerificacao', "000000000"))
        if not codigo_ver:
            codigo_ver = "000000000"
        ET.SubElement(inf_nfse, 'CodigoVerificacao').text = codigo_ver
        
        ET.SubElement(inf_nfse, 'DataEmissao').text = nfse.data_emissao.strftime('%Y-%m-%dT%H:%M:%S')
        ET.SubElement(inf_nfse, 'Competencia').text = self._format_competencia(nfse)
        ET.SubElement(inf_nfse, 'OutrasInformacoes').text = "Convertido de PDF - ABRASF 2.01"

        valores_nfse = ET.SubElement(inf_nfse, 'ValoresNfse')
        ET.SubElement(valores_nfse, 'ValorServicos').text = f"{nfse.valores.valor_servicos:.2f}"
        ET.SubElement(valores_nfse, 'ValorDeducoes').text = f"{nfse.valores.valor_deducoes:.2f}"
        ET.SubElement(valores_nfse, 'ValorPis').text = f"{nfse.valores.valor_pis:.2f}"
        ET.SubElement(valores_nfse, 'ValorCofins').text = f"{nfse.valores.valor_cofins:.2f}"
        ET.SubElement(valores_nfse, 'ValorInss').text = f"{nfse.valores.valor_inss:.2f}"
        ET.SubElement(valores_nfse, 'ValorIr').text = f"{nfse.valores.valor_ir:.2f}"
        ET.SubElement(valores_nfse, 'ValorCsll').text = f"{nfse.valores.valor_csll:.2f}"
        ET.SubElement(valores_nfse, 'OutrasRetencoes').text = f"{nfse.valores.outras_retencoes:.2f}"
        ET.SubElement(valores_nfse, 'BaseCalculo').text = f"{nfse.valores.base_calculo:.2f}"
        ET.SubElement(valores_nfse, 'Aliquota').text = f"{nfse.valores.aliquota:.2f}"
        ET.SubElement(valores_nfse, 'ValorIss').text = f"{nfse.valores.valor_iss:.2f}"
        ET.SubElement(valores_nfse, 'ValorLiquidoNfse').text = f"{nfse.valores.valor_liquido_nfse:.2f}"
        
        ET.SubElement(inf_nfse, 'ValorCredito').text = "0.00"
        
        prestador_servico = ET.SubElement(inf_nfse, 'PrestadorServico')
        ident_prestador = ET.SubElement(prestador_servico, 'IdentificacaoPrestador')
        self._append_cpf_cnpj(ident_prestador, nfse.prestador.cnpj_cpf, preferred="cnpj")
        if nfse.prestador.inscricao_municipal:
            ET.SubElement(ident_prestador, 'InscricaoMunicipal').text = nfse.prestador.inscricao_municipal

        # Domínio exige O NOME do fornecedor. Se regex limpou demais e esvaziou, inserir padrão:
        razao_prest = nfse.prestador.razao_social.strip()
        if not razao_prest: razao_prest = "Prestador Não Identificado na Extração"
        ET.SubElement(prestador_servico, 'RazaoSocial').text = razao_prest
        
        end_prestador = ET.SubElement(prestador_servico, 'Endereco')
        cod_mun_prestador = nfse.prestador.endereco.codigo_municipio if (nfse.prestador and nfse.prestador.endereco) else "3550308"
        ET.SubElement(end_prestador, 'Endereco').text = nfse.prestador.endereco.logradouro or "Não informado"
        ET.SubElement(end_prestador, 'Numero').text = nfse.prestador.endereco.numero or "S/N"
        ET.SubElement(end_prestador, 'Bairro').text = nfse.prestador.endereco.bairro or "Não informado"
        ET.SubElement(end_prestador, 'CodigoMunicipio').text = cod_mun_prestador
        ET.SubElement(end_prestador, 'Uf').text = nfse.prestador.endereco.uf or "SP"
        ET.SubElement(end_prestador, 'Cep').text = self._digits(nfse.prestador.endereco.cep) or "00000000"

        if nfse.prestador.email or nfse.prestador.telefone:
            contato_prest = ET.SubElement(prestador_servico, 'Contato')
            if nfse.prestador.telefone:
                ET.SubElement(contato_prest, 'Telefone').text = self._digits(nfse.prestador.telefone)[:11]
            if nfse.prestador.email:
                ET.SubElement(contato_prest, 'Email').text = nfse.prestador.email[:80]
        
        orgao_gerador = ET.SubElement(inf_nfse, 'OrgaoGerador')
        ET.SubElement(orgao_gerador, 'CodigoMunicipio').text = cod_mun_prestador
        
        uf_prestador = nfse.prestador.endereco.uf or "SP"
        ET.SubElement(orgao_gerador, 'Uf').text = uf_prestador

        decl = ET.SubElement(inf_nfse, 'DeclaracaoPrestacaoServico')
        inf_decl = ET.SubElement(decl, 'InfDeclaracaoPrestacaoServico')
        
        ET.SubElement(inf_decl, 'Competencia').text = self._format_competencia(nfse)
        
        # NaturezaOperacao: 1-Tributação no município, 2-Tributação fora, etc.
        # Domínio usa isso para definir o acumulador.
        ET.SubElement(inf_decl, 'NaturezaOperacao').text = "1"
        
        # RegimeEspecialTributacao: 5-MEI, 6-ME/EPP (Simples Nacional)
        if nfse.regime_especial_tributacao:
            ET.SubElement(inf_decl, 'RegimeEspecialTributacao').text = nfse.regime_especial_tributacao
        elif nfse.optante_simples_nacional:
            ET.SubElement(inf_decl, 'RegimeEspecialTributacao').text = "6"

        servico = ET.SubElement(inf_decl, 'Servico')
        valores = ET.SubElement(servico, 'Valores')
        ET.SubElement(valores, 'ValorServicos').text = f"{nfse.valores.valor_servicos:.2f}"
        ET.SubElement(valores, 'ValorDeducoes').text = f"{nfse.valores.valor_deducoes:.2f}"
        ET.SubElement(valores, 'ValorPis').text = f"{nfse.valores.valor_pis:.2f}"
        ET.SubElement(valores, 'ValorCofins').text = f"{nfse.valores.valor_cofins:.2f}"
        ET.SubElement(valores, 'ValorInss').text = f"{nfse.valores.valor_inss:.2f}"
        ET.SubElement(valores, 'ValorIr').text = f"{nfse.valores.valor_ir:.2f}"
        ET.SubElement(valores, 'ValorCsll').text = f"{nfse.valores.valor_csll:.2f}"
        ET.SubElement(valores, 'OutrasRetencoes').text = f"{nfse.valores.outras_retencoes:.2f}"
        if getattr(nfse.valores, 'valor_iss_retido', 0) > 0 or nfse.valores.iss_retido:
            ET.SubElement(valores, 'ValorIssRetido').text = f"{getattr(nfse.valores, 'valor_iss_retido', 0.0):.2f}"
        ET.SubElement(valores, 'IssRetido').text = "1" if nfse.valores.iss_retido else "2"
        ET.SubElement(valores, 'ValorIss').text = f"{nfse.valores.valor_iss:.2f}"
        ET.SubElement(valores, 'BaseCalculo').text = f"{nfse.valores.base_calculo:.2f}"
        ET.SubElement(valores, 'Aliquota').text = f"{nfse.valores.aliquota:.2f}"
        ET.SubElement(valores, 'DescontoIncondicionado').text = "0.00"
        ET.SubElement(valores, 'DescontoCondicionado').text = "0.00"
        
        # Formatação do ItemListaServico (ABRASF costuma esperar 4 dígitos sem pontos, ex: 0101, ou o formato da LC116)
        # Se vier algo como "1.05", transformamos em "0105" ou mantemos dependendo do sistema
        # Para máxima compatibilidade, garantimos que tenha pelo menos 4 caracteres.
        item_lista = nfse.servico_codigo.replace('.', '').zfill(4)
        ET.SubElement(servico, 'ItemListaServico').text = item_lista
        
        # Código de Tributação do Município (muitas vezes igual ao item da lista ou vazio)
        ET.SubElement(servico, 'CodigoTributacaoMunicipio').text = item_lista
        
        # O Domínio exige a tag explícita de CodigoCnae
        ET.SubElement(servico, 'CodigoCnae').text = "0000000"
        
        ET.SubElement(servico, 'Discriminacao').text = nfse.discriminacao
        ET.SubElement(servico, 'CodigoMunicipio').text = cod_mun_prestador
        ET.SubElement(servico, 'ExigibilidadeISS').text = "1"
        ET.SubElement(servico, 'MunicipioIncidencia').text = cod_mun_prestador
        
        prestador_decl = ET.SubElement(inf_decl, 'Prestador')
        cpf_cnpj_prestador_decl = ET.SubElement(prestador_decl, 'CpfCnpj')
        self._append_cpf_cnpj(cpf_cnpj_prestador_decl, nfse.prestador.cnpj_cpf, preferred="cnpj")
        if nfse.prestador.inscricao_municipal:
            ET.SubElement(prestador_decl, 'InscricaoMunicipal').text = nfse.prestador.inscricao_municipal
            
        tomador = ET.SubElement(inf_decl, 'Tomador')
        ident_tomador = ET.SubElement(tomador, 'IdentificacaoTomador')
        cpf_cnpj = ET.SubElement(ident_tomador, 'CpfCnpj')
        self._append_cpf_cnpj(cpf_cnpj, nfse.tomador.cnpj_cpf, preferred="cnpj")
            
        if nfse.tomador.inscricao_municipal:
            ET.SubElement(ident_tomador, 'InscricaoMunicipal').text = nfse.tomador.inscricao_municipal

        # Prevenção contra Tomador sem nome
        razao_tomador = nfse.tomador.razao_social.strip()
        if not razao_tomador: razao_tomador = "Tomador Não Identificado na Extração"
        ET.SubElement(tomador, 'RazaoSocial').text = razao_tomador
        
        end_tomador = ET.SubElement(tomador, 'Endereco')
        ET.SubElement(end_tomador, 'Endereco').text = nfse.tomador.endereco.logradouro or "Não informado"
        ET.SubElement(end_tomador, 'Numero').text = nfse.tomador.endereco.numero or "S/N"
        ET.SubElement(end_tomador, 'Bairro').text = nfse.tomador.endereco.bairro or "Não informado"
        ET.SubElement(end_tomador, 'CodigoMunicipio').text = nfse.tomador.endereco.codigo_municipio or "3550308"
        ET.SubElement(end_tomador, 'Uf').text = nfse.tomador.endereco.uf or "SP"
        ET.SubElement(end_tomador, 'Cep').text = self._digits(nfse.tomador.endereco.cep) or "00000000"

        if nfse.tomador.email or nfse.tomador.telefone:
            contato_tomador = ET.SubElement(tomador, 'Contato')
            if nfse.tomador.telefone:
                ET.SubElement(contato_tomador, 'Telefone').text = self._digits(nfse.tomador.telefone)[:11]
            if nfse.tomador.email:
                ET.SubElement(contato_tomador, 'Email').text = nfse.tomador.email[:80]
                
        if getattr(nfse, 'intermediario', None):
            intermediario = ET.SubElement(inf_decl, 'Intermediario')
            ident_inter = ET.SubElement(intermediario, 'IdentificacaoIntermediario')
            cpf_cnpj_inter = ET.SubElement(ident_inter, 'CpfCnpj')
            self._append_cpf_cnpj(cpf_cnpj_inter, nfse.intermediario.cnpj_cpf, preferred="cnpj")
            
            if nfse.intermediario.inscricao_municipal:
                ET.SubElement(ident_inter, 'InscricaoMunicipal').text = nfse.intermediario.inscricao_municipal
                
            razao_inter = nfse.intermediario.razao_social.strip()
            if not razao_inter: razao_inter = "Intermediário Não Identificado"
            ET.SubElement(intermediario, 'RazaoSocial').text = razao_inter
            
        ET.SubElement(inf_decl, 'OptanteSimplesNacional').text = "1" if getattr(nfse, 'optante_simples_nacional', False) else "2"
        ET.SubElement(inf_decl, 'IncentivoFiscal').text = "1" if getattr(nfse, 'incentivador_cultural', False) else "2"

        return root
