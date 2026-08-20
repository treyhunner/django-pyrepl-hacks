# Contributing

Thanks for your interest in this project!


## Development setup

This project uses [uv][] and [just][].

```console
just setup
```

Run `just` to see every available task.


## Running the tests

```console
just test
```

That runs the suite on both supported Python versions with coverage.
`just test tests.test_bindings` runs one module, without coverage.

There is no Django project in this repository.
`runtests.py` points `DJANGO_SETTINGS_MODULE` at `tests/settings.py` and runs Django's own test runner.


## Before you open a pull request

```console
just check
```

That formats, lints, type checks, and tests.


## Trying it by hand

The parts that matter most are the ones a test cannot reach: whether the REPL actually comes up, and whether a key you press does what it should.
Point a real Django project at your checkout and use its shell:

```console
uv pip install --editable /path/to/django-pyrepl-hacks
./manage.py shell
```


## Releasing

1. Update `CHANGELOG.md`
2. `just bump patch` (or `minor` or `major`)
3. Commit, then tag the commit with a `v` prefix on the new version (`v0.1.1`, for example)
4. Push the tag, which builds and publishes from CI

[uv]: https://docs.astral.sh/uv/
[just]: https://just.systems
