# devnotes engineering style guide

> Adopted 2024-03. Applies to all Python in this repository.
> This is the **single source of truth** for the `style-reviewer` subagent — it
> flags violations of *this document*, not of its own general preferences.

## 1. Naming

- **1.1** Functions and variables use `snake_case`. Not `camelCase`, not `PascalCase`.
- **1.2** Classes use `PascalCase`.
- **1.3** Module-level constants use `SCREAMING_SNAKE_CASE`.
- **1.4** Boolean-returning functions read as predicates: `is_admin`, `has_access`.
  A predicate must not be named for the thing it returns (`admin`, `access`).
- **1.5** Private helpers are prefixed with a single underscore.

## 2. Imports

- **2.1** Wildcard imports (`from x import *`) are forbidden. They defeat static
  analysis and make the origin of a name unknowable at the call site.
- **2.2** Import order: standard library, third party, first party — separated by
  a blank line.
- **2.3** Import the symbols you use, not the module, for first-party code.

## 3. Function signatures

- **3.1** Mutable default arguments (`def f(x=[])`, `def f(x={})`) are forbidden.
  Use `None` and construct inside the body. The default object is created once at
  definition time and shared across every call.
- **3.2** A function takes at most 5 positional parameters. Past that, take a
  dataclass or a dict.

## 4. Error handling

- **4.1** Bare `except:` is forbidden. Catch the narrowest exception type you can name.
- **4.2** An `except` block that only contains `pass` is forbidden. If an error is
  genuinely ignorable, log it and write a comment saying why.
- **4.3** Never return an exception's message or traceback in an HTTP response body.

## 5. Layout

- **5.1** Maximum line length is 100 characters.
- **5.2** Two blank lines between top-level definitions.
- **5.3** No commented-out code on `main`. Delete it; git remembers.

## 6. Literals

- **6.1** Numeric literals other than `0`, `1`, and `-1` appearing in logic must be
  named constants.
- **6.2** Configuration values (hosts, ports, limits, timeouts) live in `config.py`,
  never inline at the use site.
