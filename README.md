# CryptoSuite — PIA de Criptografía

**Estado:** Fase 1 — estructura y definición de problemas.  
**Entrega:** 14 de noviembre de 2026, 23:59.  
**Propósito:** problemario con programas que solucionan situaciones de seguridad usando algoritmos criptográficos existentes y justificando su selección.

## 1. ¿Qué estamos construyendo?

CryptoSuite es un proyecto académico de Python con **cuatro casos independientes** y un reporte técnico en **LaTeX (Overleaf)**. No pretende ser un producto de seguridad listo para producción.

| Caso | Problema real | Técnicas previstas | Resultado esperado |
|---|---|---|---|
| 1. Archivos | Proteger un documento confidencial | scrypt + AES-256-GCM | Archivo cifrado y descifrado; alteraciones rechazadas |
| 2. Comunicación | Intercambiar mensajes entre Alice y Bob | X25519, Ed25519, HKDF-SHA256, AES-256-GCM | Mensaje recuperado, participantes autenticados y manipulaciones detectadas |
| 3. Firmas | Verificar autoría e integridad de un archivo | Ed25519 y SHA-256 (para comparación de integridad) | Firma válida o inválida según el contenido y la clave |
| 4. Contraseñas | Guardar verificadores de contraseñas sin almacenar texto plano | Argon2id | Verificación correcta y rechazo de contraseñas erróneas |

> **Precisión:** el caso 2 se diseñará como una simulación local de dos participantes; no se afirmará que equivale a una aplicación de mensajería de producción. Las claves públicas de identidad deben validarse previamente para evitar ataques de intermediario.

## 2. ¿Qué pide el profesor?

- **Protocolos (25 %):** detallar negociación de claves, autenticación y transferencia de datos.
- **Métodos (20 %):** seleccionar cifrado, hashes y firmas, justificando las elecciones.
- **Diagramas (20 %):** diagramas congruentes con los protocolos y el código.
- **Tecnologías (15 %):** justificar Python, librerías y herramientas.
- **Seguridad y escalabilidad (10 %):** riesgos, límites y mitigaciones.
- **Documentación (10 %):** reporte ordenado, evidencias y procedimientos reproducibles.

## 3. Organización de carpetas

```text
CryptoSuite-PIA/
├── README.md                  # Esta guía; objetivo, comandos, pendientes
├── requirements.txt           # Dependencias del programa
├── .gitignore                 # Archivos locales/secretos a excluir de Git
├── main.py                    # Punto de entrada del menú
├── src/
│   └── cryptosuite/
│       ├── __init__.py
│       ├── cli.py             # Menú y selección de casos
│       ├── file_crypto.py     # Caso 1: cifrar/descifrar archivos
│       ├── secure_channel.py  # Caso 2: protocolo Alice/Bob
│       ├── signatures.py      # Caso 3: firmas y verificación
│       └── passwords.py       # Caso 4: verificación de contraseñas
├── tests/
│   └── test_cli.py           # Pruebas iniciales del menú
├── docs/
│   ├── reporte.tex           # Archivo principal para Overleaf
│   ├── secciones/            # Contenido del PIA por rúbrica
│   └── diagramas/            # Diagramas TikZ del protocolo
├── ejemplos/                 # Archivos sintéticos para ejecutar demos
└── evidencias/               # Capturas de pruebas (sin secretos)
```

## 4. Preparar y ejecutar desde una terminal

En macOS, abre Terminal en la carpeta `CryptoSuite-PIA`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

**Por ahora** el menú únicamente informa qué módulos están planeados. Todavía no cifra datos: implementaremos cada módulo en las siguientes fases.

Para comprobar el estado sin abrir el menú:

```bash
python main.py --estado
```

Para ejecutar las primeras pruebas (incluidas en la biblioteca estándar de Python):

```bash
python -m unittest discover -s tests -v
```

Para cerrar el entorno virtual, escribe `deactivate`.

## 5. Abrir el documento en Overleaf

Crea un proyecto de Overleaf y sube el contenido de `docs/`, manteniendo las subcarpetas. El archivo principal es **`reporte.tex`** y el compilador es **pdfLaTeX**.

En `docs/secciones/` se llenarán las siguientes partes: introducción, problemario, protocolos, justificación de algoritmos, diagramas, seguridad, pruebas y conclusiones. Es importante actualizar el documento **después de comprobar el comportamiento del código**, para evitar contradicciones.

## 6. Nuestra ruta de trabajo

- [x] Definir el alcance y los cuatro casos.
- [x] Crear las carpetas y el README.
- [x] Preparar el menú inicial y una primera prueba automatizada.
- [x] Iniciar el reporte LaTeX con problema y objetivos.
- [ ] Definir en detalle los formatos y mensajes de cada protocolo.
- [ ] Implementar el cifrado de archivos (caso 1).
- [ ] Implementar el intercambio seguro simulado (caso 2).
- [ ] Implementar firmas digitales (caso 3).
- [ ] Implementar hashes de contraseñas (caso 4).
- [ ] Crear y ejecutar pruebas positivas, negativas y de alteración.
- [ ] Dibujar flujos de protocolo completos en TikZ.
- [ ] Recopilar capturas reales, tabla de resultados y métricas.
- [ ] Finalizar análisis de seguridad, conclusiones y PDF.
- [ ] Empaquetar ZIP del software + PDF para Teams.

## 7. Reglas para no perder el orden

1. **Nunca** programar nuestros propios AES, X25519, Ed25519 o Argon2id; utilizaremos bibliotecas criptográficas mantenidas.
2. No subir contraseñas, claves privadas, semillas, archivos confidenciales ni el directorio `.venv` a GitHub.
3. No reutilizar un nonce con la misma clave en AES-GCM.
4. Registrar por cada problema: objetivo, entradas, salidas, algoritmo, protocolo, pruebas, resultado y capturas.
5. No afirmar que una función está terminada hasta que tenga pruebas y evidencia de ejecución.
6. En el canal seguro, documentar la autenticación de las identidades y la gestión de claves efímeras.

## 8. ¿Qué entregaremos?

- **PDF:** reporte final compilado desde `docs/reporte.tex` en Overleaf.
- **ZIP:** código, dependencias, pruebas, ejemplos no sensibles y este README.
- **Evidencias:** capturas de ejecución y resultados reproducibles, sin secretos.

**Siguiente paso:** especificar formalmente el *caso 1* (entradas/salidas, formato de archivo cifrado, manejo de errores y pruebas) y después implementarlo en `src/cryptosuite/file_crypto.py`.
