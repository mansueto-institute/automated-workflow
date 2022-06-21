FROM continuumio/miniconda3

ENV CONDA_ENV_NAME test

COPY environment_compute.yml .
RUN conda env create -f environment_compute.yml

RUN echo "source activate $CONDA_ENV_NAME" > ~/.bashrc
ENV PATH /opt/conda/envs/$CONDA_ENV_NAME/bin:$PATH

COPY compute.py .
COPY df.csv .

ENTRYPOINT ["python", "compute.py"]
