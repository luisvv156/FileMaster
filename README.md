# FileMaster

FileMaster es una aplicación de escritorio local para organizar archivos con IA avanzada, monitoreo continuo y una interfaz oscura construida con `CustomTkinter`.

Su objetivo es tomar una carpeta de trabajo, analizar el contenido de los documentos, proponer carpetas temáticas, renombrar archivos de forma descriptiva, detectar duplicados y mantener un agente activo que siga organizando nuevos archivos en segundo plano.

## Tabla de contenidos

- [Visión general](#visión-general)
- [Funciones principales](#funciones-principales)
- [Tecnologías del proyecto](#tecnologías-del-proyecto)
- [Requisitos previos](#requisitos-previos)
- [Instalación en Linux](#instalación-en-linux)
- [Instalación en Windows](#instalación-en-windows)
- [Ejecución de la aplicación](#ejecución-de-la-aplicación)
- [Uso paso a paso](#uso-paso-a-paso)
- [Arquitectura del proyecto](#arquitectura-del-proyecto)
- [Persistencia y rutas de datos](#persistencia-y-rutas-de-datos)
- [Variables de entorno](#variables-de-entorno)
- [Pruebas](#pruebas)
- [Empaquetado para distribución](#empaquetado-para-distribución)
- [Mejoras implementadas](#mejoras-implementadas)
- [Categorías soportadas](#categorías-soportadas)

## Visión general

FileMaster es una aplicación de escritorio avanzada con estas capacidades:

- Interfaz gráfica completa para configuración, agrupación, monitoreo, resumen, duplicados y clasificación manual;
- Análisis inicial de una carpeta con documentos;
- Agrupación temática local usando **Sentence-BERT** (embeddings semánticos reales);
- Clasificación automática de archivos nuevos con **modo EXTREME** (alta precisión);
- Renombrado inteligente con categoría, keywords y fecha;
- Detección de duplicados exactos y similares;
- Historial persistente en SQLite;
- Monitoreo continuo de carpeta en segundo plano;
- **OCR completo** con Tesseract para imágenes y documentos escaneados;
- **Soporte para español** con spaCy;
- **Detección multi-categoría** para documentos con múltiples temas;
- 17 categorías predefinidas con 85+ keywords únicos.

## Funciones principales

- **Configuración inicial**: define la carpeta a monitorear, activa/desactiva renombrado y manejo de duplicados.
- **Análisis inicial**: la app lee documentos existentes y propone grupos temáticos antes de mover nada.
- **Confirmación de grupos**: el usuario puede editar los nombres de carpeta sugeridos por la IA.
- **Organización automática**: los archivos se mueven a carpetas destino y opcionalmente se renombran.
- **Monitoreo continuo**: el agente sigue observando la carpeta y procesa archivos nuevos.
- **Detección de duplicados**: separa archivos con mismo hash o contenido muy similar.
- **Clasificación manual**: los archivos ambiguos pasan a una vista donde el usuario decide su destino.
- **Historial y resumen**: cada acción queda registrada y la app presenta estadísticas del último ciclo.
- **Detección multi-categoría**: documentos que abarcan múltiples temas se clasifican en todas las categorías relevantes.

## Tecnologías del proyecto

### Runtime principal

- **Python 3.11+**: lenguaje principal de backend y GUI.
- **CustomTkinter**: framework visual para la interfaz de escritorio.
- **SQLite**: persistencia local del historial.
- **Dataclasses**: contratos internos para documentos, categorías, duplicados y resúmenes.

### Módulos internos de IA

- **Sentence-BERT (all-MiniLM-L6-v2)**: embeddings semánticos reales mediante `sentence-transformers`.
- **Similitud coseno**: usada para clasificar y agrupar documentos.
- **DBSCAN**: clustering semántico con `scikit-learn`.
- **spaCy español**: análisis morfológico para extracción de keywords.
- **TF-IDF**: weighting de keywords para mejor clasificación.
- **Modo EXTREME**: umbrales altos para máxima precisión (0.65 threshold).

### Herramientas del sistema

- **Tesseract OCR**: para extraer texto desde imágenes o documentos escaneados.
- **pdftotext**: mejora la extracción de texto en PDFs.
- **pdfplumber**, **python-docx**, **python-pptx**: lectores de formatos Office.

### Herramientas de desarrollo

- **unittest**: pruebas automatizadas.
- **PyInstaller**: empaquetado para distribución como app de escritorio.

## Requisitos previos

### Mínimos

- Python `3.11`, `3.12` o `3.13`
- `pip`
- `venv`
- `tkinter` disponible en el sistema

### Recomendados

- `tesseract` para OCR
- `pdftotext` para mejorar lectura de PDFs
- Modelo spaCy en español (`es_core_news_sm`)

### Dependencias Python actuales

`requirements.txt`

```txt
customtkinter>=5.2,<6
sentence-transformers>=3.0,<4
scikit-learn>=1.5,<2
```

## Mejoras implementadas

### v2.0 - IA Avanzada

#### Embeddings Semánticos
- **Sentence-BERT (all-MiniLM-L6-v2)**: embeddings de 384 dimensiones
- Modelo descargado automáticamente (~90MB)
- Funciona 100% offline tras primera descarga
- Caché en memoria para rendimiento

#### Modo EXTREME
- **Threshold de similitud: 0.65** (alta precisión)
- **Threshold de clustering: 0.45** (grupos específicos)
- **Clasificador requiere margen de 0.15** sobre segunda categoría
- Solo clasifica con confianza >= 0.50

#### Detección Multi-Categoría
- `get_multi_categories()` retorna todas las categorías detectadas
- scoring ponderado (keywords exactos valen 2x, hits valen 0.5x)
- Top 3 categorías por documento
- Logging de alternativas detectadas

#### Palabras Clave Extendidas
- **85+ keywords únicos** sin conflicto
- Códigos de curso (IA-301, BD-201, etc.)
- Full keywords (angular js, tcp ip, etc.) evitan falsos positivos

#### Categorías Soportadas (17)
1. Inteligencia Artificial
2. Base de Datos
3. Administración de Redes
4. Hacking Ético
5. Tecnologías de Virtualización
6. Tecnologías en la Nube
7. Taller de Investigación
8. Programación Lógica y Funcional
9. Desarrollo Web
10. Desarrollo Móvil
11. Desarrollo de Software
12. Ciberseguridad
13. Ciencia de Datos
14. Arquitectura de Computadoras
15. Sistemas Operativos
16. Matemáticas Discretas
17. Estadística

#### OCR Completo
- Tesseract v5.5.0 integrado
- Soporte para imágenes (PNG, JPG, TIFF)
- Extracción mejorada de PDFs

#### spaCy Español
- Modelo `es_core_news_sm` instalado
- Filtrado POS para keywords de calidad
- Análisis morfológico completo

## Instalación en Linux

### 1. Instalar Python y paquetes del sistema

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-tk
```

Opcionales:

```bash
sudo apt install -y poppler-utils tesseract-ocr
```

### 2. Crear el entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```bash
python main.py
```

### 4. Ejecutar pruebas

```bash
python -m unittest discover -s tests -v
```

## Instalación en Windows

### 1. Instalar Python 3.11+

Desde `python.org`, asegurarte de incluir **Add Python to PATH**.

### 2. Crear y activar entorno virtual

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```powershell
python main.py
```

### 4. Ejecutar pruebas

```powershell
python -m unittest discover -s tests -v
```

## Ejecución de la aplicación

Linux:

```bash
source venv/bin/activate
python main.py
```

Windows:

```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

## Uso paso a paso

1. Abre FileMaster.
2. En la pantalla inicial pulsa **Configurar mi carpeta**.
3. Selecciona la carpeta que quieres monitorear.
4. Define si deseas renombrado automático y manejo de duplicados.
5. Ejecuta el análisis inicial.
6. Revisa los grupos detectados por la IA.
7. Confirma o edita los nombres de carpeta sugeridos.
8. Deja que FileMaster organice los documentos.
9. Revisa el resumen del ciclo.
10. Si hay archivos ambiguos, clasifícalos manualmente.
11. Si hay duplicados, decide si restaurarlos o eliminarlos.
12. Mantén la app abierta para que el watcher siga observando la carpeta.

## Arquitectura del proyecto

### GUI

- `gui/app.py`: construye la ventana principal, carga las pantallas y conecta la UI con el controlador.
- `gui/theme.py`: centraliza colores, tamaños, tipografías y datos visuales.
- `gui/components/`: contiene widgets reutilizables.
- `gui/screens/`: contiene cada pantalla completa.

### Core

- `core/controller.py`: cerebro del sistema. Orchestras análisis, clasificación, duplicados, history y watcher.
- `core/text_extractor.py`: lectura de contenido textual (PDF, DOCX, PPTX, imágenes).
- `core/organizer.py`: aplica movimientos y renombrados.
- `core/duplicate_detector.py`: identifica duplicados exactos y similares.
- `core/history.py`: persistencia SQLite del historial.
- `core/watcher.py`: monitoreo continuo.

### IA local

- `ai/embeddings.py`: Sentence-BERT embeddings mediante `sentence-transformers`.
- `ai/clustering.py`: agrupación semántica con DBSCAN.
- `ai/classifier.py`: asignación de categoría para archivos nuevos.
- `ai/hint_classifier.py`: clasificación por keywords únicos y detección multi-categoría.
- `ai/keyword_extractor.py`: keywords TF-IDF con spaCy.
- `ai/renamer.py`: nombres sugeridos para archivos.
- `ai/text_utils.py`: normalización, tokenización y boost de portada.

### Punto de entrada

- `main.py`: inicializa logging y arrancas la GUI.

## Persistencia y rutas de datos

La app guarda datos del usuario en una carpeta de sistema.

Ubicaciones por sistema:

- Linux: `~/.local/share/FileMaster`
- macOS: `~/Library/Application Support/FileMaster`
- Windows: `%APPDATA%\FileMaster`

Se persisten:

- configuración del usuario;
- categorías confirmadas;
- estado runtime;
- historial SQLite;
- logs de aplicación.

## Variables de entorno

### `FILEMASTER_HOME`

Permite forzar una ruta personalizada para los datos persistentes.

```bash
export FILEMASTER_HOME=/ruta/personalizada
```

## Pruebas

La suite actual usa `unittest`.

Ejecutar todas las pruebas:

```bash
python -m unittest discover -s tests -v
```

Cobertura funcional:

- embeddings y similitud semántica;
- clustering DBSCAN;
- detección de duplicados;
- extracción de texto (PDF, DOCX, imágenes);
- organización de archivos;
- flujo principal del controlador;
- hint classifier multi-categoría.

## Categorías soportadas

| # | Categoría | Keywords principales |
|---|-----------|---------------------|
| 1 | Inteligencia Artificial | tensorflow, pytorch, machine learning, neural network, gpt |
| 2 | Base de Datos | mysql, postgresql, mongodb, oracle, sql, database |
| 3 | Administración de Redes | router, switch, tcp ip, vlan, dns, dhcp, cisco |
| 4 | Hacking Ético | pentest, metasploit, nmap, cve, vulnerability, owasp |
| 5 | Tecnologías de Virtualización | docker, kubernetes, vmware, virtualbox, hypervisor |
| 6 | Tecnologías en la Nube | aws, azure, gcp, cloud, lambda, serverless |
| 7 | Taller de Investigación | tesis, metodología, hipótesis, investigación |
| 8 | Programación Lógica y Funcional | prolog, haskell, lisp, lambda, functional |
| 9 | Desarrollo Web | angular, react, vue, html, css, javascript, nodejs |
| 10 | Desarrollo Móvil | android, ios, kotlin, flutter, swift, react native |
| 11 | Desarrollo de Software | scrum, agile, uml, testing, git, refactoring |
| 12 | Ciberseguridad | ciberseguridad, firewall, criptografía, oauth, seguridad |
| 13 | Ciencia de Datos | pandas, big data, hadoop, spark, tableau |
| 14 | Arquitectura de Computadoras | cpu, gpu, assembly, register, pipeline |
| 15 | Sistemas Operativos | kernel, linux, ubuntu, bash, shell, process |
| 16 | Matemáticas Discretas | grafo, bfs, dfs, dijkstra, boolean |
| 17 | Estadística | media, varianza, probabilidad, correlación |

---

**FileMaster v2.0** - IA Avanzada para organización inteligente de archivos.

```bash
# Ejecución rápida
python -m unittest discover -s tests -v
python main.py
```