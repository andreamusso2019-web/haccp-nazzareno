import streamlit as st
import google.generativeai as genai
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
import json

# --- CONFIGURAZIONE ---
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ Chiave API non trovata nei Secrets di Streamlit!")
    st.stop()

st.set_page_config(page_title="HACCP Nazzareno", page_icon="🥖")
st.title("🥖 HACCP Automatica")

if 'dati_ddt' not in st.session_state:
    st.session_state.dati_ddt = None

# --- CARICAMENTO ---
st.write("### Carica il Documento")
uploaded_file = st.file_uploader("📂 Seleziona PDF o Foto", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file:
    # Calcola il peso del file in Megabyte
    peso_mb = uploaded_file.size / (1024 * 1024)
    
    st.info(f"📄 File '{uploaded_file.name}' in memoria (Peso: {peso_mb:.1f} MB).")
    
    if st.button("🚀 ANALIZZA DOCUMENTO", type="primary"):
        with st.spinner('Lettura in corso... il telefono sta elaborando ⏳'):
            try:
                if uploaded_file.name.lower().endswith('.pdf'):
                    # LA BILANCIA SALVAVITA PER I TELEFONI
                    if peso_mb > 2.5: # Se pesa più di 2.5 MB, il telefono rischia di bloccarsi
                        st.error("⚠️ Questo PDF è troppo pesante per la memoria del browser del telefono!")
                        st.warning("💡 TRUCCO: Apri il PDF sul cellulare, fai uno **Screenshot** alla pagina coi lotti, e carica lo screenshot come Foto!")
                        st.stop() # Ferma tutto prima che il telefono si blocchi
                    else:
                        content = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                else:
                    img = Image.open(uploaded_file)
                    img.thumbnail((800, 800)) 
                    content = img

                # IL MODELLO VINCENTE (2.5)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = "Analizza questo DDT/Fattura e restituisci SOLO JSON: {fornitore, numero_ddt, data_ricezione, prodotti: [{nome, lotto}]}. Se non trovi il lotto scrivi N/D."
                
                response = model.generate_content([prompt, content], generation_config={"response_mime_type": "application/json"})
                
                st.session_state.dati_ddt = json.loads(response.text)
                st.success("✅ Lettura completata con successo!")
                
            except Exception as e:
                st.error("⚠️ Il telefono ha interrotto la connessione o c'è un errore.")
                st.error(f"Dettaglio tecnico: {e}")

# --- RISULTATI ---
if st.session_state.dati_ddt:
    d = st.session_state.dati_ddt
    st.markdown(f"**Fornitore:** {d.get('fornitore', 'N/D')}")
    
    prodotti = [f"{p['nome']} (Lotto: {p['lotto']})" for p in d.get('prodotti', [])]
    
    if prodotti:
        scelta = st.selectbox("Quale prodotto stai lavorando?", prodotti)
        preparazione = st.radio("Cosa hai preparato?", ["Tagliata Pollo (Cotta)", "Salmone (Abbattuto)", "Altro"])
        
        oggi = datetime.date.today()
        if "Pollo" in preparazione:
            scad = oggi + relativedelta(months=1)
            txt = f"TAGLIATA DI POLLO\nData: {oggi.strftime('%d/%m/%Y')}\nScadenza: {scad.strftime('%d/%m/%Y')}\nLotto: {scelta}"
        elif "Salmone" in preparazione:
            scad = oggi + relativedelta(months=3)
            txt = f"SALMONE\nAbbattuto: {oggi.strftime('%d/%m/%Y')}\nScadenza: {scad.strftime('%d/%m/%Y')}\nLotto: {scelta}"
        else:
            txt = f"PRODOTTO: {scelta}\nData: {oggi.strftime('%d/%m/%Y')}"
            
        st.code(txt, language="text")
        st.caption("Copia e incolla nell'app della stampante.")
