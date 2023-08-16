FROM squidfunk/mkdocs-material
    RUN pip install mkdocs-macros-plugin

    COPY ./mkdocs.yml /docs/
    COPY ./docs ./docs/

    EXPOSE 8000
