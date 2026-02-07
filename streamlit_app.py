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

# --- MÓDULO 1: LEGENDAR VÍDEO (DINÂMICO + EFEITOS + CONTADOR) ---
if menu == "Legendar Vídeo":
    st.header("🎬 Gerador de Legendas Dinâmicas")
    
    # Inicializa o contador na sessão se não existir
    if 'contador_videos' not in st.session_state:
        st.session_state.contador_videos = 0

    # Exibe o contador de forma elegante
    st.sidebar.metric("Vídeos Processados", st.session_state.contador_videos)
    
    st.info("Limite: 60 segundos por vídeo.")
    video_file = st.file_uploader("Suba o vídeo do imóvel", type=["mp4", "mov"])
    
    if video_file:
        t_stamp = int(time.time())
        input_path = f"temp/in_{t_stamp}.mp4"
        output_path = f"temp/out_{t_stamp}.mp4"
        
        with open(input_path, "wb") as f: 
            f.write(video_file.read())
        
        clip = VideoFileClip(input_path)
        
        if clip.duration > 60:
            st.error(f"Vídeo de {clip.duration:.1f}s excede o limite de 60s.")
            clip.close()
            cleanup_files(input_path)
        else:
            if st.button("Gerar Vídeo com Legendas e Efeitos"):
                with st.spinner("IA Sincronizando frases..."):
                    try:
                        # 1. Transcrição com Whisper
                        model = whisper.load_model("tiny")
                        result = model.transcribe(input_path)
                        segments = result.get('segments', [])

                        subtitle_clips = []
                        temp_imgs = []

                        # --- LOOP DE SEGMENTOS (CORREÇÃO E EFEITOS) ---
                        for i, seg in enumerate(segments):
                            texto = seg['text'].strip().upper()
                            start_t = seg['start']
                            end_t = seg['end']
                            
                            if not texto: continue

                            # Criar imagem da legenda (Pillow)
                            txt_img = Image.new('RGBA', (clip.w, clip.h), (255, 255, 255, 0))
                            draw = ImageDraw.Draw(txt_img)
                            
                            try:
                                font_size = int(clip.w * 0.045) # Fonte proporcional à largura
                                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                            except:
                                font = ImageFont.load_default()

                            # Barra de fundo
                            barra_h = int(clip.h * 0.12)
                            draw.rectangle([0, clip.h - barra_h - 40, clip.w, clip.h - 40], fill=(0, 0, 0, 180))
                            
                            # Texto Centralizado
                            w_txt = draw.textlength(texto, font=font)
                            draw.text(((clip.w - w_txt) // 2, clip.h - barra_h - 30), texto, fill="white", font=font)
                            
                            seg_img_path = f"temp/seg_{t_stamp}_{i}.png"
                            txt_img.save(seg_img_path)
                            temp_imgs.append(seg_img_path)

                            # Criar clipe com FADE IN e FADE OUT
                            txt_clip = (ImageClip(seg_img_path)
                                        .set_start(start_t)
                                        .set_duration(max(0.1, end_t - start_t))
                                        .set_position('center')
                                        .crossfadein(0.2)
                                        .crossfadeout(0.2))
                            
                            subtitle_clips.append(txt_clip)

                        # 4. Mesclagem e Contador
                        if subtitle_clips:
                            video_final = CompositeVideoClip([clip] + subtitle_clips)
                            video_final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                            
                            st.success("Vídeo finalizado!")
                            st.video(output_path)
                            
                            # Incrementa o contador após sucesso
                            st.session_state.contador_videos += 1
                            
                            with open(output_path, "rb") as f:
                                st.download_button("Baixar Vídeo", f, file_name="imovel_pro.mp4")
                        else:
                            st.warning("Nenhuma fala detectada.")

                        cleanup_files(*temp_imgs)
                            
                    except Exception as e:
                        st.error(f"Erro no processamento: {e}")
                    finally:
                        clip.close()
                        cleanup_files(input_path, output_path)
    
# --- MÓDULO 2: VÍDEO DE FOTOS (TOUR COM PILLOW) ---
# --- MÓDULO 2: VÍDEO DE FOTOS (OTIMIZADO PARA CELULAR) ---
elif menu == "Vídeo de Fotos (Tour)":
    st.header("📸 Tour de Fotos")
    
    # Botão para limpar o cache se as coisas travarem
    if st.sidebar.button("Limpar Memória do App"):
        st.cache_data.clear()
        st.success("Memória limpa!")

    uploaded_images = st.file_uploader("Selecione fotos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_images:
        legendas = []
        # Reduzimos o número de colunas no mobile para não travar o render do navegador
        for i, img_file in enumerate(uploaded_images):
            # 1. Redimensionamento preventivo (O segredo para não travar o celular)
            # Abrimos a imagem em modo 'lazy' para não estourar a RAM
            with Image.open(img_file) as img_temp:
                img_temp.verify() # Verifica se o arquivo não está corrompido
            
            img_view = Image.open(img_file)
            img_view.thumbnail((300, 300)) # Miniatura leve para o navegador do celular
            st.image(img_view, caption=f"Foto {i+1}")
            
            texto = st.text_input(f"Legenda {i+1}", key=f"tour_mob_{i}")
            legendas.append(texto)

        if st.button("Criar Vídeo"):
            with st.status("Processando...", expanded=True) as status:
                try:
                    clips = []
                    temp_files = []
                    t_stamp = int(time.time())

                    for i, img_file in enumerate(uploaded_images):
                        # Forçar conversão para RGB e Redução de resolução
                        # Fotos de celulares modernos têm 12MP+, o que trava o servidor free
                        with Image.open(img_file) as img:
                            img = img.convert("RGB")
                            # Reduzimos para Full HD no máximo para economizar RAM
                            img.thumbnail((1920, 1080))
                            
                            if legendas[i].strip():
                                draw = ImageDraw.Draw(img)
                                try:
                                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
                                except:
                                    font = ImageFont.load_default()
                                
                                draw.rectangle([0, img.height-120, img.width, img.height], fill=(0,0,0,180))
                                draw.text((40, img.height-90), legendas[i].upper(), fill="white", font=font)

                            img_path = f"temp/mob_proc_{t_stamp}_{i}.jpg"
                            img.save(img_path, "JPEG", quality=85) # Quality 85 economiza muito espaço
                            temp_files.append(img_path)
                            clips.append(ImageClip(img_path).set_duration(3).set_fps(24))

                    status.update(label="Gerando arquivo de vídeo...", state="running")
                    final_video = concatenate_videoclips(clips, method="compose")
                    out_path = f"temp/tour_{t_stamp}.mp4"
                    
                    # Usamos o preset 'ultrafast' para o servidor não cansar
                    final_video.write_videofile(out_path, fps=24, codec="libx264", preset="ultrafast")

                    st.video(out_path)
                    status.update(label="Vídeo pronto!", state="complete")
                    
                    with open(out_path, "rb") as f:
                        st.download_button("Baixar Vídeo", f, file_name="tour_celular.mp4")
                    
                    cleanup_files(*temp_files, out_path)
                except Exception as e:
                    st.error(f"Erro no celular: {e}")