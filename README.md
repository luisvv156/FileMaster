# FileMaster

FileMaster es una aplicacion de escritorio local para organizar archivos con ayuda de IA ligera, monitoreo continuo y una interfaz oscura construida con `CustomTkinter`.

Su objetivo es tomar una carpeta de trabajo, analizar el contenido de los documentos, proponer carpetas tematicas, renombrar archivos de forma descriptiva, detectar duplicados y mantener un agente activo que siga organizando nuevos archivos en segundo plano.

## Tabla de contenidos

- [Vision general](#vision-general)
- [Funciones principales](#funciones-principales)
- [Tecnologias del proyecto](#tecnologias-del-proyecto)
- [Requisitos previos](#requisitos-previos)
- [Instalacion en Linux](#instalacion-en-linux)
- [Instalacion en Windows](#instalacion-en-windows)
- [Ejecucion de la aplicacion](#ejecucion-de-la-aplicacion)
- [Uso paso a paso](#uso-paso-a-paso)
- [Arquitectura del proyecto](#arquitectura-del-proyecto)
- [Persistencia y rutas de datos](#persistencia-y-rutas-de-datos)
- [Variables de entorno](#variables-de-entorno)
- [Pruebas](#pruebas)
- [Empaquetado para distribucion](#empaquetado-para-distribucion)
- [Limitaciones actuales](#limitaciones-actuales)
- [Roadmap recomendado](#roadmap-recomendado)

## Vision general

FileMaster hoy funciona como un MVP de escritorio con estas capacidades:

- interfaz grafica completa para configuracion, agrupacion, monitoreo, resumen, duplicados y clasificacion manual;
- analisis inicial de una carpeta con documentos;
- agrupacion tematica local usando embeddings ligeros y similitud coseno;
- clasificacion automatica de archivos nuevos;
- renombrado inteligente con categoria, keywords y fecha;
- deteccion de duplicados exactos y similares;
- historial persistente en SQLite;
- monitoreo continuo de carpeta en segundo plano;
- OCR opcional cuando `tesseract` esta disponible en el sistema.

## Funciones principales

- **Configuracion inicial**: define la carpeta a monitorear, activa/desactiva renombrado y manejo de duplicados.
- **Analisis inicial**: la app lee documentos existentes y propone grupos tematicos antes de mover nada.
- **Confirmacion de grupos**: el usuario puede editar los nombres de carpeta sugeridos por la IA.
- **Organizacion automatica**: los archivos se mueven a carpetas destino y opcionalmente se renombran.
- **Monitoreo continuo**: el agente sigue observando la carpeta y procesa archivos nuevos.
- **Deteccion de duplicados**: separa archivos con mismo hash o contenido muy similar.
- **Clasificacion manual**: los archivos ambiguos pasan a una vista donde el usuario decide su destino.
- **Historial y resumen**: cada accion queda registrada y la app presenta estadisticas del ultimo ciclo.

## Tecnologias del proyecto

### Runtime principal

- **Python 3.11+**: lenguaje principal de backend y GUI.
- **CustomTkinter**: framework visual para la interfaz de escritorio.
- **SQLite**: persistencia local del historial.
- **Dataclasses**: contratos internos para documentos, categorias, duplicados y resumenes.

### Modulos internos de IA

- **Embeddings locales por hashing**: implementados en `ai/embeddings.py`.
- **Similitud coseno**: usada para clasificar y agrupar documentos.
- **DBSCAN simplificado**: implementado en `ai/clustering.py`.
- **Heuristicas semanticas y keywords**: para nombres de grupo y renombrado.

### Herramientas del sistema opcionales

- **Tesseract OCR**: para extraer texto desde imagenes o documentos escaneados.
- **pdftotext**: mejora la extraccion de texto en PDFs.

### Herramientas de desarrollo

- **unittest**: pruebas automatizadas.
- **PyInstaller**: empaquetado para distribucion como app de escritorio.

## Requisitos previos

### Minimos

- Python `3.11`, `3.12` o `3.13`
- `pip`
- `venv`
- `tkinter` disponible en el sistema

### Recomendados

- `tesseract` para OCR
- `pdftotext` para mejorar lectura de PDFs

### Dependencias Python actuales

`requirements.txt`

```txt
customtkinter>=5.2,<6
```

`requirements-dev.txt`

```txt
-r requirements.txt
pyinstaller>=6,<7
```

## Instalacion en Linux

Estas instrucciones funcionan muy bien en Ubuntu o Debian. Al final agrego notas para Fedora y Arch.

### 1. Instalar Python y paquetes del sistema

En Ubuntu o Debian:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-tk
```

Opcionales recomendados:

```bash
sudo apt install -y poppler-utils tesseract-ocr
```

### 2. Entrar al proyecto

```bash
cd /ruta/a/FileMaster
```

Ejemplo:

```bash
cd /home/leo156/Documentos/FileMaster
```

### 3. Crear el entorno virtual

```bash
python3 -m venv venv
```

### 4. Activar el entorno virtual

```bash
source venv/bin/activate
```

### 5. Instalar dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Ejecutar la aplicacion

```bash
python main.py
```

### 7. Ejecutar pruebas

```bash
python -m unittest discover -s tests -v
```

### Notas para otras distros Linux

Fedora:

```bash
sudo dnf install -y python3 python3-pip python3-tkinter
sudo dnf install -y poppler-utils tesseract
```

Arch Linux:

```bash
sudo pacman -S python python-pip tk poppler tesseract
```

## Instalacion en Windows

Las instrucciones siguientes estan pensadas para Windows 10 u 11 usando PowerShell.

### 1. Instalar Python

Descarga e instala Python 3.11+ desde `python.org`.

Durante la instalacion:

- activa la opcion **Add Python to PATH**
- instala `pip`
- permite la instalacion para el usuario actual o para todos los usuarios segun tu preferencia

### 2. Abrir PowerShell y entrar al proyecto

```powershell
cd C:\ruta\al\proyecto\FileMaster
```

### 3. Crear el entorno virtual

```powershell
py -m venv venv
```

### 4. Activar el entorno virtual

```powershell
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion, puedes permitirla para la sesion actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 5. Instalar dependencias Python

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Ejecutar la aplicacion

```powershell
python main.py
```

### 7. Ejecutar pruebas

```powershell
python -m unittest discover -s tests -v
```

### Herramientas opcionales recomendadas en Windows

#### Tesseract OCR

Instala Tesseract si quieres OCR para imagenes y documentos escaneados.

Pasos generales:

1. Descarga el instalador de Tesseract para Windows.
2. Instala en una ruta simple, por ejemplo:
   `C:\Program Files\Tesseract-OCR`
3. Agrega esa carpeta al `PATH`.
4. Reinicia PowerShell y verifica:

```powershell
tesseract --version
```

#### pdftotext / Poppler

Para mejorar PDFs con texto:

1. Instala Poppler para Windows.
2. Agrega la carpeta `bin` al `PATH`.
3. Verifica:

```powershell
pdftotext -v
```

## Ejecucion de la aplicacion

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
4. Define si deseas renombrado automatico y manejo de duplicados.
5. Ejecuta el analisis inicial.
6. Revisa los grupos detectados por la IA.
7. Confirma o edita los nombres de carpeta sugeridos.
8. Deja que FileMaster organice los documentos.
9. Revisa el resumen del ciclo.
10. Si hay archivos ambiguos, clasificalos manualmente.
11. Si hay duplicados, decide si restaurarlos o eliminarlos.
12. Manten la app abierta para que el watcher siga observando la carpeta.

## Arquitectura del proyecto

### GUI

- `gui/app.py`: construye la ventana principal, carga las pantallas y conecta la UI con el controlador.
- `gui/theme.py`: centraliza colores, tamaños, tipografias y datos visuales.
- `gui/components/`: contiene widgets reutilizables.
- `gui/screens/`: contiene cada pantalla completa.

### Core

- `core/controller.py`: cerebro del sistema. Orquesta analisis, clasificacion, duplicates, history y watcher.
- `core/text_extractor.py`: lectura de contenido textual.
- `core/organizer.py`: aplica movimientos y renombrados.
- `core/duplicate_detector.py`: identifica duplicados exactos y similares.
- `core/history.py`: persistencia SQLite del historial.
- `core/watcher.py`: monitoreo continuo.

### IA local

- `ai/embeddings.py`: embeddings ligeros sin red externa.
- `ai/clustering.py`: agrupacion semantica.
- `ai/classifier.py`: asignacion de categoria para archivos nuevos.
- `ai/keyword_extractor.py`: keywords de soporte.
- `ai/renamer.py`: nombres sugeridos para archivos.
- `ai/text_utils.py`: normalizacion y tokenizacion.

### Punto de entrada

- `main.py`: inicializa logging y arranca la GUI.

### Arbol detallado

Para una vista ruta por ruta con descripcion de cada archivo:

- revisa [# File Tree: FileMaster.md](./%23%20File%20Tree%3A%20FileMaster.md)

## Persistencia y rutas de datos

La app guarda datos del usuario en una carpeta de sistema para que funcione mejor al distribuirse como ejecutable.

Ubicaciones por sistema:

- Linux: `~/.local/share/FileMaster`
- macOS: `~/Library/Application Support/FileMaster`
- Windows: `%APPDATA%\FileMaster`

Se persisten:

- configuracion del usuario;
- categorias confirmadas;
- estado runtime;
- historial SQLite;
- logs de aplicacion.

En desarrollo tambien veras datos locales dentro de `data/`.

## Variables de entorno

### `FILEMASTER_HOME`

Permite forzar una ruta personalizada para los datos persistentes.

Linux:

```bash
export FILEMASTER_HOME=/ruta/personalizada
```

Windows PowerShell:

```powershell
$env:FILEMASTER_HOME = "C:\Ruta\Personalizada"
```

## Pruebas

La suite actual usa `unittest`.

Ejecutar todas las pruebas:

```bash
python -m unittest discover -s tests -v
```

Cobertura funcional incluida actualmente:

- embeddings y similitud;
- clustering;
- duplicados;
- extraccion de texto;
- organizacion de archivos;
- flujo principal del controlador.

## Empaquetado para distribucion

### Instalar dependencias de build

```bash
pip install -r requirements-dev.txt
```

### Construir ejecutable

```bash
pyinstaller filemaster.spec
```

El resultado se genera en:

```text
dist/FileMaster/
```

### Notas de empaquetado

- la app ya usa icono de ventana desde `assets/logo.png`;
- si agregas `assets/logo.ico`, PyInstaller lo usa como icono del ejecutable;
- la configuracion de build esta en `filemaster.spec`.

## Limitaciones actuales

- la IA actual es local y ligera; no usa todavia Sentence-BERT real;
- el clustering es una implementacion simplificada inspirada en DBSCAN;
- la calidad del OCR depende de tener `tesseract` instalado;
- la calidad de lectura de PDF mejora si `pdftotext` esta disponible;
- la ventana esta pensada para layout fijo de escritorio, no redimensionable;
- el proyecto funciona como app local, no como servicio multiusuario.

## Roadmap recomendado

- integrar Sentence-BERT real para embeddings semanticos;
- reemplazar el clustering simplificado por `scikit-learn` DBSCAN;
- agregar caché inteligente de embeddings persistentes;
- ampliar tests con fixtures reales de PDF, DOCX y OCR;
- generar instaladores listos para Windows y Linux;
- añadir exportacion/importacion de configuracion;
- agregar historial visual dedicado y filtros avanzados.

## Comandos rapidos

### Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Windows

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

---

Si quieres, el siguiente paso puede ser uno de estos:

- preparar un instalador para Windows;
- conectar una IA semantica real;
- documentar cada modulo interno con docstrings mas detallados;
- generar una guia de despliegue final para entregar el proyecto. 
