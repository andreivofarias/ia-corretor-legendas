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

# --- MÓDULO 1: LEGENDAR VÍDEO (PILLOW + MOVIEPY) ---
if menu == "Legendar Vídeo":
    st.header("🎬 Gerador de Legendas")
    video_file = st.file_uploader("Suba o vídeo (Máx 60s)", type=["mp4", "mov"])
    
    if video_file:
        t_stamp = int(time.time())
        input_path = f"temp/in_{t_stamp}.mp4"
        output_path = f"temp/out_{t_stamp}.mp4"
        
        with open(input_path, "wb") as f: 
            f.write(video_file.read())
        
        clip = VideoFileClip(input_path)
        
        if clip.duration > 60:
            st.error("Vídeo muito longo! Limite de 60s.")
            clip.close()
            cleanup_files(input_path)
        else:
            if st.button("Gerar Vídeo Legendado"):
                with st.spinner("IA Transcrevendo e Editando..."):
                    try:
                        # 1. Transcrição com Whisper
                        model = whisper.load_model("tiny")
                        result = model.transcribe(input_path)
                        texto_final = result['text'].strip()

                        if texto_final:
                            # 2. CRIAR LEGENDA COM PILLOW (Evita o erro de Security Policy)
                            # Criamos uma imagem transparente do tamanho do vídeo
                            txt_img = Image.new('RGBA', (clip.w, clip.h), (255, 255, 255, 0))
                            draw = ImageDraw.Draw(txt_img)
                            
                            try:
                                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(clip.w * 0.04))
                            except:
                                font = ImageFont.load_default()

                            # Desenha a tarja preta no rodapé
                            barra_h = int(clip.h * 0.15)
                            draw.rectangle([0, clip.h - barra_h, clip.w, clip.h], fill=(0, 0, 0, 160))
                            
                            # Centraliza o texto
                            w_txt = draw.textlength(texto_final, font=font)
                            draw.text(((clip.w - w_txt) // 2, clip.h - barra_h + 10), texto_final, fill="white", font=font)
                            
                            # Salva a legenda como imagem temporária
                            txt_img_path = f"temp/txt_{t_stamp}.png"
                            txt_img.save(txt_img_path)

                            # 3. TRANSFORMA IMAGEM EM CLIPE E SOBREPÕE
                            txt_clip = ImageClip(txt_img_path).set_duration(clip.duration).set_position('center')

                            # 4. Mesclar e Exportar
                            video_legendado = CompositeVideoClip([clip, txt_clip])
                            video_legendado.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                            
                            st.success("Vídeo Legendado com Sucesso!")
                            st.video(output_path)
                            
                            with open(output_path, "rb") as f:
                                st.download_button("Baixar Vídeo Pronto", f, file_name="video_legendado.mp4")
                            
                            cleanup_files(txt_img_path)
                        else:
                            st.warning("Não detectamos fala no vídeo.")
                            
                    except Exception as e:
                        st.error(f"Erro ao processar vídeo: {e}")
                    finally:
                        clip.close()
                        cleanup_files(input_path, output_path)
    
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