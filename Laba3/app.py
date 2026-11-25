from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from datetime import datetime
from functools import wraps
import logging
import math

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("movies_api")

# Данные варианта 5. Хранятся в памяти и сбрасываются при перезапуске.
movies = [
    {
        "id": 1, "title": "Начало", "year": 2010, "rating": 8.8,
        "director": "Кристофер Нолан", "genre": "Фантастика",
        "actors": ["Леонардо ДиКаприо", "Джозеф Гордон-Левитт"],
        "cinemas": [1, 2]
    },
    {
        "id": 2, "title": "Интерстеллар", "year": 2014, "rating": 8.6,
        "director": "Кристофер Нолан", "genre": "Фантастика",
        "actors": ["Мэттью Макконахи", "Энн Хэтэуэй"],
        "cinemas": [1, 3]
    },
    {
        "id": 3, "title": "Побег из Шоушенка", "year": 1994, "rating": 9.1,
        "director": "Фрэнк Дарабонт", "genre": "Драма",
        "actors": ["Тим Роббинс", "Морган Фримен"],
        "cinemas": [2, 3]
    },
    {
        "id": 4, "title": "Зелёная миля", "year": 1999, "rating": 9.0,
        "director": "Фрэнк Дарабонт", "genre": "Драма",
        "actors": ["Том Хэнкс", "Майкл Кларк Дункан"],
        "cinemas": [1]
    },
    {
        "id": 5, "title": "Матрица", "year": 1999, "rating": 8.7,
        "director": "Лана и Лилли Вачовски", "genre": "Фантастика",
        "actors": ["Киану Ривз", "Лоренс Фишбёрн"],
        "cinemas": [2]
    },
    {
        "id": 6, "title": "Паразиты", "year": 2019, "rating": 8.5,
        "director": "Пон Джун-хо", "genre": "Триллер",
        "actors": ["Сон Кан-хо", "Чо Ё-джон"],
        "cinemas": [3]
    },
    {
        "id": 7, "title": "Остров проклятых", "year": 2010, "rating": 8.2,
        "director": "Мартин Скорсезе", "genre": "Триллер",
        "actors": ["Леонардо ДиКаприо", "Марк Руффало"],
        "cinemas": [1, 2]
    },
    {
        "id": 8, "title": "Гладиатор", "year": 2000, "rating": 8.5,
        "director": "Ридли Скотт", "genre": "Боевик",
        "actors": ["Рассел Кроу", "Хоакин Феникс"],
        "cinemas": [2, 3]
    }
]

cinemas = [
    {"id": 1, "name": "Премьер", "city": "Москва"},
    {"id": 2, "name": "Синема Парк", "city": "Санкт-Петербург"},
    {"id": 3, "name": "Каро", "city": "Казань"}
]

# Числовые идентификаторы категорий для демонстрации вложенных маршрутов.
categories = {
    1: "Фантастика",
    2: "Драма",
    3: "Триллер",
    4: "Боевик"
}

# Пример многоуровневого ресурса с тремя параметрами пути.
users_posts_comments = [
    {"user_id": 1, "post_id": 10, "comment_id": 100,
     "text": "Отличный фильм!", "author": "Алексей"}
]


@app.before_request
def log_request():
    """Логирует метод, URL, время запроса и IP клиента."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    logger.info("[%s] %s %s | IP: %s",
                timestamp, request.method, request.url, ip_address)


def parse_positive_id(value, parameter_name="id"):
    """Преобразует параметр в положительное целое число или возвращает ошибку."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, (jsonify({"error": f"Параметр {parameter_name} должен быть целым числом"}), 400)

    if number < 1:
        return None, (jsonify({"error": f"Параметр {parameter_name} должен быть положительным"}), 400)

    return number, None


def find_movie(movie_id):
    return next((movie for movie in movies if movie["id"] == movie_id), None)


# -------------------- СПИСОК, ПОИСК, ФИЛЬТРАЦИЯ И ПАГИНАЦИЯ --------------------

@app.route("/movies", methods=["GET"])
def get_movies():
    result = list(movies)

    search = request.args.get("search", "").strip()
    if len(search) > 100:
        return jsonify({"error": "Параметр search не должен превышать 100 символов"}), 400
    if search:
        result = [m for m in result if search.casefold() in m["title"].casefold()]

    # Поддерживаются фильтры вида filter=director:Имя и filter=rating:8.5.
    for filter_value in request.args.getlist("filter"):
        if ":" not in filter_value:
            return jsonify({"error": "Фильтр должен иметь формат field:value"}), 400
        field, value = filter_value.split(":", 1)
        if field not in ("director", "rating"):
            return jsonify({"error": "Разрешённые поля фильтрации: director, rating"}), 400
        if field == "rating":
            try:
                numeric_value = float(value)
            except ValueError:
                return jsonify({"error": "Значение rating должно быть числом"}), 400
            result = [m for m in result if m["rating"] == numeric_value]
        else:
            result = [m for m in result if m["director"].casefold() == value.casefold()]

    # Дополнительный короткий вариант фильтрации по режиссёру.
    director = request.args.get("director")
    if director:
        result = [m for m in result if m["director"].casefold() == director.casefold()]

    allowed_sort_fields = ["id", "title", "year", "rating"]
    sort = request.args.get("sort")
    order = request.args.get("order", "asc").lower()

    if order not in ("asc", "desc"):
        return jsonify({"error": "Параметр order должен быть asc или desc"}), 400
    if sort:
        if sort not in allowed_sort_fields:
            return jsonify({"error": f"Поле sort должно быть одним из: {', '.join(allowed_sort_fields)}"}), 400
        result.sort(key=lambda item: item[sort], reverse=(order == "desc"))

    # Проверяем значения отдельно, чтобы некорректные строки не превращались в значения по умолчанию.
    try:
        page = int(request.args.get("page", "1"))
        limit = int(request.args.get("limit", "10"))
    except ValueError:
        return jsonify({"error": "Параметры page и limit должны быть целыми числами"}), 400

    if page < 1:
        return jsonify({"error": "Параметр page должен быть не меньше 1"}), 400
    if limit < 1 or limit > 100:
        return jsonify({"error": "Параметр limit должен быть от 1 до 100"}), 400

    count = len(result)
    total_pages = math.ceil(count / limit) if count else 0
    start = (page - 1) * limit
    page_items = result[start:start + limit]

    return jsonify({
        "count": count,
        "page": page,
        "limit": limit,
        "totalPages": total_pages,
        "items": page_items
    })


# -------------------- СТАТИСТИКА --------------------

@app.route("/movies/stats", methods=["GET"])
def get_movie_stats():
    ratings = [movie["rating"] for movie in movies]
    return jsonify({
        "count": len(movies),
        "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        "min_rating": min(ratings) if ratings else None,
        "max_rating": max(ratings) if ratings else None
    })


# -------------------- ПАРАМЕТРЫ ПУТИ И ВЛОЖЕННЫЕ РЕСУРСЫ --------------------

@app.route("/movies/<movie_id>", methods=["GET"])
def get_movie(movie_id):
    numeric_id, error = parse_positive_id(movie_id, "movie_id")
    if error:
        return error
    movie = find_movie(numeric_id)
    if movie is None:
        return jsonify({"error": f"Фильм с id={numeric_id} не найден"}), 404
    return jsonify(movie)


@app.route("/movies/<movie_id>/actors", methods=["GET"])
def get_movie_actors(movie_id):
    numeric_id, error = parse_positive_id(movie_id, "movie_id")
    if error:
        return error
    movie = find_movie(numeric_id)
    if movie is None:
        return jsonify({"error": f"Фильм с id={numeric_id} не найден"}), 404
    return jsonify({"movie": movie["title"], "count": len(movie["actors"]), "actors": movie["actors"]})


@app.route("/movies/<movie_id>/cinemas", methods=["GET"])
def get_movie_cinemas(movie_id):
    numeric_id, error = parse_positive_id(movie_id, "movie_id")
    if error:
        return error
    movie = find_movie(numeric_id)
    if movie is None:
        return jsonify({"error": f"Фильм с id={numeric_id} не найден"}), 404
    related = [cinema for cinema in cinemas if cinema["id"] in movie["cinemas"]]
    return jsonify({"movie": movie["title"], "count": len(related), "cinemas": related})


@app.route("/genres/<genre>/movies", methods=["GET"])
def get_movies_by_genre(genre):
    result = [m for m in movies if m["genre"].casefold() == genre.casefold()]
    return jsonify({"genre": genre, "count": len(result), "movies": result})


@app.route("/directors/<director>/movies", methods=["GET"])
def get_movies_by_director(director):
    result = [m for m in movies if m["director"].casefold() == director.casefold()]
    return jsonify({"director": director, "count": len(result), "movies": result})


# -------------------- ДОПОЛНИТЕЛЬНЫЕ ВЛОЖЕННЫЕ МАРШРУТЫ --------------------

@app.route("/categories/<cat_id>/items", methods=["GET"])
def get_category_items(cat_id):
    category_id, error = parse_positive_id(cat_id, "cat_id")
    if error:
        return error
    genre = categories.get(category_id)
    if genre is None:
        return jsonify({"error": f"Категория с id={category_id} не найдена"}), 404
    result = [m for m in movies if m["genre"] == genre]
    return jsonify({"category": {"id": category_id, "name": genre},
                    "count": len(result), "items": result})


@app.route("/categories/<cat_id>/items/<item_id>", methods=["GET"])
def get_category_item(cat_id, item_id):
    category_id, error = parse_positive_id(cat_id, "cat_id")
    if error:
        return error
    movie_id, error = parse_positive_id(item_id, "item_id")
    if error:
        return error
    genre = categories.get(category_id)
    if genre is None:
        return jsonify({"error": f"Категория с id={category_id} не найдена"}), 404
    movie = find_movie(movie_id)
    if movie is None or movie["genre"] != genre:
        return jsonify({"error": "Фильм не найден в указанной категории"}), 404
    return jsonify({"category": genre, "item": movie})


# Три параметра пути: режиссёр, фильм и кинотеатр.
@app.route("/directors/<director>/movies/<movie_id>/cinemas/<cinema_id>", methods=["GET"])
def get_director_movie_cinema(director, movie_id, cinema_id):
    numeric_movie_id, error = parse_positive_id(movie_id, "movie_id")
    if error:
        return error
    numeric_cinema_id, error = parse_positive_id(cinema_id, "cinema_id")
    if error:
        return error

    movie = find_movie(numeric_movie_id)
    if movie is None or movie["director"].casefold() != director.casefold():
        return jsonify({"error": "Фильм указанного режиссёра не найден"}), 404

    cinema = next((c for c in cinemas if c["id"] == numeric_cinema_id), None)
    if cinema is None or numeric_cinema_id not in movie["cinemas"]:
        return jsonify({"error": "Кинотеатр не связан с указанным фильмом"}), 404

    return jsonify({"director": director, "movie": movie, "cinema": cinema})


# Многоуровневый пример с тремя параметрами пути из общей части задания.
@app.route("/users/<user_id>/posts/<post_id>/comments/<comment_id>", methods=["GET"])
def get_nested_comment(user_id, post_id, comment_id):
    parsed = []
    for value, name in ((user_id, "user_id"), (post_id, "post_id"), (comment_id, "comment_id")):
        number, error = parse_positive_id(value, name)
        if error:
            return error
        parsed.append(number)

    user_number, post_number, comment_number = parsed
    comment = next((c for c in users_posts_comments
                    if c["user_id"] == user_number
                    and c["post_id"] == post_number
                    and c["comment_id"] == comment_number), None)
    if comment is None:
        return jsonify({"error": "Вложенный комментарий не найден"}), 404
    return jsonify(comment)


# -------------------- ОБРАБОТКА ОШИБОК И WILDCARD --------------------

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Маршрут не найден"}), 404


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    # HTTP-ошибки (например, 404) должны сохранять свой исходный статус.
    if isinstance(error, HTTPException):
        return jsonify({"error": error.description}), error.code
    logger.exception("Непредвиденная ошибка сервера: %s", error)
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500


# Wildcard объявлен после всех конкретных маршрутов.
@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def wildcard(path):
    return jsonify({"error": "Маршрут не найден", "path": f"/{path}"}), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)
