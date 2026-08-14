import xml.etree.ElementTree as ET
from ..models.nfe_produto_models import NfeProduto

NS_NFE = 'http://www.portalfiscal.inf.br/nfe'


class NfeProdutoTransformer:
    """
    Transformador para NF-e de PRODUTO (Modelo 55 - DANFE Estadual) REAL,
    extraída de um DANFE genuíno (`NfeProduto`) - ao contrário do
    `NfeTransformer` (que finge uma NF-e a partir de uma nota de SERVIÇO já
    parseada, com chave de acesso calculada e ICMS zerado como workaround),
    aqui a chave de acesso e os valores de ICMS/produtos são os REAIS do
    documento-fonte.
    """

    @staticmethod
    def _digits(value) -> str:
        return ''.join(ch for ch in (value or '') if ch.isdigit())

    def transform(self, nfe: NfeProduto) -> str:
        ET.register_namespace('', NS_NFE)

        cuf = nfe.chave_acesso[:2] if len(nfe.chave_acesso) == 44 else (nfe.emitente.endereco.codigo_municipio or "35")[:2]
        cnf = nfe.chave_acesso[35:43] if len(nfe.chave_acesso) == 44 else "00000000"
        cdv = nfe.chave_acesso[43] if len(nfe.chave_acesso) == 44 else "0"

        nfe_proc = ET.Element('nfeProc', xmlns=NS_NFE, versao="4.00")
        nfe_el = ET.SubElement(nfe_proc, 'NFe', xmlns=NS_NFE)

        inf_nfe = ET.SubElement(nfe_el, 'infNFe', Id=f"NFe{nfe.chave_acesso}", versao="4.00")

        ide = ET.SubElement(inf_nfe, 'ide')
        ET.SubElement(ide, 'cUF').text = cuf
        ET.SubElement(ide, 'cNF').text = cnf
        ET.SubElement(ide, 'natOp').text = nfe.natureza_operacao[:60]
        ET.SubElement(ide, 'mod').text = "55"
        ET.SubElement(ide, 'serie').text = nfe.serie.lstrip('0') or '1'
        ET.SubElement(ide, 'nNF').text = nfe.numero.lstrip('0') or '1'
        ET.SubElement(ide, 'dhEmi').text = nfe.data_emissao.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        if nfe.data_saida_entrada:
            ET.SubElement(ide, 'dhSaiEnt').text = nfe.data_saida_entrada.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        ET.SubElement(ide, 'tpNF').text = nfe.tipo_operacao
        ET.SubElement(ide, 'idDest').text = "1" if nfe.emitente.endereco.uf == nfe.destinatario.endereco.uf else "2"
        ET.SubElement(ide, 'cMunFG').text = nfe.emitente.endereco.codigo_municipio or "2927408"
        ET.SubElement(ide, 'tpImp').text = "1"
        ET.SubElement(ide, 'tpEmis').text = "1"
        ET.SubElement(ide, 'cDV').text = cdv
        ET.SubElement(ide, 'tpAmb').text = "1"
        ET.SubElement(ide, 'finNFe').text = "1"
        ET.SubElement(ide, 'indFinal').text = "1"
        ET.SubElement(ide, 'indPres').text = "0"
        ET.SubElement(ide, 'procEmi').text = "0"
        ET.SubElement(ide, 'verProc').text = "conversornotasabrasf_v1"

        emit = ET.SubElement(inf_nfe, 'emit')
        ET.SubElement(emit, 'CNPJ').text = self._digits(nfe.emitente.cnpj_cpf)
        ET.SubElement(emit, 'xNome').text = nfe.emitente.razao_social[:60]
        ender_emit = ET.SubElement(emit, 'enderEmit')
        ET.SubElement(ender_emit, 'xLgr').text = nfe.emitente.endereco.logradouro[:60] or "RUA NAO INFORMADA"
        ET.SubElement(ender_emit, 'nro').text = nfe.emitente.endereco.numero or "S/N"
        if nfe.emitente.endereco.complemento:
            ET.SubElement(ender_emit, 'xCpl').text = nfe.emitente.endereco.complemento[:60]
        ET.SubElement(ender_emit, 'xBairro').text = nfe.emitente.endereco.bairro[:60] or "BAIRRO"
        ET.SubElement(ender_emit, 'cMun').text = nfe.emitente.endereco.codigo_municipio or "2927408"
        ET.SubElement(ender_emit, 'xMun').text = nfe.emitente.endereco.municipio or "MUNICIPIO"
        ET.SubElement(ender_emit, 'UF').text = nfe.emitente.endereco.uf or "BA"
        ET.SubElement(ender_emit, 'CEP').text = self._digits(nfe.emitente.endereco.cep) or "00000000"
        if nfe.emitente.telefone:
            ET.SubElement(ender_emit, 'fone').text = self._digits(nfe.emitente.telefone)[:14]
        if nfe.emitente.inscricao_estadual:
            ET.SubElement(emit, 'IE').text = nfe.emitente.inscricao_estadual
        ET.SubElement(emit, 'CRT').text = "3"

        dest = ET.SubElement(inf_nfe, 'dest')
        doc_dest = self._digits(nfe.destinatario.cnpj_cpf)
        if len(doc_dest) == 14:
            ET.SubElement(dest, 'CNPJ').text = doc_dest
        else:
            ET.SubElement(dest, 'CPF').text = doc_dest.zfill(11)
        ET.SubElement(dest, 'xNome').text = nfe.destinatario.razao_social[:60]
        ender_dest = ET.SubElement(dest, 'enderDest')
        ET.SubElement(ender_dest, 'xLgr').text = nfe.destinatario.endereco.logradouro[:60] or "RUA NAO INFORMADA"
        ET.SubElement(ender_dest, 'nro').text = nfe.destinatario.endereco.numero or "S/N"
        ET.SubElement(ender_dest, 'xBairro').text = nfe.destinatario.endereco.bairro[:60] or "BAIRRO"
        ET.SubElement(ender_dest, 'cMun').text = nfe.destinatario.endereco.codigo_municipio or "2927408"
        ET.SubElement(ender_dest, 'xMun').text = nfe.destinatario.endereco.municipio or "MUNICIPIO"
        ET.SubElement(ender_dest, 'UF').text = nfe.destinatario.endereco.uf or "BA"
        ET.SubElement(ender_dest, 'CEP').text = self._digits(nfe.destinatario.endereco.cep) or "00000000"
        ET.SubElement(dest, 'indIEDest').text = "9"

        vprod_total = 0.0
        for idx, item in enumerate(nfe.itens, start=1):
            det = ET.SubElement(inf_nfe, 'det', nItem=str(idx))
            prod = ET.SubElement(det, 'prod')
            ET.SubElement(prod, 'cProd').text = item.codigo[:60]
            ET.SubElement(prod, 'cEAN').text = "SEM GTIN"
            ET.SubElement(prod, 'xProd').text = item.descricao[:120]
            ET.SubElement(prod, 'NCM').text = item.ncm
            ET.SubElement(prod, 'CFOP').text = item.cfop
            ET.SubElement(prod, 'uCom').text = item.unidade[:6] or "UN"
            ET.SubElement(prod, 'qCom').text = f"{item.quantidade:.4f}"
            ET.SubElement(prod, 'vUnCom').text = f"{item.valor_unitario:.4f}"
            ET.SubElement(prod, 'vProd').text = f"{item.valor_total:.2f}"
            ET.SubElement(prod, 'cEANTrib').text = "SEM GTIN"
            ET.SubElement(prod, 'uTrib').text = item.unidade[:6] or "UN"
            ET.SubElement(prod, 'qTrib').text = f"{item.quantidade:.4f}"
            ET.SubElement(prod, 'vUnTrib').text = f"{item.valor_unitario:.4f}"
            ET.SubElement(prod, 'indTot').text = "1"

            imposto = ET.SubElement(det, 'imposto')
            icms = ET.SubElement(imposto, 'ICMS')
            icms_grupo = ET.SubElement(icms, 'ICMS00' if item.aliquota_icms > 0 else 'ICMS40')
            ET.SubElement(icms_grupo, 'orig').text = "0"
            ET.SubElement(icms_grupo, 'CST').text = item.cst_icms or "00"
            if item.aliquota_icms > 0:
                ET.SubElement(icms_grupo, 'modBC').text = "3"
                ET.SubElement(icms_grupo, 'vBC').text = f"{item.base_calculo_icms:.2f}"
                ET.SubElement(icms_grupo, 'pICMS').text = f"{item.aliquota_icms:.2f}"
                ET.SubElement(icms_grupo, 'vICMS').text = f"{item.valor_icms:.2f}"

            if item.valor_ipi > 0:
                ipi = ET.SubElement(imposto, 'IPI')
                ipi_trib = ET.SubElement(ipi, 'IPITrib')
                ET.SubElement(ipi_trib, 'CST').text = "50"
                ET.SubElement(ipi_trib, 'vBC').text = f"{item.valor_total:.2f}"
                ET.SubElement(ipi_trib, 'pIPI').text = f"{item.aliquota_ipi:.2f}"
                ET.SubElement(ipi_trib, 'vIPI').text = f"{item.valor_ipi:.2f}"

            pis = ET.SubElement(imposto, 'PIS')
            pis_outr = ET.SubElement(pis, 'PISOutr')
            ET.SubElement(pis_outr, 'CST').text = "99"
            ET.SubElement(pis_outr, 'vBC').text = "0.00"
            ET.SubElement(pis_outr, 'pPIS').text = "0.00"
            ET.SubElement(pis_outr, 'vPIS').text = "0.00"

            cofins = ET.SubElement(imposto, 'COFINS')
            cofins_outr = ET.SubElement(cofins, 'COFINSOutr')
            ET.SubElement(cofins_outr, 'CST').text = "99"
            ET.SubElement(cofins_outr, 'vBC').text = "0.00"
            ET.SubElement(cofins_outr, 'pCOFINS').text = "0.00"
            ET.SubElement(cofins_outr, 'vCOFINS').text = "0.00"

            vprod_total += item.valor_total

        total = ET.SubElement(inf_nfe, 'total')
        icms_tot = ET.SubElement(total, 'ICMSTot')
        v = nfe.valores
        fields = [
            ('vBC', v.base_calculo_icms), ('vICMS', v.valor_icms), ('vICMSDeson', 0.0), ('vFCP', 0.0),
            ('vBCST', v.base_calculo_icms_st), ('vST', v.valor_icms_st), ('vFCPST', 0.0), ('vFCPSTRet', 0.0),
            ('vProd', v.valor_total_produtos or vprod_total), ('vFrete', v.valor_frete), ('vSeg', v.valor_seguro),
            ('vDesc', v.desconto), ('vII', 0.0), ('vIPI', v.valor_ipi), ('vIPIDevol', 0.0),
            ('vPIS', 0.0), ('vCOFINS', 0.0), ('vOutro', v.outras_despesas),
            ('vNF', v.valor_total_nota),
        ]
        for tag, val in fields:
            ET.SubElement(icms_tot, tag).text = f"{val:.2f}"

        transp = ET.SubElement(inf_nfe, 'transp')
        transportador = nfe.transportador
        ET.SubElement(transp, 'modFrete').text = (transportador.frete_por_conta if transportador and transportador.frete_por_conta else "9")
        if transportador and (transportador.razao_social or transportador.cnpj_cpf):
            transporta = ET.SubElement(transp, 'transporta')
            if transportador.cnpj_cpf:
                doc_transp = self._digits(transportador.cnpj_cpf)
                if len(doc_transp) == 14:
                    ET.SubElement(transporta, 'CNPJ').text = doc_transp
                elif doc_transp:
                    ET.SubElement(transporta, 'CPF').text = doc_transp.zfill(11)
            if transportador.razao_social:
                ET.SubElement(transporta, 'xNome').text = transportador.razao_social[:60]
            if transportador.inscricao_estadual:
                ET.SubElement(transporta, 'IE').text = transportador.inscricao_estadual
            if transportador.uf:
                ET.SubElement(transporta, 'UF').text = transportador.uf
        if transportador and (transportador.peso_bruto or transportador.peso_liquido):
            vol = ET.SubElement(transp, 'vol')
            if transportador.quantidade_volumes:
                ET.SubElement(vol, 'qVol').text = f"{transportador.quantidade_volumes:.0f}"
            if transportador.peso_liquido:
                ET.SubElement(vol, 'pesoL').text = f"{transportador.peso_liquido:.3f}"
            if transportador.peso_bruto:
                ET.SubElement(vol, 'pesoB').text = f"{transportador.peso_bruto:.3f}"

        cobr = None
        if nfe.fatura_duplicata:
            cobr = ET.SubElement(inf_nfe, 'cobr')
            fat = ET.SubElement(cobr, 'fat')
            ET.SubElement(fat, 'nFat').text = nfe.numero.lstrip('0') or '1'
            ET.SubElement(fat, 'vOrig').text = f"{v.valor_total_nota:.2f}"
            ET.SubElement(fat, 'vLiq').text = f"{v.valor_total_nota:.2f}"

        pag = ET.SubElement(inf_nfe, 'pag')
        det_pag = ET.SubElement(pag, 'detPag')
        ET.SubElement(det_pag, 'tPag').text = "99"
        ET.SubElement(det_pag, 'vPag').text = f"{v.valor_total_nota:.2f}"

        if nfe.informacoes_complementares:
            inf_adic = ET.SubElement(inf_nfe, 'infAdic')
            ET.SubElement(inf_adic, 'infCpl').text = nfe.informacoes_complementares[:5000]

        if nfe.protocolo_autorizacao:
            prot_nfe = ET.SubElement(nfe_proc, 'protNFe', versao="4.00")
            inf_prot = ET.SubElement(prot_nfe, 'infProt')
            ET.SubElement(inf_prot, 'tpAmb').text = "1"
            ET.SubElement(inf_prot, 'chNFe').text = nfe.chave_acesso
            dh_recbto = nfe.protocolo_data_hora or nfe.data_emissao
            ET.SubElement(inf_prot, 'dhRecbto').text = dh_recbto.strftime('%Y-%m-%dT%H:%M:%S-03:00')
            ET.SubElement(inf_prot, 'nProt').text = nfe.protocolo_autorizacao
            ET.SubElement(inf_prot, 'digVal').text = ""
            ET.SubElement(inf_prot, 'cStat').text = "100"
            ET.SubElement(inf_prot, 'xMotivo').text = "Autorizado o uso da NF-e"

        ET.indent(nfe_proc, space='  ')
        return ET.tostring(nfe_proc, encoding='utf-8', xml_declaration=True).decode('utf-8')
