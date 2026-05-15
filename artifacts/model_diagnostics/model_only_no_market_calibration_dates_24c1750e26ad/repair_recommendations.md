# No-market PMF calibration failure modes — dates_24c1750e26ad

## Dominant failure counts

```
{
  "PIT_shape": 42
}
```

## Repairs

- **PIT_shape:** monotone / isotonic PIT calibration with shrinkage to parent stat.
- **mean_bias:** mean-shift or tail tilt on OOF PMFs with rollback on NLL.
- **p0_bias:** sparse p0 hurdle recalibration for blk/stl/stocks.
- **variance_bias:** variance inflation/deflation in joint sampler or post-hoc scale.

