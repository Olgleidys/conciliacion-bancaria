import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Auditoría Contable Pro", layout="wide")

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0.0).round(2)

def limpiar_ref(ref):
    return str(ref).replace(".0", "").strip().lstrip("0")

# --- UI ---
st.title("⚖️ Auditoría de Conciliación: Reglas de Cero Diferencias")

col1, col2 = st.columns(2)
file_b = col1.file_uploader("Estado de Cuenta Banco (Excel)", type=["xlsx"])
file_p = col2.file_uploader("Reporte Profit Plus (Excel)", type=["xlsx"])

if file_b and file_p:
    # Cargar y Normalizar
    df_b = pd.read_excel(file_b)
    df_p = pd.read_excel(file_p)
    
    df_b.columns = [c.lower().strip() for c in df_b.columns]
    df_p.columns = [c.lower().strip() for c in df_p.columns]
    
    # Preparar Banco
    df_b["monto"] = df_b["debito"] if "debito" in df_b.columns else 0.0
    df_b["monto"] = df_b["monto"] + limpiar_monto(df_b["credito"]) # Sumamos ambos lados para tener valor absoluto
    df_b["ref_clean"] = df_b["referencia"].apply(limpiar_ref)
    df_b["ref_3"] = df_b["ref_clean"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    # Preparar Profit
    df_p["monto"] = limpiar_monto(df_p["debe"]) + limpiar_monto(df_p["haber"])
    df_p["ref_clean"] = df_p["referencia"].apply(limpiar_ref)
    df_p["ref_3"] = df_p["ref_clean"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    # --- PROCESO DE AUDITORÍA ---
    conciliados = pd.DataFrame()
    pend_b = df_b.copy()
    pend_p = df_p.copy()
    
    # R1: Exacto
    m1 = pd.merge(pend_b, pend_p, on=["ref_clean", "monto"], suffixes=('_b', '_p'))
    m1["Regla"] = "R1: Exacto"
    conciliados = pd.concat([conciliados, m1])
    pend_b = pend_b.drop(m1.index_b.unique())
    pend_p = pend_p.drop(m1.index_p.unique())
    
    # R2: 3 Digitos
    m2 = pd.merge(pend_b, pend_p, on=["ref_3", "monto"], suffixes=('_b', '_p'))
    m2["Regla"] = "R2: 3 Digitos"
    conciliados = pd.concat([conciliados, m2])
    pend_b = pend_b.drop(m2.index_b.unique())
    pend_p = pend_p.drop(m2.index_p.unique())
    
    # R3: Sumatoria (Profit vs Banco)
    p_sum = pend_p.groupby(["ref_3", "monto"])["monto"].sum().reset_index(name="monto_sumado")
    m3 = pd.merge(pend_b, p_sum, left_on=["ref_3", "monto"], right_on=["ref_3", "monto_sumado"])
    m3["Regla"] = "R3: Sumatoria"
    conciliados = pd.concat([conciliados, m3])
    
    # R4 & R5: Alertas (Duplicados en Profit)
    alertas_p = pend_p[pend_p.duplicated(subset=["ref_clean", "monto"], keep=False)]
    alertas_p["Regla"] = "R4/R5: Duplicado Profit"
    
    # R6: Detección de errores de Transposición (Diferencia múltiplo de 9)
    # Comparamos pendientes entre sí
    transposiciones = []
    for i, b in pend_b.iterrows():
        for j, p in pend_p.iterrows():
            diff = abs(b["monto"] - p["monto"])
            if diff != 0 and diff % 9 == 0:
                transposiciones.append({"Banco_Ref": b["referencia"], "Profit_Ref": p["referencia"], "Banco_Monto": b["monto"], "Profit_Monto": p["monto"]})
    
    df_trans = pd.DataFrame(transposiciones)

    # --- UI FINAL ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ Conciliados", "🏦 Pendiente Banco", "💻 Pendiente Profit", "⚠️ Alertas (Duplicados)", "🔍 Transposiciones"])
    
    tab1.dataframe(conciliados, use_container_width=True)
    tab2.dataframe(pend_b, use_container_width=True)
    tab3.dataframe(pend_p, use_container_width=True)
    tab4.dataframe(alertas_p, use_container_width=True)
    tab5.dataframe(df_trans, use_container_width=True)
    
    # Exportar
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        conciliados.to_excel(writer, index=False, sheet_name="Conciliados")
        pend_b.to_excel(writer, index=False, sheet_name="Pendientes_Banco")
        pend_p.to_excel(writer, index=False, sheet_name="Pendientes_Profit")
    st.download_button("📥 Descargar Conciliación Completa", data=output.getvalue(), file_name="Auditoria_Final.xlsx")
