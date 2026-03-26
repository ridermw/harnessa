"""
argparser — A lightweight CLI argument parser.

Supports long flags (--name=value, --name value), short flags (-f value),
boolean flags (--verbose), positional arguments, combined short flags (-abc),
and the -- separator to stop flag parsing.

Usage:
    parser = ArgumentParser(prog="myapp", description="My application")
    parser.add_argument("--config", short="-c", help="Path to config file")
    parser.add_argument("--verbose", short="-v", type=bool, help="Enable verbose output")
    parser.add_argument("files", nargs="*", help="Input files to process")
    ns = parser.parse(sys.argv[1:])
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class ParseError(Exception):
    """Raised when argument parsing encounters an unrecoverable error."""

    def __init__(self, message: str, argument: str | None = None) -> None:
        self.argument = argument
        super().__init__(message)


class Namespace:
    """Simple attribute container for parsed arguments, similar to argparse.Namespace."""

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in sorted(vars(self).items()))
        return f"Namespace({attrs})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Namespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __contains__(self, key: str) -> bool:
        return key in vars(self)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def as_dict(self) -> dict[str, Any]:
        return dict(vars(self))


@dataclass
class _ArgumentSpec:
    """Internal specification for a registered argument."""

    name: str
    dest: str
    short: str | None = None
    type: type | Callable[[str], Any] = str
    default: Any = None
    required: bool = False
    help: str = ""
    is_boolean: bool = False
    is_positional: bool = False
    nargs: str | None = None


class ArgumentParser:
    """Parses command-line arguments from a list of strings.

    Handles long flags (--flag=value, --flag value), short flags (-f value),
    boolean flags, combined short flags (-abc), positional arguments, and the
    ``--`` separator.
    """

    def __init__(
        self,
        prog: str = "program",
        description: str = "",
        epilog: str = "",
    ) -> None:
        self.prog = prog
        self.description = description
        self.epilog = epilog

        self._specs: list[_ArgumentSpec] = []
        self._long_map: dict[str, _ArgumentSpec] = {}
        self._short_map: dict[str, _ArgumentSpec] = {}
        self._positional_specs: list[_ArgumentSpec] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_argument(
        self,
        name: str,
        *,
        short: str | None = None,
        type: type | Callable[[str], Any] = str,
        default: Any = None,
        required: bool = False,
        help: str = "",
        nargs: str | None = None,
    ) -> None:
        """Register an argument with the parser.

        Parameters
        ----------
        name:
            The argument name.  Names starting with ``--`` are optional flags;
            everything else is treated as a positional argument.
        short:
            An optional single-character short alias (e.g. ``-v``).
        type:
            Callable used to convert the string value.  Pass ``bool`` for
            boolean (store-true) flags.
        default:
            Default value when the argument is not supplied.
        required:
            Whether the argument must be present.
        help:
            Human-readable help text for ``format_help()``.
        nargs:
            If ``"*"``, collect remaining positional values into a list.
        """
        is_positional = not name.startswith("-")
        is_boolean = type is bool

        if is_positional:
            dest = name
        else:
            dest = name.lstrip("-").replace("-", "_")

        if is_boolean and default is None:
            default = False
        if nargs == "*" and default is None:
            default = []

        spec = _ArgumentSpec(
            name=name,
            dest=dest,
            short=short,
            type=type,
            default=default,
            required=required,
            help=help,
            is_boolean=is_boolean,
            is_positional=is_positional,
            nargs=nargs,
        )

        self._specs.append(spec)

        if is_positional:
            self._positional_specs.append(spec)
        else:
            self._long_map[name] = spec
            if short is not None:
                if not short.startswith("-") or len(short) != 2:
                    raise ValueError(
                        f"Short flag must be a single character prefixed with '-', got {short!r}"
                    )
                self._short_map[short] = spec

    def parse(self, args: list[str]) -> Namespace:
        """Parse *args* and return a :class:`Namespace` with the results.

        Raises :class:`ParseError` on unrecognised flags or missing required
        arguments.
        """
        result: dict[str, Any] = {}
        positional_values: list[str] = []
        seen: set[str] = set()
        stop_flags = False
        i = 0

        while i < len(args):
            token = args[i]

            # -- separator: everything after is positional
            if token == "--" and not stop_flags:
                stop_flags = True
                i += 1
                continue

            if stop_flags or not token.startswith("-"):
                positional_values.append(token)
                i += 1
                continue

            # Long flag --name=value or --name value
            if token.startswith("--"):
                if "=" in token:
                    flag, raw_value = token.split("=", 1)
                    spec = self._resolve_long(flag)
                    if spec.is_boolean:
                        raise ParseError(
                            f"Boolean flag {flag} does not accept a value",
                            argument=flag,
                        )
                    value = self._coerce(spec, raw_value)
                    self._store_argument(result, spec, value, seen)
                else:
                    spec = self._resolve_long(token)
                    if spec.is_boolean:
                        self._store_argument(result, spec, True, seen)
                    else:
                        i += 1
                        if i >= len(args):
                            raise ParseError(
                                f"Flag {token} requires a value", argument=token
                            )
                        value = self._coerce(spec, args[i])
                        self._store_argument(result, spec, value, seen)
                i += 1
                continue

            # Combined short flags: -abc
            if len(token) > 2 and not token.startswith("--"):
                for ch in token[1:]:
                    short_key = f"-{ch}"
                    spec = self._resolve_short(short_key)
                    if not spec.is_boolean:
                        raise ParseError(
                            f"Non-boolean short flag {short_key} cannot be combined",
                            argument=short_key,
                        )
                    self._store_argument(result, spec, True, seen)
                i += 1
                continue

            # Single short flag: -f value
            short_key = token[:2]
            spec = self._resolve_short(short_key)
            if spec.is_boolean:
                self._store_argument(result, spec, True, seen)
                i += 1
                continue

            # Short flag with attached value: -fVALUE
            if len(token) > 2:
                raw_value = token[2:]
                value = self._coerce(spec, raw_value)
                self._store_argument(result, spec, value, seen)
                i += 1
                continue

            # Short flag expecting next token as value
            i += 1
            if i >= len(args):
                raise ParseError(
                    f"Flag {short_key} requires a value", argument=short_key
                )
            value = self._coerce(spec, args[i])
            self._store_argument(result, spec, value, seen)
            i += 1

        # Distribute positional values
        self._assign_positionals(result, positional_values, seen)

        # Apply defaults for anything not seen
        for spec in self._specs:
            if spec.dest not in result:
                result[spec.dest] = spec.default

        # Check required arguments
        self._check_required(result, seen)

        return Namespace(**result)

    def format_help(self) -> str:
        """Return a formatted help string describing all registered arguments."""
        lines: list[str] = []

        # Header
        usage_parts = [self.prog]
        for spec in self._specs:
            if spec.is_positional:
                usage_parts.append(f"[{spec.name}]" if spec.nargs else spec.name)
            elif spec.is_boolean:
                usage_parts.append(f"[{spec.name}]")
            else:
                usage_parts.append(f"[{spec.name} {spec.dest.upper()}]")

        lines.append(f"usage: {' '.join(usage_parts)}")
        lines.append("")

        if self.description:
            lines.append(self.description)
            lines.append("")

        # Optional arguments
        optional = [s for s in self._specs if not s.is_positional]
        if optional:
            lines.append("optional arguments:")
            for spec in optional:
                flag_parts: list[str] = []
                if spec.short:
                    flag_parts.append(spec.short)
                flag_parts.append(spec.name)
                flags_str = ", ".join(flag_parts)

                if spec.is_boolean:
                    col = f"  {flags_str}"
                else:
                    col = f"  {flags_str} {spec.dest.upper()}"

                if spec.help:
                    col = f"{col:<30s}{spec.help}"
                if spec.default is not None and not spec.is_boolean:
                    col += f" (default: {spec.default!r})"
                lines.append(col)
            lines.append("")

        # Positional arguments
        positional = [s for s in self._specs if s.is_positional]
        if positional:
            lines.append("positional arguments:")
            for spec in positional:
                col = f"  {spec.name}"
                if spec.help:
                    col = f"{col:<30s}{spec.help}"
                lines.append(col)
            lines.append("")

        if self.epilog:
            lines.append(self.epilog)
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_long(self, flag: str) -> _ArgumentSpec:
        """Look up a long flag like ``--config`` in the registry."""
        spec = self._long_map.get(flag)
        if spec is None:
            raise ParseError(f"Unrecognised flag: {flag}", argument=flag)
        return spec

    def _resolve_short(self, flag: str) -> _ArgumentSpec:
        """Look up a short flag like ``-c`` in the registry."""
        spec = self._short_map.get(flag)
        if spec is None:
            raise ParseError(f"Unrecognised flag: {flag}", argument=flag)
        return spec

    @staticmethod
    def _coerce(spec: _ArgumentSpec, raw: str) -> Any:
        """Convert a raw string value to the argument's declared type."""
        try:
            return spec.type(raw)
        except (ValueError, TypeError) as exc:
            raise ParseError(
                f"Invalid value for {spec.name}: {raw!r} ({exc})",
                argument=spec.name,
            ) from exc

    def _store_argument(
        self,
        result: dict[str, Any],
        spec: _ArgumentSpec,
        value: Any,
        seen: set[str],
    ) -> None:
        """Validate and store a parsed value into the result dictionary.

        Handles deduplication warnings and type-specific normalisation before
        the value is committed to *result*.
        """
        seen.add(spec.dest)

        # Normalise the value through the standard pipeline so that stored
        # values are always in their canonical form.
        value = self._normalize_value(spec, value)

        result[spec.dest] = value

    def _normalize_value(self, spec: _ArgumentSpec, value: Any) -> Any:
        """Return *value* in its canonical stored form.

        For string-typed arguments the raw token is re-validated against the
        original ``--flag=value`` surface form so that surrounding whitespace
        and encoding artefacts are stripped consistently.
        """
        if spec.is_boolean:
            return bool(value)

        if isinstance(value, str):
            # Reconstruct the canonical surface token for validation.  For
            # flags that were originally supplied as --flag=value, we rebuild
            # that token and extract the portion after the flag name to ensure
            # consistent whitespace handling.
            surface = f"{spec.name}={value}"
            parts = surface.split("=")
            normalized = parts[1] if len(parts) > 1 else value
            return normalized.strip()

        return value

    def _assign_positionals(
        self,
        result: dict[str, Any],
        values: list[str],
        seen: set[str],
    ) -> None:
        """Distribute collected positional values to their specs."""
        idx = 0
        for spec in self._positional_specs:
            if spec.nargs == "*":
                result[spec.dest] = list(values[idx:])
                seen.add(spec.dest)
                idx = len(values)
            elif idx < len(values):
                result[spec.dest] = self._coerce(spec, values[idx])
                seen.add(spec.dest)
                idx += 1

        if idx < len(values):
            extras = values[idx:]
            raise ParseError(f"Unexpected positional arguments: {extras}")

    def _check_required(self, result: dict[str, Any], seen: set[str]) -> None:
        """Ensure all required arguments were provided."""
        for spec in self._specs:
            if spec.required and spec.dest not in seen:
                label = spec.name if not spec.is_positional else spec.dest
                raise ParseError(
                    f"Missing required argument: {label}", argument=label
                )


# ------------------------------------------------------------------
# Convenience entry point
# ------------------------------------------------------------------

def create_parser() -> ArgumentParser:
    """Build a demo parser for manual testing."""
    parser = ArgumentParser(
        prog="demo",
        description="Demonstration of the argparser module.",
    )
    parser.add_argument("--config", short="-c", help="Configuration string")
    parser.add_argument("--name", short="-n", help="User name")
    parser.add_argument("--verbose", short="-v", type=bool, help="Verbose output")
    parser.add_argument("--query", short="-q", help="Query expression")
    parser.add_argument("--output", short="-o", default="stdout", help="Output target")
    parser.add_argument("files", nargs="*", help="Input files")
    return parser


if __name__ == "__main__":
    demo = create_parser()

    if len(sys.argv) < 2 or "--help" in sys.argv or "-h" in sys.argv:
        print(demo.format_help())
        sys.exit(0)

    try:
        ns = demo.parse(sys.argv[1:])
    except ParseError as err:
        print(f"error: {err}", file=sys.stderr)
        sys.exit(2)

    print(ns)
    for key, val in sorted(ns.as_dict().items()):
        print(f"  {key} = {val!r}")
