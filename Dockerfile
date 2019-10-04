FROM makinacorpus/geodjango:bionic-3.7

RUN mkdir /code
COPY . /code
WORKDIR /code

RUN apt-get install -y libpango1.0-0 libcairo2

RUN python3.7 setup.py install
# Install dev requirements
RUN pip3 install -e .[dev] -U
