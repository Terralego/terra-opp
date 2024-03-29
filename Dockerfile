FROM makinacorpus/geodjango:bionic-3.7

RUN mkdir -p /code/src
COPY . /code/src
WORKDIR /code/src

RUN useradd -ms /bin/bash django
RUN chown -R django:django /code

RUN apt-get update && apt-get install -y libpango1.0-0 libcairo2 libjpeg62 libjpeg62-dev zlib1g-dev libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

USER django

RUN python3.7 -m venv /code/venv
RUN  /code/venv/bin/pip install --no-cache-dir pip setuptools wheel -U

# Install dev requirements
RUN /code/venv/bin/pip3 install --no-cache-dir -e .[dev] -U
