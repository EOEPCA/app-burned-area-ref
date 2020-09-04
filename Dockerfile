FROM docker.terradue.com/c7-repo2cli:latest

RUN mkdir -p /tmp/tmpdir

COPY . /tmp/tmpdir

RUN cd /tmp/tmpdir && repo2cli .

ENV PREFIX /opt/anaconda/envs/env_burned_area

ENV PATH /opt/anaconda/envs/env_burned_area/bin:$PATH
