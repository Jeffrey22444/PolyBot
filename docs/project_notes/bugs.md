# Bugs

## 2026-07-09 - awk Log Variable Name Collided With Built-In

- Issue: launcher filtering could print concise Terminal lines while failing to write the full stream to the intended log file.
- Root cause: the awk variable was named `log`, which collides with awk's built-in `log()` function.
- Fix: use a non-built-in variable name such as `logfile` for `print >> logfile` and `fflush(logfile)`.
- Prevention: avoid awk variable names that match built-in functions when redirecting output.
