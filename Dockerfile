FROM lambci/lambda:build-python3.6

WORKDIR /work

CMD pip install --upgrade pip && \
  pip install selenium retry -t /python/lib/python3.7/site-packages && \
  zip -r selenium.zip /python/