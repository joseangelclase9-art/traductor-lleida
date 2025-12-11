import streamlit as st
import fitz
from deep_translator import GoogleTranslator
import arabic_reshaper
from bidi.algorithm import get_display
import io

# Configuración de página
st.set_page_config(page_title="Traductor Lleida", page_icon="🌍")

def procesar_texto_arabe(texto):
    if not texto: return ""
    try:
        texto_reshaped = arabic_reshaper.reshape(texto)
        texto_bidi = get_display(texto_reshaped)
        return texto_bidi
    except:
        return texto

@st.cache_data(show_spinner=False)
def traducir_pdf(archivo_pdf_bytes, idioma_origen, idioma_destino):
    doc = fitz.open(stream=archivo_pdf_bytes, filetype="pdf")
    traductor = GoogleTranslator(source=idioma_origen, target=idioma_destino)
    
    # BUCLE PRINCIPAL
    for pagina in doc:
        # REGISTRO DE FUENTE (Indented)
        try:
            pagina.insert_font(fontname="f_arabe", fontfile="NotoSansArabic-Regular.ttf")
        except:
            pass 

        bloques = pagina.get_text("dict")["blocks"]
        
        for bloque in bloques:
            if "lines" in bloque:
                for linea in bloque["lines"]:
                    for span in linea["spans"]:
                        texto_original = span["text"].strip()
                        if len(texto_original) > 0:
                            try:
                                # TRADUCCIÓN
                                texto_traducido = traductor.translate(texto_original)
                                if not texto_traducido: continue
                                
                                if idioma_destino == 'ar':
                                    texto_traducido = procesar_texto_arabe(texto_traducido)
                                    align = 2 
                                    fuente = "f_arabe"
                                else:
                                    align = 0 
                                    fuente = "helv"
                                
                                # DIBUJAR
                                x0, y0, x1, y1 = span["bbox"]
                                rect_borrado = fitz.Rect(x0, y0, x1, y1)
                                pagina.draw_rect(rect_borrado, color=(1, 1, 1), fill=(1, 1, 1))
                                
                                rect_escritura = fitz.Rect(x0 - 5, y0, x1 + 5, y1 + 20)
                                pagina.insert_textbox(rect_escritura, texto_traducido, fontsize=span["size"] - 2, fontname=fuente, align=align, color=(0, 0, 0))
                                
                            except:
                                continue

    # RETORNO (FUERA DE LOS BUCLES)
    salida_pdf = io.BytesIO()
    doc.save(salida_pdf)
    salida_pdf.seek(0)
    return salida_pdf

# INTERFAZ
st.title("🌍 Traductor de Documentos Lleida")
st.warning("⚠️ Recuerda: Traducción automática (no oficial).")

archivo_subido = st.file_uploader("Sube tu PDF aquí", type="pdf")

idiomas_disponibles = {
    "Español": "es", "Catalán": "ca", "Árabe": "ar", 
    "Rumano": "ro", "Ucraniano": "uk", "Inglés": "en", 
    "Francés": "fr", "Chino": "zh-CN", "Ruso": "ru"
}

if archivo_subido:
    option = st.selectbox("Idioma destino:", list(idiomas_disponibles.keys()))
    if st.button("🚀 Traducir"):
        with st.spinner("Traduciendo..."):
            try:
                pdf_bytes = traducir_pdf(archivo_subido, 'auto', idiomas_disponibles[option])
                st.success("¡Hecho!")
                st.download_button("📥 Descargar PDF", pdf_bytes, file_name="traduccion.pdf")
            except Exception as e:
                st.error(f"Error: {e}")
