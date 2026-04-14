import streamlit as st
import google.generativeai as genai
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
import json

# --- CONFIGURAZIONE SICURA ---
# Se hai seguito il mio consiglio dei "Secrets", usa questa riga:
try:
    API_KEY = st.secrets["GEMINI_KEY"]
except:
    # Altrimenti usa la tua chiave diretta (ma attenzione alle email di GitHub!)
    API_KEY = "AIzaSyCFhXz8lht9koQFjXOyCdwEpfvJaLAqQ6A"

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="HACCP Nazzareno", page_icon="🥖")
st.title("🥖 HACCP Automatica")

if 'dati_ddt' not in st.session_state:
    st.session_state.dati_ddt = None

# --- CARICAMENTO ---
uploaded_file = st.file_uploader("📸 Carica o Scatta Foto DDT", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    # Mostra un'anteprima piccola per non appesantire il telefono
    st.success("File caricato!")
    
    if st.button("🚀 ANALIZZA ORA", type="primary"):
        with st.spinner('Lettura in corso...'):
            try:
                # Gestione PDF o Immagine
                if uploaded_file.name.lower().endswith('.pdf'):
                    content = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                else:
                    img = Image.open(uploaded_file)
                    # Ridimensioniamo la foto se è troppo grande (salva giga e tempo)
                    img.thumbnail((1600, 1600)) 
                    content = img

                model = genai.GenerativeModel('gemini-1.5-flash') # Ho rimesso 1.5 perché la 2.0 a volte è instabile su alcune regioni
                
                prompt = "Analizza questo DDT e restituisci SOLO JSON: {fornitore, numero_ddt, data_ricezione, prodotti: [{nome, lotto}]}"
                
                response = model.generate_content(
                    [prompt, content],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                st.session_state.dati_ddt = json.loads(response.text)
                st.rerun()
                
            except Exception as e:
                st.error(f"Errore tecnico: {e}")

# --- RISULTATI E ETICHETTA ---
if st.session_state.dati_ddt:
    d = st.session_state.dati_ddt
    st.markdown(f"**Fornitore:** {d.get('fornitore')}")
    
    prodotti = [f"{p['nome']} (Lotto: {p['lotto']})" for p in d.get('prodotti', [])]
    scelta = st.selectbox("Cosa stai lavorando?", prodotti)
    
    preparazione = st.radio("Tipo di preparazione:", ["Tagliata Pollo (Cotta)", "Salmone (Abbattuto)", "Altro"])
    
    if st.button("✅ GENERA ETICHETTA"):
        oggi = datetime.date.today()
        # Logiche semplificate
        if "Pollo" in preparazione:
            scad = oggi + relativedelta(months=1)
            txt = f"TAGLIATA DI POLLO\nCottura: {oggi}\nScadenza: {scad}\nLotto: {scelta}"
        elif "Salmone" in preparazione:
            scad = oggi + relativedelta(months=3)
            txt = f"SALMONE\nAbbattuto: {oggi}\nScadenza: {scad}\nLotto: {scelta}"
        else:
            txt = f"PRODOTTO: {scelta}\nData: {oggi}"
            
        st.code(txt)
        st.info("Copia e incolla nell'app Brother")
