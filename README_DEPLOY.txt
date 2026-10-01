DASHBOARD C2 - 22 OPERARIAS + SMART SETUP

Archivos que deben estar en la raíz del repositorio GitHub:
- app.py
- requirements.txt
- 01_pedidos.xlsx
- 02_operarias.xlsx
- 03_operaciones_pedido.xlsx
- 04_tiempos.xlsx

Cambios principales de esta versión:
1. Se consideran 22 operarias.
2. Se mantienen las cuatro operaciones: Corte, Ensamblaje, Acabados y detalles, Planchado.
3. 01_pedidos.xlsx incluye una hoja Kits_SMED con el checklist de Smart Setup.
4. Solo los pedidos con Kit_Liberado = Sí pueden ingresar al motor C2.
5. El dashboard muestra kits listos, en preparación y bloqueados.
6. La vista principal muestra estado de operarias, operación prioritaria, recomendación, ranking Top 3 y cola pendiente.
7. Se corrigió la visualización del ranking: ahora usa componentes nativos de Streamlit para evitar que aparezca HTML como texto.
8. Incluye una pestaña Plan completo C2 y descarga de resultado_asignacion_C2.xlsx.

Para desplegar:
1. Reemplaza los archivos antiguos del repositorio por estos 6 archivos.
2. Haz Commit changes.
3. Streamlit Community Cloud redeployará la app automáticamente.
4. Si Streamlit conserva caché, usa Reboot app / Clear cache desde Manage app.

Nota metodológica:
Los 22 puestos corresponden al tamaño indicado para el caso. Los valores detallados de habilidades, tiempos y pedidos incluidos en estos Excel están estructurados para el prototipo y deben sustituirse por registros empresariales cuando estén disponibles para validación definitiva.
