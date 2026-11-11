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
