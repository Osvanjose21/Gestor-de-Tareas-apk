import flet as ft
import requests
import time

# URL de tu base de datos en Firebase Realtime Database
FIREBASE_URL = "https://gestor-de-tareas-33ca6-default-rtdb.firebaseio.com"[cite: 3]


def main(page: ft.Page):
    page.title = "Gestor de Pedidos y Diligencias"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "adaptive"
    page.padding = 20

    # Estado para detectar tareas nuevas y guardar el rol elegido
    estado = {"cantidad_tareas": 0, "rol": None}

    # --- FUNCIONES DE BASE DE DATOS ---
    def obtener_tareas():
        try:
            res = requests.get(f"{FIREBASE_URL}/tareas.json", timeout=5)
            return res.json() or {}
        except Exception:
            return {}

    def obtener_clientes():
        try:
            res = requests.get(f"{FIREBASE_URL}/clientes.json", timeout=5)
            return res.json() or {}
        except Exception:
            return {}

    def mostrar_alerta(mensaje, color=ft.Colors.GREEN_700):
        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    # --- PANTALLA DE SELECCIÓN DE ROL ---
    def seleccionar_rol(rol_elegido):
        estado["rol"] = rol_elegido
        page.clean()
        if rol_elegido == "Jefe":
            construir_vista_jefe()
        else:
            construir_vista_empleado()

    # --- VISTA DEL JEFE (ASIGNAR TAREAS Y VER PROGRESO) ---
    def construir_vista_jefe():
        txt_tipo = ft.Dropdown(
            label="Tipo de asignación",
            options=[
                ft.dropdown.Option("Pedido Nuevo"),
                ft.dropdown.Option("Diligencia"),
            ],
            value="Pedido Nuevo"
        )
        txt_nombre = ft.TextField(label="Nombre y Apellido del Cliente")
        txt_telefono = ft.TextField(label="Número de Teléfono", keyboard_type=ft.KeyboardType.PHONE)
        txt_direccion = ft.TextField(label="Dirección exacta", multiline=True)
        txt_detalle = ft.TextField(label="Detalles del pedido o diligencia", multiline=True)
        lista_seguimiento = ft.Column(spacing=10)

        def enviar_tarea(e):
            if not txt_nombre.value or not txt_direccion.value:
                mostrar_alerta("Completa al menos el nombre y la dirección", ft.Colors.RED_600)
                return

            nueva_tarea = {
                "tipo": txt_tipo.value,
                "nombre": txt_nombre.value.strip(),
                "telefono": txt_telefono.value.strip(),
                "direccion": txt_direccion.value.strip(),
                "detalle": txt_detalle.value.strip(),
                "estado": "Pendiente",
                "observacion": "",
                "fecha": time.strftime("%d/%m/%Y %I:%M %p")
            }
            requests.post(f"{FIREBASE_URL}/tareas.json", json=nueva_tarea)

            # Limpiar campos
            txt_nombre.value = ""
            txt_telefono.value = ""
            txt_direccion.value = ""
            txt_detalle.value = ""
            mostrar_alerta("¡Tarea enviada!")
            cargar_seguimiento()

        def cargar_seguimiento(e=None):
            lista_seguimiento.controls.clear()
            tareas = obtener_tareas()
            for _, t in reversed(list(tareas.items())):
                es_completada = t.get("estado") == "Finalizada"
                color_borde = ft.Colors.GREEN_400 if es_completada else ft.Colors.ORANGE_400

                tarjeta = ft.Container(
                    padding=12,
                    border=ft.border.all(2, color_borde),
                    border_radius=10,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{t.get('tipo')} - {t.get('estado')}", weight="bold", color=color_borde),
                            ft.Text(t.get("fecha", ""), size=11, color="grey")
                        ], alignment="spaceBetween"),
                        ft.Text(f"Cliente: {t.get('nombre')} | Tel: {t.get('telefono')}"),
                        ft.Text(f"Dirección: {t.get('direccion')}"),
                        ft.Text(f"Detalle: {t.get('detalle')}", italic=True),
                        ft.Text(f"Observación: {t.get('observacion') or 'Ninguna'}", weight="bold", color=ft.Colors.BLUE_800)
                    ])
                )
                lista_seguimiento.controls.append(tarjeta)
            page.update()

        page.add(
            ft.Row([
                ft.Text("Panel del Jefe", size=22, weight="bold"),
                ft.IconButton(ft.Icons.REFRESH, on_click=cargar_seguimiento, tooltip="Actualizar")
            ], alignment="spaceBetween"),
            txt_tipo,
            txt_nombre,
            txt_telefono,
            txt_direccion,
            txt_detalle,
            ft.ElevatedButton("Asignar Tarea Ahora", icon=ft.Icons.SEND, on_click=enviar_tarea, width=400),
            ft.Divider(),
            ft.Text("Estado de Tareas Enviadas:", size=18, weight="bold"),
            lista_seguimiento
        )
        cargar_seguimiento()

    # --- VISTA DEL EMPLEADO (RECIBIR, NOTIFICAR, FINALIZAR Y GUARDAR CLIENTES) ---
    def construir_vista_empleado():
        lista_tareas = ft.Column(spacing=12)
        lista_clientes = ft.Column(spacing=8)

        # Campos para guardar cliente manualmente
        cli_nombre = ft.TextField(label="Nombre y Apellido")
        cli_tel = ft.TextField(label="Teléfono", keyboard_type=ft.KeyboardType.PHONE)
        cli_dir = ft.TextField(label="Dirección")
        cli_nota = ft.TextField(label="Dato extra / Referencia")

        def guardar_cliente_en_nube(nombre, tel, direccion, nota=""):
            datos = {
                "nombre": nombre,
                "telefono": tel,
                "direccion": direccion,
                "nota": nota
            }
            requests.post(f"{FIREBASE_URL}/clientes.json", json=datos)
            mostrar_alerta(f"Cliente '{nombre}' guardado en el directorio")
            cargar_clientes()

        def guardar_cliente_manual(e):
            if not cli_nombre.value:
                mostrar_alerta("Escribe el nombre del cliente", ft.Colors.RED_600)
                return
            guardar_cliente_en_nube(cli_nombre.value, cli_tel.value, cli_dir.value, cli_nota.value)
            cli_nombre.value = cli_tel.value = cli_dir.value = cli_nota.value = ""
            page.update()

        def cargar_clientes():
            lista_clientes.controls.clear()
            clientes = obtener_clientes()
            for _, c in reversed(list(clientes.items())):
                lista_clientes.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON),
                        title=ft.Text(f"{c.get('nombre')} ({c.get('telefono')})"),
                        subtitle=ft.Text(f"Dir: {c.get('direccion')} | Dato: {c.get('nota', '')}")
                    )
                )
            page.update()

        def finalizar_tarea(id_tarea, campo_obs):
            requests.patch(f"{FIREBASE_URL}/tareas/{id_tarea}.json", json={
                "estado": "Finalizada",
                "observacion": campo_obs.value.strip()
            })
            mostrar_alerta("Tarea marcada como finalizada")
            cargar_tareas_empleado()

        def cargar_tareas_empleado(e=None):
            tareas = obtener_tareas()
            total_actual = len(tareas)

            # Detectar si entró una tarea nueva para lanzar notificación emergente
            if estado["cantidad_tareas"] != 0 and total_actual > estado["cantidad_tareas"]:
                ultima_tarea = list(tareas.values())[-1]
                page.dialog = ft.AlertDialog(
                    title=ft.Text(f"?? ¡NUEVO {ultima_tarea.get('tipo', '').upper()}!"),
                    content=ft.Text(
                        f"Cliente: {ultima_tarea.get('nombre')}\n"
                        f"Teléfono: {ultima_tarea.get('telefono')}\n"
                        f"Dirección: {ultima_tarea.get('direccion')}\n"
                        f"Detalle: {ultima_tarea.get('detalle')}"
                    ),
                    actions=[
                        ft.TextButton(
                            "Entendido",
                            on_click=lambda _: setattr(page.dialog, "open", False) or page.update()
                        )
                    ]
                )
                page.dialog.open = True

            estado["cantidad_tareas"] = total_actual
            lista_tareas.controls.clear()

            for id_t, t in reversed(list(tareas.items())):
                pendiente = t.get("estado") == "Pendiente"
                campo_obs = ft.TextField(
                    label="Escribir observación",
                    value=t.get("observacion", ""),
                    read_only=not pendiente
                )

                botones = ft.Row([
                    ft.ElevatedButton(
                        "Finalizar Tarea",
                        icon=ft.Icons.CHECK_CIRCLE,
                        bgcolor=ft.Colors.GREEN_600,
                        color="white",
                        visible=pendiente,
                        on_click=lambda _, tid=id_t, obs=campo_obs: finalizar_tarea(tid, obs)
                    ),
                    ft.OutlinedButton(
                        "Guardar Cliente",
                        icon=ft.Icons.PERSON_ADD,
                        on_click=lambda _, dat=t: guardar_cliente_en_nube(
                            dat.get("nombre"), dat.get("telefono"), dat.get("direccion"), dat.get("detalle")
                        )
                    )
                ], wrap=True)

                tarjeta = ft.Container(
                    padding=15,
                    bgcolor=ft.Colors.AMBER_50 if pendiente else ft.Colors.GREEN_50,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.AMBER_400 if pendiente else ft.Colors.GREEN_400),
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"?? {t.get('tipo')}", weight="bold", size=16),
                            ft.Text(
                                t.get("estado"),
                                weight="bold",
                                color=ft.Colors.ORANGE_800 if pendiente else ft.Colors.GREEN_800
                            )
                        ], alignment="spaceBetween"),
                        ft.Text(f"?? Cliente: {t.get('nombre')}", weight="bold"),
                        ft.Text(f"?? Teléfono: {t.get('telefono')}"),
                        ft.Text(f"?? Dirección: {t.get('direccion')}"),
                        ft.Text(f"?? Detalle: {t.get('detalle')}"),
                        campo_obs,
                        botones
                    ])
                )
                lista_tareas.controls.append(tarjeta)
            page.update()

        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Mis Tareas del Día",
                    icon=ft.Icons.LIST_ALT,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Asignaciones", size=20, weight="bold"),
                            ft.IconButton(ft.Icons.REFRESH, on_click=cargar_tareas_empleado, tooltip="Buscar nuevas tareas")
                        ], alignment="spaceBetween"),
                        lista_tareas
                    ], scroll="adaptive")
                ),
                ft.Tab(
                    text="Clientes Guardados",
                    icon=ft.Icons.CONTACTS,
                    content=ft.Column([
                        ft.Text("Registrar Cliente Nuevo", size=18, weight="bold"),
                        cli_nombre, cli_tel, cli_dir, cli_nota,
                        ft.ElevatedButton("Guardar en Directorio", icon=ft.Icons.SAVE, on_click=guardar_cliente_manual),
                        ft.Divider(),
                        ft.Text("Directorio de Clientes", size=18, weight="bold"),
                        lista_clientes
                    ], scroll="adaptive")
                )
            ],
            expand=1
        )

        page.add(tabs)
        cargar_tareas_empleado()
        cargar_clientes()

    # Pantalla inicial para elegir quién usa el teléfono
    page.add(
        ft.Column([
            ft.Icon(ft.Icons.WORK_OUTLINE, size=60, color=ft.Colors.BLUE_700),
            ft.Text("Control de Operaciones", size=26, weight="bold"),
            ft.Text("Selecciona tu perfil en este teléfono:"),
            ft.ElevatedButton(
                "Soy el Jefe (Asignar tareas)",
                icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                on_click=lambda _: seleccionar_rol("Jefe"),
                width=300,
                height=50
            ),
            ft.ElevatedButton(
                "Soy el Empleado (Recibir tareas)",
                icon=ft.Icons.DELIVERY_DINING,
                on_click=lambda _: seleccionar_rol("Empleado"),
                width=300,
                height=50
            ),
        ], horizontal_alignment="center", alignment="center", spacing=15)
    )


ft.app(target=main)