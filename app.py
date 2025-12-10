import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Presupuestador Malacara", page_icon="❄️")

# --- BASE DE DATOS DE PRECIOS ---
PRECIOS_ALQUILER = {
    "Esquís Gama Bronce": {
        "Equipo Completo": [21.00, 38.50, 49.00, 58.00, 67.50],
        "Equipo Completo + Casco": [27.50, 47.50, 62.00, 73.00, 83.50],
        "Esquís + Bastones": [18.50, 34.00, 46.00, 55.50, 63.50],
        "Botas Esquí": [9.00, 15.50, 21.00, 26.00, 28.00]
    },
    "Esquís Gama Plata": {
        "Equipo Completo": [26.00, 46.50, 66.00, 83.50, 99.50],
        "Equipo Completo + Casco": [32.00, 55.50, 78.50, 98.50, 114.50],
        "Esquís + Bastones": [23.50, 44.00, 63.50, 81.00, 97.00],
        "Botas Esquí": [13.00, 24.00, 34.50, 42.50, 49.00]
    },
    "Esquís Gama Oro": {
        "Equipo Completo": [35.50, 65.00, 92.00, 120.00, 138.00],
        "Equipo Completo + Casco": [42.00, 75.50, 106.00, 136.00, 155.50],
        "Esquís + Bastones": [31.50, 53.00, 72.00, 90.50, 107.50],
        "Botas Esquí": [14.50, 26.00, 36.00, 44.00, 50.50]
    },
    "Esquís de Travesía": {
        "Equipo Completo": [35.50, 65.00, 92.00, 120.00, 138.00],
        "Equipo Completo + Casco": [42.00, 75.50, 106.00, 136.00, 155.50],
        "Esquís + Bastones": [31.50, 53.00, 72.00, 90.50, 107.50],
        "Botas Travesía": [14.50, 26.00, 36.00, 44.00, 50.50]
    },
    "Esquís Infantil (<= 13 Años)": {
        "Equipo Completo": [17.00, 30.50, 38.50, 50.00, 54.50],
        "Equipo Completo + Casco": [23.50, 40.00, 51.50, 65.00, 71.50],
        "Esquís + Bastones": [14.50, 24.00, 34.00, 40.00, 45.00],
        "Botas Esquí": [7.50, 11.50, 14.50, 17.00, 19.50]
    },
    "Esquís Infantil Oro (<= 13 Años)": {
        "Equipo Completo": [23.50, 42.50, 54.00, 69.00, 76.00],
        "Equipo Completo + Casco": [29.00, 51.50, 66.00, 83.50, 92.00],
        "Esquís + Bastones": [22.00, 41.00, 52.00, 67.50, 74.50],
        "Botas Esquí": [10.00, 16.00, 22.00, 26.50, 30.50]
    },
    "Snowboard Progresión": {
        "Tabla + Botas": [27.50, 49.00, 68.00, 84.50, 98.00],
        "Tabla + Botas + Casco": [34.00, 58.50, 82.00, 100.00, 115.50],
        "Tabla Sola": [20.00, 36.00, 52.00, 66.00, 79.50],
        "Botas Snowboard": [10.50, 18.50, 26.00, 32.00, 38.50]
    },
    "Snowboard Experto": {
        "Tabla + Botas": [32.00, 58.50, 75.50, 93.00, 100.00],
        "Tabla + Botas + Casco": [37.00, 66.50, 86.00, 106.00, 114.00],
        "Tabla Sola": [27.50, 48.00, 66.50, 82.00, 87.50],
        "Botas Snowboard": [11.50, 19.50, 26.50, 33.00, 39.50]
    },
    "Snowboard Niño": {
        "Tabla + Botas": [22.00, 37.00, 51.50, 65.00, 74.50],
        "Tabla + Botas + Casco": [28.00, 46.00, 65.00, 80.00, 93.00],
        "Tabla Sola": [18.00, 32.00, 45.00, 57.00, 71.50],
        "Botas Snowboard": [7.50, 11.50, 14.50, 17.00, 19.50]
    }
}

NIVELES_ESQUI = [
    "NIVEL A - Nunca he esquiado",
    "NIVEL A+ - Nociones básicas de cuña",
    "NIVEL B - Giros en cuña, empiezo paralelo",
    "NIVEL C - Pistas azules y rojas en paralelo",
    "NIVEL D - Paralelo conducido perfeccionado"
]

EDADES_ALUMNOS = ["5-8 años", "9-12 años", "Adulto (>13 años)"]

# --- FUNCIONES AUXILIARES ---
def calcular_precio_clases(tipo, num_personas, num_dias_horas):
    if num_personas == 0: return 0, "", "", 0
    
    if tipo == "Colectiva (3h/día)":
        precio_unitario = 55
        total = precio_unitario * num_personas * num_dias_horas
        descripcion = f"Cursillo Colectivo ({num_dias_horas} días)"
        detalle = f"{num_dias_horas} días x {num_personas} pers"
        return total, descripcion, detalle, precio_unitario
    else: # Particular
        precio_hora = 50 + (max(0, num_personas - 1) * 5)
        total = precio_hora * num_dias_horas
        descripcion = f"Clase Particular ({num_dias_horas} horas totales)"
        detalle = f"{num_dias_horas}h totales x {num_personas} pers"
        return total, descripcion, detalle, precio_hora

def calcular_precio_alquiler(gama, equipo, dias):
    if dias < 1: return 0
    if dias > 5: dias = 5
    try:
        precio = PRECIOS_ALQUILER[gama][equipo][dias-1]
        return precio
    except:
        return 0

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        # Logo: Se muestra si existe el archivo 'logo.png' en el mismo directorio
        if os.path.exists("logo.png"):
            # Ajusta las coordenadas (x, y, w) según tu logo. 
            self.image('logo.png', 10, 8, 40)
            self.ln(20) # Salto de línea después del logo
        else:
            self.set_font('Arial', 'B', 24)
            self.set_text_color(220, 50, 50) 
            self.cell(0, 10, 'Presupuesto', 0, 1, 'C')
            self.set_text_color(50, 50, 100)
            self.cell(0, 10, 'Malacara Esquí - Snowboard', 0, 1, 'C')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Malacara Esquí y Snowboard - www.malacaraesqui.es', 0, 0, 'C')

# --- INTERFAZ STREAMLIT ---
st.title("⛷️ Presupuestador Malacara Pro")

# --- GENERAR ID UNICO ---
# Usamos fecha y hora para simular correlativo sin base de datos
id_presupuesto = "MAL-" + datetime.now().strftime("%Y%m%d-%H%M")

# 1. DATOS DEL CLIENTE
with st.container():
    st.markdown("### 1. Detalles del Cliente")
    col1, col2 = st.columns(2)
    cliente_nombre = col1.text_input("Nombre del Titular", "Iván Fernández")
    cliente_fechas = col2.text_input("Fechas del Viaje", "22/12 - 24/12")
    cliente_telefono = col1.text_input("Teléfono")
    cliente_email = col2.text_input("Email")
    fecha_solicitud = datetime.now().strftime("%d/%m/%Y")
    st.caption(f"ID Presupuesto: {id_presupuesto}")

# 2. CLASES
st.divider()
st.markdown("### 2. Clases de Esquí / Snowboard")

# Variables de estado para alumnos
if 'alumnos' not in st.session_state:
    st.session_state['alumnos'] = []

# Configuración General Clases
col_conf1, col_conf2, col_conf3 = st.columns(3)
estacion = col_conf1.selectbox("Estación", ["Astún", "Candanchú"])
tipo_clase = col_conf2.selectbox("Tipo de Clase", ["Ninguna", "Colectiva (3h/día)", "Particular"])

duracion_clase = 0
lbl_duracion = "-"

if tipo_clase == "Colectiva (3h/día)":
    duracion_clase = col_conf3.number_input("Días de Clase", 1, 5, 3)
    lbl_duracion = "días"
elif tipo_clase == "Particular":
    duracion_clase = col_conf3.number_input("Total Horas Contratadas", 1, 20, 2)
    lbl_duracion = "horas"

# Añadir Alumnos
if tipo_clase != "Ninguna":
    st.markdown("#### Añadir Alumnos a la Clase")
    with st.expander("📝 Formulario Nuevo Alumno", expanded=True):
        c_al1, c_al2 = st.columns(2)
        nuevo_nombre = c_al1.text_input("Nombre Alumno")
        nuevo_edad = c_al2.selectbox("Tramo de Edad", EDADES_ALUMNOS)
        
        c_al3, c_al4 = st.columns(2)
        nuevo_mod = c_al3.radio("Modalidad", ["Esquí", "Snowboard"], horizontal=True)
        nuevo_nivel = c_al4.selectbox("Nivel", NIVELES_ESQUI)
        
        if st.button("➕ Añadir Alumno"):
            if nuevo_nombre:
                st.session_state['alumnos'].append({
                    "nombre": nuevo_nombre,
                    "edad": nuevo_edad,
                    "nivel": nuevo_nivel,
                    "modalidad": nuevo_mod
                })
            else:
                st.warning("Por favor escribe un nombre.")

    # Listado de Alumnos Añadidos
    if len(st.session_state['alumnos']) > 0:
        st.info(f"Alumnos inscritos: {len(st.session_state['alumnos'])}")
        df_alumnos = pd.DataFrame(st.session_state['alumnos'])
        st.table(df_alumnos)
        
        if st.button("🗑️ Borrar lista de alumnos"):
            st.session_state['alumnos'] = []
            st.rerun()
    else:
        st.warning("No hay alumnos añadidos aún.")

# Calcular Precio Clases
precio_clases = 0
desc_clases = ""
detalle_clases = ""
unitario_clases = 0
num_alumnos_real = len(st.session_state['alumnos'])

# Si el usuario no añade alumnos pero quiere presupuesto rápido, permitimos cálculo manual (opcional)
# Pero aquí priorizamos la lista. Si la lista está vacía, precio 0.
if tipo_clase != "Ninguna" and num_alumnos_real > 0:
    precio_clases, desc_clases, detalle_clases, unitario_clases = calcular_precio_clases(tipo_clase, num_alumnos_real, duracion_clase)
    st.success(f"💰 Subtotal Clases ({num_alumnos_real} alumnos): {precio_clases}€")


# 3. ALQUILER DE MATERIAL
st.divider()
st.markdown("### 3. Alquiler de Material")

if 'alquileres' not in st.session_state:
    st.session_state['alquileres'] = []

with st.expander("Añadir Equipo de Alquiler"):
    c1, c2, c3, c4 = st.columns(4)
    cat_select = c1.selectbox("Gama", list(PRECIOS_ALQUILER.keys()))
    equip_options = list(PRECIOS_ALQUILER[cat_select].keys())
    equip_select = c2.selectbox("Equipo", equip_options)
    dias_alq = c3.slider("Días Alquiler", 1, 5, 3)
    cant_equip = c4.number_input("Cantidad", 1, 10, 1)
    
    if st.button("Añadir Equipo"):
        precio_unit = calcular_precio_alquiler(cat_select, equip_select, dias_alq)
        subtotal_linea = precio_unit * cant_equip
        st.session_state['alquileres'].append({
            "gama": cat_select,
            "tipo": equip_select,
            "dias": dias_alq,
            "cantidad": cant_equip,
            "precio_unit": precio_unit,
            "subtotal": subtotal_linea
        })

total_alquiler = 0
if len(st.session_state['alquileres']) > 0:
    df_alq = pd.DataFrame(st.session_state['alquileres'])
    st.dataframe(df_alq[["gama", "tipo", "dias", "cantidad", "subtotal"]], use_container_width=True)
    total_alquiler = df_alq["subtotal"].sum()
    if st.button("Borrar Alquileres"):
        st.session_state['alquileres'] = []
        st.rerun()

st.write(f"**Subtotal Alquiler: {total_alquiler}€**")

# 4. DESCUENTOS Y TOTALES
st.divider()
st.markdown("### 4. Resumen Final")

subtotal_general = precio_clases + total_alquiler

col_d1, col_d2 = st.columns(2)
aplicar_descuento = col_d1.checkbox("¿Aplicar Descuento?")
tipo_desc = col_d2.radio("Tipo", ["Porcentaje (%)", "Cantidad Fija (€)"], disabled=not aplicar_descuento, horizontal=True)
valor_desc = col_d1.number_input("Valor", min_value=0.0, value=0.0, disabled=not aplicar_descuento)
concepto_desc = col_d2.text_input("Concepto", "Descuento Especial", disabled=not aplicar_descuento)

descuento_total = 0
if aplicar_descuento:
    if tipo_desc == "Porcentaje (%)":
        descuento_total = subtotal_general * (valor_desc / 100)
    else:
        descuento_total = valor_desc

total_final = subtotal_general - descuento_total

st.metric(label="TOTAL A PAGAR", value=f"{total_final:.2f}€", delta=f"-{descuento_total:.2f}€" if descuento_total > 0 else None)

# 5. GENERAR PDF
def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    blue_header = (230, 240, 255)
    
    # ID y Fecha
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Fecha: {fecha_solicitud} | Ref: {id_presupuesto}", 0, 1, 'R')
    pdf.ln(5)
    
    # Texto intro
    pdf.multi_cell(0, 5, "Gracias por contactar con Malacara Esquí y Snowboard. A continuación, encontrará su presupuesto detallado.")
    pdf.ln(5)
    
    # BLOQUE CLIENTE
    pdf.set_fill_color(*blue_header)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Detalles del Cliente", 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "Nombre:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_nombre, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "Fechas:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_fechas, 0, 1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "Teléfono:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_telefono, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 6, "Email:", 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 6, cliente_email, 0, 1)
    pdf.ln(5)
    
    # BLOQUE CLASES
    if tipo_clase != "Ninguna" and num_alumnos_real > 0:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, f"Clases: {tipo_clase} en {estacion}", 0, 1, 'L', fill=True)
        
        # Tabla Alumnos
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(50, 8, "Alumno", 1, 0, 'C')
        pdf.cell(30, 8, "Edad", 1, 0, 'C')
        pdf.cell(30, 8, "Modalidad", 1, 0, 'C')
        pdf.cell(80, 8, "Nivel", 1, 1, 'C') # Ancho restante
        
        pdf.set_text_color(0)
        pdf.set_font("Arial", '', 8)
        for al in st.session_state['alumnos']:
            pdf.cell(50, 8, al['nombre'], 1, 0)
            pdf.cell(30, 8, al['edad'], 1, 0, 'C')
            pdf.cell(30, 8, al['modalidad'], 1, 0, 'C')
            # Nivel recortado si es muy largo
            nivel_corto = (al['nivel'][:40] + '..') if len(al['nivel']) > 40 else al['nivel']
            pdf.cell(80, 8, nivel_corto, 1, 1)
        
        # Resumen precio clases
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(140, 8, f"Total Clases ({desc_clases}):", 0, 0, 'R')
        pdf.cell(50, 8, f"{precio_clases} eur", 0, 1, 'R')
        pdf.ln(5)

    # BLOQUE ALQUILER
    if len(st.session_state['alquileres']) > 0:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0)
        pdf.cell(0, 8, "Presupuesto de Alquiler", 0, 1, 'L', fill=True)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(70, 8, "Equipo", 1, 0, 'C')
        pdf.cell(30, 8, "Duración", 1, 0, 'C')
        pdf.cell(30, 8, "Precio Unit.", 1, 0, 'C')
        pdf.cell(30, 8, "Cantidad", 1, 0, 'C')
        pdf.cell(30, 8, "Subtotal", 1, 1, 'C')
        
        pdf.set_text_color(0)
        pdf.set_font("Arial", '', 8)
        
        for item in st.session_state['alquileres']:
            desc_item = f"{item['gama']} - {item['tipo']}"
            pdf.cell(70, 8, desc_item[:40], 1, 0)
            pdf.cell(30, 8, f"{item['dias']} dias", 1, 0, 'C')
            pdf.cell(30, 8, f"{item['precio_unit']} eur", 1, 0, 'C')
            pdf.cell(30, 8, str(item['cantidad']), 1, 0, 'C')
            pdf.cell(30, 8, f"{item['subtotal']} eur", 1, 1, 'C')
        
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(160, 8, "Total Alquiler:", 0, 0, 'R')
        pdf.cell(30, 8, f"{total_alquiler:.2f} eur", 0, 1, 'R')
        pdf.ln(5)

    # RESUMEN FINAL
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "", 0, 1, fill=True) # Barra gris fondo
    pdf.set_y(pdf.get_y() - 10) # Volver arriba para escribir encima
    
    texto_total = f"TOTAL PRESUPUESTO: {total_final:.2f} eur"
    pdf.cell(0, 10, texto_total, 0, 1, 'R')
    
    if descuento_total > 0:
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 6, f"Incluye descuento de {descuento_total:.2f} eur ({concepto_desc})", 0, 1, 'R')
        pdf.set_text_color(0)
    
    pdf.ln(5)
    
    # CONDICIONES
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0)
    pdf.cell(0, 8, "Condiciones", 0, 1, 'L')
    pdf.set_font("Arial", '', 9)
    condiciones = (
        "- Este presupuesto tiene una validez de 15 días.\n"
        "- Para confirmar la reserva, se requiere un depósito del 30%.\n"
        "- Cancelaciones con menos de 48 horas conllevan cargo.\n"
        "- Los precios están sujetos a cambios según la temporada."
    )
    pdf.multi_cell(0, 5, condiciones)
    
    return pdf.output(dest='S').encode('latin-1')

st.divider()
if st.button("📄 CREAR PDF FINAL", type="primary"):
    pdf_bytes = create_pdf()
    nombre_archivo = f"Presupuesto_{id_presupuesto}_{cliente_nombre.split()[0]}.pdf"
    
    st.download_button(
        label="⬇️ Descargar PDF",
        data=pdf_bytes,
        file_name=nombre_archivo,
        mime='application/pdf'
    )
