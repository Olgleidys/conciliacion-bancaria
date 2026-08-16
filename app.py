import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema de Conciliación Bancaria", layout="wide")

# --- FUNCIONES ---
def limpiar_monto(serie):
    if serie is None: return 0.0
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors="coerce").fillna(0.0).round(2)

def estandarizar_columnas(df, tipo):
    """
    Estandariza columnas. Busca nombres aproximados pero normaliza a nombres exactos requeridos.
    """
    # Mapeo de nombres esperados (Case insensitive)
    cols_map = {c.lower(): c for c in df.columns}
    
    if tipo == "banco":
        # Buscamos nombres parecidos a los requeridos
        rename_dict = {}
        if "fecha" in cols_map: rename_dict[cols_map["fecha"]] = "fecha"
        if "referencia" in cols_map: rename_dict[cols_map["referencia"]] = "referencia"
        if "descripcion" in cols_map: rename_dict[cols_map["descripcion"]] = "descripcion"
        if "debito" in cols_map: rename_dict[cols_map["debito"]] = "debito"
        if "credito" in cols_map: rename_dict[cols_map["credito"]] = "credito"
        
        df = df.rename(columns=rename_dict)
        # Asegurar columnas necesarias
        df["debito"] = limpiar_monto(df.get("debito", 0))
        df["credito"] = limpiar_monto(df.get("credito", 0))
        df["Monto_Final"] = df["credito"] - df["debito"]
    else:
        rename_dict = {}
        if "fecha" in cols_map: rename_dict[cols_map["fecha"]] = "fecha"
        if "referencia" in cols_map: rename_dict[cols_map["referencia"]] = "referencia"
        if "descripcion" in cols_map: rename_dict[cols_map["descripcion"]] = "descripcion"
        if "debe" in cols_map: rename_dict[cols_map["debe"]] = "debe"
        if "haber" in cols_map: rename_dict[cols_map["haber"]] = "haber"
        
        df = df.rename(columns=rename_dict)
        df["debe"] = limpiar_monto(df.get("debe", 0))
        df["haber"] = limpiar_monto(df.get("haber", 0))
        df["Monto_Final"] = df["debe"] - df["haber"]

    # Normalizar Referencia
    df["referencia"] = df["referencia"].astype(str).str.strip().replace("nan", "")
    df["ref_3"] = df["referencia"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    return df

def check_4_digits(m1, m2):
    s1 = f"{abs(float(m1)):.2f}".replace('.', '')
    s2 = f"{abs(float(m2)):.2f}".replace('.', '')
    if len(s1) < 4 or len(s2) < 4: return False
    for i in range(len(s1) - 3):
        if s1[i:i+4] in s2: return True
    return False

# --- UI ---
st.title("📊 Sistema de Conciliación")
f_b, f_p = st.columns(2)
file_b = f_b.file_uploader("📥 Estado de Cuenta (Banco)", type=["xlsx"])
file_p = f_p.file_uploader("📥 Reporte Profit", type=["xlsx"])

if file_b and file_p:
    df_b = estandarizar_columnas(pd.read_excel(file_b), "banco")
    df_p = estandarizar_columnas(pd.read_excel(file_p), "profit")
    
    pend_b, pend_p = df_b.copy(), df_p.copy()
    conciliados = pd.DataFrame()
    alertas = pd.DataFrame()

    # --- PUNTOS 1 AL 3: CONCILIACIÓN ---
    # 1. Exacto
    m1 = pd.merge(pend_b, pend_p, on=["referencia", "Monto_Final"], suffixes=("_B", "_P"))
    if not m1.empty:
        m1["Regla"] = "1. Exacto"
        conciliados = pd.concat([conciliados, m1])
        pend_b = pend_b[~pend_b.index.isin(m1.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m1.index.get_level_values(0))]

    # 2. Ref 3 dígitos + Monto
    m2 = pd.merge(pend_b, pend_p, on=["ref_3", "Monto_Final"], suffixes=("_B", "_P"))
    if not m2.empty:
        m2["Regla"] = "2. Ref 3 Digitos + Monto"
        conciliados = pd.concat([conciliados, m2])
        pend_b = pend_b[~pend_b.index.isin(m2.index.get_level_values(0))]
        pend_p = pend_p[~pend_p.index.isin(m2.index.get_level_values(0))]

    # 3. Sumatoria Profit
    df_p_grouped = pend_p.groupby(["ref_3", "Monto_Final"])["Monto_Final"].sum().reset_index(name="Suma_Profit")
    m3 = pd.merge(pend_b, df_p_grouped, on=["ref_3", "Monto_Final"])
    if not m3.empty:
        m3["Regla"] = "3. Sumatoria Profit"
        conciliados = pd.concat([conciliados, m3])

    # --- CRUCES (Exclusivo Debe Banco / Haber Profit) ---
    cruce_dh = pd.merge(df_b[df_b["debito"] > 0], df_p[df_p["haber"] > 0], on="referencia")
    cruce_dh = cruce_dh[cruce_dh["debito"] == cruce_dh["haber"]]
    cruce_dh["Regla"] = "Cruce Debe Banco vs Haber Profit"

    # --- PUNTOS 4 AL 6: DETECCIÓN DE DUPLICADOS (Sobre data original) ---
    # 4. Duplicado Exacto
    dup_4 = df_b[df_b.duplicated(subset=["referencia", "Monto_Final"], keep=False) & (df_b["referencia"] != "")]
    if not dup_4.empty:
        dup_4["Alerta"] = "4. Duplicado Exacto"
        alertas = pd.concat([alertas, dup_4])
    
    # 5. Duplicado 3 dígitos
    dup_5 = df_b[df_b.duplicated(subset=["ref_3", "Monto_Final"], keep=False) & (df_b["referencia"] != "")]
    if not dup_5.empty:
        dup_5["Alerta"] = "5. Duplicado 3 Digitos"
        alertas = pd.concat([alertas, dup_5])
    
    # 6. Error 4 dígitos (Finger error)
    for ref, group in df_b[df_b["referencia"] != ""].groupby("referencia"):
        if len(group) > 1:
            for i, row1 in group.iterrows():
                for j, row2 in group.iterrows():
                    if i < j and check_4_digits(row1["Monto_Final"], row2["Monto_Final"]):
                        err = pd.DataFrame([row1, row2])
                        err["Alerta"] = "6. Error 4 Digitos Consecutivos"
                        alertas = pd.concat([alertas, err])

    # --- PESTAÑAS ---
    tabs = st.tabs(["✅ Conciliado", "🏦 Pendiente Banco", "💻 Pendiente Profit", "🔄 Cruces (Debe/Haber)", "⚠️ Alertas (Duplicados)"])
    tabs[0].dataframe(conciliados, use_container_width=True)
    tabs[1].dataframe(pend_b, use_container_width=True)
    tabs[2].dataframe(pend_p, use_container_width=True)
    tabs[3].dataframe(cruce_dh, use_container_width=True)
    tabs[4].dataframe(alertas.drop_duplicates(), use_container_width=True)
