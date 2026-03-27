FROM golang:1.22-alpine AS build

WORKDIR /src

COPY services/simulator/go.mod services/simulator/go.sum ./
RUN go mod download

COPY services/simulator ./

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/simulator ./cmd/simulator

FROM alpine:3.20

RUN addgroup -S app && adduser -S -G app app && apk add --no-cache ca-certificates

WORKDIR /app

COPY --from=build /out/simulator /app/simulator

USER app

EXPOSE 8080

ENTRYPOINT ["/app/simulator"]
