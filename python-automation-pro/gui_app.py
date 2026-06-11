import flet as ft
import os
import threading
from datetime import datetime, date
from src.main import run_batch_conversion, run_contrato_conversion
from src.models.contrato_locacao_model import ContratoLocacao, EntidadeContrato

def main(page: ft.Page):
    page.title = "Conversor NFS-e para ABRASF XML"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 780
    page.window_height = 750
    page.window_resizable = True
    page.padding = 30
    page.vertical_alignment = ft.MainAxisAlignment.START

    # ---------------------------------------------------------------
    # Componentes de UI — Seleção de arquivos PDF
    # ---------------------------------------------------------------
    input_dir_text  = ft.TextField(label="Pasta de Entrada (PDFs)", expand=True, read_only=True)
    output_dir_text = ft.TextField(label="Pasta de Saída (XMLs)",   expand=True, read_only=True)

    progress_bar = ft.ProgressBar(width=720, color="blue", value=0, visible=False)
    status_text  = ft.Text("Aguardando início...", color="white70")
    log_area     = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)

    selected_files = []

    # ---------------------------------------------------------------
    # Dropdown de formato
    # ---------------------------------------------------------------
    format_dropdown = ft.Dropdown(
        label="Tipo de Arquivo",
        value="abrasf",
        options=[
            ft.dropdown.Option("abrasf",          "NFS-e (Padrão ABRASF 2.01)"),
            ft.dropdown.Option("nfe",              "NF-e (DANFE Estadual - Modelo 55)"),
            ft.dropdown.Option("contrato_locacao", "Contrato de Locação (ABRASF XML)"),
        ],
        width=350
    )

    # ---------------------------------------------------------------
    # Campos do formulário — Contrato de Locação
    # ---------------------------------------------------------------
    # Locador (→ Tomador no XML)
    locador_nome    = ft.TextField(label="Locador — Razão Social / Nome",      expand=True)
    locador_doc     = ft.TextField(label="Locador — CNPJ / CPF",               width=200)
    locador_im      = ft.TextField(label="Locador — Inscrição Municipal",       width=200)
    locador_end     = ft.TextField(label="Locador — Logradouro",                expand=True)
    locador_num     = ft.TextField(label="Nº",   width=80)
    locador_bairro  = ft.TextField(label="Bairro",                             expand=True)
    locador_mun     = ft.TextField(label="Cód. Município (IBGE)", value="2927408", width=160)
    locador_uf      = ft.TextField(label="UF",   value="BA",  width=60)
    locador_cep     = ft.TextField(label="CEP",  width=110)

    # Locatário (→ Prestador no XML)
    locatario_nome   = ft.TextField(label="Locatário — Razão Social / Nome",   expand=True)
    locatario_doc    = ft.TextField(label="Locatário — CNPJ / CPF",            width=200)
    locatario_im     = ft.TextField(label="Locatário — Inscrição Municipal",    width=200)
    locatario_end    = ft.TextField(label="Locatário — Logradouro",             expand=True)
    locatario_num    = ft.TextField(label="Nº",  width=80)
    locatario_bairro = ft.TextField(label="Bairro",                            expand=True)
    locatario_mun    = ft.TextField(label="Cód. Município (IBGE)", value="2927408", width=160)
    locatario_uf     = ft.TextField(label="UF",  value="BA",  width=60)
    locatario_cep    = ft.TextField(label="CEP", width=110)

    # Dados do serviço
    valor_mensal_field   = ft.TextField(label="Valor Mensal (R$)", width=180, value="1100.00")
    discriminacao_field  = ft.TextField(
        label="Discriminação do Serviço",
        expand=True,
        value="Locação de veículo conforme contrato",
        multiline=True,
        min_lines=2,
        max_lines=4
    )
    aliquota_field       = ft.TextField(label="Alíquota ISS (ex: 0.03)", width=160, value="0.03")
    servico_codigo_field = ft.TextField(label="Código Serviço LC116",    width=160, value="0601")

    # ---------------------------------------------------------------
    # DatePicker — Data de Emissão
    # ---------------------------------------------------------------
    data_emissao_label = ft.Text("Data de Emissão: (não selecionada)", color="white70")
    selected_date: list[date] = [datetime.now().date()]   # mutável via lista
    data_emissao_label.value = f"Data de Emissão: {selected_date[0].strftime('%d/%m/%Y')}"

    def on_date_picked(e):
        if e.control.value:
            selected_date[0] = e.control.value.date() if isinstance(e.control.value, datetime) else e.control.value
            data_emissao_label.value = f"Data de Emissão: {selected_date[0].strftime('%d/%m/%Y')}"
            page.update()

    date_picker = ft.DatePicker(
        on_change=on_date_picked,
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        value=datetime.now(),
    )
    page.overlay.append(date_picker)

    btn_data = ft.ElevatedButton(
        "Escolher Data",
        icon=ft.icons.CALENDAR_MONTH,
        on_click=lambda _: date_picker.pick_date(),
    )

    # ---------------------------------------------------------------
    # Painel do formulário de contrato (visível apenas quando selecionado)
    # ---------------------------------------------------------------
    contrato_panel = ft.Column([
        ft.Divider(),
        ft.Text("📋 Dados do Contrato de Locação", size=16, weight=ft.FontWeight.BOLD, color="lightblue"),

        # Locador
        ft.Text("Locador (→ Tomador no XML)", color="orange", weight=ft.FontWeight.W_600),
        ft.Row([locador_nome, locador_doc, locador_im]),
        ft.Row([locador_end, locador_num]),
        ft.Row([locador_bairro, locador_mun, locador_uf, locador_cep]),

        ft.Divider(height=4),

        # Locatário
        ft.Text("Locatário (→ Prestador no XML)", color="lightgreen", weight=ft.FontWeight.W_600),
        ft.Row([locatario_nome, locatario_doc, locatario_im]),
        ft.Row([locatario_end, locatario_num]),
        ft.Row([locatario_bairro, locatario_mun, locatario_uf, locatario_cep]),

        ft.Divider(height=4),

        # Serviço / Valores
        ft.Text("Dados do Serviço / Valores", color="white70", weight=ft.FontWeight.W_600),
        ft.Row([valor_mensal_field, aliquota_field, servico_codigo_field]),
        ft.Row([discriminacao_field]),

        # Data de Emissão
        ft.Divider(height=4),
        ft.Row([btn_data, data_emissao_label], spacing=16),
    ], visible=False, spacing=8)

    # Painel PDF (visível por padrão)
    pdf_panel = ft.Column([
        ft.Row([
            input_dir_text,
            ft.Tooltip(
                message="Selecionar Pasta",
                content=ft.IconButton(ft.icons.FOLDER_OPEN, on_click=lambda _: input_picker.get_directory_path())
            ),
            ft.Tooltip(
                message="Selecionar Arquivos Individualmente",
                content=ft.IconButton(ft.icons.PICTURE_AS_PDF,
                    on_click=lambda _: file_picker.pick_files(allow_multiple=True, allowed_extensions=["pdf"]))
            )
        ]),
        ft.Row([
            output_dir_text,
            ft.Tooltip(
                message="Selecionar Pasta de Destino",
                content=ft.IconButton(ft.icons.DRIVE_FILE_MOVE, on_click=lambda _: output_picker.get_directory_path())
            )
        ]),
    ], visible=True, spacing=8)

    # Seleção de pasta de saída também usada pelo contrato
    output_contrato_dir = ft.TextField(label="Pasta de Saída (XML do Contrato)", expand=True, read_only=True)
    output_contrato_panel = ft.Row([
        output_contrato_dir,
        ft.Tooltip(
            message="Selecionar Pasta de Destino",
            content=ft.IconButton(
                ft.icons.DRIVE_FILE_MOVE,
                on_click=lambda _: output_contrato_picker.get_directory_path()
            )
        )
    ], visible=False)

    def on_output_contrato_result(e):
        if e.path:
            output_contrato_dir.value = e.path
            page.update()

    output_contrato_picker = ft.FilePicker(on_result=on_output_contrato_result)
    page.overlay.append(output_contrato_picker)

    # ---------------------------------------------------------------
    # Dialogs de seleção de arquivos PDF
    # ---------------------------------------------------------------
    def on_input_result(e):
        nonlocal selected_files
        if e.path:
            input_dir_text.value = e.path
            selected_files = []
            page.update()

    def on_file_result(e):
        nonlocal selected_files
        if e.files:
            selected_files = [f.path for f in e.files]
            input_dir_text.value = f"{len(selected_files)} arquivo(s) selecionado(s)"
            page.update()

    def on_output_result(e):
        if e.path:
            output_dir_text.value = e.path
            page.update()

    input_picker  = ft.FilePicker(on_result=on_input_result)
    file_picker   = ft.FilePicker(on_result=on_file_result)
    output_picker = ft.FilePicker(on_result=on_output_result)
    page.overlay.extend([input_picker, file_picker, output_picker])

    # ---------------------------------------------------------------
    # Alternância de painéis conforme formato
    # ---------------------------------------------------------------
    def on_format_change(e):
        is_contrato = format_dropdown.value == "contrato_locacao"
        pdf_panel.visible            = not is_contrato
        contrato_panel.visible       = is_contrato
        output_contrato_panel.visible = is_contrato
        page.update()

    format_dropdown.on_change = on_format_change

    # ---------------------------------------------------------------
    # Log helpers
    # ---------------------------------------------------------------
    def add_log(msg, color="white"):
        log_area.controls.append(ft.Text(msg, color=color, size=12))
        page.update()

    def update_progress(progress, message):
        progress_bar.value = progress
        status_text.value  = message
        add_log(message)
        page.update()

    # ---------------------------------------------------------------
    # Processamento principal
    # ---------------------------------------------------------------
    def start_processing(e):
        is_contrato = format_dropdown.value == "contrato_locacao"

        # Validação de saída
        out_dir = output_contrato_dir.value if is_contrato else output_dir_text.value
        if not out_dir:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione a pasta de saída!"))
            page.snack_bar.open = True
            page.update()
            return

        if not is_contrato and not input_dir_text.value:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, selecione os arquivos/pasta de entrada!"))
            page.snack_bar.open = True
            page.update()
            return

        if is_contrato:
            # Validação mínima dos campos do contrato
            erros = []
            if not locador_nome.value.strip():
                erros.append("Nome do Locador é obrigatório")
            if not locador_doc.value.strip():
                erros.append("CNPJ/CPF do Locador é obrigatório")
            if not locatario_nome.value.strip():
                erros.append("Nome do Locatário é obrigatório")
            if not locatario_doc.value.strip():
                erros.append("CNPJ/CPF do Locatário é obrigatório")
            if not valor_mensal_field.value.strip():
                erros.append("Valor Mensal é obrigatório")
            if erros:
                page.snack_bar = ft.SnackBar(ft.Text(" | ".join(erros)))
                page.snack_bar.open = True
                page.update()
                return

        files_to_check = []
        if not is_contrato:
            if selected_files:
                files_to_check = selected_files
            elif input_dir_text.value and os.path.isdir(input_dir_text.value):
                files_to_check = [os.path.join(input_dir_text.value, f) for f in os.listdir(input_dir_text.value) if f.lower().endswith('.pdf')]

        def do_run(selected_pages=None):
            process_btn.disabled = True
            progress_bar.visible = True
            log_area.controls.clear()
            add_log("[*] Iniciando processamento...", "blue")
            page.update()

            def run():
                try:
                    if is_contrato:
                        # Montar objeto ContratoLocacao
                        dt_emissao = datetime.combine(selected_date[0], datetime.min.time())
                        contrato = ContratoLocacao(
                            locador=EntidadeContrato(
                                cnpj_cpf=locador_doc.value.strip(),
                                razao_social=locador_nome.value.strip(),
                                inscricao_municipal=locador_im.value.strip() or None,
                                logradouro=locador_end.value.strip() or "Não informado",
                                numero=locador_num.value.strip() or "S/N",
                                bairro=locador_bairro.value.strip() or "Não informado",
                                codigo_municipio=locador_mun.value.strip() or "2927408",
                                uf=locador_uf.value.strip() or "BA",
                                cep=locador_cep.value.strip() or "00000000",
                            ),
                            locatario=EntidadeContrato(
                                cnpj_cpf=locatario_doc.value.strip(),
                                razao_social=locatario_nome.value.strip(),
                                inscricao_municipal=locatario_im.value.strip() or None,
                                logradouro=locatario_end.value.strip() or "Não informado",
                                numero=locatario_num.value.strip() or "S/N",
                                bairro=locatario_bairro.value.strip() or "Não informado",
                                codigo_municipio=locatario_mun.value.strip() or "2927408",
                                uf=locatario_uf.value.strip() or "BA",
                                cep=locatario_cep.value.strip() or "00000000",
                            ),
                            valor_mensal=float(valor_mensal_field.value.replace(",", ".")),
                            discriminacao=discriminacao_field.value.strip(),
                            aliquota_iss=float(aliquota_field.value.replace(",", ".")),
                            servico_codigo=servico_codigo_field.value.strip() or "0601",
                            data_emissao=dt_emissao,
                        )
                        run_contrato_conversion(
                            contrato=contrato,
                            output_dir=out_dir,
                            progress_callback=update_progress
                        )
                    else:
                        if len(files_to_check) == 1:
                            from src.main import run_conversion
                            # Chama run_conversion direto se for um único arquivo, pois suporta selected_pages
                            output_xml = os.path.join(out_dir, "temp.xml") # run_conversion espera o caminho do xml, embora vá gerar os corretos
                            run_conversion(
                                pdf_path=files_to_check[0],
                                output_xml_path=output_xml,
                                output_format=format_dropdown.value,
                                selected_pages=selected_pages
                            )
                            update_progress(1.0, f"[+] Concluído! XMLs gerados em {out_dir}")
                        else:
                            run_batch_conversion(
                                input_dir=input_dir_text.value if not selected_files else None,
                                pdf_files=selected_files if selected_files else None,
                                output_dir=out_dir,
                                progress_callback=update_progress,
                                output_format=format_dropdown.value
                            )

                    page.snack_bar = ft.SnackBar(ft.Text("Processamento concluído com sucesso!"))
                    page.snack_bar.open = True
                except Exception as ex:
                    add_log(f"[ERRO] {str(ex)}", "red")
                    page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {str(ex)}"))
                    page.snack_bar.open = True
                finally:
                    process_btn.disabled = False
                    page.update()

            threading.Thread(target=run, daemon=True).start()

        # Verifica se é um único arquivo PDF com múltiplas páginas
        if not is_contrato and len(files_to_check) == 1:
            from src.extractors.pdf_extractor import SPPdfExtractor
            try:
                extractor = SPPdfExtractor(files_to_check[0])
                nfse_list = extractor.parse_multiple()
                invalid_pages = getattr(extractor, 'invalid_pages', [])
                
                if invalid_pages:
                    msgs = [f"Pág {p['page']}: {p['reason']}" for p in invalid_pages]
                    page.snack_bar = ft.SnackBar(
                        ft.Text("Atenção: " + " | ".join(msgs)),
                        bgcolor=ft.colors.ORANGE_800
                    )
                    page.snack_bar.open = True
                    page.update()
                
                if len(nfse_list) > 1:
                    def on_dialog_close(e, sel_pages=None):
                        dialog.open = False
                        page.update()
                        do_run(selected_pages=sel_pages)

                    options = []
                    for n in nfse_list:
                        options.append(
                            ft.ElevatedButton(
                                f"Página {n.pagina_origem}",
                                on_click=lambda e, p=n.pagina_origem: on_dialog_close(e, [p])
                            )
                        )
                    
                    options.append(
                        ft.ElevatedButton(
                            "Todas as Válidas",
                            on_click=lambda e: on_dialog_close(e, None),
                            bgcolor=ft.colors.BLUE_700
                        )
                    )
                    
                    dialog = ft.AlertDialog(
                        title=ft.Text("Múltiplas Páginas Encontradas"),
                        content=ft.Column([ft.Text("O PDF possui mais de uma nota válida. Qual deseja converter?")] + options, tight=True)
                    )
                    page.overlay.append(dialog)
                    dialog.open = True
                    page.update()
                    return
            except Exception as ex:
                pass # se der erro, deixa o do_run processar e mostrar no log
                
        do_run()

    process_btn = ft.ElevatedButton(
        "Iniciar Conversão",
        icon=ft.icons.PLAY_ARROW,
        on_click=start_processing,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    # ---------------------------------------------------------------
    # Layout
    # ---------------------------------------------------------------
    page.add(
        ft.Column([
            ft.Text("Conversor NFS-e / Contratos", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([format_dropdown]),
            pdf_panel,
            output_contrato_panel,
            contrato_panel,
            ft.Container(height=8),
            process_btn,
            ft.Divider(),
            status_text,
            progress_bar,
            ft.Container(
                content=log_area,
                border=ft.border.all(1, ft.colors.WHITE24),
                border_radius=8,
                expand=True,
                bgcolor=ft.colors.BLACK12,
                height=160,
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO)
    )

if __name__ == "__main__":
    ft.app(target=main)
