# ---- build ----
FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/workbench-api ./cmd/api

# ---- run ----
FROM alpine:3.20
RUN adduser -D -u 10001 app
USER app
COPY --from=build /out/workbench-api /usr/local/bin/workbench-api
EXPOSE 8080
ENTRYPOINT ["workbench-api"]
