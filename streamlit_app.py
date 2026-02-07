import streamlit as st
import os
import whisper
import time
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="Layer1 App", page_icon="🏢", layout="centered")

if 'menu_escolhido' not in st.session_state:
    st.session_state.menu_escolhido = None
if 'contador_videos' not in st.session_state:
    st.session_state.contador_videos = 0

menu = st.session_state.menu_escolhido

# --- FUNÇÃO PARA DESENHAR LEGENDA PROPORCIONAL ---
def draw_responsive_text(img, text):
    draw = ImageDraw.Draw(img)
    # Define o tamanho da fonte como 5% da largura da imagem (mínimo 20px)
    font_size = max(20, int(img.width * 0.05))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Calcula altura da barra (15% da imagem)
    bar_height = int(img.height * 0.15)
    
    # Desenha fundo preto semi-transparente
    draw.rectangle([0, img.height - bar_height, img.width, img.height], fill=(0, 0, 0, 180))
    
    # Centraliza o texto
    text = text.upper()
    w_txt = draw.textlength(text, font=font)
    
    # Se o texto for maior que a foto, reduz a fonte até caber
    while w_txt > img.width * 0.9 and font_size > 12:
        font_size -= 2
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
        w_txt = draw.textlength(text, font=font)

    draw.text(((img.width - w_txt) // 2, img.height - (bar_height // 2) - (font_size // 2)), text, fill="white", font=font)
    return img

# --- INTERFACE ---
if menu is None:
    st.markdown("<h1 style='text-align: center;'>🏢 Layer1 App</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬\nLEGENDAR VÍDEO"):
            st.session_state.menu_escolhido = "Legendar Vídeo"
            st.rerun()
    with col2:
        if st.button("📸\nTOUR DE FOTOS"):
            st.session_state.menu_escolhido = "Vídeo de Fotos (Tour)"
            st.rerun()
else:
    if st.button("⬅️ Sair"):
        st.session_state.menu_escolhido = None
        st.rerun()

    if menu == "Vídeo de Fotos (Tour)":
        st.header("📸 Tour de Fotos com Áudio")
        
        # Upload de Fotos
        files = st.file_uploader("Fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        
        # Upload de Áudio (OPCIONAL)
        audio_file = st.file_uploader("🎵 Adicionar Trilha Sonora (MP3/WAV)", type=["mp3", "wav"])
        
        if files:
            legendas = []
            for i, f in enumerate(files):
                st.image(f, width=150)
                legendas.append(st.text_input(f"Legenda {i+1}", key=f"t_{i}"))

            if st.button("Gerar Tour Layer1"):
                with st.spinner("Processando imagens e mixando áudio..."):
                    try:
                        clips = []
                        temp_paths = []
                        t_s = int(time.time())

                        for i, f in enumerate(files):
                            img = Image.open(f).convert("RGB")
                            # Redimensiona para um padrão HD para evitar quebras
                            img = img.resize((1280, 720)) 
                            
                            if legendas[i]:
                                img = draw_responsive_text(img, legendas[i])
                            
                            p = f"temp/p_{t_s}_{i}.jpg"
                            img.save(p)
                            temp_paths.append(p)
                            clips.append(ImageClip(p).set_duration(4).crossfadein(0.5))

                        video = concatenate_videoclips(clips, method="compose")
                        
                        # --- LÓGICA DE ÁUDIO ---
                        if audio_file:
                            a_path = f"temp/audio_{t_s}.mp3"
                            with open(a_path, "wb") as f_aud: f_aud.write(audio_file.read())
                            audio_clip = AudioFileClip(a_path)
                            
                            # Ajusta o áudio ao tempo do vídeo (corta ou faz loop)
                            if audio_clip.duration > video.duration:
                                audio_clip = audio_clip.subclip(0, video.duration)
                            video = video.set_audio(audio_clip)
                            temp_paths.append(a_path)

                        out = f"temp/final_{t_s}.mp4"
                        video.write_videofile(out, fps=24, codec="libx264", audio_codec="aac")
                        
                        st.video(out)
                        st.session_state.contador_videos += 1
                        
                        # Cleanup
                        for p in temp_paths: 
                            if os.path.exists(p): os.remove(p)
                    except Exception as e:
                        st.error(f"Erro: {e}")