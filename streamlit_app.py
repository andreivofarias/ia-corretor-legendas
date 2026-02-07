import streamlit as st
import os
import whisper
import time
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# --- 1. CONFIGURAÇÕES E MARCA ---
st.set_page_config(page_title="Layer1 App", page_icon="🏢", layout="centered")

# Inicialização global das variáveis de controle
if 'menu_escolhido' not in st.session_state:
    st.session_state.menu_escolhido = None
if 'contador_videos' not in st.session_state:
    st.session_state.contador_videos = 0

# GARANTIA: Definimos 'menu' logo no início para evitar o NameError
menu = st.session_state.menu_escolhido

# CSS (Estilo Layer1)
st.markdown("""
    <style>
    div.stButton > button { width: 100%; height: 100px; font-size: 20px; font-weight: bold; border-radius: 12px; }
    .main-title { text-align: center; font-size: 40px; font-weight: 900; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f0f2f6; text-align: center; padding: 10px; font-size: 12px; border-top: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

def cleanup_files(*filenames):
    for f in filenames:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

# --- 2. TELA INICIAL ---
if menu is None:
    st.markdown("<h1 class='main-title'>🏢 Layer1 App</h1>", unsafe_allow_html=True)
    st.sidebar.metric("Vídeos Gerados", st.session_state.contador_videos)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬\nLEGENDAR VÍDEO"):
            st.session_state.menu_escolhido = "Legendar Vídeo"
            st.rerun()
    with col2:
        if st.button("📸\nTOUR DE FOTOS"):
            st.session_state.menu_escolhido = "Vídeo de Fotos (Tour)"
            st.rerun()
    st.info("💡 Selecione uma ferramenta acima.")

# --- 3. EXECUÇÃO DAS FERRAMENTAS ---
else:
    # Cabeçalho de Navegação
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ Sair"):
            st.session_state.menu_escolhido = None
            st.rerun()
    with col_title:
        st.markdown(f"### 🏢 Layer1 > {menu}")
    
    st.divider()

    if menu == "Legendar Vídeo":
        video_file = st.file_uploader("Suba o vídeo (Máx 60s)", type=["mp4", "mov"])
        if video_file:
            t_stamp = int(time.time())
            input_path = f"temp/in_{t_stamp}.mp4"
            output_path = f"temp/out_{t_stamp}.mp4"
            with open(input_path, "wb") as f: f.write(video_file.read())
            
            # Encapsulado em try para fechar o clip sempre
            try:
                clip = VideoFileClip(input_path)
                if clip.duration > 61:
                    st.error("Vídeo muito longo!")
                else:
                    if st.button("Gerar Legendas"):
                        with st.spinner("IA Layer1 processando..."):
                            model = whisper.load_model("tiny")
                            result = model.transcribe(input_path)
                            segments = result.get('segments', [])
                            subtitle_clips = []
                            temp_imgs = []

                            for i, seg in enumerate(segments):
                                texto = seg['text'].strip().upper()
                                if not texto: continue
                                
                                txt_img = Image.new('RGBA', (clip.w, clip.h), (255, 255, 255, 0))
                                draw = ImageDraw.Draw(txt_img)
                                try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(clip.w * 0.045))
                                except: font = ImageFont.load_default()
                                
                                barra_h = int(clip.h * 0.12)
                                draw.rectangle([0, clip.h - barra_h - 40, clip.w, clip.h - 40], fill=(0, 0, 0, 180))
                                w_txt = draw.textlength(texto, font=font)
                                draw.text(((clip.w - w_txt) // 2, clip.h - barra_h - 30), texto, fill="white", font=font)
                                
                                p = f"temp/s_{t_stamp}_{i}.png"
                                txt_img.save(p)
                                temp_imgs.append(p)
                                subtitle_clips.append(ImageClip(p).set_start(seg['start']).set_duration(max(0.1, seg['end'] - seg['start'])).set_position('center').crossfadein(0.2))

                            video_final = CompositeVideoClip([clip] + subtitle_clips)
                            video_final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                            st.video(output_path)
                            st.session_state.contador_videos += 1
                            cleanup_files(*temp_imgs)
                clip.close()
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                cleanup_files(input_path, output_path)

    elif menu == "Vídeo de Fotos (Tour)":
        uploaded_images = st.file_uploader("Selecione fotos", type=["jpg", "png"], accept_multiple_files=True)
        if uploaded_images:
            legendas = []
            for i, img_f in enumerate(uploaded_images):
                st.image(img_f, width=150)
                legendas.append(st.text_input(f"Legenda {i+1}", key=f"t_{i}"))

            if st.button("Gerar Tour"):
                with st.spinner("Renderizando..."):
                    try:
                        clips = []
                        temp_imgs = []
                        t_s = int(time.time())
                        for i, img_f in enumerate(uploaded_images):
                            img = Image.open(img_f).convert("RGB")
                            img.thumbnail((1280, 720))
                            if legendas[i]:
                                draw = ImageDraw.Draw(img)
                                try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                                except: font = ImageFont.load_default()
                                draw.rectangle([0, img.height-100, img.width, img.height], fill=(0,0,0,180))
                                draw.text((30, img.height-80), legendas[i].upper(), fill="white", font=font)
                            p = f"temp/p_{t_s}_{i}.jpg"
                            img.save(p)
                            temp_imgs.append(p)
                            clips.append(ImageClip(p).set_duration(3).crossfadein(0.5))
                        
                        out = f"temp/tour_{t_s}.mp4"
                        concatenate_videoclips(clips, method="compose").write_videofile(out, fps=24, codec="libx264")
                        st.video(out)
                        st.session_state.contador_videos += 1
                        cleanup_files(*temp_imgs, out)
                    except Exception as e:
                        st.error(f"Erro: {e}")

# Rodapé
st.markdown("<div class='footer'>Layer1 App © 2026</div>", unsafe_allow_html=True)