FROM rust:latest AS builder

RUN apt-get update
RUN apt-get install protobuf-compiler -y

WORKDIR /usr/src/app

COPY . .

RUN rustup target add x86_64-unknown-linux-musl
RUN cargo build --target x86_64-unknown-linux-musl --release

FROM scratch

EXPOSE 7878

COPY --from=builder /usr/src/app/target/x86_64-unknown-linux-musl/release/server /usr/local/bin/server

CMD ["server"]