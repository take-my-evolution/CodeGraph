import os
import argparse
from analyzer import ProjectAnalyzer
from visualizer import GraphVisualizer

def get_project_path():
    """Запрашивает путь к проекту у пользователя"""
    try:
        path = input("Enter project path (or press Enter for current directory): ").strip()
        if not path:
            return os.getcwd()
        
        # Проверяем существование пути
        if not os.path.exists(path):
            print(f"Path {path} does not exist. Using current directory.")
            return os.getcwd()
        
        return os.path.abspath(path)
    except EOFError:
        return os.getcwd()

def main():
    parser = argparse.ArgumentParser(description='Анализ и визуализация зависимостей в проекте')
    parser.add_argument('--output', type=str, default='code_graph.html',
                       help='Имя выходного HTML файла (по умолчанию: code_graph.html)')
    parser.add_argument('--include-external', action='store_true',
                       help='Включить внешние зависимости')
    parser.add_argument('--extensions', type=str, default='.py,.js,.html,.css',
                       help='Расширения файлов для анализа (через запятую)')
    
    args = parser.parse_args()
    
    # Запрашиваем путь к проекту
    project_path = get_project_path()
    print(f"Анализ проекта в директории: {project_path}")
    
    # Конвертируем строку с расширениями в список
    extensions = args.extensions.split(',')
    
    # Создаем анализатор
    analyzer = ProjectAnalyzer(
        project_path=project_path,
        file_extensions=extensions,
        include_external=args.include_external
    )
    
    # Запускаем анализ
    print("Анализ проекта...")
    dependencies = analyzer.analyze()
    
    # Создаем визуализатор
    print("Создание графа...")
    visualizer = GraphVisualizer(dependencies)
    visualizer.create_graph()
    
    # Сохраняем результат
    output_path = os.path.join(project_path, args.output)
    print(f"Сохранение результата в {output_path}...")
    visualizer.save(args.output)
    
    print(f"Готово! Откройте {output_path} в веб-браузере для просмотра графа.")

if __name__ == "__main__":
    main()
