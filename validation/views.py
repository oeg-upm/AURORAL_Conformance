from datetime import date

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView
from .models import Configuration, ValidThingDescription, UserProfile
from .services import retrieve_endpoints, is_compliance
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

class AllTD(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "index.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtered_queryset = self.get_queryset()

        status_counts_query = filtered_queryset.values('conformance_status').annotate(
            count=Count('conformance_status'))
        status_counts = {status['conformance_status']: status['count'] for status in status_counts_query}
        for status in range(6):
            status_counts.setdefault(status, 0)

        total = sum(status_counts.values())
        conformant = status_counts.get(6, 0)
        not_conformant = total - conformant

        context['status_counts'] = status_counts
        context['total'] = total
        context['conformant'] = conformant
        context['not_conformant'] = not_conformant

        return context


class ValidTD(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "valid.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_valid=True)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset


class NotValidTD(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "notValid.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_valid=False)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset


class NotChecked(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "status/access.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(conformance_status=0)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset


class noAccess(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "status/access.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(conformance_status=1)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset

class AccessLevel(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "status/access.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(conformance_status=2)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset


class SyntaxLevel(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "status/access.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(conformance_status=3)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset


class SyntacticLevel(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "status/access.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(conformance_status=4)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset

class SemanticLevel(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "status/access.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(conformance_status=5)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset

class AuroralLevel(LoginRequiredMixin, ListView):
    model = ValidThingDescription
    template_name = "status/access.html"

    def get_queryset(self):
        queryset = super().get_queryset().filter(conformance_status=6)
        if not self.request.user.is_superuser:
            user_profile = UserProfile.objects.get(user=self.request.user)
            queryset = queryset.filter(company=user_profile.company.name)
        return queryset

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


def validate_item(request, oid, property, extra_parameters=None):
    try:
        extra_parameters = request.GET
        url = Configuration.objects.first()
        item = ValidThingDescription.objects.get(oid=oid, property=property)
        compliance_result, report_message = is_compliance(url.url_server, url.oid, oid, property, extra_parameters)
        item.check_date = timezone.now()
        if compliance_result == 6:
            item.conformance_status = compliance_result
            item.reportInfo = "AURORAL Conformant"
            item.is_valid = True
        elif not compliance_result:
            item.conformance_status = 1
            item.reportInfo = "No access"
            item.is_valid = False
        else:
            print(compliance_result)
            item.conformance_status = compliance_result
            item.is_valid = False
            item.reportInfo = report_message
        item.save()
        return JsonResponse({'status': str(item.is_valid), 'message': 'Conformant.'})
    except ValidThingDescription.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Not found.'})
    except Exception as e:
        item = ValidThingDescription.objects.get(oid=oid, property=property)
        item.check_date = timezone.now()
        item.conformance_status = 1
        item.reportInfo = str(e)
        item.is_valid = False
        item.save()
        return JsonResponse({'status': 'error', 'message': str(e)})
