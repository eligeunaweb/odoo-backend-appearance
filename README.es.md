# Apariencia del gestor para Odoo 16

Ajustes visuales para el cliente interno de Odoo.

**Validación:** instalación limpia y pruebas de servidor superadas en Docker aislado el 20 de noviembre de 2026. Quedan pendientes el navegador y la desinstalación.

## Instalar y comprobar

El nombre técnico es `euw_backend_appearance`. Si instalaste el módulo anterior `backend_appearance`, exporta los perfiles y temas que quieras conservar antes de desinstalarlo. Después instala el módulo con el nuevo nombre e importa los JSON. Odoo lo trata como una instalación independiente. Los resultados de pruebas de servidor publicados son anteriores al cambio de nombre.

En una base desechable de Odoo 16, añade el repositorio a la ruta de módulos del servidor, actualiza la lista de aplicaciones en modo desarrollador e instala **Apariencia del gestor**. Quita el filtro Aplicaciones si hace falta. Abre **Ajustes → Apariencia del gestor**.

El panel se divide en **Barra superior**, **Menú de aplicaciones**, **Espacio de trabajo** y **Temas**. Los cambios se ven al instante en la pestaña actual. Puedes abrir Contactos y volver al panel para aplicar o descartar el borrador. En el selector de ámbito, elige el perfil global o el de la empresa activa. La empresa hereda el perfil global hasta que se guarde un perfil propio. **Usar la apariencia global** elimina la personalización de esa empresa.

En Barra superior, cambia entre **Color liso**, **Patrón** y **Foto**. La foto tiene encuadre vertical. Puedes añadir un logotipo y un icono de pestaña. Las imágenes admiten PNG y JPEG de hasta 4 MB, y WebP cuando el servidor dispone del decodificador.

En **Temas** puedes guardar hasta 20 combinaciones con nombre y exportarlas o importarlas como JSON de versión 1. Al cargar o importar un tema, queda como borrador hasta que pulses **Aplicar cambios**.

En un laboratorio Windows ya instalado, ejecuta `./start-test.ps1 -Update` desde la carpeta del repositorio. El script repite las pruebas, prepara los recursos web y deja el servidor abierto en el puerto 18119.

El estilo **Personalizado** permite elegir el fondo del menú y el resaltado de la aplicación. El texto cambia automáticamente a negro o blanco según el fondo de cada estado.

Para instalar el módulo y ejecutar las pruebas automatizadas en Docker, abre PowerShell en esta carpeta:

```powershell
docker compose -p codex-odoo-appearance-16 -f compose.test.yml run --rm odoo odoo -d appearance_test -i euw_backend_appearance --test-enable --test-tags /euw_backend_appearance --stop-after-init
```

Este proyecto Compose tiene su propia base y su propia red. Para usar una instancia de pruebas existente, conserva sus parámetros de conexión y rutas de módulos:

```sh
odoo -d appearance_test -i euw_backend_appearance --test-enable --test-tags /euw_backend_appearance --stop-after-init
```

Para la aceptación manual, instala Contactos, Ventas e Inventario. Crea y edita un contacto, guarda un presupuesto con un producto y abre un listado de Inventario. Comprueba búsquedas, filtros, permisos de un usuario normal y el diseño en pantalla estrecha. Actualiza el módulo y desinstálalo desde Aplicaciones en la base de pruebas. Recarga el cliente y abre de nuevo los registros creados. Comprueba que se recupera el aspecto original y se elimina el perfil publicado.

Objetivo de compatibilidad: Odoo 16.0 Community. Instalación limpia y pruebas de servidor superadas en Docker aislado con Contactos, Ventas e Inventario. Quedan pendientes la validación visual completa y la desinstalación. Licencia: LGPL-3.
