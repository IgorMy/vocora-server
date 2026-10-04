FROM postgres:17-alpine

ARG PGVECTOR_VERSION=0.8.7

# Build pgvector from source and drop the build tools in the same layer,
# so they don't end up in the final image.
# - OPTFLAGS="": portable build, not tied to the CPU of the build machine
# - with_llvm=no: skip JIT bitcode, which would need the exact clang/llvm Postgres was built with
RUN apk add --no-cache --virtual .build-deps build-base \
    && wget -qO- "https://github.com/pgvector/pgvector/archive/refs/tags/v${PGVECTOR_VERSION}.tar.gz" \
        | tar -xz -C /tmp \
    && make -C "/tmp/pgvector-${PGVECTOR_VERSION}" OPTFLAGS="" with_llvm=no \
    && make -C "/tmp/pgvector-${PGVECTOR_VERSION}" with_llvm=no install \
    && rm -rf "/tmp/pgvector-${PGVECTOR_VERSION}" \
    && apk del .build-deps
