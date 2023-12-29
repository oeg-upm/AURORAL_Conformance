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
        return combined_items
    except requests.RequestException as e:
        return {"error": str(e)}

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

def is_compliance(url, agid, oid):
    try:
        response_org = requests.get(url + "/api/discovery/remote/td/" + agid + "?oids=" + oid)
        response_org.raise_for_status()
        item = ValidThingDescription.objects.get(agid=agid, oid=oid)
        print(response_org.content)
        result_org = response_org.json()
        for message in result_org.get("message", []):
            properties = message.get("td", {}).get("properties", {})
            for property_key, property_value in properties.items():
                for form in property_value.get("forms", []):
                    href = form.get("href")
                    return check_compliance(href)
    except Exception as e:
        print(str(e))
        return False

def check_compliance(endpoint):
    try:
        data = requests.get(endpoint)
        data.raise_for_status()
        data = data.json()
        if data is None:
            return False
            #return ValueError("The content is not a valid JSON")
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
            return False
            #return ValueError(f"Keys not present in @context: {', '.join(missing_keys)}")
        return True
    except JsonLdError as e:
        if "loading remote context failed" in str(e):
            return JsonResponse({
                'is_valid_jsonld': False,
                'message': "Invalid URL context, please check your URL"
            }), 400
        else:
            return JsonResponse({
                'is_valid_jsonld': False,
                'message': str(e)
            }), 400
    except Exception as e:
        return JsonResponse({
            'is_valid_jsonld': False,
            'message': str(e)
        }), 400

