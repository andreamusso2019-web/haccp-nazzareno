import streamlit as st
import google.generativeai as genai
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
import json

# --- 1. CONFIGURAZIONE GOOGLE GEMINI ---
API_KEY = "AIzaSyCFhXz8lht9koQFjXOyCdwEpfvJaLAqQ6A" # La tua chiave
genai.configure(api_key=API_KEY)

# --- 2. IMPOSTAZIONI PAGINA ---
st.set_page_config(page_title="HACCP Nazzareno", page_icon="🥖", layout="centered")
st.title("🥖 Gestione HACCP Panificio")

if 'dati_ddt' not in st.session_state:
    st.session_state.dati_ddt = None

# --- 3. CARICAMENTO DEL DOCUMENTO ---
st.write("### 1. Carica il Documento di Trasporto")
uploaded_file = st.file_uploader("📸 Scatta foto o carica DDT/Fattura (anche PDF)", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    is_pdf = uploaded_file.name.lower().endswith('.pdf')
    
    if is_pdf:
        st.info("📄 File PDF riconosciuto e caricato correttamente.")
        file_to_send = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
    else:
        image = Image.open(uploaded_file)
        st.image(image, caption="Documento Caricato", use_container_width=True)
        file_to_send = image
    
    if st.button("🧠 Leggi Documento con IA", type="primary"):
        with st.spinner('L\'IA sta analizzando il documento...'):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = """
                Sei un assistente esperto di HACCP. Leggi questo DDT/Fattura ed estrai i dati.
                Restituisci i dati seguendo esattamente questo formato:
                {
                  "fornitore": "Nome Fornitore",
                  "numero_ddt": "Numero DDT",
                  "data_ricezione": "DD/MM/YYYY",
                  "prodotti": [
                    {"nome": "Nome prodotto 1", "lotto": "Lotto 1"},
                    {"nome": "Nome prodotto 2", "lotto": "Lotto 2"}
                  ]
                }
                Se non trovi un lotto per un prodotto, scrivi "N/D".
                """
                
                # FORZIAMO GEMINI A NON CHIACCHIERARE E DARE SOLO I DATI
                response = model.generate_content(
                    [prompt, file_to_send],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                dati = json.loads(response.text)
                st.session_state.dati_ddt = dati
                st.rerun()
                
            except Exception as e:
                # ORA VEDREMO IL VERO MOTIVO DELL'ERRORE!
                st.error(f"⚠️ Si è verificato un errore: {e}")
                if 'response' in locals():
                    st.warning(f"Dati grezzi ricevuti: {response.text}")

# --- 4. SEZIONE RICETTARIO E ETICHETTA ---
if st.session_state.dati_ddt:
    dati = st.session_state.dati_ddt
    st.success("✅ Documento letto con successo!")
    st.write(f"**Fornitore:** {dati.get('fornitore', 'N/D')} | **DDT:** {dati.get('numero_ddt', 'N/D')} | **Data:** {dati.get('data_ricezione', 'N/D')}")
    
    st.markdown("---")
    st.write("### 2. Scegli Materia Prima e Piatto")
    
    lista_prodotti = [f"{p['nome']} (Lotto: {p['lotto']})" for p in dati.get('prodotti', [])]
    
    if lista_prodotti:
        prodotto_selezionato = st.selectbox("Quale materia prima stai usando in questo momento?", lista_prodotti)
        
        indice = lista_prodotti.index(prodotto_selezionato)
        materia_prima = dati['prodotti'][indice]['nome']
        lotto_originale = dati['prodotti'][indice]['lotto']
        
        piatto = st.selectbox("Cosa ci stai preparando?", ["Tagliata di Pollo", "Salmone o Pesce (Abbattuto)", "Altra Preparazione Libera..."])
        
        oggi = datetime.date.today()
        
        if piatto == "Tagliata di Pollo":
            st.info("⚙️ Regola applicata: Cottura a 80° - Abbattuto a 3°. Scadenza calcolata a +1 mese.")
            scadenza = oggi + relativedelta(months=1)
            note = "Cotto 80° - Abbattuto a 3°"
            descrizione_finale = "TAGLIATE DI POLLO"
            
        elif piatto == "Salmone o Pesce (Abbattuto)":
            st.info("⚙️ Regola applicata: Crudo/Decongelato, Abbattuto a -18°. Scadenza calcolata a +3 mesi.")
            scadenza = oggi + relativedelta(months=3)
            note = "Abbattuto a -18°"
            descrizione_finale = materia_prima.upper()
            
        else:
            descrizione_finale = st.text_input("Nome Prodotto Finale (es. Polpette):", materia_prima)
            note = st.text_input("Inserisci lo stato (es. Cotto a 80°):")
            giorni_scad = st.number_input("Quanti giorni di scadenza?", min_value=1, value=3)
            scadenza = oggi + datetime.timedelta(days=giorni_scad)

        st.markdown("---")
        if st.button("🖨️ Genera Etichetta Definitiva", type="primary"):
            stringa_lotto = f"{dati.get('data_ricezione')}, {dati.get('numero_ddt')}, {lotto_originale}"
            
            etichetta_finale = f"""{descrizione_finale}
Data Cottura: {oggi.strftime("%d/%m/%Y")}
Scadenza: {scadenza.strftime("%d/%m/%Y")}
Note: {note}
Lotto: {stringa_lotto}"""
            
            st.code(etichetta_finale, language="text")
            st.caption("Premi il bottoncino in alto a destra nel riquadro nero per copiare, poi incolla nell'App Brother.")
            
    else:
        st.warning("Non sono riuscito a trovare prodotti in questo documento.")