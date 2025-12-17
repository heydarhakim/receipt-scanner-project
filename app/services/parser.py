import re

def clean_currency(price_str):
    """
    Converts IDR string formats (Rp 50.000, 50.000,00) to float.
    Indonesia uses '.' for thousands and ',' for decimals.
    """
    # Remove 'Rp', 'IDR', spaces
    cleaned = re.sub(r'[^\d.,]', '', price_str)
    
    if not cleaned:
        return 0.0

    # Handle standard Indonesian format: 50.000,00 -> 50000.00
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif '.' in cleaned and cleaned.count('.') > 1: 
        # Likely thousands separators only: 1.000.000 -> 1000000
        cleaned = cleaned.replace('.', '')
    elif '.' in cleaned:
        # Ambiguous: could be 50.000 (50k) or 50.00 (50). 
        # Assumption in IDR context: usually thousands separator if 3 digits follow.
        parts = cleaned.split('.')
        if len(parts[-1]) == 3:
            cleaned = cleaned.replace('.', '')
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def is_noise(line):
    """Filter out phone numbers, dates, and common non-item headers."""
    line_lower = line.lower()
    
    # Check for phone numbers (start with 08, +62)
    if re.search(r'(\+62|08)\d{8,}', line):
        return True
        
    # Check for dates
    if re.search(r'\d{2}[-/]\d{2}[-/]\d{2,4}', line):
        return True
        
    # Check specific keywords
    noise_words = ['telp', 'fax', 'jl.', 'jakarta', 'indonesia', 'cashier', 'kasir', 'reg', 'pos', 'receipt', 'tax', 'ppn', 'change', 'kembali']
    if any(word in line_lower for word in noise_words):
        return True
        
    return False

def parse_receipt_text(text_lines):
    """
    Heuristic parser to extract items.
    Strategy: Look for lines ending in numbers (price). 
    """
    items = []
    total_candidate = 0.0
    
    # Regex to find price at the end of a string
    # Matches: 50.000 | Rp50.000 | 50,000
    price_pattern = re.compile(r'(?:Rp\.?\s?)?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)$')

    for line in text_lines:
        line = line.strip()
        if not line or is_noise(line):
            continue
            
        # Check if line ends with a price
        match = price_pattern.search(line)
        
        if match:
            price_str = match.group(1)
            raw_val = clean_currency(price_str)
            
            # Text before the price is likely the product name
            product_name = line[:match.start()].strip()
            
            # Heuristic: Valid items usually have a name longer than 2 chars
            if len(product_name) > 2 and raw_val > 0:
                # Detect "Total" line
                if "total" in product_name.lower() and "sub" not in product_name.lower():
                    total_candidate = max(total_candidate, raw_val)
                else:
                    # Simple Quantity logic: 
                    # Complex receipts might split "2 x 5000". 
                    # For this V1, we assume qty=1 unless explicit logic added.
                    items.append({
                        "name": product_name,
                        "qty": 1,
                        "unit_price": raw_val,
                        "subtotal": raw_val
                    })
    
    # Calculate total from items if OCR missed the "Total" line
    calc_total = sum(item['subtotal'] for item in items)
    final_total = total_candidate if total_candidate > 0 else calc_total
    
    return items, final_total