load:
	python src/etl/loader.py

ratios:
	python src/etl/ratios.py

test:
	pytest

report:
	python src/report.py

dashboard:
	python src/dashboard.py

api:
	python src/api.py

clean:
	powershell -Command "Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force"