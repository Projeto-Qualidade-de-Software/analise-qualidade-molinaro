'''Explicação das Alterações:
Chave de API: Substituí a chave da OpenAI pela chave do DeepSeek (DEEPSEEK_API_KEY).

Função transcrever_video: Agora, a função faz uma chamada HTTP POST para a API do DeepSeek.
O corpo da requisição é semelhante ao que você usaria com a OpenAI
mas a URL e os cabeçalhos são específicos para o DeepSeek.

Tratamento de Erros: Adicionei um tratamento de erro para capturar exceções
relacionadas a problemas de rede ou respostas inválidas da API.

Leandro: E1101, W0613

Brandão: W0719, W0718

Cabral: W3101, C0411

Sthe: C0116, C0103, C0303
'''
# pylint: disable=invalid-name

# 1. Bibliotecas Padrão do Python (Standard Libraries)
import os
import re  # Biblioteca para sanitizar nomes de arquivos
import tkinter as tk
from io import BytesIO
from time import strftime
from tkinter import filedialog

# 2. Bibliotecas de Terceiros (Third-party Libraries)
import customtkinter
import fpdf  # Biblioteca para gerar PDF
import requests
import yt_dlp
from PIL import Image, ImageTk
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

QUALITY_OPTIONS = ['Video', 'Audio', 'PDF']

def selecionar_diretorio():
    """Permite ao usuário selecionar um diretório para salvar os arquivos baixados."""
    try:
        diretorio_destino = filedialog.askdirectory()
        if not diretorio_destino:
            raise ValueError("Nenhum diretório selecionado.")
        label_diretorio.configure(text=f"Diretório selecionado:{diretorio_destino}",
        text_color="white")
        return diretorio_destino
    except ValueError as e:
        label_diretorio.configure(text=str(e), text_color="red")
        raise
def obter_transcricao(video_id):
    """Obtém a legenda (automática ou manual) diretamente do YouTube."""
    try:
        # Nas versões mais recentes da biblioteca, é necessário instanciar a API
        ytt_api = YouTubeTranscriptApi()

        # Puxa a lista de todas as transcrições disponíveis para o vídeo
        transcript_list = ytt_api.list(video_id)

        # Procura pela legenda em Português ou Inglês
        transcript = transcript_list.find_transcript(['pt', 'pt-BR', 'en'])

        # Faz o download (fetch) do conteúdo da legenda encontrada
        transcript_data = transcript.fetch()

        # Concatena os blocos de texto da legenda numa única string
        texto_completo = " ".join([item.text for item in transcript_data])

        # Remove quebras de linha que vêm por padrão na legenda
        texto_completo = texto_completo.replace('\n', ' ')

        return texto_completo
    except TranscriptsDisabled:
        return "Erro: As legendas estão desativadas para este vídeo."
    except NoTranscriptFound:
        return "Erro: Nenhuma legenda em português ou inglês foi encontrada neste vídeo."
    except Exception as e:
        return f"Erro ao obter a legenda do vídeo: {str(e)}"

def sanitize_filename(filename):
    """Remove ou substitui caracteres inválidos para nomes de arquivos no Windows"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def gerar_pdf(diretorio_destino, video_title, thumbnail_path, transcricao):
    """"Gera um PDF com o título do vídeo, a thumbnail e a transcrição."""
    try:
        pdf = fpdf.FPDF()
        pdf.add_page()

        # Adicionar título
        pdf.set_font("Arial", size=24, style="B")

        # Sanitizar título para o PDF suportar os caracteres
        titulo_pdf = video_title.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(200, 10, txt=titulo_pdf, ln=True, align='C')

        # Adicionar a imagem (thumbnail) se ela existir
        if thumbnail_path:
            pdf.image(thumbnail_path, x=55, y=25, w=100)

        # Tratar a transcrição para remover emojis e caracteres que o FPDF não suporta (latin-1)
        transcricao_limpa = transcricao.encode('latin-1', 'ignore').decode('latin-1')

        # Adicionar a transcrição
        pdf.set_font("Arial", size=12)
        pdf.ln(85)  # Pula linhas para não sobrepor a imagem
        pdf.multi_cell(0, 10, transcricao_limpa)

        # Sanitizar o título do vídeo para usá-lo como nome do arquivo
        video_title_sanitized = sanitize_filename(video_title)

        # Salvar o PDF com o nome sanitizado
        pdf_output_path = os.path.join(diretorio_destino, f"{video_title_sanitized}.pdf")
        pdf.output(pdf_output_path)
        label_status.configure(text=f"PDF criado: {pdf_output_path}", text_color="green")

    except OSError as e:
        # Captura erros de sistema operacional (como falta de permissão ou disco cheio)
        label_status.configure(text=f"Erro de sistema ao salvar PDF: {str(e)}", text_color="red")
    except UnicodeEncodeError as e:
        # A biblioteca FPDF pode falhar se a transcrição tiver emojis ou caracteres muito especiais
        label_status.configure(text="Erro de formatação: Texto possui caracteres incompatíveis.",
                               text_color="red")

def realizar_download():
    """"Realiza o download do vídeo ou áudio e opcionalmente gera o PDF"""
    try:
        link_video = entrada_link.get()

        if not link_video.strip():
            raise ValueError("O link do vídeo está vazio.")

        diretorio_destino = selecionar_diretorio()

        ydl_opts = {}
        if combobox_var.get() == 'Video':
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': os.path.join(diretorio_destino, '%(title)s.%(ext)s'),
                'progress_hooks': [hook_progresso],
                'nocolor': True,
            }
        elif combobox_var.get() == 'Audio':
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]',
                'outtmpl': os.path.join(diretorio_destino, '%(title)s.%(ext)s'),
                'progress_hooks': [hook_progresso],
                'nocolor': True,
            }
        elif combobox_var.get() == 'PDF':
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': os.path.join(diretorio_destino, '%(title)s.%(ext)s'),
                'progress_hooks': [hook_progresso],
                'nocolor': True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link_video, download=False)
            video_title = info_dict.get('title', None)
            video_id = info_dict.get('id', None) # Necessário para buscar a legenda
            thumbnail_url = info_dict.get('thumbnail', None)

            label_titulo.configure(text=video_title, text_color="white")

            if combobox_var.get() == 'PDF':
                # Baixar o vídeo
                ydl.download([link_video])

                # Baixar a thumbnail
                thumbnail_path = None
                if thumbnail_url:
                    thumbnail_path = baixar_thumbnail(thumbnail_url, diretorio_destino)

                # Obter a legenda original do YouTube (sem uso de IA)
                transcricao = obter_transcricao(video_id)

                # Gerar o PDF
                gerar_pdf(diretorio_destino, video_title, thumbnail_path, transcricao)

            else:
                # Download de vídeo ou áudio
                ydl.download([link_video])

    except ValueError as e:
        # Captura erros de validação (ex: link vazio ou diretório não selecionado)
        label_status.configure(text=f"Aviso: {str(e)}", text_color="orange")
        print(f"Erro de Validação: {e}")
    except yt_dlp.utils.DownloadError as e:
        # Captura erros específicos do YouTube (link quebrado, vídeo privado, etc)
        label_status.configure(text="Erro no YouTube: Verifique o link ou sua conexão.",
                                text_color="red")
        print(f"Erro no yt_dlp: {e}")
    except OSError as e:
        # Captura erros do sistema (ex: sem permissão para salvar na pasta)
        label_status.configure(text="Erro no sistema: Não foi possível salvar o arquivo.",
                                text_color="red")
        print(f"Erro de Sistema Operacional: {e}")

def hook_progresso(d):
    """"Atualiza a barra de progresso e o rótulo de porcentagem durante o download."""
    if d['status'] == 'downloading':
        if d.get('total_bytes') and d.get('downloaded_bytes'):
            porcentagem = d['downloaded_bytes'] / d['total_bytes'] * 100
            barra_progresso.set(porcentagem / 100)
            label_porcentagem.configure(text=f"{porcentagem:.2f}%")
        else:
            label_porcentagem.configure(text="Progresso não disponível")

    if d['status'] == 'finished':
        barra_progresso.set(1)
        label_porcentagem.configure(text="100%")
        label_status.configure(text="Download Concluído!", text_color="white")

def mostrar_thumbnail(thumbnail_url):
    """Exibe a thumbnail do vídeo na interface."""
    try:
        response = requests.get(thumbnail_url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img = img.resize((320, 180), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        label_thumbnail.configure(image=img_tk)
        label_thumbnail.image = img_tk
    except requests.exceptions.RequestException as e:
        # Falha de conexão/internet ao tentar acessar a imagem
        label_status.configure(text="Erro de rede ao carregar thumbnail", text_color="red")
        print(f"Erro de rede (Thumbnail): {e}")
    except OSError as e:
        # A biblioteca PIL falhou ao tentar ler os bytes da imagem
        label_status.configure(text="Erro ao processar imagem da thumbnail", text_color="red")
        print(f"Erro de imagem (Thumbnail): {e}")

def baixar_thumbnail(thumbnail_url, diretorio_destino):
    """"Baixa a thumbnail do vídeo e salva no diretório de destino."""
    try:
        response = requests.get(thumbnail_url)
        thumbnail_path = os.path.join(diretorio_destino, 'thumbnail.jpg')
        with open(thumbnail_path, 'wb') as f:
            f.write(response.content)
        return thumbnail_path
    except requests.exceptions.RequestException as e:
        label_status.configure(text=f"Erro de conexão ao baixar thumbnail: {str(e)}",
                                text_color="red")
        return None

# Inicialização da interface
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")

janela = customtkinter.CTk()
janela.geometry("720x650")
janela.title("Molinaro's Downloader")

label_titulo = customtkinter.CTkLabel(janela, text="Video Link", font=("Consolas bold", 17))
label_titulo.pack(padx=10, pady=10)

label_thumbnail = customtkinter.CTkLabel(janela, text="")
label_thumbnail.pack(pady=10)

url = tk.StringVar()
entrada_link = customtkinter.CTkEntry(janela, width=550, height=40, textvariable=url)
entrada_link.pack(pady=10)

combobox_var = customtkinter.StringVar(value='Video')
combobox = customtkinter.CTkComboBox(janela,
                                     values=QUALITY_OPTIONS,
                                     variable=combobox_var, width=250)
combobox.pack(pady=15)

botao_download = customtkinter.CTkButton(janela,
                                         text="Download",
                                         command=realizar_download,
                                         width=250, font=("Consolas", 13))
botao_download.pack(pady=10)

label_diretorio = customtkinter.CTkLabel(janela, text="")
label_diretorio.pack(pady=10)

label_status = customtkinter.CTkLabel(janela, text="")
label_status.pack(pady=10)

label_porcentagem = customtkinter.CTkLabel(janela, text="")
label_porcentagem.pack(pady=10)

barra_progresso = customtkinter.CTkProgressBar(janela, width=400)
barra_progresso.set(0)
barra_progresso.pack_forget()

# Relógio no canto inferior direito
def mostrar_relogio():
    """Atualiza o rótulo do relógio a cada segundo."""
    horario_atual = strftime('%H:%M:%S')
    label_relogio.configure(text=horario_atual)
    label_relogio.after(1000, mostrar_relogio)

label_relogio = customtkinter.CTkLabel(janela, text="")
label_relogio.place(relx=1.0, rely=1.0, anchor="se")
mostrar_relogio()

janela.mainloop()
