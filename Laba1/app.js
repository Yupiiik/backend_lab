const express = require('express');
const app = express();
const port = 3000;

// Консольное логирование всех запросов 
app.use((req, res, next) => {
  const time = new Date().toISOString();
  console.log(`[${time}] ${req.method} ${req.url}`);
  next();
});

// 1. Текстовый эндпоинт
app.get('/', (req, res) => {
  res.send('Сервер работает');
});

// 2. Коллекция: фильмы
app.get('/api/movies', (req, res) => {
  const movies = [
    { id: 1, title: 'Inception', year: 2010, genre: 'Sci-Fi' },
    { id: 2, title: 'Interstellar', year: 2014, genre: 'Sci-Fi' },
    { id: 3, title: 'The Matrix', year: 1999, genre: 'Action' },
    { id: 4, title: 'Fight Club', year: 1999, genre: 'Drama' },
    { id: 5, title: 'Pulp Fiction', year: 1994, genre: 'Crime' }
  ];
  res.json(movies);
});

// 3. Коллекция: кинотеатры 
app.get('/api/cinemas', (req, res) => {
  const cinemas = [
    { id: 1, name: 'Каро Фильм', city: 'Москва', halls: 8 },
    { id: 2, name: 'Синема Парк', city: 'Санкт-Петербург', halls: 6 },
    { id: 3, name: 'Формула Кино', city: 'Казань', halls: 5 },
    { id: 4, name: 'Премьер Зал', city: 'Екатеринбург', halls: 4 }
  ];
  res.json(cinemas);
});

// 4. Эндпоинт с параметром в пути 
app.get('/api/movies/:id', (req, res) => {
  const movieId = req.params.id;
  res.json({
    requestedId: movieId,
    status: 'success'
  });
});

// 5. Обработка 404
app.use((req, res) => {
  res.status(404).json({ error: 'Маршрут не найден' });
});

app.listen(port, () => {
  console.log(`Сервер запущен на http://localhost:${port}`);
});