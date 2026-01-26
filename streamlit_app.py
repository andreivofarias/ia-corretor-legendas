import streamlit as st
import whisper
import os

st.set_page_config(page_title="Legenda Imobiliária IA", page_icon="🏠")

st.title("🏠 Gerador de Legendas para Corretores")
st.markdown("Suba seu vídeo e a IA extrairá o texto automaticamente.")

uploaded_file = st.file_uploader("Escolha um vídeo de imóvel", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Salva o arquivo temporariamente
    with open("video_input.mp4", "wb") as f:
        f.write(uploaded_file.read())
    
    st.video("video_input.mp4")
    
    if st.button("Gerar Transcrição"):
        with st.spinner("A IA está ouvindo o vídeo..."):
            # Carrega o modelo de IA
            model = whisper.load_model("tiny") # 'tiny' é o mais rápido para o plano grátis
            result = model.transcribe("video_input.mp4")
            
            st.subheader("Texto Transcrito:")
            st.write(result["text"])
            
            # Botão para baixar o texto
            st.download_button("Baixar Legenda (TXT)", result["text"])