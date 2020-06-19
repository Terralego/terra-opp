FROM makinacorpus/geodjango:bionic-3.7

RUN mkdir /code
COPY . /code
WORKDIR /code

RUN apt-get install -y libpango1.0-0 libcairo2

RUN pip3 install --no-cache-dir pip setuptools wheel -U

# Install dev requirements
RUN pip3 install --no-cache-dir -e .[dev] -U
