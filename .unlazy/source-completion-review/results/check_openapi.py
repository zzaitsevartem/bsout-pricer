import json
import sys
import urllib.request

with urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=10) as response:
    document = json.load(response)
schemas = document['components']['schemas']
matching = {name: schema for name, schema in schemas.items() if name == 'CatalogItemResponse' or name.endswith('__CatalogItemResponse')}
if not matching:
    sys.exit('FAIL: CatalogItemResponse schema not found')
for name, schema in matching.items():
    has_source = 'source' in schema.get('properties', {})
    print(f'{name}: source={has_source}')
    if not has_source:
        sys.exit('FAIL: source missing from runtime OpenAPI')
print('PASS: runtime OpenAPI exposes source')
