# Test-Bank

API-автотесты для учебного банковского приложения на **Python + pytest + requests + pydantic**. Проект построен как расширяемый фреймворк: эндпоинты описаны декларативно, запросы и ответы типизированы pydantic-моделями, тестовые данные генерируются автоматически, а созданные в тестах пользователи удаляются после прогона.

## Стек

| Инструмент | Назначение |
|---|---|
| Python 3.10+ | язык тестов |
| pytest | запуск тестов, фикстуры, параметризация, маркеры |
| requests | HTTP-клиент |
| pydantic v2 | модели запросов/ответов и валидация ответов API |
| rstr | генерация строк по регулярным выражениям |

## Тестируемое API

Базовый URL задаётся в `resources/urls.properties`:

```properties
backendUrl=http://localhost:4111/api
```

Покрытые эндпоинты (`src/main/api/foundation/endpoint.py`):

| Константа | Метод | Путь | Модель запроса | Модель ответа |
|---|---|---|---|---|
| `ADMIN_CREATE_USER` | POST | `/admin/create` | `CreateUserRequest` | `CreateUserResponse` |
| `ADMIN_GET_USERS` | GET | `/admin/users` | — | `List[CreateUserResponse]` |
| `ADMIN_DELETE_USER` | DELETE | `/admin/users/{id}` | — | — |
| `LOGIN_USER` | POST | `/auth/token/login` | `LoginUserRequest` | `LoginUserResponse` |
| `CREATE_ACCOUNT` | POST | `/account/create` | — | `CreateAccountResponse` |

Авторизация — Bearer-токен, который получается через `/auth/token/login`. Админские запросы по умолчанию выполняются от пользователя `admin` / `123456`.

## Структура проекта

```
Test-Bank/
├── conftest.py                  # подключает фикстуры из src/main/api/fixtures
├── pytest.ini                   # маркер api, pythonpath = .
├── resources/
│   └── urls.properties          # адрес бэкенда
└── src/main/api/
    ├── configs/config.py        # Config — синглтон, читает urls.properties
    ├── foundation/              # ядро фреймворка
    │   ├── endpoint.py          # Endpoint (Enum): URL + модели запроса/ответа
    │   ├── http_requester.py    # базовый класс: спецификации и сборка URL
    │   ├── crud_endpoint.py     # протокол CRUD (post / get / delete)
    │   └── requesters/
    │       ├── crud_requester.py           # «сырые» запросы, возвращает Response
    │       └── validate_crud_requester.py  # то же + валидация ответа в pydantic-модель
    ├── specs/
    │   ├── request_specs.py     # заголовки: базовые, с токеном, без авторизации
    │   └── response_specs.py    # проверки статус-кода: 200, 201, 400, 401, 403, 404
    ├── models/                  # pydantic-модели запросов и ответов
    ├── generators/
    │   ├── creation_rule.py     # CreationRule(regex=...) — правило генерации поля
    │   └── model_generator.py   # RandomModelGenerator — заполняет модель случайными данными
    ├── steps/                   # бизнес-шаги
    │   ├── base_steps.py
    │   ├── admin_steps.py       # создать / удалить / получить пользователей, логин
    │   └── user_steps.py        # создать счёт
    ├── classes/api_manager.py   # ApiManager — единая точка доступа к admin_steps и user_steps
    ├── fixtures/                # pytest-фикстуры
    │   ├── object_fixture.py    # created_obj + удаление созданных пользователей после теста
    │   ├── api_fixture.py       # api_manager
    │   └── user_fixture.py      # create_user_request — готовый пользователь в системе
    ├── requests/                # старая реализация requester'ов (до перехода на foundation)
    └── tests/                   # тесты
```

## Архитектура

Тест обращается только к шагам через `ApiManager`, а вся работа с HTTP спрятана ниже:

```
test → ApiManager → AdminSteps / UserSteps → ValidateCrudRequester / CrudRequester → Endpoint + Specs → API
```

- **Endpoint** — один enum на все эндпоинты. Чтобы добавить новый, достаточно описать URL и модели, писать отдельный класс запроса не нужно.
- **Request / Response Specs** — заголовки и ожидаемый статус передаются в requester как параметры, поэтому один и тот же эндпоинт проверяется и в позитивных, и в негативных сценариях.
- **CrudRequester** возвращает `requests.Response` и нужен для негативных проверок. **ValidateCrudRequester** дополнительно превращает JSON ответа в pydantic-модель через `TypeAdapter`, так что несоответствие контракту сразу роняет тест.
- **RandomModelGenerator** обходит аннотации модели и генерирует значения: по регулярке из `CreationRule`, если она задана, иначе — по типу поля. Например, для `CreateUserRequest` username соответствует `^[a-zA-Z0-9]{3,15}$`, а пароль — заданному шаблону со спецсимволами.
- **Очистка данных** — каждый созданный пользователь попадает в список `created_obj`, и после теста фикстура удаляет его через `DELETE /admin/users/{id}`.

## Тесты

| Файл | Тест | Что проверяет |
|---|---|---|
| `create_user_test.py` | `test_create_user_valid` | Админ создаёт пользователя со сгенерированными данными, в ответе совпадают username и role |
| | `test_create_user_invalid` (9 наборов) | Невалидные username/password возвращают 400: кириллица, слишком короткий логин, спецсимволы в логине, кириллица в пароле, короткий пароль, нет заглавных, нет строчных, нет цифр, нет спецсимволов |
| `user_login_test.py` | `test_login_admin` | Логин админа, роль `ROLE_ADMIN` |
| | `test_login_user` | Логин созданного пользователя, роль `ROLE_USER` |
| `create_account_test.py` | `test_create_account` | Пользователь создаёт счёт, стартовый баланс равен 0 |
| `admin_users_test.py` | — | заготовка под тесты админских эндпоинтов |

Все тесты помечены маркером `api`.

## Запуск

### 1. Поднять бэкенд

Тесты работают с приложением, запущенным локально по адресу `http://localhost:4111/api`, где есть администратор `admin` / `123456`. Если бэкенд доступен по другому адресу, поменяйте `backendUrl` в `resources/urls.properties`.

### 2. Клонировать репозиторий и установить зависимости

```bash
git clone https://github.com/AndrewShabailov/Test-Bank.git
cd Test-Bank

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Запустить тесты

Команды выполняются из корня проекта: `pytest.ini` добавляет корень в `pythonpath`, поэтому импорты вида `src.main.api...` работают без дополнительной настройки.

```bash
# все тесты
pytest -v

# только API-тесты по маркеру
pytest -v -m api

# один файл / один класс / один тест
pytest src/main/api/tests/create_user_test.py -v
pytest src/main/api/tests/create_user_test.py::TestCreateUser -v
pytest src/main/api/tests/create_user_test.py::TestCreateUser::test_create_user_valid -v

# с выводом print и логов
pytest -v -s --log-cli-level=INFO
```

## Как добавить новый тест

1. Описать модели запроса и ответа в `models/`; для генерируемых полей указать `Annotated[str, CreationRule(regex=...)]`.
2. Добавить эндпоинт в `Endpoint`.
3. Добавить метод в `AdminSteps` или `UserSteps`: `ValidateCrudRequester` для позитивного сценария, `CrudRequester` с нужной `ResponseSpecs` — для негативного.
4. Если в тесте создаются сущности, добавить их в `created_obj` и описать удаление в `object_fixture.py`.
5. Написать тест в `tests/`, используя фикстуры `api_manager` и `create_user_request`.
