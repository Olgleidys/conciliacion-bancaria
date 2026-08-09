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
    4. El sistema procesará automáticamente los cruces (por referencia exacta y por los últimos 3 dígitos) y detectará duplicados en Profit.
    5. Visualice los resultados por pestañas y descargue el reporte limpio en Excel con el nombre personalizado.
    """)

# --- UI DE CONFIGURACIÓN Y CARGA ---
c1, c2 = st.columns(2)
empresa = c1.selectbox(
    "🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"]
)
banco = c2.selectbox(
    "🏦 Seleccione el banco:",
    ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"],
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
ano = p3.selectbox("📅 Año:", ["2026", "2027", "2025"])

b1, b2 = st.columns(2)
banco_file = b1.file_uploader(
    f"📥 Estado de Cuenta {banco} (.csv)", type=["csv"]
)
profit_file = b2.file_uploader("📥 Reporte de Profit Plus (.csv)", type=["csv"])


def limpiar_monto(serie):
  return pd.to_numeric(
      serie.astype(str)
      .str.replace(".", "", regex=False)
      .str.replace(",", ".", regex=False)
      .str.strip(),
      errors="coerce",
  ).fillna(0)


if banco_file and profit_file:
  df_b = pd.read_csv(banco_file, sep=None, engine="python", encoding="latin-1")
  df_p = pd.read_csv(profit_file, sep=None, engine="python", encoding="latin-1")

  # Copias para procesamiento interno
  df_b_proc = df_b.copy()
  df_p_proc = df_p.copy()

  for df in [df_b_proc, df_p_proc]:
    cols = list(df.columns)
    if "Referencia" in df.columns:
      df.rename(columns={"Referencia": "Ref"}, inplace=True)
    cols = list(df.columns)
    df.rename(
        columns={cols[0]: "Fecha", cols[1]: "Ref", cols[3]: "Monto"},
        inplace=True,
    )
    df["Monto"] = limpiar_monto(df["Monto"])
    # Limpieza estricta de referencias (elimina decimales .0 y espacios)
    df["Ref"] = (
        df["Ref"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

  # --- IDENTIFICAR DUPLICADOS EN PROFIT ---
  df_p_proc["Es_Duplicado"] = df_p_proc.duplicated(
      subset=["Ref", "Monto"], keep=False
  )
  df_p["Es_Duplicado"] = df_p_proc["Es_Duplicado"]
  df_p_duplicados = df_p[df_p["Es_Duplicado"]].copy()

  # Guardar índices originales para mapear después
  df_b_proc["orig_idx"] = df_b_proc.index
  df_p_proc["orig_idx"] = df_p_proc.index

  # --- LÓGICA DE CRUCE DOBLE (100% + 3 DÍGITOS) ---
  cruce_1 = pd.merge(
      df_b_proc, df_p_proc, on=["Ref", "Monto"], suffixes=("_B_proc", "_P_proc")
  )
  idx_b_1 = cruce_1["orig_idx_B_proc"]
  idx_p_1 = cruce_1["orig_idx_P_proc"]

  # Generar Ref3 solo con valores válidos
  df_b_proc["Ref3"] = df_b_proc["Ref"].str[-3:]
  df_p_proc["Ref3"] = df_p_proc["Ref"].str[-3:]

  rest_b = df_b_proc[
      (~df_b_proc["orig_idx"].isin(idx_b_1)) & (df_b_proc["Ref3"] != "")
  ]
  rest_p = df_p_proc[
      (~df_p_proc["orig_idx"].isin(idx_p_1)) & (df_p_proc["Ref3"] != "")
  ]

  cruce_2 = pd.merge(
      rest_b, rest_p, on=["Ref3", "Monto"], suffixes=("_B_proc", "_P_proc")
  )
  idx_b_2 = cruce_2["orig_idx_B_proc"]
  idx_p_2 = cruce_2["orig_idx_P_proc"]

  todos_idx_b = pd.concat([idx_b_1, idx_b_2])
  todos_idx_p = pd.concat([idx_p_1, idx_p_2])

  # Separar Conciliados y Pendientes
  df_b_conciliados = df_b.loc[todos_idx_b].reset_index(drop=True)
  df_p_conciliados = df_p.loc[todos_idx_p].reset_index(drop=True)

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
  tab1, tab2, tab3 = st.tabs(
      ["✅ Movimientos Conciliados", "🏦 Pendientes Banco", "💻 Pendientes Profit"]
  )

  with tab1:
    st.dataframe(cruce_final_display, use_container_width=True)

  with tab2:
    st.dataframe(df_b_pendientes, use_container_width=True)

  with tab3:
    st.dataframe(df_p_pendientes, use_container_width=True)

  # --- SECCIÓN DE DUPLICADOS EN PROFIT ---
  if not df_p_duplicados.empty:
    st.subheader(
        "⚠️ Registros Duplicados Detectados en Profit (Mismo Nro. de Referencia"
        " y Monto)"
    )
    cols_dup_show = [c for c in df_p_duplicados.columns if c != "Es_Duplicado"]
    st.dataframe(df_p_duplicados[cols_dup_show], use_container_width=True)

  # --- NOMBRE DINÁMICO PARA EL ARCHIVO EXCEL ---
  nombre_archivo = f"Conciliacion_{empresa}_{banco}_{frecuencia}_{mes}_{ano}.xlsx"

  # --- DESCARGA ---
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    cruce_final_display.to_excel(writer, index=False, sheet_name="Conciliados")
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
