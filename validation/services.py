import requests
import json

from django.http import JsonResponse
from pyld import jsonld
from pyld.jsonld import JsonLdError

from validation.models import ValidThingDescription, Company
from urllib.parse import urlencode

def retrieve_endpoints(url):
    try:
        response_org = requests.get(url + "/api/discovery/items/organisation")
        response_org.raise_for_status()
        result_org = response_org.json()
        combined_items = []
        response_partners = requests.get(url + "/api/collaboration/partners")
        response_partners.raise_for_status()
        partners = response_partners.json().get('message', [])
        for partner_id in partners:
            response_partner_contract = requests.get(url + "/api/collaboration/contracts/" + partner_id)
            response_partner_contract.raise_for_status()
            partners_contract = response_partner_contract.json().get('message', [])
            ctid_list = []
            if 'ctid' in partners_contract and partners_contract['ctid']!="NOT_EXISTS":
                ctid_list.append(partners_contract['ctid'])
            for partner_contract in ctid_list:
                response_partner_items = requests.get(url + "/api/discovery/items/contract/" + partner_contract)
                response_partner_items.raise_for_status()
                final_items = response_partner_items.json().get('message', [])
                for result_original in result_org['message']:
                    for final_item in final_items:
                        combined_item = {**result_original, **final_item}
                        combined_items.append(combined_item)
        final_items = process_items(combined_items,url)
        print(final_items)
        return final_items
    except Exception as e:
        return {"error": str(e)}


def process_items(combined_items, url):
    expanded_items = []
    seen_items = set()
    for item in combined_items:
        oid = item['oid']
        agid = item['agid']
        company_name = item.get('company')
        try:
            company, created = Company.objects.get_or_create(name=company_name)
            response_detail = requests.get(url + "/api/discovery/remote/td/" + agid + "?oids=" + oid)
            response_detail.raise_for_status()
            detail = response_detail.json()
            properties = detail.get('message', [])[0].get('td', {}).get('properties', {})
            for property_name in properties.keys():
                new_item = item.copy()
                new_item['property'] = property_name
                new_item['conformance_status'] = 0
                item_str = json.dumps(new_item, sort_keys=True)
                if item_str not in seen_items:
                    expanded_items.append(new_item)
                    seen_items.add(item_str)
        except Exception as e:
            print(f"Error processing item {item}: {e}")
    return expanded_items


def is_compliance(url, localoid, oid, property, extra_parameters=None):
    try:
        #response_org = requests.get(url + "/api/properties/" + localoid + "/" + oid + "/" + property)
        request_url = f"{url}/api/properties/{localoid}/{oid}/{property}"
        if extra_parameters:
            query_string = urlencode(extra_parameters)  # Convierte el diccionario a una cadena de consulta
            request_url += f"?{query_string}"
        response_org = requests.get(request_url)
        response_org.raise_for_status()
        result_org = response_org.json()
        return check_compliance(result_org.get("message"))
    except Exception as e:
        print(str(e))
        return (1,str(e))


def check_compliance(data):
    try:
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        elif data is None:
            return (2, "The content is not a valid JSON")
        elif (isinstance(data, list) and len(data) == 0):
            return (2, "The content is an empty list")
        jsonld.expand(data)
        print(data)
        isAuroralConformant = False
        contexts = data.get('@context')
        if contexts is None:
            return (3, "Not a valid JSON-LD 1.1")

        context_keys = set()
        if isinstance(contexts, list):
            for context in contexts:
                if isinstance(context, str) and context.startswith(('http://', 'https://')):
                    response = requests.get(context)
                    if context.startswith(('http://auroralh2020.github.io/auroral-ontology-contexts/',
                                            'https://auroralh2020.github.io/auroral-ontology-contexts/')):
                        isAuroralConformant = True
                    response.raise_for_status()
                    context_data = response.json()
                    context_keys.update(extract_keys_from_json(context_data))
                elif isinstance(context, dict):
                    context_keys.update(context.keys())
        else:
            # Handle single context case
            if isinstance(contexts, str) and contexts.startswith(('http://', 'https://')):
                response = requests.get(contexts)
                print(response)
                if contexts.startswith(('http://auroralh2020.github.io/auroral-ontology-contexts/', 'https://auroralh2020.github.io/auroral-ontology-contexts/')):
                    isAuroralConformant = True
                response.raise_for_status()
                context_data = response.json()
                context_keys.update(extract_keys_from_json(context_data))
            elif isinstance(contexts, dict):
                context_keys.update(contexts.keys())

        jsonld_data_without_context = {k: v for k, v in data.items() if k != '@context'}
        jsonld_keys = extract_keys_from_json(jsonld_data_without_context)
        missing_keys = jsonld_keys - context_keys
        if missing_keys:
            print(f"Keys not present in @context: {', '.join(missing_keys)}")
            return (4, f"Keys not present in @context: {', '.join(missing_keys)}")
        if isAuroralConformant:
            return (6, "Auroral Conformant")
        else:
            return (5, "Semantic interoperability conformant")
    except JsonLdError as e:
        print(e)
        if "loading remote context failed" in str(e):
            print("Invalid URL context, please check your URL")
            return (2, str(e))
        else:
            print(e)
            return (2, str(e))
    except Exception as e:
        print(e)
        return (1, "No access")


def extract_keys_from_json(data):
    keys = set()
    if isinstance(data, dict):
        for key, value in data.items():
            keys.add(key)
            keys.update(extract_keys_from_json(value))
    elif isinstance(data, list):
        for item in data:
            keys.update(extract_keys_from_json(item))
    return keys