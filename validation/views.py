from datetime import date

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView
from .models import Configuration, ValidThingDescription
from .services import retrieve_endpoints, is_compliance
from django.http import JsonResponse
from django.utils import timezone


class AllTD(ListView):
    model = ValidThingDescription
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_counts_query = ValidThingDescription.objects.values('conformance_status').annotate(
            count=Count('conformance_status'))
        status_counts = {status['conformance_status']: status['count'] for status in status_counts_query}
        for status in range(6):
            status_counts.setdefault(status, 0)
        context['status_counts'] = status_counts
        return context


class ValidTD(ListView):
    model = ValidThingDescription
    template_name = "valid.html"

    def get_queryset(self):
        return ValidThingDescription.objects.filter(is_valid=True)


class NotValidTD(ListView):
    model = ValidThingDescription
    template_name = "notValid.html"

    def get_queryset(self):
        return ValidThingDescription.objects.filter(is_valid=False)


def retrieve_endpoints_view(request):
    try:
        config = Configuration.objects.first()
        if config and config.url_server:
            response = retrieve_endpoints(config.url_server)
            json_ids = set()
            for item in response:
                identifier = (
                item.get('name'), item.get('property'), item.get('company'), item.get('agid'), item.get('oid'),
                item.get('cid'))
                json_ids.add(identifier)
                if not ValidThingDescription.objects.filter(
                        name=item.get('name'),
                        property=item.get('property'),
                        company=item.get('company'),
                        agid=item.get('agid'),
                        oid=item.get('oid'),
                        cid=item.get('cid')
                ).exists():
                    ValidThingDescription.objects.create(
                        name=item.get('name'),
                        property=item.get('property'),
                        oid=item.get('oid'),
                        agid=item.get('agid'),
                        cid=item.get('cid'),
                        company=item.get('company'),
                        check_date=timezone.now(),
                        is_valid=False,
                        conformance_status=0
                    )
            for thing in ValidThingDescription.objects.all():
                if (thing.name, thing.property, thing.company, thing.agid, thing.oid, thing.cid) not in json_ids:
                    thing.delete()

            object_list = ValidThingDescription.objects.all().values(
                'id', 'name', 'property', 'oid', 'agid', 'cid', 'company', 'check_date', 'is_valid'
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Data saved',
                'object_list': list(object_list)
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Endpoint error'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def element_detail(request, item_id):
    item = get_object_or_404(ValidThingDescription, pk=item_id)
    return render(request, 'element.html', {'item': item})


def validate_item(request, oid, property):
    try:
        url = Configuration.objects.first()
        item = ValidThingDescription.objects.get(oid=oid, property=property)
        compliance_result = is_compliance(url.url_server, url.oid, oid, property)
        item.check_date = timezone.now()
        print(compliance_result)
        if compliance_result == 5:
            item.conformance_status = compliance_result
            item.is_valid = True
        elif not compliance_result:
            item.conformance_status = 1
            item.is_valid = False
        else:
            print(compliance_result)
            item.conformance_status = compliance_result
            item.is_valid = False
        item.save()
        return JsonResponse({'status': str(item.is_valid), 'message': 'Conformant.'})
    except ValidThingDescription.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
