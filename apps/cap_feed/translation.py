from modeltranslation.translator import TranslationOptions, register

from .models import Country, Region


@register(Region)
class RegionTO(TranslationOptions):
    fields = ("name",)


@register(Country)
class CountryTO(TranslationOptions):
    fields = ("name",)
