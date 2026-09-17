import xml.etree.ElementTree as ET
from ..models.cte_os_model import CteOS

NS_CTE = 'http://www.portalfiscal.inf.br/cte'


class CteTransformer:
    """
    Transformador para CT-e OS (Conhecimento de Transporte Eletrônico para
    Outros Serviços) - Modelo 67, DACTE OS - REAL, extraído de um documento
    genuíno (`CteOS`, ver LAYOUT_DACTE_OS). Gera um XML estruturalmente FIEL
    ao padrão nacional do CT-e no que importa para não misrepresentar o
    documento: raiz `cteProc`/`CTe`/`infCte`, `mod=67`, namespace
    `.../cte` - DELIBERADAMENTE distinto do `NfeProdutoTransformer`
    (`infNFe`/`mod=55`, namespace `.../nfe`). Um CT-e é um documento fiscal
    diferente de uma NF-e de mercadoria (não tem tabela de itens/NCM - o que
    se transporta é um SERVIÇO), e usar as tags de NF-e para representá-lo
    seria uma inverdade estrutural equivalente a fabricar dado fiscal.

    Não é uma reprodução byte-a-byte do XSD oficial de transmissão do CT-e
    (que já ocorreu - o documento-fonte já traz protocolo de autorização; o
    objetivo aqui é representar fielmente os dados extraídos para uso
    contábil, não retransmitir à SEFAZ) - mesmo nível de fidelidade já
    aplicado pelo `NfeProdutoTransformer` (sem bloco de assinatura digital,
    por exemplo). Blocos sem equivalente oficial direto no CT-e (retenções
    federais PIS/COFINS/IR/INSS/CSLL, que o gerador "Master CT-e" imprime na
    mesma grade do ICMS) ficam num elemento `retencoes` próprio, não
    forçados dentro de `imp/ICMS`. Chave de acesso e valores são os REAIS do
    documento-fonte.
    """

    @staticmethod
    def _digits(value) -> str:
        return ''.join(ch for ch in (value or '') if ch.isdigit())

    def transform(self, cte: CteOS) -> str:
        ET.register_namespace('', NS_CTE)

        chave = cte.chave_acesso
        cuf = chave[:2] if len(chave) == 44 else (cte.emitente.endereco.codigo_municipio or "29")[:2]
        cdv = chave[43] if len(chave) == 44 else "0"

        cte_proc = ET.Element('cteProc', xmlns=NS_CTE, versao="4.00")
        cte_el = ET.SubElement(cte_proc, 'CTe', xmlns=NS_CTE)
        inf_cte = ET.SubElement(cte_el, 'infCte', Id=f"CTe{chave}", versao="4.00")

        ide = ET.SubElement(inf_cte, 'ide')
        ET.SubElement(ide, 'cUF').text = cuf
        ET.SubElement(ide, 'CFOP').text = cte.cfop
        ET.SubElement(ide, 'natOp').text = cte.natureza_operacao[:60]
        ET.SubElement(ide, 'mod').text = cte.modelo
        ET.SubElement(ide, 'serie').text = cte.serie.lstrip('0') or '1'
        ET.SubElement(ide, 'nCT').text = cte.numero.lstrip('0') or '1'
        ET.SubElement(ide, 'dhEmi').text = cte.data_emissao.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        ET.SubElement(ide, 'tpImp').text = "1"
        ET.SubElement(ide, 'tpEmis').text = "1"
        ET.SubElement(ide, 'cDV').text = cdv
        ET.SubElement(ide, 'tpAmb').text = "1"
        ET.SubElement(ide, 'tpCTe').text = "0" if cte.tipo_cte.strip().lower() == "normal" else "3"
        ET.SubElement(ide, 'tpServico').text = cte.tipo_servico
        ET.SubElement(ide, 'procEmi').text = "0"
        ET.SubElement(ide, 'verProc').text = "conversornotasabrasf_v1"
        ET.SubElement(ide, 'cMunIni').text = cte.codigo_municipio_inicio or ""
        ET.SubElement(ide, 'xMunIni').text = cte.municipio_inicio_prestacao or ""
        ET.SubElement(ide, 'cMunFim').text = cte.codigo_municipio_fim or ""
        ET.SubElement(ide, 'xMunFim').text = cte.municipio_fim_prestacao or ""
        if cte.protocolo_autorizacao:
            ET.SubElement(ide, 'nProt').text = cte.protocolo_autorizacao
        if cte.protocolo_data_hora:
            ET.SubElement(ide, 'dhRecbto').text = cte.protocolo_data_hora.strftime('%Y-%m-%dT%H:%M:%S-03:00')

        emit = ET.SubElement(inf_cte, 'emit')
        ET.SubElement(emit, 'CNPJ').text = self._digits(cte.emitente.cnpj_cpf)
        ET.SubElement(emit, 'xNome').text = cte.emitente.razao_social[:60]
        if cte.emitente.inscricao_estadual:
            ET.SubElement(emit, 'IE').text = cte.emitente.inscricao_estadual
        ender_emit = ET.SubElement(emit, 'enderEmit')
        ET.SubElement(ender_emit, 'xLgr').text = cte.emitente.endereco.logradouro[:60] or "RUA NAO INFORMADA"
        ET.SubElement(ender_emit, 'nro').text = cte.emitente.endereco.numero or "S/N"
        if cte.emitente.endereco.complemento:
            ET.SubElement(ender_emit, 'xCpl').text = cte.emitente.endereco.complemento[:60]
        ET.SubElement(ender_emit, 'xBairro').text = cte.emitente.endereco.bairro[:60] or "BAIRRO"
        ET.SubElement(ender_emit, 'cMun').text = cte.emitente.endereco.codigo_municipio or ""
        ET.SubElement(ender_emit, 'xMun').text = cte.emitente.endereco.municipio or ""
        ET.SubElement(ender_emit, 'UF').text = cte.emitente.endereco.uf or ""
        ET.SubElement(ender_emit, 'CEP').text = self._digits(cte.emitente.endereco.cep) or "00000000"
        if cte.emitente.telefone:
            ET.SubElement(ender_emit, 'fone').text = self._digits(cte.emitente.telefone)[:14]

        # `toma` (tomador do serviço) - CT-e OS não carrega o tomador dentro
        # de "toma3/toma4" da grade padrão de carga (que referenciam papéis
        # de remetente/destinatário/expedidor/recebedor de MERCADORIA, sem
        # sentido para transporte de pessoas); representado aqui de forma
        # direta, como o próprio DACTE OS imprime ("TOMADOR DO SERVIÇO").
        toma = ET.SubElement(inf_cte, 'toma')
        doc_toma = self._digits(cte.tomador.cnpj_cpf)
        if len(doc_toma) == 14:
            ET.SubElement(toma, 'CNPJ').text = doc_toma
        else:
            ET.SubElement(toma, 'CPF').text = doc_toma.zfill(11)
        ET.SubElement(toma, 'xNome').text = cte.tomador.razao_social[:60]
        if cte.tomador.inscricao_estadual:
            ET.SubElement(toma, 'IE').text = cte.tomador.inscricao_estadual
        ender_toma = ET.SubElement(toma, 'enderToma')
        ET.SubElement(ender_toma, 'xLgr').text = cte.tomador.endereco.logradouro[:60] or "RUA NAO INFORMADA"
        ET.SubElement(ender_toma, 'nro').text = cte.tomador.endereco.numero or "S/N"
        if cte.tomador.endereco.complemento:
            ET.SubElement(ender_toma, 'xCpl').text = cte.tomador.endereco.complemento[:60]
        ET.SubElement(ender_toma, 'xBairro').text = cte.tomador.endereco.bairro[:60] or "BAIRRO"
        ET.SubElement(ender_toma, 'cMun').text = cte.tomador.endereco.codigo_municipio or ""
        ET.SubElement(ender_toma, 'xMun').text = cte.tomador.endereco.municipio or ""
        ET.SubElement(ender_toma, 'UF').text = cte.tomador.endereco.uf or ""
        ET.SubElement(ender_toma, 'CEP').text = self._digits(cte.tomador.endereco.cep) or "00000000"
        if cte.tomador.email:
            ET.SubElement(toma, 'email').text = cte.tomador.email

        servico = ET.SubElement(inf_cte, 'infServico')
        ET.SubElement(servico, 'xDescServ').text = cte.descricao_servico[:2000]
        ET.SubElement(servico, 'qCarga').text = f"{cte.quantidade_servico:.4f}"

        imp = ET.SubElement(inf_cte, 'imp')
        icms = ET.SubElement(imp, 'ICMS')
        icms00 = ET.SubElement(icms, 'ICMS00')
        ET.SubElement(icms00, 'vBC').text = f"{cte.imposto.base_calculo_icms:.2f}"
        ET.SubElement(icms00, 'pICMS').text = f"{cte.imposto.aliquota_icms:.2f}"
        ET.SubElement(icms00, 'vICMS').text = f"{cte.imposto.valor_icms:.2f}"
        if cte.imposto.percentual_reducao_bc:
            ET.SubElement(icms00, 'pRedBC').text = f"{cte.imposto.percentual_reducao_bc:.2f}"
        if cte.imposto.valor_icms_st:
            ET.SubElement(icms00, 'vICMSST').text = f"{cte.imposto.valor_icms_st:.2f}"

        # Retenções federais sobre o pagamento do serviço (PIS/COFINS/IR/
        # INSS/CSLL) - sem tag equivalente no schema oficial do CT-e, que só
        # trata ICMS; o gerador de origem ("Master CT-e") as imprime na
        # mesma grade "INFORMAÇÕES RELATIVAS AO IMPOSTO" do documento.
        retencoes = ET.SubElement(inf_cte, 'retencoes')
        ET.SubElement(retencoes, 'vPIS').text = f"{cte.imposto.valor_pis:.2f}"
        ET.SubElement(retencoes, 'vCOFINS').text = f"{cte.imposto.valor_cofins:.2f}"
        ET.SubElement(retencoes, 'vIR').text = f"{cte.imposto.valor_ir:.2f}"
        ET.SubElement(retencoes, 'vINSS').text = f"{cte.imposto.valor_inss:.2f}"
        ET.SubElement(retencoes, 'vCSLL').text = f"{cte.imposto.valor_csll:.2f}"

        total = ET.SubElement(inf_cte, 'total')
        ET.SubElement(total, 'vTPrest').text = f"{cte.valor_total_prestacao:.2f}"
        ET.SubElement(total, 'vRec').text = f"{cte.valor_a_receber:.2f}"

        if cte.modal_rodoviario:
            rodo = ET.SubElement(inf_cte, 'infModal')
            rodo_os = ET.SubElement(rodo, 'rodoOS')
            if cte.modal_rodoviario.registro_estadual:
                ET.SubElement(rodo_os, 'NroRegEstadual').text = cte.modal_rodoviario.registro_estadual
            if cte.modal_rodoviario.placa_veiculo:
                ET.SubElement(rodo_os, 'placa').text = cte.modal_rodoviario.placa_veiculo
            if cte.modal_rodoviario.renavam:
                ET.SubElement(rodo_os, 'renavam').text = cte.modal_rodoviario.renavam
            if cte.modal_rodoviario.uf_licenciamento:
                ET.SubElement(rodo_os, 'UFLic').text = cte.modal_rodoviario.uf_licenciamento
            if cte.modal_rodoviario.cnpj_cpf_responsavel:
                ET.SubElement(rodo_os, 'RNTRC').text = cte.modal_rodoviario.cnpj_cpf_responsavel

        # `cte.observacoes` já inclui a linha "NUMERO DO PEDIDO: ..." (faz
        # parte do mesmo bloco impresso na nota) - `numero_pedido` não é
        # reconcatenado aqui para não duplicar a informação no `xObs`.
        if cte.observacoes:
            compl = ET.SubElement(inf_cte, 'compl')
            ET.SubElement(compl, 'xObs').text = cte.observacoes[:2000]

        if cte.protocolo_autorizacao:
            prot_cte = ET.SubElement(cte_proc, 'protCTe', versao="4.00")
            inf_prot = ET.SubElement(prot_cte, 'infProt')
            ET.SubElement(inf_prot, 'tpAmb').text = "1"
            ET.SubElement(inf_prot, 'chCTe').text = chave
            dh_recbto = cte.protocolo_data_hora or cte.data_emissao
            ET.SubElement(inf_prot, 'dhRecbto').text = dh_recbto.strftime('%Y-%m-%dT%H:%M:%S-03:00')
            ET.SubElement(inf_prot, 'nProt').text = cte.protocolo_autorizacao
            ET.SubElement(inf_prot, 'digVal').text = ""
            ET.SubElement(inf_prot, 'cStat').text = "100"
            ET.SubElement(inf_prot, 'xMotivo').text = "Autorizado o uso do CT-e"

        ET.indent(cte_proc, space='  ')
        return ET.tostring(cte_proc, encoding='utf-8', xml_declaration=True).decode('utf-8')
