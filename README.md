# Проект «Фудграм»

- https://foodgramrecipes.ru/

Продуктовый помощник - сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Как развернуть проект на сервере:

## Клонировать репозиторий и перейти в него в командной строке
`
git clone git@github.com:Alexey-Koltsov/foodgram-project-react.git
`
## Перейти в папку
`
cd /c/Dev/foodgram-project-react/backend/
`
## Cоздать виртуальное окружение
Windows
`
python -m venv venv
`

LinuxmacOS

`
python3 -m venv venv
`
## Активировать виртуальное окружение
Windows
`
source venv/Scripts/activate
`

LinuxmacOS
`
python3 -m venv venv source venvbinactivate
`
## Обновить PIP

Windows
`
python -m pip install --upgrade pip
`

LinuxmacOS
`
python3 -m pip install --upgrade pip
`
##Активировать виртуальное окружение
`
source venv/Scripts/activate
`
LinuxmacOS
`
source venv/bin/activate
`
## Обновить PIP

Windows
`
python -m pip install --upgrade pip
`

LinuxmacOS
`
python3 -m pip install --upgrade pip
`

##Установить зависимости из файла requirements.txt
`
pip install -r requirements.txt
`
## Установить зависимости из файла requirements.txt
`
pip install -r requirements.txt
`

## Собрать образы

В папках frontend/, backend/ и infra/ соберите образы foodgram_frontend, foodgram_backend и foodgram_infra образ nginx с конфигом для управления проектом foodgram-project-react и отправьте их в Docker Hub.

В терминале в корне проекта foodgram-project-react последовательно 
выполните команды из листинга; замените username на ваш логин на 
Docker Hub.
`
cd frontend
`
`
docker build -t username/foodgram_frontend .
`
`
cd ../backend
`
`
docker build -t username/foodgram_backend .
`
`
cd ../infra
`
`
docker build -t username/foodgram_gateway .
`
## Загружаем образы на Docker Hub

Отправьте собранные образы фронтенда, бэкенда и Nginx на Docker Hub:
`
docker push alexeykoltsov/foodgram_frontend
`
`
docker push alexeykoltsov/foodgram_backend
`
`
docker push alexeykoltsov/foodgram_gateway
`

## Заходим на сервер
Чистим кэш
`
npm cache clean --force
`
`
sudo apt clean
`
`
sudo journalctl --vacuum-time=1d
`
## Создаем папку с проектом в домашней директории сервера и переходим в нее
`
sudo mkdir foodgram
`
`
cd foodgram/
`
## Создаем на сервере файл docker-compose.production.yml, открываем его и копируем в него содеожимое из такого же файла  с локального компьютера
`
sudo touch docker-compose.production.yml
`
`
sudo nano docker-compose.production.yml
`
## Создаем на сервере файл .env, открываем его и копируем в него содержимое из такого же файла с локального компьютера
`
sudo touch .env
`
`
sudo nano .env
` 
## Поднимаем контейнеры
`
sudo docker compose -f docker-compose.production.yml up -d
`
## Выполните миграции
`
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
`
## Cоберите статические файлы бэкенда и скопируйте их в /backend_static/static/:
`
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
`
`
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
`
## Загрузите в базу данных ингредиенты
`
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_data
`
## Создайте суперпользователя
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser

## Откройте и добавьте в Nginx данные для доступа к сайту, доменное имя
`
server {
    server_name foodgramrecipes.ru;

    location / {
        proxy_pass http://127.0.0.1:7000;
    }
`
## Проверьте правильность синтаксиса добавленных данных к Nginx и перезагрузите Nginx
`
sudo nginx -t
`
`
sudo service nginx reload
`
## Получите SSL-сертификат
`
sudo certbot --nginx
`
## Перезагрузите конфигурацию Nginx
`
sudo systemctl reload nginx
`

## Автор: 
Кольцов Алексей.
