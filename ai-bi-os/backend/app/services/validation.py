import re
import json

def expand_number(num_str: str) -> float:
    num_str = num_str.lower()
    multiplier = 1.0
    if num_str.endswith('k'):
        multiplier = 1_000.0
        num_str = num_str[:-1]
    elif num_str.endswith('m'):
        multiplier = 1_000_000.0
        num_str = num_str[:-1]
    elif num_str.endswith('b'):
        multiplier = 1_000_000_000.0
        num_str = num_str[:-1]
    elif num_str.endswith('l'): # Lakhs
        multiplier = 100_000.0
        num_str = num_str[:-1]
    elif num_str.endswith('cr'): # Crores
        multiplier = 10_000_000.0
        num_str = num_str[:-2]
    
    return float(num_str) * multiplier

def extract_numbers(text: str) -> list[float]:
    # Remove commas and $ signs
    text = text.replace(',', '').replace('$', '')
    
    # We want to match numbers, optionally followed by k, m, b, l, cr, or %
    # \d+(?:\.\d+)?(?:[kKmMbBlL]|[cC][rR]|%)?
    # But we need word boundaries, except % isn't a word character.
    # So we can just use re.finditer and check
    
    pattern = r'\b(\d+(?:\.\d+)?)\s*([kKmMbBlL]|[cC][rR]|%)?(?:\b|\s|$)'
    matches = re.finditer(pattern, text)
    
    nums = []
    for match in matches:
        base_val = float(match.group(1))
        suffix = match.group(2)
        if suffix:
            suffix = suffix.lower()
            if suffix == 'k': base_val *= 1_000
            elif suffix == 'm': base_val *= 1_000_000
            elif suffix == 'b': base_val *= 1_000_000_000
            elif suffix == 'l': base_val *= 100_000
            elif suffix == 'cr': base_val *= 10_000_000
            elif suffix == '%': 
                # Percentage can match the raw number (e.g. 12.3) or the decimal (0.123)
                # We'll just return the raw number (12.3) and handle the decimal match in the verifier
                pass 
        nums.append(base_val)
    return nums

def verify_numbers_against_facts(llm_text: str, facts_text: str) -> bool:
    llm_nums = extract_numbers(llm_text)
    fact_nums = extract_numbers(facts_text)
    
    if not llm_nums:
        return True # no numbers to verify
        
    for l_num in llm_nums:
        if l_num == 0: continue
        
        match_found = False
        for f_num in fact_nums:
            # Check exact or slight rounding (absolute diff < 1.0)
            if abs(l_num - f_num) < 1.0:
                match_found = True
                break
            
            # If l_num is a percentage representation of f_num (e.g. 12.3 vs 0.123)
            if abs(l_num - (f_num * 100)) < 1.0:
                match_found = True
                break
                
            # Allow LLM rounding to 1 or 2 decimal places for large numbers
            # e.g., facts has 2833322.58, LLM says 2.8M (which we parsed as 2800000)
            # The difference is 33322.58, which is < 0.05 * 2833322.58 (5% error margin for abbreviations)
            if f_num != 0 and abs(l_num - f_num) / abs(f_num) < 0.05:
                match_found = True
                break
                
        if not match_found:
            return False
            
    return True
