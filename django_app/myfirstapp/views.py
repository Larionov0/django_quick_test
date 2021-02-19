from django.shortcuts import render
from django.http import HttpResponseNotFound
from . import models


def prodreports(request):
    return render(request, 'prodreports.html', context={
        'productions': models.Production.objects.all()
    })


def production_detail(request, prod_id):
    prod_set = models.Production.objects.filter(id=prod_id)
    if prod_set.count() == 0:
        return HttpResponseNotFound('<h1>Такого отчета нету:(</h1>')

    production = prod_set[0]
    return render(request, 'production_detail.html', context={
        'production': production,
        'prod_produced_set': models.ProductionProduced.objects.filter(prod_report_id=production.id)
    })
