from django.db import models
from datetime import date, timedelta


# Create your models here.

class UOM(models.Model):
    '''
    еденицы измерения
    '''
    # название еденицы измерения
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Еденицы измерения"
        verbose_name_plural = verbose_name


class Nomenclature(models.Model):
    '''
    Номенклатура - включает материалы и готовую продукци
    '''
    name = models.CharField(max_length=50)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Номенклатура материалов и ГП"
        verbose_name_plural = verbose_name


class Counterparty(models.Model):
    '''
    список контрагентов
    '''
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        # Add verbose name 
        verbose_name = 'Контрагенты'
        verbose_name_plural = verbose_name


class ConversionRate(models.Model):
    '''    
    коэффециенты конверсии 1 base_uom = conversion_rate of target_uom
    '''
    material = models.ForeignKey(Nomenclature, on_delete=models.PROTECT)
    base_uom = models.ForeignKey(UOM,
                                 on_delete=models.PROTECT,
                                 related_name='covn_base_uom')
    target_uom = models.ForeignKey(UOM, on_delete=models.PROTECT,
                                   related_name='covn_target_uom')
    conversion_rate = models.DecimalField(max_digits=10,
                                          decimal_places=4)

    def __str__(self):
        return f"{self.material} {self.base_uom}" \
               f" {self.target_uom} {self.conversion_rate}"

    class Meta:
        verbose_name = "Коэффециент конверсии"
        verbose_name_plural = verbose_name


class Purchase(models.Model):
    """
    Таблица закупок
    """
    purch_date = models.DateField()
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT)
    material = models.ForeignKey(Nomenclature, on_delete=models.PROTECT)
    purch_uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    price_ex_vat = models.DecimalField(max_digits=10, decimal_places=3)
    price_with_vat = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.counterparty} - {self.material} - {self.purch_date}"

    class Meta:
        verbose_name = "Закупки"
        verbose_name_plural = verbose_name


class Production(models.Model):
    """
    отчет производства
    """
    prod_date = models.DateField()
    description = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.description} - {self.prod_date}"

    class Meta:
        verbose_name = "отчет производства"
        verbose_name_plural = verbose_name


class ProductionProduced(models.Model):
    """
    Номенклатура, которая была получена в результате производства
    """
    prod_report = models.ForeignKey(Production, on_delete=models.CASCADE)
    produced = models.ForeignKey(Nomenclature, on_delete=models.PROTECT)
    produced_uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.prod_report} - {self.produced} - {self.quantity}"

    class Meta:
        verbose_name = "Произведенная продукция"
        verbose_name_plural = verbose_name
    
    @property
    def cost_price(self):
        materials_consumed = ProductionConsumed.objects.filter(produced=self)
        return sum(map(lambda material: material.full_purchase_price, materials_consumed))


class ProductionConsumed(models.Model):
    """
    Номенклатура, которая была списана в результате производства
    и связанная с ProductionProduced
    """

    produced = models.ForeignKey(ProductionProduced, on_delete=models.CASCADE)
    consumed = models.ForeignKey(Nomenclature, on_delete=models.PROTECT)
    consumed_uom = models.ForeignKey(UOM, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.produced} - {self.consumed} - {self.quantity} !{self.average_purchase_price}!"

    class Meta:
        verbose_name = "Списанные материалы"
        verbose_name_plural = verbose_name

    @property
    def average_purchase_price(self):
        date_X = self.produced.prod_report.prod_date
        start_date = date_X - timedelta(days=30)
        last_purchases = Purchase.objects.filter(material_id=self.consumed.id, purch_date__gte=start_date, purch_date__lte=date_X)
        if last_purchases.count() == 0:
            last_purchases = [Purchase.objects.filter(material_id=self.consumed.id, purch_date__lte=date_X).latest('purch_date')]
        return sum(map(lambda purchase: purchase.price_ex_vat, last_purchases)) / sum(map(lambda purchase: purchase.quantity, last_purchases))

    @property
    def full_purchase_price(self):
        """
        Возвращает стоимость затраты.
        Учитывается колличество потраченного материала.
        """
        return self.average_purchase_price * self.quantity
