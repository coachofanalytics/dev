# Simple make targets for common workflows

.PHONY: help dev-up test test-regression deploy-uat logs-uat clone-db

help:
	@echo "Available targets:"
	@echo "  make dev-up           # start local dev server (clone DB)"
	@echo "  make test             # run full tests"
	@echo "  make test-regression  # run regression tests (if present)"
	@echo "  make deploy-uat       # deploy current branch to Heroku UAT"
	@echo "  make logs-uat         # tail Heroku UAT logs"
	@echo "  make clone-db         # run database clone script"

DEV_PORT?=8000

dev-up:
	bash scripts/dev/dev_server.sh --port $(DEV_PORT)

test:
	cd coda && pytest -q || true

test-regression:
	[ -f tests/run_tests.sh ] && ./tests/run_tests.sh --regression || echo "No regression runner found"

deploy-uat:
	git push heroku 25.10_CODA_UAT_CM:main --force

logs-uat:
	heroku logs --tail --app codamakutano --num 100

clone-db:
	bash scripts/clone_prod_database.sh
