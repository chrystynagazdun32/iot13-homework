import os
import json
import logging
from functools import wraps


class FileHandlerException(Exception):
    pass


class FileCorrupted(FileHandlerException):
    def __init__(self, filename):
        super().__init__(f"Помилка: Файл '{filename}' пошкоджений або має неправильний формат JSON.")


class FileNotFound(FileHandlerException):
    def __init__(self, filename):
        super().__init__(f"Помилка: Файл '{filename}' не знайдено.")


def logged(mode="console", log_file="file_handler.log"):
    """Декоратор для логування методів класу."""
    
    logger = logging.getLogger('FileHandlerLogger')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        if mode == "file":
            handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        else:
            handler = logging.StreamHandler()

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            operation = func.__name__
            filename = getattr(self, 'file_path', 'N/A')

            logger.info(f"Спроба: {operation} з файлом {filename}.")

            try:
                result = func(self, *args, **kwargs)
                logger.info(f"Успіх: {operation} завершено для {filename}.")
                return result
            except FileHandlerException as e:
                logger.error(f"Виняток: {operation} для {filename}. Помилка: {e}")
                raise
            except Exception as e:
                logger.critical(
                    f"Критична помилка: {operation} для {filename}. Помилка: {e}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


class JsonFileHandler:

    def __init__(self, file_path):
        self.file_path = file_path
        
        if not os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            except Exception as e:
                raise FileHandlerException(
                    f"Неможливо створити файл '{self.file_path}': {e}"
                )

    @logged()
    def read_file(self):
        if not os.path.exists(self.file_path):
            raise FileNotFound(self.file_path)

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise FileCorrupted(self.file_path)
        except Exception:
            raise FileHandlerException(
                f"Невідома помилка при читанні файлу '{self.file_path}'."
            )

    @logged()
    def write_file(self, data, overwrite=True):
        if not os.path.exists(self.file_path):
            raise FileNotFound(self.file_path)

        try:
            if overwrite:
                content_to_write = data
            else:
                current_data = self.read_file()

                if isinstance(current_data, dict) and isinstance(data, dict):
                    current_data.update(data)
                    content_to_write = current_data

                elif isinstance(current_data, list) and isinstance(data, list):
                    current_data.extend(data)
                    content_to_write = current_data

                elif not current_data:
                    content_to_write = data

                else:
                    raise FileHandlerException(
                        "Помилка дозапису: невідповідність типів даних (потрібно dict->dict або list->list)."
                    )

            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(content_to_write, f, indent=4, ensure_ascii=False)

        except FileHandlerException:
            raise
        except Exception as e:
            raise FileHandlerException(
                f"Невідома помилка при записі у файл '{self.file_path}'. Помилка: {e}"
            )

    @logged()
    def append_file(self, data):
        return self.write_file(data, overwrite=False)
