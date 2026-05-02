build:
	docker compose -f local.yml up --build -d --remove-orphans

up:
	docker compose -f local.yml up -d

down:
	docker compose -f local.yml down

down-v:
	docker compose -f local.yml down -v

banker-config:
	docker compose -f local.yml config

makemigrations:
	docker compose -f local.yml run --rm api python manage.py makemigrations

migration:
	docker compose -f local.yml run --rm api python manage.py migrate

collectstatic:
	docker compose -f local.yml run --rm api python manage.py collectstatic --no-input --clear

superuser:
	docker compose -f local.yml run --rm api python manage.py createsuperuser

flush:
	docker compose -f local.yml run --rm api python manage.py flush

net-inspect:
	docker network inspect banker_local_nw

v-inspect:
	docker volume inspect banker_local_db

banker-db:
	docker compose -f local.yml exec postgres psql --username=august.dev --dbname=banker

show-migrations:
	docker compose -f local.yml run --rm api python manage.py showmigrations user_profile

rollback:
	docker compose -f local.yml run --rm api python manage.py migrate user_profile zero