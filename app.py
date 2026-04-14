import streamlit as st
import google.generativeai as genai
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
import json

# --- CONFIGURAZIONE ---
try:
    API_KEY = st.secrets["GEMINI_KEY"]
except:
    API_KEY = "AIzaSyCFhXz8lht9koQFjXOyCdwEpfvJaLAqQ6A"

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="HACCP Nazzareno", page_icon="🥖")
st.title("🥖 HACCP Automatica")

if 'dati_ddt' not in st.session_state:
    st.session_state.dati_ddt = None

# --- CARICAMENTO ---
uploaded_file = st.file_uploader("📸 Carica o Scatta Foto", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    # Creiamo un "documento di identità" per il file, così non lo legge due volte
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    # NOVITÀ: Nessun bottone! Se il file è nuovo, parte da solo.
    if st.session_state.get('ultimo_file') != file_id:
        st.session_state.dati_ddt = None # Pulisce i dati vecchi
        
        with st.spinner('Magia in corso... sto leggendo il documento ⏳'):
            try:
                # Gestisce sia PDF che Foto
                if uploaded_file.name.lower().endswith('.pdf'):
                    content = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                else:
                    img = Image.open(uploaded_file)
                    img.thumbnail((1200, 1200)) # Sgonfia la foto per non bloccare il telefono
                    content = img

                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = "Analizza questo DDT e restituisci SOLO JSON: {fornitore, numero_ddt, data_ricezione, prodotti: [{nome, lotto}]}"
                
                response = model.generate_content(
                    [prompt, content],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # Salva i dati e ricorda che questo file è stato letto
                st.session_state.dati_ddt = json.loads(response.text)
                st.session_state.ultimo_file = file_id 
                
            except Exception as e:
                st.error(f"⚠️ Ricarica la pagina e riprova. Errore tecnico: {e}")

# --- RISULTATI E ETICHETTA ---
if st.session_state.dati_ddt:
    st.success("✅ Documento letto perfettamente!")
    d = st.session_state.dati_ddt
    st.markdown(f"**Fornitore:** {d.get('fornitore')} | **DDT:** {d.get('numero_ddt')}")
    
    prodotti = [f"{p['nome']} (Lotto: {p['lotto']})" for p in d.get('prodotti', [])]
    
    if prodotti:
        scelta = st.selectbox("Cosa stai lavorando?", prodotti)
        preparazione = st.radio("Tipo di preparazione:", ["Tagliata Pollo (Cotta)", "Salmone (Abbattuto)", "Altro"])
        
        oggi = datetime.date.today()
        if "Pollo" in preparazione:
            scad = oggi + relativedelta(months=1)
            txt = f"TAGLIATA DI POLLO\nCottura: {oggi.strftime('%d/%m/%Y')}\nScadenza: {scad.strftime('%d/%m/%Y')}\nLotto: {scelta}"
        elif "Salmone" in preparazione:
            scad = oggi + relativedelta(months=3)
            txt = f"SALMONE\nAbbattuto: {oggi.strftime('%d/%m/%Y')}\nScadenza: {scad.strftime('%d/%m/%Y')}\nLotto: {scelta}"
        else:
            txt = f"PRODOTTO: {scelta}\nData: {oggi.strftime('%d/%m/%Y')}"
            
        st.code(txt, language="text")
        st.info("👆 Clicca l'iconcina in alto a destra nel riquadro nero per copiare l'etichetta.")
    else:
        st.warning("Non ho trovato prodotti in questo documento.")
