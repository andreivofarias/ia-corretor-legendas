import streamlit as st
import os

# --- CORREÇÃO PARA O STREAMLIT CLOUD (IMAGEMAGICK) ---
# Esta parte PRECISA vir antes de importar o moviepy
if not os.name == 'nt': 
    os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

import whisper
import time
# Agora importamos as ferramentas de vídeo
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips

# --- CONFIGURAÇÕES DE SEGURANÇA ---
if not os.path.exists("temp"):
    os.makedirs("temp")

def cleanup_files(*filenames):
    """Remove ficheiros temporários para otimizar espaço."""
    for f in filenames:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

# --- INTERFACE ---
st.set_page_config(page_title="Imóvel Pro AI", page_icon="🏠")
st.title("🏠 Imóvel Pro AI")
st.markdown("---")

menu = st.sidebar.selectbox("Escolha o Serviço", ["Legendar Vídeo", "Vídeo de Fotos (Tour)"])

# --- MÓDULO 1: LEGENDAR VÍDEO ---
if menu == "Legendar Vídeo":
    st.header("🎬 Gerador de Legendas Automáticas")
    st.info("Limite: 60 segundos por vídeo.")
    
    video_file = st.file_uploader("Suba o vídeo do imóvel", type=["mp4", "mov"])
    logo_file = st.file_uploader("Suba a sua Logo (Opcional - PNG)", type=["png"])

    if video_file:
        t_stamp = int(time.time())
        input_path = f"temp/in_{t_stamp}.mp4"
        output_path = f"temp/out_{t_stamp}.mp4"
        
        with open(input_path, "wb") as f:
            f.write(video_file.read())

        # TRAVA DE SEGURANÇA: Duração do Vídeo
        clip_check = VideoFileClip(input_path)
        duracao = clip_check.duration
        clip_check.close()

        if duracao > 60:
            st.error(f"Vídeo demasiado longo ({duracao:.1f}s). O limite é de 60 segundos.")
            cleanup_files(input_path)
        else:
            if st.button("Gerar Vídeo Profissional"):
                with st.spinner("IA a processar... Isto pode levar 1-2 minutos."):
                    try:
                        # 1. Transcrição com Whisper
                        model = whisper.load_model("tiny")
                        result = model.transcribe(input_path)
                        
                        # 2. Carregar Clipe
                        main_clip = VideoFileClip(input_path)
                        elements = [main_clip]

                        # 3. Adicionar Legenda (Fonte DejaVu-Sans-Bold para Linux/Cloud)
                        if result['text'].strip():
                            txt = TextClip(result['text'], fontsize=24, color='yellow', 
                                           method='caption', size=(main_clip.w*0.8, None),
                                           font='DejaVu-Sans-Bold').set_duration(main_clip.duration).set_position(('center', 'bottom'))
                            elements.append(txt)

                        # 4. Adicionar Logo
                        if logo_file:
                            logo_path = f"temp/logo_{t_stamp}.png"
                            with open(logo_path, "wb") as f: f.write(logo_file.read())
                            logo = (ImageClip(logo_path)
                                    .set_duration(main_clip.duration)
                                    .resize(width=main_clip.w * 0.15)
                                    .set_position(("right", "top"))
                                    .set_opacity(0.8))
                            elements.append(logo)

                        # 5. Renderização Final
                        final_video = CompositeVideoClip(elements)
                        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

                        st.success("Vídeo concluído!")
                        st.video(output_path)
                        with open(output_path, "rb") as f:
                            st.download_button("Baixar Vídeo", f, file_name="video_imovel_pro.mp4")

                    except Exception as e:
                        st.error(f"Erro técnico: {e}")
                    finally:
                        cleanup_files(input_path, output_path)

# --- MÓDULO 2: VÍDEO DE FOTOS (TOUR) ---
elif menu == "Vídeo de Fotos (Tour)":
    st.header("📸 Tour Automático de Fotos")
    st.info("Limite: Máximo de 20 fotos por tour.")
    
    uploaded_images = st.file_uploader("Selecione as fotos (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_images:
        if len(uploaded_images) > 20:
            st.error(f"Selecionou {len(uploaded_images)} fotos. O limite máximo é de 20.")
        else:
            if st.button("Criar Tour em Vídeo"):
                with st.spinner("A montar o seu tour..."):
                    try:
                        clips = []
                        temp_imgs = []
                        t_stamp = int(time.time())
                        
                        for i, img_file in enumerate(uploaded_images):
                            t_path = f"temp/img_{t_stamp}_{i}.png"
                            with open(t_path, "wb") as f: f.write(img_file.read())
                            temp_imgs.append(t_path)
                            
                            img_clip = ImageClip(t_path).set_duration(3).crossfadein(0.5)
                            clips.append(img_clip)
                        
                        tour_output = f"temp/tour_{t_stamp}.mp4"
                        final_tour = concatenate_videoclips(clips, method="compose")
                        final_tour.write_videofile(tour_output, fps=24, codec="libx264")
                        
                        st.success("Tour gerado!")
                        st.video(tour_output)
                        with open(tour_output, "rb") as f:
                            st.download_button("Baixar Tour", f, file_name="tour_fotos.mp4")
                        
                        cleanup_files(*temp_imgs, tour_output)
                    except Exception as e:
                        st.error(f"Erro ao criar tour: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("v1.1 - Hotfix Cloud")