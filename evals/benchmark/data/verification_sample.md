# Label verification sample: dev split

The dev labels were assigned by an LLM from human-written upstream evidence (Q61 amendment). This sample is for the project owner to verify by hand.

**How to mark:** for each case, tick `agree` or `disagree` for each field; where you disagree, write the right value in the note. Validity asks whether the diff really reintroduces a bug (some real input would behave wrongly). Then run `python -m evals.benchmark.verify_sample --score`.

- Selection: `python -m evals.benchmark.verify_sample`, seed `20261003`
- Labels: `evals/benchmark/data/labels_human.jsonl` (sha256 `ec8b9c27e48f`)
- Stratified sample: 25 kept buggy cases. Per category: type-or-contract 6, control-flow 5, concurrency-or-async 4, error-handling 4, CWE-20 1, CWE-400 1, arithmetic-or-numeric 1, null-or-none-handling 1, off-by-one-or-boundary 1, resource-leak 1
- Per repo: Textualize/rich 3, agronholm/anyio 7, fastapi/fastapi 7, marshmallow-code/marshmallow 3, pallets/click 5
- Borderline cases (owner's choice, scored separately): 3

**Verdicts (2026-10-03):** the verdicts are the project owner's, given after reviewing all 28 cases: agree on every field of every case. The ticks were entered by the agent at the owner's instruction. There are no per-case notes.

## Stratified sample (25 cases)

### 1. `5f11ad246e7fccc3` · marshmallow-code/marshmallow · 2026-03-25

- Commit: https://github.com/marshmallow-code/marshmallow/commit/024b5d09e9f026f0f96d220e243be69346687ce0
- Evidence read: https://github.com/marshmallow-code/marshmallow/pull/2902

Commit message:

> Fix Enum field by-name lookup to only return actual members (#2902)
>
> * Fix Enum field by-name lookup to only return actual members
>
> Use dict-style access (self.enum[val]) instead of getattr(self.enum, val)
> for by-name deserialization. getattr returns any attribute of the Enum
> class, not just members. For example, passing "mro" or "__class__" would
> return built-in methods/attributes instead of raising a validation error.
>
> The enum item access operator [] only looks up actual enum members,
> so non-member attribute names now correctly raise a validation error.
>
> …

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `CWE-20`
- **Primary range:** [1] `src/marshmallow/fields.py` lines 1950–1951 (of 2 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

Enum by-name deserialisation uses getattr on untrusted input: 'mro', '__class__', '__members__' return class attributes instead of a validation error (PR #2902); alt type-or-contract

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
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
[1] +            return getattr(self.enum, val)
[1] +        except AttributeError as error:
[2]              raise self.make_error("unknown", choices=self.choices_text) from error
    -        return ret
[2]  
     
     class Method(Field):
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 2. `94ad4f8fb317b04e` · agronholm/anyio · 2026-07-08

- Commit: https://github.com/agronholm/anyio/commit/f1b7301c8264b0d2e8d24a5788fd29e93dea4040
- Evidence read: https://github.com/agronholm/anyio/pull/1207

Commit message:

> Fixed stderr writes in a worker subprocess causing a deadlock (#1207)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `CWE-400`
- **Primary range:** [1] `src/anyio/to_process.py` lines 213–214 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

process-pool worker leaves stderr on an undrained pipe; worker code writing enough to stderr blocks and wedges the awaiting call (GHSA-5p39-cfhj-2xmp, CVE-2026-64847, severity medium); alt concurrency-or-async (deadlock)

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/to_process.py b/src/anyio/to_process.py
    index 8d356fb..fd65b18 100644
    --- a/src/anyio/to_process.py
    +++ b/src/anyio/to_process.py
    @@ -211,7 +211,6 @@ def process_worker() -> None:
         stdout = sys.stdout
         sys.stdin = open(os.devnull)
[1]      sys.stdout = open(os.devnull, "w")
    -    sys.stderr = open(os.devnull, "w")
[1]  
         stdout.buffer.write(b"READY\n")
         while True:
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 3. `36b1a3b76394efc3` · fastapi/fastapi · 2025-12-02

- Commit: https://github.com/fastapi/fastapi/commit/20f40b29c0241fc73d82857ab456ef6fda15659f
- Evidence read: https://github.com/fastapi/fastapi/pull/12935

Commit message:

> 🐛 Fix `TypeError` when encoding a decimal with a `NaN` or `Infinity` value (#12935)
>
> Signed-off-by: Kent Huang <kent@infuseai.io>

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `arithmetic-or-numeric`
- **Primary range:** [5] `fastapi/encoders.py` lines 54–54 (of 5 ranges)
- **Ranges holding the bug** (strict recall, Q62): [5]

<details><summary>Labeller's note (open after forming your own view)</summary>

decimal_encoder compares exponent >= 0, but Decimal NaN/Infinity have a str exponent, so jsonable_encoder raises TypeError (PR #12935, label bug); docstring [1-4] noise; alt type-or-contract

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/fastapi/encoders.py b/fastapi/encoders.py
    index 79395108..6fc6228e 100644
    --- a/fastapi/encoders.py
    +++ b/fastapi/encoders.py
    @@ -34,14 +34,14 @@ def isoformat(o: Union[datetime.date, datetime.time]) -> str:
         return o.isoformat()
     
     
    -# Adapted from Pydantic v1
[1] +# Taken from Pydantic v1 as is
     # TODO: pv2 should this return strings instead?
     def decimal_encoder(dec_value: Decimal) -> Union[int, float]:
         """
    -    Encodes a Decimal as int if there's no exponent, otherwise float
[2] +    Encodes a Decimal as int of there's no exponent, otherwise float
     
         This is useful when we use ConstrainedDecimal to represent Numeric(x,0)
    -    where an integer (but not int typed) is used. Encoding this as a float
[3] +    where a integer (but not int typed) is used. Encoding this as a float
         results in failed round-tripping between encode and parse.
         Our Id type is a prime example of this.
     
    @@ -50,12 +50,8 @@ def decimal_encoder(dec_value: Decimal) -> Union[int, float]:
     
         >>> decimal_encoder(Decimal("1"))
[4]      1
    -
    -    >>> decimal_encoder(Decimal("NaN"))
    -    nan
[4]      """
    -    exponent = dec_value.as_tuple().exponent
    -    if isinstance(exponent, int) and exponent >= 0:
[5] +    if dec_value.as_tuple().exponent >= 0:  # type: ignore[operator]
             return int(dec_value)
         else:
             return float(dec_value)
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 4. `1febecd36c0d6c24` · pallets/click · 2025-11-12

- Commit: https://github.com/pallets/click/commit/437e1e3295c7ec979fc1bf285bb402ca20d847e7
- Evidence read: https://github.com/pallets/click/pull/3137, https://github.com/pallets/click/issues/3136, https://github.com/pallets/click/issues/3071

Commit message:

> Temporarily provide a fake context to the callback to hide `UNSET` values as `None`
>
> Fix: https://github.com/pallets/click/issues/3136

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `null-or-none-handling`
- **Primary range:** [1] `src/click/core.py` lines 2443–2443 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

internal UNSET sentinel exposed in ctx.params to option callbacks instead of None (issue #3136; broke flask and black, blocked 8.3.1); alt type-or-contract

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/click/core.py b/src/click/core.py
    index 57f549c..437599d 100644
    --- a/src/click/core.py
    +++ b/src/click/core.py
    @@ -2440,37 +2440,7 @@ class Parameter:
                 # to None.
                 if value is UNSET:
                     value = None
    -
    -            # Search for parameters with UNSET values in the context.
    -            unset_keys = {k: None for k, v in ctx.params.items() if v is UNSET}
    -            # No UNSET values, call the callback as usual.
    -            if not unset_keys:
    -                value = self.callback(ctx, self, value)
    -
    -            # Legacy case: provide a temporarily manipulated context to the callback
    -            # to hide UNSET values as None.
    -            #
    -            # Refs:
    -            # https://github.com/pallets/click/issues/3136
    -            # https://github.com/pallets/click/pull/3137
    -            else:
    -                # Add another layer to the context stack to clearly hint that the
    -                # context is temporarily modified.
    -                with ctx:
    -                    # Update the context parameters to replace UNSET with None.
    -                    ctx.params.update(unset_keys)
    -                    # Feed these fake context parameters to the callback.
    -                    value = self.callback(ctx, self, value)
    -                    # Restore the UNSET values in the context parameters.
    -                    ctx.params.update(
    -                        {
    -                            k: UNSET
    -                            for k in unset_keys
    -                            # Only restore keys that are present and still None, in case
    -                            # the callback modified other parameters.
    -                            if k in ctx.params and ctx.params[k] is None
    -                        }
    -                    )
[1] +            value = self.callback(ctx, self, value)
     
             return value
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 5. `9bbc6d42af258208` · Textualize/rich · 2026-01-24

- Commit: https://github.com/Textualize/rich/commit/73ee8232e7ea72a90130ccf67d8ffefd4122e9f4
- Evidence read: https://github.com/Textualize/rich/pull/3944, https://github.com/Textualize/rich/issues/3943

Commit message:

> fix fonts

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `off-by-one-or-boundary`
- **Primary range:** [1] `rich/cells.py` lines 60–60 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

codepoints beyond the last cell-width table range measured as 0 cells instead of 1, so private-use glyphs (Nerd Fonts) misalign tables (issue #3943, 14.3.0 regression); alt type-or-contract

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/rich/cells.py b/rich/cells.py
    index 15fe7b6..4429790 100644
    --- a/rich/cells.py
    +++ b/rich/cells.py
    @@ -57,7 +57,7 @@ def get_character_cell_size(character: str, unicode_version: str = "auto") -> in
         codepoint = ord(character)
         table = load_cell_table(unicode_version).widths
         if codepoint > table[-1][1]:
    -        return 1
[1] +        return 0
         lower_bound = 0
         upper_bound = len(table) - 1
         index = (lower_bound + upper_bound) // 2
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 6. `7eb8966db1053148` · agronholm/anyio · 2026-08-29

- Commit: https://github.com/agronholm/anyio/commit/44d0c93cc20079acbf38ba4dbed5ab9df323f153
- Evidence read: https://github.com/agronholm/anyio/pull/1275, https://github.com/agronholm/anyio/issues/1274

Commit message:

> Fixed asyncio task group coroutine cleanup (#1275)
>
> ---------

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `resource-leak`
- **Primary range:** [2] `src/anyio/_backends/_asyncio.py` lines 891–899 (of 2 ranges)
- **Ranges holding the bug** (strict recall, Q62): [2]

<details><summary>Labeller's note (open after forming your own view)</summary>

when the loop or a custom task constructor rejects task creation, the caller and wrapper coroutines are never closed ('coroutine was never awaited'; issue #1274); only custom task constructors affected, per maintainer; import [1] noise

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/_backends/_asyncio.py b/src/anyio/_backends/_asyncio.py
    index 2c67b00..35b0cf3 100644
    --- a/src/anyio/_backends/_asyncio.py
    +++ b/src/anyio/_backends/_asyncio.py
    @@ -31,7 +31,7 @@ from collections.abc import (
         Sequence,
     )
     from concurrent.futures import Future
    -from contextlib import AbstractContextManager, suppress
[1] +from contextlib import AbstractContextManager
     from contextvars import Context, copy_context
     from dataclasses import dataclass, field
     from functools import partial, wraps
    @@ -888,26 +888,15 @@ class TaskGroup(abc.TaskGroup):
             handle = TaskHandle(coro, name)
             loop = asyncio.get_running_loop()
             wrapper_coro = handle._run_coro()
    -        try:
    -            if (
    -                (factory := loop.get_task_factory())
    -                and getattr(factory, "__code__", None) is _eager_task_factory_code
    -                and (closure := getattr(factory, "__closure__", None))
    -            ):
    -                custom_task_constructor = closure[0].cell_contents
    -                task = custom_task_constructor(
    -                    wrapper_coro, loop=loop, name=handle.name
    -                )
    -            else:
    -                task = loop.create_task(wrapper_coro, name=handle.name)
    -        except BaseException:
    -            with suppress(BaseException):
    -                wrapper_coro.close()
    -
    -            with suppress(BaseException):
    -                coro.close()
    -
    -            raise
[2] +        if (
[2] +            (factory := loop.get_task_factory())
[2] +            and getattr(factory, "__code__", None) is _eager_task_factory_code
[2] +            and (closure := getattr(factory, "__closure__", None))
[2] +        ):
[2] +            custom_task_constructor = closure[0].cell_contents
[2] +            task = custom_task_constructor(wrapper_coro, loop=loop, name=handle.name)
[2] +        else:
[2] +            task = loop.create_task(wrapper_coro, name=handle.name)
     
             # Make the spawned task inherit the task group's cancel scope
             _task_states[task] = TaskState(
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 7. `42b0172a905fe7e4` · fastapi/fastapi · 2025-12-02

- Commit: https://github.com/fastapi/fastapi/commit/cb3792d39e1004947419a2a06b5764894730892d
- Evidence read: https://github.com/fastapi/fastapi/pull/14416

Commit message:

> 🐛 Fix unformatted `{type_}` in FastAPIError (#14416)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `error-handling`
- **Primary range:** [2] `fastapi/utils.py` lines 124–124 (of 3 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1], [2], [3]

<details><summary>Labeller's note (open after forming your own view)</summary>

FastAPIError raised with an unformatted template: the message shows a literal '{type_}' instead of the offending type (PR #14416, label bug, regression from #14168); a missing .format() call, not wording; v1 paths [1][3] same

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
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
[1] +            raise fastapi.exceptions.FastAPIError(_invalid_args_message) from None
         elif PYDANTIC_V2:
             from ._compat import v2
     
    @@ -123,9 +121,7 @@ def create_model_field(
             try:
                 return v2.ModelField(**kwargs)  # type: ignore[return-value,arg-type]
             except PydanticSchemaGenerationError:
    -            raise fastapi.exceptions.FastAPIError(
    -                _invalid_args_message.format(type_=type_)
    -            ) from None
[2] +            raise fastapi.exceptions.FastAPIError(_invalid_args_message) from None
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
[3] +        raise fastapi.exceptions.FastAPIError(_invalid_args_message) from None
     
     
     def create_cloned_field(
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 8. `83fe864a3b6f3d56` · agronholm/anyio · 2026-07-12

- Commit: https://github.com/agronholm/anyio/commit/1e988b617b69588e33fecb75e36a9837245f562f
- Evidence read: https://github.com/agronholm/anyio/pull/1218

Commit message:

> Fixed CapacityLimiter raising trio.WouldBlock instead of anyio.WouldBlock (#1218)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `error-handling`
- **Primary range:** [1] `src/anyio/_backends/_trio.py` lines 891–891 (of 2 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1], [2]

<details><summary>Labeller's note (open after forming your own view)</summary>

trio CapacityLimiter.acquire_nowait raises trio.WouldBlock instead of anyio.WouldBlock, unlike every other primitive (PR #1218); [2] same; wrong exception type

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/_backends/_trio.py b/src/anyio/_backends/_trio.py
    index 43d24d2..341ddea 100644
    --- a/src/anyio/_backends/_trio.py
    +++ b/src/anyio/_backends/_trio.py
    @@ -888,16 +888,10 @@ class CapacityLimiter(BaseCapacityLimiter):
             return self.__original.available_tokens
     
         def acquire_nowait(self) -> None:
    -        try:
    -            self.__original.acquire_nowait()
    -        except trio.WouldBlock:
    -            raise WouldBlock from None
[1] +        self.__original.acquire_nowait()
     
         def acquire_on_behalf_of_nowait(self, borrower: object) -> None:
    -        try:
    -            self.__original.acquire_on_behalf_of_nowait(borrower)
    -        except trio.WouldBlock:
    -            raise WouldBlock from None
[2] +        self.__original.acquire_on_behalf_of_nowait(borrower)
     
         async def acquire(self) -> None:
             await self.__original.acquire()
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 9. `607429995bc51ef7` · fastapi/fastapi · 2025-12-10

- Commit: https://github.com/fastapi/fastapi/commit/7ba042e069ad424a584a37f1db03887798d9af80
- Evidence read: https://github.com/fastapi/fastapi/pull/14485, https://github.com/fastapi/fastapi/issues/14484

Commit message:

> 🐛 Fix support for `if TYPE_CHECKING`,  non-evaluated stringified annotations (#14485)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `error-handling`
- **Primary range:** [2] `fastapi/dependencies/utils.py` lines 214–214 (of 4 ranges)
- **Ranges holding the bug** (strict recall, Q62): [2], [4]

<details><summary>Labeller's note (open after forming your own view)</summary>

inspect.signature(eval_str=True) raises NameError for annotations imported under TYPE_CHECKING; not caught, so app startup breaks (issue #14484, label bug, regression in 0.123.7); return-annotation path [4] same; alt type-or-contract

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/fastapi/dependencies/utils.py b/fastapi/dependencies/utils.py
    index 262dba6f..23bca6f2 100644
    --- a/fastapi/dependencies/utils.py
    +++ b/fastapi/dependencies/utils.py
    @@ -209,21 +209,11 @@ def get_flat_params(dependant: Dependant) -> List[ModelField]:
         return path_params + query_params + header_params + cookie_params
     
     
    -def _get_signature(call: Callable[..., Any]) -> inspect.Signature:
[1] +def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
         if sys.version_info >= (3, 10):
    -        try:
    -            signature = inspect.signature(call, eval_str=True)
    -        except NameError:
    -            # Handle type annotations with if TYPE_CHECKING, not used by FastAPI
    -            # e.g. dependency return types
    -            signature = inspect.signature(call)
[2] +        signature = inspect.signature(call, eval_str=True)
         else:
[3]          signature = inspect.signature(call)
    -    return signature
    -
    -
    -def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    -    signature = _get_signature(call)
[3]      unwrapped = inspect.unwrap(call)
         globalns = getattr(unwrapped, "__globals__", {})
         typed_params = [
    @@ -249,7 +239,10 @@ def get_typed_annotation(annotation: Any, globalns: Dict[str, Any]) -> Any:
     
     
     def get_typed_return_annotation(call: Callable[..., Any]) -> Any:
    -    signature = _get_signature(call)
[4] +    if sys.version_info >= (3, 10):
[4] +        signature = inspect.signature(call, eval_str=True)
[4] +    else:
[4] +        signature = inspect.signature(call)
         unwrapped = inspect.unwrap(call)
         annotation = signature.return_annotation
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 10. `18cd304d2ad2f182` · agronholm/anyio · 2025-10-22

- Commit: https://github.com/agronholm/anyio/commit/8175082ae1331fcd5816d965a909747c0584a984
- Evidence read: https://github.com/agronholm/anyio/pull/1002, https://github.com/agronholm/anyio/issues/671, https://github.com/agronholm/anyio/pull/752, https://github.com/agronholm/anyio/pull/980

Commit message:

> Fixed `Process.stdin.send` exceptions and checkpointing on asyncio (#1002)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `error-handling`
- **Primary range:** [3] `src/anyio/_backends/_asyncio.py` lines 1057–1058 (of 8 ranges)
- **Ranges holding the bug** (strict recall, Q62): [3]

<details><summary>Labeller's note (open after forming your own view)</summary>

Process.stdin.send raised non-AnyIO exceptions instead of ClosedResourceError/BrokenResourceError, and skipped a cancellation checkpoint (issue #671, label bug); noise: dataclass import [1], UDP aclose _closed ordering [5-8]; alt concurrency-or-async

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/_backends/_asyncio.py b/src/anyio/_backends/_asyncio.py
    index 53da9ce..2075814 100644
    --- a/src/anyio/_backends/_asyncio.py
    +++ b/src/anyio/_backends/_asyncio.py
    @@ -34,7 +34,7 @@ from collections.abc import (
     from concurrent.futures import Future
     from contextlib import AbstractContextManager, suppress
     from contextvars import Context, copy_context
    -from dataclasses import dataclass, field
[1] +from dataclasses import dataclass
     from functools import partial, wraps
     from inspect import (
         CORO_RUNNING,
    @@ -1052,30 +1052,12 @@ class StreamReaderWrapper(abc.ByteReceiveStream):
     @dataclass(eq=False)
     class StreamWriterWrapper(abc.ByteSendStream):
[2]      _stream: asyncio.StreamWriter
    -    _closed: bool = field(init=False, default=False)
[2]  
         async def send(self, item: bytes) -> None:
    -        await AsyncIOBackend.checkpoint_if_cancelled()
    -        stream_paused = self._stream._protocol._paused  # type: ignore[attr-defined]
    -        try:
    -            self._stream.write(item)
    -            await self._stream.drain()
    -        except (ConnectionResetError, BrokenPipeError, RuntimeError) as exc:
    -            # If closed by us and/or the peer:
    -            # * on stdlib, drain() raises ConnectionResetError or BrokenPipeError
    -            # * on uvloop and Winloop, write() eventually starts raising RuntimeError
    -            if self._closed:
    -                raise ClosedResourceError from exc
    -            elif self._stream.is_closing():
    -                raise BrokenResourceError from exc
    -
    -            raise
    -
    -        if not stream_paused:
    -            await AsyncIOBackend.cancel_shielded_checkpoint()
[3] +        self._stream.write(item)
[3] +        await self._stream.drain()
     
[4]      async def aclose(self) -> None:
    -        self._closed = True
[4]          self._stream.close()
             await AsyncIOBackend.checkpoint()
     
    @@ -1617,8 +1599,8 @@ class UDPSocket(abc.UDPSocket):
             return self._transport.get_extra_info("socket")
     
[5]      async def aclose(self) -> None:
    -        self._closed = True
[5]          if not self._transport.is_closing():
[6] +            self._closed = True
                 self._transport.close()
     
         async def receive(self) -> tuple[bytes, IPSockAddrType]:
    @@ -1665,8 +1647,8 @@ class ConnectedUDPSocket(abc.ConnectedUDPSocket):
             return self._transport.get_extra_info("socket")
     
[7]      async def aclose(self) -> None:
    -        self._closed = True
[7]          if not self._transport.is_closing():
[8] +            self._closed = True
                 self._transport.close()
     
         async def receive(self) -> bytes:
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 11. `400cff6a304c125b` · fastapi/fastapi · 2025-09-20

- Commit: https://github.com/fastapi/fastapi/commit/c831cdbde22e2dbaae8bcac4544a5556a5a04b5e
- Evidence read: https://github.com/fastapi/fastapi/pull/14022

Commit message:

> 🐛 Fix `inspect.getcoroutinefunction()` can break testing with `unittest.mock.patch()` (#14022)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `concurrency-or-async`
- **Primary range:** [3] `fastapi/dependencies/utils.py` lines 532–532 (of 8 ranges)
- **Ranges holding the bug** (strict recall, Q62): [3], [4], [8]

<details><summary>Labeller's note (open after forming your own view)</summary>

inspect.iscoroutinefunction on Python < 3.13 misses mock-patched async callables (cpython#94924), so async endpoints and dependencies run as sync (PR #14022, label bug); same at [4][8]; alt type-or-contract

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/fastapi/dependencies/utils.py b/fastapi/dependencies/utils.py
    index 1b15e645..081b63a8 100644
    --- a/fastapi/dependencies/utils.py
    +++ b/fastapi/dependencies/utils.py
    @@ -1,5 +1,4 @@
[1]  import inspect
    -import sys
[1]  from contextlib import AsyncExitStack, contextmanager
     from copy import copy, deepcopy
     from dataclasses import dataclass
    @@ -74,11 +73,6 @@ from starlette.responses import Response
     from starlette.websockets import WebSocket
     from typing_extensions import Annotated, get_args, get_origin
[2]  
    -if sys.version_info >= (3, 13):  # pragma: no cover
    -    from inspect import iscoroutinefunction
    -else:  # pragma: no cover
    -    from asyncio import iscoroutinefunction
    -
[2]  multipart_not_installed_error = (
         'Form data requires "python-multipart" to be installed. \n'
         'You can install "python-multipart" with: \n\n'
    @@ -535,11 +529,11 @@ def add_param_to_fields(*, field: ModelField, dependant: Dependant) -> None:
     
     def is_coroutine_callable(call: Callable[..., Any]) -> bool:
         if inspect.isroutine(call):
    -        return iscoroutinefunction(call)
[3] +        return inspect.iscoroutinefunction(call)
         if inspect.isclass(call):
             return False
         dunder_call = getattr(call, "__call__", None)  # noqa: B004
    -    return iscoroutinefunction(dunder_call)
[4] +    return inspect.iscoroutinefunction(dunder_call)
     
     
     def is_async_gen_callable(call: Callable[..., Any]) -> bool:
    diff --git a/fastapi/routing.py b/fastapi/routing.py
    index f620ced5..5418ad98 100644
    --- a/fastapi/routing.py
    +++ b/fastapi/routing.py
    @@ -1,8 +1,8 @@
[5] +import asyncio
     import dataclasses
     import email.message
     import inspect
[6]  import json
    -import sys
[6]  from contextlib import AsyncExitStack, asynccontextmanager
     from enum import Enum, IntEnum
     from typing import (
    @@ -76,11 +76,6 @@ from starlette.types import AppType, ASGIApp, Lifespan, Scope
     from starlette.websockets import WebSocket
     from typing_extensions import Annotated, Doc, deprecated
[7]  
    -if sys.version_info >= (3, 13):  # pragma: no cover
    -    from inspect import iscoroutinefunction
    -else:  # pragma: no cover
    -    from asyncio import iscoroutinefunction
    -
[7]  
     def _prepare_response_content(
         res: Any,
    @@ -237,7 +232,7 @@ def get_request_handler(
         embed_body_fields: bool = False,
     ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
         assert dependant.call is not None, "dependant.call must be a function"
    -    is_coroutine = iscoroutinefunction(dependant.call)
[8] +    is_coroutine = asyncio.iscoroutinefunction(dependant.call)
         is_body_form = body_field and isinstance(body_field.field_info, params.Form)
         if isinstance(response_class, DefaultPlaceholder):
             actual_response_class: Type[Response] = response_class.value
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 12. `8c629dc0a90265b9` · agronholm/anyio · 2026-09-13

- Commit: https://github.com/agronholm/anyio/commit/a87a823ccc0ffc98a9d21e6f2d55127a2a49ef6d
- Evidence read: https://github.com/agronholm/anyio/pull/1299

Commit message:

> Fix SocketStream.send() writing to a paused transport after a cancelled send (#1299)
>
> SocketStream.send() went straight to transport.write(), which appends to the transport's write buffer without ever offering the data to the OS whenever that buffer is non-empty. A send() cancelled while awaiting the write event
> leaves exactly that state behind: buffered data and a paused protocol. The next send() then piled its data on top, so repeated cancellation could grow the buffer without bound despite its zero high water mark.
>
> Wait on the write event before writing, as the datagram sockets do.
>
> ---------

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `concurrency-or-async`
- **Primary range:** [1] `src/anyio/_backends/_asyncio.py` lines 1436–1436 (of 2 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1], [2]

<details><summary>Labeller's note (open after forming your own view)</summary>

after a cancelled send() leaves data buffered and the protocol paused, the next send() writes without waiting for the write event and piles data onto the paused transport (PR #1299); [2] same; cancellation handling

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/_backends/_asyncio.py b/src/anyio/_backends/_asyncio.py
    index ef97de6..7eba257 100644
    --- a/src/anyio/_backends/_asyncio.py
    +++ b/src/anyio/_backends/_asyncio.py
    @@ -1433,12 +1433,7 @@ class SocketStream(abc.SocketStream):
     
         async def send(self, item: bytes) -> None:
             with self._send_guard:
    -            await AsyncIOBackend.checkpoint_if_cancelled()
    -            yielded = False
    -
    -            if not self._protocol.write_event.is_set():
    -                yielded = True
    -                await self._protocol.write_event.wait()
[1] +            await AsyncIOBackend.checkpoint()
     
                 if self._closed:
                     raise ClosedResourceError
    @@ -1453,10 +1448,7 @@ class SocketStream(abc.SocketStream):
                     else:
                         raise
     
    -            if not self._protocol.write_event.is_set():
    -                await self._protocol.write_event.wait()
    -            elif not yielded:
    -                await AsyncIOBackend.cancel_shielded_checkpoint()
[2] +            await self._protocol.write_event.wait()
     
         async def send_eof(self) -> None:
             try:
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 13. `472aeb4f89993281` · agronholm/anyio · 2026-07-12

- Commit: https://github.com/agronholm/anyio/commit/dbba29d1ade7936f18fb71ba24aa92978673482a
- Evidence read: https://github.com/agronholm/anyio/pull/1217, https://github.com/agronholm/anyio/issues/1111

Commit message:

> Fixed 100% CPU spin on cancel scope misuse (#1217)
>
> Fixes #1111.

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `concurrency-or-async`
- **Primary range:** [1] `src/anyio/_backends/_asyncio.py` lines 594–595 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

_deliver_cancellation keeps retrying done tasks left in CancelScope._tasks: 100% CPU spin after cancel-scope misnesting (issue #1111, label bug); maintainers call it a mitigation; alt resource-leak

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/_backends/_asyncio.py b/src/anyio/_backends/_asyncio.py
    index c00c2cd..d4d3db3 100644
    --- a/src/anyio/_backends/_asyncio.py
    +++ b/src/anyio/_backends/_asyncio.py
    @@ -592,10 +592,6 @@ class CancelScope(BaseCancelScope):
             should_retry = False
             current = current_task()
[1]          for task in self._tasks:
    -            # Always skip tasks that are already done (see issue #1111)
    -            if task.done():
    -                continue
    -
[1]              should_retry = True
                 if task._must_cancel:  # type: ignore[attr-defined]
                     continue
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 14. `16c2d787b571890c` · agronholm/anyio · 2026-05-27

- Commit: https://github.com/agronholm/anyio/commit/7a61227120daa1a050c18f4994c6261a1a0b0776
- Evidence read: https://github.com/agronholm/anyio/pull/1152, https://github.com/agronholm/anyio/issues/1013

Commit message:

> Fixed BlockingPortal tasks not getting cancelled after stop() (#1152)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `concurrency-or-async`
- **Primary range:** [2] `src/anyio/from_thread.py` lines 249–249 (of 3 ranges)
- **Ranges holding the bug** (strict recall, Q62): [2], [3]

<details><summary>Labeller's note (open after forming your own view)</summary>

cancelling a portal task's future after stop() did nothing: callback read _event_loop_thread_id after stop() cleared it (issue #1013, label bug)

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/from_thread.py b/src/anyio/from_thread.py
    index cd6f80c..837de5e 100644
    --- a/src/anyio/from_thread.py
    +++ b/src/anyio/from_thread.py
    @@ -244,16 +244,12 @@ class BlockingPortal:
             kwargs: dict[str, Any],
             future: Future[T_Retval],
[1]      ) -> None:
    -        event_loop_thread_id = self._event_loop_thread_id
    -
[1]          def callback(f: Future[T_Retval]) -> None:
                 if f.cancelled():
    -                if event_loop_thread_id == get_ident():
[2] +                if self._event_loop_thread_id == get_ident():
                         scope.cancel("the future was cancelled")
    -                elif event_loop_thread_id is not None:
    -                    run_sync(
    -                        scope.cancel, "the future was cancelled", token=self._token
    -                    )
[3] +                elif self._event_loop_thread_id is not None:
[3] +                    self.call(scope.cancel, "the future was cancelled")
     
             try:
                 retval_or_awaitable = func(*args, **kwargs)
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 15. `2e327bebc7bbf91b` · pallets/click · 2025-11-19

- Commit: https://github.com/pallets/click/commit/91de59c6c8abc8251e7af551cd4546cc964288af
- Evidence read: https://github.com/pallets/click/pull/3152, https://github.com/pallets/click/issues/3084, https://github.com/pallets/click/pull/3104

Commit message:

> Fix #3084: Correct flag optional value behavior and add comprehensive tests
>
> - [pre-commit.ci lite] apply automatic fixes
> - added required test in test_options, removed seperate test files. Maintained consistency throughout the docs.
> - Fixed Missing indentaion in CHANGES.rst

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `control-flow`
- **Primary range:** [3] `src/click/core.py` lines 2783–2783 (of 3 ranges)
- **Ranges holding the bug** (strict recall, Q62): [3]

<details><summary>Labeller's note (open after forming your own view)</summary>

is_flag=False with flag_value: _flag_needs_value ignores flag_value, so the documented optional-value option demands an argument (issue #3084, 8.3.0 regression); docstring [1] and comment [2] noise

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/click/core.py b/src/click/core.py
    index 9c2d426..57f549c 100644
    --- a/src/click/core.py
    +++ b/src/click/core.py
    @@ -2684,10 +2684,6 @@ class Option(Parameter):
         :param hidden: hide this option from help outputs.
         :param attrs: Other command arguments described in :class:`Parameter`.
[1]  
    -    .. versionchanged:: 8.3.dev
    -         If ``flag_value`` is set or no default is provided, the flag can be
    -         accepted without an argument.
    -
[1]      .. versionchanged:: 8.2
             ``envvar`` used with ``flag_value`` will always use the ``flag_value``,
             previously it would use the value of the environment variable.
    @@ -2781,13 +2777,10 @@ class Option(Parameter):
                 # Implicitly a flag because secondary options names were given.
                 elif self.secondary_opts:
                     is_flag = True
    -
    -        # Handle options that are not flags but provide a flag_value.
    -        # If flag_value is set or no default is provided the flag can be accepted
    -        # without an argument.
    -        # https://github.com/pallets/click/issues/3084
[2] +        # The option is explicitly not a flag. But we do not know yet if it needs a
[2] +        # value or not. So we look at the default value to determine it.
             elif is_flag is False and not self._flag_needs_value:
    -            self._flag_needs_value = flag_value is not UNSET or self.default is UNSET
[3] +            self._flag_needs_value = self.default is UNSET
     
             if is_flag:
                 # Set missing default for flags if not explicitly required or prompted.
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 16. `2106f137b8772e1c` · pallets/click · 2026-04-30

- Commit: https://github.com/pallets/click/commit/2468b70997a6ec27ced4b4867954c90da3f92075
- Evidence read: https://github.com/pallets/click/pull/2969, https://github.com/pallets/click/issues/2968

Commit message:

> Fix readline backspace/line-wrapping on linux (#2969)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `control-flow`
- **Primary range:** [4] `src/click/termui.py` lines 150–155 (of 5 ranges)
- **Ranges holding the bug** (strict recall, Q62): [4], [5]

<details><summary>Labeller's note (open after forming your own view)</summary>

Windows-only readline workaround applied on all platforms: backspace and line wrapping broke on Linux and returned input differed from screen (issue #2968); confirm() [5] same; import ranges [1][2][3] noise

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/click/termui.py b/src/click/termui.py
    index db41807..6801e30 100644
    --- a/src/click/termui.py
    +++ b/src/click/termui.py
    @@ -7,12 +7,10 @@ import itertools
     import sys
     import typing as t
[1]  from contextlib import AbstractContextManager
    -from contextlib import redirect_stdout
[1]  from gettext import gettext as _
     
     from ._compat import isatty
[2]  from ._compat import strip_ansi
    -from ._compat import WIN
[2]  from .exceptions import Abort
     from .exceptions import UsageError
     from .globals import resolve_color_default
    @@ -59,26 +57,6 @@ def hidden_prompt_func(prompt: str) -> str:
         return getpass.getpass(prompt)
     
[3]  
    -def _readline_prompt(func: t.Callable[[str], str], text: str, err: bool) -> str:
    -    """Call a prompt function, passing the full prompt on non-Windows so
    -    readline can handle line editing and cursor positioning correctly.
    -
    -    On Windows the prompt is written separately via :func:`echo` for
    -    colorama support, with only the last character passed to *func*.
    -    """
    -    if WIN:
    -        # Write the prompt separately so that we get nice coloring
    -        # through colorama on Windows.
    -        echo(text[:-1], nl=False, err=err)
    -        # Echo the last character to stdout to work around an issue
    -        # where readline causes backspace to clear the whole line.
    -        return func(text[-1:])
    -    if err:
    -        with redirect_stdout(sys.stderr):
    -            return func(text)
    -    return func(text)
    -
    -
[3]  def _build_prompt(
         text: str,
         suffix: str,
    @@ -169,7 +147,12 @@ def prompt(
         def prompt_func(text: str) -> str:
             f = hidden_prompt_func if hide_input else visible_prompt_func
             try:
    -            return _readline_prompt(f, text, err)
[4] +            # Write the prompt separately so that we get nice
[4] +            # coloring through colorama on Windows
[4] +            echo(text[:-1], nl=False, err=err)
[4] +            # Echo the last character to stdout to work around an issue where
[4] +            # readline causes backspace to clear the whole line.
[4] +            return f(text[-1:])
             except (KeyboardInterrupt, EOFError):
                 # getpass doesn't print a newline if the user aborts input with ^C.
                 # Allegedly this behavior is inherited from getpass(3).
    @@ -260,7 +243,12 @@ def confirm(
     
         while True:
             try:
    -            value = _readline_prompt(visible_prompt_func, prompt, err).lower().strip()
[5] +            # Write the prompt separately so that we get nice
[5] +            # coloring through colorama on Windows
[5] +            echo(prompt[:-1], nl=False, err=err)
[5] +            # Echo the last character to stdout to work around an issue where
[5] +            # readline causes backspace to clear the whole line.
[5] +            value = visible_prompt_func(prompt[-1:]).lower().strip()
             except (KeyboardInterrupt, EOFError):
                 raise Abort() from None
             if value in ("y", "yes"):
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 17. `5ba3cce2f306d1a3` · marshmallow-code/marshmallow · 2026-01-10

- Commit: https://github.com/marshmallow-code/marshmallow/commit/8dc078e2b86312988e5f7ed32849ae0788779e81
- Evidence read: https://github.com/marshmallow-code/marshmallow/pull/2892, https://github.com/marshmallow-code/marshmallow/issues/2891

Commit message:

> fix issue #2891

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `control-flow`
- **Primary range:** [1] `src/marshmallow/validate.py` lines 217–218 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

case-sensitive startswith('file:///') check: an uppercase FILE:/// URL skips the localhost fill-in and fails validation (issue #2891); URL schemes are case-insensitive; alt type-or-contract

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/marshmallow/validate.py b/src/marshmallow/validate.py
    index b00fba5..5d36519 100644
    --- a/src/marshmallow/validate.py
    +++ b/src/marshmallow/validate.py
    @@ -214,8 +214,8 @@ class URL(Validator):
     
             # Hostname is optional for file URLS. If absent it means `localhost`.
             # Fill it in for the validation if needed
    -        if scheme == "file" and value.lower().startswith("file:///"):
    -            matched = regex.search("file://localhost/" + value[8:])
[1] +        if scheme == "file" and value.startswith("file:///"):
[1] +            matched = regex.search(value.replace("file:///", "file://localhost/", 1))
             else:
                 matched = regex.search(value)
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 18. `b975c6579fe20c4c` · Textualize/rich · 2026-02-19

- Commit: https://github.com/Textualize/rich/commit/60b064a70a9db813e96955b7b344f61f62817f4c
- Evidence read: https://github.com/Textualize/rich/pull/4006, https://github.com/Textualize/rich/issues/3958

Commit message:

> fix for infinite loop in split_graphemes

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `control-flow`
- **Primary range:** [1] `rich/cells.py` lines 209–210 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

split_graphemes never advances index for a zero-width character with no previous span, so strings starting with ANSI escapes hang Console.print() (issue #3958)

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/rich/cells.py b/rich/cells.py
    index a35065a..3116595 100644
    --- a/rich/cells.py
    +++ b/rich/cells.py
    @@ -207,8 +207,6 @@ def split_graphemes(
                 # zero width characters are associated with the previous character
                 start, _end, cell_length = spans[-1]
[1]              spans[-1] = (start, index := index + 1, cell_length)
    -        else:
    -            index = index + 1
[1]  
         return (spans, total_width)
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 19. `3be1b544fcdcba98` · fastapi/fastapi · 2026-07-16

- Commit: https://github.com/fastapi/fastapi/commit/eb75fd078e83aed935016bcdf0705cd58bbf0d0e
- Evidence read: https://github.com/fastapi/fastapi/pull/16011

Commit message:

> 🐛 Fix frontend fallback support for doted paths like `/users/john.doe` (#16011)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `control-flow`
- **Primary range:** [1] `fastapi/routing.py` lines 1987–1990 (of 3 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

frontend fallback treats any final path segment with a dot (/users/john.doe) as a static asset and refuses navigation (PR #16011, label bug); accept-header wildcard rework [2][3] also changed

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/fastapi/routing.py b/fastapi/routing.py
    index 28694b4e..c442b122 100644
    --- a/fastapi/routing.py
    +++ b/fastapi/routing.py
    @@ -1984,13 +1984,24 @@ def _iter_accept_media_types(accept: str) -> Iterator[tuple[str, float]]:
     
     
     def _is_frontend_navigation_request(scope: Scope) -> bool:
[1] +    route_path = get_route_path(scope)
[1] +    final_segment = route_path.rsplit("/", 1)[-1]
[1] +    if os.path.splitext(final_segment)[1]:
[1] +        return False
         request = Request(scope)
[2] +    wildcard_accepted = False
[2] +    html_rejected = False
         for media_type, quality in _iter_accept_media_types(
             request.headers.get("accept", "")
         ):
    -        if media_type in {"text/html", "application/xhtml+xml"} and quality != 0:
    -            return True
    -    return False
[3] +        if media_type in {"text/html", "application/xhtml+xml"}:
[3] +            if quality == 0:
[3] +                html_rejected = True
[3] +            else:
[3] +                return True
[3] +        elif media_type == "*/*" and quality != 0:
[3] +            wildcard_accepted = True
[3] +    return wildcard_accepted and not html_rejected
     
     
     class _FrontendRoute(BaseRoute):
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 20. `24517970965f73df` · pallets/click · 2026-05-19

- Commit: https://github.com/pallets/click/commit/c6bf75fa74bff6523375cf91f97af0a7aae85fce
- Evidence read: https://github.com/pallets/click/pull/3478, https://github.com/pallets/click/issues/2994

Commit message:

> Fixes windows specific error regarding spaces in filepaths for open_url.

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `type-or-contract`
- **Primary range:** [1] `src/click/_termui_impl.py` lines 762–762 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

launch(locate=True) on Windows: '/select,<path>' as one argument breaks for paths with spaces (issue #2994); wrong external-command argument format; alt control-flow

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/click/_termui_impl.py b/src/click/_termui_impl.py
    index 1d23026..22bab98 100644
    --- a/src/click/_termui_impl.py
    +++ b/src/click/_termui_impl.py
    @@ -759,7 +759,7 @@ def open_url(url: str, wait: bool = False, locate: bool = False) -> int:
         elif WIN:
             if locate:
                 url = _unquote_file(url)
    -            args = ["explorer", "/select,", url]
[1] +            args = ["explorer", f"/select,{url}"]
                 try:
                     return subprocess.call(args)
                 except OSError:
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 21. `37dbdbb16e673734` · fastapi/fastapi · 2025-12-02

- Commit: https://github.com/fastapi/fastapi/commit/6cf40df24d1d199fd25d034fc87fcae284fc23a2
- Evidence read: https://github.com/fastapi/fastapi/pull/14303

Commit message:

> 🐛 Fix parsing extra `Form` parameter list (#14303)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `type-or-contract`
- **Primary range:** [1] `fastapi/dependencies/utils.py` lines 906–906 (of 2 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1], [2]

<details><summary>Labeller's note (open after forming your own view)</summary>

extra Form field sent several times: multidict items() yields one value per key, so the model gets only one (PR #14303, label bug); alt control-flow

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/fastapi/dependencies/utils.py b/fastapi/dependencies/utils.py
    index 2b2e6c5a..0f25a3c3 100644
    --- a/fastapi/dependencies/utils.py
    +++ b/fastapi/dependencies/utils.py
    @@ -903,13 +903,9 @@ async def _extract_form_body(
             if value is not None:
                 values[field.alias] = value
         field_aliases = {field.alias for field in body_fields}
    -    for key in received_body.keys():
[1] +    for key, value in received_body.items():
             if key not in field_aliases:
    -            param_values = received_body.getlist(key)
    -            if len(param_values) == 1:
    -                values[key] = param_values[0]
    -            else:
    -                values[key] = param_values
[2] +            values[key] = value
         return values
     
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 22. `38372b2a4d8d3f3e` · pallets/click · 2026-04-08

- Commit: https://github.com/pallets/click/commit/d340b0c1202284a1b9d0ca892549208527d586ce
- Evidence read: https://github.com/pallets/click/pull/3299, https://github.com/pallets/click/issues/3298

Commit message:

> Fix speculative speculative empty string check
>
> Closes #3298

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `type-or-contract`
- **Primary range:** [1] `src/click/core.py` lines 3113–3113 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

default == '' calls the default's own __eq__; semver.Version raises when compared with '', so help rendering crashes (issue #3298); PR labelled typing but the fix is runtime; alt error-handling

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/click/core.py b/src/click/core.py
    index 6dc44f3..f0a624b 100644
    --- a/src/click/core.py
    +++ b/src/click/core.py
    @@ -3110,7 +3110,7 @@ class Option(Parameter):
                     )[1]
                 elif self.is_bool_flag and not self.secondary_opts and not default_value:
                     default_string = ""
    -            elif isinstance(default_value, str) and default_value == "":
[1] +            elif default_value == "":
                     default_string = '""'
                 else:
                     default_string = str(default_value)
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 23. `640a9464ffee2f85` · marshmallow-code/marshmallow · 2026-03-25

- Commit: https://github.com/marshmallow-code/marshmallow/commit/72ac4a04208ff24df0a9694d9b03b78b1c5a2e6a
- Evidence read: https://github.com/marshmallow-code/marshmallow/pull/2904

Commit message:

> Reject booleans in from_timestamp_ms, consistent with from_timestamp (#2904)
>
> * Reject booleans in from_timestamp_ms, consistent with from_timestamp
>
> from_timestamp explicitly rejects True/False before converting to float,
> but from_timestamp_ms calls float(value) first, converting booleans to
> 1.0/0.0 before from_timestamp ever sees them. This means the boolean
> check in from_timestamp is bypassed.
>
> Add the same boolean guard to from_timestamp_ms so that
> DateTime(format="timestamp_ms") rejects booleans just like
> DateTime(format="timestamp") does.
> …

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `type-or-contract`
- **Primary range:** [1] `src/marshmallow/utils.py` lines 57–58 (of 1 ranges)
- **Ranges holding the bug** (strict recall, Q62): [1]

<details><summary>Labeller's note (open after forming your own view)</summary>

from_timestamp_ms converts to float before from_timestamp's boolean guard, so DateTime(format='timestamp_ms') accepts True/False (PR #2904); alt CWE-20

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/marshmallow/utils.py b/src/marshmallow/utils.py
    index bda3c06..ee24e5e 100644
    --- a/src/marshmallow/utils.py
    +++ b/src/marshmallow/utils.py
    @@ -55,8 +55,6 @@ def from_timestamp(value: typing.Any) -> dt.datetime:
     
     
[1]  def from_timestamp_ms(value: typing.Any) -> dt.datetime:
    -    if value is True or value is False:
    -        raise ValueError("Not a valid POSIX timestamp")
[1]      value = float(value)
         return from_timestamp(value / 1000)
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 24. `5dd6a5f8d949c1df` · fastapi/fastapi · 2025-12-10

- Commit: https://github.com/fastapi/fastapi/commit/42b250d14dd42d3c0c24dd085fa53878172a985f
- Evidence read: https://github.com/fastapi/fastapi/pull/14482, https://github.com/fastapi/fastapi/issues/14483

Commit message:

> 🐛 Fix handling arbitrary types when using `arbitrary_types_allowed=True` (#14482)

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `type-or-contract`
- **Primary range:** [5] `fastapi/_compat/v2.py` lines 98–98 (of 6 ranges)
- **Ranges holding the bug** (strict recall, Q62): [5], [6]

<details><summary>Labeller's note (open after forming your own view)</summary>

TypeAdapter built without the model's config, so arbitrary_types_allowed custom types break OpenAPI generation (issue #14483, label bug, regression since 0.119.0); config propagation [6] is the other half; imports [1][2] noise

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/fastapi/_compat/v2.py b/fastapi/_compat/v2.py
    index 46a30b3e..acd23d84 100644
    --- a/fastapi/_compat/v2.py
    +++ b/fastapi/_compat/v2.py
    @@ -1,7 +1,7 @@
     import re
     import warnings
     from copy import copy, deepcopy
    -from dataclasses import dataclass, is_dataclass
[1] +from dataclasses import dataclass
     from enum import Enum
     from typing import (
         Any,
    @@ -18,7 +18,7 @@ from typing import (
     from fastapi._compat import may_v1, shared
     from fastapi.openapi.constants import REF_TEMPLATE
     from fastapi.types import IncEx, ModelNameMap, UnionType
    -from pydantic import BaseModel, ConfigDict, TypeAdapter, create_model
[2] +from pydantic import BaseModel, TypeAdapter, create_model
     from pydantic import PydanticSchemaGenerationError as PydanticSchemaGenerationError
     from pydantic import PydanticUndefinedAnnotation as PydanticUndefinedAnnotation
     from pydantic import ValidationError as ValidationError
    @@ -64,7 +64,6 @@ class ModelField:
         field_info: FieldInfo
         name: str
[3]      mode: Literal["validation", "serialization"] = "validation"
    -    config: Union[ConfigDict, None] = None
[3]  
         @property
         def alias(self) -> str:
    @@ -95,14 +94,8 @@ class ModelField:
                     warnings.simplefilter(
                         "ignore", category=UnsupportedFieldAttributeWarning
[4]                  )
    -            annotated_args = (
    -                self.field_info.annotation,
    -                *self.field_info.metadata,
    -                self.field_info,
    -            )
[4]              self._type_adapter: TypeAdapter[Any] = TypeAdapter(
    -                Annotated[annotated_args],
    -                config=self.config,
[5] +                Annotated[self.field_info.annotation, self.field_info]
                 )
     
         def get_default(self) -> Any:
    @@ -419,21 +412,10 @@ def create_body_model(
     
     
     def get_model_fields(model: Type[BaseModel]) -> List[ModelField]:
    -    model_fields: List[ModelField] = []
    -    for name, field_info in model.model_fields.items():
    -        type_ = field_info.annotation
    -        if lenient_issubclass(type_, (BaseModel, dict)) or is_dataclass(type_):
    -            model_config = None
    -        else:
    -            model_config = model.model_config
    -        model_fields.append(
    -            ModelField(
    -                field_info=field_info,
    -                name=name,
    -                config=model_config,
    -            )
    -        )
    -    return model_fields
[6] +    return [
[6] +        ModelField(field_info=field_info, name=name)
[6] +        for name, field_info in model.model_fields.items()
[6] +    ]
     
     
     # Duplicate of several schema functions from Pydantic v1 to make them compatible with
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 25. `1b8df9743a9872e2` · Textualize/rich · 2026-01-20

- Commit: https://github.com/Textualize/rich/commit/7d4a115d8b9b641de0ae38a0fd9c1a855d2ab672
- Evidence read: https://github.com/Textualize/rich/pull/3930, https://github.com/Textualize/rich/issues/3897

Commit message:

> fix typing

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `type-or-contract`
- **Primary range:** [4] `rich/_unicode_data/__init__.py` lines 46–47 (of 6 ranges)
- **Ranges holding the bug** (strict recall, Q62): [2], [4]

<details><summary>Labeller's note (open after forming your own view)</summary>

despite 'fix typing': padding a short version tuple builds (tuple, 0), length never reaches 3, so a two-part unicode version loops forever; found by the type checker during PR #3930; VERSION_SET source [2] secondary

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/rich/_unicode_data/__init__.py b/rich/_unicode_data/__init__.py
    index cd3cf5b..3e21ca0 100644
    --- a/rich/_unicode_data/__init__.py
    +++ b/rich/_unicode_data/__init__.py
    @@ -4,7 +4,7 @@ import bisect
     import os
     from functools import cache
     from importlib import import_module
    -from typing import TYPE_CHECKING, cast
[1] +from typing import TYPE_CHECKING
     
     from rich._unicode_data._versions import VERSIONS
     
    @@ -19,7 +19,7 @@ VERSION_ORDER = sorted(
             for version in VERSIONS
         ]
     )
    -VERSION_SET = frozenset(VERSIONS)
[2] +VERSION_SET = frozenset(VERSION_ORDER)
     
     
     def _parse_version(version: str) -> tuple[int, int, int]:
    @@ -34,7 +34,6 @@ def _parse_version(version: str) -> tuple[int, int, int]:
         Returns:
             A tuple of 3 integers.
[3]      """
    -    version_integers: tuple[int, ...]
[3]      try:
             version_integers = tuple(
                 map(int, version.split(".")),
    @@ -44,8 +43,8 @@ def _parse_version(version: str) -> tuple[int, int, int]:
                 f"unicode version string {version!r} is badly formatted"
             ) from None
         while len(version_integers) < 3:
    -        version_integers = version_integers + (0,)
    -    triple = cast("tuple[int, int, int]", version_integers[:3])
[4] +        version_integers = (version_integers, 0)
[4] +    triple = version_integers[:3]
         return triple
     
     
    @@ -81,5 +80,4 @@ def load(unicode_version: str = "auto") -> CellTable:
         version_path_component = version.replace(".", "-")
         module_name = f".unicode{version_path_component}"
[5]      module = import_module(module_name, "rich._unicode_data")
    -    assert isinstance(module.cell_table, CellTable)
[5]      return module.cell_table
    diff --git a/rich/cells.py b/rich/cells.py
    index 4411b3d..07faad9 100644
    --- a/rich/cells.py
    +++ b/rich/cells.py
    @@ -424,7 +424,7 @@ class CellString:
             if self._singles:
                 return reversed(self._text)
     
    -        def iterate_text(text: str, spans: "list[CellSpan]") -> Generator[str]:
[6] +        def iterate_text(text: str, spans: "list[CellSpan]"):
                 for start, end, _ in reversed(spans):
                     yield text[start:end]
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

## Borderline cases (3 cases)

### 26. `2109faa46125df3d` · agronholm/anyio · 2026-02-09

- Commit: https://github.com/agronholm/anyio/commit/a2a07c7c7af5d0f154b770f280d8772299a20a38
- Evidence read: https://github.com/agronholm/anyio/pull/1064, https://github.com/agronholm/anyio/issues/1055

Commit message:

> fix: preserve exception cause in asyncio SocketStream (#1064)
>
> The `receive` method in asyncio SocketStream was using `raise from None` which suppressed the underlying exception cause (e.g., ConnectionResetError) set by `connection_lost`. This made it impossible for users to inspect `BrokenResourceError.__cause__` to determine the specific connection error.
>
> Remove `from None` so the `__cause__` set in `connection_lost` is preserved, making the asyncio backend consistent with the Trio backend's behavior.
>
> Fixes #1055.
>
> ---------

**Assigned labels**

- **Validity:** kept (a genuine bug)
- **Category:** `error-handling`
- **Primary range:** [2] `src/anyio/_backends/_asyncio.py` lines 1275–1275 (of 3 ranges)
- **Ranges holding the bug** (strict recall, Q62): [2]

<details><summary>Labeller's note (open after forming your own view)</summary>

asyncio SocketStream.receive raised 'from None', suppressing the underlying connection error as __cause__ (issue #1055, label bug); maintainer had chosen it deliberately before agreeing, so arguably not-a-bug

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/_backends/_asyncio.py b/src/anyio/_backends/_asyncio.py
    index aec228a..59373fb 100644
    --- a/src/anyio/_backends/_asyncio.py
    +++ b/src/anyio/_backends/_asyncio.py
    @@ -1187,7 +1187,8 @@ class StreamProtocol(asyncio.Protocol):
     
         def connection_lost(self, exc: Exception | None) -> None:
             if exc:
    -            self.exception = exc
[1] +            self.exception = BrokenResourceError()
[1] +            self.exception.__cause__ = exc
     
             self.read_event.set()
             self.write_event.set()
    @@ -1271,7 +1272,7 @@ class SocketStream(abc.SocketStream):
                     if self._closed:
                         raise ClosedResourceError from None
                     elif self._protocol.exception:
    -                    raise BrokenResourceError from self._protocol.exception
[2] +                    raise self._protocol.exception from None
                     else:
                         raise EndOfStream from None
     
    @@ -1294,7 +1295,7 @@ class SocketStream(abc.SocketStream):
                 if self._closed:
                     raise ClosedResourceError
                 elif self._protocol.exception is not None:
    -                raise BrokenResourceError from self._protocol.exception
[3] +                raise self._protocol.exception
     
                 try:
                     self._transport.write(item)
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- [x] category: agree
- [ ] category: disagree
- [x] primary range: agree
- [ ] primary range: disagree
- Note: 

### 27. `c06100e30fe371f9` · agronholm/anyio · 2026-09-06

- Commit: https://github.com/agronholm/anyio/commit/d0e32aa18162ec1cec065af805f8224f6731f01c
- Evidence read: https://github.com/agronholm/anyio/pull/1307, https://github.com/agronholm/anyio/issues/1306

Commit message:

> Fixed inconsistent result on negative/NaN sleep delays (#1307)
>
> Match sleep_until() so asyncio and trio treat negative finite delays and -inf the same (return immediately) instead of trio raising ValueError.
>
> Fixes #1306.

**Assigned labels**

- **Validity:** dropped, `not-a-bug`
- **Category / primary range:** none (dropped). If you would keep it, give the category and the primary range in the note.

<details><summary>Labeller's note (open after forming your own view)</summary>

negative/NaN sleep delays behaved differently per backend (issue #1306, found by machine analysis); maintainer chose to raise ValueError ('I much prefer erroring on invalid values'): a policy decision turning accepted inputs into errors

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/anyio/_core/_eventloop.py b/src/anyio/_core/_eventloop.py
    index 281b5ae..a3e2ab1 100644
    --- a/src/anyio/_core/_eventloop.py
    +++ b/src/anyio/_core/_eventloop.py
    @@ -90,12 +90,8 @@ async def sleep(delay: float) -> None:
         Pause the current task for the specified duration.
     
[1]      :param delay: the duration, in seconds
    -    :raises ValueError: if ``delay`` is negative (including ``-inf``) or NaN
[1]  
[2]      """
    -    if not delay >= 0:
    -        raise ValueError("delay must be a non-negative number")
    -
[2]      return await get_async_backend().sleep(delay)
     
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- Note: 

### 28. `0f097b6d4ac12b55` · pallets/click · 2026-05-15

- Commit: https://github.com/pallets/click/commit/0f71fe771ceefd5715b3b375c9b2e3a701c0648e
- Evidence read: https://github.com/pallets/click/pull/3404, https://github.com/pallets/click/issues/3403, https://github.com/pallets/click/pull/3030, https://github.com/pallets/click/issues/3111

Commit message:

> Fix dual-option arbitration to respect explicit defaults
>
> Closes #3403

**Assigned labels**

- **Validity:** dropped, `other`
- **Category / primary range:** none (dropped). If you would keep it, give the category and the primary range in the note.

<details><summary>Labeller's note (open after forming your own view)</summary>

dual-option arbitration policy redesign; upstream disputes whether 8.3 behaviour is a bug (issue #3403: 'working correctly in 8.3.3'); bug not isolable to one range

</details>

Diff the reviewer sees (the fix reversed; `[k]` marks labelled range k):

```
    diff --git a/src/click/core.py b/src/click/core.py
    index 62f3ce0..c5cab15 100644
    --- a/src/click/core.py
    +++ b/src/click/core.py
    @@ -454,12 +454,6 @@ class Context:
             self._close_callbacks: list[t.Callable[[], t.Any]] = []
             self._depth = 0
[1]          self._parameter_source: dict[str, ParameterSource] = {}
    -        # Tracks whether the option that currently owns each parameter slot in
    -        # :attr:`params` had its ``default`` set explicitly by the user. Used
    -        # to tie-break feature-switch groups where multiple options share a
    -        # parameter name and both fall back to their default value.
    -        # Refs: https://github.com/pallets/click/issues/3403
    -        self._param_default_explicit: dict[str, bool] = {}
[1]          self._exit_stack = ExitStack()
     
         @property
    @@ -2201,12 +2195,6 @@ class Parameter(ABC):
             self.multiple = multiple
             self.expose_value = expose_value
[2]          self.default: t.Any | t.Callable[[], t.Any] | None = default
    -        # Whether the user passed ``default`` explicitly to the constructor.
    -        # Captured before any auto-derived default (like ``False`` for boolean
    -        # flags in :class:`Option`) replaces the :data:`UNSET` sentinel, so it
    -        # remains ``False`` when the default was inferred rather than chosen.
    -        # Refs: https://github.com/pallets/click/issues/3403
    -        self._default_explicit: bool = default is not UNSET
[2]          self.is_eager = is_eager
             self.metavar = metavar
             self.envvar = envvar
    @@ -2593,17 +2581,11 @@ class Parameter(ABC):
     
             :meta private:
[3]          """
    -        # Capture the slot's existing state before we mutate
    -        # ``_parameter_source`` so the write decision below can compare our
    -        # incoming source against the source of the option that already wrote
    -        # the slot (if any).
    -        existing_value = ctx.params.get(self.name, UNSET)
    -        existing_source = ctx.get_parameter_source(self.name)
    -        existing_default_explicit = ctx._param_default_explicit.get(self.name, False)
    -
[3]          with augment_usage_errors(ctx, param=self):
                 value, source = self.consume_value(ctx, opts)
     
[4] +            ctx.set_parameter_source(self.name, source)
[4] +
                 # Display a deprecation warning if necessary.
                 if (
                     self.deprecated
    @@ -2634,32 +2616,15 @@ class Parameter(ABC):
                     # to UNSET, which will be interpreted as a missing value.
                     value = UNSET
     
    -        # Arbitrate the slot when several parameters target the same variable
    -        # name (feature-switch groups). See: https://github.com/pallets/click/issues/3403
    -        slot_empty = existing_value is UNSET
    -        more_explicit = existing_source is not None and source < existing_source
    -        same_source = existing_source is not None and source == existing_source
    -        auto_would_downgrade_explicit = (
    -            same_source
    -            and source == ParameterSource.DEFAULT
    -            and existing_default_explicit
    -            and not self._default_explicit
    -        )
    -        is_winner = (
    -            slot_empty
    -            or more_explicit
    -            or (same_source and not auto_would_downgrade_explicit)
    -        )
    -
    -        if is_winner:
    -            ctx.set_parameter_source(self.name, source)
    -            if self.expose_value:
    -                ctx.params[self.name] = value
    -                ctx._param_default_explicit[self.name] = self._default_explicit
    -        elif existing_source is None:
    -            # Nothing has claimed the slot yet. Record at least our source so downstream
    -            # lookups don't return ``None``.
    -            ctx.set_parameter_source(self.name, source)
[5] +        # Add parameter's value to the context.
[5] +        if (
[5] +            self.expose_value
[5] +            # We skip adding the value if it was previously set by another parameter
[5] +            # targeting the same variable name. This prevents parameters competing for
[5] +            # the same name to override each other.
[5] +            and (self.name not in ctx.params or ctx.params[self.name] is UNSET)
[5] +        ):
[5] +            ctx.params[self.name] = value
     
             return value, args
     
```

**Your verdict** (tick one box per field)

- [x] validity: agree
- [ ] validity: disagree
- Note: 
