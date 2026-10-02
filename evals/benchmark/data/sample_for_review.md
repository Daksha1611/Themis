# Benchmark sample for hand review

15 cases drawn at random (seed 20261002) from the **dev** split only.
For each case, check: is the fix a genuine bug fix (buggy) or a change with no bug
(clean)? Do the labeled lines cover the bug? Is the category right (or rightly null)?

## 1. `1c45442908d2c032` · buggy · fastapi/fastapi

- Commit: https://github.com/fastapi/fastapi/commit/185cecd891ee9591fd0f3beb65b412339d152bf4 (2025-10-08)
- Linked issue: — · PR: #12942
- Category label: **null** (no category signal)
- Labeled spans: `fastapi/_compat.py` 592–593
- Size: 3 lines in 1 file(s)

Original commit message:

```text
🐛 Fix tagged discriminated union not recognized as body field (#12942)

Co-authored-by: Motov Yurii <109919500+YuriiMotov@users.noreply.github.com>
Co-authored-by: Patrick Arminio <patrick.arminio@gmail.com>
Co-authored-by: Sebastián Ramírez <tiangolo@gmail.com>
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/fastapi/_compat.py b/fastapi/_compat.py
index 21ea1a23..8ea5bf25 100644
--- a/fastapi/_compat.py
+++ b/fastapi/_compat.py
@@ -590,9 +590,6 @@ def field_annotation_is_complex(annotation: Union[Type[Any], None]) -> bool:
     if origin is Union or origin is UnionType:
         return any(field_annotation_is_complex(arg) for arg in get_args(annotation))
 
-    if origin is Annotated:
-        return field_annotation_is_complex(get_args(annotation)[0])
-
     return (
         _annotation_is_complex(annotation)
         or _annotation_is_complex(origin)
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 2. `7313edb9e374be2d` · buggy · fastapi/fastapi

- Commit: https://github.com/fastapi/fastapi/commit/80d69ae0bb393c728c61c41086b770237b7b676c (2025-12-02)
- Linked issue: — · PR: #14430
- Category label: **null** (no category signal)
- Labeled spans: `fastapi/_compat/v2.py` 20–20, `fastapi/_compat/v2.py` 384–384
- Size: 4 lines in 1 file(s)

Original commit message:

```text
🐛 Fix optional sequence handling with new union syntax from Python 3.10 (#14430)

Co-authored-by: pre-commit-ci-lite[bot] <117423508+pre-commit-ci-lite[bot]@users.noreply.github.com>
Co-authored-by: Sebastián Ramírez <tiangolo@gmail.com>
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/fastapi/_compat/v2.py b/fastapi/_compat/v2.py
index 0faa7d5a..543a42dd 100644
--- a/fastapi/_compat/v2.py
+++ b/fastapi/_compat/v2.py
@@ -17,7 +17,7 @@ from typing import (
 
 from fastapi._compat import may_v1, shared
 from fastapi.openapi.constants import REF_TEMPLATE
-from fastapi.types import IncEx, ModelNameMap, UnionType
+from fastapi.types import IncEx, ModelNameMap
 from pydantic import BaseModel, TypeAdapter, create_model
 from pydantic import PydanticSchemaGenerationError as PydanticSchemaGenerationError
 from pydantic import PydanticUndefinedAnnotation as PydanticUndefinedAnnotation
@@ -381,7 +381,7 @@ def copy_field_info(*, field_info: FieldInfo, annotation: Any) -> FieldInfo:
 
 def serialize_sequence_value(*, field: ModelField, value: Any) -> Sequence[Any]:
     origin_type = get_origin(field.field_info.annotation) or field.field_info.annotation
-    if origin_type is Union or origin_type is UnionType:  # Handle optional sequences
+    if origin_type is Union:  # Handle optional sequences
         union_args = get_args(field.field_info.annotation)
         for union_arg in union_args:
             if union_arg is type(None):
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 3. `1aa90df70bff24f2` · buggy · agronholm/anyio

- Commit: https://github.com/agronholm/anyio/commit/2571e5805b9986cdcbc1e155c9898188cd13d611 (2026-06-27)
- Linked issue: — · PR: #1175
- Category label: **concurrency-or-async** (scores {'concurrency-or-async': 4, 'null-or-none-handling': 1, 'resource-leak': 1})
- Labeled spans: `src/anyio/_backends/_asyncio.py` 1118–1119, `src/anyio/_backends/_asyncio.py` 1121–1122, `src/anyio/_backends/_asyncio.py` 1123–1124, `src/anyio/_backends/_asyncio.py` 1125–1126, `src/anyio/_backends/_asyncio.py` 1127–1128, `src/anyio/_backends/_asyncio.py` 1134–1134, `src/anyio/_backends/_asyncio.py` 1139–1139, `src/anyio/_backends/_asyncio.py` 2402–2403, `src/anyio/_backends/_asyncio.py` 2685–2686, `src/anyio/_backends/_asyncio.py` 2687–2687, `src/anyio/_backends/_asyncio.py` 2695–2695, `src/anyio/_backends/_asyncio.py` 2702–2703, `src/anyio/_backends/_asyncio.py` 2706–2706
- Size: 55 lines in 1 file(s)

Original commit message:

```text
Fix asyncio waiting on closing streams in ``Process.wait()`` (#1175)

Normalize to same behavior as trio and asyncio+uvloop.
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/src/anyio/_backends/_asyncio.py b/src/anyio/_backends/_asyncio.py
index cd773af..e6fd955 100644
--- a/src/anyio/_backends/_asyncio.py
+++ b/src/anyio/_backends/_asyncio.py
@@ -1116,40 +1116,27 @@ class Process(abc.Process):
     _stdin: StreamWriterWrapper | None
     _stdout: StreamReaderWrapper | None
     _stderr: StreamReaderWrapper | None
-    _exited: asyncio.Event
-    _transport: asyncio.SubprocessTransport
 
     async def aclose(self) -> None:
         with CancelScope(shield=True) as scope:
-            # We need to close the underlying pipe_transports as well to allow a
-            # process blocking on full buffers to receive SIGPIPE and exit.
             if self._stdin:
                 await self._stdin.aclose()
-                if pipe := self._transport.get_pipe_transport(0):
-                    pipe.close()
             if self._stdout:
                 await self._stdout.aclose()
-                if pipe := self._transport.get_pipe_transport(1):
-                    pipe.close()
             if self._stderr:
                 await self._stderr.aclose()
-                if pipe := self._transport.get_pipe_transport(2):
-                    pipe.close()
 
             scope.shield = False
             try:
                 await self.wait()
             except BaseException:
                 scope.shield = True
-                # Closing the transport on asyncio also handles sending kill
-                self._transport.close()
+                self.kill()
                 await self.wait()
                 raise
 
     async def wait(self) -> int:
-        await self._exited.wait()
-        assert self._process.returncode is not None
-        return self._process.returncode
+        return await self._process.wait()
 
     def terminate(self) -> None:
         self._process.terminate()
@@ -2413,24 +2400,6 @@ class TestRunner(abc.TestRunner):
         self._raise_async_exceptions()
 
 
-class _ProcessStreamProtocol(asyncio.subprocess.SubprocessStreamProtocol):
-    """
-    A subprocess protocol that allows us to be notified of ``process_exited``
-
-    asyncio's own ``Process.wait()`` only resolves once every pipe transport has
-    disconnected so to get same semantics as on trio and uvloop we need this.
-    """
-
-    def __init__(self) -> None:
-        # Match the standard factory for asyncio.create_process
-        super().__init__(limit=2**16, loop=asyncio.get_running_loop())
-        self.exited = asyncio.Event()
-
-    def process_exited(self) -> None:
-        super().process_exited()
-        self.exited.set()
-
-
 class AsyncIOBackend(AsyncBackend):
     @classmethod
     def run(
@@ -2714,13 +2683,8 @@ class AsyncIOBackend(AsyncBackend):
         if isinstance(command, PathLike):
             command = os.fspath(command)
 
-        # Use loop.subprocess_shell()/subprocess_exec() rather than their
-        # asyncio.create_subprocess_*() counterparts to get access to
-        # transport/protocol.
-        loop = asyncio.get_running_loop()
         if isinstance(command, (str, bytes)):
-            transport, protocol = await loop.subprocess_shell(
-                _ProcessStreamProtocol,
+            process = await asyncio.create_subprocess_shell(
                 command,
                 stdin=stdin,
                 stdout=stdout,
@@ -2728,8 +2692,7 @@ class AsyncIOBackend(AsyncBackend):
                 **kwargs,
             )
         else:
-            transport, protocol = await loop.subprocess_exec(
-                _ProcessStreamProtocol,
+            process = await asyncio.create_subprocess_exec(
                 *command,
                 stdin=stdin,
                 stdout=stdout,
@@ -2737,18 +2700,10 @@ class AsyncIOBackend(AsyncBackend):
                 **kwargs,
             )
 
-        process = asyncio.subprocess.Process(transport, protocol, loop)
         stdin_stream = StreamWriterWrapper(process.stdin) if process.stdin else None
         stdout_stream = StreamReaderWrapper(process.stdout) if process.stdout else None
         stderr_stream = StreamReaderWrapper(process.stderr) if process.stderr else None
-        return Process(
-            process,
-            stdin_stream,
-            stdout_stream,
-            stderr_stream,
-            protocol.exited,
-            transport,
-        )
+        return Process(process, stdin_stream, stdout_stream, stderr_stream)
 
     @classmethod
     def setup_process_pool_exit_at_shutdown(cls, workers: set[abc.Process]) -> None:
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 4. `a3e5f5b90622d8e2` · buggy · agronholm/anyio

- Commit: https://github.com/agronholm/anyio/commit/586e3cf49a32379139309034382046288742b479 (2026-07-25)
- Linked issue: — · PR: #1200
- Category label: **type-or-contract** (scores {'type-or-contract': 2, 'error-handling': 1})
- Labeled spans: `src/anyio/_core/_fileio.py` 927–930
- Size: 20 lines in 1 file(s)

Original commit message:

```text
Fixed Path.with_stem() not validating an empty stem (#1200)

anyio.Path.with_stem() reimplemented the operation as with_name(stem + self.suffix) instead of delegating to
pathlib's own with_stem(). For a path with a non-empty suffix, an empty stem therefore produced a silently wrong path
(e.g. Path("foo.txt").with_stem("") -> Path(".txt")) rather than raising ValueError like pathlib.PurePath.with_stem() does.

The sibling wrappers with_name() and with_suffix() already delegate to self._path; with_stem() now does the same, restoring parity with pathlib for every input (empty-stem-with-suffix now raises, all other cases are byte-identical to before).

---------

Co-authored-by: Alex Grönholm <alex.gronholm@nextday.fi>
Co-authored-by: Tobias Petersen <tobias.alex.petersen@gmail.com>
Co-authored-by: NIYONSHUTI Emmanuel <nemmy0257@gmail.com>
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/src/anyio/_core/_fileio.py b/src/anyio/_core/_fileio.py
index 280b44b..692c754 100644
--- a/src/anyio/_core/_fileio.py
+++ b/src/anyio/_core/_fileio.py
@@ -924,22 +924,10 @@ class Path:
     def with_name(self, name: str) -> Self:
         return type(self)(self._path.with_name(name), limiter=self._limiter)
 
-    if sys.version_info < (3, 13):
-        # Backport pathlib's Python>=3.13 behavior for empty stems on paths with non-empty suffixes.
-        # See: https://github.com/python/cpython/pull/114612
-        def with_stem(self, stem: str) -> Self:
-            suffix = self._path.suffix
-            if not suffix:
-                return self.with_name(stem)
-            elif not stem:
-                # If the suffix is non-empty, we can't make the stem empty.
-                raise ValueError(f"{self!r} has a non-empty suffix")
-            else:
-                return self.with_name(stem + suffix)
-    else:
-
-        def with_stem(self, stem: str) -> Self:
-            return type(self)(self._path.with_stem(stem), limiter=self._limiter)
+    def with_stem(self, stem: str) -> Self:
+        return type(self)(
+            self._path.with_name(stem + self._path.suffix), limiter=self._limiter
+        )
 
     def with_suffix(self, suffix: str) -> Self:
         return type(self)(self._path.with_suffix(suffix), limiter=self._limiter)
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 5. `5f11ad246e7fccc3` · buggy · marshmallow-code/marshmallow

- Commit: https://github.com/marshmallow-code/marshmallow/commit/024b5d09e9f026f0f96d220e243be69346687ce0 (2026-03-25)
- Linked issue: — · PR: #2902
- Category label: **null** (weak signal only (error-handling=1))
- Labeled spans: `src/marshmallow/fields.py` 1950–1951, `src/marshmallow/fields.py` 1952–1953
- Size: 5 lines in 1 file(s)

Original commit message:

```text
Fix Enum field by-name lookup to only return actual members (#2902)

* Fix Enum field by-name lookup to only return actual members

Use dict-style access (self.enum[val]) instead of getattr(self.enum, val)
for by-name deserialization. getattr returns any attribute of the Enum
class, not just members. For example, passing "mro" or "__class__" would
return built-in methods/attributes instead of raising a validation error.

The enum item access operator [] only looks up actual enum members,
so non-member attribute names now correctly raise a validation error.

* Add test for Enum field rejecting non-member attributes by name

* Update changelog

---------

Co-authored-by: Jared Deckard <jared@shademaps.com>
Co-authored-by: Steven Loria <git@stevenloria.com>
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/src/marshmallow/fields.py b/src/marshmallow/fields.py
index 31c1492..1c2e72e 100644
--- a/src/marshmallow/fields.py
+++ b/src/marshmallow/fields.py
@@ -1947,10 +1947,9 @@ class Enum(Field[_EnumT]):
             except ValueError as error:
                 raise self.make_error("unknown", choices=self.choices_text) from error
         try:
-            ret = self.enum[val]
-        except KeyError as error:
+            return getattr(self.enum, val)
+        except AttributeError as error:
             raise self.make_error("unknown", choices=self.choices_text) from error
-        return ret
 
 
 class Method(Field):
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 6. `42b0172a905fe7e4` · buggy · fastapi/fastapi

- Commit: https://github.com/fastapi/fastapi/commit/cb3792d39e1004947419a2a06b5764894730892d (2025-12-02)
- Linked issue: — · PR: #14416
- Category label: **null** (weak signal only (error-handling=1))
- Labeled spans: `fastapi/utils.py` 113–113, `fastapi/utils.py` 124–124, `fastapi/utils.py` 132–132
- Size: 12 lines in 1 file(s)

Original commit message:

```text
🐛 Fix unformatted `{type_}` in FastAPIError (#14416)

Co-authored-by: Alex Colby <alex.colby@intellisense.io>
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/fastapi/utils.py b/fastapi/utils.py
index b3b89ed2..2e79ee6b 100644
--- a/fastapi/utils.py
+++ b/fastapi/utils.py
@@ -110,9 +110,7 @@ def create_model_field(
         try:
             return v1.ModelField(**v1_kwargs)  # type: ignore[no-any-return]
         except RuntimeError:
-            raise fastapi.exceptions.FastAPIError(
-                _invalid_args_message.format(type_=type_)
-            ) from None
+            raise fastapi.exceptions.FastAPIError(_invalid_args_message) from None
     elif PYDANTIC_V2:
         from ._compat import v2
 
@@ -123,9 +121,7 @@ def create_model_field(
         try:
             return v2.ModelField(**kwargs)  # type: ignore[return-value,arg-type]
         except PydanticSchemaGenerationError:
-            raise fastapi.exceptions.FastAPIError(
-                _invalid_args_message.format(type_=type_)
-            ) from None
+            raise fastapi.exceptions.FastAPIError(_invalid_args_message) from None
     # Pydantic v2 is not installed, but it's not a Pydantic v1 ModelField, it could be
     # a Pydantic v1 type, like a constrained int
     from fastapi._compat import v1
@@ -133,9 +129,7 @@ def create_model_field(
     try:
         return v1.ModelField(**v1_kwargs)  # type: ignore[no-any-return]
     except RuntimeError:
-        raise fastapi.exceptions.FastAPIError(
-            _invalid_args_message.format(type_=type_)
-        ) from None
+        raise fastapi.exceptions.FastAPIError(_invalid_args_message) from None
 
 
 def create_cloned_field(
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 7. `475492aa9771e0ef` · buggy · pallets/click

- Commit: https://github.com/pallets/click/commit/4f70b379b55b3b7f7dec0d8b9d3e91a347c238e1 (2025-08-23)
- Linked issue: — · PR: —
- Category label: **type-or-contract** (scores {'type-or-contract': 2})
- Labeled spans: `src/click/core.py` 2442–2442
- Size: 2 lines in 1 file(s)

Original commit message:

```text
Fix typing
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/src/click/core.py b/src/click/core.py
index a6ade10..b1df59d 100644
--- a/src/click/core.py
+++ b/src/click/core.py
@@ -2439,7 +2439,7 @@ class Parameter:
         rv = self.resolve_envvar_value(ctx)
 
         if rv is not None and self.nargs != 1:
-            rv = t.cast(cabc.Sequence[str], self.type.split_envvar_value(rv))
+            rv = self.type.split_envvar_value(rv)
 
         return rv
 
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 8. `7a28a9adf0d7d761` · buggy · fastapi/fastapi

- Commit: https://github.com/fastapi/fastapi/commit/5d40dfbc9bc1df1c7801acc53857ec7a072b7697 (2025-11-13)
- Linked issue: — · PR: #14349
- Category label: **type-or-contract** (scores {'type-or-contract': 2})
- Labeled spans: `fastapi/_compat/v2.py` 265–270
- Size: 12 lines in 1 file(s)

Original commit message:

```text
🐛 Fix handling of JSON Schema attributes named "$ref" (#14349)
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/fastapi/_compat/v2.py b/fastapi/_compat/v2.py
index 5cd49343..6a87b9ae 100644
--- a/fastapi/_compat/v2.py
+++ b/fastapi/_compat/v2.py
@@ -262,12 +262,12 @@ def _replace_refs(
     new_schema = deepcopy(schema)
     for key, value in new_schema.items():
         if key == "$ref":
-            value = schema["$ref"]
-            if isinstance(value, str):
-                ref_name = schema["$ref"].split("/")[-1]
-                if ref_name in old_name_to_new_name_map:
-                    new_name = old_name_to_new_name_map[ref_name]
-                    new_schema["$ref"] = REF_TEMPLATE.format(model=new_name)
+            ref_name = schema["$ref"].split("/")[-1]
+            if ref_name in old_name_to_new_name_map:
+                new_name = old_name_to_new_name_map[ref_name]
+                new_schema["$ref"] = REF_TEMPLATE.format(model=new_name)
+            else:
+                new_schema["$ref"] = schema["$ref"]
             continue
         if isinstance(value, dict):
             new_schema[key] = _replace_refs(
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 9. `3f489da11486b473` · buggy · marshmallow-code/marshmallow

- Commit: https://github.com/marshmallow-code/marshmallow/commit/902f99c4151d1f0c4c3b8e8dfbafc7b6a76aeaa6 (2026-08-08)
- Linked issue: — · PR: #3016
- Category label: **type-or-contract** (scores {'type-or-contract': 3})
- Labeled spans: `src/marshmallow/validate.py` 160–160
- Size: 2 lines in 1 file(s)

Original commit message:

```text
Fix URL validator rejecting a fragment after an empty path (#3016)

* Fix URL validator rejecting a fragment after an empty path

`validate.URL` rejected absolute URLs whose fragment follows an empty
path with no query, such as `https://example.com#frag`. RFC 3986 permits
a fragment after an empty path, and anchor links to a domain root are
common in practice.

Allow `#` to introduce the URL tail so the fragment is accepted. This
also makes a bare `#frag` valid in relative mode, matching the existing
handling of a bare `?query`.

* Add changelog entry for URL fragment fix (:pr:`3016`)

* Remove explanatory comment per review

* credit

---------

Co-authored-by: Steven Loria <git@stevenloria.com>
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/src/marshmallow/validate.py b/src/marshmallow/validate.py
index 35c0e8b..3463a47 100644
--- a/src/marshmallow/validate.py
+++ b/src/marshmallow/validate.py
@@ -157,7 +157,7 @@ class URL(Validator):
                     r"(?::\d+)?",
                 )
             )
-            relative_part = r"(?:/?|[/?#]\S+)\Z"
+            relative_part = r"(?:/?|[/?]\S+)\Z"
 
             if relative:
                 if absolute:
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 10. `d777dbbda423e6fc` · buggy · fastapi/fastapi

- Commit: https://github.com/fastapi/fastapi/commit/e92a0dc3ce5ecbebb8655dbe5465cb61d48f9fc0 (2026-07-28)
- Linked issue: — · PR: #15937
- Category label: **control-flow** (scores {'control-flow': 2})
- Labeled spans: `fastapi/routing.py` 632–633, `fastapi/routing.py` 636–636, `fastapi/routing.py` 668–669, `fastapi/routing.py` 672–672
- Size: 10 lines in 1 file(s)

Original commit message:

```text
🐛 Fix `status_code` being ignored for SSE and JSONL streaming endpoints (#15937)

Co-authored-by: pre-commit-ci-lite[bot] <117423508+pre-commit-ci-lite[bot]@users.noreply.github.com>
Co-authored-by: Yurii Motov <yurii.motov.monte@gmail.com>
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/fastapi/routing.py b/fastapi/routing.py
index 52973226..3ba83fc6 100644
--- a/fastapi/routing.py
+++ b/fastapi/routing.py
@@ -630,13 +630,10 @@ def get_request_handler(
                     _sse_with_checkpoints(sse_receive_stream)
                 )
 
-                response_args = _build_response_args(
-                    status_code=status_code, solved_result=solved_result
-                )
                 response = StreamingResponse(
                     sse_stream_content,
                     media_type="text/event-stream",
-                    **response_args,
+                    background=solved_result.background_tasks,
                 )
                 response.headers["Cache-Control"] = "no-cache"
                 # For Nginx proxies to not buffer server sent events
@@ -669,13 +666,10 @@ def get_request_handler(
 
                     jsonl_stream_content = _sync_stream_jsonl()
 
-                response_args = _build_response_args(
-                    status_code=status_code, solved_result=solved_result
-                )
                 response = StreamingResponse(
                     jsonl_stream_content,
                     media_type="application/jsonl",
-                    **response_args,
+                    background=solved_result.background_tasks,
                 )
                 response.headers.raw.extend(solved_result.response.headers.raw)
             elif _is_async_gen_callable(dependant.call) or _is_gen_callable(
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 11. `13a874d6aa499272` · clean · Textualize/rich

- Commit: https://github.com/Textualize/rich/commit/9ac7e797cc731429603cdebd21c1746e5984c7b6 (2026-02-26)
- Linked issue: — · PR: —
- Category label: **null** (clean case)
- Labeled spans: none (clean case)
- Size: 16 lines in 1 file(s)

Original commit message:

```text
Use faster generator for link IDs
```

Diff shown to the reviewer:

```diff
diff --git a/rich/style.py b/rich/style.py
index 5294241..3806a8c 100644
--- a/rich/style.py
+++ b/rich/style.py
@@ -1,8 +1,9 @@
 import sys
 from functools import lru_cache
+from itertools import count
 from operator import attrgetter
 from pickle import dumps, loads
-from random import randint
+from random import getrandbits
 from typing import Any, Dict, Iterable, List, Optional, Type, Union, cast
 
 from . import errors
@@ -18,6 +19,9 @@ _hash_getter = attrgetter(
 StyleType = Union[str, "Style"]
 
 
+_id_generator = count(getrandbits(24))
+
+
 class _Bit:
     """A descriptor to get/set a style attribute bit."""
 
@@ -195,7 +199,7 @@ class Style:
         self._link = link
         self._meta = None if meta is None else dumps(meta)
         self._link_id = (
-            f"{randint(0, 999999)}{hash(self._meta)}" if (link or meta) else ""
+            f"{next(_id_generator)}{hash(self._meta)}" if (link or meta) else ""
         )
         self._hash: Optional[int] = None
         self._null = not (self._set_attributes or color or bgcolor or link or meta)
@@ -245,7 +249,7 @@ class Style:
         style._attributes = 0
         style._link = None
         style._meta = dumps(meta)
-        style._link_id = f"{randint(0, 999999)}{hash(style._meta)}"
+        style._link_id = f"{next(_id_generator)}{hash(style._meta)}"
         style._hash = None
         style._null = not (meta)
         return style
@@ -483,7 +487,7 @@ class Style:
         style._attributes = self._attributes
         style._set_attributes = self._set_attributes
         style._link = self._link
-        style._link_id = f"{randint(0, 999999)}" if self._link else ""
+        style._link_id = f"{next(_id_generator)}" if self._link else ""
         style._null = False
         style._meta = None
         style._hash = None
@@ -635,7 +639,7 @@ class Style:
         style._attributes = self._attributes
         style._set_attributes = self._set_attributes
         style._link = self._link
-        style._link_id = f"{randint(0, 999999)}" if self._link else ""
+        style._link_id = f"{next(_id_generator)}" if self._link else ""
         style._hash = self._hash
         style._null = False
         style._meta = self._meta
@@ -681,7 +685,7 @@ class Style:
         style._attributes = self._attributes
         style._set_attributes = self._set_attributes
         style._link = link
-        style._link_id = f"{randint(0, 999999)}" if link else ""
+        style._link_id = f"{next(_id_generator)}" if link else ""
         style._hash = None
         style._null = False
         style._meta = self._meta
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 12. `6a31dd18a51e7ec9` · buggy · fastapi/fastapi

- Commit: https://github.com/fastapi/fastapi/commit/09f5941f0e18db2b28b40d35a5da7a94c23eb9ed (2026-02-04)
- Linked issue: — · PR: #14789
- Category label: **null** (no category signal)
- Labeled spans: `fastapi/dependencies/utils.py` 207–207
- Size: 7 lines in 1 file(s)

Original commit message:

```text
🐛 Fix TYPE_CHECKING annotations for Python 3.14 (PEP 649) (#14789)
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/fastapi/dependencies/utils.py b/fastapi/dependencies/utils.py
index fc5dfed8..b647818c 100644
--- a/fastapi/dependencies/utils.py
+++ b/fastapi/dependencies/utils.py
@@ -204,12 +204,7 @@ def _get_signature(call: Callable[..., Any]) -> inspect.Signature:
         except NameError:
             # Handle type annotations with if TYPE_CHECKING, not used by FastAPI
             # e.g. dependency return types
-            if sys.version_info >= (3, 14):
-                from annotationlib import Format
-
-                signature = inspect.signature(call, annotation_format=Format.FORWARDREF)
-            else:
-                signature = inspect.signature(call)
+            signature = inspect.signature(call)
     else:
         signature = inspect.signature(call)
     return signature
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 13. `c6961eb7d54408f7` · buggy · Textualize/rich

- Commit: https://github.com/Textualize/rich/commit/a34914be5d1cc9dc298ca92e5c9af757157a0bb7 (2025-04-04)
- Linked issue: — · PR: —
- Category label: **null-or-none-handling** (scores {'null-or-none-handling': 3})
- Labeled spans: `rich/traceback.py` 180–180
- Size: 4 lines in 1 file(s)

Original commit message:

```text
fix for null tb_offset
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/rich/traceback.py b/rich/traceback.py
index bd064de..b2cc630 100644
--- a/rich/traceback.py
+++ b/rich/traceback.py
@@ -177,9 +177,7 @@ def install(
 
             # determine correct tb_offset
             compiled = tb_data.get("running_compiled_code", False)
-            tb_offset = tb_data.get("tb_offset")
-            if tb_offset is None:
-                tb_offset = 1 if compiled else 0
+            tb_offset = tb_data.get("tb_offset", 1 if compiled else 0)
             # remove ipython internal frames from trace with tb_offset
             for _ in range(tb_offset):
                 if tb is None:
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 14. `5664ca68e610b908` · buggy · agronholm/anyio

- Commit: https://github.com/agronholm/anyio/commit/02d7fbe2ae1e3701a3be3f764dcda89e066c009a (2026-08-23)
- Linked issue: — · PR: #1279
- Category label: **null** (tie: concurrency-or-async=2, control-flow=2)
- Labeled spans: `src/anyio/_backends/_asyncio.py` 1045–1045, `src/anyio/_backends/_asyncio.py` 1048–1049
- Size: 5 lines in 1 file(s)

Original commit message:

```text
Fixed worker result race with closed event loop (#1279)
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/src/anyio/_backends/_asyncio.py b/src/anyio/_backends/_asyncio.py
index 418fc8d..726cfb9 100644
--- a/src/anyio/_backends/_asyncio.py
+++ b/src/anyio/_backends/_asyncio.py
@@ -1042,13 +1042,10 @@ class WorkerThread(Thread):
                     finally:
                         del threadlocals.current_cancel_scope
 
-                    try:
+                    if not self.loop.is_closed():
                         self.loop.call_soon_threadsafe(
                             self._report_result, future, result, exception
                         )
-                    except RuntimeError:
-                        if not self.loop.is_closed():
-                            raise
 
                     del result, exception
 
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no

## 15. `3811ac234bb6c989` · buggy · agronholm/anyio

- Commit: https://github.com/agronholm/anyio/commit/e0e2531de14c54eed895c92b4c8e87b44f47634b (2025-04-15)
- Linked issue: — · PR: —
- Category label: **null** (weak signal only (concurrency-or-async=1))
- Labeled spans: `src/anyio/_core/_fileio.py` 431–431, `src/anyio/_core/_fileio.py` 445–445
- Size: 4 lines in 1 file(s)

Original commit message:

```text
Fixed Path.copy() and Path.copy_info failing on Python 3.14.0a7
```

Diff shown to the reviewer (the fix reversed, package source only):

```diff
diff --git a/src/anyio/_core/_fileio.py b/src/anyio/_core/_fileio.py
index 2eae029..17459b7 100644
--- a/src/anyio/_core/_fileio.py
+++ b/src/anyio/_core/_fileio.py
@@ -428,7 +428,7 @@ class Path:
                 follow_symlinks=follow_symlinks,
                 preserve_metadata=preserve_metadata,
             )
-            return Path(await to_thread.run_sync(func, pathlib.Path(target)))
+            return Path(await to_thread.run_sync(func, target))
 
         async def copy_into(
             self,
@@ -442,7 +442,7 @@ class Path:
                 follow_symlinks=follow_symlinks,
                 preserve_metadata=preserve_metadata,
             )
-            return Path(await to_thread.run_sync(func, pathlib.Path(target_dir)))
+            return Path(await to_thread.run_sync(func, target_dir))
 
         async def move(self, target: str | os.PathLike[str]) -> Path:
             # Upstream does not handle anyio.Path properly as a PathLike
```

Your verdict: genuine? ☐ yes ☐ no · labels cover the bug? ☐ yes ☐ no · category right? ☐ yes ☐ no
