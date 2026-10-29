.PHONY: up down run dash test replay reset init

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

test:
	pytest -q

reset:
	bash scripts/reset_demo.sh

