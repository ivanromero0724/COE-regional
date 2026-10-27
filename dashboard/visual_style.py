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


# A complete categorical palette for EVERY treemap (Overview, Capacities,
# cooperation). Area and percentages carry the quantitative meaning; hue is
# decorative and does not imply that one category performs better than another.
TREEMAP_COLORS=CAPACITY_COLORS
TREEMAP_DARK_TEXT='#0E2739'


def treemap_text_color(background):
    """Prefer the higher-contrast of light and dark labels on each PAHO tile."""
    def luminance(color):
        raw=color.lstrip('#')
        channels=[int(raw[i:i+2],16)/255 for i in (0,2,4)]
        channels=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
                  for v in channels]
        return sum(v*weight for v,weight in zip(channels,(0.2126,0.7152,0.0722)))
    bg=luminance(background)
    dark=luminance(TREEMAP_DARK_TEXT)
    white_contrast=1.05/(bg+0.05)
    dark_contrast=(max(bg,dark)+0.05)/(min(bg,dark)+0.05)
    return '#FFFFFF' if white_contrast>=dark_contrast else TREEMAP_DARK_TEXT
