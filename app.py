import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Conciliación Bancaria", layout="wide")

custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# --- INSTRUCCIONES DE USO ---
with st.expander("📖 Instrucciones de uso"):
  st.markdown("""
    1. Seleccione la empresa, el banco correspondiente, la frecuencia, el mes y el año.
    2. Cargue el archivo del estado de cuenta bancario en formato `.csv`.
    3. Cargue el reporte de Profit Plus en formato `.csv`.
    4. El sistema valida cruces contables estrictos, detecta duplicados en Profit y señala **inversiones de columna (Debe/Haber cruzados)**.
    5. Visualice los resultados por pestañas y descargue el reporte completo en Excel.
    """)

# --- UI DE CONFIGURACIÓN Y CARGA ---
c1, c2 = st.columns(2)
empresa = c1.selectbox(
    "🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"]
)
banco = c2.selectbox(
    "🏦 Seleccione el banco:",
    ["Banesco", "Venezuela", "Banplus", "Banplus Mazal", "Mercantil", "BFC"],
)

p1, p2, p3 = st.columns(3)
frecuencia = p1.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
mes = p2.selectbox(
    "📆 Mes:",
    [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ],
)
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2028", "2029", "2030"])

b1, b2 = st.columns(2)
banco_file = b1.file_uploader(
    f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"]
)
profit_file = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])


def limpiar_monto(serie):
  return (
      pd.to_numeric(
          serie.astype(str)
          .str.replace(".", "", regex=False)
          .str.replace(",", ".", regex=False)
          .str.strip(),
          errors="coerce",
      )
      .fillna(0)
      .abs()
  )


if banco_file and profit_file:
  df_b = pd.read_csv(banco_file, sep=None, engine="python", encoding="latin-1")
  df_p = pd.read_csv(profit_file, sep=None, engine="python", encoding="latin-1")

  df_b_proc = df_b.copy()
  df_p_proc = df_p.copy()

  # --- PROCESAMIENTO BANCO [Fecha, Referencia, Descripción, Débito, Crédito] ---
  cols_b = list(df_b_proc.columns)
  rename_b = {}
  if len(cols_b) > 0:
    rename_b[cols_b[0]] = "Fecha"
  if len(cols_b) > 1:
    rename_b[cols_b[1]] = "Referencia"
  if len(cols_b) > 2:
    rename_b[cols_b[2]] = "Descripcion"
  if len(cols_b) > 3:
    rename_b[cols_b[3]] = "Debito"
  if len(cols_b) > 4:
    rename_b[cols_b[4]] = "Credito"

  df_b_proc.rename(columns=rename_b, inplace=True)
  df_b_proc["Debito"] = (
      limpiar_monto(df_b_proc["Debito"])
      if "Debito" in df_b_proc.columns
      else 0.0
  )
  df_b_proc["Credito"] = (
      limpiar_monto(df_b_proc["Credito"])
      if "Credito" in df_b_proc.columns
      else 0.0
  )
  if "Ref" in df_b_proc.columns:
    df_b_proc["Ref"] = (
        df_b_proc["Ref"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
  df_b_proc["Ref3"] = df_b_proc["Ref"].str[-3:]
  df_b_proc["orig_idx"] = df_b_proc.index

  # --- PROCESAMIENTO PROFIT [Fecha, Referencia, Descripción, Debe, Haber] ---
  cols_p = list(df_p_proc.columns)
  start_p = 1 if len(cols_p) > 0 and str(cols_p[0]).isdigit() else 0
  rename_p = {}
  if len(cols_p) > start_p + 0:
    rename_p[cols_p[start_p + 0]] = "Fecha"
  if len(cols_p) > start_p + 1:
    rename_p[cols_p[start_p + 1]] = "Referencia"
  if len(cols_p) > start_p + 2:
    rename_p[cols_p[start_p + 2]] = "Descripcion"
  if len(cols_p) > start_p + 3:
    rename_p[cols_p[start_p + 3]] = "Debe"
  if len(cols_p) > start_p + 4:
    rename_p[cols_p[start_p + 4]] = "Haber"

  df_p_proc.rename(columns=rename_p, inplace=True)
  df_p_proc["Debe"] = (
      limpiar_monto(df_p_proc["Debe"]) if "Debe" in df_p_proc.columns else 0.0
  )
  df_p_proc["Haber"] = (
      limpiar_monto(df_p_proc["Haber"])
      if "Haber" in df_p_proc.columns
      else 0.0
  )
  if "Ref" in df_p_proc.columns:
    df_p_proc["Ref"] = (
        df_p_proc["Ref"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
  df_p_proc["Ref3"] = df_p_proc["Ref"].str[-3:]
  df_p_proc["orig_idx"] = df_p_proc.index

  # --- IDENTIFICAR DUPLICADOS EN PROFIT (Puntos 4 y 5) ---
  df_p_proc["Monto_Total_Duplicidad"] = df_p_proc["Debe"] + df_p_proc["Haber"]
  
  # 4. Duplicados exactos (Mismo número de referencia y monto)
  df_p_proc["Es_Duplicado_Exacto"] = df_p_proc.duplicated(
      subset=["Ref", "Monto_Total_Duplicidad"], keep=False
  )
  
  # 5. Duplicados que tengan los mismos últimos 3 dígitos de referencia y monto iguales
  df_p_proc["Es_Duplicado_Ref3"] = df_p_proc.duplicated(
      subset=["Ref3", "Monto_Total_Duplicidad"], keep=False
  )
  
  # Fusionar banderas para la vista general de duplicados que ya tenías
  df_p_proc["Es_Duplicado"] = df_p_proc["Es_Duplicado_Exacto"] | df_p_proc["Es_Duplicado_Ref3"]
  df_p["Es_Duplicado"] = df_p_proc["Es_Duplicado"]
  df_p_duplicados = df_p[df_p["Es_Duplicado"]].copy()

  # 6. Duplicados con misma referencia y montos diferentes (coinciden 3 números consecutivos del monto -> marcar rojo)
  def detectar_montos_similares(group):
    if len(group) > 1:
      montos = group["Monto_Total_Duplicidad"].tolist()
      # Validar similitud de al menos 3 dígitos consecutivos en montos diferentes
      for i in range(len(montos)):
        for j in range(i + 1, len(montos)):
          m1_str = f"{montos[i]:.2f}".replace(".", "")
          m2_str = f"{montos[j]:.2f}".replace(".", "")
          # Buscar subcadenas consecutivas de longitud 3
          coincide = any(m1_str[k:k+3] in m2_str for k in range(len(m1_str)-2))
          if coincide and montos[i] != montos[j]:
            group.loc[:, "Alerta_Rojo"] = True
    return group

  df_p_proc = df_p_proc.groupby("Ref", group_keys=False).apply(detectar_montos_similares)
  if "Alerta_Rojo" not in df_p_proc.columns:
    df_p_proc["Alerta_Rojo"] = False

  # --- CRUCE 1: INGRESOS CORRECTOS (Banco Crédito ↔ Profit Debe) ---
  b_cred = df_b_proc[df_b_proc["Credito"] > 0].copy()
  b_cred["Monto"] = b_cred["Credito"]
  p_debe = df_p_proc[df_p_proc["Debe"] > 0].copy()
  p_debe["Monto"] = p_debe["Debe"]

  cruce_ing_1 = pd.merge(
      b_cred, p_debe, on=["Ref", "Monto"], suffixes=("_B", "_P")
  )
  idx_b_ing1 = cruce_ing_1["orig_idx_B"]
  idx_p_ing1 = cruce_ing_1["orig_idx_P"]

  rest_b_ing = b_cred[
      (~b_cred["orig_idx"].isin(idx_b_ing1)) & (b_cred["Ref3"] != "")
  ]
  rest_p_ing = p_debe[
      (~p_debe["orig_idx"].isin(idx_p_ing1)) & (p_debe["Ref3"] != "")
  ]
  
  # 2. Cruce por últimos 3 dígitos y monto iguales
  cruce_ing_2 = pd.merge(
      rest_b_ing, rest_p_ing, on=["Ref3", "Monto"], suffixes=("_B", "_P")
  )
  idx_b_ing2 = cruce_ing_2["orig_idx_B"]
  idx_p_ing2 = cruce_ing_2["orig_idx_P"]

  # 3. Cruce por suma parcial (Profit múltiple suma exacto al Banco con misma Ref)
  # Identificamos pendientes de ingresos en banco y profit
  pend_b_ing_sum = rest_b_ing[~rest_b_ing["orig_idx"].isin(idx_b_ing2)]
  pend_p_ing_sum = rest_p_ing[~rest_p_ing["orig_idx"].isin(idx_p_ing2)]
  
  idx_b_ing3 = []
  idx_p_ing3 = []
  for _, row_b in pend_b_ing_sum.iterrows():
    ref_b = row_b["Ref"]
    monto_b = row_b["Monto"]
    match_p = pend_p_ing_sum[pend_p_ing_sum["Ref"] == ref_b]
    if not match_p.empty and match_p["Debe"].sum() == monto_b:
      idx_b_ing3.append(row_b["orig_idx"])
      idx_p_ing3.extend(match_p["orig_idx"].tolist())

  # --- CRUCE 2: EGRESOS CORRECTOS (Banco Débito ↔ Profit Haber) ---
  b_deb = df_b_proc[df_b_proc["Debito"] > 0].copy()
  b_deb["Monto"] = b_deb["Debito"]
  p_haber = df_p_proc[df_p_proc["Haber"] > 0].copy()
  p_haber["Monto"] = p_haber["Haber"]

  cruce_eg_1 = pd.merge(
      b_deb, p_haber, on=["Ref", "Monto"], suffixes=("_B", "_P")
  )
  idx_b_eg1 = cruce_eg_1["orig_idx_B"]
  idx_p_eg1 = cruce_eg_1["orig_idx_P"]

  rest_b_eg = b_deb[
      (~b_deb["orig_idx"].isin(idx_b_eg1)) & (b_deb["Ref3"] != "")
  ]
  rest_p_eg = p_haber[
      (~p_haber["orig_idx"].isin(idx_p_eg1)) & (p_haber["Ref3"] != "")
  ]
  cruce_eg_2 = pd.merge(
      rest_b_eg, rest_p_eg, on=["Ref3", "Monto"], suffixes=("_B", "_P")
  )
  idx_b_eg2 = cruce_eg_2["orig_idx_B"]
  idx_p_eg2 = cruce_eg_2["orig_idx_P"]

  # Cruce por suma parcial para egresos
  pend_b_eg_sum = rest_b_eg[~rest_b_eg["orig_idx"].isin(idx_b_eg2)]
  pend_p_eg_sum = rest_p_eg[~rest_p_eg["orig_idx"].isin(idx_p_eg2)]
  
  idx_b_eg3 = []
  idx_p_eg3 = []
  for _, row_b in pend_b_eg_sum.iterrows():
    ref_b = row_b["Ref"]
    monto_b = row_b["Monto"]
    match_p = pend_p_eg_sum[pend_p_eg_sum["Ref"] == ref_b]
    if not match_p.empty and match_p["Haber"].sum() == monto_b:
      idx_b_eg3.append(row_b["orig_idx"])
      idx_p_eg3.extend(match_p["orig_idx"].tolist())

  # Consolidar todos los índices conciliados
  todos_idx_b = pd.concat([
      idx_b_ing1, idx_b_ing2, pd.Series(idx_b_ing3), 
      idx_b_eg1, idx_b_eg2, pd.Series(idx_b_eg3)
  ]).dropna().unique()
  
  todos_idx_p = pd.concat([
      idx_p_ing1, idx_p_ing2, pd.Series(idx_p_ing3), 
      idx_p_eg1, idx_p_eg2, pd.Series(idx_p_eg3)
  ]).dropna().unique()

  # --- DETECCIÓN DE INVERSIONES DE COLUMNA ---
  p_haber_all = df_p_proc[df_p_proc["Haber"] > 0].copy()
  p_haber_all["Monto"] = p_haber_all["Haber"]
  inv_ing = pd.merge(
      b_cred[~b_cred["orig_idx"].isin(todos_idx_b)],
      p_haber_all[~p_haber_all["orig_idx"].isin(todos_idx_p)],
      on=["Ref", "Monto"],
      suffixes=("_B", "_P"),
  )

  p_debe_all = df_p_proc[df_p_proc["Debe"] > 0].copy()
  p_debe_all["Monto"] = p_debe_all["Debe"]
  inv_eg = pd.merge(
      b_deb[~b_deb["orig_idx"].isin(todos_idx_b)],
      p_debe_all[~p_debe_all["orig_idx"].isin(todos_idx_p)],
      on=["Ref", "Monto"],
      suffixes=("_B", "_P"),
  )

  df_inversiones = pd.concat([inv_ing, inv_eg], ignore_index=True)

  # Separar Conciliados y Pendientes
  df_b_conciliados = df_b.loc[df_b.index.isin(todos_idx_b)].reset_index(drop=True)
  df_p_conciliados = df_p.loc[df_p.index.isin(todos_idx_p)].reset_index(drop=True)

  df_b_pendientes = df_b.loc[~df_b.index.isin(todos_idx_b)].reset_index(drop=True)
  df_p_pendientes = df_p.loc[~df_p.index.isin(todos_idx_p)].reset_index(drop=True)

  cruce_final_display = pd.concat(
      [
          df_b_conciliados.add_suffix(" (Banco)"),
          df_p_conciliados.add_suffix(" (Profit)"),
      ],
      axis=1,
  )

  # --- PESTAÑAS DE VISUALIZACIÓN ---
  tab1, tab2, tab3, tab4 = st.tabs([
      "✅ Conciliados",
      "🔄 Inversiones (Debe/Haber)",
      "🏦 Pendientes Banco",
      "💻 Pendientes Profit",
      "⚠️ Duplicados/Errores",
  ])

  with tab1:
    st.dataframe(cruce_final_display, use_container_width=True)

  with tab2:
    if not df_inversiones.empty:
      st.warning(
          "⚠️ Se encontraron operaciones con columnas invertidas (ej. Ingresos"
          " registrados en el Haber o Egresos en el Debe):"
      )
      st.dataframe(df_inversiones, use_container_width=True)
    else:
      st.success(
          "No se detectaron inversiones de columnas (Debe/Haber) erróneas."
      )

  with tab3:
    st.dataframe(df_b_pendientes, use_container_width=True)

  with tab4:
    st.dataframe(df_p_pendientes, use_container_width=True)

  # --- SECCIÓN DE DUPLICADOS EN PROFIT (Con marcado en rojo visual para punto 6) ---
  if not df_p_duplicados.empty:
    st.subheader(
        "⚠️ Registros Duplicados / Alertas Detectados en Profit"
    )
    cols_dup_show = [
        c for c in df_p_duplicados.columns if c != "Monto_Total_Duplicidad"
    ]
    
    # Aplicar color rojo en la interfaz de Streamlit si cumple la regla 6
    def resaltar_rojo(row):
      idx = row.name
      if idx in df_p_proc.index and df_p_proc.loc[idx, "Alerta_Rojo"]:
        return ['background-color: #8b0000; color: white'] * len(row)
      return [''] * len(row)

    st.dataframe(
        df_p_duplicados[cols_dup_show].style.apply(resaltar_rojo, axis=1), 
        use_container_width=True
    )

  # --- NOMBRE DINÁMICO PARA EL ARCHIVO EXCEL ---
  nombre_archivo = f"Conciliacion {empresa} {banco} {frecuencia} {mes} {ano}.xlsx"

  # --- DESCARGA ---
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    cruce_final_display.to_excel(writer, index=False, sheet_name="Conciliados")
    if not df_inversiones.empty:
      df_inversiones.to_excel(writer, index=False, sheet_name="Inversiones_DebeHaber")
    df_b_pendientes.to_excel(
        writer, index=False, sheet_name="Pendientes_Banco"
    )
    df_p_pendientes.to_excel(
        writer, index=False, sheet_name="Pendientes_Profit"
    )
    if not df_p_duplicados.empty:
      df_p_duplicados[cols_dup_show].to_excel(
          writer, index=False, sheet_name="Duplicados_Profit"
      )

  st.download_button(
      "📥 Descargar Reporte Completo",
      data=output.getvalue(),
      file_name=nombre_archivo,
  )

else:
  st.info("Cargue ambos archivos para proceder con la conciliación.")

st.markdown(
    '<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación'
    " Bancaria — Creado por Lic. Olgleidys Hernández ✨</p></div>",
    unsafe_allow_html=True,
)
