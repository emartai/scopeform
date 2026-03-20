dev:
	docker-compose up --build

migrate:
	docker-compose exec api alembic upgrade head

test:
	docker-compose exec api pytest

lint:
	ruff check api cli-py
	npm run lint

logs:
	docker-compose logs -f api
