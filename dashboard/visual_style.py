"""Shared PAHO chart identity, based on the Capacities & gaps gallery.

Keep visual-only constants here so regional and country charts remain aligned.
Category colors are intentionally not used as a risk or maturity score.
"""

FONT_FAMILY='"Avenir Next", Avenir, "Segoe UI", Arial, sans-serif'
NAVY='#005A8B'
CYAN='#009BDA'
ORANGE='#F36B32'
LIGHT_BLUE='#75B8D6'
GREEN='#53A567'
SLATE='#8DA9B9'
PURPLE='#8C6BB1'
TEXT='#17324D'
MUTED='#607B8A'
BORDER='#DFE9F1'
GRID='#E7EDF3'
AXIS='#91A5B4'
WHITE='#FFFFFF'

# Exact categorical palette already established in Capacities & gaps.
CAPACITY_COLORS=(NAVY,CYAN,ORANGE,LIGHT_BLUE,GREEN,SLATE,PURPLE)

# PAHO frequency scale: no events (neutral), 1–2 (cyan), 3–5 (navy), >5 (orange).
# Use the same four colors for the donut cards and the country heatmap.
HAZARD_COLORS=(SLATE,CYAN,NAVY,ORANGE)
