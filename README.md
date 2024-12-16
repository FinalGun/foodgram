## Foodgram

### Технологии:

Python, Django, Django Rest Framework, Docker, Gunicorn, NGINX, PostgreSQL, Yandex Cloud, Continuous Integration, Continuous Deployment

### Как развернуть проект на удаленном сервере:

- Установить на сервере Docker, Docker Compose:

```
sudo apt install curl
```
```                             
curl -fsSL https://get.docker.com -o get-docker.sh
```
```      
sh get-docker.sh
```
```                                       
sudo apt-get install docker-compose-plugin              
```

- Скопировать на сервер файл docker-compose.production.yml и в этой директории создать файл .env.
- Пример файла .env:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY='секретный ключ Django'
ALLOWED_HOSTS=123.123.123.123 localhost "ip адрес вашего сервера" "Домен"
DNS="Домен"


```

- Создать и запустить контейнеры Docker, выполнить команду на сервере
```
sudo docker compose -f docker-compose.production.yml up -d
```

- После успешной сборки выполнить миграции:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

- Создать суперпользователя:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

- Собрать статику:
```
sudo docker compose exec backend python manage.py collectstatic
```
```
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
- Наполнить базу данными:
```
sudo docker compose exec backend python manage.py tags_load
```
```
sudo docker compose exec backend python manage.py ingredients_load
```
- Документация будет доступна по адресу https://"DNS"/api/docs/

### Локальный запуск без Docker:

- В терминале перейти в директорию foodgram\backend\backend_foodgramm и выполнить команды:
```
python manage.py runserver
```
```
python manage.py migrate
```
- Документация будет доступна по адресу http://localhost/api/docs/

### Автор:
[Игошев Александр](https://github.com/FinalGun)
