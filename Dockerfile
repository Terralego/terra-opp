FROM makinacorpus/geodjango:bionic-3.6

RUN mkdir -p /code/src

RUN useradd -ms /bin/bash django
RUN chown -R django:django /code

RUN apt-get update && apt-get install -y libpango1.0-0 libcairo2

USER django

RUN python3.6 -m venv /code/venv
RUN  /code/venv/bin/pip install --no-cache-dir pip setuptools wheel -U

COPY . /code/src
WORKDIR /code/src

# Install dev requirements
RUN /code/venv/bin/pip3 install --no-cache-dir -e .[dev] -U
