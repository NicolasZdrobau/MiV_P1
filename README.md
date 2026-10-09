# Pràctica 1 MiV – Redisseny del gràfic de viatgers de Renfe, Iryo i Ouigo

Redisseny interactiu del gràfic publicat pel president de Renfe a X (maig 2026),
amb dades oficials de la CNMC (CNMCData).

## Fitxers
- `ds_24406_1.csv` – dataset original de la CNMC (transport ferroviari de viatgers)
- `preprocessament.py` – Fase 2: filtratge, agrupament, normalització i reconfiguració
- `app.py` – Fase 3: aplicació interactiva amb Streamlit + Plotly

## Com executar-ho
```bash
pip install -r requirements.txt
streamlit run app.py
```
S'obre al navegador a `http://localhost:8501`.
