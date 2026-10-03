# Tablero EDA · Actividad Colaborativa I

Tablero interactivo en **Python (Streamlit + Plotly)** para el análisis exploratorio de
`Datos.xlsx` (300 estudiantes, 10 variables). Lo construimos para el módulo *La información en
el sistema educativo* de la Maestría en Educación y Transformación Digital.

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. Copie la base del curso en `data/Datos.xlsx`.
2. Ejecute:

```bash
streamlit run app.py
```

El tablero abre en `http://localhost:8501`. Si `data/Datos.xlsx` no existe, puede subir el
archivo desde el panel lateral.

> **Para desarrollar sin la base oficial:** `python scripts/generate_sample_data.py` crea
> `data/datos_sinteticos.xlsx` con la misma estructura y datos inventados. No lo use para el
> informe.

## Personalización (antes de publicar)

Todo lo editable está en `src/eda_dashboard/config.py`:

| Qué | Dónde |
|---|---|
| Título, nombre del equipo, integrantes, nivel, fecha | `TeamInfo` |
| Umbral de alerta de asistencia (75 %) y nota aprobatoria (6,0) | `ATTENDANCE_ALERT`, `PASSING_GRADE` |
| Colores (azul principal, naranja para el grupo en riesgo) | `Palette` |

La redacción de las cinco decisiones (hallazgo, decisión, población, indicador y riesgo) está
en `src/eda_dashboard/findings.py`. Las cifras se calculan solas a partir de los datos, pero
el texto de cada decisión es un **borrador**: ajústenlo a la realidad de sus instituciones.

## Publicación con URL pública (Streamlit Community Cloud, gratuito)

1. Suba esta carpeta a un repositorio de GitHub, con `data/Datos.xlsx` incluido.
2. Entre a <https://share.streamlit.io>, inicie sesión con GitHub y elija **Create app**.
3. Seleccione el repositorio y la rama, y como *Main file path* escriba `app.py`.
4. Presione **Deploy**. Obtendrá una URL del tipo `https://<nombre>.streamlit.app`.
5. Abra la URL en una ventana de incógnito y desde otro computador para verificar que carga
   sin iniciar sesión. Esa es la URL que va en la portada del informe.

## Cómo cubre los requisitos de la guía

| Requisito (sección 6.1 y rúbrica) | Dónde está en el tablero |
|---|---|
| Título y texto de contexto | Encabezado: autoría, propósito y público |
| Vista de KPI | Sección 1: cinco tarjetas que mezclan total, promedio y proporciones |
| Al menos cuatro gráficos de tipos variados | Barras horizontales, histogramas, barras apiladas al 100 %, cajas, barras agrupadas, dispersión y ranking |
| Análisis univariado, bivariado y de tres variables | Secciones 2, 3–4 y 5 (tipo de escuela × segunda variable × promedio) |
| Interactividad que aporta análisis | Filtros laterales (ubicación, tipo, género, grados) que actualizan todos los gráficos **y sus textos**, más un selector de la variable de cruce en la sección 5 |
| Texto interpretativo bajo cada gráfico | Se calcula con los datos filtrados: compara, dimensiona (tamaño del efecto, puntos porcentuales) y plantea la implicación |
| De 3 a 5 hallazgos y decisiones | Sección 8: cinco fichas con los cinco componentes |
| Paleta coherente | Azul para los datos y naranja solo para el grupo en desventaja |

## Estructura del código

```
app.py                       Punto de entrada: carga, filtros y orden de secciones
src/eda_dashboard/
├── config.py                Esquema, etiquetas, paleta, umbrales y datos del equipo
├── data_loader.py           Lectura del Excel, validación y normalización
├── analysis.py              Cálculos puros (KPI, cruces, brechas, d de Cohen, correlación)
├── narrative.py             Textos interpretativos generados a partir de los datos
├── findings.py              Hallazgos → decisiones (ficha de 5 componentes)
├── charts.py                Constructores de gráficos Plotly con un estilo común
├── formatting.py            Formato numérico colombiano (7,09 · 68 %)
└── ui/
    ├── styles.py            CSS del tablero
    ├── components.py        Encabezado, tarjetas KPI, recuadros de lectura y fichas
    ├── sidebar.py           Carga de archivo y filtros
    └── sections.py          Una función por sección; la tupla SECTIONS define el orden
scripts/generate_sample_data.py   Base sintética para desarrollo
tests/                       Pruebas de carga, análisis e interfaz
```

**Principios:** cada capa tiene una sola responsabilidad (datos → análisis → narrativa →
gráficos → interfaz). El análisis no depende de Streamlit, así que se puede probar o
reutilizar en un notebook. La configuración está centralizada y el texto dinámico se escapa
antes de mostrarse.

### Validación de la base

El cargador acepta variantes comunes: `Género`/`Genero`, `Si`/`sí`/`1`, `Publica`, asistencia
en escala 0–1 y números con coma decimal. Si faltan columnas o aparecen categorías
desconocidas, el tablero se detiene con un mensaje claro. Si descarta filas incompletas o
fuera de rango, lo informa en el panel lateral.

## Pruebas y estilo

```bash
pip install -r requirements-dev.txt
pytest          # 32 pruebas; las de interfaz requieren data/Datos.xlsx
ruff check .
```
