FROM rust:1.65 as builder
WORKDIR /usr/src/myapp
COPY . .
RUN cargo build --release

FROM debian:buster-slim
COPY --from=builder /usr/src/myapp/target/release/myapp .
CMD ["./myapp"]