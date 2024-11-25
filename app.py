import streamlit as st
import pandas as pd
from io import BytesIO

# Función para cargar el inventario desde Google Sheets
def load_inventory_file():
    # Enlace al archivo del inventario en Google Sheets
    inventario_url = "https://docs.google.com/spreadsheets/d/1DVcPPILcqR0sxBZZAOt50lQzoKhoLCEx/edit?usp=sharing&ouid=109532697276677589725&rtpof=true&sd=true"
    inventario_api_df = pd.read_excel(inventario_url, sheet_name="Hoja1")
    inventario_api_df.columns = inventario_api_df.columns.str.lower().str.strip()  # Asegurar nombres consistentes
    return inventario_api_df

# Función para procesar las alternativas basadas en los productos faltantes
def procesar_alternativas(faltantes_df, inventario_api_df):
    # Convertir los nombres de las columnas a minúsculas
    faltantes_df.columns = faltantes_df.columns.str.lower().str.strip()

    # Verificar si el archivo de faltantes contiene las columnas requeridas
    if not {'cur', 'codart'}.issubset(faltantes_df.columns):
        st.error("El archivo de faltantes debe contener las columnas: 'cur' y 'codart'")
        return pd.DataFrame()  # Devuelve un DataFrame vacío si faltan columnas

    # Filtrar el inventario solo por los artículos que están en el archivo de faltantes
    cur_faltantes = faltantes_df['cur'].unique()
    alternativas_inventario_df = inventario_api_df[inventario_api_df['cur'].isin(cur_faltantes)]

    # Verificar si las columnas necesarias existen en el inventario
    columnas_necesarias = ['codart', 'cur', 'nomart', 'cum', 'carta', 'opcion']
    for columna in columnas_necesarias:
        if columna not in alternativas_inventario_df.columns:
            st.error(f"La columna '{columna}' no se encuentra en el inventario. Verifica el archivo de origen.")
            st.stop()

    # Convertir la columna 'opcion' a enteros
    alternativas_inventario_df['opcion'] = alternativas_inventario_df['opcion'].fillna(0).astype(int)

    # Seleccionar las columnas requeridas
    alternativas_disponibles_df = alternativas_inventario_df[columnas_necesarias]

    # Combinar los faltantes con las alternativas disponibles
    alternativas_disponibles_df = pd.merge(
        faltantes_df[['cur', 'codart']],
        alternativas_disponibles_df,
        on=['cur', 'codart'],
        how='inner'
    )

    return alternativas_disponibles_df

# Función para generar un archivo Excel
def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alternativas')
    output.seek(0)
    return output

# Función para descargar la plantilla
def descargar_plantilla():
    plantilla_url = "https://docs.google.com/spreadsheets/d/1CRTYE0hbMlV8FiOeVDgDjGUm7x8E-XA8/export?format=xlsx"
    return plantilla_url

# Interfaz de Streamlit
st.markdown(
    """
    <h1 style="text-align: center; color: #FF5800; font-family: Arial, sans-serif;">
        RAMEDICAS S.A.S.
    </h1>
    <h3 style="text-align: center; font-family: Arial, sans-serif; color: #3A86FF;">
        Buscador de Alternativas por Código de Artículo
    </h3>
    <p style="text-align: center; font-family: Arial, sans-serif; color: #6B6B6B;">
        Esta herramienta te permite buscar y consultar los códigos alternativos de productos con las opciones deseadas de manera eficiente y rápida.
    </p>
    """,
    unsafe_allow_html=True
)

# Botón para descargar la plantilla
st.markdown(
    f"""
    <a href="{descargar_plantilla()}" download>
        <button style="background-color: #FF5800; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer;">
            Descargar plantilla de faltantes
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# Subir archivo de faltantes
uploaded_file = st.file_uploader("Sube un archivo con los productos faltantes (contiene 'cur' y 'codart')", type=["xlsx", "csv"])

if uploaded_file:
    # Leer el archivo subido
    if uploaded_file.name.endswith('xlsx'):
        faltantes_df = pd.read_excel(uploaded_file)
    else:
        faltantes_df = pd.read_csv(uploaded_file)

    # Cargar el inventario
    inventario_api_df = load_inventory_file()

    # Procesar alternativas
    alternativas_disponibles_df = procesar_alternativas(faltantes_df, inventario_api_df)

    # Mostrar las alternativas
    if not alternativas_disponibles_df.empty:
        st.write("Alternativas disponibles para los productos faltantes:")
        st.dataframe(alternativas_disponibles_df)

        # Permitir seleccionar opciones
        opciones_disponibles = alternativas_disponibles_df['opcion'].unique()
        opciones_seleccionadas = st.multiselect(
            "Selecciona las opciones que deseas ver (puedes elegir varias):",
            options=sorted(opciones_disponibles)
        )

        # Filtrar según las opciones seleccionadas
        if opciones_seleccionadas:
            alternativas_filtradas = alternativas_disponibles_df[alternativas_disponibles_df['opcion'].isin(opciones_seleccionadas)]
            st.write(f"Mostrando alternativas para las opciones seleccionadas: {', '.join(map(str, opciones_seleccionadas))}")
            st.dataframe(alternativas_filtradas)

            # Generar archivo Excel para descargar
            excel_file = generar_excel(alternativas_filtradas)
            st.download_button(
                label="Descargar archivo Excel con las opciones seleccionadas",
                data=excel_file,
                file_name="alternativas_filtradas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("No has seleccionado ninguna opción para mostrar.")
    else:
        st.write("No se encontraron alternativas para los códigos ingresados.")
