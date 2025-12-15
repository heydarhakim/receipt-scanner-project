import re

def parse_idr(price_str):
    """
    Normalizes 'Rp 50.000', '50.000,00', '50000' to integer 50000.
    Returns None if validation fails.
    """
    # Remove non-numeric chars except , and .
    clean_str = re.sub(r'[^\d,.]', '', price_str)
    
    # Handle Indonesian format: 1.000,00 -> remove dots, split comma
    if ',' in clean_str:
        clean_str = clean_str.split(',')[0] # Drop cents
    
    clean_str = clean_str.replace('.', '')
    
    try:
        val = int(clean_str)
        return val if val > 0 else None
    except ValueError:
        return None

def parse_receipt_lines(lines):
    """
    Heuristic parser to associate Item Names with Prices.
    Assumes price is usually at the end of the line or in the next line.
    """
    items = []
    
    # Regex to identify a price pattern (e.g., 50.000 or 50,000)
    price_pattern = re.compile(r'[\d]{1,3}(?:[.,]\d{3})*(?:,\d{2})?')

    for line in lines:
        # filter out common noise
        if len(line) < 3: continue
        
        # Check if line contains a price
        matches = price_pattern.findall(line)
        if matches:
            # Take the last match as the price usually
            raw_price = matches[-1]
            price_val = parse_idr(raw_price)
            
            if price_val:
                # The text before the price is likely the item name
                # We remove the price string from the line
                item_name = line.replace(raw_price, '').strip()
                # Clean up 'Rp' or other noise from name
                item_name = re.sub(r'(?i)rp\.?', '', item_name).strip()
                # Remove leading/trailing non-alphanumeric chars
                item_name = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', item_name)

                if len(item_name) > 2:
                    items.append({"name": item_name, "price": price_val})
    
    return items