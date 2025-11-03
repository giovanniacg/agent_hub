COMPOSE ?= docker compose
SERVICE ?= web

.PHONY: build up up-detached down stop logs shell migrate makemigrations createsuperuser collectstatic test lint

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

up-detached:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

stop:
	$(COMPOSE) stop

logs:
	$(COMPOSE) logs -f $(SERVICE)

shell:
	$(COMPOSE) exec $(SERVICE) bash

migrate:
	$(COMPOSE) run --rm $(SERVICE) python manage.py migrate

makemigrations:
	$(COMPOSE) run --rm $(SERVICE) python manage.py makemigrations

createsuperuser:
	$(COMPOSE) run --rm $(SERVICE) python manage.py createsuperuser

collectstatic:
	$(COMPOSE) run --rm $(SERVICE) python manage.py collectstatic --no-input

test:
	$(COMPOSE) run --rm $(SERVICE) python manage.py test

lint:
	$(COMPOSE) run --rm $(SERVICE) ruff check .
