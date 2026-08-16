import io
import pandas as pd
import streamlit as st
import itertools

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Sistema de Conciliación Bancaria", layout="wide")
custom_css = """
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    h1, h2, h3 { color: #f8fafc !important; }
    .stDownloadButton button { background-color: #0284c7 !important; color: white !important; font-weight: bold; width: 100%; padding: 10px; border-radius: 8px;}
    .footer { text-align: center; padding: 20px; font-size: 14px; color: #94a3b8; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- INSTRUCCIONES ---
with st.expander("📝 Instrucciones de uso"):
    st.write("""
    1. **Carga**: Sube el archivo de Banco y el de Profit.
    2. **Proceso**: El sistema ejecuta 6 reglas:
       - **Reglas de Éxito (1-3)**: Concilian automáticamente.
       - **Reglas de Alerta (4-6)**: Detectan errores de digitación o duplicados sin conciliar.
    3. **Resultado**: Descarga el Excel con los hallazgos categorizados.
    """)

# --- FUNCIONES DE NORMALIZACIÓN ---
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0.0).round(2)

def normalizar_archivo(file, tipo):
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    col_ref = next((c for c in df.columns if any(k in c for k in ["referencia", "ref", "doc"])), df.columns[0])
    df = df.rename(columns={col_ref: "Ref"})
    df["Ref"] = df["Ref"].apply(lambda x: str(x).strip().replace(".0", ""))
    df["Ref_3"] = df["Ref"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    # Calcular Monto Final
    if tipo == "banco":
        df["Monto_Final"] = limpiar_monto(df.get("cred", 0)) - limpiar_monto(df.get("deb", 0))
    else:
        df["Monto_Final"] = limpiar_monto(df.get("debe", 0)) - limpiar_monto(df.get("haber", 0))
    return df

# --- PROCESAMIENTO (LOS 6 PUNTOS) ---
file_b = st.file_uploader("📥 Banco", type=["xlsx"])
file_p = st.file_uploader("📥 Profit", type=["xlsx"])

if file_b and file_p:
    banco_df = normalizar_archivo(file_b, "banco")
    profit_df = normalizar_archivo(file_p, "profit")
    
    # Listas de pendientes
    pend_b = banco_df.copy()
    pend_p = profit_df.copy()
    conciliados = pd.DataFrame()
    alertas = pd.DataFrame()

    # --- REGLA 1: Exacto (Ref + Monto) ---
    m1 = pd.merge(pend_b, pend_p, on=["Ref", "Monto_Final"], suffixes=("_B", "_P"))
    if not m1.empty:
        m1["Regla"] = "1. Exacto"
        conciliados = pd.concat([conciliados, m1])
        pend_b = pend_b[~pend_b.index.isin(m1.index.get_level_values(0))] # Ajustar según índice
        pend_p = pend_p[~pend_p.index.isin(m1.index.get_level_values(0))]

    # --- REGLA 2: Ref 3 dígitos + Monto ---
    m2 = pd.merge(pend_b, pend_p, on=["Ref_3", "Monto_Final"], suffixes=("_B", "_P"))
    if not m2.empty:
        m2["Regla"] = "2. Ref 3 Digitos + Monto"
        conciliados = pd.concat([conciliados, m2])
        pend_b = pend_b[~pend_b.index.isin(m2.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m2.index.get_level_values(0))]

    # --- REGLA 3: Sumatoria (Profit vs Banco) ---
    sumatoria = pend_p.groupby("Ref_3")["Monto_Final"].sum().reset_index()
    m3 = pd.merge(pend_b, sumatoria, on=["Ref_3", "Monto_Final"], suffixes=("_B", "_P"))
    if not m3.empty:
        m3["Regla"] = "3. Sumatoria Profit"
        conciliados = pd.concat([conciliados, m3])
        # Nota: Aquí no removemos todos porque pueden ser múltiples registros de Profit
        pend_b = pend_b[~pend_b.index.isin(m3.index.get_level_values(0))]

    # --- REGLA 4: Duplicado Exacto ---
    dup_b = banco_df[banco_df.duplicated(subset=["Ref", "Monto_Final"], keep=False)]
    if not dup_b.empty:
        dup_b["Regla"] = "4. Duplicado Exacto"
        alertas = pd.concat([alertas, dup_b])

    # --- REGLA 5: Duplicado 3 Digitos ---
    dup_3 = banco_df[banco_df.duplicated(subset=["Ref_3", "Monto_Final"], keep=False)]
    if not dup_3.empty:
        dup_3["Regla"] = "5. Duplicado 3 Digitos"
        alertas = pd.concat([alertas, dup_3])

    # --- REGLA 6: Error Digitación (4 dígitos consecutivos) ---
    def check_4_digits(m1, m2):
        s1 = f"{abs(float(m1)):.2f}".replace('.', '')
        s2 = f"{abs(float(m2)):.2f}".replace('.', '')
        for i in range(len(s1) - 3):
            if s1[i:i+4] in s2: return True
        return False

    for ref, group in banco_df.groupby("Ref"):
        if len(group) > 1:
            for i, row in group.iterrows():
                for j, row2 in group.iterrows():
                    if i < j and check_4_digits(row["Monto_Final"], row2["Monto_Final"]):
                        err = pd.DataFrame([row, row2])
                        err["Regla"] = "6. Error 4 Digitos"
                        alertas = pd.concat([alertas, err])

    # --- RESULTADOS ---
    tabs = st.tabs(["✅ Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit", "⚠️ Alertas (4-6)"])
    tabs[0].dataframe(conciliados)
    tabs[1].dataframe(pend_b)
    tabs[2].dataframe(pend_p)
    tabs[3].dataframe(alertas.drop_duplicates())

    # --- DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        conciliados.to_excel(writer, sheet_name="Conciliados", index=False)
        alertas.to_excel(writer, sheet_name="Alertas", index=False)
    st.download_button("📥 Descargar Reporte Final", output.getvalue(), "Conciliacion_Final.xlsx")

st.markdown('<div class="footer">Sistema Automatizado | Olgleidys Hernández</div>', unsafe_allow_html=True)
