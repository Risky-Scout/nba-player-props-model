PYTHON ?= python3

.PHONY: doctor minutes-predict build-pmf validate-delivery derek-feed bdl-fetch-proof api-readiness

doctor:
	@$(PYTHON) --version
	@$(PYTHON) -c "import sys; print('python_executable=' + sys.executable)"
	@$(PYTHON) -c "import pandas, pyarrow, sklearn, joblib, numpy; print('python env ok: pandas=' + pandas.__version__ + ' pyarrow=' + pyarrow.__version__ + ' numpy=' + numpy.__version__)"
	@which $(PYTHON) || echo "WARN: cannot resolve $(PYTHON) on PATH"
	@which pip || echo "WARN: pip missing on PATH"
	@PIP_PY=$$(pip -V 2>/dev/null | awk '{print $$4}'); \
	RUN_PY=$$($(PYTHON) -c "import sys; print(sys.executable)"); \
	if [ -n "$$PIP_PY" ] && [ "$$PIP_PY" != "$$RUN_PY" ]; then \
		echo "WARN: pip ($$PIP_PY) points to a different Python than runtime ($$RUN_PY)"; \
	else \
		echo "pip-runtime python alignment ok"; \
	fi
	@if [ -z "$$BDL_API_KEY" ]; then echo "WARN: BDL_API_KEY missing"; else echo "BDL_API_KEY present"; fi
	@if [ -z "$$ODDS_API_KEY" ] && [ -z "$$THE_ODDS_API_KEY" ]; then echo "WARN: ODDS_API_KEY / THE_ODDS_API_KEY missing"; else echo "ODDS API key present"; fi

minutes-predict:
	$(PYTHON) scripts/build_minutes_predictions.py --slate-date $(SLATE_DATE) --train-through-date $(TRAIN_THROUGH_DATE) --run-mode $${RUN_MODE:-morning_expected}

build-pmf:
	$(PYTHON) scripts/build_daily_pmf_delivery.py --date $(SLATE_DATE) --train-through-date $(TRAIN_THROUGH_DATE)

validate-delivery:
	$(PYTHON) scripts/validate_daily_pmf_delivery.py --date $(SLATE_DATE) --train-through-date $(TRAIN_THROUGH_DATE)

derek-feed:
	$(PYTHON) scripts/build_derek_forward_feed.py --date $(SLATE_DATE)

bdl-fetch-proof:
	$(PYTHON) scripts/verify_bdl_fetch_proof_for_derek.py --date $(SLATE_DATE)

api-readiness:
	$(PYTHON) scripts/verify_derek_live_api_readiness.py --date $(SLATE_DATE) --run-mode $${RUN_MODE:-morning_expected}
