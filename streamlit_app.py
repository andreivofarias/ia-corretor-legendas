import streamlit as st
import os
import whisper
import time
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAÇÕES DE SEGURANÇA ---
os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

if not os.path.exists("temp"):
    os.makedirs("temp")

def cleanup_files(*filenames):
    for f in filenames:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

# --- INTERFACE ---
st.set_page_config(page_title="Imóvel Pro AI", page_icon="🏠")
st.title("🏠 Imóvel Pro AI")

menu = st.sidebar.selectbox("Escolha o Serviço", ["Legendar Vídeo", "Vídeo de Fotos (Tour)"])

# --- MÓDULO 1: LEGENDAR VÍDEO (WHISPER) ---
if menu == "Legendar Vídeo":
    st.header("🎬 Gerador de Legendas")
    video_file = st.file_uploader("Suba o vídeo (Máx 60s)", type=["mp4", "mov"])
    if video_file:
        input_path = f"temp/in_{int(time.time())}.mp4"
        with open(input_path, "wb") as f: f.write(video_file.read())
        
        clip_check = VideoFileClip(input_path)
        if clip_check.duration > 60:
            st.error("Vídeo muito longo!")
            clip_check.close()
            cleanup_files(input_path)
        else:
            if st.button("Gerar Legendas"):
                with st.spinner("Processando áudio..."):
                    model = whisper.load_model("tiny")
                    result = model.transcribe(input_path)
                    st.success("Texto extraído!")
                    st.write(result['text'])
                    # Aqui você pode adicionar a lógica de sobreposição se o ImageMagick colaborar
        clip_check.close()

# --- MÓDULO 2: VÍDEO DE FOTOS (TOUR COM PILLOW) ---
elif menu == "Vídeo de Fotos (Tour)":
    st.header("📸 Tour de Fotos com Legendas")
    uploaded_images = st.file_uploader("Selecione até 20 fotos", type=["jpg", "png"], accept_multiple_files=True)
    
    if uploaded_images:
        if len(uploaded_images) > 20:
            st.error("Limite de 20 fotos excedido.")
        else:
            legendas = []
            cols = st.columns(2)
            for i, img_file in enumerate(uploaded_images):
                with cols[i % 2]:
                    st.image(img_file, width=150)
                    texto = st.text_input(f"Legenda {i+1}", key=f"tour_{i}")
                    legendas.append(texto)

            if st.button("Criar Vídeo"):
                with st.spinner("Desenhando legendas nas fotos..."):
                    try:
                        clips = []
                        temp_files = []
                        t_stamp = int(time.time())

                        for i, img_file in enumerate(uploaded_images):
                            # 1. Abrir a imagem com Pillow
                            img = Image.open(img_file).convert("RGB")
                            
                            # 2. Desenhar a legenda se existir
                            if legendas[i].strip():
                                draw = ImageDraw.Draw(img)
                                # Tenta usar uma fonte do sistema, se não, usa a padrão
                                try:
                                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                                except:
                                    font = ImageFont.load_default()
                                
                                # Desenha barra preta no rodapé
                                draw.rectangle([0, img.height-100, img.width, img.height], fill=(0,0,0,180))
                                draw.text((40, img.height-80), legendas[i].upper(), fill="white", font=font)

                            # 3. Salvar imagem processada
                            img_path = f"temp/proc_{t_stamp}_{i}.jpg"
                            img.save(img_path)
                            temp_files.append(img_path)

                            # 4. Criar clipe para o MoviePy
                            clips.append(ImageClip(img_path).set_duration(3).crossfadein(0.5))

                        # 5. Concatenar e gerar vídeo
                        final_video = concatenate_videoclips(clips, method="compose")
                        out_path = f"temp/tour_{t_stamp}.mp4"
                        final_video.write_videofile(out_path, fps=24, codec="libx264")

                        st.video(out_path)
                        with open(out_path, "rb") as f:
                            st.download_button("Baixar Tour", f, file_name="tour_imovel.mp4")
                        
                        cleanup_files(*temp_files, out_path)
                    except Exception as e:
                        st.error(f"Erro: {e}")