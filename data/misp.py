# data/misp.py
import datetime

def generate_misp_feed(victims):
    """Generate MISP feed format"""
    events = []
    
    for victim in victims:
        if not victim.get('domain'):
            continue
            
        event = {
            "info": f"LockBit Ransomware Victim: {victim.get('domain')}",
            "threat_level_id": 2,  # Medium
            "analysis": 2,  # Complete
            "distribution": 0,  # Your organization only
            "date": victim.get('first_seen', datetime.datetime.now().strftime("%Y-%m-%d")),
            "Attribute": []
        }
        
        # Add domain as attribute
        event["Attribute"].append({
            "type": "domain",
            "category": "Network activity",
            "to_ids": False,
            "value": victim.get('domain')
        })
        
        # Add description
        if victim.get('description_preview'):
            event["Attribute"].append({
                "type": "text",
                "category": "Other",
                "to_ids": False,
                "value": victim.get('description_preview')
            })
            
        # Add any emails found in contact info
        if victim.get('contact_info', {}).get('email'):
            event["Attribute"].append({
                "type": "email",
                "category": "Payload delivery",
                "to_ids": False,
                "value": victim.get('contact_info').get('email')
            })
        
        # Add tags
        event["Tag"] = [
            {"name": "tlp:amber"},
            {"name": "ransomware"},
            {"name": "lockbit"},
            {"name": "misp-galaxy:ransomware=\"LockBit\""}
        ]
        
        events.append(event)
    
    return {"response": events}
