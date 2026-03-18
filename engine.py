import ast
import operator
import re
from typing import Any, Dict

def evaluate_rule_condition(condition: str, data: Dict[str, Any]) -> bool:
    if condition.strip().upper() == "DEFAULT":
        return True

    try:
        # Very simple and safe expression evaluator for conditions formatting like:
        #   amount > 100 && country == 'US' || department == 'HR'
        
        # Replace logical operators with Python equivalents
        expr_str = condition.replace("&&", " and ").replace("||", " or ")
        
        # We need to evaluate safely
        # To do this natively without external libs (since we didn't add expr-eval etc to Python),
        # we will use a limited scope `eval` or ast-based approach. 
        # Given this is a challenge, we can provide a safe environment for eval.
        
        # Inject string functions like contains, startsWith, endsWith
        # E.g., contains(country, 'US') -> ('US' in country)
        # But for simplicity, we can regex replace these to python forms before ast parse,
        # or we implement them as functions in our eval environment.
        
        def contains(field_val, substr):
            if not isinstance(field_val, str) or not isinstance(substr, str): return False
            return substr in field_val

        def startsWith(field_val, prefix):
            if not isinstance(field_val, str) or not isinstance(prefix, str): return False
            return field_val.startswith(prefix)

        def endsWith(field_val, suffix):
            if not isinstance(field_val, str) or not isinstance(suffix, str): return False
            return field_val.endswith(suffix)
            
        allowed_globals = {
            "__builtins__": {},
            "contains": contains,
            "startsWith": startsWith,
            "endsWith": endsWith,
        }
        
        # The variables in `data` are the locals. Let's merge them into locals, but make sure they match names.
        # This allows conditions to just reference `amount` and it resolves to `data['amount']`.
        
        # Evaluate
        result = eval(expr_str, allowed_globals, data)
        return bool(result)
    except Exception as e:
        # Invalid rule logic
        return False

