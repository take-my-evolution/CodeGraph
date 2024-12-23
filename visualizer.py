from pyvis.network import Network
import networkx as nx
from typing import Dict, Optional
import os
import json

class GraphVisualizer:
    def __init__(self, dependencies: Dict, output_dir: Optional[str] = None):
        """
        Инициализация визуализатора графа
        
        Args:
            dependencies: Словарь зависимостей от анализатора
            output_dir: Директория для сохранения результатов
        """
        self.dependencies = dependencies
        self.output_dir = output_dir or os.getcwd()
        self.graph = Network(
            height="100vh",
            width="100%",
            bgcolor="#ffffff",
            font_color="#000000"
        )
        self.graph.toggle_physics(True)
        self._setup_graph_options()

    def _setup_graph_options(self):
        """Настройка параметров отображения графа"""
        options = {
            "nodes": {
                "shape": "dot",
                "size": 25,
                "font": {
                    "size": 14,
                    "face": "Tahoma"
                }
            },
            "edges": {
                "color": {"inherit": True},
                "smooth": {"type": "continuous"}
            },
            "physics": {
                "barnesHut": {
                    "gravitationalConstant": -15000,
                    "centralGravity": 0.3,
                    "springLength": 200
                },
                "minVelocity": 0.75
            },
            "groups": {
                "files": {
                    "color": "#97c2fc",
                    "shape": "dot"
                },
                "classes": {
                    "color": "#ffb347",
                    "shape": "diamond"
                },
                "functions": {
                    "color": "#7be141",
                    "shape": "triangle"
                },
                "methods": {
                    "color": "#7be141",
                    "shape": "triangle"
                }
            }
        }
        self.graph.set_options(json.dumps(options))

    def create_graph(self) -> None:
        """Создает граф на основе данных о зависимостях"""
        # Сначала создаем все узлы файлов
        for file_path, data in self.dependencies.items():
            self.graph.add_node(
                file_path,
                label=os.path.basename(file_path),
                title=self._create_node_tooltip(file_path, data),
                color='lightblue',
                shape='dot',
                size=10,
                group='files'
            )

        # Затем добавляем все связи и остальные узлы
        for file_path, data in self.dependencies.items():
            # Добавляем связи по импортам
            for imp in data.get('imports', []):
                # Ищем соответствующий файл в зависимостях
                target_file = None
                for dep_file in self.dependencies.keys():
                    if os.path.basename(dep_file) == f"{imp}.py":
                        target_file = dep_file
                        break
                
                if target_file:
                    self.graph.add_edge(file_path, target_file, color='blue', dashes=False)

            # Добавляем связи по конкретным импортированным элементам
            for imported_name in data.get('imported_names', []):
                module_name, item_name = imported_name.split('.')
                # Ищем соответствующий файл
                target_file = None
                for dep_file in self.dependencies.keys():
                    if os.path.basename(dep_file) == f"{module_name}.py":
                        target_file = dep_file
                        break
                
                if target_file:
                    self.graph.add_edge(
                        file_path, 
                        target_file, 
                        color='blue', 
                        title=f"imports {item_name}",
                        dashes=False
                    )

            # Добавляем узлы для классов и их методов
            for class_info in data.get('classes', []):
                class_id = f"{file_path}::{class_info['name']}"
                self.graph.add_node(
                    class_id,
                    label=class_info['name'],
                    title=f"Class: {class_info['name']}",
                    color='orange',
                    shape='diamond',
                    size=8,
                    group='classes'
                )
                self.graph.add_edge(file_path, class_id)

                # Добавляем методы класса
                for method in class_info.get('methods', []):
                    method_id = f"{class_id}::{method['name']}"
                    self.graph.add_node(
                        method_id,
                        label=method['name'],
                        title=f"Method: {method['name']}\nArgs: {', '.join(method.get('args', []))}",
                        color='green',
                        shape='triangle',
                        size=6,
                        group='methods'
                    )
                    self.graph.add_edge(class_id, method_id)

            # Добавляем узлы для функций
            for func_info in data.get('functions', []):
                func_id = f"{file_path}::{func_info['name']}"
                self.graph.add_node(
                    func_id,
                    label=func_info['name'],
                    title=f"Function: {func_info['name']}\nArgs: {', '.join(func_info.get('args', []))}",
                    color='green',
                    shape='triangle',
                    size=6,
                    group='functions'
                )
                self.graph.add_edge(file_path, func_id)

    def _create_node_tooltip(self, file_path: str, data: Dict) -> str:
        """
        Создание подсказки для узла
        
        Args:
            file_path: Путь к файлу
            data: Данные о файле
        
        Returns:
            str: HTML-подсказка
        """
        tooltip = [f"<b>File:</b> {file_path}"]
        
        if data.get('classes'):
            tooltip.append("\n<b>Classes:</b>")
            for class_info in data['classes']:
                tooltip.append(f"- {class_info['name']}")
        
        if data.get('functions'):
            tooltip.append("\n<b>Functions:</b>")
            for func in data['functions']:
                if func['name'].startswith('_'):
                    continue  # Пропускаем приватные методы
                tooltip.append(f"- {func['name']}")
        
        return '\n'.join(tooltip)

    def save(self, filename: str = "code_graph.html"):
        """
        Сохранение графа в HTML файл
        
        Args:
            filename: Имя выходного файла
        """
        output_path = os.path.join(self.output_dir, filename)
        self.graph.save_graph(output_path)
        
        # Добавляем кнопки фильтрации после сохранения
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Добавляем HTML для кнопок фильтрации
        filter_buttons = """
        <style>
        .filter-panel {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 999;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            gap: 10px;
        }
        .filter-button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #4a90e2;
            color: white;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        .filter-button:hover {
            background: #357abd;
        }
        .legend {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 3px;
        }
        </style>
        <div class="filter-panel">
            <button class="filter-button" onclick="filterNodes('files')">Только файлы</button>
            <button class="filter-button" onclick="filterNodes('classes')">Показать классы</button>
            <button class="filter-button" onclick="filterNodes('functions')">Показать функции</button>
            <button class="filter-button" onclick="filterNodes('all')">Показать все</button>
        </div>
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #97c2fc;"></div>
                <span>Файлы</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffb347;"></div>
                <span>Классы</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #7be141;"></div>
                <span>Функции</span>
            </div>
        </div>
        """
        
        # Добавляем JavaScript для фильтрации
        filter_script = """
        <script>
        function filterNodes(group) {
            var nodes = network.body.data.nodes;
            var edges = network.body.data.edges;
            
            if (group === 'all') {
                nodes.forEach(node => {
                    nodes.update({id: node.id, hidden: false});
                });
                edges.forEach(edge => {
                    edges.update({id: edge.id, hidden: false});
                });
            } else {
                nodes.forEach(node => {
                    var shouldHide = (
                        (group === 'files' && (node.group === 'classes' || node.group === 'functions')) ||
                        (group === 'classes' && node.group === 'functions')
                    );
                    nodes.update({id: node.id, hidden: shouldHide});
                });
                
                edges.forEach(edge => {
                    var fromNode = nodes.get(edge.from);
                    var toNode = nodes.get(edge.to);
                    var shouldHide = fromNode.hidden || toNode.hidden;
                    edges.update({id: edge.id, hidden: shouldHide});
                });
            }
        }
        </script>
        """
        
        # Вставляем кнопки и скрипт перед закрывающим тегом body
        content = content.replace('</body>', f'{filter_buttons}{filter_script}</body>')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
