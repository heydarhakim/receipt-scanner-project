import re

def clean_currency(price_str):
    """
    Strict cleaning for Indonesian Rupiah.
    Ignores low values and noise.
    """
    if not price_str:
        return 0.0

    # 1. Remove common IDR prefixes/suffixes
    # matches "Rp", "IDR", ".-", ",-"
    cleaned = re.sub(r'(?i)(Rp\.?|IDR|\s|,\-|\.\-)', '', price_str)
    
    # 2. Remove all non-numeric characters except dots and commas
    cleaned = re.sub(r'[^\d.,]', '', cleaned)
    
    if not cleaned:
        return 0.0

    # 3. IDR Logic: 
    # - "100.000" -> 100000 (Standard)
    # - "59.900" -> 59900
    # - "500" -> 500
    # - "100.000,00" -> 100000.00
    
    # If it ends with ,00 or .00, remove the decimals
    if cleaned.endswith(',00'):
        cleaned = cleaned[:-3]
    elif cleaned.endswith('.00'):
        cleaned = cleaned[:-3]

    # Now remove ALL thousands separators (dots)
    # This assumes IDR does not use dots for decimals (standard ID convention)
    final_clean = cleaned.replace('.', '').replace(',', '.')

    try:
        val = float(final_clean)
        # 4. SAFETY THRESHOLD:
        # Ignore values < 500 IDR (catches dates like "20.25", "1.1", "3/4")
        if val < 500: 
            return 0.0
        return val
    except ValueError:
        return 0.0

def is_noise(line):
    line_lower = line.lower()
    
    # 1. Phone Numbers / IDs (Long digits starting with 08, +62, or just long numeric strings)
    # Catches: "0811...", "32126/4", "T808-9119"
    if re.search(r'(\+62|08)\d{5,}', line): return True
    if re.search(r'\d{5,}[-/]\d+', line): return True # Transaction IDs like 12345/01

    # 2. Dates/Times (Strict)
    # Catches: 26.11.25, 08:04:20
    if re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', line): return True
    if re.search(r'\d{1,2}:\d{2}', line): return True

    # 3. Headers/Footers
    noise_keywords = [
        'telp', 'fax', 'jl.', 'jakarta', 'indonesia', 'npwp', 'struk',
        'transaksi', 'merchant', 'terminal', 'mid', 'tid', 'reff',
        'bca', 'mandiri', 'bri', 'bni', 'debit', 'credit', 'tunai',
        'kembali', 'change', 'tax', 'ppn', 'layanan', 'konsumen',
        'call', 'sms', 'email', 'thank', 'terima kasih', 'selamat'
    ]
    if any(k in line_lower for k in noise_keywords):
        return True
        
    return False

def parse_receipt_text(text_lines):
    items = []
    total_candidate = 0.0
    
    # Pre-cleaning: Remove noise lines immediately
    clean_lines = [line.strip() for line in text_lines if line.strip() and not is_noise(line)]

    for i, line in enumerate(clean_lines):
        line_lower = line.lower()

        # --- Strategy 1: "Label : Price" (ShopeePay / Topup Style) ---
        # Matches: "Tagihan : 100.000" or "Total : Rp 50.000"
        if ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                label = parts[0].strip()
                price_text = parts[-1].strip() # Take the last part
                
                # Check if label implies a payment or item
                valid_labels = ['tagihan', 'total', 'bayar', 'harga', 'nominal', 'price', 'amount']
                
                # If label is generic (like "Total"), save as candidate but don't add as item yet
                price = clean_currency(price_text)
                
                if price > 0:
                    if any(v in label.lower() for v in valid_labels):
                        if 'total' in label.lower() or 'bayar' in label.lower():
                            total_candidate = max(total_candidate, price)
                        else:
                            # It's likely a specific item like "Tagihan"
                            items.append({
                                "name": label,
                                "qty": 1,
                                "unit_price": price,
                                "subtotal": price
                            })
                    continue

        # --- Strategy 2: "ItemName ... Price" (Supermarket Style) ---
        # Regex to find price at END of line
        # Matches: "IDM RAMOS... 59.900"
        match = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)$', line)
        if match:
            price_raw = match.group(1)
            price = clean_currency(price_raw)
            
            if price > 0:
                # Text before the price
                prefix = line[:match.start()].strip()
                
                # CASE A: Standard "Name 1 50000"
                # Check for Quantity pattern in prefix (e.g. " 1 " or " 2x ")
                qty = 1
                name = prefix
                
                # Try to extract quantity at the end of the name
                # "MOGU MOGU 1 " -> Name="MOGU MOGU", Qty=1
                qty_match = re.search(r'\s(\d+)\s*$', prefix)
                if qty_match:
                    qty_val = int(qty_match.group(1))
                    if 0 < qty_val < 50: # Sanity check for quantity
                        qty = qty_val
                        name = prefix[:qty_match.start()].strip()

                # CASE B: Floating Price (OCR split name and price)
                # If Name is empty or too short (e.g. line is just "1 59.900"), 
                # look at the PREVIOUS line for the name.
                if len(name) < 3 and i > 0:
                    prev_line = clean_lines[i-1]
                    # Ensure prev line wasn't already used or noise
                    if not is_noise(prev_line) and len(prev_line) > 3:
                        name = prev_line
                
                if len(name) > 2 and "total" not in name.lower():
                    items.append({
                        "name": name,
                        "qty": qty,
                        "unit_price": price,
                        "subtotal": price * qty
                    })
                elif "total" in name.lower() or "bayar" in name.lower():
                    total_candidate = max(total_candidate, price)

    # Fallback: If no "Total" line found, sum the items
    calc_total = sum(item['subtotal'] for item in items)
    
    # If explicit total is suspiciously low/missing, use calculated
    final_total = total_candidate if total_candidate >= calc_total else calc_total
    
    # If absolutely no items found, but we have a total, make a dummy item
    if not items and final_total > 0:
        items.append({
            "name": "Total Transaksi",
            "qty": 1,
            "unit_price": final_total,
            "subtotal": final_total
        })

    return items, final_total