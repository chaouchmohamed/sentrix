.PHONY: up down run dash test replay reset init api api-install frontend frontend-install build-frontend

init:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt || true

up:
	docker compose up -d

down:
	docker compose down

run:
	python -m sentrix.main --live honeypot/cowrie-var/log/cowrie/cowrie.json

replay:
	python -m sentrix.main --replay data/sample/cowrie_sample.json

dash:
	streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0

api:
	.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port $${API_PORT:-8000} --reload

api-install:
	.venv/bin/pip install -r api/requirements.txt

frontend:
	cd frontend && npm run dev

frontend-install:
	cd frontend && npm install

build-frontend:
	cd frontend && npm run build

test:
	pytest -q

reset:
	bash scripts/reset_demo.sh

