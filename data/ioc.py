# data/ioc.py
import re

def extract_iocs_from_victims(victims):
    """Extract potential IOCs from victim data"""
    iocs = {
        'domains': set(),
        'emails': set(),
        'ips': set(),
        'urls': set()
    }
    
    for victim in victims:
        # Add the victim domain
        if victim.get('domain'):
            iocs['domains'].add(victim.get('domain'))
        
        # Extract from description if available
        if victim.get('full_description'):
            # Look for emails
            desc = victim.get('full_description')
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', desc)
            for email in emails:
                iocs['emails'].add(email)
            
            # Look for IPs
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', desc)
            for ip in ips:
                iocs['ips'].add(ip)
            
            # Look for URLs
            urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*', desc)
            for url in urls:
                iocs['urls'].add(url)
    
    # Convert sets to lists for JSON serialization
    return {k: list(v) for k, v in iocs.items()}
