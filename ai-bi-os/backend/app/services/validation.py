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

def extract_numbers_with_metadata(text: str) -> list[tuple[float, bool]]:
    text = text.replace(',', '').replace('$', '')
    pattern = r'\b(\d+(?:\.\d+)?)\s*([kKmMbBlL]|[cC][rR]|%)?(?:\b|\s|$)'
    matches = re.finditer(pattern, text)
    
    results = []
    for match in matches:
        base_val = float(match.group(1))
        suffix = match.group(2)
        was_abbreviated = False
        
        if suffix:
            suffix = suffix.lower()
            if suffix == 'k': 
                base_val *= 1_000
                was_abbreviated = True
            elif suffix == 'm': 
                base_val *= 1_000_000
                was_abbreviated = True
            elif suffix == 'b': 
                base_val *= 1_000_000_000
                was_abbreviated = True
            elif suffix == 'l': 
                base_val *= 100_000
                was_abbreviated = True
            elif suffix == 'cr': 
                base_val *= 10_000_000
                was_abbreviated = True
            elif suffix == '%': 
                pass
                
        results.append((base_val, was_abbreviated))
    return results

def verify_numbers_against_facts(llm_text: str, facts_text: str) -> bool:
    fact_matches = extract_numbers_with_metadata(facts_text)
    fact_nums = [val for val, _ in fact_matches]
    if not fact_nums:
        return True
        
    llm_matches = extract_numbers_with_metadata(llm_text)
    for l_num, was_abbreviated in llm_matches:
        if l_num == 0:
            continue
            
        match_found = False
        for f_num in fact_nums:
            if abs(l_num - f_num) < 1.0:
                match_found = True
                break
            if abs(l_num - (f_num * 100)) < 1.0:
                match_found = True
                break
            if was_abbreviated and f_num != 0 and abs(l_num - f_num) / abs(f_num) < 0.05:
                match_found = True
                break
            if not was_abbreviated and f_num != 0 and abs(l_num - f_num) / abs(f_num) < 0.005:
                match_found = True
                break
                
        if not match_found:
            return False
            
    return True
