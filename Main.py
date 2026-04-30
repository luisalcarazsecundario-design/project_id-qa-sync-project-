import flet as ft
import firebase_admin
from firebase_admin import credentials, firestore

# 1. Inicializar Firebase
cred = credentials.Certificate("credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

def main(page: ft.Page):
    page.title = "QA-Sync Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    reportes_ref = db.collection("reportes")

    def agregar_reporte(e):
        if txt_producto.value != "" and txt_desc.value != "":
            datos = {
                "producto": txt_producto.value,
                "descripcion": txt_desc.value,
                "estado": "Pendiente"
            }
            reportes_ref.add(datos)
            txt_producto.value = ""
            txt_desc.value = ""
            actualizar_lista()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, llena todos los campos"))
            page.snack_bar.open = True
            page.update()

    def actualizar_lista():
        lista_vista.controls.clear()
        docs = reportes_ref.stream()
        for doc in docs:
            d = doc.to_dict()
            # Usamos un TextButton para EVITAR el error de 'IconButton must have icon'
            lista_vista.controls.append(
                ft.ListTile(
                    title=ft.Text(d.get("producto", "N/A")),
                    subtitle=ft.Text(d.get("descripcion", "N/A")),
                    trailing=ft.TextButton(
                        "ELIMINAR", 
                        style=ft.ButtonStyle(color="red"),
                        on_click=lambda _, id=doc.id: borrar_reporte(id)
                    )
                )
            )
        page.update()

    def borrar_reporte(doc_id):
        reportes_ref.document(doc_id).delete()
        actualizar_lista()

    # --- INTERFAZ ---
    txt_producto = ft.TextField(label="Código de Producto", border_radius=10)
    txt_desc = ft.TextField(label="Descripción Técnica", border_radius=10)
    
    # Botón de registro sin icono para asegurar que abra
    btn_crear = ft.ElevatedButton(
        "REGISTRAR HALLAZGO EN NUBE", 
        on_click=agregar_reporte
    )
    
    lista_vista = ft.Column(scroll=ft.ScrollMode.AUTO)

    page.add(
        ft.Text("QA-Sync: Reporte de Incidencias", size=25, weight="bold", color="blue"),
        txt_producto,
        txt_desc,
        btn_crear,
        ft.Divider(),
        ft.Text("Catálogo de Servicios/Auditorías (Firebase)", size=16, weight="bold"),
        lista_vista
    )
    
    actualizar_lista()

ft.app(target=main)