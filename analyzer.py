import os
import ast
from typing import Dict, List, Set, Optional
import logging

class ProjectAnalyzer:
    def __init__(self, 
                 project_path: Optional[str] = None,
                 file_extensions: Optional[List[str]] = None,
                 include_external: bool = False):
        """
        Инициализация анализатора проекта
        
        Args:
            project_path: Путь к проекту для анализа. Если None, используется текущая директория
            file_extensions: Список расширений файлов для анализа
            include_external: Включать ли внешние зависимости
        """
        self.project_path = project_path or os.getcwd()
        self.file_extensions = file_extensions or ['.py', '.js', '.html', '.css']
        self.include_external = include_external
        self.dependencies = {}  # Словарь зависимостей
        self.logger = logging.getLogger(__name__)

    def analyze(self) -> Dict:
        """
        Анализ проекта и построение графа зависимостей
        
        Returns:
            Dict: Словарь зависимостей между модулями
        """
        self.dependencies = {}
        self._scan_directory(self.project_path)
        return self.dependencies

    def _scan_directory(self, directory: str) -> None:
        """
        Рекурсивное сканирование директории
        
        Args:
            directory: Путь к директории для сканирования
        """
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in self.file_extensions):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, self.project_path)
                        self._analyze_file(file_path, relative_path)
        except Exception as e:
            self.logger.error(f"Ошибка при сканировании директории {directory}: {str(e)}")

    def _analyze_file(self, file_path: str, relative_path: str) -> None:
        """
        Анализ отдельного файла
        
        Args:
            file_path: Абсолютный путь к файлу
            relative_path: Относительный путь к файлу
        """
        try:
            if file_path.endswith('.py'):
                self._analyze_python_file(file_path, relative_path)
            # TODO: Добавить анализ для других типов файлов (js, html, css)
        except Exception as e:
            self.logger.error(f"Ошибка при анализе файла {file_path}: {str(e)}")

    def _analyze_python_file(self, file_path: str, relative_path: str) -> None:
        """
        Анализ Python файла
        
        Args:
            file_path: Путь к файлу
            relative_path: Относительный путь к файлу
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read(), filename=file_path)
                
            imports = set()
            imported_names = set()  # Для хранения импортированных классов/функций
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_name = name.name.split('.')[0]
                        imports.add(module_name)
                        imported_names.add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        imports.add(module_name)
                        # Добавляем информацию о конкретных импортированных элементах
                        for name in node.names:
                            imported_names.add(f"{module_name}.{name.name}")

            # Фильтрация внешних зависимостей
            if not self.include_external:
                local_imports = set()
                local_names = set()
                for imp in imports:
                    possible_paths = [
                        os.path.join(self.project_path, f"{imp}.py"),
                        os.path.join(self.project_path, imp, "__init__.py"),
                        os.path.join(os.path.dirname(file_path), f"{imp}.py"),
                    ]
                    if any(os.path.exists(p) for p in possible_paths):
                        local_imports.add(imp)
                        # Сохраняем импортированные имена только для локальных модулей
                        local_names.update(name for name in imported_names if name.split('.')[0] == imp)
                imports = local_imports
                imported_names = local_names

            self.dependencies[relative_path] = {
                'imports': list(imports),
                'imported_names': list(imported_names),  # Добавляем новое поле
                'functions': self._get_functions(tree),
                'classes': self._get_classes(tree)
            }
        except Exception as e:
            self.logger.error(f"Ошибка при анализе Python файла {file_path}: {str(e)}")

    def _get_functions(self, tree: ast.AST) -> List[Dict]:
        """
        Получение списка функций из AST
        
        Args:
            tree: AST дерево Python файла
        
        Returns:
            List[Dict]: Список функций с их характеристиками
        """
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args]
                })
        return functions

    def _get_classes(self, tree: ast.AST) -> List[Dict]:
        """
        Получение информации о классах из AST
        
        Args:
            tree: AST дерево
            
        Returns:
            Список словарей с информацией о классах
        """
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'args': self._get_function_args(item)
                        })
                classes.append({
                    'name': node.name,
                    'methods': methods
                })
        return classes

    def _get_function_args(self, node: ast.FunctionDef) -> List[str]:
        """
        Получение аргументов функции
        
        Args:
            node: Узел AST функции
        
        Returns:
            List[str]: Список аргументов функции
        """
        return [arg.arg for arg in node.args.args]

    def _is_local_import(self, import_name: str) -> bool:
        """
        Проверка, является ли импорт локальным
        
        Args:
            import_name: Имя импортируемого модуля
        
        Returns:
            bool: True если импорт локальный, False если внешний
        """
        # Проверяем наличие файла с таким именем в проекте
        possible_paths = [
            os.path.join(self.project_path, *import_name.split('.')),
            os.path.join(self.project_path, *import_name.split('.')) + '.py'
        ]
        return any(os.path.exists(path) for path in possible_paths)
