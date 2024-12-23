from analyzer import ProjectAnalyzer
import json

def main():
    # Создаем экземпляр анализатора
    analyzer = ProjectAnalyzer(include_external=False)
    
    # Запускаем анализ
    dependencies = analyzer.analyze()
    
    # Выводим результаты в консоль
    print(json.dumps(dependencies, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
