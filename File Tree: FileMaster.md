# File Tree: FileMaster

**Actualizado:** 27/03/2026  
**Ruta raiz:** `/home/leo156/Documentos/FileMaster`

Este archivo describe la estructura actual del proyecto y el rol de cada carpeta o archivo principal.

## Arbol del proyecto documentado

```text
FileMaster/
├── ai/                             # Modulos de inteligencia artificial local y heuristicas semanticas
│   ├── __init__.py                 # Marca el paquete de IA
│   ├── classifier.py               # Clasifica documentos nuevos contra categorias ya confirmadas
│   ├── clustering.py               # Agrupa embeddings con una version simplificada de DBSCAN
│   ├── embeddings.py               # Genera embeddings locales por hashing estable de tokens
│   ├── keyword_extractor.py        # Extrae keywords frecuentes para grupos y categorias
│   ├── renamer.py                  # Sugiere nombres descriptivos para archivos organizados
│   └── text_utils.py               # Normalizacion, tokenizacion y utilidades de texto
│
├── assets/                         # Recursos visuales usados por la GUI y el empaquetado
│   ├── icons/                      # Carpeta reservada para iconos adicionales
│   │   └── .gitkeep                # Mantiene la carpeta en control de versiones
│   └── logo.png                    # Logo principal de FileMaster para ventana y branding
│
├── config/                         # Configuracion global, rutas persistentes y logging
│   ├── logging_config.py           # Configura logs rotativos de la aplicacion
│   ├── settings.py                 # Carga, guarda y resuelve rutas/configuracion del usuario
│   └── user_config.json            # Configuracion local editable generada para desarrollo
│
├── core/                           # Backend principal del flujo de organizacion
│   ├── __init__.py                 # Marca el paquete central
│   ├── controller.py               # Orquesta analisis, clasificacion, watcher, resumen y GUI
│   ├── duplicate_detector.py       # Detecta duplicados exactos y similares
│   ├── file_manager.py             # Operaciones seguras de mover, crear y eliminar archivos
│   ├── history.py                  # Persistencia del historial en SQLite
│   ├── models.py                   # Dataclasses compartidas entre backend e interfaz
│   ├── ocr_handler.py              # OCR opcional con Tesseract si esta instalado
│   ├── organizer.py                # Aplica movimientos y renombrados sobre archivos
│   ├── text_extractor.py           # Extrae texto de TXT, PDF, DOCX, PPTX e imagenes
│   └── watcher.py                  # Observa cambios en la carpeta configurada en segundo plano
│
├── data/                           # Datos locales persistentes del proyecto durante desarrollo
│   ├── categories.json             # Categorias confirmadas por el usuario
│   ├── embeddings_cache.pkl        # Cache opcional de embeddings para acelerar analisis
│   ├── file_history.db             # Base SQLite con historial de acciones
│   └── runtime_state.json          # Estado runtime de grupos, resumen y agente
│
├── gui/                            # Interfaz de escritorio construida con CustomTkinter
│   ├── __init__.py                 # Marca el paquete de GUI
│   ├── app.py                      # Ventana principal y navegacion entre pantallas
│   ├── theme.py                    # Paleta, tipografias, medidas y datos demo visuales
│   ├── components/                 # Componentes reutilizables de la interfaz
│   │   ├── common.py               # Botones base, iconos, titlebar y dialogos
│   │   ├── file_card.py            # Tarjeta para archivos recientes
│   │   ├── folder_chip.py          # Chip visual para carpetas y contadores
│   │   ├── keyword_tag.py          # Etiquetas de palabras clave
│   │   ├── sidebar.py              # Sidebar principal de navegacion
│   │   ├── stat_card.py            # Tarjetas de estadisticas del dashboard
│   │   ├── status_badge.py         # Badge de estado del agente
│   │   └── toggle_switch.py        # Switch visual para opciones de configuracion
│   └── screens/                    # Pantallas completas de la aplicacion
│       ├── config_screen.py        # Configuracion inicial de carpeta y opciones
│       ├── duplicates_screen.py    # Revision y acciones sobre duplicados
│       ├── groups_screen.py        # Confirmacion de grupos detectados por la IA
│       ├── main_panel.py           # Panel principal del agente y la actividad
│       ├── manual_classify_screen.py # Clasificacion manual de archivos ambiguos
│       ├── summary_screen.py       # Resumen del ultimo ciclo de organizacion
│       └── welcome_screen.py       # Pantalla de bienvenida/hero inicial
│
├── tests/                          # Suite de pruebas automatizadas
│   ├── fixtures/                   # Archivos o carpetas reservados para fixtures
│   │   └── .gitkeep                # Mantiene la carpeta en el repositorio
│   ├── test_clustering.py          # Prueba agrupacion semantica
│   ├── test_controller_flow.py     # Smoke test del flujo completo del controlador
│   ├── test_duplicate_detector.py  # Prueba deteccion de duplicados
│   ├── test_embeddings.py          # Prueba embeddings y similitud
│   ├── test_organizer.py           # Prueba movimientos y renombrados
│   └── test_text_extractor.py      # Prueba extraccion de texto
│
├── .gitignore                      # Ignora archivos temporales, build, venv y caches
├── README.md                       # Documentacion principal del proyecto
├── filemaster.spec                 # Configuracion de PyInstaller para empaquetar la app
├── main.py                         # Punto de entrada de la aplicacion
├── requirements-dev.txt            # Dependencias de desarrollo y empaquetado
└── requirements.txt                # Dependencias de ejecucion
```

## Flujo de alto nivel

1. `main.py` inicia logging y levanta la GUI principal.
2. `gui/app.py` crea la ventana, construye pantallas y conecta la UI con `core/controller.py`.
3. `core/controller.py` usa:
   - `core/text_extractor.py` para leer texto,
   - `ai/embeddings.py` para vectorizar,
   - `ai/clustering.py` para proponer grupos,
   - `ai/classifier.py` para clasificar nuevos archivos,
   - `core/duplicate_detector.py` para duplicados,
   - `core/organizer.py` y `core/file_manager.py` para mover y renombrar,
   - `core/history.py` para registrar acciones.
4. `core/watcher.py` mantiene el monitoreo en segundo plano.

## Archivos generados en tiempo de ejecucion

- `data/categories.json`: categorias confirmadas por el usuario.
- `data/runtime_state.json`: ultimo estado visible del sistema.
- `data/file_history.db`: historial persistente de acciones.
- `data/embeddings_cache.pkl`: cache local de embeddings.

## Notas

- La IA actual es **local y ligera**; todavia no usa Sentence-BERT real ni DBSCAN de `scikit-learn`.
- La GUI esta pensada para escritorio fijo tipo app Electron.
- El empaquetado actual recomendado es con **PyInstaller**.
