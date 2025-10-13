import tkinter as tk
from tkinter import ttk, messagebox
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from bson import json_util
import re
from collections import OrderedDict

# --- CONFIGURACIÓN GLOBAL ---
MAX_COLUMN_WIDTH = 150
JSON_COLUMNS = ['attrs', 'location', 'metadata', 'servicePath', 'attrNames', 'entityType']

# --- CLASE DE CONFIGURACIÓN DE ESTILOS ---
class StyleConfig:
    """Define la paleta de colores y la configuración de estilos para la aplicación."""
    
    ROOT_BG_COLOR = '#e6f0f5'
    BG_COLOR = '#ffffff'
    PRIMARY_COLOR = '#60a5fa'  # Azul más claro y moderno (blue-400)
    PRIMARY_HOVER = '#3b82f6'  # Azul hover (blue-500)
    SECONDARY_COLOR = '#94a3b8'  # Gris slate moderno
    SECONDARY_HOVER = '#64748b'  # Gris slate hover
    FG_COLOR = '#1e293b'  # Texto oscuro moderno
    TABLE_HEADER_BG = '#f1f5f9'
    TABLE_ALT_ROW = '#f8fafc'
    TABLE_HOVER = '#dbeafe'  # Azul muy claro para hover (blue-100)
    TABLE_SEPARATOR = '#e2e8f0'

    @staticmethod
    def setup_modern_style(style_obj):
        style_obj.theme_use('alt')
        style_obj.configure('.', background=StyleConfig.BG_COLOR, foreground=StyleConfig.FG_COLOR, font=('Segoe UI', 10))
        style_obj.map('.', background=[('disabled', StyleConfig.ROOT_BG_COLOR)]) 

        style_obj.configure('TButton',
                           font=('Segoe UI', 10, 'bold'),
                           padding=[15, 10],
                           relief='flat',
                           background=StyleConfig.SECONDARY_COLOR,
                           foreground='white',
                           borderwidth=0,
                           highlightthickness=0)
        style_obj.map('TButton',
                      background=[('active', StyleConfig.SECONDARY_HOVER), ('!disabled', StyleConfig.SECONDARY_COLOR)],
                      foreground=[('active', 'white'), ('!disabled', 'white')])

        style_obj.configure('Primary.TButton', 
                           background=StyleConfig.PRIMARY_COLOR,
                           foreground='white',
                           borderwidth=0,
                           highlightthickness=0)
        style_obj.map('Primary.TButton',
                      background=[('active', StyleConfig.PRIMARY_HOVER), ('!disabled', StyleConfig.PRIMARY_COLOR)],
                      relief=[('active', 'flat'), ('!disabled', 'flat')])

        style_obj.configure('TLabel', background=StyleConfig.BG_COLOR, foreground=StyleConfig.FG_COLOR, padding=2)
        style_obj.configure('Title.TLabel', font=('Segoe UI', 11, 'bold'), background=StyleConfig.BG_COLOR)
        style_obj.configure('TEntry',
                           fieldbackground='white',
                           foreground=StyleConfig.FG_COLOR,
                           borderwidth=1,
                           relief='solid', 
                           padding=8)
        style_obj.configure('TPanedwindow', background=StyleConfig.ROOT_BG_COLOR)
        style_obj.configure('Treeview',
                           background='white',
                           foreground=StyleConfig.FG_COLOR,
                           fieldbackground='white',
                           rowheight=30,
                           borderwidth=0,
                           relief='flat')
        style_obj.map('Treeview',
                      background=[('selected', StyleConfig.PRIMARY_COLOR), ('!selected', 'white')],
                      foreground=[('selected', 'white')])
        style_obj.configure('Treeview.Heading',
                           background=StyleConfig.TABLE_HEADER_BG,
                           foreground=StyleConfig.FG_COLOR,
                           font=('Segoe UI', 10, 'bold'),
                           padding=[5, 10],
                           relief='flat')
        style_obj.configure('Nav.Treeview',
                           background=StyleConfig.BG_COLOR,
                           fieldbackground=StyleConfig.BG_COLOR,
                           rowheight=25)
        style_obj.map('Nav.Treeview',
                      background=[('selected', StyleConfig.PRIMARY_COLOR)],
                      foreground=[('selected', 'white')])
        style_obj.configure('Separator.Treeview',
                           background='white',
                           fieldbackground='white')

# --- CLASE DEL PANEL DE NAVEGACIÓN (DBs y Collections) ---
class NavigationPanel(ttk.Frame):
    def __init__(self, parent, app_instance):
        super().__init__(parent, width=280, style='TFrame')
        self.app = app_instance
        self.client = None
        self.pack(fill='y', expand=False)
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Bases de Datos y Colecciones", style='Title.TLabel').pack(fill='x', padx=10, pady=(10, 5))
        
        self.nav_tree = ttk.Treeview(self, columns=('type',), show='tree', style='Nav.Treeview')
        self.nav_tree.heading('#0', text='Recurso')
        self.nav_tree.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.nav_tree.bind('<<TreeviewOpen>>', self.on_tree_expand)
        self.nav_tree.bind('<<TreeviewSelect>>', self.on_nav_select)
        
        nav_v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.nav_tree.yview)
        nav_v_scrollbar.pack(side='right', fill='y')
        self.nav_tree.configure(yscrollcommand=nav_v_scrollbar.set)

    def set_client(self, client):
        self.client = client
        self.load_dbs()

    def load_dbs(self):
        if not self.client: return
        for item in self.nav_tree.get_children():
            self.nav_tree.delete(item)
        try:
            db_names = self.client.list_database_names()
            for db_name in sorted(db_names):
                if db_name not in ["admin", "local", "config"]:
                    db_id = self.nav_tree.insert('', 'end', text=db_name, values=('db',))
                    self.nav_tree.insert(db_id, 'end', text='Cargando Colecciones...', values=('placeholder',))
        except Exception as e:
            messagebox.showerror("Error al cargar DBs", f"Fallo al cargar bases de datos: {e}")

    def on_tree_expand(self, event):
        if not self.nav_tree.selection(): return
        selected_item = self.nav_tree.selection()[0]
        item_values = self.nav_tree.item(selected_item, 'values')

        if item_values and item_values[0] == 'db':
            children = self.nav_tree.get_children(selected_item)
            if children and self.nav_tree.item(children[0], 'values')[0] == 'placeholder':
                self.load_collections(selected_item)

    def on_nav_select(self, event):
        if not self.nav_tree.selection(): return

        selected_item = self.nav_tree.selection()[0]
        item_values = self.nav_tree.item(selected_item, 'values')
        item_text = self.nav_tree.item(selected_item, 'text')

        if not item_values or item_values[0] in ['placeholder', 'db']: return

        item_type = item_values[0]

        if item_type == 'collection':
            parent_id = self.nav_tree.parent(selected_item)
            db_name = self.nav_tree.item(parent_id, 'text')
            collection_name = item_text
            self.app.load_collection_data(db_name, collection_name)

    def load_collections(self, db_id):
        if not self.client: return

        for child in self.nav_tree.get_children(db_id):
            self.nav_tree.delete(child)

        db_name = self.nav_tree.item(db_id, 'text')
        db = self.client[db_name]

        try:
            collection_names = db.list_collection_names()
            for col_name in sorted(collection_names):
                self.nav_tree.insert(db_id, 'end', text=col_name, values=('collection',))
        except Exception as e:
            messagebox.showerror("Error al cargar Colecciones", f"Fallo al cargar colecciones de {db_name}: {e}")

# --- CLASE DEL PANEL DE DATOS (Filtro, Tabla, Paginación) ---
class DataPanel(ttk.Frame):
    def __init__(self, parent, app_instance):
        super().__init__(parent, style='TFrame')
        self.app = app_instance
        self.pack(fill='both', expand=True)
        self.create_widgets()

    def create_widgets(self):
        filter_frame = ttk.Frame(self, padding="5", style='TFrame')
        filter_frame.pack(fill='x', expand=False)

        ttk.Label(filter_frame, text="Filtro JSON (ej. {\"id.type\": \"Device\"}):").pack(side='left', padx=5)
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.app.current_filter, width=50, style='TEntry')
        self.filter_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(filter_frame, text="⚡ Aplicar Filtro", command=self.app.apply_filter, style='Primary.TButton').pack(side='left', padx=5)

        self.data_label = ttk.Label(self, text="Selecciona una colección para ver los datos.", style='Title.TLabel')
        self.data_label.pack(fill='x', padx=10, pady=5)

        table_frame = ttk.Frame(self, style='TFrame')
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(table_frame, background='white', highlightthickness=0)
        self.canvas.pack(side='left', fill='both', expand=True)

        self.data_tree = ttk.Treeview(self.canvas, show='headings', style='Separator.Treeview')
        self.data_tree_window = self.canvas.create_window((0, 0), window=self.data_tree, anchor='nw')
        self.data_tree.bind('<Double-1>', self.app.on_cell_double_click)
        self.data_tree.bind('<Motion>', self.on_motion)
        self.data_tree.bind('<Leave>', self.on_leave)
        self.data_tree.bind('<Configure>', self.update_canvas)

        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.data_tree.yview)
        v_scrollbar.pack(side='right', fill='y')
        self.data_tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.data_tree.xview)
        h_scrollbar.pack(fill='x', padx=10)
        self.data_tree.configure(xscrollcommand=h_scrollbar.set)

        op_frame = ttk.Frame(self, padding="5", style='TFrame')
        op_frame.pack(fill='x', expand=False)

        ttk.Label(op_frame, text="Doc. por página:").pack(side='left', padx=(20, 5))
        self.page_size_combo = ttk.Combobox(op_frame,
                                            textvariable=self.app.page_size,
                                            values=[20, 50, 100],
                                            width=5,
                                            state="readonly",
                                            style='TCombobox')
        self.page_size_combo.pack(side='left', padx=5)
        self.page_size_combo.bind('<<ComboboxSelected>>', lambda e: self.app.apply_page_size())

        ttk.Button(op_frame, text="✎ Ver/Editar", command=self.app.open_document_op, style='Primary.TButton').pack(side='left', padx=10)
        ttk.Button(op_frame, text="✖ Eliminar", command=self._delete_document_wrapper, style='TButton').pack(side='left', padx=10)

        self.page_info_label = ttk.Label(op_frame, textvariable=self.app.page_info_text)
        self.page_info_label.pack(side='right', padx=5)

        ttk.Button(op_frame, text="►", command=lambda: self.app.change_page(1)).pack(side='right', padx=5)
        ttk.Button(op_frame, text="◄", command=lambda: self.app.change_page(-1)).pack(side='right', padx=5)

        self.last_hovered = None
        self.horizontal_lines = []

    def update_canvas(self, event=None):
        """Actualizar el tamaño del Treeview y dibujar líneas horizontales."""
        self.canvas.itemconfig(self.data_tree_window, width=self.canvas.winfo_width(), height=self.canvas.winfo_height())
        self.draw_horizontal_lines()

    def draw_horizontal_lines(self):
        """Dibujar líneas horizontales entre filas."""
        for line in self.horizontal_lines:
            self.canvas.delete(line)
        self.horizontal_lines = []

        row_height = 30
        num_rows = len(self.data_tree.get_children())
        if num_rows == 0:
            return

        canvas_width = self.canvas.winfo_width()
        for i in range(num_rows + 1):
            y = i * row_height
            line = self.canvas.create_line(0, y, canvas_width, y, fill=StyleConfig.TABLE_SEPARATOR, width=1)
            self.horizontal_lines.append(line)

    def on_motion(self, event):
        """Handle mouse motion to highlight the row under the cursor."""
        item = self.data_tree.identify_row(event.y)
        if item and item != self.last_hovered:
            if self.last_hovered:
                tags = list(self.data_tree.item(self.last_hovered, 'tags'))
                if 'hover' in tags:
                    tags.remove('hover')
                    self.data_tree.item(self.last_hovered, tags=tags)
            self.data_tree.item(item, tags=list(self.data_tree.item(item, 'tags')) + ['hover'])
            self.last_hovered = item
            self.data_tree.tag_configure('hover', background=StyleConfig.TABLE_HOVER)

    def on_leave(self, event):
        """Remove hover effect when mouse leaves the treeview."""
        if self.last_hovered:
            tags = list(self.data_tree.item(self.last_hovered, 'tags'))
            if 'hover' in tags:
                tags.remove('hover')
                self.data_tree.item(self.last_hovered, tags=tags)
            self.last_hovered = None

    def _delete_document_wrapper(self):
        """Wrapper para llamar al método de eliminación de la aplicación principal."""
        self.app.delete_document_op()

# --- CLASE PRINCIPAL DE LA APLICACIÓN ---
class MongoExplorerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mongo Explorer (K8s Ready) - Modern UI")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Variables de estado
        self.mongo_uri = tk.StringVar(value="mongodb://127.0.0.1:27018/")
        self.current_filter = tk.StringVar()
        self.page_size = tk.IntVar(value=20)
        self.page_info_text = tk.StringVar(value="Página 1")
        
        self.client = None
        self.current_db_name = None
        self.current_collection_name = None
        self.current_page = 0
        self.sort_column = None
        self.sort_direction = 1  # 1 = ascendente, -1 = descendente

        # Configuración del estilo
        self.style = ttk.Style()
        StyleConfig.setup_modern_style(self.style)
        self.config(background=StyleConfig.ROOT_BG_COLOR)

        self.create_widgets()

    def create_widgets(self):
        connection_frame = ttk.Frame(self, padding="10 10 10 0", style='TFrame')
        connection_frame.pack(fill='x', expand=False, padx=10, pady=(10, 0))

        ttk.Label(connection_frame, text="URI de MongoDB:").pack(side='left', padx=5)
        self.uri_entry = ttk.Entry(connection_frame, textvariable=self.mongo_uri, width=80, style='TEntry')
        self.uri_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(connection_frame, text="⚡ Conectar", command=self.connect_mongo, style='Primary.TButton').pack(side='left', padx=5)

        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL, style='TPanedwindow')
        main_paned_window.pack(fill='both', expand=True, padx=10, pady=10)

        self.nav_panel = NavigationPanel(main_paned_window, self)
        main_paned_window.add(self.nav_panel)

        self.data_panel = DataPanel(main_paned_window, self)
        main_paned_window.add(self.data_panel)

    def connect_mongo(self):
        uri = self.mongo_uri.get()
        if not uri:
            messagebox.showerror("Error de Conexión", "La URI de MongoDB no puede estar vacía.")
            return

        try:
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                directConnection=True
            )
            self.client.admin.command('ping')
            messagebox.showinfo("Conexión Exitosa", "Conectado a MongoDB.")
            self.nav_panel.set_client(self.client)
        except Exception as e:
            error_msg = f"No se pudo conectar. Asegúrate de que el túnel 'kubectl port-forward' esté activo.\n\nDetalles: {e}"
            messagebox.showerror("Error de Conexión", error_msg)
            self.client = None

    def load_collection_data(self, db_name, collection_name):
        self.current_db_name = db_name
        self.current_collection_name = collection_name
        self.current_page = 0
        self.sort_column = None
        self.sort_direction = 1
        self.load_documents()

    def apply_filter(self):
        if not self.current_collection_name:
            messagebox.showwarning("Filtro", "Selecciona una colección primero.")
            return
        self.current_page = 0
        self.load_documents()

    def apply_page_size(self):
        if not self.current_collection_name: return
        self.current_page = 0
        self.load_documents()

    def change_page(self, direction):
        new_page = self.current_page + direction
        if new_page >= 0:
            self.current_page = new_page
            self.load_documents()
        else:
            messagebox.showinfo("Paginación", "Ya estás en la primera página.")

    def toggle_sort(self, column):
        """Alternar ordenación de una columna."""
        if self.sort_column == column:
            # Si es la misma columna, cambiar dirección
            self.sort_direction = -1 if self.sort_direction == 1 else 1
        else:
            # Nueva columna, empezar con ascendente
            self.sort_column = column
            self.sort_direction = 1
        
        self.current_page = 0
        self.load_documents()

    def _get_clean_id(self, doc_id_bson):
        if isinstance(doc_id_bson, ObjectId):
            return str(doc_id_bson)
        
        full_id_str = str(doc_id_bson).replace("'", '"')

        try:
            id_doc = json_util.loads(full_id_str)
            if isinstance(id_doc, dict) and 'id' in id_doc:
                return id_doc['id']
            return str(doc_id_bson)
        except:
            id_match = re.search(r'"id"\s*:\s*"([^"]*)"', full_id_str)
            if id_match:
                return id_match.group(1)
            return str(doc_id_bson)

    def load_documents(self):
        if not self.current_db_name or not self.current_collection_name: return

        self.data_panel.data_tree.tag_configure('oddrow', background=StyleConfig.TABLE_ALT_ROW)
        self.data_panel.data_tree.tag_configure('hover', background=StyleConfig.TABLE_HOVER)
        self.data_panel.data_tree.tag_configure('separator', background='white')

        db = self.client[self.current_db_name]
        collection = db[self.current_collection_name]

        self.data_panel.data_label.config(text=f"Colección: {self.current_db_name}.{self.current_collection_name}")

        skip = self.current_page * self.page_size.get()
        limit = self.page_size.get()

        query_filter = {}
        filter_str = self.current_filter.get().strip()
        if filter_str:
            try:
                query_filter = json.loads(filter_str)
            except json.JSONDecodeError as e:
                messagebox.showerror("Error de Filtro", f"Formato JSON inválido: {e}")
                query_filter = {}

        try:
            cursor = collection.find(query_filter).skip(skip).limit(limit)
            
            # Aplicar ordenación si hay una columna seleccionada
            if self.sort_column:
                cursor = cursor.sort(self.sort_column, self.sort_direction)
            
            documents = list(cursor)

            for item in self.data_panel.data_tree.get_children():
                self.data_panel.data_tree.delete(item)

            if not documents:
                self.data_panel.data_label.config(text=f"Colección: {self.current_db_name}.{self.current_collection_name} (Página {self.current_page + 1} - Sin resultados)")
                self.data_panel.data_tree.config(columns=())
                self.page_info_text.set(f"Página {self.current_page + 1}")
                self.data_panel.draw_horizontal_lines()
                return

            all_keys = set()
            for doc in documents:
                all_keys.update(doc.keys())
            
            sorted_keys = ['_id'] + sorted([k for k in all_keys if k != '_id'])
            
            self.data_panel.data_tree.config(columns=sorted_keys)
            
            for col in sorted_keys:
                # Determinar el texto del encabezado con indicador de ordenación
                header_text = col
                if self.sort_column == col:
                    header_text = f"{col} {'↑' if self.sort_direction == 1 else '↓'}"
                
                self.data_panel.data_tree.heading(col, text=header_text, anchor='w', 
                                                 command=lambda c=col: self.toggle_sort(c))
                self.data_panel.data_tree.column(col, width=MAX_COLUMN_WIDTH, anchor='w', stretch=True, minwidth=60)

            for i, doc in enumerate(documents):
                values = []
                for key in sorted_keys:
                    value = doc.get(key)
                    if value is None:
                        values.append("")
                    elif isinstance(value, (dict, list)):
                        try:
                            values.append(json.dumps(value, default=json_util.default, separators=(',', ':'))[:MAX_COLUMN_WIDTH] + "...")
                        except Exception:
                            values.append(str(value)[:MAX_COLUMN_WIDTH])
                    else:
                        values.append(str(value)[:MAX_COLUMN_WIDTH])
                
                full_id_bson_str = json_util.dumps(doc['_id'])
                tag = 'oddrow' if i % 2 != 0 else 'separator'
                self.data_panel.data_tree.insert('', 'end', iid=full_id_bson_str, values=values, tags=(tag,))

            self.page_info_text.set(f"Página {self.current_page + 1}")
            self.data_panel.draw_horizontal_lines()

        except Exception as e:
            messagebox.showerror("Error de Carga", f"Fallo al cargar documentos: {e}")

    def on_cell_double_click(self, event):
        if not self.data_panel.data_tree.selection(): return

        item_id = self.data_panel.data_tree.selection()[0]
        region = self.data_panel.data_tree.identify("region", event.x, event.y)
        
        if region == "cell":
            col_id = self.data_panel.data_tree.identify_column(event.x)
            col_index = int(col_id.replace('#', '')) - 1
            col_name = self.data_panel.data_tree.heading(col_id)['text']
            
            if col_name == '_id':
                messagebox.showwarning("Edición", "El campo '_id' no se puede editar directamente en la celda. Usa 'Ver/Editar Documento' para reemplazar el documento completo.")
                return

            item_values = self.data_panel.data_tree.item(item_id, 'values')
            current_value = item_values[col_index] if col_index < len(item_values) else ""
            self.open_cell_editor(item_id, col_name, current_value)

    def open_cell_editor(self, full_id_bson_str, col_name, current_value):
        if not self.client or not self.current_collection_name: return

        db = self.client[self.current_db_name]
        collection = db[self.current_collection_name]

        try:
            viewer = tk.Toplevel(self)
            viewer.title(f"Editar '{col_name}' de ID: {self._get_clean_id(full_id_bson_str)}")
            viewer.geometry("600x400")
            viewer.config(background='#ffffff')

            is_json_field = col_name in JSON_COLUMNS or (isinstance(current_value, str) and (current_value.startswith('{') or current_value.startswith('[')))

            ttk.Label(viewer, text=f"Campo: {col_name} (Tipo: {'JSON/Array' if is_json_field else 'Texto/Valor'})", style='Title.TLabel').pack(padx=10, pady=5, anchor='w')

            text_frame = ttk.Frame(viewer, padding=5, style='TFrame')
            text_frame.pack(fill='both', expand=True, padx=10, pady=5)

            text_widget = tk.Text(text_frame, wrap='word', borderwidth=1, relief='solid', padx=5, pady=5, font=('Consolas', 10), background='white')
            text_widget.pack(side='left', fill='both', expand=True)

            v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            v_scrollbar.pack(side='right', fill='y')
            text_widget.config(yscrollcommand=v_scrollbar.set)

            if is_json_field:
                try:
                    document_query = self._get_id_query_from_bson(full_id_bson_str)
                    document = collection.find_one(document_query)
                    
                    if document and col_name in document:
                        full_value = document[col_name]
                        formatted_value = json_util.dumps(full_value, indent=4)
                        text_widget.insert('1.0', formatted_value)
                    else:
                        text_widget.insert('1.0', current_value)
                        messagebox.showwarning("Advertencia", "No se pudo recuperar el valor completo del campo. Se muestra el valor truncado de la tabla.")
                except Exception as e:
                    text_widget.insert('1.0', current_value)
                    messagebox.showwarning("Advertencia", f"Error al formatear JSON: {e}. Mostrando valor sin formato.")
            else:
                text_widget.insert('1.0', current_value)

            button_frame = ttk.Frame(viewer, padding="10", style='TFrame')
            button_frame.pack(fill='x', expand=False)

            def copy_content():
                content = text_widget.get('1.0', tk.END)
                self.clipboard_clear()
                self.clipboard_append(content)
                viewer.title(f"✓ COPIADO - Editar '{col_name}'")
                self.after(2000, lambda: viewer.title(f"Editar '{col_name}' de ID: {self._get_clean_id(full_id_bson_str)}"))

            def save_cell_edition():
                try:
                    new_value_str = text_widget.get('1.0', tk.END).strip()
                    
                    if is_json_field or (isinstance(new_value_str, str) and (new_value_str.startswith('{') or new_value_str.startswith('['))):
                        new_value = json_util.loads(new_value_str) 
                    else:
                        new_value = new_value_str 
                    
                    update_query = self._get_id_query_from_bson(full_id_bson_str)

                    result = collection.update_one(
                        update_query,
                        {"$set": {col_name: new_value}}
                    )

                    if result.modified_count == 1:
                        messagebox.showinfo("Éxito", f"Campo '{col_name}' actualizado correctamente.")
                        viewer.destroy()
                        self.load_documents()
                    else:
                        messagebox.showwarning("Error", f"No se pudo actualizar el campo '{col_name}'. Documento no encontrado o no modificado.")

                except json.JSONDecodeError as e:
                    messagebox.showerror("Error de Guardado", f"El contenido no es JSON válido para este campo: {e}")
                except Exception as e:
                    messagebox.showerror("Error de Guardado", f"Fallo al guardar en la base de datos: {e}")

            ttk.Button(button_frame, text="⎘ Copiar", command=copy_content, style='TButton').pack(side='left', padx=5)
            ttk.Button(button_frame, text="✓ Guardar", command=save_cell_edition, style='Primary.TButton').pack(side='left', padx=15)
            ttk.Button(button_frame, text="✖ Cerrar", command=viewer.destroy, style='TButton').pack(side='right', padx=5)

        except Exception as e:
            messagebox.showerror("Error de Visualización", f"Fallo en la visualización/edición de la celda: {e}")

    def _get_id_query_from_bson(self, full_id_str):
        cleaned_id_str = str(full_id_str).replace("'", '"')
        id_query = {}

        try:
            id_doc = json_util.loads(cleaned_id_str)
            if isinstance(id_doc, dict) and 'id' in id_doc:
                id_value_to_search = id_doc['id']
                id_query = {"_id.id": id_value_to_search}
            else:
                id_query = {"_id": id_doc}
        except:
            id_match = re.search(r'"id"\s*:\s*"([^"]*)"', cleaned_id_str)
            if id_match:
                id_value_to_search = id_match.group(1)
                id_query = {"_id.id": id_value_to_search}
            else:
                try:
                    id_query = {"_id": ObjectId(full_id_str)}
                except:
                    id_query = {"_id": full_id_str}
        
        return id_query

    def open_document_op(self):
        if not self.data_panel.data_tree.selection():
            messagebox.showinfo("Operación", "Por favor, selecciona un documento de la tabla.")
            return

        selected_item_id = self.data_panel.data_tree.selection()[0]
        full_id_str = selected_item_id
        
        db = self.client[self.current_db_name]
        collection = db[self.current_collection_name]
        
        try:
            document_query = self._get_id_query_from_bson(full_id_str)
            id_value_to_show = self._get_clean_id(full_id_str)

            document = collection.find_one(document_query)

            if not document:
                messagebox.showerror("Error", f"Documento no encontrado. La consulta falló con: {document_query}.")
                return

            document_id_to_save = document['_id']

            editor = tk.Toplevel(self)
            editor.title(f"Documento ID: {id_value_to_show[:50]}...")
            editor.geometry("700x500")
            editor.config(background='#ffffff')

            ttk.Label(editor, text="JSON del Documento:", style='Title.TLabel').pack(padx=10, pady=5, anchor='w')

            json_text_widget = tk.Text(editor, wrap='word', borderwidth=1, relief='flat', padx=5, pady=5, font=('Consolas', 10), background='white')
            json_text_widget.pack(fill='both', expand=True, padx=10, pady=5)

            formatted_json = json_util.dumps(document, indent=4)
            json_text_widget.insert('1.0', formatted_json)

            def save_document():
                try:
                    new_json_str = json_text_widget.get('1.0', tk.END)
                    new_doc = json_util.loads(new_json_str)

                    update_id = document_id_to_save

                    new_doc.pop('_id', None)

                    collection.replace_one(
                        {"_id": update_id},
                        new_doc
                    )
                    messagebox.showinfo("Éxito", "Documento actualizado correctamente.")
                    editor.destroy()
                    self.load_documents()
                except Exception as e:
                    messagebox.showerror("Error de Guardado", f"Error al guardar o parsear JSON: {e}")

            button_frame = ttk.Frame(editor, padding="10", style='TFrame')
            button_frame.pack(fill='x', expand=False)

            ttk.Button(button_frame, text="✓ Guardar Documento", command=save_document, style='Primary.TButton').pack(side='left', padx=5)
            ttk.Button(button_frame, text="✖ Cerrar", command=editor.destroy, style='TButton').pack(side='right', padx=5)

        except Exception as e:
            messagebox.showerror("Error de Documento (General)", f"Fallo al obtener/procesar el documento: {e}")

    def delete_document_op(self):
        """
        Elimina el documento seleccionado de la colección actual, previa confirmación.
        """
        if not self.data_panel.data_tree.selection():
            messagebox.showinfo("Operación", "Por favor, selecciona un documento de la tabla para eliminar.")
            return

        if not self.current_db_name or not self.current_collection_name:
            messagebox.showwarning("Error", "No hay una colección seleccionada.")
            return

        selected_item_id = self.data_panel.data_tree.selection()[0]
        full_id_str = selected_item_id
        id_value_to_show = self._get_clean_id(full_id_str)

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el documento con ID: {id_value_to_show} de la colección {self.current_collection_name}?\n\nEsta acción es irreversible."
        )

        if not confirm:
            return

        db = self.client[self.current_db_name]
        collection = db[self.current_collection_name]

        try:
            document_query = self._get_id_query_from_bson(full_id_str)
            result = collection.delete_one(document_query)

            if result.deleted_count == 1:
                messagebox.showinfo("Éxito", f"Documento con ID {id_value_to_show} eliminado correctamente.")
                self.load_documents()
            else:
                messagebox.showerror("Error", f"No se pudo eliminar el documento. Documento no encontrado o error en la consulta.")

        except Exception as e:
            messagebox.showerror("Error de Eliminación", f"Fallo al eliminar el documento: {e}")

if __name__ == "__main__":
    app = MongoExplorerApp()
    app.mainloop()