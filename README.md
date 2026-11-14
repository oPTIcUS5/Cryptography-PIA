# VotoSeguro — PIA de Criptografía

VotoSeguro es un **prototipo académico de votación electrónica** que simula una elección municipal. Permite iniciar sesión, emitir un voto cifrado, cerrar la elección y consultar los resultados.

## Contenido del proyecto

- **`src/votoseguro/`**: código principal del sistema (criptografía, base de datos y conteo de votos).
- **`app.py`**: aplicación web desarrollada con Flask.
- **`launcher.py`**: archivo para iniciar el servidor local.
- **`manage.py`**: comandos para preparar, cerrar y contar los votos de la elección.
- **`templates/`**: páginas HTML del sistema.
- **`static/`**: estilos CSS y código JavaScript.
- **`tests/`**: pruebas del funcionamiento del programa.
- **`scripts/`**: prueba de compatibilidad entre JavaScript y Python.
- **`docs/`**: reporte y diagramas del proyecto en LaTeX.
- **`evidencias/`**: indicaciones para las capturas de funcionamiento.
- **`data/`**: datos y claves generados localmente (carpeta privada, no se comparte).
- **`requirements.txt`**: dependencias necesarias de Python.
- **`MANUAL_DE_ARCHIVOS.md`**: explicación más detallada de los archivos.

## Ejecución básica

Después de instalar las dependencias con `pip install -r requirements.txt`, ejecutar desde la carpeta principal:

```bash
python manage.py init     # Preparar la elección (solo la primera vez)
python launcher.py        # Iniciar la aplicación
```

Abrir **http://127.0.0.1:5000/login** en el navegador. Para cerrar la votación y obtener los resultados, ejecutar en otra terminal:

```bash
python manage.py close
python manage.py tally
python manage.py verify
```

> **Nota:** Este programa es una demostración escolar con cuentas y candidaturas ficticias; no está diseñado para elecciones reales.
