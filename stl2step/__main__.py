# SPDX-FileCopyrightText: 2025 Stefan Helmert <stefan@entroserv.de>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CLI entry: python -m stl2step <file.stl> [output.step]"""

from __future__ import annotations

import sys

from stl2step.convert import convert_stl_to_step, default_output_path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m stl2step <input.stl> [output.step]", file=sys.stderr)
        return 2

    input_path = args[0]
    output_path = args[1] if len(args) > 1 else default_output_path(input_path)

    print("stl2step")
    convert_stl_to_step(
        input_path,
        output_path,
        on_log=print,
        on_progress=None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
