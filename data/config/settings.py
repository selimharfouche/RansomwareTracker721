# config/settings.py
import os

# Multi-site Configuration
SITES = {
    "lockbit": {
        "name": "LockBit",
        "mirrors": [
            "lockbit3753ekiocyo5epmpy6klmejchjtzddoekjlnt6mu3qh4de2id.onion",
            "lockbit3g3ohd3katajf6zaehxz4h4cnhmz5t735zpltywhwpc6oy3id.onion",
            "lockbit3olp7oetlc4tl5zydnoluphh7fvdt5oa6arcp2757r7xkutid.onion",
            "lockbit435xk3ki62yun7z5nhwz6jyjdp2c64j5vge536if2eny3gtid.onion",
            "lockbit4lahhluquhoka3t4spqym2m3dhe66d6lr337glmnlgg2nndad.onion",
            "lockbit6knrauo3qafoksvl742vieqbujxw7rd6ofzdtapjb4rrawqad.onion",
            "lockbit7ouvrsdgtojeoj5hvu6bljqtghitekwpdy3b6y62ixtsu5jqd.onion"
        ],
        "identifier": "LockBit",  # Text to identify this site in HTML
        "json_file": "lockbit_entities.json"
    },
    "bashe": {
        "name": "Bashe",
        "mirrors": [
            "basheqtvzqwz4vp6ks5lm2ocq7i6tozqgf6vjcasj4ezmsy4bkpshhyd.onion",
            "basherq53eniermxovo3bkduw5qqq5bkqcml3qictfmamgvmzovykyqd.onion",
            "basherykagbxoaiaxkgqhmhd5gbmedwb3di4ig3ouovziagosv4n77qd.onion",
            "bashete63b3gcijfofpw6fmn3rwnmyi5aclp55n6awcfbexivexbhyad.onion",
            "bashex7mokreyoxl6wlswxl4foi7okgs7or7aergnuiockuoq35yt3ad.onion"
        ],
        "identifier": "segment__date__deadline",  # CSS class that's unique to this site
        "json_file": "bashe_entities.json"
    }
    # Add more sites here as needed:
    # "blackcat": { ... }
    # "clop": { ... }
}

OUTPUT_DIR = "website/public/data"
HTML_SNAPSHOTS_DIR = "html_snapshots"
WAIT_TIME = 15  # Increased wait time to handle anti-bot measures

# Ensure our directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HTML_SNAPSHOTS_DIR, exist_ok=True)