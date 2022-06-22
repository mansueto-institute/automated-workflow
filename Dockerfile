FROM continuumio/miniconda3

ENV CONDA_ENV_NAME test

COPY environment_compute.yml .
RUN conda env create -f environment_compute.yml

RUN echo "source activate $CONDA_ENV_NAME" > ~/.bashrc
ENV PATH /opt/conda/envs/$CONDA_ENV_NAME/bin:$PATH

COPY batch_compute.py .

ENTRYPOINT ["python", "batch_compute.py"]
