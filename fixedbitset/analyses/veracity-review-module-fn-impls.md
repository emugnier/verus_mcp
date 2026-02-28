<style>
  body { max-width: 98%; margin: auto; font-size: 16px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 4px 8px; }
</style>

# Module Function Implementations Review

## Specification Summary by Module

| Abbr | Meaning |
|------|---------|
| Tr | declared in a `trait` block |
| IT | in `impl Trait for Type` |
| IBI | in bare `impl Type` |
| ML | module-level free fn |
| V! | inside `verus!` macro |
| -V! | outside `verus!` macro |
| Unk | has requires/ensures (strength not assessed) |
| Hole | contains `assume()`, `admit()`, or `#[verifier::external_body]` |
| NoSpec | no spec |

| # | Dir | Module | Tr | IT | IBI | ML | V! | -V! | Unk | Hole | NoSpec |
|---|-----|--------|:--:|:--:|:---:|:--:|:--:|:---:|:---:|:----:|:------:|
| 1 | block | wasm | 0 | 8 | 2 | 0 | 0 | 10 | 0 | 0 | 10 |

## Function-by-Function Detail

### block/wasm.rs

| # | Function | Trait | IT | IBI | ML | V! | -V! | NoSpec | SpecStr | Lines |
|---|----------|:-----:|:--:|:--:|:--:|:--:|:---:|:------:|:-------:|------:|
| 1 | `is_empty` |  |  | Y |  |  | Y | Y |  | 11&#8209;14 |
| 2 | `andnot` |  |  | Y |  |  | Y | Y |  | 16&#8209;19 |
| 3 | `not` |  | Y |  |  |  | Y | Y |  | 24&#8209;27 |
| 4 | `bitand` |  | Y |  |  |  | Y | Y |  | 32&#8209;35 |
| 5 | `bitand_assign` |  | Y |  |  |  | Y | Y |  | 39&#8209;42 |
| 6 | `bitor` |  | Y |  |  |  | Y | Y |  | 47&#8209;50 |
| 7 | `bitor_assign` |  | Y |  |  |  | Y | Y |  | 54&#8209;57 |
| 8 | `bitxor` |  | Y |  |  |  | Y | Y |  | 62&#8209;65 |
| 9 | `bitxor_assign` |  | Y |  |  |  | Y | Y |  | 69&#8209;72 |
| 10 | `eq` |  | Y |  |  |  | Y | Y |  | 76&#8209;79 |


### Legend

- **Trait** = function declared in a `trait` block (with spec).
- **IT** = implemented in `impl Trait for Type` (inherits trait spec).
- **IBI** = implemented in bare `impl Type` (own spec).
- **ML** = module-level free function.
- **V!** = inside `verus!` macro.
- **-V!** = outside `verus!` macro.
- **NoSpec** = no requires/ensures.
- **SpecStr** = spec strength: unknown = has requires/ensures (strength not assessed); hole = contains `assume()`, `admit()`, or `#[verifier::external_body]`.
