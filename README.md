# API autotests

API тесты

## Зависимости

* Python: 3.11+
* Pip: 22.3.1+
* Poetry 1.3.2+


## Инструкции:


---

## Использование script.py

#### Установка

* Установка poetry
    ```shell
    pip install poetry
    ```
  
* Зависимости для запуска тестов
    ```shell
    python script.py install
    ```

* Зависимости для написания тестов
    ```shell
    python script.py install --all
    ```

#### Форматирование кода

```shell
python script.py format
```

#### Запуск линтеров

```shell
python script.py lint
```

#### Генерация .pyi файлов

```shell
python script.py pyi
```
