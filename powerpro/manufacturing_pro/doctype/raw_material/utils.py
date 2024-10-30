# Copyright (c) 2024, Yefri Tavarez and Contributors
# For license information, please see license.txt

import hashlib

def hash_key(value):
    # Convert the value to a string (if it's not) and then encode it to bytes
    value_str = str(value).encode('utf-8')
    
    # Use SHA-256 to create a consistent hash
    hash_object = hashlib.sha256(value_str)
    
    # Return the hexadecimal representation of the hash
    return hash_object.hexdigest()
