# Apariencia del gestor para Odoo 19

Ajustes visuales para el cliente interno de Odoo.

## Instalar y comprobar

En una base desechable de Odoo 19, añade el repositorio a la ruta de módulos del servidor, actualiza la lista de aplicaciones en modo desarrollador e instala **Apariencia del gestor**. Quita el filtro Aplicaciones si hace falta. Abre **Ajustes → Apariencia del gestor**.

Elige un acento, un color para la barra y una densidad. Pulsa **Previsualizar** y abre un listado y un formulario reales de Contactos en esa misma pestaña. Vuelve a Ajustes para aplicar o descartar. Recarga una segunda sesión para comprobar la publicación. Usa **Restaurar valores originales** para recuperar el aspecto de Odoo. El perfil es global para toda la base.

En **Patrón de la barra superior**, elige liso, puntos, cuadrícula, diagonales u ondas. Para un fondo con patrón, ajusta la intensidad de 0 a 100 y pulsa **Previsualizar**. El patrón se puede combinar con el color estándar o con un color propio.

Para instalar el módulo y ejecutar las pruebas automatizadas en Docker, abre PowerShell en esta carpeta:

```powershell
docker compose -p codex-odoo-appearance -f compose.test.yml run --rm odoo odoo -d appearance_test -i backend_appearance --test-enable --test-tags /backend_appearance --stop-after-init
```

Este proyecto Compose tiene su propia base y su propia red. Para usar una instancia de pruebas existente, conserva sus parámetros de conexión y rutas de módulos:

```sh
odoo -d appearance_test -i backend_appearance --test-enable --test-tags /backend_appearance --stop-after-init
```

Para la aceptación manual, instala Contactos, Ventas e Inventario. Crea y edita un contacto, guarda un presupuesto con un producto y abre un listado de Inventario. Comprueba búsquedas, filtros, permisos de un usuario normal y el diseño en pantalla estrecha. Actualiza el módulo y desinstálalo desde Aplicaciones en la base de pruebas. Recarga el cliente y abre de nuevo los registros creados. Comprueba que se recupera el aspecto original y se elimina el perfil publicado.

Objetivo de compatibilidad: Odoo 19.0 Community. Pendiente de validación en ejecución y de convivencia con otros módulos. Licencia: LGPL-3.
