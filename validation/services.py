import requests
import json

from django.http import JsonResponse
from pyld import jsonld
from pyld.jsonld import JsonLdError

from validation.models import ValidThingDescription


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
        try:
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


def is_compliance(url, localoid, oid, property):
    try:
        response_org = requests.get(url + "/api/properties/" + localoid + "/" + oid + "/" + property)
        response_org.raise_for_status()
        result_org = response_org.json()
        return check_compliance(result_org.get("message"))
    except Exception as e:
        print(str(e))
        return False


def check_compliance(data):
    try:
        print(data)
        if data is None:
            print("The content is not a valid JSON")
            #return False
            return 3
        jsonld.expand(data)
        context = data.get('@context')
        if isinstance(context, str) and context.startswith(('http://', 'https://')):
            response = requests.get(context)
            response.raise_for_status()
            context_data = response.json()
        else:
            context_data = context
        context_keys = extract_keys_from_json(context_data)
        jsonld_data_without_context = {k: v for k, v in data.items() if k != '@context'}
        jsonld_keys = extract_keys_from_json(jsonld_data_without_context)
        missing_keys = jsonld_keys - context_keys
        if missing_keys:
            #return False
            print(f"Keys not present in @context: {', '.join(missing_keys)}")
            return 4
        return 5
    except JsonLdError as e:
        print("nb")
        return 2
        #if "loading remote context failed" in str(e):
            #print("BBBB")
            #return JsonResponse({
                #'is_valid_jsonld': False,
                #'message': "Invalid URL context, please check your URL"
            #}), 400
        #else:
            #print("CC")
            #return JsonResponse({
                #'is_valid_jsonld': False,
                #'message': str(e)
            #}), 400
    except Exception as e:
        print("a")
        return 1
        #return JsonResponse({
            #'is_valid_jsonld': False,
            #'message': str(e)
        #}), 400


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