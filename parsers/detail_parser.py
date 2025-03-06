# parsers/detail_parser.py

def parse_victim_details(soup):
    """Parse victim details from the detail page with support for multiple formats"""
    details = {}
    
    # Try to detect which format we're dealing with
    is_format_1 = soup.select_one('.post-company-content .desc') is not None
    is_format_2 = soup.select_one('.post-wrapper') is not None
    
    # Extract full description
    desc_elem = None
    if is_format_1:
        desc_elem = soup.select_one('.post-company-content .desc')
    elif is_format_2:
        desc_elem = soup.select_one('.post-company-content .desc')
    
    if desc_elem:
        details['full_description'] = desc_elem.text.strip()
        
        # Try to extract data volume if mentioned
        if "data volume:" in details['full_description'].lower():
            for line in details['full_description'].split('\n'):
                if "data volume:" in line.lower():
                    details['data_size'] = line.split("data volume:")[1].strip()
        
        # Try to extract contact information
        contact_info = {}
        for line in details['full_description'].split('\n'):
            if "e-mail:" in line.lower() or "email:" in line.lower():
                email_parts = line.split(":")
                if len(email_parts) > 1:
                    contact_info['email'] = email_parts[1].strip()
            elif "phone:" in line.lower():
                phone_parts = line.split(":")
                if len(phone_parts) > 1:
                    contact_info['phone'] = phone_parts[1].strip()
            elif "headquarters:" in line.lower() or "address:" in line.lower():
                address_parts = line.split(":")
                if len(address_parts) > 1:
                    contact_info['address'] = address_parts[1].strip()
        
        if contact_info:
            details['contact_info'] = contact_info
    
    # Extract deadline if present
    deadline_elem = soup.select_one('.post-banner-p')
    if deadline_elem and "Deadline:" in deadline_elem.text:
        details['deadline'] = deadline_elem.text.replace("Deadline:", "").strip()
    
    # Extract uploaded date - try both formats
    upload_elem = soup.select_one('.uploaded-date-utc')
    if upload_elem:
        details['uploaded'] = upload_elem.text.strip()
    
    # Extract updated date if available
    update_elem = soup.select_one('.updated-date-utc')
    if update_elem:
        details['last_updated'] = update_elem.text.strip()
    
    return details
