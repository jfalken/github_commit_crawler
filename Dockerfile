FROM mongo:2.6
MAINTAINER jfalken <chris.sandulow@gmail.com>

# Update apt-get sources, install python tools
RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y python \
  python-dev \
  python-distribute \
  python-pip \
  libyaml-dev \
  supervisor && \
  easy_install -U pip

# Copy applications to folders in container
ADD /ghcc_process ghcc_process
ADD /viewer_process viewer_process

# Copy config
ADD /config ghcc_process/config

# Install application requirements
RUN pip install -r ghcc_process/requirements.txt

EXPOSE 5000

# Start Supervisor (mongodb, ghcc and gunicorn app server)
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]
