# Semantic Analysis

---

# Docker

1. Construit imagen con antlr

```diff
docker build --rm -t csp-image .
```

2. correr contenido (windows)

```diff
docker run --rm -it -v "${PWD}\program:/program" csp-image
```
