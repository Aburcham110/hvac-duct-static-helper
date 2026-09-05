#!/usr/bin/env python3
"""Educational duct size / velocity / rough ESP helper (stdlib).

NOT Manual D. Not a ductulator replacement.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from typing import List, Optional

DISCLAIMER = (
    "EDUCATIONAL ONLY — NOT Manual D / NOT a ductulator replacement. "
    "Use ACCA Manual D and OEM blower tables for real designs."
)

# Rule-of-thumb max velocities FPM (educational)
MAX_VEL = {
    "supply-main": 900.0,
    "supply-branch": 700.0,
    "return-main": 700.0,
    "return-branch": 600.0,
    "flex": 500.0,
}


@dataclass
class Result:
    lines: List[str]


def area_sqft(shape: str, w_in: float, h_in: Optional[float], d_in: Optional[float]) -> float:
    if shape == "round":
        if not d_in:
            raise ValueError("round duct needs --diameter-in")
        r = d_in / 24.0  # inches → feet radius
        return math.pi * r * r
    if not h_in:
        raise ValueError("rect duct needs --height-in")
    return (w_in / 12.0) * (h_in / 12.0)


def analyze(
    *,
    cfm: Optional[float],
    shape: str,
    width_in: float,
    height_in: Optional[float],
    diameter_in: Optional[float],
    duct_type: str,
    filter_dp_in: Optional[float],
    coil_dp_in: Optional[float],
    other_dp_in: float,
) -> Result:
    lines = [DISCLAIMER, ""]
    a = area_sqft(shape, width_in, height_in, diameter_in)
    lines.append(f"Internal area (approx): {a:.3f} ft²")

    vel = None
    if cfm is not None:
        if a <= 0:
            raise ValueError("area must be > 0")
        vel = cfm / a
        lines.append(f"CFM: {cfm:.0f}  →  velocity ≈ {vel:.0f} FPM")
        lim = MAX_VEL.get(duct_type, 700.0)
        lines.append(f"Educational velocity guide ({duct_type}): keep under ~{lim:.0f} FPM")
        if vel > lim:
            lines.append("Status: ABOVE educational velocity band — noise/friction risk")
        else:
            lines.append("Status: within educational velocity band (still verify Manual D)")
        # Rough friction reminder: higher V → much higher ΔP
        lines.append(
            f"Friction reminder: ΔP rises roughly with V² — {vel:.0f} FPM vs {lim:.0f} "
            f"guide is {(vel/lim)**2:.2f}× guide dynamic pressure factor (very rough)"
        )

    parts = []
    total = 0.0
    if filter_dp_in is not None:
        parts.append(f"filter {filter_dp_in:.2f}\"")
        total += filter_dp_in
    if coil_dp_in is not None:
        parts.append(f"coil {coil_dp_in:.2f}\"")
        total += coil_dp_in
    if other_dp_in:
        parts.append(f"other {other_dp_in:.2f}\"")
        total += other_dp_in
    if parts:
        lines.append("")
        lines.append(f"Measured/entered component ΔP: {', '.join(parts)}")
        lines.append(f"Sum component ESP contribution ≈ {total:.2f} in. w.c.")
        lines.append("Compare sum + duct/fitting losses to blower ESP table (OEM)")

    lines += [
        "",
        "Checklist:",
        "  [ ] Measure TESP (supply plenum − return plenum) at design fan speed",
        "  [ ] Separate filter and coil ΔP when diagnosing high static",
        "  [ ] Flex: stretch fully, minimize sag; count as high friction",
        "  [ ] Closed dampers / dirty filter often look like 'bad blower'",
        "",
        DISCLAIMER,
    ]
    return Result(lines=lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Educational duct / static helper.",
        epilog=DISCLAIMER,
    )
    p.add_argument("-i", "--interactive", action="store_true")
    p.add_argument("--cfm", type=float)
    p.add_argument("--shape", choices=("rect", "round"), default="rect")
    p.add_argument("--width-in", type=float, help="Rect width inches (or ignored if round)")
    p.add_argument("--height-in", type=float)
    p.add_argument("--diameter-in", type=float)
    p.add_argument("--duct-type", choices=list(MAX_VEL.keys()), default="supply-main")
    p.add_argument("--filter-dp", type=float, default=None, help="Filter ΔP in. w.c.")
    p.add_argument("--coil-dp", type=float, default=None, help="Coil ΔP in. w.c.")
    p.add_argument("--other-dp", type=float, default=0.0, help="Other ΔP in. w.c.")
    return p


def pf(prompt: str, default: Optional[float] = None) -> Optional[float]:
    while True:
        suf = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suf}: ").strip()
        if not raw and default is not None:
            return float(default)
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            print("Enter a number.")


def main(argv: Optional[List[str]] = None) -> int:
    ns = build_parser().parse_args(argv)
    try:
        if ns.interactive:
            print(DISCLAIMER)
            print()
            shape = input("Shape rect/round [rect]: ").strip() or "rect"
            if shape == "round":
                d = pf("Diameter inches")
                w = d or 0.0
                h = None
                dia = d
            else:
                w = pf("Width inches") or 0.0
                h = pf("Height inches")
                dia = None
            cfm = pf("CFM (blank skip)")
            dt = input(f"Duct type {list(MAX_VEL)} [supply-main]: ").strip() or "supply-main"
            fd = pf("Filter ΔP in.wc (blank skip)")
            cd = pf("Coil ΔP in.wc (blank skip)")
            od = pf("Other ΔP in.wc", 0.0) or 0.0
            r = analyze(
                cfm=cfm,
                shape=shape,
                width_in=w,
                height_in=h,
                diameter_in=dia,
                duct_type=dt,
                filter_dp_in=fd,
                coil_dp_in=cd,
                other_dp_in=od,
            )
        else:
            if ns.width_in is None and ns.shape == "rect":
                raise SystemExit("Need duct dimensions (and usually --cfm), or -i")
            w = ns.width_in if ns.width_in is not None else (ns.diameter_in or 0.0)
            r = analyze(
                cfm=ns.cfm,
                shape=ns.shape,
                width_in=w,
                height_in=ns.height_in,
                diameter_in=ns.diameter_in,
                duct_type=ns.duct_type,
                filter_dp_in=ns.filter_dp,
                coil_dp_in=ns.coil_dp,
                other_dp_in=ns.other_dp,
            )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    print("\n".join(r.lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
