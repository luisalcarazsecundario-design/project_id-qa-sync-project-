import flet as ft
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Cargar variables desde el archivo .env (para portabilidad)
load_dotenv()

# 1. Conexión Robusta a Firebase
def conectar_db():
    # Intento 1: Usar archivo físico credentials.json (Uso local)
    ruta_json = "credentials.json"
    if os.path.exists(ruta_json):
        if not firebase_admin._apps:
            cred = credentials.Certificate(ruta_json)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    
    # Intento 2: Usar Variables de Entorno (Para otras PCs o GitHub)
    try:
        if not firebase_admin._apps:
            config = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                # Procesa los saltos de línea de la llave privada
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.getenv("FIREBASE_PRIVATE_KEY") else None,
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CERT_URL")
            }
            if config["project_id"]:
                cred = credentials.Certificate(config)
                firebase_admin.initialize_app(cred)
                return firestore.client()
    except Exception as e:
        print(f"Error conectando a Firebase: {e}")
    return None

db = conectar_db()

def main(page: ft.Page):
    # Configuración de la página
    page.title = "QA-Sync Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 500
    page.window_height = 850
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    if db is None:
        page.add(ft.Text("⚠️ Error: No se detectó configuración de Firebase", color="red"))
        return

    col_reportes = db.collection("reportes")

    # --- FUNCIONES CRUD ---
    def cambiar_estado(doc_id, est_actual):
        nuevo = "Finalizado" if est_actual == "Pendiente" else "Pendiente"
        col_reportes.document(doc_id).update({"estado": nuevo})
        cargar_datos()

    def eliminar_item(doc_id):
        col_reportes.document(doc_id).delete()
        cargar_datos()

    def registrar_hallazgo(e):
        if input_cod.value and input_desc.value:
            col_reportes.add({
                "producto": input_cod.value,
                "descripcion": input_desc.value,
                "estado": "Pendiente"
            })
            input_cod.value = ""
            input_desc.value = ""
            cargar_datos()
        page.update()

    def cargar_datos():
        vista_lista.controls.clear()
        try:
            docs = col_reportes.stream()
            for doc in docs:
                data = doc.to_dict()
                id_doc = doc.id
                est = data.get("estado", "Pendiente")
                color_icon = "green" if est == "Finalizado" else "amber"
                
                # Fila de incidencia con botones de acción visibles
                vista_lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.BUG_REPORT, color=color_icon, size=28),
                            ft.Column([
                                ft.Text(data.get("producto"), weight="bold", size=15),
                                ft.Text(data.get("descripcion"), size=12, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"Status: {est}", size=10, italic=True)
                            ], expand=True, spacing=2),
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.Icons.SYNC, icon_color="blue",
                                    on_click=lambda _, i=id_doc, s=est: cambiar_estado(i, s)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE, icon_color="red",
                                    on_click=lambda _, i=id_doc: eliminar_item(i)
                                ),
                            ], spacing=0)
                        ]),
                        bgcolor="#232629",
                        padding=12,
                        border_radius=10,
                        width=440,
                        height=90
                    )
                )
        except Exception as ex:
            print(f"Error Firestore: {ex}")
        page.update()

    # --- COMPONENTES DE INTERFAZ ---
    input_cod = ft.TextField(label="ID del Producto", width=440, border=ft.InputBorder.UNDERLINE)
    input_desc = ft.TextField(label="Descripción del Bug", multiline=True, width=440)
    
    # Botón corregido usando 'content' para evitar errores de argumentos inesperados
    btn_guardar = ft.ElevatedButton(
        content=ft.Text("SUBIR A FIRESTORE", weight="bold"), 
        on_click=registrar_hallazgo, 
        width=440, height=50, 
        style=ft.ButtonStyle(bgcolor="blue", color="white")
    )
    
    vista_lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=400)

    # Agregar elementos a la página (Todo dentro de la función main)
    page.add(
        ft.Column([
            ft.Text("QA-SYNC MOBILE", size=30, weight="heavy", color="blue"),
            ft.Text("Gestión de Calidad en la Nube", size=12, color="white70"),
            ft.Divider(height=20),
            input_cod,
            input_desc,
            ft.Container(btn_guardar, margin=15),
            ft.Text("HISTORIAL DE INCIDENCIAS", size=18, weight="bold"),
            ft.Container(vista_lista, padding=5)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=460)
    )
    
    cargar_datos()

if __name__ == "__main__":
    # Iniciar la aplicación
    ft.app(target=main)