# data/stats.py
import datetime

def generate_stats(victims):
    """Generate statistics about the victims"""
    stats = {
        'total_victims': len(victims),
        'published_count': sum(1 for v in victims if v.get('status') == 'PUBLISHED'),
        'countdown_count': sum(1 for v in victims if v.get('status') and v.get('status') != 'PUBLISHED'),
        'domains_by_tld': {},
        'last_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    
    # Count domains by TLD
    for victim in victims:
        domain = victim.get('domain', '')
        if domain:
            tld = domain.split('.')[-1] if '.' in domain else 'unknown'
            stats['domains_by_tld'][tld] = stats['domains_by_tld'].get(tld, 0) + 1
    
    return stats
