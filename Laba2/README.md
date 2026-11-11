# Лабораторная работа №2. HTTP-методы: обработка GET, POST, PUT, DELETE

<div align="center">

**Студент:** Кулябцев Б.М.
**Группа:** ПИЖ-б-о-25-2
**Вариант:** 5 — сущность «Фильмы» (`movies`)
**Уровень сложности:** продвинутый (комплект 3)
**Технологии:** Node.js, Express 5, Postman

</div>

---

## 📑 Содержание

1. [Цель работы](#-цель-работы)
2. [Теоретическое обоснование](#-теоретическое-обоснование)
3. [Структура проекта и запуск](#-структура-проекта-и-запуск)
4. [Выполнение практического примера](#-выполнение-практического-примера)
5. [Выполнение индивидуального задания](#-выполнение-индивидуального-задания)
6. [Тестирование в Postman](#-тестирование-в-postman)
7. [Ответы на контрольные вопросы](#-ответы-на-контрольные-вопросы)
8. [Вывод](#-вывод)
9. [Список использованных источников](#-список-использованных-источников)

---

## 🎯 Цель работы

Освоить обработку HTTP-методов (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) в Express, научиться реализовывать CRUD-операции над коллекцией объектов, хранящейся в памяти сервера, возвращать корректные HTTP-коды ответов (`200`, `201`, `204`, `400`, `404`, `500`) и тестировать API с помощью Postman.

---

## 📚 Теоретическое обоснование

### CRUD

**CRUD** — четыре базовые операции над данными:

| Операция | Расшифровка | HTTP-метод | SQL-аналог |
| -------- | ----------- | ---------- | ---------- |
| **C**reate | Создание | `POST` | `INSERT` |
| **R**ead | Чтение | `GET` | `SELECT` |
| **U**pdate | Обновление | `PUT` / `PATCH` | `UPDATE` |
| **D**elete | Удаление | `DELETE` | `DELETE` |

### HTTP-методы

| Метод | Назначение | Тело запроса | Идемпотентность | Безопасность | Коды ответов |
| ----- | ---------- | :----------: | :-------------: | :----------: | ------------ |
| `GET` | получение данных | нет | да | да | `200`, `404` |
| `POST` | создание ресурса | да | нет | нет | `201`, `400` |
| `PUT` | полная замена ресурса | да | да | нет | `200`, `404`, `400` |
| `PATCH` | частичное обновление | да | нет* | нет | `200`, `404`, `400` |
| `DELETE` | удаление ресурса | нет | да | нет | `200`, `204`, `404` |

\* `PATCH` в общем случае не гарантирует идемпотентность.

### Коды состояния HTTP

| Код | Название | Когда используется |
| :-: | -------- | ------------------ |
| `200` | OK | успешный `GET`, `PUT`, `PATCH`, `DELETE` с телом |
| `201` | Created | успешный `POST` (ресурс создан) |
| `204` | No Content | успешный `DELETE` (без тела ответа) |
| `400` | Bad Request | ошибка в данных запроса |
| `404` | Not Found | ресурс или маршрут не найден |
| `500` | Internal Server Error | ошибка на сервере |

### Хранение данных в памяти

В работе не используется база данных: данные лежат в массиве в оперативной памяти сервера.

* **Плюсы:** простота, не нужна установка БД, быстрый доступ.
* **Минусы:** данные теряются при перезапуске сервера, не подходит для production.

---

## 🗂️ Структура проекта и запуск

```text
Laba2/
├── app.js                                    # сервер: индивидуальное задание (фильмы, порт 3000)
├── practice-app.js                           # сервер: практический пример (товары, порт 3001)
├── package.json
├── package-lock.json
├── access.log                                # журнал запросов (создаётся при работе сервера)
├── Lab2_CRUD_API.postman_collection.json     # коллекция запросов Postman
├── Local_Development.postman_environment.json# окружение Postman
├── README.md
└── screenshots/
```

**Установка и запуск:**

```bash
cd Laba2
npm install
npm run dev          # сервер фильмов: http://localhost:3000  (nodemon)
npm run practice     # практический пример: http://localhost:3001
```

![Установка зависимостей и запуск сервера](screenshots/00_install_and_start.png)

---

## 🧪 Выполнение практического примера

Практический пример из методички — CRUD для товаров (`items`) с хранением в массиве. Реализованы пять маршрутов (`GET /items`, `GET /items/:id`, `POST /items`, `PUT /items/:id`, `DELETE /items/:id`) и обработка `404`. Пример запускается на порту `3001`, чтобы не конфликтовать с сервером индивидуального задания.

<details>
<summary>📄 Код <code>practice-app.js</code></summary>

```javascript
// Практический пример из методички: CRUD по товарам (items).
// Запускается на порту 3001, чтобы не конфликтовать с app.js (фильмы, порт 3000).
const express = require('express');

const app = express();
const port = 3001;

// Middleware для парсинга JSON из тела запроса
app.use(express.json());

// Middleware для логирования запросов
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

// ============ ХРАНИЛИЩЕ ДАННЫХ В ПАМЯТИ ============
let items = [
  { id: 1, name: 'Товар 1', price: 100, quantity: 5 },
  { id: 2, name: 'Товар 2', price: 200, quantity: 3 },
  { id: 3, name: 'Товар 3', price: 300, quantity: 10 }
];

// Счётчик для генерации новых ID
let nextId = 4;

// ============ CRUD-ОПЕРАЦИИ ============

// GET /items — получить все элементы
app.get('/items', (req, res) => {
  res.json({
    count: items.length,
    items: items
  });
});

// GET /items/:id — получить один элемент
app.get('/items/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const item = items.find(i => i.id === id);

  if (!item) {
    return res.status(404).json({ error: 'Элемент не найден' });
  }
  res.json(item);
});

// POST /items — создать новый элемент
app.post('/items', (req, res) => {
  const { name, price, quantity } = req.body || {};

  // Валидация: обязательные поля
  if (!name || price === undefined) {
    return res.status(400).json({ error: 'Поля name и price обязательны' });
  }

  const newItem = {
    id: nextId++,
    name: name,
    price: price,
    quantity: quantity || 0
  };
  items.push(newItem);

  // 201 Created — ресурс создан
  res.status(201).json(newItem);
});

// PUT /items/:id — обновить элемент
app.put('/items/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const index = items.findIndex(i => i.id === id);

  if (index === -1) {
    return res.status(404).json({ error: 'Элемент не найден' });
  }

  const { name, price, quantity } = req.body || {};

  items[index] = {
    id: id,
    name: name || items[index].name,
    price: price !== undefined ? price : items[index].price,
    quantity: quantity !== undefined ? quantity : items[index].quantity
  };

  res.json(items[index]);
});

// DELETE /items/:id — удалить элемент
app.delete('/items/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const index = items.findIndex(i => i.id === id);

  if (index === -1) {
    return res.status(404).json({ error: 'Элемент не найден' });
  }

  const deletedItem = items.splice(index, 1)[0];

  // 200 OK с удалённым элементом
  res.json({
    message: 'Элемент удалён',
    deleted: deletedItem
  });
});

// ============ ОБРАБОТКА 404 ============
app.use((req, res) => {
  res.status(404).json({ error: 'Маршрут не найден' });
});

// ============ ЗАПУСК СЕРВЕРА ============
app.listen(port, () => {
  console.log(`Сервер запущен на http://localhost:${port}`);
});
```

</details>

### Результаты запросов

**GET /items** — получить все товары, `200 OK`

![GET /items](screenshots/practice_01_get_all.png)

**GET /items/1** — один товар, `200 OK`

![GET /items/1](screenshots/practice_02_get_by_id.png)

**GET /items/999** — несуществующий товар, `404 Not Found`

![GET /items/999](screenshots/practice_03_get_404.png)

**POST /items** — создание товара, `201 Created`

![POST /items](screenshots/practice_04_post.png)

**PUT /items/1** — обновление товара, `200 OK`

![PUT /items/1](screenshots/practice_05_put.png)

**DELETE /items/{id}** — удаление товара, `200 OK`

![DELETE /items/{id}](screenshots/practice_06_delete.png)

---

## 🎬 Выполнение индивидуального задания

**Вариант 5, продвинутый уровень.**

| Параметр | Значение |
| -------- | -------- |
| Сущность | Фильмы (`movies`) |
| Поля | `id`, `title`, `year`, `director`, `rating` |
| Поиск по | `title` |
| Статистика | количество и средний рейтинг |
| Связи | фильмы того же режиссёра |

### Реализованные эндпоинты

| Метод | URL | Описание | Успех | Ошибки |
| ----- | --- | -------- | :---: | :----: |
| `GET` | `/movies` | список; `?search=`, `?sort=&order=`, `?page=&limit=` | `200` | `400` |
| `GET` | `/movies/:id` | один фильм | `200` | `400`, `404` |
| `POST` | `/movies` | создание | `201` | `400` |
| `PUT` | `/movies/:id` | полная замена (нужны все поля) | `200` | `400`, `404` |
| `PATCH` | `/movies/:id` | частичное обновление | `200` | `400`, `404` |
| `DELETE` | `/movies/:id` | удаление | `204` | `400`, `404` |
| `DELETE` | `/movies` | удалить все фильмы | `200` | — |
| `POST` | `/movies/bulk` | массовое создание (массив, «всё или ничего») | `201` | `400` |
| `GET` | `/movies/stats` | статистика: `count`, `avg_rating`, `min_rating`, `max_rating` | `200` | — |
| `GET` | `/movies/:id/related` | фильмы того же режиссёра | `200` | `400`, `404` |

### Выполнение требований по уровням

| Требование | Как реализовано |
| ---------- | --------------- |
| **Базовый:** CRUD + `404` | пять маршрутов, `404` при отсутствии фильма |
| **Средний:** валидация | `title`, `director` — непустые строки; `year` — целое число (1888 … текущий год + 5); `rating` — число от 0 до 10; ошибки → `400` |
| **Средний:** поиск, сортировка, пагинация | `?search=`, `?sort=` (только `id`, `title`, `year`, `director`, `rating`), `?order=asc\|desc`, `?page=`, `?limit=` (1…100); неверные значения → `400` |
| **Средний:** коды ответов | `201` при `POST`, `204` при `DELETE`, `400` при неверных данных |
| **Продвинутый:** `PATCH` | обновляются только переданные поля, значения валидируются |
| **Продвинутый:** массовые операции | `DELETE /movies`, `POST /movies/bulk` |
| **Продвинутый:** `stats`, `related` | статистика и фильмы того же режиссёра |
| **Продвинутый:** логирование | middleware пишет `метод`, `URL` и `код ответа` в консоль и в файл `access.log` |
| **Продвинутый:** глобальный обработчик ошибок | middleware с четырьмя аргументами в конце цепочки: `500` для неожиданных ошибок, `400` для некорректного JSON, `413` для слишком большого тела |

### Важные детали реализации

* Маршруты `/movies/stats` и `/movies/bulk` объявлены **до** `/movies/:id`, иначе Express принял бы `stats` за значение параметра `:id`.
* Параметр `:id` проверяется один раз через `app.param('id', …)`: нецелое значение → `400`, несуществующий id → `404`.
* Тело запроса ограничено `express.json({ limit: '100kb' })`.
* В Express 5 при пустом теле `req.body` равен `undefined`, поэтому валидатор сначала проверяет, что тело — JSON-объект.
* Счётчик `nextId` только растёт, поэтому идентификаторы не повторяются; он сбрасывается лишь при `DELETE /movies`.
* Для проверки ответа `500` добавлен служебный маршрут `GET /error-test`, который намеренно выбрасывает ошибку.

<details>
<summary>📄 Код <code>app.js</code></summary>

```javascript
const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const port = 3000;

// ============ ЛОГИРОВАНИЕ В ФАЙЛ access.log ============
const logStream = fs.createWriteStream(path.join(__dirname, 'access.log'), { flags: 'a' });

const writeLog = (line) => {
  const entry = `[${new Date().toISOString()}] ${line}`;
  console.log(entry);
  logStream.write(entry + '\n');
};

// Логер стоит первым, чтобы в журнал попадали и запросы с ошибками (в том числе с битым JSON)
app.use((req, res, next) => {
  res.on('finish', () => writeLog(`${req.method} ${req.originalUrl} -> ${res.statusCode}`));
  next();
});

// Middleware для парсинга JSON (с ограничением размера тела запроса)
app.use(express.json({ limit: '100kb' }));

// ============ ХРАНИЛИЩЕ ДАННЫХ В ПАМЯТИ (ФИЛЬМЫ) ============
// Поля по варианту 5: id, title, year, director, rating
let movies = [
  { id: 1, title: 'Начало', year: 2010, director: 'Кристофер Нолан', rating: 8.8 },
  { id: 2, title: 'Тёмный рыцарь', year: 2008, director: 'Кристофер Нолан', rating: 9.0 },
  { id: 3, title: 'Интерстеллар', year: 2014, director: 'Кристофер Нолан', rating: 8.6 },
  { id: 4, title: 'Криминальное чтиво', year: 1994, director: 'Квентин Тарантино', rating: 8.9 },
  { id: 5, title: 'Побег из Шоушенка', year: 1994, director: 'Фрэнк Дарабонт', rating: 9.3 }
];

// Счётчик для генерации ID (id никогда не переиспользуются, пока не вызван DELETE /movies)
let nextId = 6;

// ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
const MIN_YEAR = 1888; // первый в истории фильм
const MAX_YEAR = new Date().getFullYear() + 5;
const SORT_FIELDS = ['id', 'title', 'year', 'director', 'rating'];

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
const isNonEmptyString = (v) => typeof v === 'string' && v.trim() !== '';

// Валидация фильма. isPatch = true -> проверяются только переданные поля
const validateMovie = (body, isPatch = false) => {
  if (!isObject(body)) return ['Тело запроса должно быть JSON-объектом'];

  const errors = [];
  const check = (field) => !isPatch || body[field] !== undefined;

  if (check('title') && !isNonEmptyString(body.title)) {
    errors.push('title: обязательное поле, непустая строка');
  }
  if (check('year') && !(Number.isInteger(body.year) && body.year >= MIN_YEAR && body.year <= MAX_YEAR)) {
    errors.push(`year: обязательное поле, целое число от ${MIN_YEAR} до ${MAX_YEAR}`);
  }
  if (check('director') && !isNonEmptyString(body.director)) {
    errors.push('director: обязательное поле, непустая строка');
  }
  if (check('rating') && !(typeof body.rating === 'number' && Number.isFinite(body.rating) && body.rating >= 0 && body.rating <= 10)) {
    errors.push('rating: обязательное поле, число от 0 до 10');
  }
  return errors;
};

const buildMovie = (id, data) => ({
  id,
  title: data.title.trim(),
  year: data.year,
  director: data.director.trim(),
  rating: data.rating
});

// Проверка параметра :id во всех маршрутах вида /movies/:id...
app.param('id', (req, res, next, value) => {
  if (!/^\d+$/.test(value)) {
    return res.status(400).json({ error: 'id должен быть целым неотрицательным числом' });
  }
  req.movieId = Number(value);
  next();
});

// ============ GET /movies — список с поиском, сортировкой и пагинацией ============
app.get('/movies', (req, res) => {
  const { search, sort, order, page, limit } = req.query;
  const errors = [];

  if (search !== undefined && typeof search !== 'string') errors.push('search должен быть строкой');
  if (sort !== undefined && !SORT_FIELDS.includes(sort)) {
    errors.push(`sort должен быть одним из: ${SORT_FIELDS.join(', ')}`);
  }
  if (order !== undefined && !['asc', 'desc'].includes(order)) errors.push('order должен быть asc или desc');
  if (page !== undefined && !(/^\d+$/.test(page) && Number(page) >= 1)) errors.push('page должен быть целым числом >= 1');
  if (limit !== undefined && !(/^\d+$/.test(limit) && Number(limit) >= 1 && Number(limit) <= 100)) {
    errors.push('limit должен быть целым числом от 1 до 100');
  }
  if (errors.length > 0) return res.status(400).json({ errors });

  let result = [...movies];

  // 1. Поиск по названию
  if (search) {
    const s = search.toLowerCase();
    result = result.filter((m) => m.title.toLowerCase().includes(s));
  }

  // 2. Сортировка
  if (sort) {
    const dir = order === 'desc' ? -1 : 1;
    result.sort((a, b) => {
      if (typeof a[sort] === 'string') return a[sort].localeCompare(b[sort], 'ru') * dir;
      return (a[sort] - b[sort]) * dir;
    });
  }

  // 3. Пагинация
  const pageNum = page ? Number(page) : 1;
  const limitNum = limit ? Number(limit) : 10;
  const start = (pageNum - 1) * limitNum;

  res.json({
    count: result.length,
    page: pageNum,
    limit: limitNum,
    total_pages: Math.ceil(result.length / limitNum),
    movies: result.slice(start, start + limitNum)
  });
});

// ============ ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ (объявлены ДО /movies/:id!) ============

// GET /movies/stats — статистика
app.get('/movies/stats', (req, res) => {
  if (movies.length === 0) {
    return res.json({ count: 0, avg_rating: null, min_rating: null, max_rating: null });
  }
  const ratings = movies.map((m) => m.rating);
  const avg = ratings.reduce((sum, r) => sum + r, 0) / ratings.length;

  res.json({
    count: movies.length,
    avg_rating: parseFloat(avg.toFixed(2)),
    min_rating: Math.min(...ratings),
    max_rating: Math.max(...ratings)
  });
});

// POST /movies/bulk — массовое создание (всё или ничего)
app.post('/movies/bulk', (req, res) => {
  const items = req.body;
  if (!Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: 'Ожидается непустой массив фильмов' });
  }
  if (items.length > 100) {
    return res.status(400).json({ error: 'За один запрос можно создать не более 100 фильмов' });
  }

  // Сначала валидируем все элементы, и только потом создаём
  const details = [];
  items.forEach((item, index) => {
    const errors = validateMovie(item);
    if (errors.length > 0) details.push({ index, errors });
  });
  if (details.length > 0) {
    return res.status(400).json({ error: 'Ошибка валидации фильмов', details });
  }

  const created = items.map((item) => buildMovie(nextId++, item));
  movies.push(...created);
  res.status(201).json({ message: `Создано фильмов: ${created.length}`, movies: created });
});

// DELETE /movies — удалить все
app.delete('/movies', (req, res) => {
  const deleted = movies.length;
  movies = [];
  nextId = 1;
  res.json({ message: 'Все фильмы удалены', deleted });
});

// ============ CRUD ============

// GET /movies/:id — один фильм
app.get('/movies/:id', (req, res) => {
  const movie = movies.find((m) => m.id === req.movieId);
  if (!movie) return res.status(404).json({ error: 'Фильм не найден' });
  res.json(movie);
});

// GET /movies/:id/related — фильмы того же режиссёра
app.get('/movies/:id/related', (req, res) => {
  const movie = movies.find((m) => m.id === req.movieId);
  if (!movie) return res.status(404).json({ error: 'Фильм не найден' });

  const related = movies.filter((m) => m.director === movie.director && m.id !== movie.id);
  res.json({
    movie: movie.title,
    director: movie.director,
    related_movies: related
  });
});

// POST /movies — создание
app.post('/movies', (req, res) => {
  const errors = validateMovie(req.body);
  if (errors.length > 0) return res.status(400).json({ errors });

  const newMovie = buildMovie(nextId++, req.body);
  movies.push(newMovie);
  res.status(201).json(newMovie);
});

// PUT /movies/:id — полная замена (нужны все поля)
app.put('/movies/:id', (req, res) => {
  const index = movies.findIndex((m) => m.id === req.movieId);
  if (index === -1) return res.status(404).json({ error: 'Фильм не найден' });

  const errors = validateMovie(req.body);
  if (errors.length > 0) return res.status(400).json({ errors });

  movies[index] = buildMovie(req.movieId, req.body);
  res.json(movies[index]);
});

// PATCH /movies/:id — частичное обновление (только переданные поля)
app.patch('/movies/:id', (req, res) => {
  const index = movies.findIndex((m) => m.id === req.movieId);
  if (index === -1) return res.status(404).json({ error: 'Фильм не найден' });

  const body = req.body;
  if (isObject(body) && !SORT_FIELDS.some((f) => f !== 'id' && body[f] !== undefined)) {
    return res.status(400).json({ error: 'Передайте хотя бы одно поле: title, year, director или rating' });
  }
  const errors = validateMovie(body, true);
  if (errors.length > 0) return res.status(400).json({ errors });

  const updated = { ...movies[index] };
  for (const field of ['title', 'year', 'director', 'rating']) {
    if (body[field] !== undefined) {
      updated[field] = typeof body[field] === 'string' ? body[field].trim() : body[field];
    }
  }
  movies[index] = updated;
  res.json(updated);
});

// DELETE /movies/:id — удаление (204 No Content, без тела)
app.delete('/movies/:id', (req, res) => {
  const index = movies.findIndex((m) => m.id === req.movieId);
  if (index === -1) return res.status(404).json({ error: 'Фильм не найден' });

  movies.splice(index, 1);
  res.status(204).send();
});

// Тестовый маршрут для проверки глобального обработчика ошибок (500)
app.get('/error-test', () => {
  throw new Error('Тестовая ошибка сервера');
});

// ============ ОБРАБОТКА ОШИБОК ============

// 404 — маршрут не найден
app.use((req, res) => {
  res.status(404).json({ error: 'Маршрут не найден' });
});

// Глобальный обработчик ошибок (должен быть последним и иметь 4 аргумента)
app.use((err, req, res, next) => {
  if (res.headersSent) return next(err);

  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: 'Некорректный JSON в теле запроса' });
  }
  if (err.type === 'entity.too.large') {
    return res.status(413).json({ error: 'Тело запроса слишком большое' });
  }

  console.error(err.stack);
  writeLog(`[ERROR] ${req.method} ${req.originalUrl} - ${err.message}`);
  res.status(500).json({ error: 'Внутренняя ошибка сервера' });
});

app.listen(port, () => {
  console.log(`Сервер запущен на http://localhost:${port}`);
});
```

</details>

### Результаты запросов

**GET /movies** — список всех фильмов, `200 OK`

![GET /movies](screenshots/movies_01_get_all.png)

**GET /movies/1** — один фильм, `200 OK`

![GET /movies/1](screenshots/movies_02_get_by_id.png)

**GET /movies?search=нач** — поиск по названию, `200 OK`

![GET /movies?search=нач](screenshots/movies_03_search.png)

**GET /movies?sort=rating&order=desc** — сортировка по рейтингу, `200 OK`

![GET /movies?sort=rating&order=desc](screenshots/movies_04_sort.png)

**GET /movies?page=2&limit=2** — пагинация, `200 OK`

![GET /movies?page=2&limit=2](screenshots/movies_05_pagination.png)

**GET /movies/stats** — статистика (количество, средний рейтинг), `200 OK`

![GET /movies/stats](screenshots/movies_06_stats.png)

**GET /movies/1/related** — фильмы того же режиссёра, `200 OK`

![GET /movies/1/related](screenshots/movies_07_related.png)

**POST /movies** — создание фильма, `201 Created`

![POST /movies](screenshots/movies_08_post.png)

**POST /movies/bulk** — массовое создание, `201 Created`

![POST /movies/bulk](screenshots/movies_09_bulk.png)

**PUT /movies/1** — полное обновление, `200 OK`

![PUT /movies/1](screenshots/movies_10_put.png)

**PATCH /movies/2** — частичное обновление (только `rating`), `200 OK`

![PATCH /movies/2](screenshots/movies_11_patch.png)

**DELETE /movies/6** — удаление фильма, `204 No Content` (без тела)

![DELETE /movies/6](screenshots/movies_12_delete.png)

**DELETE /movies** — удаление всех фильмов, `200 OK`

![DELETE /movies](screenshots/movies_13_delete_all.png)

### Обработка ошибок

**GET /movies/999** — несуществующий фильм, `404 Not Found`

![GET /movies/999](screenshots/errors_01_404_movie.png)

**GET /movies/abc** — некорректный id, `400 Bad Request`

![GET /movies/abc](screenshots/errors_02_400_id.png)

**GET /unknown** — несуществующий маршрут, `404 Not Found`

![GET /unknown](screenshots/errors_03_404_route.png)

**POST /movies (пустое тело `{}`)** — не переданы обязательные поля, `400 Bad Request`

![POST /movies (пустое тело `{}`)](screenshots/errors_04_400_empty.png)

**POST /movies (неверные типы)** — `year` и `rating` — строки, `400 Bad Request`

![POST /movies (неверные типы)](screenshots/errors_05_400_types.png)

**POST /movies (rating = 11)** — значение вне допустимого диапазона, `400 Bad Request`

![POST /movies (rating = 11)](screenshots/errors_06_400_range.png)

**POST /movies (битый JSON)** — синтаксическая ошибка в JSON, `400 Bad Request`

![POST /movies (битый JSON)](screenshots/errors_07_400_bad_json.png)

**POST /movies/bulk (неверный элемент)** — один из фильмов невалиден, `400 Bad Request`

![POST /movies/bulk (неверный элемент)](screenshots/errors_08_400_bulk.png)

**PUT /movies/999** — обновление несуществующего фильма, `404 Not Found`

![PUT /movies/999](screenshots/errors_09_404_put.png)

**PUT /movies/1 (неполное тело)** — для PUT нужны все поля, `400 Bad Request`

![PUT /movies/1 (неполное тело)](screenshots/errors_10_400_put.png)

**PATCH /movies/999** — `404 Not Found`

![PATCH /movies/999](screenshots/errors_11_404_patch.png)

**PATCH /movies/1 (пустое тело)** — `400 Bad Request`

![PATCH /movies/1 (пустое тело)](screenshots/errors_12_400_patch.png)

**DELETE /movies/999** — `404 Not Found`

![DELETE /movies/999](screenshots/errors_13_404_delete.png)

**GET /movies?page=0&limit=abc** — неверные параметры пагинации, `400 Bad Request`

![GET /movies?page=0&limit=abc](screenshots/errors_14_400_pagination.png)

**GET /movies?sort=password** — недопустимое поле сортировки, `400 Bad Request`

![GET /movies?sort=password](screenshots/errors_15_400_sort.png)

**GET /error-test** — глобальный обработчик ошибок, `500 Internal Server Error`

![GET /error-test](screenshots/errors_16_500.png)

### Журнал запросов `access.log`

Каждый запрос записывается в файл вместе с кодом ответа, а необработанные ошибки — с пометкой `[ERROR]`.

![Содержимое access.log](screenshots/access_log.png)

---

## 📮 Тестирование в Postman

Создана коллекция **Lab2 CRUD API** и окружение **Local Development** (`base_url = http://localhost:3000`, `practice_url = http://localhost:3001`). Коллекция экспортирована в формате *Collection v2.1* и лежит в этой папке: [`Lab2_CRUD_API.postman_collection.json`](./Lab2_CRUD_API.postman_collection.json).

### Структура коллекции

```text
Lab2 CRUD API
├── Practice (items, порт 3001)
│   ├── GET All Items
│   ├── GET Item by ID
│   ├── POST Create Item
│   ├── PUT Update Item
│   ├── DELETE Delete Item
│   └── GET Nonexistent Item (404)
├── Setup (сброс данных)
│   ├── DELETE All Movies (reset)
│   └── POST Seed Movies
├── Movies (вариант 5)
│   ├── GET All Movies
│   ├── GET Movie by ID
│   ├── GET Search by title
│   ├── GET Sort by rating desc
│   ├── GET Pagination
│   ├── GET Stats
│   ├── GET Related (same director)
│   ├── POST Create Movie
│   ├── POST Bulk Create
│   ├── PUT Update Movie
│   ├── PATCH Update Rating
│   └── DELETE Delete Movie
├── Errors
│   └── 16 запросов: 400 / 404 / 500
└── Cleanup (в конце!)
    ├── DELETE All Movies
    └── GET Empty List
```

В каждом запросе на вкладке **Tests** написаны автотесты (`pm.test`): проверяются код ответа, формат JSON, наличие и значения полей. Папка **Setup** возвращает сервер к исходным данным, поэтому коллекцию можно запускать повторно без перезапуска сервера. Папка **Cleanup** должна выполняться последней, так как удаляет все фильмы.

![Структура коллекции в Postman](screenshots/postman_collection.png)

![Окружение Local Development](screenshots/postman_environment.png)

### Результаты автотестов (Test Results)

![Test Results — GET All Movies](screenshots/postman_tests_get.png)

![Test Results — POST Create Movie](screenshots/postman_tests_post.png)

![Test Results — ошибки](screenshots/postman_tests_errors.png)

### Collection Runner

Результат запуска всей коллекции (**Run collection**): все тесты пройдены (PASS).

![Collection Runner](screenshots/collection_runner.png)

---

## ❓ Ответы на контрольные вопросы

**1. Как реализовать частичное обновление (PATCH)?**
Создаётся маршрут `app.patch('/movies/:id', …)`. В нём проверяется, что фильм существует (иначе `404`), валидируются только переданные в теле поля, а затем в копию объекта записываются только эти поля. В отличие от `PUT`, непереданные поля остаются прежними.

**2. Как реализовать массовое удаление элементов?**
Маршрут `DELETE /movies` без параметра очищает массив (`movies = []`) и возвращает количество удалённых элементов. При необходимости удаление можно ограничить фильтром, например по query-параметру.

**3. Как реализовать массовое создание элементов?**
Маршрут `POST /movies/bulk` принимает JSON-массив. Сначала валидируется каждый элемент, и если есть ошибки, возвращается `400` с номерами неверных элементов. Только после успешной проверки всем элементам присваиваются id и они добавляются в массив, а клиент получает `201`.

**4. Как реализовать глобальный обработчик ошибок?**
Это middleware с четырьмя аргументами `(err, req, res, next)`, которое регистрируется **после** всех маршрутов. Оно логирует ошибку и возвращает клиенту `500` с безопасным сообщением, не раскрывая стек вызовов. Для известных типов ошибок (`entity.parse.failed`, `entity.too.large`) возвращаются `400` и `413`. В Express 5 ошибки из `async`-обработчиков и отклонённых промисов попадают в такой обработчик автоматически.

**5. Как логировать запросы в файл?**
С помощью middleware, который на событии `finish` ответа записывает дату, метод, URL и код ответа. Для записи используется поток `fs.createWriteStream('access.log', { flags: 'a' })`, где флаг `a` дописывает строки в конец файла, а не перезаписывает его.

**6. Что такое REST API и какие принципы лежат в его основе?**
REST — архитектурный стиль построения веб-API, в котором данные представлены **ресурсами** с собственными URL (`/movies/5`), а операции выполняются стандартными HTTP-методами. Основные принципы: клиент-серверная архитектура, **stateless** (сервер не хранит состояние клиента между запросами), кэшируемость, единообразный интерфейс, многоуровневая система; код по требованию — необязательный принцип. Ответы возвращаются в унифицированном формате (обычно JSON) с осмысленными кодами состояния.

**7. Как организовать структуру проекта для масштабируемого CRUD API?**
Код разделяют по слоям: `routes/` (маршруты), `controllers/` (обработчики запросов), `services/` или `models/` (бизнес-логика и работа с данными), `middleware/` (логирование, валидация, обработка ошибок), `config/` (настройки, порт, переменные окружения из `.env`). Точка входа (`server.js`) только запускает приложение, а само приложение (`app.js`) собирает middleware и маршруты.

**8. Какие существуют стратегии генерации уникальных ID?**
Автоинкрементный счётчик (как в работе; просто, но id предсказуемы и сбрасываются при перезапуске), последовательности и `AUTO_INCREMENT` в БД, **UUID v4** (случайные, уникальны глобально), ULID и Snowflake-идентификаторы (уникальные и упорядоченные по времени), а также естественные ключи (например, ISBN).

**9. Как защитить API от слишком больших запросов?**
Ограничить размер тела запроса (`express.json({ limit: '100kb' })` — при превышении сервер вернёт `413`), ограничить размер страницы в пагинации (в работе `limit` ≤ 100) и число элементов в массовых операциях, валидировать входные данные, использовать ограничение частоты запросов (`express-rate-limit`) и ограничения на уровне обратного прокси (например, Nginx).

**10. Как реализовать связь между сущностями (например, задачи и пользователи)?**
В дочерней сущности хранится внешний ключ (`userId` в задаче), а для получения связанных данных создаются вложенные маршруты (`GET /users/:id/tasks`). При создании записи нужно проверять, что связанный объект существует (иначе `400` или `404`). В работе связь организована по полю `director`: `GET /movies/:id/related` возвращает другие фильмы того же режиссёра.

---

## ✅ Вывод

В ходе лабораторной работы был реализован CRUD API на Express для сущности «Фильмы» (вариант 5, продвинутый уровень) с хранением данных в памяти сервера. Реализованы все пять базовых маршрутов, валидация входных данных, поиск, сортировка и пагинация, частичное обновление (`PATCH`), массовые операции (`DELETE /movies`, `POST /movies/bulk`), статистика, связанные фильмы по режиссёру, логирование запросов в файл `access.log` и глобальный обработчик ошибок. Работа API проверена в Postman: создана коллекция с автотестами, все тесты проходят в Collection Runner.

В процессе выполнения я закрепил на практике назначение HTTP-методов и кодов состояния, разницу между `PUT` и `PATCH`, идемпотентность методов, принципы построения REST API, а также научился писать автотесты в Postman и использовать окружения.

Основные трудности:

* **Порядок объявления маршрутов.** Маршрут `/movies/stats`, объявленный после `/movies/:id`, перехватывался параметрическим маршрутом и возвращал `404`; решение — объявлять статические маршруты раньше параметрических.
* **Обработка некорректных запросов.** В Express 5 при отсутствии тела `req.body` равен `undefined`, а битый JSON вызывает ошибку парсера. Без специальной обработки в обоих случаях клиент получал `500` вместо `400`, поэтому в валидацию и глобальный обработчик ошибок были добавлены соответствующие проверки.
* **Код `204`.** Ответ `204 No Content` не должен содержать тела, поэтому для `DELETE /movies/:id` используется `res.status(204).send()` без JSON.
* **Повторный запуск тестов.** Так как данные хранятся в памяти и тесты изменяют их, в коллекцию добавлена папка Setup, возвращающая сервер к исходному состоянию.

---

## 📖 Список использованных источников

1. Express — Routing: <https://expressjs.com/en/guide/routing.html>
2. Express — Request и Response (API 4.x/5.x): <https://expressjs.com/en/4x/api.html>
3. MDN — HTTP-методы: <https://developer.mozilla.org/ru/docs/Web/HTTP/Methods>
4. MDN — Коды состояния HTTP: <https://developer.mozilla.org/ru/docs/Web/HTTP/Status>
5. REST API Tutorial: <https://restfulapi.net/>
6. Postman Learning Center: <https://learning.postman.com/>
7. Методические указания к лабораторной работе №2 «HTTP-методы: обработка GET, POST, PUT, DELETE».
