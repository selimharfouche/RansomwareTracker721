# config/settings.py
import os

# Configuration
LOCKBIT_MIRRORS = [
    "lockbit3753ekiocyo5epmpy6klmejchjtzddoekjlnt6mu3qh4de2id.onion",
    "lockbit3g3ohd3katajf6zaehxz4h4cnhmz5t735zpltywhwpc6oy3id.onion",
    "lockbit3olp7oetlc4tl5zydnoluphh7fvdt5oa6arcp2757r7xkutid.onion",
    "lockbit435xk3ki62yun7z5nhwz6jyjdp2c64j5vge536if2eny3gtid.onion",
    "lockbit4lahhluquhoka3t4spqym2m3dhe66d6lr337glmnlgg2nndad.onion",
    "lockbit6knrauo3qafoksvl742vieqbujxw7rd6ofzdtapjb4rrawqad.onion",
    "lockbit7ouvrsdgtojeoj5hvu6bljqtghitekwpdy3b6y62ixtsu5jqd.onion"
]
OUTPUT_DIR = "website/public/data"
ENTITIES_JSON = "lockbit_entities.json"
MIRRORS_FILE = "working_mirrors.json"
WAIT_TIME = 15  # Increased wait time for anti-bot measures

# Ensure our directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)