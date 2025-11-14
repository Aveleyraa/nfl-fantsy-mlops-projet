# nfl-fantsy-mlops-projet
tried to evaluate different models to mimic de original app


Lo primero es preparar el ambiente para ejecutar

Se ejecuta todo con uv así que para instalar lo primero debes de descargar con:


curl -LsSf https://astral.sh/uv/install.sh | sh


Después se crea el ambiente virtual  venv (con el nombre de preferencia)

usando el comando uv venv

Se activa el ambiente :

source venv/bin/activate

y se ejecuta el comando

uv pip insall -e .[dev]

se isntala el pre.commit-config:

pre-commit install

Si se tienen notebooks y se quieren emparejar con un archivo .py se debe de ejetucar el siguinte comando:

jupytext --set-formats ipynb,py:percent notebooks/<nombre del notebook>.ipynb


