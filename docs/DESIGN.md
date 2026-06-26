# Design Notes

The uhchi GUI direction for Corvus is based on:

- Dark graphite: `#2D2D2D`
- Red foreground: `#CC2936`
- Teal outline or offset shadow: `#2A9D8F`

Reference image:

![uhchi red and teal outline reference](assets/uhchi-style-reference.png)

Phase 0 stores these values as CSS tokens in `frontend/src/app/globals.css`.
Phase 5 should apply them to the real dashboard while keeping performance
thresholds visibly labeled as directional defaults.

