# HVAC Duct / Static Helper (Educational)

Python **stdlib-only** rough CFM vs duct size/velocity, optional filter/coil ΔP sum, simple friction reminders.

> **Educational only — not Manual D / not a ductulator replacement.**

## Quick start

```bash
cd hvac-duct-static-helper
python3 duct_static.py --cfm 800 --shape rect --width-in 12 --height-in 8 --duct-type supply-main
python3 duct_static.py --cfm 400 --shape round --diameter-in 8 --filter-dp 0.4 --coil-dp 0.3
python3 duct_static.py -i
```
