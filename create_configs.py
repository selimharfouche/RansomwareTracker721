# create_configs.py
import os
import json
import argparse
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Default configurations for sites
DEFAULT_CONFIGS = {
    "lockbit": {
        "site_key": "lockbit",
        "site_name": "LockBit",
        "json_file": "lockbit_entities.json",
        "mirrors": [
            "lockbit3753ekiocyo5epmpy6klmejchjtzddoekjlnt6mu3qh4de2id.onion",
            "lockbit3g3ohd3katajf6zaehxz4h4cnhmz5t735zpltywhwpc6oy3id.onion",
            "lockbit3olp7oetlc4tl5zydnoluphh7fvdt5oa6arcp2757r7xkutid.onion",
            "lockbit435xk3ki62yun7z5nhwz6jyjdp2c64j5vge536if2eny3gtid.onion",
            "lockbit4lahhluquhoka3t4spqym2m3dhe66d6lr337glmnlgg2nndad.onion",
            "lockbit6knrauo3qafoksvl742vieqbujxw7rd6ofzdtapjb4rrawqad.onion",
            "lockbit7ouvrsdgtojeoj5hvu6bljqtghitekwpdy3b6y62ixtsu5jqd.onion"
        ],
        "site_verification": {
            "type": "text",
            "value": "LockBit"
        },
        "parsing": {
            "entity_selector": "a.post-block",
            "fields": [
                {
                    "name": "id",
                    "type": "attribute",
                    "selector": "self",
                    "attribute": "href",
                    "regex": "^\\/?(.+)$",
                    "regex_group": 1
                },
                {
                    "name": "domain",
                    "type": "text",
                    "selector": ".post-title"
                },
                {
                    "name": "status",
                    "type": "conditional",
                    "conditions": [
                        {
                            "selector": ".post-timer",
                            "exists": true,
                            "value": "countdown"
                        },
                        {
                            "selector": ".post-timer-end",
                            "exists": true,
                            "value": "published"
                        }
                    ],
                    "default": "unknown"
                },
                {
                    "name": "description_preview",
                    "type": "text",
                    "selector": ".post-block-text"
                },
                {
                    "name": "updated",
                    "type": "text",
                    "selector": ".updated-post-date span, .views .updated-post-date",
                    "regex": "Updated:\\s*(.+)",
                    "regex_group": 1,
                    "optional": true
                },
                {
                    "name": "views",
                    "type": "text",
                    "selector": "div[style*=\"opacity\"] span[style*=\"font-weight: bold\"], .views span[style*=\"font-weight: bold\"], .views span[style*=\"font-size: 12px\"]",
                    "regex": "(\\d+)",
                    "regex_group": 1,
                    "convert": "int",
                    "optional": true
                },
                {
                    "name": "countdown_remaining",
                    "type": "complex",
                    "condition": {
                        "selector": ".post-timer",
                        "exists": true
                    },
                    "fields": [
                        {
                            "name": "days",
                            "type": "text",
                            "selector": ".timer .days",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        },
                        {
                            "name": "hours",
                            "type": "text",
                            "selector": ".timer .hours",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        },
                        {
                            "name": "minutes",
                            "type": "text",
                            "selector": ".timer .minutes",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        },
                        {
                            "name": "seconds",
                            "type": "text",
                            "selector": ".timer .seconds",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        }
                    ]
                },
                {
                    "name": "class",
                    "type": "attribute",
                    "selector": "self",
                    "attribute": "class",
                    "regex": "(?:^|\\s)(?!post-block)(\\S+)(?:\\s|$)",
                    "regex_group": 1,
                    "optional": true
                }
            ]
        }
    },
    "bashe": {
        "site_key": "bashe",
        "site_name": "Bashe",
        "json_file": "bashe_entities.json",
        "mirrors": [
            "basheqtvzqwz4vp6ks5lm2ocq7i6tozqgf6vjcasj4ezmsy4bkpshhyd.onion",
            "basherq53eniermxovo3bkduw5qqq5bkqcml3qictfmamgvmzovykyqd.onion",
            "basherykagbxoaiaxkgqhmhd5gbmedwb3di4ig3ouovziagosv4n77qd.onion",
            "bashete63b3gcijfofpw6fmn3rwnmyi5aclp55n6awcfbexivexbhyad.onion",
            "bashex7mokreyoxl6wlswxl4foi7okgs7or7aergnuiockuoq35yt3ad.onion"
        ],
        "site_verification": {
            "type": "class",
            "value": "segment__date__deadline"
        },
        "parsing": {
            "entity_selector": "div.segment.published, div.segment[class*=\"segment timer\"]",
            "fields": [
                {
                    "name": "id",
                    "type": "attribute",
                    "selector": "self",
                    "attribute": "onclick",
                    "regex": "id=(\\d+)",
                    "regex_group": 1
                },
                {
                    "name": "domain",
                    "type": "text",
                    "selector": ".segment__text__off"
                },
                {
                    "name": "status",
                    "type": "conditional",
                    "conditions": [
                        {
                            "selector": "self[class*=\"timer\"]",
                            "exists": true,
                            "value": "countdown"
                        },
                        {
                            "selector": ".segment__block",
                            "exists": true,
                            "value": "published"
                        }
                    ],
                    "default": "unknown"
                },
                {
                    "name": "country",
                    "type": "text",
                    "selector": ".segment__country__deadline",
                    "optional": true
                },
                {
                    "name": "description_preview",
                    "type": "text",
                    "selector": ".segment__text__dsc"
                },
                {
                    "name": "updated",
                    "type": "text",
                    "selector": ".segment__date__deadline",
                    "regex": "(\\d{4}/\\d{2}/\\d{2} \\d{2}:\\d{2}:\\d{2})",
                    "regex_group": 1,
                    "optional": true
                },
                {
                    "name": "views",
                    "type": "text",
                    "selector": ".segment__date__deadline",
                    "regex": "views: (\\d+)",
                    "regex_group": 1,
                    "convert": "int",
                    "optional": true
                },
                {
                    "name": "countdown_remaining",
                    "type": "complex",
                    "condition": {
                        "selector": "self[class*=\"timer\"]",
                        "exists": true
                    },
                    "fields": [
                        {
                            "name": "days",
                            "type": "text",
                            "selector": ".timer .days",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        },
                        {
                            "name": "hours",
                            "type": "text",
                            "selector": ".timer .hours",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        },
                        {
                            "name": "minutes",
                            "type": "text",
                            "selector": ".timer .minutes",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        },
                        {
                            "name": "seconds",
                            "type": "text",
                            "selector": ".timer .seconds",
                            "regex": "(\\d+)",
                            "regex_group": 1,
                            "convert": "int",
                            "optional": true
                        }
                    ]
                }
            ]
        }
    }
}

def create_site_config(site_key, output_dir):
    """Create a site configuration file"""
    if site_key not in DEFAULT_CONFIGS:
        print(f"No default configuration available for {site_key}")
        return False
    
    config = DEFAULT_CONFIGS[site_key]
    filename = f"{site_key}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        print(f"Configuration file for {site_key} already exists at {filepath}")
        return False
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Write the configuration file
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created configuration file for {site_key} at {filepath}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Create site configuration files')
    parser.add_argument('--sites', type=str, nargs='+', help='Sites to create configuration for')
    parser.add_argument('--output', type=str, default=os.path.join(PROJECT_ROOT, 'data', 'config', 'sites'), 
                      help='Output directory for configuration files')
    parser.add_argument('--all', action='store_true', help='Create configuration files for all available sites')
    
    args = parser.parse_args()
    
    if args.all:
        sites = DEFAULT_CONFIGS.keys()
    elif args.sites:
        sites = args.sites
    else:
        parser.print_help()
        return
    
    for site in sites:
        create_site_config(site, args.output)

if __name__ == "__main__":
    main()